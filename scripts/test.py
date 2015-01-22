#!/usr/bin/env python

import sys
import time
from sensors import grpycfg, gsensors


if __name__ == "__main__":
  cfg = grpycfg(sys.argv[1])
  g = gsensors(cfg)
  while(True):
    v = g.readValue(0);
    sys.stdout.write("\r%04d (%%%3.2f)" % (v, 100.0 * v / 4096.0))
    sys.stdout.flush()
    time.sleep(.1);
