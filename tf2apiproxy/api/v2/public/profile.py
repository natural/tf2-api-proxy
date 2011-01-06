#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tf2apiproxy.lib import ApiHandler


##
## Proxy for the profile of a given Steam ID.  Does not support
## language codes.
##
class Profile(ApiHandler):
    cache_time = 60 * 5
    profile_url_fs = ('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0001/'
		      '?key=%s&steamids=%s')

    @property
    def cache_key(self):
	return self.path_tail

    @property
    def remote_url(self):
	id64 = self.path_tail
	return self.profile_url_fs % (self.api_key, id64, ) if id64 else ''

    def cook(self, profile):
	if not self.is_public(profile):
	    profile = {'exception':'private profile'}
	else:
	    player = profile['response']['players']['player'][0]
	    keys = ['steamid', 'personaname', 'profileurl', 'avatar',
		    'avatarmedium', 'avatarfull']
	    ## help JSON.parse in chrome not suck
	    player['steamid'] = str(player['steamid'])
	    profile = dict([(k, player[k]) for k in keys])
	return profile

    def is_public(self, data):
	try:
	    return data['response']['players']['player'][0]['communityvisibilitystate'] == 3
	except (Exception, ):
	    return False


main = Profile.make_main()


if __name__ == '__main__':
    main()
