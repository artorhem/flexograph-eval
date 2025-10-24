#!/bin/bash
# Build script for flexograph-eval base image

set -e

IMAGE_NAME="flexograph-eval-base"
IMAGE_TAG="latest"
DOCKERFILE="containers/base.Dockerfile"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Flexograph Eval Base Image${NC}"
echo "========================================"
echo ""

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}Error: Dockerfile not found at $DOCKERFILE${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}Building image: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
docker build -f "$DOCKERFILE" -t "${IMAGE_NAME}:${IMAGE_TAG}" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Base image built successfully!${NC}"
    echo ""
    echo "Image details:"
    docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Test the image: docker run --rm -it ${IMAGE_NAME}:${IMAGE_TAG} bash"
    echo "2. Push to registry (optional):"
    echo "   docker tag ${IMAGE_NAME}:${IMAGE_TAG} yourusername/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "   docker push yourusername/${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "3. Update your Dockerfiles to use: FROM ${IMAGE_NAME}:${IMAGE_TAG}"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
