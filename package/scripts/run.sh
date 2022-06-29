echo "*****************************************"
echo "running on $DOCKER_HOST"
echo "*****************************************"

if [ -z "$DOCKER_HOST" ]; then
   DOCKER_TOOL=docker
else
   DOCKER_TOOL=docker-17.04.0
fi

# set the definitions
INSTANCE=uva-dibs
NAMESPACE=uvadave

ENV_FILE=/tmp/env.$$

echo "BASE_URL=http://docker1.lib.virginia.edu:8080" >> ${ENV_FILE}
echo "DATABASE_FILE=/dibs/data/dibs.db" >> ${ENV_FILE}
echo "MANIFEST_DIR=/dibs/data/manifests" >> ${ENV_FILE}
echo "PROCESS_DIR=/dibs/data/processing" >> ${ENV_FILE}
echo "THUMBNAILS_DIR=/dibs/data/thumbnails" >> ${ENV_FILE}
echo "IIIF_BASE_URL=https://iiif-dev.internal.lib.virginia.edu" >> ${ENV_FILE}
echo "MAIL_HOST=out.mail.virginia.edu" >> ${ENV_FILE}
echo "MAIL_PORT=25" >> ${ENV_FILE}
echo "MAIL_SENDER=dibs-dev@virginia.edu" >> ${ENV_FILE}
echo "RELOAN_WAIT_TIME=30" >> ${ENV_FILE}
echo "RUN_MODE=verbose" >> ${ENV_FILE}
echo "APACHE_ULIMIT_MAX_FILES=true" >> ${ENV_FILE}

$DOCKER_TOOL run -d -p 8080:80 --rm --log-opt tag=$INSTANCE --env-file ${ENV_FILE} --name $INSTANCE $NAMESPACE/$INSTANCE
