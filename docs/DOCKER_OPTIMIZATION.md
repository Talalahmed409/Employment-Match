# Docker Image Size Optimization Guide

## Why Was the Docker Image 10GB?

The original Docker image was 10GB due to several factors:

### 1. **Heavy ML Libraries**

- **PyTorch**: ~2-3GB (with CUDA support)
- **TorchVision**: ~1GB
- **TorchAudio**: ~500MB
- **Transformers**: ~2-3GB
- **Sentence-Transformers**: ~1GB

### 2. **Build Dependencies**

- `build-essential` package adds significant size
- Development tools not needed at runtime

### 3. **Model Downloads**

- Sentence transformer models cached during build
- Large model files stored in image layers

### 4. **Generated Data**

- ESCO embeddings (~20MB)
- Pre-processed skill data

## Optimization Strategies Applied

### 1. **Multi-Stage Build**

```dockerfile
# Builder stage with build dependencies
FROM python:3.9-slim as builder
# Install build tools, create venv, install packages

# Final stage with only runtime dependencies
FROM python:3.9-slim
# Copy only the virtual environment
COPY --from=builder /opt/venv /opt/venv
```

### 2. **CPU-Only PyTorch**

```txt
# Use CPU-only versions (saves ~3-4GB)
torch>=2.1.0+cpu
torchvision>=0.16.0+cpu
torchaudio>=2.1.0+cpu
--extra-index-url https://download.pytorch.org/whl/cpu
```

### 3. **Optimized .dockerignore**

- Excludes unnecessary files from build context
- Prevents copying of development files, logs, cache

### 4. **Cleanup Commands**

```dockerfile
# Remove build tools and cache
RUN pip uninstall -y setuptools pip && \
    rm -rf /root/.cache/pip
```

## Build Options

### 1. **Production Build** (Recommended)

```bash
./build-docker.sh -t production
```

- **Size**: ~3-4GB
- **Features**: All ML capabilities
- **Use case**: Production deployment

### 2. **Lightweight Development Build**

```bash
./build-docker.sh -t lightweight
```

- **Size**: ~500MB-1GB
- **Features**: Basic API without ML models
- **Use case**: Development and testing

### 3. **Full Build** (Original)

```bash
./build-docker.sh -t full
```

- **Size**: ~8-10GB
- **Features**: Everything including GPU support
- **Use case**: When you need GPU acceleration

## Usage Examples

### Build and Run Production Image

```bash
# Build optimized production image
./build-docker.sh -t production -n my-app -v 1.0

# Run the container
docker run -p 8080:8080 my-app:1.0
```

### Development with Docker Compose

```bash
# Use lightweight development build
docker-compose --profile dev up api-dev

# Or build and run production
docker-compose up api
```

### Check Image Sizes

```bash
# List all images and their sizes
docker images | grep employment-match

# Get detailed size information
docker system df
```

## Size Comparison

| Build Type  | Size       | Features      | Use Case              |
| ----------- | ---------- | ------------- | --------------------- |
| Original    | ~10GB      | Full ML + GPU | GPU development       |
| Production  | ~3-4GB     | Full ML (CPU) | Production deployment |
| Lightweight | ~500MB-1GB | Basic API     | Development/testing   |

## Additional Optimizations

### 1. **Use Alpine Linux Base** (Alternative)

```dockerfile
FROM python:3.9-alpine
# Even smaller base image (~100MB vs ~400MB)
# But may have compatibility issues with some packages
```

### 2. **Runtime Model Loading**

- Load ML models at runtime instead of build time
- Use volume mounts for model storage
- Implement lazy loading in the application

### 3. **Model Compression**

- Use quantized models
- Implement model pruning
- Use smaller model variants

### 4. **Layer Optimization**

```dockerfile
# Combine RUN commands to reduce layers
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
```

## Troubleshooting

### Build Fails with CPU PyTorch

```bash
# If you need GPU support, use the full build
./build-docker.sh -t full
```

### Model Loading Issues

```bash
# Check if models are properly downloaded
docker run --rm your-image python -c "import torch; print(torch.__version__)"
```

### Memory Issues

```bash
# Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory
```

## Best Practices

1. **Use Multi-Stage Builds**: Separate build and runtime environments
2. **Minimize Layers**: Combine RUN commands where possible
3. **Use .dockerignore**: Exclude unnecessary files
4. **Choose Right Base Image**: Use slim variants when possible
5. **Clean Up**: Remove build dependencies and cache
6. **Version Pinning**: Use specific versions for reproducibility
7. **Security Scanning**: Regularly scan images for vulnerabilities

## Monitoring Image Size

```bash
# Track image size over time
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Analyze image layers
docker history your-image-name

# Find largest files in image
docker run --rm your-image du -h / | sort -hr | head -20
```
