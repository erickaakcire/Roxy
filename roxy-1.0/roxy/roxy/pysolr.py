# -*- coding: utf-8 -*-
"""
All we need to create a Solr connection is a url.

>>> conn = Solr('http://127.0.0.1:8983/solr/')

First, completely clear the index.

>>> conn.delete(q='*:*')

For now, we can only index python dictionaries. Each key in the dictionary
will correspond to a field in Solr.

>>> docs = [
...     {'id': 'testdoc.1', 'order_i': 1, 'name': 'document 1', 'text': u'Paul Verlaine'},
...     {'id': 'testdoc.2', 'order_i': 2, 'name': 'document 2', 'text': u'Владимир Маякoвский'},
...     {'id': 'testdoc.3', 'order_i': 3, 'name': 'document 3', 'text': u'test'},
...     {'id': 'testdoc.4', 'order_i': 4, 'name': 'document 4', 'text': u'test'}
... ]


We can add documents to the index by passing a list of docs to the connection's
add method.

>>> conn.add(docs)

>>> results = conn.search('Verlaine')
>>> len(results)
1

>>> results = conn.search(u'Владимир')
>>> len(results)
1


Simple tests for searching. We can optionally sort the results using Solr's
sort syntax, that is, the field name and either asc or desc.

>>> results = conn.search('test', sort='order_i asc')
>>> for result in results:
...     print result['name']
document 3
document 4

>>> results = conn.search('test', sort='order_i desc')
>>> for result in results:
...     print result['name']
document 4
document 3


To update documents, we just use the add method.

>>> docs = [
...     {'id': 'testdoc.4', 'order_i': 4, 'name': 'document 4', 'text': u'blah'}
... ]
>>> conn.add(docs)

>>> len(conn.search('blah'))
1
>>> len(conn.search('test'))
1


We can delete documents from the index by id, or by supplying a query.

>>> conn.delete(id='testdoc.1')
>>> conn.delete(q='name:"document 2"')

>>> results = conn.search('Verlaine')
>>> len(results)
0


Docs can also have multiple values for any particular key. This lets us use
Solr's multiValue fields.

>>> docs = [
...     {'id': 'testdoc.5', 'cat': ['poetry', 'science'], 'name': 'document 5', 'text': u''},
...     {'id': 'testdoc.6', 'cat': ['science-fiction',], 'name': 'document 6', 'text': u''},
... ]

>>> conn.add(docs)
>>> results = conn.search('cat:"poetry"')
>>> for result in results:
...     print result['name']
document 5

>>> results = conn.search('cat:"science-fiction"')
>>> for result in results:
...     print result['name']
document 6

>>> results = conn.search('cat:"science"')
>>> for result in results:
...     print result['name']
document 5

Docs can also boost any particular key. This lets us use Solr's boost on a field.

>>> docs = [
...     {'id': 'testdoc.7', 'order_i': '7', 'name': 'document 7', 'text': u'eight', 'author': 'seven'},
...     {'id': 'testdoc.8', 'order_i': '8', 'name': 'document 8', 'text': u'seven', 'author': 'eight'},
... ]

>>> conn.add(docs, boost={'author': '2.0',})
>>> results = conn.search('seven author:seven')
>>> for result in results:
...     print result['name']
document 7
document 8

>>> results = conn.search('eight author:eight')
>>> for result in results:
...     print result['name']
document 8
document 7

"""

# TODO: unicode support is pretty sloppy. define it better.

from datetime import datetime
import re
import urllib
import urllib2
from urlparse import urlsplit, urlunsplit

try:
    # for python 2.5
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        # use etree from lxml if it is installed
        from lxml import etree as ET
    except ImportError:
        try:
            # use cElementTree if available
            import cElementTree as ET
        except ImportError:
            try:
                from elementtree import ElementTree as ET
            except ImportError:
                raise ImportError("No suitable ElementTree implementation was found.")

try:
    # For Python < 2.6 or people using a newer version of simplejson
    import simplejson as json
except ImportError:
    # For Python >= 2.6
    import json

