from twisted.web import resource, server
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import and_, or_, not_, select, desc, delete

from xml.dom import minidom

from roxy import pysolr
from roxy import roxy
from roxy import blacklist

import uuid

class Status(resource.Resource):
	def render(self, request):
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")
		roxy.refresh()
			
		try:
			roxy.clearExtraContent()
			
			metadata = roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.End == None)
	
			whereclause = and_(*where_parts)

			stmt = select([sessions.c.Id], whereclause=whereclause)
			result = stmt.execute()
	
			return "OK: " + str(len(result.fetchall())) + " active session(s)"
		except:
			return "ERROR"

class Redirect(resource.Resource):
	def render(self, request):
		request.setHeader("Location", "http://proxy.roxyproxy.org/?referrer=" + request.uri[14:])
		request.setResponseCode(302)		
	
		return ""

class UserStatus(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		user_status = minidom.parseString("<div />")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")

		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']
	
			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.Id, sessions.c.Start, sessions.c.Log], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if len(active_sessions) > 0:
				header = user_status.createElement("div")
				header.setAttribute("class", "section-header")
				header.appendChild(user_status.createTextNode("Session Details"))
				user_status.documentElement.appendChild(header)

				section = user_status.createElement("div")
				section.setAttribute("class", "section")

				table = user_status.createElement("table")

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.appendChild(user_status.createTextNode("Session Status:"))
				tr.appendChild(td)

				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				
				if (active_sessions[0]["Log"]):
					td.appendChild(user_status.createTextNode("Active: Logging Enabled"))
				else:
					td.appendChild(user_status.createTextNode("Active: Logging Disabled"))
				
				tr.appendChild(td)
				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.appendChild(user_status.createTextNode("Session Start:"))
				tr.appendChild(td)

				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				td.appendChild(user_status.createTextNode(active_sessions[0]["Start"].strftime("%I:%M %p - %b %d, %Y")))
				tr.appendChild(td)
				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				tr.appendChild(td)
				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				a = user_status.createElement("a")
				a.setAttribute("href", "#")
				a.setAttribute("class", "private_button")
				a.setAttribute("onclick", "expireSession()")
				a.appendChild(user_status.createTextNode("End Current Session"))
				td.appendChild(a)
				tr.appendChild(td)
				table.appendChild(tr)

				section.appendChild(table)
				
				user_status.documentElement.appendChild(section)
				user_status.documentElement.appendChild(section)
			else:
				header = user_status.createElement("div")
				header.setAttribute("class", "section-header")
				header.appendChild(user_status.createTextNode("Choose A New Session Type"))
				user_status.documentElement.appendChild(header)

				section = user_status.createElement("div")
				section.setAttribute("class", "section")

				table = user_status.createElement("table")

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.appendChild(user_status.createTextNode("Session Status:"))
				tr.appendChild(td)
					
				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				td.appendChild(user_status.createTextNode("Inactive"))
				tr.appendChild(td)

				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.setAttribute("style", "vertical-align: middle;")
				td.appendChild(user_status.createTextNode("Username:"))
				tr.appendChild(td)
					
				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				input = user_status.createElement("input")
				input.setAttribute("class", "field")
				input.setAttribute("id", "userid")
				input.setAttribute("type", "text")
				td.appendChild(input)
				tr.appendChild(td)

				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.setAttribute("style", "vertical-align: middle;")
				td.appendChild(user_status.createTextNode("Password:"))
				tr.appendChild(td)
					
				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				input = user_status.createElement("input")
				input.setAttribute("class", "field")
				input.setAttribute("id", "password")
				input.setAttribute("type", "password")
				td.appendChild(input)
				tr.appendChild(td)

				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				tr.appendChild(td)

				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				a = user_status.createElement("a")
				a.setAttribute("href", "#")
				a.setAttribute("class", "regular_button")
				a.setAttribute("onclick", "createSession()")
				a.setAttribute("title", "Roxy will record the sites you view, except for any sites you've blacklisted or sites that are secure (start with https and have a 'lock' symbol like banking sites).")
				a.appendChild(user_status.createTextNode("Regular Session"))
				td.appendChild(a)

				a = user_status.createElement("a")
				a.setAttribute("href", "#")
				a.setAttribute("class", "private_button")
				a.setAttribute("onclick", "privateSession()")
				a.appendChild(user_status.createTextNode("Private Session"))
				a.setAttribute("title", "Roxy will not record any information about the web sites you visit in a private session. Please use this option sparingly to help the research project. You can blacklist specific sites using the Full History link on the right.")
				td.appendChild(a)

				a = user_status.createElement("a")
				a.setAttribute("href", "#")
				a.setAttribute("class", "guest_button")
				a.setAttribute("onclick", "guestSession()")
				a.appendChild(user_status.createTextNode("Guest Session"))
				a.setAttribute("title", "If you are not a participant in the Beyond The Click research project please use this option so that none of your web browsing is logged.")
				td.appendChild(a)

				tr.appendChild(td)
				table.appendChild(tr)

				section.appendChild(table)
				
				user_status.documentElement.appendChild(section)

		return user_status.toxml("utf-8")

