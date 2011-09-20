from zope.interface import implements

from twisted.cred.portal import IRealm
from twisted.web.resource import IResource
from twisted.web import static

class AdminHTMLRealm(object):
	implements(IRealm)

	def __init__(self, resource):
		self.resource = resource
        
	def requestAvatar(self, avatarId, mind, *interfaces):
		if IResource in interfaces:
			return (IResource, self.resource, lambda: None)
		raise NotImplementedError()

