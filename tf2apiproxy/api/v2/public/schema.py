#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tf2apiproxy.lib import ApiHandler


##
# Proxy for the TF2 items schema.  Supports language codes via
# the 'lang=' query string parameter.
#
class Schema(ApiHandler):
    schema_url_fs = ('http://api.steampowered.com/ITFItems_440/GetSchema/v0001/'
                     '?key=%s&format=json&language=%s')

    img_fixes = {
	5027 : 'media/img/TF_Tool_PaintCan_1.png',      # Indubitably Green
	5028 : 'media/img/TF_Tool_PaintCan_2.png',      # Zephaniah's Greed
	5029 : 'media/img/TF_Tool_PaintCan_3.png',      # Noble Hatter's Violet
	5030 : 'media/img/TF_Tool_PaintCan_4.png',      # Color No. 216-190-216
	5031 : 'media/img/TF_Tool_PaintCan_5.png',      # A Deep Commitment to Purple
	5032 : 'media/img/TF_Tool_PaintCan_6.png',      # Mann Co. Orange
	5033 : 'media/img/TF_Tool_PaintCan_7.png',      # Muskelmannbraun
	5034 : 'media/img/TF_Tool_PaintCan_8.png',      # Peculiarly Drab Tincture
	5035 : 'media/img/TF_Tool_PaintCan_9.png',      # Radigan Conagher Brown
	5036 : 'media/img/TF_Tool_PaintCan_10.png',     # Ye Olde Rustic Colour
	5037 : 'media/img/TF_Tool_PaintCan_11.png',     # Australium Gold
	5038 : 'media/img/TF_Tool_PaintCan_12.png',     # Aged Moustache Grey
	5039 : 'media/img/TF_Tool_PaintCan_13.png',     # An Extraordinary Abundance of Tinge
	5040 : 'media/img/TF_Tool_PaintCan_14.png',     # A Distinctive Lack of Hue
	5051 : 'media/img/TF_Tool_PaintCan_15.png',     # Pink as Hell
	5052 : 'media/img/TF_Tool_PaintCan_16.png',     # A Color Similar to Slate
	5053 : 'media/img/TF_Tool_PaintCan_17.png',     # Drably Olive
	5054 : 'media/img/TF_Tool_PaintCan_18.png',     # The Bitter Taste of Defeat and Lime
	5055 : 'media/img/TF_Tool_PaintCan_19.png',     # The Color of a Gentlemann's Business Pants
	5056 : 'media/img/TF_Tool_PaintCan_20.png',     # Dark Salmon Injustice

        5060 : 'media/img/TF_Tool_PaintCan_5060.png', # operators overalls
        5061 : 'media/img/TF_Tool_PaintCan_5061.png', # waterlogged lab coat
        5062 : 'media/img/TF_Tool_PaintCan_5062.png', # balaclavas are forever
        5063 : 'media/img/TF_Tool_PaintCan_5063.png', # air of debonair
        5064 : 'media/img/TF_Tool_PaintCan_5064.png', # value of teamwork
        5065 : 'media/img/TF_Tool_PaintCan_5065.png', # cream spirit

    }

    @property
    def cache_key(self):
	return self.request_lang

    @property
    def remote_url(self):
	return self.schema_url_fs % (self.api_key, self.request_lang, )

    def cook(self, schema):
	app_url = self.app_url
	img_fixes = self.img_fixes
	for item in schema['result']['items']['item']:
	    if item['defindex'] in img_fixes:
		item['image_url'] = app_url + img_fixes[item['defindex']]
	return schema


main = Schema.make_main()


if __name__ == '__main__':
    main()