class UserHistory(resource.Resource):
#		ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
#			
#		if ip_addresses:
#			roxy.createSession(ip_addresses[0], request.args["userid"][0])
#			return "<ok ip_address=\"" + ip_addresses[0] + "\" action=\"create_session\" />"

	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		user_history = minidom.parseString("<div />")

		header = user_history.createElement("div")
		header.setAttribute("class", "section-header")
		header.appendChild(user_history.createTextNode("Session History"))
		user_history.documentElement.appendChild(header)

		section = user_history.createElement("div")
		section.setAttribute("class", "section")
		user_history.documentElement.appendChild(section)

		table = user_history.createElement("table")
		table.setAttribute("class", "user-history")
		section.appendChild(table)


		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
		
		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.Id, sessions.c.Start, sessions.c.Log, sessions.c.User], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if len(active_sessions) > 0:
				requests = metadata.tables['requests']

				where_parts = []
				where_parts.append(requests.c.Session == active_sessions[0]["Id"])
				where_parts.append(requests.c.Content != None)
				where_parts.append(requests.c.Indexed != None)

				whereclause = and_(*where_parts)

				req_stmt = select([requests.c.Url, requests.c.Indexed], whereclause=whereclause, order_by=[desc(requests.c.Indexed)])

				req_result = req_stmt.execute()
	
				sites = req_result.fetchall()
	
				domains = []

				for row in sites:
					url = row["Url"].split("/")[0]
					
					url_components = url.split(".")
					
					if (len(url_components[-1]) > 2):
						url = ".".join(url_components[-2:])
					else:
						url = ".".join(url_components[-3:])
					
					try:
						domains.index(url)
					except:
						domains.append(url)
				
				if (len(domains) < 1):
					tr = user_history.createElement("tr")
					td = user_history.createElement("td")
					td.appendChild(user_history.createTextNode("No sites logged for this session, yet. Visit History & Blacklist to see your log from previous sessions."))
					tr.appendChild(td)
					table.appendChild(tr)
				else:
					for domain in domains[:20]:
						tr = user_history.createElement("tr")
						td = user_history.createElement("td")
						td.setAttribute("class", "history-site")
						td.appendChild(user_history.createTextNode(domain))
						tr.appendChild(td)
