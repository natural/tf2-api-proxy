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
	5046 : 'media/img/TF_Tool_PaintCan_TeamColor.png',
	5051 : 'media/img/TF_Tool_PaintCan_15.png',
	5052 : 'media/img/TF_Tool_PaintCan_16.png',
	5053 : 'media/img/TF_Tool_PaintCan_17.png',
	5054 : 'media/img/TF_Tool_PaintCan_18.png',
	5055 : 'media/img/TF_Tool_PaintCan_19.png',
	5056 : 'media/img/TF_Tool_PaintCan_20.png',
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
