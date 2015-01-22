#!/bin/bash

#Nuke all non-checked in code sources
git clean -df
git pull
git checkout -- . -f