#						td = user_history.createElement("td")
#						td.setAttribute("class", "history-ops")
#					
#						a_delete = user_history.createElement("a")
#						a_delete.appendChild(user_history.createTextNode("Delete"))
#						a_delete.setAttribute("class", "delete-domain")
#						a_delete.setAttribute("onclick", "deleteDomain('" + domain + "')")
#						td.appendChild(a_delete)
#
#						a_blacklist = user_history.createElement("a")
#						a_blacklist.appendChild(user_history.createTextNode("Blacklist"))
#						a_blacklist.setAttribute("class", "blacklist-domain")
#						a_blacklist.setAttribute("onclick", "blacklistDomain('" + domain + "')")
#						td.appendChild(a_blacklist)
#
#						tr.appendChild(td)
						table.appendChild(tr)
			else:
				tr = user_history.createElement("tr")
				td = user_history.createElement("td")
				td.appendChild(user_history.createTextNode("Please start a session to retrieve history."))
				tr.appendChild(td)
				table.appendChild(tr)
		else:
			tr = user_history.createElement("tr")
			td = user_history.createElement("td")
			td.appendChild(user_history.createTextNode("Error fetching history. Please contact Roxy administrator."))
			tr.appendChild(td)
			table.appendChild(tr)
			
		tr = user_history.createElement("tr")
		td = user_history.createElement("td")
		td.setAttribute("colspan", "2")
		td.setAttribute("class", "refresh-sites")
		a = user_history.createElement("a")
		a.setAttribute("href", "#recent-sites")
		a.setAttribute("onclick", "loadUserHistory()")
		a.appendChild(user_history.createTextNode("Refresh Session History"))
		td.appendChild(a)
		tr.appendChild(td)
		table.appendChild(tr)
			
		return user_history.toxml("utf-8")
		
class CreateSession(resource.Resource):
	def render(self, request):
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")
		request.setHeader("Content-type", "text/xml")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
			
		if ip_addresses:
			if (roxy.validateUser(request.args["userid"][0], request.args["password"][0])):
				roxy.createSession(ip_addresses[0], request.args["userid"][0])
				
				return "<status message=\"Session established.\" go=\"true\" />"
			else:
				return "<status message=\"Invalid username &amp; password. Please try again.\" go=\"false\" />"

		return "<no_client_address />"

class ExpireSession(resource.Resource):
	def render(self, request):
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")
		request.setHeader("Content-type", "text/xml")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
	
		if ip_addresses:
			roxy.expireSession(ip_addresses[0])
			return "<ok ip_address=\"" + ip_addresses[0] + "\" action=\"expire_session\" />"

		return "<no_client_address />"

