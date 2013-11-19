#!/usr/bin/env python

import re
import time
import urllib
import base64
import string
import sys
from threading import Thread
from Queue import Queue
import dns.resolver


class Freeway(object):
    """
    Freeway can make you free from GFW!

    Responsible for generating routes file for autoddvpn script.

    Usage:
        freeway = Freeway()
        freeway.process(args)

    Check available args.
    """

    def __init__(self):
        self.domain_list = None
        self.white_list = []
        self.iplist = []
        self.subnets = []
        self.single_ips = []

    def fetch_from_file(self, path):
        """
        fetch domains from input file
        """
        print("Fetching from %s ..." % path)
        try:
            lines = open(path).readlines()
        except Exception, e:
            print("Failed to fetch from %s: %s" % (path, e))
            return False

        self.domain_list = []
        for line in lines:
            domain_line = line.rstrip()
            if domain_line != '':
                self.domain_list.append(domain_line)

        print("Got %d domains" % len(self.domain_list))
        return True

    def fetch_from_gfwlist(self):
        """
        fetch blocked domains from gfwlist
        """
        gfwlist = 'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt'
        print "fetching gfwList ..."

        try:
            d = urllib.urlopen(gfwlist).read()
        except Exception, e:
            print("Failed to fetch from: %s" % gfwlist)
            print("Make sure you run this script from somewhere GFW is bypassed ...")
            return False

        data = base64.b64decode(d)
        lines = string.split(data, "\n")
        self.domain_list = self.__parse_domains(lines)
        print("Got %d domains" % len(self.domain_list))
        return True

    def digest_ips(self):
        """
        Combine ips with same subnet into one subnet
        """
        all_subnets = {}
        self.subnets = []
        self.single_ips = []
        # extract all subnets
        for ip in self.iplist:
            subnet = self.__get_sutnet(ip)
            if all_subnets.has_key(subnet):
                all_subnets[subnet].append(ip)
            else:
                new_list = [ip]
                all_subnets[subnet] = new_list

        for subnet, subnet_ips in all_subnets.items():
            if len(subnet_ips) > 1:
                self.subnets.append(subnet)
            else:
                self.single_ips.append(subnet_ips[0])

        self.subnets.sort()
        self.single_ips.sort()

    def export(self, path="/tmp/result.txt", format=0):
        """
        export resolved ips to file

        :param format:
         0: format for route command, with subnet and single ips, including `-net` and `-host` options
         1: format for dnsmasq
         2: format for route command, only with `-host` option for all ips
        """

        try:
            out = open(path, 'wa')
        except Exception, e:
            print("Something wrong : %s." % e)

        if format == 0:
            for ip in self.subnets:
                out.write("route add -net %s/24 gw $VPNGW \n" % ip)
            for ip in self.single_ips:
                out.write("route add -host %s gw $VPNGW \n" % ip)
        elif format == 1:
            for domain in self.domain_list:
                out.write('server=/%s/8.8.8.8\n' % domain)
        elif format == 2:
            for ip in self.iplist:
                out.write("route add -host %s gw $OLDGW \n" % ip)
        else:
            print("Invalid format option")
            out.close()
            return

        out.close()
        print("Exported to %s ..." % path)

    def process(self, path=None, thread_num=60, format=0, output="/tmp/result.txt"):
        """
        Main method of this class. Fetch -> resolve -> export
        """
        if path:
            is_succeed = self.fetch_from_file(path)
        else:
            is_succeed = self.fetch_from_gfwlist()

        if not is_succeed:
            print "Error while fetching domains, exit..."
            sys.exit(1)

        self.__multithread_resolve(thread_num)
        self.digest_ips()
        self.export(output, format)

    def generate_gfw_dnsmasq_conf(self, output='gfwdomains.conf'):
        self.fetch_from_gfwlist()
        self.export(path=output, format=1)

    # private methods
    def __is_ip_address(self, hostname=''):
        pat = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
        if re.match(pat, hostname):
            return True
        else:
            return False

    def __parse_domains(self, lines):
        """
        parse domains from gfwlist file
        """
        domain_list = []
        for line in lines:
            if len(line) == 0:
                continue
            if line[0] == "!":
                continue
            if line[0] == "|":
                continue
            if line[0] == "@":
                continue
            if line[0] == "[":
                continue
            if line.find('zh.wikipedia.org') == 0:
                continue
            line = string.replace(line, "||", "").lstrip(".")
            # strip everything from "/" to the end
            if line.find("/") != -1:
                line = line[0:line.find("/")]
            if line.find("*") != -1:
                continue
            if line.find(".") == -1:
                continue
                # if line in oklist:
            # 	continue
            domain_list.append(line)

        return domain_list

    def __resolve_domain(self, domain=''):
        """
        Resolve single domain with name server 8.8.8.8, and return all ips of this domain

        return list[ip]
        """
        _ip = []
        if self.__is_ip_address(domain):
            # print hostname + " is IP address"
            _ip.append(domain)
            return _ip
        r = dns.resolver.get_default_resolver()
        r.nameservers = ['8.8.8.8']
        #answers = dns.resolver.query(hostname, 'A')
        try:
            answers = r.query(domain, 'A')
            for rdata in answers:
                # print rdata.address
                _ip.append(rdata.address)
        except dns.resolver.NoAnswer:
            print "no answer"

        if domain.find("www.") != 0:
            domain = "www." + domain
            # print "querying " + hostname
            try:
                answers = dns.resolver.query(domain, 'A')
                for rdata in answers:
                    # print rdata.address
                    _ip.append(rdata.address)
            except dns.resolver.NoAnswer:
                print "no answer"
        # print("processed %s, it has %d ips." % (hostname, len(_ip)))

        return list(set(_ip))

    def __multithread_resolve(self, pool_size=60):
        q = Queue()
        workers = []
        self.iplist = []

        def worker():
            while True:
                domain = q.get()
                try:
                    self.iplist.extend(self.__resolve_domain(domain))
                except Exception, e:
                    print("Something wrong with %s: %s" % (domain, e))
                q.task_done()

        for hostname in self.domain_list:
            q.put(hostname)

        for i in range(pool_size):
            t = Thread(target=worker)
            t.setDaemon(True)
            workers.append(t)
            t.start()

        # wait for completion
        q.join()

        if self.iplist:
            print("Finish domain lookup! There are %d in total" % len(self.iplist))

    def __get_sutnet(self, ip=''):
        if self.__is_ip_address(ip):
            (a, b, c, d) = string.split(ip, ".")
            return "%s.%s.%s.0" % (a, b, c)



if __name__ == '__main__':
    start_time = time.time()

    gfw_routes = 'gfw_routes'
    except_routes = 'except_routes'
    custom_routes = 'custom_routes'
    gfwdomains_conf = 'gfwdomains.conf'

    freeway = Freeway()
    freeway.process(output=gfw_routes)
    freeway.process(path='custom_domains', output=custom_routes)
    freeway.process(path='except_domains', output=except_routes, format=2)
    freeway.generate_gfw_dnsmasq_conf(output=gfwdomains_conf)

    print "GFW routes save to %s" % gfw_routes
    print "custom routes save to %s" % custom_routes
    print "except routes save to %s" % except_routes
    print "dnsmasq config file save to %s" % gfwdomains_conf

    t = time.time() - start_time
    print time.time() - start_time, "seconds"
