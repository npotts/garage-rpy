#!/usr/bin/python

import sys
import io
import os
import os.path
import base64
import picamera
import string
import random
import cherrypy
from grpy import grpycfg, gsensors
from random import randint


class imgcapture:
    """function as a crappy stringio obj with the ability to emit"""
    buffer = ""
    html = ""

    def __init__(self):
        self.buffer = ""

    def write(self, wstr):
        self.buffer += wstr

    def flush(self):
        return

    def htmltag(self, imgfmt, cssClass):
        """returns a fully formed html string to insert as an image"""
        # <img alt="Embedded Image" src="data:image/png;base64,{{base64}}" />
        b64 = base64.standard_b64encode(self.buffer)
        html = """<img class="{}", alt="camera" src="data:image/{};base64,{}" />""".format(cssClass, imgfmt, b64)
        return html

class cmaster:
    """Camera wrapper"""
    camera = None

    def __init__(self):
        self.camera = picamera.PiCamera()
        self.camera.hflip = True
        self.camera.vflip = True
        self.camera.brightness = 70

    def raw(self):
        """returns raw bytes from the image"""
        buf = imgcapture()
        self.camera.capture(buf, "png")
        return buf.buffer
        # return buf.htmltag("png", cssClass)

    def html(self, cssClass="gpix"):
        """returns html <img> with the image encoded in the url"""
        buf = imgcapture()
        self.camera.capture(buf, "png")
        return buf.htmltag("png", cssClass)


class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return open('www/index.html')

class GaragePyWebService(object):
    exposed = True
    camera = None

    def __init__(self):
        self.camera = cmaster()

    @cherrypy.tools.accept(media='image/png')
    def GET(self):
        cherrypy.response.headers['Content-Type'] = "image/png"
        return self.camera.raw()

    def POST(self, smashit=None, length=None, pos=None):
        global sensors
        if smashit:
            sensors.pulseGPIO()
            return "Garage Button Triggered."
        if pos:
            pos = sensors.dict()[0]["value"]  # dump of everything
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
        '/camera': {
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