try:
    # Desirable from a timeout perspective.
    from httplib2 import Http
    TIMEOUTS_AVAILABLE = True
except ImportError:
    from httplib import HTTPConnection
    TIMEOUTS_AVAILABLE = False

try:
    set
except NameError:
    from sets import Set as set

__author__ = 'Joseph Kocherhans, Jacob Kaplan-Moss, Daniel Lindsley'
__all__ = ['Solr']
__version__ = (2, 0, 12)

def get_version():
    return "%s.%s.%s" % __version__[0:3]

DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.\d+)?Z$')

class SolrError(Exception):
    pass

class Results(object):
    def __init__(self, docs, hits, highlighting=None, facets=None, spellcheck=None, stats=None):
        self.docs = docs
        self.hits = hits
        self.highlighting = highlighting or {}
        self.facets = facets or {}
        self.spellcheck = spellcheck or {}
        self.stats = stats or {}

    def __len__(self):
        return len(self.docs)

    def __iter__(self):
        return iter(self.docs)

class Solr(object):
    def __init__(self, url, decoder=None, timeout=60):
        self.decoder = decoder or json.JSONDecoder()
        self.url = url
        self.scheme, netloc, path, query, fragment = urlsplit(url)
        self.base_url = urlunsplit((self.scheme, netloc, '', '', ''))
        netloc = netloc.split(':')
        self.host = netloc[0]
        if len(netloc) == 1:
            self.host, self.port = netloc[0], None
        else:
            self.host, self.port = netloc
        self.path = path.rstrip('/')
        self.timeout = timeout
    
    def _send_request(self, method, path, body=None, headers=None):
        if TIMEOUTS_AVAILABLE:
            http = Http(timeout=self.timeout)
            url = self.base_url + path
            
            try:
                headers, response = http.request(url, method=method, body=body, headers=headers)
            except AttributeError:
                # For httplib2.
                raise SolrError("Failed to connect to server at '%s'. Are you sure '%s' is correct? Checking it in a browser might help..." % (url, self.base_url))
            
            if int(headers['status']) != 200:
                raise SolrError(self._extract_error(headers, response))
            
            return response
        else:
            if headers is None:
                headers = {}
            
            conn = HTTPConnection(self.host, self.port)
            conn.request(method, path, body, headers)
            response = conn.getresponse()
            
            if response.status != 200:
                raise SolrError(self._extract_error(dict(response.getheaders()), response.read()))
            
            return response.read()

    def _select(self, params):
        # encode the query as utf-8 so urlencode can handle it
        params['q'] = params['q'].encode('utf-8')
        # specify json encoding of results
        params['wt'] = 'json'
        
        if len(params['q']) < 1024:
            # Typical case.
            path = '%s/select/?%s' % (self.path, urllib.urlencode(params, True))
            return self._send_request('GET', path)
        else:
            # Handles very long queries by submitting as a POST.
            path = '%s/select/' % (self.path,)
            headers = {
                'Content-type': 'application/x-www-form-urlencoded; charset=utf-8',
            }
            body = urllib.urlencode(params, False)
            return self._send_request('POST', path, body=body, headers=headers)
    
    def _mlt(self, params):
        # encode the query as utf-8 so urlencode can handle it
        params['q'] = params['q'].encode('utf-8')
        params['wt'] = 'json' # specify json encoding of results
        path = '%s/mlt/?%s' % (self.path, urllib.urlencode(params, True))
        return self._send_request('GET', path)

    def _update(self, message, clean_ctrl_chars=True, commit=True):
        """
        Posts the given xml message to http://<host>:<port>/solr/update and
        returns the result.
        
        Passing `sanitize` as False will prevent the message from being cleaned
        of control characters (default True). This is done by default because
        these characters would cause Solr to fail to parse the XML. Only pass
        False if you're positive your data is clean.
        """
        path = '%s/update/' % self.path
        
        # Per http://wiki.apache.org/solr/UpdateXmlMessages, we can append a
        # ``commit=true`` to the URL and have the commit happen without a
        # second request.
        if commit:
            path += '?commit=true'
        
        # Clean the message of ctrl characters.
        if clean_ctrl_chars:
            message = sanitize(message)
        
        return self._send_request('POST', path, message, {'Content-type': 'text/xml; charset=utf-8'})
    
    def _extract_error(self, headers, response):
        """
        Extract the actual error message from a solr response.
        """
        reason = headers.get('reason', None)
        full_html = None
        
        if reason is None:
            reason, full_html = self._scrape_response(headers, response)
        
        msg = "[Reason: %s]" % reason
        
        if reason is None:
            msg += "\n%s" % full_html
        
        return msg
    
    def _scrape_response(self, headers, response):
        """
        Scrape the html response.
        """
        # identify the responding server
        server_type = None
        server_string = headers.get('server', None)
        
        if 'jetty' in server_string.lower():
            server_type = 'jetty'
        
        if 'coyote' in server_string.lower():
            # TODO: During the pysolr 3 effort, make this no longer a
            #       conditional and consider using ``lxml.html`` instead.
            from BeautifulSoup import BeautifulSoup
            server_type = 'tomcat'
        
        reason = None
        full_html = ''
        dom_tree = None
        
        if server_type == 'tomcat':
            # Tomcat doesn't produce a valid XML response
            soup = BeautifulSoup(response)
            body_node = soup.find('body')
            p_nodes = body_node.findAll('p')
            
            for p_node in p_nodes:
                children = p_node.findChildren()
                
                if len(children) >= 2 and 'message' in children[0].renderContents().lower():
                    reason = children[1].renderContents()
            
            if reason is None:
                full_html = soup.prettify()
        else:
            # Let's assume others do produce a valid XML response
            try:
                dom_tree = ET.fromstring(response)
                reason_node = None
                
                # html page might be different for every server
                if server_type == 'jetty':
                    reason_node = dom_tree.find('body/pre')
                
                if reason_node is not None:
                    reason = reason_node.text
                
                if reason is None:
                    full_html = ET.tostring(dom_tree)
            except SyntaxError, e:
                full_html = "%s" % response
        
        full_html = full_html.replace('\n', '')
        full_html = full_html.replace('\r', '')
        full_html = full_html.replace('<br/>', '')
        full_html = full_html.replace('<br />', '')
        full_html = full_html.strip()
        return reason, full_html
    
    # Conversion #############################################################
    
    def _from_python(self, value):
        """
        Converts python values to a form suitable for insertion into the xml
        we send to solr.
        """
        if hasattr(value, 'strftime'):
            if hasattr(value, 'hour'):
                value = "%sZ" % value.isoformat()
            else:
                value = "%sT00:00:00Z" % value.isoformat()
        elif isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'
        else:
            value = unicode(value)
        return value
    
    def _to_python(self, value):
        """
        Converts values from Solr to native Python values.
        """
        if isinstance(value, (int, float, long, complex)):
            return value
        
        if isinstance(value, (list, tuple)):
            value = value[0]
        
        if value == 'true':
            return True
        elif value == 'false':
            return False
        
        if isinstance(value, basestring):
            possible_datetime = DATETIME_REGEX.search(value)
        
            if possible_datetime:
                date_values = possible_datetime.groupdict()
            
                for dk, dv in date_values.items():
                    date_values[dk] = int(dv)
            
                return datetime(date_values['year'], date_values['month'], date_values['day'], date_values['hour'], date_values['minute'], date_values['second'])
        
        try:
            # This is slightly gross but it's hard to tell otherwise what the
            # string's original type might have been. Be careful who you trust.
            converted_value = eval(value)
            
            # Try to handle most built-in types.
            if isinstance(converted_value, (list, tuple, set, dict, int, float, long, complex)):
                return converted_value
        except:
            # If it fails (SyntaxError or its ilk) or we don't trust it,
            # continue on.
            pass
        
        return value
    
    def _is_null_value(self, value):
        """
        Check if a given value is ``null``.
        
        Criteria for this is based on values that shouldn't be included
        in the Solr ``add`` request at all.
        """
        # TODO: This should probably be removed when solved in core Solr level?
        return (value is None) or (isinstance(value, basestring) and len(value) == 0)
    
    # API Methods ############################################################
    
    def search(self, q, **kwargs):
        """Performs a search and returns the results."""
        params = {'q': q}
        params.update(kwargs)
        response = self._select(params)
        
        # TODO: make result retrieval lazy and allow custom result objects
        result = self.decoder.decode(response)
        result_kwargs = {}
        
        if result.get('highlighting'):
            result_kwargs['highlighting'] = result['highlighting']
        
        if result.get('facet_counts'):
            result_kwargs['facets'] = result['facet_counts']
        
        if result.get('spellcheck'):
            result_kwargs['spellcheck'] = result['spellcheck']
        
        if result.get('stats'):
            result_kwargs['stats'] = result['stats']
        
        return Results(result['response']['docs'], result['response']['numFound'], **result_kwargs)
    
    def more_like_this(self, q, mltfl, **kwargs):
        """
        Finds and returns results similar to the provided query.
        
        Requires Solr 1.3+.
        """
        params = {
            'q': q,
            'mlt.fl': mltfl,
        }
        params.update(kwargs)
        response = self._mlt(params)
        
        result = self.decoder.decode(response)
        
        if result['response'] is None:
            result['response'] = {
                'docs': [],
                'numFound': 0,
            }
        
        return Results(result['response']['docs'], result['response']['numFound'])
    
    def add(self, docs, commit=True, boost=None):
        """Adds or updates documents. For now, docs is a list of dictionaries
        where each key is the field name and each value is the value to index.
        """
        message = ET.Element('add')
        
        for doc in docs:
            d = ET.Element('doc')
            
            for key, value in doc.items():
                if key == 'boost':
                    d.set('boost', str(value))
                    continue
                
                # handle lists, tuples, and other iterables
                if hasattr(value, '__iter__'):
                    for v in value:
                        if self._is_null_value(value):
                            continue
                        
                        if boost and v in boost:
                            f = ET.Element('field', name=key, boost=boost[v])
                        else:
                            f = ET.Element('field', name=key)
                        
                        f.text = self._from_python(v)
                        d.append(f)
                # handle strings and unicode
                else:
                    if self._is_null_value(value):
                        continue
                    
                    if boost and key in boost:
                        f = ET.Element('field', name=key, boost=boost[key])
                    else:
                        f = ET.Element('field', name=key)
                    f.text = self._from_python(value)
                    d.append(f)
            
            message.append(d)
        
        m = ET.tostring(message, 'utf-8')
        response = self._update(m, commit=commit)
    
    def delete(self, id=None, q=None, commit=True, fromPending=True, fromCommitted=True):
        """Deletes documents."""
        if id is None and q is None:
            raise ValueError('You must specify "id" or "q".')
        elif id is not None and q is not None:
            raise ValueError('You many only specify "id" OR "q", not both.')
        elif id is not None:
            m = '<delete><id>%s</id></delete>' % id
        elif q is not None:
            m = '<delete><query>%s</query></delete>' % q
        
        response = self._update(m, commit=commit)
    
    def commit(self):
        response = self._update('<commit />')
    
    def optimize(self):
        response = self._update('<optimize />')


