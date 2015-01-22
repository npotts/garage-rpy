import os
import time
import math
import logging
try:
  import spidev
except:
  print("Unable to import spidev")
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
            for sensor in cfg.get(spi, "sensors").split(","):
                sensor = sensor.strip()
                #do some magic to allow count to value equations in a config file.
                # yeah, yeah, yeah, you can do something stupid like '__import__("os").system("rm -rf /")',
                # but that is up to the user to figure out.
                s = "lambda cnt: %s" % cfg.get(sensor, "count_to_value")
                rtn["cnt2val"][cfg.getint(sensor, "a2d_port")] = eval(s)
                rtn["spi_names"][cfg.getint(sensor, "a2d_port")] = cfg.get(sensor, "name") 
                rtn["spi_descriptions"][cfg.getint(sensor, "a2d_port")] = cfg.get(sensor, "description")

            #where is the GPIO switch
            switch = cfg.get("general", "open_close_switch")
            rtn["gpio_pin"] = cfg.get(switch, "pin")
            rtn["gpio_idle"] = cfg.get(switch, "idle_state")
            rtn["gpio_pulse"] = cfg.get(switch, "pulse")

            # this goodness merges the self dictionary of items with the one we just read from
            self.__dict__.update(**rtn) 

        except Exception as e:
            print("Unable to parse config properly: %s" % e)
            print("Check your configuration file '%s'" % cfg_file)

class gsensors:
  def __init__(self, cfg):
    self.cnt2val = cfg.cnt2val
    self.spi = spidev.SpiDev()
    self.spi.open(cfg.spi_port, cfg.spi_ce)

  def readRawCounts(self, channel):
    # Function to read SPI data from MCP3208 chip. 
    # channel must be an integer 0-7 adc;
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
    # Function to convert counts to 
    cnt = self.readRawCounts(channel)

    #apply count_to_value for the channel
    return self.cnt2val[channel](cnt)

