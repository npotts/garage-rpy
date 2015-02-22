#!/bin/bash


HOST=garage

#smash the open door button
curl --data "smashit=1" http://$HOST/generator
