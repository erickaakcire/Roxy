from twisted.web import proxy, http

from stripogram import html2text, html2safehtml

from twisted.internet import threads
from twisted.python import log

from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import and_, or_, not_, select, delete

import urlparse
import cgi

import uuid
import array
import re
import sys

import pysolr
import chardet
from html2text import html2text # GPL!!!

from datetime import datetime, timedelta

from cStringIO import StringIO

from blacklist import userBlacklist, addUserBlacklist
import blacklist

active_ips = {}
session_ips = {}
roxy_metadata = None

# next_pages = {}

def refresh():
	remove = []
	
	for ip_address, date in active_ips.iteritems():
		try:
			active_date = active_ips[ip_address]
			now = datetime.now()

			if ((now - active_date).seconds > (30 * 60)): # 30 minute refresh
				remove.append(ip_address)
		except KeyError:
			pass
			
	for ip_address in remove:
		try:
			del active_ips[ip_address]
			expireSession(ip_address)
		except KeyError:
			pass

def getLocalMetadata():
	global roxy_metadata
	
	if (roxy_metadata is None):
		engine = create_engine("mysql://root:dr0w554p@localhost/roxyproxy", pool_size=20) # , echo=True)
		roxy_metadata = MetaData(bind=engine, reflect=True)
		
	return roxy_metadata

def logRequest(ip_address, user_agent, referer, host, path):
	if host != "proxy.roxyproxy.org":
		metadata = getLocalMetadata()

		session_id = None
		
		try:
			session_id = session_ips[ip_address]
		except KeyError:
			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_address)
			where_parts.append(sessions.c.Log == True)
			where_parts.append(sessions.c.End == None)
	
			whereclause = and_(*where_parts)

			stmt = select([sessions.c.Id], whereclause=whereclause)
			result = stmt.execute()
	
			ids_list = result.fetchone()

			if ids_list:
				session_id = ids_list[0]
				session_ips[ip_address] = session_id
	
		if (session_id):
			requests = metadata.tables['requests']

			insert = requests.insert().prefix_with("DELAYED")
			insert.execute(Id=uuid.uuid4(), Session=session_id, Date=datetime.now(), Url=(host + path), UserAgent=user_agent, Referrer=referer, Archive=True)

def updateRequestStatus(host, path, status):
	metadata = getLocalMetadata()

	requests = metadata.tables['requests']

	where_parts = []
	where_parts.append(requests.c.Url == host + path)
	where_parts.append(requests.c.Status == None)
	
	whereclause = and_(*where_parts)
	
	update = requests.update(whereclause=whereclause, values=dict(Status=status))
	update.execute()
	
def updateRequestMimeType(host, path, type):
	metadata = getLocalMetadata()

	requests = metadata.tables['requests']

	where_parts = []
	where_parts.append(requests.c.Url == host + path)
	where_parts.append(requests.c.MimeType == None)
	
	whereclause = and_(*where_parts)
	
	update = requests.update(whereclause=whereclause, values=dict(MimeType=type))
	update.execute()

def updateRequestLength(host, path, length):
	metadata = getLocalMetadata()

	requests = metadata.tables['requests']

	where_parts = []
	where_parts.append(requests.c.Url == host + path)
	where_parts.append(requests.c.Size == None)
	
	whereclause = and_(*where_parts)
	
	update = requests.update(whereclause=whereclause, values=dict(Size=length))
	update.execute()

def deleteDomainEntries(session_id, domain):
	metadata = getLocalMetadata()

	requests = metadata.tables['requests']

	where_parts = []
	where_parts.append(requests.c.Session == session_id)
	where_parts.append(requests.c.Url.like("%" + domain + "/%"))
	where_parts.append(requests.c.Indexed != None)

	whereclause = and_(*where_parts)

	to_delete = select([requests.c.Url, requests.c.Id], whereclause=whereclause)
	deleted = to_delete.execute()
	
	delete_set = deleted.fetchall()

	count = len(delete_set)
				
	if (count > 0):
		conn = pysolr.Solr('http://127.0.0.1:8983/solr/')

		for row in delete_set:
			conn.delete(id=row["Id"])

		delete_stmt = delete(requests, whereclause=whereclause)
		delete_stmt.execute()

	return count

