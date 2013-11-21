
## Aufow -- Autoddvpn for OpenWrt

此工程主要贡献来自于[autoddvpn](https://code.google.com/p/autoddvpn/)及[openwrt-smarthosts-autoddvpn](http://code.google.com/p/openwrt-smarthosts-autoddvpn/)。主要在OpenWrt路由上实现autoddvpn的效果。

本来已经在ddwrt路由上搭好audoddvpn，在[这里](https://github.com/lincank/autoddvpn)可以找到一些常用的脚本。不过最近从ddwrt转移到OpenWrt上，因为发现OpenWrt更加灵活，可玩度更高一些。此工程是在audoddwrt现有的代码及脚本基础上移植并应用在OpenWrt+Openvpn上的。

### 效果
实现无痛翻墙并支持翻墙网站及ip的定期自动更新。

### 条件
本方案在以下条件下测试通过：

* OpenWrt 12.09
* Openvpn

[openwrt-smarthosts-autoddvpn](http://code.google.com/p/openwrt-smarthosts-autoddvpn/)就是基于OpenWrt+PPTP的，

### 效果
GFW的手段主要手段及解决办法:

* DNS污染：利用OpenWrt的dnsmasq来提供dns服务，并指定使用Google DNS来查询这些受污染的网址
* 连接重置：通过openvpn来访问这些被封的ip

### 生成routes
openvpn启动后会运行`vpnup.sh`脚本来加载需要通过vpn访问的ip，关闭时通过`vpndown.sh`来从路由表中移除这些ip。

`vpnup.sh`会用到以下4个文件，确保这几个文件在`vpnup.sh`脚本所定义的`PWD`目录下。

#### 静态路由
* `basic_routes`: 一些最基本的ip，如Google DNS等，这个文件基本固定不变。
* `gfw_routes`: 从`http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt`上获取的被GFW和谐掉的ip
* `custom_routes`: 从自定义的`custom_domains`文件的域名中解析出来的ip
* `except_routes`: 从自定义的`except_domains`文件的域名中解析出来的ip，这里指定某些特定的ip不通过vpn。
* `fixed_ip_routes`: 固定IP的网站(在`fixed_ip_domains`中定义的)的ip地址。

#### dnsmasq配置文件
以下文件在要放在`/etc/dnsmasq.d`文件夹当中，具体见下文。
* `autoddvpn.conf`: 最基本的被DNS污染的网站。
* `fixed_ip_domain.conf`: 由`fixed_ip_domains`的生成的固定网站/ip对。


以上4个文件中，`basic_routes`固定不变，其他3个可以通过以下方法生成：

* 在`custom_domains`里加入你想要通过vpn走的域名
* 在`excep_domains`里加入你不想要通过vpn走的域名
* 运行 `python freeway.py`

> 要有`dnspython`支持，安装运行：`sudo pip install dnspython`



### dnsmasq
把那些被污染的网址，通过Google DNS查询出真实的ip地址，并把这些ip地址放入dnsmasq的配置中。

在dnsmasq配置文件`/etc/dnsmasq.conf`中添加以下代码：

	conf-dir=/etc/dnsmasq.d
	
如果此目录不存在的话，新建一个：

	mkdir /etc/dnsmasq.d
	
把`autoddvpn.conf`及`gfwdomains`放入此文件夹，并重启dnsmasq：

	/etc/init.d/dnsmasq restart
此时你查询返回的就应该是正确的ip地址了lol

#### DNS设置
网络设置中，打开LAN接口设置，可以在`使用自定义DNS服务器`中填入以下：

	199.91.73.222
	8.8.8.8

分别是V2EX和Google的DNS服务器


### openvpn
> **注意**：操作前确保你有足够的空间，一般8M的Flash都足够了，4M的可能就不够，可以插个USB上去

主要安装参考[openwrt官网](http://wiki.openwrt.org/inbox/vpn.howto)

安装

	opkg update
	opkg install openvpn

新建一个文件夹并把所有与openvpn有关的文件都放在这个目录下

	mkdir /mnt/etc/openvpn
>**注意**：也可以在在其他位置，不过与此有关的路径都要做相应的修改

在`/etc/config/network`为openvpn加一个接口

	config interface 'vpn'
    	    option ifname 'tun0'
        	option defaultroute '0'
        	option peerdns '0'
        	option proto 'none'

openvpn的配置在`/mnt/etc/openvpn/openvpn.conf`，具体参考[autoddvpn](http://code.google.com/p/autoddvpn/wiki/OpenVPNManualStartUP)。注意`vpnup.sh`，`vpndown.sh`以及那些key的路径。

	vi /etc/config/openvpn
	
	package openvpn
	config openvpn vpn
        option client 1
        option enabled 1
        option config /mnt/etc/openvpn/openvpn.conf

启动

	/etc/init.d/openvpn start

开机启动

	/etc/init.d/openvpn enable

### 配置防火墙
>**注意**：以下的端口与协议要跟你openvpn配置里的一致，以下用的是openvpn的默认配置：`udp`协议及`1194`端口。

	vi /etc/config/firewall
	
	## 增加以下内容
	config 'include'
        option 'path' '/etc/firewall.user'

	config 'rule'
        option 'target' 'ACCEPT'
        option 'name' 'VPN'
        option 'src' 'wan'
        option 'proto' 'udp'
        option 'dest_port' '1194'

	## 自定义防火墙内容
	vi /etc/firewall.user
	
	## 增加以下内容
	iptables -t nat -A prerouting_wan -p udp --dport 1194 -j ACCEPT
	iptables -A input_wan -p udp --dport 1194 -j ACCEPT

	iptables -I INPUT -i tun+ -j ACCEPT
	iptables -I FORWARD -i tun+ -j ACCEPT
	iptables -I OUTPUT -o tun+ -j ACCEPT
	iptables -I FORWARD -o tun+ -j ACCEPT
	
	## 重启firewall
	/etc/init.d/firewall restart

### 自动更新
`update_files.sh`脚本会从指定网站下载新版本的路由及dnsmasq配置文件。只要在服务器上定时运行`freeway.py`脚本更新以上文件（主要是GFW路由）。这个脚本利用了`wget`的时间戳`--timestamping or -N`，来检查服务器的版本是否比本地的新，如果是的话就下载，不是的话就不下载。

需要根据情况修改路径及网站：

* `DIR`: 这些文件所在路径
* `DOMAIN`: 放这些文件的网址

#### 定期执行
通过Web界面或直接修改`/etc/config/cron`来添加cron任务。如：

	0 11 * * * /etc/openvpn/update_files.sh 

运行`/etc/init.d/cron start`后，会自己生成`vi /etc/crontabs/root`。


启动并让它开机运行

	/etc/init.d/cron start
	/etc/init.d/cron enable

大功告成！😄
### 测试
重启一下路由，运行下面命令看vpn是否工作正常，正常情况下你应该看到它通过的是你VPN的ip，如`10.8.0.1`

	traceroute facebook.com