class PrivateSession(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
			
		if ip_addresses:
			if (roxy.validateUser(request.args["userid"][0], request.args["password"][0])):
				roxy.privateSession(ip_addresses[0], request.args["userid"][0])
				
				return "<status message=\"Private session established.\" go=\"true\" />"
			else:
				return "<status message=\"Invalid username &amp; password. Please try again.\" go=\"false\" />"

		return "<no_client_address />"

class SearchData(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		matches = minidom.parseString("<table class=\"search-results\"><tr><td class=\"search-results\"><strong>User ID</strong></td><td class=\"search-results\"><strong>Domain</strong></td><td class=\"search-results\"><strong>Date</strong></td></tr></table>")

		conn = pysolr.Solr('http://127.0.0.1:8983/solr/')

		query = request.args["query"][0]
		
		rows = 20
		
		try:
			rows = int(request.args["rows"][0])
		except:
			pass

		sort = request.args["sort"][0]
		
		results = conn.search(query, rows=rows, sort=sort)

		for result in results:
			tr = matches.createElement("tr")
			td = matches.createElement("td")
			td.setAttribute("class", "search-results")
			td.appendChild(matches.createTextNode(result["user_id"]))
			tr.appendChild(td)

			td = matches.createElement("td")
			td.setAttribute("class", "search-results")
			td.appendChild(matches.createTextNode(result["domain"]))
			tr.appendChild(td)

			td = matches.createElement("td")
			td.setAttribute("class", "search-results")
			td.appendChild(matches.createTextNode(str(result["fetch_date"]).replace("T", " ")))
			tr.appendChild(td)

			td = matches.createElement("td")
			td.setAttribute("class", "search-results")
			a = matches.createElement("a")
			a.setAttribute("href", "#" + result["id"])

			try:
				if (result["is_interesting"]):
					a.setAttribute("onclick", "flagNormal('" + result["id"] + "')")
					a.appendChild(matches.createTextNode("Unflag"))
				else:
					a.setAttribute("onclick", "flagInteresting('" + result["id"] + "')")
					a.appendChild(matches.createTextNode("Flag"))
			except KeyError:
					a.setAttribute("onclick", "flagInteresting('" + result["id"] + "')")
					a.appendChild(matches.createTextNode("Flag"))
			
			td.appendChild(a)

			tr.appendChild(td)

			matches.documentElement.appendChild(tr)

			tr = matches.createElement("tr")
			td = matches.createElement("td")
			td.setAttribute("class", "search-results")
			td.setAttribute("colspan", "4")
			
			td.appendChild(matches.createTextNode("URL: "))
			
			a = matches.createElement("a")
			a.setAttribute("href", "http://" + str(result["url"]))
			a.appendChild(matches.createTextNode(result["url"].replace("+", " ").replace("/", " /").replace("&", " &")))
			td.appendChild(a)

			tr.appendChild(td)

			matches.documentElement.appendChild(tr)

			try:
				tr = matches.createElement("tr")
				td = matches.createElement("td")
				td.setAttribute("class", "search-results")
				td.setAttribute("colspan", "4")
			
				td.appendChild(matches.createTextNode("Referrer: "))
			
				a = matches.createElement("a")
				a.setAttribute("href", "http://" + str(result["referrer"]))
				a.appendChild(matches.createTextNode(result["referrer"].replace("+", " ").replace("/", " /").replace("&", " &")))
				td.appendChild(a)

				tr.appendChild(td)

				matches.documentElement.appendChild(tr)
			except KeyError:
				pass

			try:
				tr = matches.createElement("tr")
				td = matches.createElement("td")
				td.setAttribute("class", "search-results")
				td.setAttribute("colspan", "4")
			
				td.appendChild(matches.createTextNode("Search Terms: "))
				td.appendChild(matches.createTextNode(str(result["search_terms"])))

				tr.appendChild(td)

				matches.documentElement.appendChild(tr)
			except KeyError:
				pass

			tr = matches.createElement("tr")
			td = matches.createElement("td")
			td.setAttribute("class", "search-results")
			td.setAttribute("colspan", "4")

			td.appendChild(matches.createTextNode("Request ID: "))
			td.appendChild(matches.createTextNode(result["request_id"]))
			tr.appendChild(td)

			matches.documentElement.appendChild(tr)


		tr = matches.createElement("tr")
		td = matches.createElement("td")
		td.appendChild(matches.createTextNode("Query: " + query))
		td.setAttribute("colspan", "3")
		tr.appendChild(td)
		matches.documentElement.appendChild(tr)
	
		return matches.toxml("utf-8")

class DeleteDomain(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "application/json")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		domain = request.args["domain"][0]
		session = request.args["session"][0]

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")

		message = "No entries matching '" + domain + "' found to delete."

		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.Id == session)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.Id, sessions.c.Start, sessions.c.Log, sessions.c.User], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if len(active_sessions) > 0:
				count = roxy.deleteDomainEntries(active_sessions[0]["Id"], domain)

				if (count > 0):
					message = str(count) + " entries removed from the log."
			else:
				message = "No active session available."
		else:
			message = "Unable to determine IP address."
			
		return "{ \"message\": \"" + message + "\" }"

