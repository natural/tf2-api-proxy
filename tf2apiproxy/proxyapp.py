#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cgi import parse_qs as parseqs
from datetime import datetime, timedelta
from logging import info, error
from os import path
from re import search
from urllib2 import urlopen, quote as urlquote
from wsgiref.util import application_uri

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app

from simplejson import loads as jsonloads, dumps as jsondumps


def api_keys():
    return [key.strip() for key in open('../apikey.txt').readlines()]
api_keys = api_keys()


def api_key_factory():
    return {'WEB_API_KEY':api_keys[0]}


def environ_extras_middleware(app, factory=api_key_factory):
    def environ_extras_app(environ, start_response):
	environ.update(factory())
	return app(environ, start_response)
    return environ_extras_app


class History(db.Model):
    url = db.StringProperty(required=True, indexed=True)
    payload = db.TextProperty()


class ProxyApp(RequestHandler):
    ##
    ## Base class for proxy app handlers.
    ##
    cache_time = 60 * 60

    def web_api_key(self):
	return self.request.environ.get('WEB_API_KEY', '')

    def request_lang(self, default='en'):
	lang = default
	try:
	    values = parseqs(self.request.query_string).get('lang', (lang, ))
	    lang = values[0].lower()
	except:
	    pass
	return lang

    def cache_get(self, *subkeys):
	key = '-'.join((self.__class__.__name__, ) + subkeys)
	value = memcache.get(key)
	info('cache get: %s, hit: %s', key, value is not None)
	return value

    def cache_set(self, value, *subkeys, **kwds):
	key = '-'.join((self.__class__.__name__, ) + subkeys)
	vlen = len(value) if isinstance(value, (basestring, list, tuple, )) else '?'
	info('cache set: %s, type: %s, len: %s', key, type(value).__name__, vlen)
	return memcache.set(key, value, kwds.get('time', self.cache_time))

    def write_json(self, value, seconds):
	if not isinstance(value, (basestring, )):
	    value = jsondumps(value, indent=4)
	self.response.headers['Content-Type'] = 'application/x-javascript'
	self.response.headers['Expires'] =  (datetime.now() + timedelta(hours=1)).ctime()
	self.response.headers['Cache-Control'] = 'max-age=' + str(seconds)
	cb = parseqs(self.request.query_string).get('callback', (None, ))[0]
	if cb:
	    value = '%s(%s)' % (cb, value)
	self.response.out.write(value)



class SchemaApp(ProxyApp):
    ##
    ## Proxy for the TF2 items schema.  Supports language codes via
    ## the 'lang=' query string parameter.
    ##
    schema_url_fs = ('http://api.steampowered.com/ITFItems_440/GetSchema/v0001/'
                     '?key=%s&format=json&language=%s')

    img_fixes = {
	5027 : 'media/img/TF_Tool_PaintCan_1.png',
	5028 : 'media/img/TF_Tool_PaintCan_2.png',
	5029 : 'media/img/TF_Tool_PaintCan_3.png',
	5030 : 'media/img/TF_Tool_PaintCan_4.png',
	5031 : 'media/img/TF_Tool_PaintCan_5.png',
	5032 : 'media/img/TF_Tool_PaintCan_6.png',
	5033 : 'media/img/TF_Tool_PaintCan_7.png',
	5034 : 'media/img/TF_Tool_PaintCan_8.png',
	5035 : 'media/img/TF_Tool_PaintCan_9.png',
	5036 : 'media/img/TF_Tool_PaintCan_10.png',
	5037 : 'media/img/TF_Tool_PaintCan_11.png',
	5038 : 'media/img/TF_Tool_PaintCan_12.png',
	5039 : 'media/img/TF_Tool_PaintCan_13.png',
	5040 : 'media/img/TF_Tool_PaintCan_14.png',

	5051 : 'media/img/TF_Tool_PaintCan_15.png',
	5052 : 'media/img/TF_Tool_PaintCan_16.png',
	5053 : 'media/img/TF_Tool_PaintCan_17.png',
	5054 : 'media/img/TF_Tool_PaintCan_18.png',
	5055 : 'media/img/TF_Tool_PaintCan_19.png',
	5056 : 'media/img/TF_Tool_PaintCan_20.png',
    }


    def get(self):
	schema = self.get_schema(self.request_lang())
	self.write_json(schema, seconds=self.cache_time)

    def format_url(self, lang):
	return self.schema_url_fs % (self.web_api_key(), lang, )

    def get_schema(self, lang):
	## 0.  memcache hit -> response
	schema = self.cache_get(lang)
	if schema:
	    return schema
	url = self.format_url(lang)

	## 1. mmemcache miss -> url fetch
	try:
	    schema = jsonloads(urlopen(url).read())
	    app_uri = application_uri(self.request.environ)
	    img_fixes = self.img_fixes
	    for item in schema['result']['items']['item']:
		if item['defindex'] in img_fixes:
		    item['image_url'] = app_uri + img_fixes[item['defindex']]
	except (Exception, ), exc:
	    ## 1a.  fetch failure -> history lookup
	    storage = History.all().filter('url =', url).get()
	    if storage:
		## this assumes that the schema has already been
		## parsed and fixed at least one time.
		schema = jsonloads(storage.payload)
		self.cache_set(schema, lang)
	    else:
		## 1b. total failure
		schema = {}
	else:
	    ## 2.  store in cache and history table; the size should
	    ## be okay because the schema was parsed successfully.
	    storage = History.all().filter('url =', url).get()
	    if storage is None:
		storage = History(url=url)
	    storage.payload = jsondumps(schema, indent=4)
	    storage.put()
	    self.cache_set(schema, lang)
	return schema


