#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.api import memcache
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app

from proxyapp import SchemaApp, environ_extras_middleware


class CachePrimer(RequestHandler):
    lang_codes = 'da nl en fi fr de hu it ja ko no pl pt ro ru zh es sw'.split()

    def get(self):
	w = self.response.out.write
	w('<html><code>')
	w('purging cache...')
	ok = memcache.flush_all()
	w('<br>...cache purge %s.' % ('okay' if ok else 'fail'))
	w('<br><br>priming schemas...')

	sa = SchemaApp()
	sa.request = self.request
	for lang in self.lang_codes:
	    schema = sa.get_schema(lang)
	    w('<br>    ...got schema for %s, size %s' % (lang, len(str(schema))))
	w('<br>...primed %s schemas.' % len(self.lang_codes))
	w('<br><br>done.')
	w('</code></html>')


routes = (
    (r'/admin.d/purge_and_prime', CachePrimer),
    )


def main():
    app = WSGIApplication(routes, debug=True)
    app = environ_extras_middleware(app)
    run_wsgi_app(app)


if __name__ == '__main__':
    main()

