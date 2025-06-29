#!/bin/bash

# Docker build script for Employment Match API
# Options for different build types

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE     Build type: full, lightweight, or production"
    echo "  -n, --name NAME     Image name (default: employment-match)"
    echo "  -v, --version VER   Image version/tag (default: latest)"
    echo "  --no-cache          Build without cache"
    echo "  --push              Push image to registry after build"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Build types:"
    echo "  full        - Full build with all ML models (largest size)"
    echo "  lightweight - Development build without heavy ML models"
    echo "  production  - Optimized production build"
    echo ""
    echo "Examples:"
    echo "  $0 -t lightweight -n my-app -v dev"
    echo "  $0 -t production --no-cache"
    echo "  $0 -t full --push"
}

# Default values
BUILD_TYPE="production"
IMAGE_NAME="employment-match"
IMAGE_VERSION="latest"
NO_CACHE=""
PUSH_IMAGE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -v|--version)
            IMAGE_VERSION="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE="true"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate build type
case $BUILD_TYPE in
    full|lightweight|production)
        ;;
    *)
        print_error "Invalid build type: $BUILD_TYPE"
        show_usage
        exit 1
        ;;
esac

# Set Dockerfile based on build type
case $BUILD_TYPE in
    full)
        DOCKERFILE="Dockerfile"
        print_status "Building full image with all ML models..."
        ;;
    lightweight)
        DOCKERFILE="Dockerfile.lightweight"
        print_status "Building lightweight development image..."
        ;;
    production)
        DOCKERFILE="Dockerfile"
        print_status "Building optimized production image..."
        ;;
esac

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    print_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi

# Build the image
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_VERSION}"
print_status "Building image: $FULL_IMAGE_NAME"
print_status "Using Dockerfile: $DOCKERFILE"

# Show image size before build
print_status "Current Docker images:"
docker images | grep "$IMAGE_NAME" || print_warning "No existing images found for $IMAGE_NAME"

# Build command
BUILD_CMD="docker build $NO_CACHE -f $DOCKERFILE -t $FULL_IMAGE_NAME ."
print_status "Running: $BUILD_CMD"

# Execute build
if eval $BUILD_CMD; then
    print_status "Build completed successfully!"
    
    # Show image size after build
    print_status "New image size:"
    docker images | grep "$IMAGE_NAME" | grep "$IMAGE_VERSION"
    
    # Show total image size
    TOTAL_SIZE=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "$IMAGE_NAME" | awk '{sum+=$3} END {print sum}')
    print_status "Total size for $IMAGE_NAME images: $TOTAL_SIZE"
    
    # Push if requested
    if [ "$PUSH_IMAGE" = "true" ]; then
        print_status "Pushing image to registry..."
        docker push "$FULL_IMAGE_NAME"
    fi
    
    print_status "Build completed! You can run the image with:"
    echo "  docker run -p 8080:8080 $FULL_IMAGE_NAME"
    
else
    print_error "Build failed!"
    exit 1
fi 