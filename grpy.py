#!/usr/bin/python
import os
import json
import time
import math
import socket
import asyncore
import logging
import spidev
import RPi.GPIO as GPIO
try:
  import ConfigParser as configparser #python2
except:
  import configparser #python3


class grpycfg:
  """Class that returns an object with variables read from the ini file"""
  def __init__(self, cfg_file):
    """Merge items from **entries to self  Effectivly, this returns
    and object WC that has public variables."""
    try:
      cfg = configparser.SafeConfigParser()
      cfg.read(cfg_file)
      rtn={}

      rtn["tcp_port"] = cfg.getint("general", "tcp_port")
      rtn["loglevel"] = cfg.getint("general", "loglevel")

      #retrieve SPI parameters if present
      spi                = cfg.get("general", "adc_spi")
      rtn["spi_port"]    = cfg.getint(spi, "spidev_port")
      rtn["spi_ce"]      = cfg.getint(spi, "spidev_ce")
      rtn["cnt2val"] = {}
      rtn["spi_names"] = {}
      rtn["spi_descriptions"] = {}
      rtn["spi_units"] = {}
      for sensor in cfg.get(spi, "sensors").split(","):
        sensor = sensor.strip()
        #do some magic to allow count to value equations in a config file.
        # yeah, yeah, yeah, you can do something stupid like '__import__("os").system("rm -rf /")',
        # but that is up to the user to figure out.
        s = "lambda cnt: %s" % cfg.get(sensor, "count_to_value")
        rtn["cnt2val"][cfg.getint(sensor, "a2d_port")] = eval(s)
        rtn["spi_names"][cfg.getint(sensor, "a2d_port")] = cfg.get(sensor, "name") 
        rtn["spi_descriptions"][cfg.getint(sensor, "a2d_port")] = cfg.get(sensor, "description")
        rtn["spi_units"][cfg.getint(sensor, "a2d_port")] = cfg.get(sensor, "units")

      #where is the GPIO switch
      switch = cfg.get("general", "open_close_switch")
      rtn["gpio_pin"] = cfg.getint(switch, "pin")
      rtn["gpio_idle"] = cfg.getint(switch, "idle_state")
      rtn["gpio_pulse"] = cfg.getfloat(switch, "pulse")

      # this goodness merges the self dictionary of items with the one we just read from
      self.__dict__.update(**rtn) 

    except Exception as e:
      print("Unable to parse config properly: %s" % e)
      print("Check your configuration file '%s'" % cfg_file)

class gsensors:
  def __del__(self):
    """Its always a good idea to cleanup"""
    GPIO.cleanup()

  def __init__(self, cfg):
    """Initialize the sensors"""
    self.cfg = cfg #grab a local copy of the config

    #setup SPI
    self.spi = spidev.SpiDev()
    self.spi.open(self.cfg.spi_port, self.cfg.spi_ce)

    #setup GPIO
    GPIO.setmode(GPIO.BCM)
    #GPIO.setwarnings(False)
    GPIO.setup(self.cfg.gpio_pin, GPIO.OUT, initial=int(self.cfg.gpio_idle))
    GPIO.output(self.cfg.gpio_pin, int(self.cfg.gpio_idle))

  def readRawCounts(self, channel):
    """Read raw ADC counts from the MCP3208 chip.  Channel is the ADC channel (0-7) to read from"""
    if (channel < 0) | (channel > 7):
      return -1;
    # A slight difference between the MCP3008 and the MCP3208 is
    # the MCP3208 is a 12-bit device.  Per the MCP3208/MCP3204 datasheet
    # on pg 21, we should:
    #   Shove out 5 zero bits, followed by 1 one bit, followed by 
    #   1 SGL/DIFF bit (=0), followed by 3 channel select bits D2,
    #   D1, and D0 followed by 14 dont care bits (I use zeros) as
    #   The ADC values are clocked into the master.
    
    # Though I do not have the same steps in detail for the MCP3008/MCP3004,
    # the concepts are the same, and you should use this function instead
    #adc = self.spi.xfer2([1,(8+channel)<<4,0])
    #data = (adc[1]&0x03 << 8) + adc[2]
    
    #For 12 bit MCP3208 devices, we ignore the first 12 bits, and keep the last 12
    adc = self.spi.xfer2( [0x06| (channel >> 2), channel << 6, 0])
    data = ((adc[1] & 0x0f) << 8) + adc[2]
    return data

  def readValue(self, channel):
    """Function to convert counts to some "values" via a provided transfer function"""
    cnt = self.readRawCounts(channel)
    return (cnt, self.cfg.cnt2val[channel](cnt), self.cfg.spi_units[channel])

  def pulseGPIO(self):
    """Pulses the GPIO per the configuration"""
    GPIO.output(self.cfg.gpio_pin, not bool(self.cfg.gpio_idle))
    time.sleep(self.cfg.gpio_pulse)
    GPIO.output(self.cfg.gpio_pin, bool(self.cfg.gpio_idle))

class CommandHandler(asyncore.dispatcher_with_send):
  global sensors
  __help_text = """
Available commands:
help              Show this message
config            dump the ini configuration 
count <channel>   Retrieves the raw count values of a2d <channel>
value <channel>   Retrieves the converted value of the a2d <channel>
v     <channel>   Retrieves the converted value of the a2d <channel> with units
pulsegpio         Pulse gpio pin as set in the configuration
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

if __name__ == "__main__":
  import sys
  from subprocess import call
  if not os.geteuid() == 0:
    print("Script must be run as root.  Attempting to re-run as root")
    sys.argv.insert(0, "sudo")
    exit(call(sys.argv))
  startSocketServer(sys.argv[1])