class BlacklistDomain(resource.Resource):
#	def render(self, request):
#		request.setHeader("Content-type", "application/json")
#		request.setHeader("Cache-Control", "no-cache, must-revalidate")
#		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
#		request.setHeader("Pragma", "no-cache")
#
#		ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
#			
#		return "{ \"message\": \"Todo: Blacklist Domain\" }"

	def render(self, request):
		request.setHeader("Content-type", "application/json")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		domain = request.args["domain"][0]

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")

		message = "'" + domain + "' blacklisted & logged entries deleted."

		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.User], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if len(active_sessions) > 0:
				count = roxy.blacklistDomain(domain, active_sessions[0]["User"])
				
				if (count > 0):
					message = "'" + domain + "' blacklisted & " + str(count) + " logged entries deleted."
			else:
				message = "No active session available."
		else:
			message = "Unable to determine IP address."
			
		return "{ \"message\": \"" + message + "\" }"

# class RedirectToProxy(resource.Resource):
#		def render(self, request):
#			request.setHeader("Location", "http://proxy.roxyproxy.org/")
#
#			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
#			
#			if ip_addresses:
#				roxy.expireSession(ip_addresses[0], request.getHeader("User-Agent"))
#
#			return ""
#
# class RedirectToOriginalSite(resource.Resource):
#		def render(self, request):
#			try:
#				ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
#
#				request.setHeader("Location", roxy.next_pages[ip_addresses[0]])
#			except:
#				request.setHeader("Location", "http://proxy.roxyproxy.org/")
#
#			return ""

class UserBlacklistForm(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		user_status = minidom.parseString("<div />")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
		
		next = None
		previous = None
		page = 0
		
		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.User, sessions.c.Id], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if len(active_sessions) > 0:
				header = user_status.createElement("div")
				header.setAttribute("class", "section-header")
				header.appendChild(user_status.createTextNode("Quick Blacklist"))
				user_status.documentElement.appendChild(header)

				section = user_status.createElement("div")
				section.setAttribute("class", "section")
				
				table = user_status.createElement("table")
				table.setAttribute("style", "width: 530px")

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.setAttribute("style", "vertical-align: middle;")
				td.appendChild(user_status.createTextNode("Blacklisted Domains:"))
				tr.appendChild(td)
				td = user_status.createElement("td")
				td.setAttribute("class", "value")

				bls = roxy.blacklistForIp(ip_addresses[0])

				td.appendChild(user_status.createTextNode(str(len(bls)) + " domain(s) blocked "))
				
				a = user_status.createElement("a")
				a.setAttribute("href", "/my-blacklist")
				a.appendChild(user_status.createTextNode("(Full Blacklist)"))
				a.setAttribute("title", "Blacklist this website. It will be deleted from the log and no further information will be gathered by Roxy from this site.")
				
				td.appendChild(a)

				tr.appendChild(td)
				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				td.setAttribute("style", "vertical-align: middle;")
				td.appendChild(user_status.createTextNode("Domain:"))
				tr.appendChild(td)
				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				input = user_status.createElement("input")
				input.setAttribute("class", "field")
				input.setAttribute("id", "blacklist_domain")
				input.setAttribute("type", "text")
				td.appendChild(input)
				tr.appendChild(td)
				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				tr.appendChild(td)
				td = user_status.createElement("td")
				td.setAttribute("style", "font-size: smaller");
				td.appendChild(user_status.createTextNode("A domain is typically the last part of a website's hostname. For example, the domain for "))
				strong = user_status.createElement("strong")
				strong.appendChild(user_status.createTextNode("www.example.com"))
				td.appendChild(strong)
				td.appendChild(user_status.createTextNode(" is "))
				strong = user_status.createElement("strong")
				strong.appendChild(user_status.createTextNode("example.com"))
				td.appendChild(strong)
				td.appendChild(user_status.createTextNode(". (It would help the project if you do not blacklist news websites since this information is important to the research.)"))
				tr.appendChild(td)
				table.appendChild(tr)

				tr = user_status.createElement("tr")
				td = user_status.createElement("td")
				td.setAttribute("class", "label")
				tr.appendChild(td)
				td = user_status.createElement("td")
				td.setAttribute("class", "value")
				a = user_status.createElement("a")
				a.setAttribute("href", "#")
				a.setAttribute("class", "private_button")
				a.setAttribute("onclick", "blacklist()")
				a.appendChild(user_status.createTextNode("Blacklist Domain"))
				td.appendChild(a)
				tr.appendChild(td)

				table.appendChild(tr)
				user_status.documentElement.appendChild(table)

		return user_status.toxml("utf-8")