def blacklistDomain(domain, user):
	metadata = getLocalMetadata()

	requests = metadata.tables['requests']
	sessions = metadata.tables['sessions']
	
	where_parts = []
	where_parts.append(requests.c.Session == sessions.c.Id)
	where_parts.append(requests.c.Url.like("%" + domain + "/%"))
	where_parts.append(sessions.c.User == user)

	whereclause = and_(*where_parts)

	to_delete = select([requests.c.Id], whereclause=whereclause)
	deleted = to_delete.execute()
	
	delete_set = deleted.fetchall()

	count = len(delete_set)
	
	if (count > 0):
		conn = pysolr.Solr('http://127.0.0.1:8983/solr/')

		for row in delete_set:
			conn.delete(id=row["Id"])

			where_parts = []
			where_parts.append(requests.c.Id == row["Id"])
			where_parts.append(requests.c.Url.like("%" + domain + "/%"))

			whereclause = and_(*where_parts)

			delete_stmt = delete(requests, whereclause=whereclause)
			delete_stmt.execute()

	addUserBlacklist(user, domain)

	return count

def blacklistForIp(ip_address):
	metadata = getLocalMetadata()
	sessions = metadata.tables['sessions']
	
	where_parts = []
	where_parts.append(sessions.c.IpAddress == ip_address)
	where_parts.append(sessions.c.End == None)

	whereclause = and_(*where_parts)

	stmt = select([sessions.c.User], whereclause=whereclause)
	users = stmt.execute().fetchall()

	if (len(users) > 0):
		return userBlacklist(users[0]["User"])
	
	return []

def blacklistDomainForIp(ip_address, domain):
	metadata = getLocalMetadata()
	sessions = metadata.tables['sessions']
	
	where_parts = []
	where_parts.append(sessions.c.IpAddress == ip_address)
	where_parts.append(sessions.c.End == None)

	whereclause = and_(*where_parts)

	stmt = select([sessions.c.User], whereclause=whereclause)
	users = stmt.execute().fetchall()

	if (len(users) > 0):
		blacklistDomain(domain, users[0]["User"])
		return True
	
	return False

def searchTermsForUrl(url):
	components = urlparse.urlparse(url)

	try:
		if (components[1].find("google.com") != -1):
			return cgi.parse_qs(components[4])["q"][0]
		elif (components[1].find("youtube.com") != -1):
			return cgi.parse_qs(components[4])["search_query"][0]
		elif (components[1].find("yahoo.com") != -1):
			return cgi.parse_qs(components[4])["p"][0]
		elif (components[1].find("bing.com") != -1):
			return cgi.parse_qs(components[4])["q"][0]
		elif (components[1].find("wikipedia.org") != -1):
			return cgi.parse_qs(components[4])["search"][0]
		elif (components[1].find("amazon.com") != -1):
			return cgi.parse_qs(components[4])["field-keywords"][0]
		elif (components[1].find("ask.com") != -1):
			return cgi.parse_qs(components[4])["q"][0]
	except:
		pass
	
	return ""

def setInteresting(doc_id, is_interesting):
	conn = pysolr.Solr('http://127.0.0.1:8983/solr/')

	results = conn.search("id:" + doc_id, rows=1)

	for result in results:
		result["is_interesting"] = is_interesting;

		conn.add([result])

def updateTextContent(host, path, content, headers):
	metadata = getLocalMetadata()

	requests = metadata.tables['requests']
	sessions = metadata.tables['sessions']

	where_parts = []
	where_parts.append(requests.c.Url == host + path)
	where_parts.append(requests.c.Content == None)
	where_parts.append(requests.c.MimeType != None)
	
	whereclause = and_(*where_parts)

	if (host != "proxy.roxyproxy.org"):
			encoding = chardet.detect(content)

			if (encoding["encoding"]):
				content = unicode(content, encoding["encoding"], "replace")
			else:
				content = unicode(content, "ascii", "replace")

			html_content = content

