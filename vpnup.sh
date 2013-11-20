#!/bin/sh

set -x
export PATH="/bin:/sbin:/usr/sbin:/usr/bin"

LOG='/tmp/autoddvpn.log'
LOCK='/tmp/autoddvpn.lock'
PID=$$
EXROUTEDIR='/jffs/exroute.d'
INFO="[INFO#${PID}]"
DEBUG="[DEBUG#${PID}]"
ERROR="[ERROR#${PID}]"
PWD='/etc/openvpn'

echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") vpnup.sh started" >> $LOG
for i in 1 2 3 4 5 6
do
	if [ -f $LOCK ]; then
		echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") got $LOCK , sleep 10 secs. #$i/6" >> $LOG
		sleep 10
	else
		break
	fi
done

if [ -f $LOCK ]; then
   echo "$ERROR $(date "+%d/%b/%Y:%H:%M:%S") still got $LOCK , I'm aborted. Fix me." >> $LOG
   exit 0
fi
#else
#	echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") $LOCK was released, let's continue." >> $LOG
#fi

# create the lock
echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") vpnup" >> $LOCK
	
	

OLDGW=$(route -n | grep ^0.0.0.0 | awk '{print $2}')

case $1 in
	"pptp")
		case "$(nvram get router_name)" in
			"tomato")
				echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") router type: tomato" >> $LOG
				VPNSRV=$(nvram get pptpd_client_srvip)
				VPNSRVSUB=$(nvram get pptpd_client_srvsub)
				PPTPDEV=$(nvram get pptp_client_iface)
				VPNGW=$(nvram get pptp_client_gateway)
				;;
			*)
				# assume it to be a DD-WRT
				echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") router type: DD-WRT" >> $LOG
				VPNSRV=$(nvram get pptpd_client_srvip)
				VPNSRVSUB=$(nvram get pptpd_client_srvsub)
				PPTPDEV=$(route -n | grep ^${VPNSRVSUB%.[0-9]*} | awk '{print $NF}' | head -n 1)
				VPNGW=$(ifconfig $PPTPDEV | grep -Eo "P-t-P:([0-9.]+)" | cut -d: -f2)
				VPNUPCUSTOM='/jffs/pptp/vpnup_custom' 
				;;
		esac
		;;
	"openvpn")
		VPNSRV=$(nvram get openvpncl_remoteip)
		#OPENVPNSRVSUB=$(nvram get OPENVPNd_client_srvsub)
		#OPENVPNDEV=$(route | grep ^$OPENVPNSRVSUB | awk '{print $NF}')
		OPENVPNDEV='tun0'
		VPNGW=$(ifconfig $OPENVPNDEV | grep -Eo "P-t-P:([0-9.]+)" | cut -d: -f2)
		VPNUPCUSTOM='/jffs/openvpn/vpnup_custom'
		;;
	*)
		echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") unknown vpnup.sh parameter,quit." >> $LOCK
		exit 1
esac

if [ $OLDGW == '' ]; then
	echo "$ERROR OLDGW is empty, is the WAN disconnected?" >> $LOG
	exit 0
else
	echo "$INFO OLDGW is $OLDGW" 
fi

#route add -host $VPNSRV gw $OLDGW
#echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") delete default gw $OLDGW"  >> $LOG
#route del default gw $OLDGW

#echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") add default gw $VPNGW"  >> $LOG
#route add default gw $VPNGW

export VPNGW=$VPNGW
export OLDGW=$OLDGW
export PWD=$PWD


# BASIC_ROUTES="$PWD/basic_routes"
# GFW_ROUTES="$PWD/gfw_routes"
# CUSTOM_ROUTES="$PWD/custom_routes"
# EXCEPT_ROUTES="$PWD/except_routes"
ROUTES="basic_routes gfw_routes custom_routes fixed_ip_routes"

for route in $ROUTES
do
	echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") adding ${route}, this may take a while." >> $LOG
	grep ^route $PWD/$route  | /bin/sh -x
done
##### begin batch route #####
# echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") adding the basic routes, this may take a while." >> $LOG
# grep ^route $BASIC_ROUTES  | /bin/sh -x
# 
# echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") adding the gfw routes, this may take a while." >> $LOG
# grep ^route $GFW_ROUTES  | /bin/sh -x
# 
# echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") adding the custom routes, this may take a while." >> $LOG
# grep ^route $CUSTOM_ROUTES  | /bin/sh -x
# 
# echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") adding the except routes, this may take a while." >> $LOG
# grep ^route $EXCEPT_ROUTES  | /bin/sh -x

##### end batch route #####


# echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") loading vpnup_custom if available" >> $LOG

#grep ^route $VPNUPCUSTOM  | /bin/sh -x

# prepare for the exceptional routes, see http://code.google.com/p/autoddvpn/issues/detail?id=7
# echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") preparing the exceptional routes" >> $LOG


echo "$INFO static routes added"
echo "$INFO $(date "+%d/%b/%Y:%H:%M:%S") vpnup.sh ended" >> $LOG
# release the lock
rm -f $LOCK
