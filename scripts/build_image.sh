#
# Builds a Docker image.
#
# Environment variables:
#
#   CONTAINER_REGISTRY - The hostname of your container registry.
#   VERSION - The version number to tag the images with.
#
# Parameters:
#
#   1 - The path to the code for the image and the name of the image.
#
# Usage:
#
#       ./scripts/build-image.sh <image-name>
#
# Example command line usage:
#
#       ./scripts/build-image.sh service
#

set -u # or set -o nounset
: "$1"
: "$CONTAINER_REGISTRY"
: "$VERSION"

export APP=$1
# common Dockerfile used by all services
DF=./services/Dockerfile

# except if app folder has its own Dockerfile, then use it instead
APPDF=./services/${APP}/Dockerfile
if test -a ${APPDF}
then
    DF=${APPDF}
fi

VERSION_TAG="${VERSION_MAJOR:-1}.${VERSION_MINOR:-0}.${VERSION_PATCH:-0}.${BUILD_NUMBER}"
docker build -t $CONTAINER_REGISTRY/$APP:$VERSION  \
             -t $CONTAINER_REGISTRY/$APP:latest \
             --build-arg VERSION_MAJOR=${VERSION_MAJOR:-1} \
             --build-arg VERSION_MINOR=${VERSION_MINOR:-0} \
             --build-arg VERSION_PATCH=${VERSION_PATCH:-0} \
             --build-arg BUILD_NUMBER=$BUILD_NUMBER \
             --build-arg BUILD_DATE="$BUILD_DATE" \
             --build-arg BUILD_COMMIT=$BUILD_COMMIT \
             --build-arg BUILD_BRANCH=$BUILD_BRANCH \
             --build-arg app=fitnessclub \
             -t ${APP}:${VERSION_TAG} \             
             --file ${DF} \
             --build-arg app=${APP} .
