#!/usr/bin/env bash

# add fake data
admin/load-mock-data
admin/people-manager add role="library" uname="dibsuser"

# ensure permissions
admin/set-server-permissions --owner www-data --group www-data

#
# end of file
#
