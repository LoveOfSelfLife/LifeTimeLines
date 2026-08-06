# Version Management System

This document describes how to use the version management system for the Active Friends Club application.

## Overview

The version system provides:
- Version display in the navbar (e.g., "Active Friends Club 1.0")
- Detailed version and build information on the About page
- Support for development and production builds
- Integration with Docker builds and CI/CD pipelines

## Files

- `version.py` - Central version management
- `build-version.sh` - Build script with version injection
- `Dockerfile.version-example` - Example Docker modifications

## Version Format

- **Development**: `1.0.0-dev` 
- **Production**: `1.0.0.123` (where 123 is the build number)

## Environment Variables

The system uses these environment variables for build-time version injection:

| Variable | Description | Default |
|----------|-------------|---------|
| `BUILD_NUMBER` | Build number from CI/CD | `dev` |
| `BUILD_DATE` | Build timestamp | Current timestamp |
| `BUILD_COMMIT` | Git commit hash | `unknown` |
| `BUILD_BRANCH` | Git branch name | `development` |

## Local Development

In development mode (no environment variables set):
- Version shows as `1.0.0-dev`
- Build info shows development defaults
- "Development Build" badge appears on About page

## Production Deployment

### Docker Build Example

```bash
# Set version information
export BUILD_NUMBER=$(date +%Y%m%d%H%M%S)
export BUILD_DATE=$(date -u '+%Y-%m-%d %H:%M:%S UTC')  
export BUILD_COMMIT=$(git rev-parse HEAD)
export BUILD_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Build with version info
docker build \
  --build-arg VERSION_MAJOR=1 \
  --build-arg VERSION_MINOR=0 \
  --build-arg VERSION_PATCH=0 \
  --build-arg BUILD_NUMBER=$BUILD_NUMBER \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg BUILD_COMMIT=$BUILD_COMMIT \
  --build-arg BUILD_BRANCH=$BUILD_BRANCH \
  --build-arg app=fitnessclub \
  -t active-friends-club:1.0.0.$BUILD_NUMBER \
  .
```

### GitHub Actions Example

```yaml
- name: Get build information
  run: |
    echo "BUILD_DATE=$(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> $GITHUB_ENV
    echo "BUILD_COMMIT=${GITHUB_SHA}" >> $GITHUB_ENV  
    echo "BUILD_BRANCH=${GITHUB_REF#refs/heads/}" >> $GITHUB_ENV
    echo "BUILD_NUMBER=${GITHUB_RUN_NUMBER}" >> $GITHUB_ENV

- name: Build Docker image
  run: |
    docker build \
      --build-arg BUILD_NUMBER=$BUILD_NUMBER \
      --build-arg BUILD_DATE="$BUILD_DATE" \
      --build-arg BUILD_COMMIT=$BUILD_COMMIT \
      --build-arg BUILD_BRANCH=$BUILD_BRANCH \
      --build-arg app=fitnessclub \
      -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:1.0.0.$BUILD_NUMBER \
      -f services/Dockerfile .
```

## Updating Version Numbers

To update the major/minor version numbers:
1. Edit `version.py`
2. Update `VERSION_MAJOR`, `VERSION_MINOR`, or `VERSION_PATCH`
3. Build numbers are automatically assigned by CI/CD

## Viewing Version Information

- **Navbar**: Shows short version (e.g., "Active Friends Club 1.0")
- **About Page**: Shows complete version and build details
- **Footer**: Shows full version string

The About page includes:
- Full version string
- Build number
- Build date and time
- Git commit hash (first 8 characters)
- Git branch
- Development build indicator (if applicable)