#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cgi import parse_qs
from datetime import datetime, timedelta
from logging import info, error
from os import environ
from urllib2 import urlopen
from wsgiref.util import application_uri

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import RequestHandler, Request, Response
from google.appengine.ext.webapp.util import run_wsgi_app

from simplejson import dumps as json_dumps, loads as json_loads


devel = environ.get('SERVER_SOFTWARE', '').startswith('Dev')


def wsgi_local(app, debug):
    methods = ('get', 'post', 'head', 'options', 'put', 'delete', 'trace')
    def local(environ, start_response):
	handler = app(Request(environ), Response())
	method = environ['REQUEST_METHOD'].lower()
	if method not in methods:
	    handler.error(405)
	else:
	    call = getattr(handler, method, None)
	    if call is None:
		handler.error(501)
	    else:
		try:
		    call()
		except Exception, e:
		    handler.handle_exception(e, debug)
	handler.response.wsgi_write(start_response)
	return ['']
    return local


class History(db.Model):
    ##
    # History -> stores the result of a url fetch; referenced
    # when fetches fail.
    #
    url = db.StringProperty(required=True, indexed=True)
    payload = db.TextProperty()


class ApiHandler(RequestHandler):
    ##
    # ApiHandler -> base class for proxied api calls.
    #
    cache_time = 60 * 60
    read_size = -1
    fail_value = {}

    def __init__(self, request, response):
	super(RequestHandler, self).__init__()
	self.request = request
	self.response = response

    @property
    def api_key(self):
	return self.request.environ.get('WEB_API_KEY', '')

    @property
    def app_url(self):
	return application_uri(self.request.environ)

    def cache_get(self, *subkeys):
	key = '-'.join((self.__class__.__name__, ) + subkeys)
	value = memcache.get(key)
	info('cache get: %s, hit: %s', key, value is not None)
	return value

    def cache_set(self, value, *subkeys, **kwds):
	key = '-'.join((self.__class__.__name__, ) + subkeys)
	vlen = len(value) if isinstance(value, (basestring, list, tuple, dict)) else '?'
	info('cache set: %s, type: %s, len: %s', key, type(value).__name__, vlen)
	return memcache.set(key, value, kwds.get('time', self.cache_time))

    def cook(self, value):
	return value

    def get(self):
	data = self.remote_api_data()
	self.write_json(data, seconds=self.cache_time)

    def load(self, value):
	return json_loads(value)

    @property
    def path_tail(self):
	return self.request.environ['PATH_INFO'].split('/')[-1]

    def remote_api_data(self):
	## 0.  memcache hit -> response
	v = self.cache_get(self.cache_key)
	if v:
	    return v

	## 1. mmemcache miss -> url fetch
	url = self.remote_url
	try:
	    if not url:
		raise Exception('bad url')
	    data = self.load(urlopen(url).read(self.read_size))
	except (Exception, ), exc:
	    error('error: %s, url: %s', exc, url)
    	    ## 1a.  fetch failure -> history lookup
	    storage = History.all().filter('url =', url).get()
	    if storage:
		## this assumes that the value has already been
		## parsed and cooked at least one time.
		data = self.load(storage.payload)
		self.cache_set(data)
	    else:
		## 1b. total failure
		data = self.fail_value
	else:
	    ## 2a.  cook the new value before storing and sending
	    data = self.cook(data)
	    ## 2b.  store in cache and history
	    storage = History.all().filter('url =', url).get()
	    if storage is None:
		storage = History(url=url)
	    # reparse because it may have changed
	    storage.payload = json_dumps(data, indent=4)
	    storage.put()
	    self.cache_set(data, self.cache_key)
	return data

    @property
    def request_lang(self):
	lang = 'en'
	try:
	    values = parse_qs(self.request.query_string).get('lang', (lang, ))
	    lang = values[0].lower()
	except:
	    pass
	return lang

    def write_json(self, value, seconds):
	if not isinstance(value, (basestring, )):
	    value = json_dumps(value, indent=4)
	self.response.headers['Content-Type'] = 'application/x-javascript'
	self.response.headers['Expires'] =  (datetime.now() + timedelta(hours=1)).ctime()
	self.response.headers['Cache-Control'] = 'max-age=' + str(seconds)
	cb = parse_qs(self.request.query_string).get('callback', (None, ))[0]
	if cb:
	    value = '%s(%s)' % (cb, value)
	self.response.out.write(value)

    @classmethod
    def make_main(cls, debug=devel):
	def main():
	    run_wsgi_app(wsgi_local(cls, debug))
	return main