class SolrCoreAdmin(object):
    """
    Handles core admin operations: see http://wiki.apache.org/solr/CoreAdmin
    
    Operations offered by Solr are:
       1. STATUS
       2. CREATE
       3. RELOAD
       4. RENAME
       5. ALIAS
       6. SWAP
       7. UNLOAD
       8. LOAD (not currently implemented)
    """
    def __init__(self, url, *args, **kwargs):
        super(SolrCoreAdmin, self).__init__(*args, **kwargs)
        self.url = url
    
    def _get_url(self, url, params={}, headers={}):
        request = urllib2.Request(url, data=urllib.urlencode(params), headers=headers)
        # Let ``socket.error``, ``urllib2.HTTPError`` and ``urllib2.URLError``
        # propagate up the stack.
        response = urllib2.urlopen(request)
        return response.read()
    
    def status(self, core=None):
        """http://wiki.apache.org/solr/CoreAdmin#head-9be76f5a459882c5c093a7a1456e98bea7723953"""
        params = {
            'action': 'STATUS',
        }
        
        if core is not None:
            params.update(core=core)
        
        return self._get_url(self.url, params=params)
    
    def create(self, name, instance_dir=None, config='solrcofig.xml', schema='schema.xml'):
        """http://wiki.apache.org/solr/CoreAdmin#head-7ca1b98a9df8b8ca0dcfbfc49940ed5ac98c4a08"""
        params = {
            'action': 'STATUS',
            'name': name,
            'config': config,
            'schema': schema,
        }
        
        if instance_dir is None:
            params.update(instanceDir=name)
        else:
            params.update(instanceDir=instance_dir)
        
        return self._get_url(self.url, params=params)
    
    def reload(self, core):
        """http://wiki.apache.org/solr/CoreAdmin#head-3f125034c6a64611779442539812067b8b430930"""
        params = {
            'action': 'RELOAD',
            'core': core,
        }
        return self._get_url(self.url, params=params)
    
    def rename(self, core, other):
        """http://wiki.apache.org/solr/CoreAdmin#head-9473bee1abed39e8583ba45ef993bebb468e3afe"""
        params = {
            'action': 'RENAME',
            'core': core,
            'other': other,
        }
        return self._get_url(self.url, params=params)
    
    def alias(self, core, other):
        """
        http://wiki.apache.org/solr/CoreAdmin#head-8bf9004eaa4d86af23d2758aafb0d31e2e8fe0d2
        
        Experimental feature in Solr 1.3
        """
        params = {
            'action': 'ALIAS',
            'core': core,
            'other': other,
        }
        return self._get_url(self.url, params=params)
    
    def swap(self, core, other):
        """http://wiki.apache.org/solr/CoreAdmin#head-928b872300f1b66748c85cebb12a59bb574e501b"""
        params = {
            'action': 'SWAP',
            'core': core,
            'other': other,
        }
        return self._get_url(self.url, params=params)
    
    def unload(self, core):
        """http://wiki.apache.org/solr/CoreAdmin#head-f5055a885932e2c25096a8856de840b06764d143"""
        params = {
            'action': 'UNLOAD',
            'core': core,
        }
        return self._get_url(self.url, params=params)
        
    def load(self, core):
        raise NotImplementedError('Solr 1.4 and below do not support this operation.')


