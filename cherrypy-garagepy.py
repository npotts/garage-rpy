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
        return cherrypy.session['mystring']

    def POST(self, smashit=None, length=None, pos=None):
        if smashit:
        #     data_value='{"units": ["%%", "C"], "counts": [1081, 14], "values": [%d, 34.32199599497977]}'
        # #get some values from the unit.   We will refresh every 10 seconds or so
        # rtn = html_core__
        # progress_bars = ""
        # d = json.loads(data_value % randint(0, 100))
        # print(d)
        # for i in range(len(d["values"])):
        #     progress_bars += "<br />\n" + progress_bar__ % (int(d["values"][i]),  "Test ", d["units"][i])
        #     print(d["values"][i])
        # return rtn % progress_bars;
            # print("\n\nSmashit pressed")
            cherrypy.session["doneit"] = "Yeah baby"
            return "Garage Button Triggered."
        if length:
            # print("\n\nGive it now pressed")
            some_string = ''.join(random.sample(string.hexdigits, int(length)))
            cherrypy.session['mystring'] = "ADSASDA " + some_string
            return some_string
        if pos:
            d = randint(0, 100)
            return '{"pos":%d, "spos":"%s"}' % (d,  "closed" if d > 90 else "open")
        return "ALL SORTS OF CRAP"

    def PUT(self, another_string):
        cherrypy.session['mystring'] = another_string

    def DELETE(self):
        cherrypy.session.pop('mystring', None)

if __name__ == '__main__':
    conf = {
        'global': {
            "server.socket_host": '0.0.0.0',
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