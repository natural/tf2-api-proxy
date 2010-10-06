#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cgi import parse_qs as parseqs
from logging import info
from os import path
from urllib2 import urlopen, quote as urlquote

from google.appengine.api import memcache
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app

from simplejson import loads as jsonloads, dumps as jsondumps


def api_keys():
    return [key.strip() for key in open('apikey.txt').readlines()]
api_keys = api_keys()


def api_key_factory():
    return {'WEB_API_KEY':api_keys[0]}


def environ_extras_middleware(app, factory=api_key_factory):
    def environ_extras_app(environ, start_response):
	environ.update(factory())
	return app(environ, start_response)
    return environ_extras_app


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

    def write_json(self, value):
	value = jsondumps(value, indent=4)
	self.response.headers['Content-Type'] = 'application/json'
	self.response.headers['Content-Length'] = len(value)
	self.response.out.write(value)



class SchemaApp(ProxyApp):
    ##
    ## Proxy for the TF2 items schema.  Supports language codes via
    ## the 'lang=' query string parameter.
    ##
    schema_url_fs = ('http://api.steampowered.com/ITFItems_440/GetSchema/v0001/'
                     '?key=%s&format=json&language=%s')

    def get(self):
	schema = self.get_schema(self.request_lang())
	self.write_json(schema)

    def format_url(self, lang):
	return self.schema_url_fs % (self.web_api_key(), lang, )

    def get_schema(self, lang):
	schema = self.cache_get(lang)
	if schema:
	    return schema
	schema = jsonloads(urlopen(self.format_url(lang)).read())
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
	self.write_json(self.get_items(id64))

    def get_items(self, id64):
	items = self.cache_get(id64)
	if items:
	    return items
	items = urlopen(self.format_url(id64)).read()
	items = jsonloads(items)['result']['items']['item']
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

    def get(self, name):
	self.write_json(self.search(name))

    def search(self, name):
	# See CREDITS.txt for copyright.
	results = self.cache_get(name)
	if results:
	    return results
	search_url = self.format_url(name)
	try:
	    res = urlopen(search_url).read().split('<a class="linkTitle" href="')
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
	self.write_json(self.get_profile(id64))

    def get_profile(self, id64):
	profile = self.cache_get(id64)
	if profile:
	    return profile
	profile = jsonloads(urlopen(self.format_url(id64)).read())
	if not self.is_public(profile):
	    profile = {'exception':'private profile'}
	else:
	    profile = self.reformat_profile(profile)
	self.cache_set(profile, id64)
	return profile

    def is_public(self, data):
	return data['response']['players']['player'][0]['communityvisibilitystate'] == 3

    def reformat_profile(self, data):
	player = data['response']['players']['player'][0]
	keys = ['steamid', 'personaname', 'profileurl', 'avatar',
		'avatarmedium', 'avatarfull']
	return dict([(k, player[k]) for k in keys])

    def format_url(self, id64):
	return self.profile_url_fs % (self.web_api_key(), id64)


routes = (
    (r'/api/v1/items/(?P<id64>\d{17})', ItemsApp),
    (r'/api/v1/profile/(?P<id64>\d{17})', ProfileApp),
    (r'/api/v1/search/(?P<name>.{1,32})', SearchApp),
    (r'/api/v1/schema', SchemaApp),
)


def main():
    app = WSGIApplication(routes, debug=True)
    app = environ_extras_middleware(app)
    run_wsgi_app(app)


if __name__ == '__main__':
    main()

