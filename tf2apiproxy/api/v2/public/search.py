#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import path
from urllib2 import urlopen, quote as urlquote

from tf2apiproxy.lib import ApiHandler


##
## Proxy for searching for a Steam ID by profile name.
##
class Search(ApiHandler):
    cache_time = 60 * 5
    community_url = 'http://steamcommunity.com/'
    search_url = community_url + 'actions/Search?T=Account&K=%s'
    id_lookup_url = community_url + 'id/%s/?xml=1'
    fail_value = []

    @property
    def cache_key(self):
	return self.path_tail

    @property
    def remote_url(self):
	return self.search_url % (urlquote(self.path_tail), )

    def cook(self, html):
	# See CREDITS.txt for copyright.
	res = html.split('<a class="linkTitle" href="')
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
	return results

    def load(self, value):
	return value


main = Search.make_main()


if __name__ == '__main__':
    main()
