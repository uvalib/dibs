#!/usr/bin/env bash

# generate the settings file
scripts/make-settings.sh

# temp only
#scripts/add-fake-data.sh
#scripts/add-admins.sh

# redirect to standout/stderr
ln -sf /proc/$$/fd/1 /var/log/apache2/access.log
ln -sf /proc/$$/fd/2 /var/log/apache2/error.log

# start Apache
/usr/sbin/apache2ctl -DFOREGROUND

#
# end of file
#