# Using two-tuples to preserve order.
REPLACEMENTS = (
    # Nuke nasty control characters.
    ('\x00', ''), # Start of heading
    ('\x01', ''), # Start of heading
    ('\x02', ''), # Start of text
    ('\x03', ''), # End of text
    ('\x04', ''), # End of transmission
    ('\x05', ''), # Enquiry
    ('\x06', ''), # Acknowledge
    ('\x07', ''), # Ring terminal bell
    ('\x08', ''), # Backspace
    ('\x0b', ''), # Vertical tab
    ('\x0c', ''), # Form feed
    ('\x0e', ''), # Shift out
    ('\x0f', ''), # Shift in
    ('\x10', ''), # Data link escape
    ('\x11', ''), # Device control 1
    ('\x12', ''), # Device control 2
    ('\x13', ''), # Device control 3
    ('\x14', ''), # Device control 4
    ('\x15', ''), # Negative acknowledge
    ('\x16', ''), # Synchronous idle
    ('\x17', ''), # End of transmission block
    ('\x18', ''), # Cancel
    ('\x19', ''), # End of medium
    ('\x1a', ''), # Substitute character
    ('\x1b', ''), # Escape
    ('\x1c', ''), # File separator
    ('\x1d', ''), # Group separator
    ('\x1e', ''), # Record separator
    ('\x1f', ''), # Unit separator
)

def sanitize(data):
    fixed_string = data
    
    for bad, good in REPLACEMENTS:
        fixed_string = fixed_string.replace(bad, good)
    
    return fixed_string


if __name__ == "__main__":
    import doctest
    doctest.testmod()
