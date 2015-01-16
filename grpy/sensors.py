import os
import time
import math
import logging
try:
    import spidev
except:
    pass
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
    self.spi.open(cfg.spidev_port, cfg.spidev_ce)

  def readRawCounts(self, channel):
    # Function to read SPI data from MCP3008 chip channel must be an integer 0-7
    #adc = [0x02, 0x30, 0xff]
    adc = self.spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

  def readValue(self, channel):
    # Function to convert counts to 
    cnt = self.readRawCounts(channel)

    #apply count_to_value for the channel
    return self.cnt2val[channel](cnt)