class ItemsApp(ProxyApp):
    ##
    ## Proxy for the items of a given Steam ID.  Does not support language codes.
    ##
    cache_time = 60 * 5
    items_url_fs = ('http://api.steampowered.com/ITFItems_440/GetPlayerItems/v0001/'
		    '?key=%s&SteamID=%s')

    def get(self, id64):
	self.write_json(self.get_items(id64), seconds=self.cache_time)

    def get_items(self, id64):
	## 0.  memcache hit -> response
	items = self.cache_get(id64)
	if items:
	    return items
	url = self.format_url(id64)

	## 1.  memcache miss -> url fetch
	try:
	    items = jsonloads(urlopen(url).read())['result']['items']['item']
	except (Exception, ), exc:
	    ## 1a.  fetch failure -> history lookup
	    storage = History.all().filter('url =', url).get()
	    if storage:
		items = jsonloads(storage.payload)
		self.cache_set(items, id64)
	    else:
		## 1b.  total failure
		items = {}
	else:
	    ## 2.  store in cache and history table
	    storage = History.all().filter('url =', url).get()
	    if storage is None:
		storage = History(url=url)
	    storage.payload = jsondumps(items, indent=4)
	    storage.put()
	    self.cache_set(items, id64)
	return items

    def format_url(self, id64):
	return self.items_url_fs % (self.web_api_key(), id64, )


class SearchApp(ProxyApp):
    ##
    ## Proxy for searching for a Steam ID by profile name.
    ##
    cache_time = 60 * 5
    community_url = 'http://steamcommunity.com/'
    search_url = community_url + 'actions/Search?T=Account&K=%s'
    id_lookup_url = community_url + 'id/%s/?xml=1'

    def get(self, name):
	self.write_json(self.search(name), seconds=self.cache_time)

    def search(self, name):
	# See CREDITS.txt for copyright.
	## 0. memcache hit -> response
	results = self.cache_get(name)
	if results:
	    return results

	search_url = self.format_url(name)
	try:
	    try:
		res = urlopen(search_url).read().split('<a class="linkTitle" href="')
	    except (Exception, ), exc:
		res = [] # wha?
	    results = []
	    for user in res:
		if user.startswith(self.community_url):
		    userobj = {
			'persona': user[user.find('>') + 1:user.find('<')],
			'id': path.basename(user[:user.find('"')])
			}
		    if user.startswith(self.community_url + 'profiles'):
			userobj['id_type'] = 'id64'
		    else:
			userobj['id_type'] = 'id'
			try:
			    exres = urlopen(self.id_lookup_url % userobj['id']).read(128)
			    id64 = exres[exres.find('<steamID64>'):exres.find('</steamID64>')].split('>')[1]
			except (Exception, ):
			    raise
			else:
			    userobj['id'] = id64
			    userobj['id_type'] = 'id64'

		    results.append(userobj)
	except (Exception, ), exc:
	    results = ({'exception':str(exc), })
	self.cache_set(results, name)
	return results

    def format_url(self, name):
	return self.search_url % (urlquote(name), )



