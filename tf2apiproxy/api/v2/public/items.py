#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tf2apiproxy.lib import ApiHandler


##
## Proxy for the items of a given Steam ID.  Does not support language codes.
##
class Items(ApiHandler):
    cache_time = 60 * 5
    items_url_fs = ('http://api.steampowered.com/ITFItems_440/GetPlayerItems/v0001/'
		    '?key=%s&SteamID=%s')

    @property
    def cache_key(self):
	return self.path_tail

    @property
    def remote_url(self):
	id64 = self.path_tail
	return self.items_url_fs % (self.api_key, id64, ) if id64 else ''


main = Items.make_main()


if __name__ == '__main__':
    main()
