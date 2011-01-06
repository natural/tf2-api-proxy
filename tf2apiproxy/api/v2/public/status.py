#!/usr/bin/env python
# -*- coding: utf-8 -*-
from re import search

from tf2apiproxy.lib import ApiHandler


class Status(ApiHandler):
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
    read_size = 1024

    @property
    def cache_key(self):
	return self.path_tail

    @property
    def remote_url(self):
	id64 = self.path_tail
	return self.status_url_fs % (id64, )

    def load(self, chunk):
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



main = Status.make_main()


if __name__ == '__main__':
    main()
