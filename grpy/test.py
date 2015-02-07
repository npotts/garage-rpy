#!/usr/bin/env python

import sys
#import time
#from sensors import grpycfg, gsensors
import sensorServer

if __name__ == "__main__":
  sensorServer.startSocketServer(sys.argv[1])
  
  # cfg = grpycfg(sys.argv[1])
  # g = gsensors(cfg)
  # while(True):
  #   v = g.readValue(0);
  #   t1 = g.readRawCounts(1);
  #   t = g.readValue(1);
  #   sys.stdout.write("\r%04d (%%%3.2f) -%04d -  %2.4fC" % (v, 100.0 * v / 4096.0, t1, t))
  #   sys.stdout.flush()
  #   time.sleep(.1);