#		try:
#			try:
#				content = html2text(content.encode("ascii", "replace"))
#			except:
#				content = content.encode("ascii", "replace")
				
			where_parts = []
			where_parts.append(requests.c.Url == host + path)
			where_parts.append(requests.c.Indexed == None)

			whereclause = and_(*where_parts)
		
			if (len(content) > 1024):
				update = requests.update(whereclause=whereclause, values=dict(Content=content.encode("utf-8", "'xmlcharrefreplace'")))
				update.execute()

				where_parts = []
				where_parts.append(requests.c.Url == host + path)
				where_parts.append(requests.c.Indexed == None)
				where_parts.append(requests.c.Session == sessions.c.Id)
				whereclause = and_(*where_parts)

				stmt = select([requests.c.Id, requests.c.Session, requests.c.Url, requests.c.MimeType, requests.c.Status, requests.c.Date, requests.c.UserAgent, \
							   sessions.c.IpAddress, sessions.c.User, sessions.c.Start, sessions.c.End, requests.c.Referrer], whereclause=whereclause)

				result = stmt.execute()
	
				sql_doc = result.fetchone()

				if (sql_doc):
					solr_doc = {}
					solr_doc["id"] = sql_doc[0];
					solr_doc["session_id"] = sql_doc[1]

					solr_doc["request_id"] = sql_doc[0]
					solr_doc["url"] = sql_doc[2]

					terms = searchTermsForUrl("http://" + sql_doc[2])

					solr_doc["host"] = host
					solr_doc["domain"] = host # TODO

					solr_doc["mime_type"] = sql_doc[3]
					solr_doc["http_status"] = sql_doc[4]
					solr_doc["fetch_date"] = sql_doc[5]
					solr_doc["user_agent"] = sql_doc[6]
					solr_doc["client_ip"] = sql_doc[7]
					solr_doc["user_id"] = sql_doc[8]
					solr_doc["session_start_date"] = sql_doc[9]
					solr_doc["session_end_date"] = sql_doc[10]
					solr_doc["referrer"] = sql_doc[11]
					solr_doc["is_interesting"] = False

					terms = terms + " " + searchTermsForUrl(sql_doc[11])

					solr_doc["search_terms"] = terms

					if (blacklist.userAllow(solr_doc["user_id"], solr_doc["host"])):
						title_re = re.compile("<title>(.*?)<\/title>",re.DOTALL|re.M|re.I)
						matches = title_re.findall(html_content)
				
						if (len(matches) > 0):
							solr_doc["title"] = matches[0]
						try:
							solr_doc["text_content"] = content.encode("ascii", "replace");
							solr_doc["text_size"] = len(content);

							conn = pysolr.Solr('http://127.0.0.1:8983/solr/')

							conn.add([solr_doc])
						except UnicodeDecodeError:
							pass
					else:
						where_parts = []
						where_parts.append(requests.c.Id == solr_doc["id"])

						whereclause = and_(*where_parts)

						delete_stmt = delete(requests, whereclause=whereclause)
						delete_stmt.execute()

			where_parts = []
			where_parts.append(requests.c.Url == host + path)
			where_parts.append(requests.c.Indexed == None)

			whereclause = and_(*where_parts)

			update = requests.update(whereclause=whereclause, values=dict(Indexed=datetime.now()))
			update.execute()
#		except:
#			print "Unexpected error:", sys.exc_info()[0]
#
#			where_parts = []
#			where_parts.append(requests.c.Url == host + path)
#			where_parts.append(requests.c.Indexed == None)
#			whereclause = and_(*where_parts)
#
#			update = requests.update(whereclause=whereclause, values=dict(Content=""))
#			update.execute()

def clearExtraContent():
	metadata = getLocalMetadata()
	requests = metadata.tables['requests']

	where_parts = []
	where_parts.append(requests.c.MimeType == None)
	where_parts.append(requests.c.Date < (datetime.now() - timedelta(seconds=300)))
	
	whereclause = and_(*where_parts)

	delete = requests.delete(whereclause=whereclause)
	delete.execute()

	where_parts = []
	where_parts.append(requests.c.Content == None)
	where_parts.append(requests.c.Date < (datetime.now() - timedelta(seconds=300)))
	
	whereclause = and_(*where_parts)

	delete = requests.delete(whereclause=whereclause)
	delete.execute()

	where_parts = []
	where_parts.append(requests.c.Content == "")
	where_parts.append(requests.c.Date < (datetime.now() - timedelta(seconds=300)))
	
	whereclause = and_(*where_parts)

	delete = requests.delete(whereclause=whereclause)
	delete.execute()

def expireSession(ip_address):
	metadata = getLocalMetadata()
	sessions = metadata.tables['sessions']
	
	where_parts = []
	where_parts.append(sessions.c.IpAddress == ip_address)
	
	whereclause = and_(*where_parts)
	
	update = sessions.update(whereclause=whereclause, values=dict(End=datetime.now()))
	update.execute()

	try:
		del active_ips[ip_address]
	except KeyError:
		pass

	try:
		del session_ips[ip_address]
	except KeyError:
		pass
	
def createSession(ip_address, userid, logging=True):
	metadata = getLocalMetadata()

	sessions = metadata.tables['sessions']
	
	u = uuid.uuid4()
	
	expireSession(ip_address)
	
	insert = sessions.insert()
	insert.execute(Id=uuid.uuid4(), User=userid, Start=datetime.now(), Log=logging, IpAddress=ip_address)

	now = datetime.now()

	active_ips[ip_address] = now
	
def validateUser(username, password):
	metadata = getLocalMetadata()

	users = metadata.tables['users']

	where_parts = []
	where_parts.append(users.c.Username == username)
	where_parts.append(users.c.Password == password)
	whereclause = and_(*where_parts)

	stmt = select([users.c.Id], whereclause=whereclause)
	result = stmt.execute()

	if (result.fetchone()):
		return True
	
	return False

def privateSession(ip_address, userid):
	createSession(ip_address, userid, False)

