echo "*****************************************"
echo "running on $DOCKER_HOST"
echo "*****************************************"

if [ -z "$DOCKER_HOST" ]; then
   DOCKER_TOOL=docker
else
   DOCKER_TOOL=docker-17.04.0
fi

~/Sandboxes/terraform-infrastructure/scripts/ecr-authenticate.ksh

# set the definitions
INSTANCE=uva-dibs
NAMESPACE=115119339709.dkr.ecr.us-east-1.amazonaws.com/uvalib
TAG=latest

if [ $# -eq 1 ]; then
  TAG=$1
fi

IMAGE=$NAMESPACE/$INSTANCE:$TAG

echo "Using $IMAGE..."
$DOCKER_TOOL run -ti -p 8080:80 --rm $IMAGE /bin/bash -l