class FullUserHistory(resource.Resource):
#		ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
#			
#		if ip_addresses:
#			roxy.createSession(ip_addresses[0], request.args["userid"][0])
#			return "<ok ip_address=\"" + ip_addresses[0] + "\" action=\"create_session\" />"

	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		user_history = minidom.parseString("<div />")

		header = user_history.createElement("div")
		header.setAttribute("class", "section-header")
		header.appendChild(user_history.createTextNode("Full History"))
		user_history.documentElement.appendChild(header)

		section = user_history.createElement("div")
		section.setAttribute("class", "section")
		user_history.documentElement.appendChild(section)

		table = user_history.createElement("table")
		table.setAttribute("class", "user-history")
		section.appendChild(table)

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")
		
		next = None
		previous = None
		page = 0
		
		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()

			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.User, sessions.c.Id], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if len(active_sessions) > 0:
				requests = metadata.tables['requests']

				where_parts = []
				where_parts.append(requests.c.Session == sessions.c.Id)
				where_parts.append(sessions.c.User == active_sessions[0]["User"])
				where_parts.append(requests.c.Content != None)
				where_parts.append(requests.c.Indexed != None)

				whereclause = and_(*where_parts)

				req_stmt = select([requests.c.Url, requests.c.Date, requests.c.Session], whereclause=whereclause, order_by=[desc(requests.c.Date)])

				req_result = req_stmt.execute()
	
				sites = req_result.fetchall()
	
				domains = []
				
				try:
					page = int(request.args["p"][0])
				except:
					page = 0

				if (page > 0):
					previous = page - 1;
					
				start = page * 50
				end = start + 50

				if (len(sites) > end):
					next = page + 1

				for row in sites[start:end]:
					url = row["Url"].split("/")[0]
					
					url_components = url.split(".")
					
					domain = ""
					if (len(url_components[-1]) > 2):
						domain = ".".join(url_components[-2:])
					else:
						domain = ".".join(url_components[-3:])
					
					tr = user_history.createElement("tr")
					tr.setAttribute("class", "history-site")
					td = user_history.createElement("td")
					td.setAttribute("class", "history-site")
					td.setAttribute("style", "word-wrap:break-word")

					a = user_history.createElement("a")
					a.setAttribute("href", "http://" + row["Url"])
					a.setAttribute("target", "_blank")
					a.appendChild(user_history.createTextNode(row["Url"][:48]))
					td.appendChild(a)

					tr.appendChild(td)
					td = user_history.createElement("td")
					td.setAttribute("class", "history-ops")
					
					a_delete = user_history.createElement("a")
					a_delete.appendChild(user_history.createTextNode("Delete"))
					a_delete.setAttribute("class", "delete-domain")
					a_delete.setAttribute("title", "Delete this specific web page. It will not be available to the research project.")
					a_delete.setAttribute("onclick", "deleteDomain('" + domain + "', '" + row["Session"] + "')")
					td.appendChild(a_delete)

					a_blacklist = user_history.createElement("a")
					a_blacklist.appendChild(user_history.createTextNode("Blacklist"))
					a_blacklist.setAttribute("class", "blacklist-domain")
					a_blacklist.setAttribute("title", "Blacklist this domain. No further information will be gathered by Roxy from this site.")
					a_blacklist.setAttribute("onclick", "blacklistDomain('" + domain + "')")
					td.appendChild(a_blacklist)

					tr.appendChild(td)
					table.appendChild(tr)
			else:
				tr = user_history.createElement("tr")
				td = user_history.createElement("td")
				td.appendChild(user_history.createTextNode("Please start a session to retrieve history."))
				tr.appendChild(td)
				table.appendChild(tr)
		else:
			tr = user_history.createElement("tr")
			td = user_history.createElement("td")
			td.appendChild(user_history.createTextNode("Error fetching history. Please contact Roxy administrator."))
			tr.appendChild(td)
			table.appendChild(tr)
			
		tr = user_history.createElement("tr")
		td = user_history.createElement("td")
		td.setAttribute("colspan", "2")
		td.setAttribute("class", "refresh-sites")

		if (previous is not None):
			a = user_history.createElement("a")
			a.setAttribute("href", "#recent-sites")
			a.setAttribute("onclick", "loadFullUserHistory(" + str(previous) + ")")
			a.appendChild(user_history.createTextNode("Previous Page"))
			td.appendChild(a)
			td.appendChild(user_history.createTextNode(" -- "))

		a = user_history.createElement("a")
		a.setAttribute("href", "#recent-sites")
		a.setAttribute("onclick", "loadFullUserHistory(" + str(page) + ")")
		a.appendChild(user_history.createTextNode("Refresh"))
		td.appendChild(a)

		if (next is not None):
			td.appendChild(user_history.createTextNode(" -- "))

			a = user_history.createElement("a")
			a.setAttribute("href", "#recent-sites")
			a.setAttribute("onclick", "loadFullUserHistory(" + str(next) + ")")
			a.appendChild(user_history.createTextNode("Next Page"))
			td.appendChild(a)

		tr.appendChild(td)
		table.appendChild(tr)

			
		return user_history.toxml("utf-8")