class RoxyProxyClient(proxy.ProxyClient):
	def setRequestDetail(self, key, value):
		try:
			self.requestDetails
		except AttributeError:
			self.requestDetails = {}
			
		self.requestDetails[key] = value

	def handleStatus(self, version, code, message):
		self.father.setResponseCode(int(code), message)
		self.setRequestDetail("code", int(code))
	
	def handleHeader(self, key, value):
		try:
			self.responseHeaders
		except AttributeError:
			self.responseHeaders = {}

		self.responseHeaders[key.lower()] = value
			
		if key.lower() in ['server', 'date', 'content-type']:
			self.father.responseHeaders.setRawHeaders(key, [value])
		else:
			self.father.responseHeaders.addRawHeader(key, value)

		if (key.lower() == "content-type"):
			try:
				value.index("text/html")
				
				self.responseData = StringIO()

				self.setRequestDetail("mime-type", value)
			except ValueError:
				pass
		elif (key.lower() == "content-length"):
			self.setRequestDetail("content-length", value)

	def handleResponsePart(self, data):
		try:
			self.responseData.write(data)
		except:
			pass
			
		proxy.ProxyClient.handleResponsePart(self, data)

	def handleResponseEnd(self):
		try:
			self.response_handled
		except:
			try:
				if self.responseData != None:
					try:
						self.requestDetails["mime-type"]
	
						if (blacklist.allow(self.headers["host"])):
							commands = []

							try:
								commands.append((updateRequestStatus, [self.headers["host"], self.rest, self.requestDetails["code"]], {}))
							except KeyError:
								pass

							try:
								commands.append((updateRequestMimeType, [self.headers["host"], self.rest, self.requestDetails["mime-type"]], {}))
							except KeyError:
								pass

							try:
								commands.append((updateRequestLength, [self.headers["host"], self.rest, self.requestDetails["content-length"]], {}))
							except KeyError:
								pass

							commands.append((updateTextContent, [self.headers["host"], self.rest, self.responseData.getvalue(), self.responseHeaders], {}))

							threads.callMultipleInThread(commands)

					except KeyError:
						pass
					
			except AttributeError:
				pass
			
			self.response_handled = True

		if (self.father.do_finish):
			proxy.ProxyClient.handleResponseEnd(self)

class RoxyProxyClientFactory(proxy.ProxyClientFactory):
	protocol = RoxyProxyClient

class RoxyProxyRequest(proxy.ProxyRequest):
	protocols = {'http': RoxyProxyClientFactory}
	ports = {'http': 80}
		
	def interrupted(self, err):
		self.do_finish = False

	def process(self):
		self.do_finish = True
		
		self.notifyFinish().addErrback(self.interrupted)
		
		parsed = urlparse.urlparse(self.uri)

		print("URL: " + self.uri)
		
		protocol = parsed[0]
		host = parsed[1]
		
		raw_host = host

		if (protocol == ""):
			protocol = "http"

		port = self.ports[protocol]
			
		uri = host
			
		if ':' in host:
			host, port = host.split(':')
			port = int(port)

		rest = urlparse.urlunparse(('', '') + parsed[2:])
		if not rest:
			rest = rest + '/'
		class_ = self.protocols[protocol]

		self.requestHeaders.removeHeader('accept-encoding')

		headers = self.getAllHeaders().copy()
		if 'host' not in headers:
			headers['host'] = host

		if 'referer' not in headers:
			headers['referer'] = ""
       
		now = datetime.now()
		
		active_date = None
		
		try:
#			refresh()
			active_date = active_ips[self.getClientIP()]
		except KeyError:
			pass
		
		if (active_date or host == "proxy.roxyproxy.org"):
			if active_date:
				active_ips[self.getClientIP()] = now

			if (host == "proxy.roxyproxy.org" and rest == "/test"):
				rest = "/test-success"

			headers["X-Forwarded-For"] = self.getClientIP()

			commands = []
			commands.append((logRequest, [self.getClientIP(), self.getHeader("User-Agent"), headers["referer"], raw_host, rest], {}))
			threads.callMultipleInThread(commands)
			
			self.content.seek(0, 0)
			s = self.content.read()
			clientFactory = class_(self.method, rest, self.clientproto, headers, s, self)
			self.reactor.connectTCP(host, port, clientFactory)
		else:
			headers['host'] = "proxy.roxyproxy.org"

			self.content.seek(0, 0)
			s = self.content.read()
			clientFactory = class_("GET", "/redirect?ref=" + self.uri, self.clientproto, headers, s, self)
			self.reactor.connectTCP("proxy.roxyproxy.org", 80, clientFactory)

class RoxyProxy(proxy.Proxy):
	requestFactory = RoxyProxyRequest

class RoxyHTTPFactory(http.HTTPFactory):

    def log(self, request):
		pass
