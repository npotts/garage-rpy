import sys
import json
import asyncore
import socket
from sensors import gsensors, grpycfg


class CommandHandler(asyncore.dispatcher_with_send):
  global sensors
  __help_text = """
Available commands:
help              Show this message
config            dump the ini configuration 
count <channel>   Retrieves the raw count values of a2d <channel>
value <channel>   Retrieves the converted value of the a2d <channel>
v     <channel>   Retrieves the converted value of the a2d <channel> with units
pulsegpio         Pulse gpio pin # as set in the configuration
quit|exit         Close the socket connection

Additionally, if valid JSON document is passed, with the 
key of "channels" defined to be an array of channels to 
query such as:
  
  {
    "channels": [0, 3, 4]
  }

A JSON document similar to below will be returned:
  {
    "counts": [514, 1024, 152], 
    "values": [2.43, 4690, 25],
    "units": ['V', 'mV', 'C']
  }

Where the indexes of the array are mapped to channel 
#0, 3, and 4 respectively. It is also possible to set
the "pulsegpio" via a "pulsegpio": 1 directive, or
you can sever the socket connection after via setting a 
"quit" or "exit" section.  Their values are ignored.

EG:

{"channels": [0], "pulsegpio": 1, "exit": 0} 

would:

- Return something like: {"counts": [514], "values": [2.5], "units": ['V'], "pulsed": 1}
- Pulse the GPIO as per the config, and
- Close the socket.

"""
  def parseCommand(self, cmd):
    """Parses the actual commands and returns a string of what the"""
    global sensors
    cmd = cmd.lower()
    rtn = "Unknown command '%s'.  Try 'help'" % cmd
    if cmd == "help": return self.send(self.__help_text)
    if cmd == "quit" or cmd == "exit": 
      self.send("Closing connection\n")
      self.close()
    if cmd.startswith("pulsegpio"):
      sensors.pulseGPIO();
      return self.send("GPIO #%d Pulsed\n>" % sensors.cfg.gpio_pin)
    if cmd.startswith("count") or cmd.startswith("value") or cmd.startswith("v"):
      try:
        channel = int(cmd.split(" ")[1])
      except:
        return self.send("Error: '%s' is incorrect usage\n>" % cmd);
      try:
        data = sensors.readValue(channel)
      except:
        return self.send("Error:  Unable to query SPI device\n>");
      if cmd.startswith("count"):
        return self.send("%d\n>" % data[0])
      if cmd.startswith("value"):
        return self.send("%s\n>" % data[1])
      if cmd.startswith("v"):
        return self.send("%1.2f %s \n>" % (data[1], data[2]))

    try:
      j = json.loads(cmd)
    except: #not a JSON message
      return 
    #some sort of JSON messages
    rtn={}

    try: #give a decent attempt to decode the channels
      if "pulsegpio" in j:
        try:
          sensors.pulseGPIO()
          rtn["pulsed"] = 1
        except Exception as e:
          print(e)
          rtn["pulsed"] = 0
        del(j["pulsegpio"])
      if len(rtn) != 0 and "channels" not in j:
        return self.send("%s\n" % json.dumps(rtn))
      looksOk = True
      for chan in j["channels"]:
        if int(chan) != chan:
          looksOk = False
      if (looksOk):
        rtn["counts"] = []
        rtn["values"] = []
        rtn["units"] = []
        for chan in j["channels"]:
          d = sensors.readValue(chan)
          rtn["counts"].append(d[0])
          rtn["values"].append(d[1])
          rtn["units"].append(d[2])
    except Exception as e:
      print(e)
      return self.send('Error: Malformed "channels" section\n>')
    self.send("%s\n" % json.dumps(rtn))
    if "exit" in j or "quit" in j:
      return self.close();


  def handle_read(self):
    data = self.recv(8192)
    if data:
      commands = data.splitlines()
      for cmd in commands:
        if cmd == '':
          self.send(">")
          continue
        self.parseCommand(cmd.strip())
  
class SensorServer(asyncore.dispatcher):
  def __init__(self, host, port):
    asyncore.dispatcher.__init__(self)
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.set_reuse_addr()
    self.bind((host, port))
    self.listen(5)

  def handle_accept(self):
    pair = self.accept()
    if pair is not None:
      sock, addr = pair
      #sock.send("Welcome to GaragePy!\n>")
      print('Incoming connection from %s' % repr(addr))
      handler = CommandHandler(sock)

def startSocketServer(cfg_fname):
  global sensors
  cfg = grpycfg(cfg_fname)
  sensors = gsensors(cfg)
  server = SensorServer('', cfg.tcp_port)
  asyncore.loop()
