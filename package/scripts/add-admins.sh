#!/usr/bin/env bash

# add the admins
admin/people-manager add role="library" uname="rmg6f"   # Bob Gartland
admin/people-manager add role="library" uname="rh9ec"   # Bob Haschart
admin/people-manager add role="library" uname="cm9kg"   # Caleb Mechem
admin/people-manager add role="library" uname="cma4u"   # Carla Arton
admin/people-manager add role="library" uname="dpg3k"   # Dave Goldstein
admin/people-manager add role="library" uname="jlk4p"   # Jack Kelly
admin/people-manager add role="library" uname="md5wz"   # Mike Durbin
admin/people-manager add role="library" uname="mhw8m"   # Mark Witteman
admin/people-manager add role="library" uname="naw4t"   # Nestor Walker
admin/people-manager add role="library" uname="rar6u"   # Renee Reighart

# ensure permissions
admin/set-server-permissions --owner www-data --group www-data

#
# end of file
#
