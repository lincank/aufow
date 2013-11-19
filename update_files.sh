#!/bin/sh
# Author: Guimin
#
# Update routes reloated files from server
# cron job:
# 00 11 * * * root /etc/openvpn/update_files.sh

DIR='/etc/openvpn/'
DOMAIN='http://www.everants.com/'
FILES=('custom_routes' 'gfwdomains.conf' 'except_routes' 'gfw_routes');

for file in ${FILES[@]}
do
	echo "Updating file: ${file}"
	cmd="wget -P ${DIR} -S ${DOMAIN}${file}"
	echo "Executing: ${cmd}"
	`${cmd}`
done
