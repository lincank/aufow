#!/bin/sh
# Author: Guimin
#
# Update routes reloated files from server
# cron job:
# 00 11 * * * root /etc/openvpn/update_files.sh

DIR=/etc/openvpn/

FILES=(custom_routes gfwdomains.conf except_routes gfw_routes)

for file in FILES
do
	echo "Updating file: ${file}"
	wget -P ${DIR} -N ${DIR}${file}	
done
