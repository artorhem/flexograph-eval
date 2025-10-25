#!/bin/bash

# Parse arguments
TEST_MODE=false
SERVICE_NAME=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --test)
      TEST_MODE=true
      shift
      ;;
    *)
      SERVICE_NAME="$1"
      shift
      ;;
  esac
done

# Check if service name is provided
if [ -z "$SERVICE_NAME" ]; then
  echo "Usage: $0 [--test] <service_name>"
  echo "Example: $0 gapbs"
  echo "Example: $0 --test gapbs"
  echo "Available services: gapbs, gemini, ligra, galois, blaze, graphchi, xstream, lumos, gridgraph, margraphita"
  exit 1
fi

# NUMA settings based on test mode
if [ "$TEST_MODE" = true ]; then
  # Test mode: use CPUs 0-27
  NUMA_NODE_0_CPUS="0-27"
  echo "Running in TEST mode with CPUs 0-27"
else
  # Production mode: NUMA node 0 physical cores and hyperthreads
  # Adjust these based on Kitkat's NUMA topology
  NUMA_NODE_0_CPUS="0-47,96-143"
fi

# Verify that the service exists in docker-compose.yml
if ! docker compose config --services | grep -q "^${SERVICE_NAME}$"; then
  echo "Error: Service '${SERVICE_NAME}' not found in docker-compose.yml"
  echo "Available services:"
  docker compose config --services
  exit 1
fi

# Build the service using docker compose if not already built
echo "Building service using docker compose: ${SERVICE_NAME}"
docker compose build "${SERVICE_NAME}"
if [ $? -ne 0 ]; then
  echo "Error: Failed to build service ${SERVICE_NAME}"
  exit 1
fi

# Get the project name (directory name by default)
PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
echo "Project name is ${PROJECT_NAME} and service name is ${SERVICE_NAME}"

# Construct the image name using docker compose naming convention
IMAGE_NAME="${PROJECT_NAME}-${SERVICE_NAME}"

# Verify the image exists
if ! docker images | grep -q "${IMAGE_NAME}"; then
  echo "Error: Image ${IMAGE_NAME} not found after build"
  exit 1
fi

echo "Launching service: ${SERVICE_NAME} in detached mode"
echo "Using image: ${IMAGE_NAME}"
echo "NUMA settings: CPUs=${NUMA_NODE_0_CPUS}, Memory node=0"
echo ""

# Launch the service in detached mode with NUMA settings
docker run -d \
  --name "${SERVICE_NAME}" \
  --privileged \
  --cpuset-mems="0" \
  --cpuset-cpus="$NUMA_NODE_0_CPUS" \
  -v "$(pwd)/datasets":/datasets \
  -v "$(pwd)/systems":/systems \
  -v "$(pwd)/results":/results \
  -v "$(pwd)/extra_space":/extra_space \
  "$IMAGE_NAME" \
  /bin/bash -c "
      echo 'Verifying configuration:'
      grep 'Cpus_allowed_list' /proc/self/status
      grep 'Mems_allowed_list' /proc/self/status
      echo ''

      sleep infinity
    "

if [ $? -eq 0 ]; then
  echo "✓ Container '${SERVICE_NAME}' launched successfully"
  echo ""
  echo "To connect to the container:"
  echo "  docker exec -it ${SERVICE_NAME} /bin/bash"
  echo ""
  echo "To run the benchmark script:"
  echo "  docker exec -it ${SERVICE_NAME} python /scripts/${SERVICE_NAME}/${SERVICE_NAME}.py"
  echo ""
  echo "To stop the container:"
  echo "  docker stop ${SERVICE_NAME}"
  echo ""
  echo "To remove the container:"
  echo "  docker rm ${SERVICE_NAME}"
else
  echo "Error: Failed to launch container"
  exit 1
fi
