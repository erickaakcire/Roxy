from twisted.application import service, internet

from twisted.web import resource, server, static
from twisted.web import proxy, http

from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import and_, or_, not_, select
from datetime import datetime, timedelta

from twisted.cred.portal import Portal
from twisted.cred.checkers import FilePasswordDB
from twisted.web.guard import DigestCredentialFactory
from twisted.web.guard import HTTPAuthSessionWrapper

import sys

sys.path.append(".")

from roxy import roxy
from web import web
from web import auth

from twisted.internet import reactor
reactor.suggestThreadPoolSize(20)

application = service.Application("roxy")

def init_database():
	now = datetime.now()
	
	metadata = roxy.getLocalMetadata()

	sessions = metadata.tables['sessions']
	where_parts = []
	where_parts.append(sessions.c.End == None)
	
	whereclause = and_(*where_parts)

	update = sessions.update(whereclause=whereclause, values=dict(End=now))
	update.execute()

# Initialization
init_database()

# Proxy Server

roxy_factory = roxy.RoxyHTTPFactory()
roxy_factory.protocol = roxy.RoxyProxy

roxy_proxy = internet.TCPServer(58080, roxy_factory)
roxy_proxy.setServiceParent(application)

# Web UI

root = resource.Resource()
root.putChild('', static.File('web-static/index.html'))
root.putChild('about', static.File('web-static/about.html'))
root.putChild('history', static.File('web-static/history.html'))
root.putChild('faq', static.File('web-static/faq.html'))
root.putChild('test', static.File('web-static/test-error.html'))
root.putChild('test-success', static.File('web-static/test-success.html'))
# root.putChild('redirect', static.File('web-static/redirect.html'))
root.putChild('redirect', web.Redirect())
root.putChild('status', web.Status())
root.putChild('status.xml', web.UserStatus())
root.putChild('history.xml', web.UserHistory())
root.putChild('full_history.xml', web.FullUserHistory())
root.putChild('service.xml', static.File('web-static/service.xml'))

root.putChild('using', static.File('web-static/using.html'))
root.putChild('setup', static.File('web-static/setup.html'))
root.putChild('FirefoxDiagram.gif', static.File('web-static/FirefoxDiagram.gif'))
root.putChild('IEConnections.gif', static.File('web-static/IEConnections.gif'))
root.putChild('IELanSettings.gif', static.File('web-static/IELanSettings.gif'))
root.putChild('macsystem.gif', static.File('web-static/macsystem.gif'))
root.putChild('Apple.gif', static.File('web-static/Apple.gif'))
root.putChild('MacNetwork.gif', static.File('web-static/MacNetwork.gif'))

root.putChild('style.css', static.File('web-static/style.css'))
root.putChild('niftyCorners.css', static.File('web-static/niftyCorners.css'))
root.putChild('tipsy.css', static.File('web-static/tipsy.css'))
root.putChild('tipsy.gif', static.File('web-static/tipsy.gif'))
root.putChild('roxy.js', static.File('web-static/roxy.js'))
root.putChild('roxy-admin.js', static.File('web-static/roxy-admin.js'))
root.putChild('search.js', static.File('web-static/search.js'))
root.putChild('jquery.corner.js', static.File('web-static/jquery.corner.js'))
root.putChild('jquery.js', static.File('web-static/jquery.js'))
root.putChild('jquery.tipsy.js', static.File('web-static/jquery.tipsy.js'))
root.putChild('cookie.js', static.File('web-static/cookie.js'))
root.putChild('jquery-ui', static.File('web-static/jquery-ui'))
root.putChild('sidebar.xml', static.File('web-static/sidebar.xml'))
root.putChild('meta-sidebar.xml', static.File('web-static/meta-sidebar.xml'))

root.putChild('my-blacklist', static.File('web-static/blacklist.html'))
root.putChild('my-blacklist.xml', web.MyBlacklist())
root.putChild('remove-blacklist.xml', web.RemoveBlacklist())
root.putChild('user-blacklist.xml', web.UserBlacklistForm())

root.putChild('proxy.pac', static.File('web-static/proxy.pac'))

root.putChild('create_session', web.CreateSession())
root.putChild('expire_session', web.ExpireSession())
root.putChild('private_session', web.PrivateSession())

root.putChild('delete_domain.json', web.DeleteDomain())
root.putChild('blacklist_domain.json', web.BlacklistDomain())

credentialFactory = DigestCredentialFactory("md5", "Roxy Proxy Administration")

portal = Portal(auth.AdminHTMLRealm(static.File('web-static/admin.html')), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('admin', admin)

portal = Portal(auth.AdminHTMLRealm(static.File('web-static/search.html')), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('search', admin)

portal = Portal(auth.AdminHTMLRealm(static.File('web-static/sessions.html')), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('sessions', admin)

portal = Portal(auth.AdminHTMLRealm(web.SearchData()), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('search.xml', admin)

portal = Portal(auth.AdminHTMLRealm(web.AddUser()), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('add_user.xml', admin)

portal = Portal(auth.AdminHTMLRealm(web.DeleteUser()), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('delete_user.xml', admin)

portal = Portal(auth.AdminHTMLRealm(web.FetchUser()), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('fetch_user.xml', admin)

portal = Portal(auth.AdminHTMLRealm(web.AllUserSessions()), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('all_user_sessions.xml', admin)

portal = Portal(auth.AdminHTMLRealm(web.SetInteresting()), [FilePasswordDB('httpd.password')])
admin = HTTPAuthSessionWrapper(portal, [credentialFactory])
root.putChild('set_interesting.xml', admin)

site = server.Site(root)

http = internet.TCPServer(58081, site)
http.setServiceParent (application)