class AddUser(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		status = minidom.parseString("<status />")

		try:
			username = request.args["username"][0]
			password = request.args["password"][0]
			
			metadata = roxy.getLocalMetadata()

			users = metadata.tables['users']
			
			where_parts = []
			where_parts.append(users.c.Username == username)
			whereclause = and_(*where_parts)

			delete_user = users.delete(whereclause=whereclause)
			delete_user.execute()
			
			insert = users.insert()
			insert.execute(Id=uuid.uuid4(), Username=username, Password=password)

			status.documentElement.setAttribute("message", "Success: User added.")
		except:			
			status.documentElement.setAttribute("message", "Error: Missing username or password.")

		return status.toxml("utf-8")

class DeleteUser(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		status = minidom.parseString("<status />")

		try:
			username = request.args["username"][0]
			
			metadata = roxy.getLocalMetadata()

			users = metadata.tables['users']
			
			where_parts = []
			where_parts.append(users.c.Username == username)
			whereclause = and_(*where_parts)

			delete_user = users.delete(whereclause=whereclause)
			delete_user.execute()

			status.documentElement.setAttribute("message", "Success: User deleted.")
		except:			
			status.documentElement.setAttribute("message", "Error: Missing username.")

		return status.toxml("utf-8")

class FetchUser(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		status = minidom.parseString("<status />")

		username = request.args["username"][0]
			
		metadata = roxy.getLocalMetadata()

		users = metadata.tables['users']
			
		where_parts = []
		where_parts.append(users.c.Username == username)
		whereclause = and_(*where_parts)

		stmt = select([users.c.Username, users.c.Password], whereclause=whereclause)
		result = stmt.execute()
	
		user = result.fetchone()
			
		if (user):
			status.documentElement.setAttribute("message", user["Username"] + ": " + user["Password"])
		else:
			status.documentElement.setAttribute("message", "No such user: " + username + ".")

		return status.toxml("utf-8")

class AllUserSessions(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		table = minidom.parseString("<table />")

		metadata = roxy.getLocalMetadata()

		users = metadata.tables['users']
		sessions = metadata.tables['sessions']
		
		stmt = select([users.c.Username, users.c.Id], distinct=True, order_by=[users.c.Username])
		results = stmt.execute()
		
		for row in results.fetchall():
			tr = table.createElement("tr")
			td = table.createElement("td");
			td.setAttribute("class", "label")
			td.appendChild(table.createTextNode(row["Username"]))
			tr.appendChild(td)
			
			where_parts = []
			where_parts.append(sessions.c.User == row["Username"])
			whereclause = and_(*where_parts)

			sessions_stmt = select([sessions.c.Start, sessions.c.End], whereclause=whereclause, order_by=[desc(sessions.c.Start)], limit=1)
			session_res = sessions_stmt.execute()
			
			found_sessions = session_res.fetchall()

			td = table.createElement("td");
			td.setAttribute("class", "value")
			
			if (len(found_sessions) > 0):
				if (found_sessions[0]["End"] is not None):
					td.appendChild(table.createTextNode("Session completed at " + str(found_sessions[0]["End"]) + "."))
				else:
					td.appendChild(table.createTextNode("Session in progress since " + str(found_sessions[0]["Start"]) + "."))
			else:
				td.appendChild(table.createTextNode("Never Logged In"))
			
			tr.appendChild(td)
			table.documentElement.appendChild(tr)

		return table.toxml("utf-8")

class MyBlacklist(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")

		table = minidom.parseString("<table />")
		
		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()
			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.User], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if (len(active_sessions) > 0):
				for bl in blacklist.userBlacklist(active_sessions[0]["User"]):
					tr = table.createElement("tr")
					td = table.createElement("td");
					td.setAttribute("class", "label")
					td.appendChild(table.createTextNode(bl))
					tr.appendChild(td)
			
					td = table.createElement("td");
					td.setAttribute("class", "value")
					
					a = table.createElement("a");
					a.setAttribute("onclick", "removeBlacklist('" + bl + "')")
					a.setAttribute("href", "#")
					a.appendChild(table.createTextNode("Remove"))
					td.appendChild(a)

					tr.appendChild(td)
					table.documentElement.appendChild(tr)
			else:
					tr = table.createElement("tr")
					td = table.createElement("td");
					td.setAttribute("class", "label")
					td.appendChild(table.createTextNode("No active session."))
					tr.appendChild(td)
					table.documentElement.appendChild(tr)
		else:
			tr = table.createElement("tr")
			td = table.createElement("td");
			td.setAttribute("class", "label")
			td.appendChild(table.createTextNode("Please establish a session."))
			tr.appendChild(td)
			table.documentElement.appendChild(tr)

		return table.toxml("utf-8")

class RemoveBlacklist(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")

		if (request.requestHeaders.getRawHeaders("x-forwarded-for") is None):
			ip_addresses = ["0.0.0.0"]
		else:
			ip_addresses = request.requestHeaders.getRawHeaders("x-forwarded-for")[0].split(", ")

		table = minidom.parseString("<table />")
		
		if ip_addresses:
			metadata = 	roxy.getLocalMetadata()
			sessions = metadata.tables['sessions']

			where_parts = []
			where_parts.append(sessions.c.IpAddress == ip_addresses[0])
			where_parts.append(sessions.c.End == None)

			whereclause = and_(*where_parts)

			stmt = select([sessions.c.User], whereclause=whereclause, order_by=[desc(sessions.c.Start)])

			result = stmt.execute()
	
			active_sessions = result.fetchall()

			if (len(active_sessions) > 0):
				blacklist.removeUserBlacklist(active_sessions[0]["User"], request.args["domain"][0]) 

				return "<ok />"
		return "<error />"
		
class SetInteresting(resource.Resource):
	def render(self, request):
		request.setHeader("Content-type", "text/xml")
		request.setHeader("Cache-Control", "no-cache, must-revalidate")
		request.setHeader("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		request.setHeader("Pragma", "no-cache")
		
		doc_id = request.args["id"][0]
		interesting = False
		
		try:
			interesting = (request.args["interesting"][0] == "true")
		except:
			pass
			
		roxy.setInteresting(doc_id, interesting)		

		return "<ok />"
		
