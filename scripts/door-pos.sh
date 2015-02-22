#!/bin/bash
HOST=garage
curl --data "pos=1" -s http://$HOST/generator |\
  jq '"The garage door is \(.spos) [aka \(.pos)% open] "' -e -c | \
  sed s/\"//g 
