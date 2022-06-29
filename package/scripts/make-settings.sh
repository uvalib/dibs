#!/usr/bin/env bash

# rendering mechanism
render_template() {
  eval "echo \"$(cat ${1})\""
}

# generate the settings file from the template
render_template settings.ini.template > settings.ini
chown www-data:www-data settings.ini

#
# end of file
#
