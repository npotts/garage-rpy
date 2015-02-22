#!/usr/bin/python

import sys
import os, os.path
import string
import random
import cherrypy

from grpy import grpycfg, gsensors

from random import randint

class StringGenerator(object):
   @cherrypy.expose
   def index(self):
       return open('www/index.html')

class GaragePyWebService(object):
    exposed = True

    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        # return cherrypy.session['mystring']
        pass

    def POST(self, smashit=None, length=None, pos=None):
        global sensors
        if smashit:
            sensors.pulseGPIO()
            return "Garage Button Triggered."
        if pos:
            pos = sensors.dict()[0]["value"]; #dump of everything
            print(pos)
            return '{"pos":%d, "spos":"%s"}' % (pos,  "closed" if pos < 5 else "open")
        return "error"

    def PUT(self, another_string):
        # cherrypy.session['mystring'] = another_string
        pass

    def DELETE(self):
        # cherrypy.session.pop('mystring', None)
        pass

if __name__ == '__main__':
    if "-p" in sys.argv:
        pidfile = sys.argv[sys.argv.index("-p")+1]
        print("Writing PID to %s" % pidfile)
        pid = open(pidfile, "w")
        pid.write("%d" % os.getpid())
        pid.close()
    global sensors
    cfg = grpycfg("config.ini")
    sensors = gsensors(cfg)
    conf = {
        'global': {
            "server.socket_host": '0.0.0.0',
            "server.socket_port": 80,
        },
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/generator': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        },
        '/www': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './www'
        }
    }
    webapp = StringGenerator()
    webapp.generator = GaragePyWebService()
    cherrypy.quickstart(webapp, '/', conf)