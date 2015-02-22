#!/bin/bash


HOST=garage

#smash the open door button
curl --data "pos=1" http://$HOST/generator