class ProfileApp(ProxyApp):
    ##
    ## Proxy for the profile of a given Steam ID.  Does not support
    ## language codes.
    ##
    cache_time = 60 * 5
    profile_url_fs = ('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0001/'
		      '?key=%s&steamids=%s')

    def get(self, id64):
	self.write_json(self.get_profile(id64), seconds=self.cache_time)

    def get_profile(self, id64):
	## 0. memcache hit -> response
	profile = self.cache_get(id64)
	if profile:
	    return profile
	url = self.format_url(id64)

	## 1.  memcache miss -> url fetch
	try:
	    profile = jsonloads(urlopen(url).read())
	    if not self.is_public(profile):
		profile = {'exception':'private profile'}
	    else:
		profile = self.reformat_profile(profile)
	except (Exception, ), exc:
	    ## 1a.  fetch failure -> history lookup
	    storage = History.all().filter('url =', url).get()
	    if storage:
		profile = jsonloads(storage.payload)
		self.cache_set(profile, id64)
	    else:
		## 1b.  total failure
		profile = {}
	else:
	    ## 2.  store in cache and history table
	    storage = History.all().filter('url =', url).get()
	    if storage is None:
		storage = History(url=url)
	    storage.payload = jsondumps(profile, indent=4)
	    storage.put()
	    self.cache_set(profile, id64)
	return profile

    def is_public(self, data):
	try:
	    return data['response']['players']['player'][0]['communityvisibilitystate'] == 3
	except (Exception, ):
	    return False

    def reformat_profile(self, data):
	player = data['response']['players']['player'][0]
	keys = ['steamid', 'personaname', 'profileurl', 'avatar',
		'avatarmedium', 'avatarfull']
	## help JSON.parse in chrome not suck
	player['steamid'] = str(player['steamid'])
	return dict([(k, player[k]) for k in keys])

    def format_url(self, id64):
	return self.profile_url_fs % (self.web_api_key(), id64)


class OnlineStatusApp(ProxyApp):
    cache_time = 60 * 15
    status_url_fs = 'http://steamcommunity.com/profiles/%s/?xml=1'
    status_rxs = (
	('avatar_full', '<avatarFull><!\[CDATA\[(.*?)\]\]>'),
	('avatar_icon', '<avatarIcon><!\[CDATA\[(.*?)\]\]>'),
	('avatar_medium', '<avatarMedium><!\[CDATA\[(.*?)\]\]>'),
	('message_state', '<stateMessage><!\[CDATA\[(.*?)\]\]>'),
	('name', '<steamID><!\[CDATA\[(.*?)\]\]>'),
	('online_state', '<onlineState>(.*?)</onlineState>'),
    )

    def format_url(self, id64):
	return self.status_url_fs % (id64, )

    def parse_raw(self, chunk):
	val = {}
	for name, rx in self.status_rxs:
	    try:
		txt = search(rx, chunk).groups()[0]
		try:
		    txt = unicode(txt)
		except (UnicodeDecodeError, ):
		    txt = unicode(txt, errors='ignore')
		val[name] = txt
	    except (AttributeError, IndexError, ):
		pass
	return val

    def get(self, id64):
	self.write_json(self.get_status(id64), seconds=self.cache_time)

    def get_status(self, id64):
	status = self.cache_get(id64)
	if status:
	    return status

	## 1.  memcache miss -> url fetch
	url = self.format_url(id64)
	try:
	    raw_status = urlopen(url).read(1024)
	except (Exception, ), exc:
	    ## 1a. memcache miss -> fetch failure -> history lookup
	    storage = History.all().filter('url =', url).get()
	    if storage:
		status = jsonloads(storage.payload)
		self.cache_set(status, id64)
	    else:
		## 1b. memcache miss -> fetch failure -> history failure =total failure
		status = {}
	else:
	    ## 2.  parse, and if successful, store in cache and history table
	    try:
		status = self.parse_raw(raw_status)
	    except (Exception, ), exc:
		## 2a. parse failure
		status = {}
	    else:
		storage = History.all().filter('url =', url).get()
		if storage is None:
		    storage = History(url=url)
		storage.payload = jsondumps(status, indent=4)
		storage.put()
		self.cache_set(status, id64)
	return status


class NewsApp(ProxyApp):
    cache_time = 60 * 15
    count = 5
    max_length = 256
    news_url = ('http://api.steampowered.com/ISteamNews/GetNewsForApp/v0001/'
		'?appid=440&count=%s&maxlength=%s&format=json')


    def get(self):
	self.write_json(self.get_news(), seconds=self.cache_time)

    def get_news(self):
	url = self.news_url % (self.count, self.max_length)
	news = self.cache_get(url)
	if news:
	    return news
	try:
	    news = jsonloads(urlopen(url).read())['appnews']['newsitems']['newsitem']
	except (Exception, ), exc:
	    news = []
	else:
	    self.cache_set(news, url)
	return news


routes = (
    (r'/api/v1/items/(?P<id64>\d{17})', ItemsApp),
    (r'/api/v1/profile/(?P<id64>\d{17})', ProfileApp),
    (r'/api/v1/search/(?P<name>.{1,32})', SearchApp),
    (r'/api/v1/status/(?P<id64>\d{17})', OnlineStatusApp),
    (r'/api/v1/schema', SchemaApp),
    (r'/api/v1/news', NewsApp),
)


def main():
    app = WSGIApplication(routes)
    app = environ_extras_middleware(app)
    run_wsgi_app(app)


if __name__ == '__main__':
    main()
