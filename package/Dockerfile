#
# build the target application
#
FROM public.ecr.aws/ubuntu/ubuntu:23.10

# for tzdata package
ENV DEBIAN_FRONTEND=noninteractive

# update the package manager to use the old release repos
# also attempt to thwart some AWS code pipeline behavior to prevent this
RUN cat /etc/apt/sources.list | sed -e 's&ports.ubuntu.com/ubuntu-ports&old-releases.ubuntu.com/ubuntu&g' | sed -e 's/security.ubuntu.com/old-releases.ubuntu.com/g' | sed -e 's/archive.ubuntu.com/old-releases.ubuntu.com/g' > /tmp/sources.list && mv /tmp/sources.list /etc/apt/sources.list

# update the packages
RUN apt -y update && apt -y upgrade && apt -y install tzdata apache2 vim python3-pip && apt -y install apache2-dev apache2-utils libapache2-mod-wsgi-py3

# set the timezone appropriatly
ENV TZ=EST5EDT
RUN cp /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install the application requirements
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt --break-system-packages

# Specify home 
ENV APP_HOME=/dibs
WORKDIR $APP_HOME

# .profile
COPY package/data/container_bash_profile /root/.profile

# port and run command
EXPOSE 80
CMD ["scripts/entry.sh"]

# install the application
ADD . $APP_HOME
RUN chown -R www-data:www-data $APP_HOME

# configuration files
COPY package/config/settings.ini.template $APP_HOME/settings.ini.template
COPY package/scripts/*.sh $APP_HOME/scripts/

# Apache configuration
COPY package/config/dibs.conf /etc/apache2/conf-available/dibs.conf
RUN ln -s /etc/apache2/conf-available/dibs.conf /etc/apache2/conf-enabled
RUN rm /etc/apache2/sites-available/*.conf

# Add the build tag
ARG BUILD_TAG
RUN test -n "$BUILD_TAG" && touch $APP_HOME/buildtag.build-$BUILD_TAG || touch $APP_HOME/buildtag.build-0

#
# end of file
#
