#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tf2apiproxy.lib import ApiHandler


##
## Proxy for the items of a given Steam ID.  Does not support language codes.
##
class News(ApiHandler):
    cache_time = 60 * 15
    count = 5
    max_length = 256
    news_url = ('http://api.steampowered.com/ISteamNews/GetNewsForApp/v0001/'
		'?appid=440&count=%s&maxlength=%s&format=json')

    @property
    def cache_key(self):
	return self.remote_url

    @property
    def remote_url(self):
	return self.news_url % (self.count, self.max_length, )


main = News.make_main()


if __name__ == '__main__':
    main()
