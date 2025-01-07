#
# build the target application
#
FROM public.ecr.aws/ubuntu/ubuntu:25.04

# for tzdata package
ENV DEBIAN_FRONTEND=noninteractive

# update the packages
RUN apt -y update && apt -y upgrade && apt -y install tzdata apache2 vim python3-pip && apt -y install apache2-dev apache2-utils libapache2-mod-wsgi-py3

# set the timezone appropriatly
ENV TZ=America/New_York
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
