#!/bin/bash

# RAM-Constrained Container Launcher for Out-of-Core Systems
# Usage: ./launch-container-ram-constrained.sh [OPTIONS] <service_name> <dataset_name> <ram_spec>
# Example: ./launch-container-ram-constrained.sh blaze graph500_26 75
#          ./launch-container-ram-constrained.sh --test graphchi dota_league 100
#          ./launch-container-ram-constrained.sh blaze graph500_26 50G

set -e

# Parse arguments
TEST_MODE=false
NO_NUMA=false
SERVICE_NAME=""
DATASET_NAME=""
RAM_SPEC=""
RAM_PERCENT=""
RAM_ABSOLUTE_GB=""

usage() {
    cat << 'EOF'
Usage: ./launch-container-ram-constrained.sh [OPTIONS] <service_name> <dataset_name> <ram_spec>

Options:
  --test              Run in test mode with limited CPUs (0-27)
  --no_numa           Disable NUMA pinning
  --help              Show this help message

Arguments:
  service_name        OOC system: blaze, graphchi, xstream, lumos, planar
  dataset_name        Dataset: dota_league, graph500_26, graph500_28, etc.
  ram_spec            RAM allocation - either:
                        Percentage: 50, 75, 100, 125 (as % of estimated working memory)
                        Absolute: 50G, 50M (with G or M suffix)

Examples:
  ./launch-container-ram-constrained.sh blaze graph500_26 75
  ./launch-container-ram-constrained.sh --test graphchi dota_league 100
  ./launch-container-ram-constrained.sh --no_numa xstream graph500_28 50G
  ./launch-container-ram-constrained.sh blaze graph500_26 32G
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            TEST_MODE=true
            shift
            ;;
        --no_numa)
            NO_NUMA=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            if [ -z "$SERVICE_NAME" ]; then
                SERVICE_NAME="$1"
            elif [ -z "$DATASET_NAME" ]; then
                DATASET_NAME="$1"
            elif [ -z "$RAM_SPEC" ]; then
                RAM_SPEC="$1"
            else
                echo "Error: Too many arguments"
                usage
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [ -z "$SERVICE_NAME" ] || [ -z "$DATASET_NAME" ] || [ -z "$RAM_SPEC" ]; then
    echo "Error: Missing required arguments"
    usage
fi

# Parse RAM_SPEC: determine if percentage or absolute
if [[ "$RAM_SPEC" =~ ^([0-9]+)(G|M)$ ]]; then
    # Absolute RAM specification (e.g., 50G, 512M)
    RAM_ABSOLUTE_GB=$((BASH_REMATCH[1]))
    UNIT="${BASH_REMATCH[2]}"
    if [ "$UNIT" = "M" ]; then
        RAM_ABSOLUTE_GB=$((RAM_ABSOLUTE_GB / 1024))
        if [ $RAM_ABSOLUTE_GB -lt 1 ]; then
            RAM_ABSOLUTE_GB=1
        fi
    fi
    RAM_PERCENT="absolute"
elif [[ "$RAM_SPEC" =~ ^[0-9]+$ ]]; then
    # Percentage specification (e.g., 50, 75, 100)
    if ! echo "$RAM_SPEC" | grep -qE '^(50|75|100|125|500)$'; then
        echo "Error: RAM percentage must be 50, 75, 100, 125, or 500"
        exit 1
    fi
    RAM_PERCENT="$RAM_SPEC"
else
    echo "Error: Invalid RAM specification: $RAM_SPEC"
    echo "Use format: 50 (percentage), 50G (gigabytes), or 512M (megabytes)"
    exit 1
fi

# Check memory estimates file
MEMORY_ESTIMATES="scripts/memory_estimates.json"
if [ ! -f "$MEMORY_ESTIMATES" ]; then
    echo "Error: memory_estimates.json not found at $MEMORY_ESTIMATES"
    exit 1
fi

# Get memory allocation from estimates or use absolute value
WORKING_MEMORY_GB=$(python3 << PYTHON_EOF
import json
import sys

try:
    if '$RAM_PERCENT' == 'absolute':
        # Use absolute value directly
        total_memory = int($RAM_ABSOLUTE_GB)
        print(total_memory)
    else:
        # Use percentage of estimated memory
        with open('$MEMORY_ESTIMATES') as f:
            estimates = json.load(f)

        if '$DATASET_NAME' not in estimates:
            print(f"Error: Dataset '$DATASET_NAME' not found in memory_estimates.json", file=sys.stderr)
            sys.exit(1)

        base_memory = estimates['$DATASET_NAME']['estimated_working_memory_gb']
        allocated_memory = base_memory * ($RAM_PERCENT / 100.0)

        # Add 10% overhead for OS, buffers, and runtime structures
        os_overhead = 1.1
        total_memory = int(allocated_memory * os_overhead)

        print(total_memory)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF
)

if [ $? -ne 0 ]; then
    exit 1
fi

# NUMA settings based on flags
if [ "$NO_NUMA" = true ]; then
    NUMA_NODE_0_CPUS=""
    echo "Running with NUMA settings disabled"
elif [ "$TEST_MODE" = true ]; then
    # Test mode: use CPUs 0-27
    NUMA_NODE_0_CPUS="0-27"
    echo "Running in TEST mode with CPUs 0-27"
