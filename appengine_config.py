#!/usr/bin/env python
# -*- coding: utf-8 -*-


def api_keys():
    import os, tf2apiproxy
    p = os.path.join(os.path.dirname(tf2apiproxy.__file__), '..', 'apikey.txt')
    return [key.strip() for key in open(p).readlines()]


def api_key_factory():
    return {'WEB_API_KEY':api_keys()[0]}


def environ_extras_middleware(app, factory=api_key_factory):
    def environ_extras_app(environ, start_response):
	environ.update(factory())
	return app(environ, start_response)
    return environ_extras_app


## framework hook to add our middleware
def webapp_add_wsgi_middleware(app):
    return environ_extras_middleware(app)
