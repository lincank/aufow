#!/bin/sh
# Author: Guimin
#
# Update routes reloated files from server
# cron job:
# 00 11 * * * root /etc/openvpn/update_files.sh 2>&1 >> /tmp/update_files.log
# 
# Works for ash shell, OpenWrt built-in

DIR='/etc/openvpn/'
DOMAIN='http://www.everants.com/'

# ash style array in this way
FILES="custom_routes gfwdomains.conf except_routes gfw_routes";

echo "*********** routes update script starts ***********"
echo "[`date`]"
for file in $FILES
do
	echo "---> Updating file: ${file} "
	cmd="wget -P ${DIR} -N ${DOMAIN}${file}"
	echo "Executing: ${cmd}"
	`${cmd}`
done

echo "*********** routes update script ends ***********"