else
    # Production mode: NUMA node 0 physical cores and hyperthreads
    NUMA_NODE_0_CPUS="0-47,96-143"
    echo "Running in PRODUCTION mode with CPUs 0-47,96-143"
fi

# Get project name and verify image exists
PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
IMAGE_NAME="${PROJECT_NAME}-${SERVICE_NAME}"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "RAM-Constrained OOC Benchmark Container"
echo "═══════════════════════════════════════════════════════════════════"
echo "Service:           $SERVICE_NAME"
echo "Dataset:           $DATASET_NAME"
if [ "$RAM_PERCENT" = "absolute" ]; then
    echo "RAM Allocation:    ${RAM_ABSOLUTE_GB}GB (absolute)"
else
    echo "RAM Allocation:    ${RAM_PERCENT}% (of estimated working memory)"
fi
echo "Allocated Memory:  ${WORKING_MEMORY_GB}GB"
echo "Image:             $IMAGE_NAME"
echo "NUMA CPUs:         ${NUMA_NODE_0_CPUS:-disabled}"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Verify image exists
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo "Error: Docker image '$IMAGE_NAME' not found"
    echo "Build it first with: docker compose build $SERVICE_NAME"
    exit 1
fi

# Create unique container name with timestamp
TIMESTAMP=$(date +%s)
if [ "$RAM_PERCENT" = "absolute" ]; then
    CONTAINER_NAME="${SERVICE_NAME}_${DATASET_NAME}_${RAM_ABSOLUTE_GB}gb_${TIMESTAMP}"
else
    CONTAINER_NAME="${SERVICE_NAME}_${DATASET_NAME}_${RAM_PERCENT}pct_${TIMESTAMP}"
fi

echo "Container name: $CONTAINER_NAME"
echo ""

# Launch container with memory constraint
echo "Launching container with memory limit ${WORKING_MEMORY_GB}GB..."

if [ "$NO_NUMA" = true ]; then
    docker run -d \
        --name "$CONTAINER_NAME" \
        --memory "${WORKING_MEMORY_GB}g" \
        --memory-swap "${WORKING_MEMORY_GB}g" \
        --privileged \
        -v "$(pwd)/datasets":/datasets \
        -v "$(pwd)/systems":/systems \
        -v "$(pwd)/results":/results \
        -v "$(pwd)/extra_space":/extra_space \
        -v "$(pwd)/scripts":/scripts \
        "$IMAGE_NAME" \
        /bin/bash -c "
            echo '============================================='
            echo 'Container Configuration:'
            echo '============================================='
            echo 'Dataset: $DATASET_NAME'
            echo 'RAM Allocation: ${WORKING_MEMORY_GB}GB (${RAM_PERCENT}%)'
            echo ''
            echo 'Memory Info:'
            grep 'MemTotal' /proc/meminfo
            echo ''
            echo 'To run benchmarks:'
            echo '  docker exec -it $CONTAINER_NAME python /scripts/${SERVICE_NAME}/${SERVICE_NAME}.py \\\'
            echo '    --dataset=$DATASET_NAME --ram-percent=$RAM_PERCENT'
            echo ''
            sleep infinity
        "
else
    docker run -d \
        --name "$CONTAINER_NAME" \
        --memory "${WORKING_MEMORY_GB}g" \
        --memory-swap "${WORKING_MEMORY_GB}g" \
        --privileged \
        --cpuset-cpus="$NUMA_NODE_0_CPUS" \
        --cpuset-mems="0" \
        -v "$(pwd)/datasets":/datasets \
        -v "$(pwd)/systems":/systems \
        -v "$(pwd)/results":/results \
        -v "$(pwd)/extra_space":/extra_space \
        -v "$(pwd)/scripts":/scripts \
        "$IMAGE_NAME" \
        /bin/bash -c "
            echo '============================================='
            echo 'Container Configuration:'
            echo '============================================='
            echo 'Dataset: $DATASET_NAME'
            echo 'RAM Allocation: ${WORKING_MEMORY_GB}GB (${RAM_PERCENT}%)'
            echo 'NUMA CPUs: $NUMA_NODE_0_CPUS'
            echo ''
            echo 'Memory Info:'
            grep 'MemTotal' /proc/meminfo
            echo ''
            echo 'CPU Info:'
            grep 'Cpus_allowed_list' /proc/self/status
            echo ''
            echo 'To run benchmarks:'
            echo '  docker exec -it $CONTAINER_NAME python /scripts/${SERVICE_NAME}/${SERVICE_NAME}.py \\\'
            echo '    --dataset=$DATASET_NAME --ram-percent=$RAM_PERCENT'
            echo ''
            sleep infinity
        "
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Container launched successfully"
    echo ""
    echo "Container ID: $CONTAINER_NAME"
    echo ""
    echo "Quick reference:"
    echo "  Connect:       docker exec -it $CONTAINER_NAME bash"
    echo "  Run benchmark: docker exec -it $CONTAINER_NAME python /scripts/${SERVICE_NAME}/${SERVICE_NAME}.py --dataset=$DATASET_NAME --ram-percent=$RAM_PERCENT"
    echo "  Stop:          docker stop $CONTAINER_NAME"
    echo "  Remove:        docker rm $CONTAINER_NAME"
    echo "  List running:  docker ps | grep $SERVICE_NAME"
    echo ""
else
    echo "Error: Failed to launch container"
    exit 1
fi
