import re
import time
import urllib
import base64
import string
from threading import Thread
from Queue import Queue
#from socket import gethostbyname
import dns.resolver


class Freeway(object):
	"""docstring for Freeway"""
	def __init__(self):
		self.domain_list = None
		self.white_list = []
		self.iplist = []
		self.subnets = []
		self.single_ips = []

	def fetch_from_file(self, path):
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
		gfwlist = 'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt'
		print "fetching gfwList ..."

		try:
			d = urllib.urlopen(gfwlist).read()
		except Exception, e:
			print("Failed to fetch from %s: %s" % (path, e))
			print("Make sure you run this script from somewhere GFW is bypassed ...")
			return False

		data = base64.b64decode(d)
		lines = string.split(data, "\n")
		self.domain_list = self.parse_domains(lines)
		print("Got %d domains" % len(self.domain_list))
		return True

	def parse_domains(self, lines):
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
			line = string.replace(line, "||","").lstrip(".")
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


	def is_ip(self, hostname=''):
		pat = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
		if re.match(pat, hostname):
			return True
		else:
			return False

	def get_iplist(self, hostname=''):
		
		_ip = []
		if self.is_ip(hostname):
			# print hostname + " is IP address"
			_ip.append(hostname)
			return _ip
		r = dns.resolver.get_default_resolver()
		r.nameservers=['8.8.8.8']
		#answers = dns.resolver.query(hostname, 'A')
		try:
			answers = r.query(hostname, 'A')
			for rdata in answers:
				# print rdata.address
				_ip.append(rdata.address)
		except dns.resolver.NoAnswer:
			print "no answer"

		if hostname.find("www.") != 0:
			hostname = "www." + hostname
			# print "querying " + hostname
			try:
				answers = dns.resolver.query(hostname, 'A')
				for rdata in answers:
					# print rdata.address
					_ip.append(rdata.address)
			except dns.resolver.NoAnswer:
				print "no answer"
		print("processed %s, it has %d ips." % (hostname, len(_ip)))

		return list(set(_ip))

	def resolve_domains(self, pool_size=60):
		"""
		Resolve domains from 8.8.8.8 with threadpool 
		"""
		q = Queue()
		workers = []
		self.iplist = []
		def worker():
			while  True:
				domain = q.get()
				try:
					self.iplist.extend(self.get_iplist(domain))
				except Exception, e:
					print("Something wrong with %s: %s" % (domain, e))
				q.task_done()	
			
		for i in range(pool_size):
			t = Thread(target=worker)
			t.setDaemon(True)
			workers.append(t)
			t.start()

		for hostname in self.domain_list:
			q.put(hostname)

		# wait for completion
		q.join()

		if self.iplist:
			print("Finish domain lookup! There are %d in total" % len(self.iplist))
	
	def get_sutnet(self, ip=''):
		if self.is_ip(ip):
			(a, b, c, d) = string.split(ip, ".")
			return "%s.%s.%s.0" % (a, b, c)

	def degest_ips(self):
		all_subnets = {}
		# extract all subnets
		for ip in self.iplist:	
			subnet = self.get_sutnet(ip)
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
			
if __name__ == '__main__': 
	start_time = time.time()
	lookup = Freeway()
	if lookup.fetch_from_file("custom_domains"):
		lookup.resolve_domains(5)
		lookup.degest_ips()
		lookup.export(path="custom_routes")	

	if lookup.fetch_from_file("except_domains"):
		lookup.resolve_domains(5)
		lookup.degest_ips()
		lookup.export(path="except_routes", format=2)	


	# lookup.fetch_from_gfwlist()
	
	t = time.time() - start_time
	print time.time() - start_time, "seconds"





	














	