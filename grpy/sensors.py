import os
import time
import math
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
    GPIO.setwarnings(False)
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
