#!/bin/bash

#Where to fetch and store needed source code to
CODE=~/code

#sudo apt-get install -y build-essential RPi.GPIO python-cherrypy3 python-pip python-dev

mkdir -p $CODE
python -c "import spidev" &>/dev/null || ( echo "Installing needed python 'spidev' module"; cd $CODE && git clone  --recursive https://github.com/doceme/py-spidev && cd $CODE/py-spidev && sudo python setup.py install )


ls $CODE/garage-rpy &> /dev/null || (echo Fetching Garage-rpy sources; git clone --recursive https://github.com/npotts/garage-rpy $CODE/garage-rpy )
ls /usr/bin/cherrypy-garagepy.py &> /dev/null || ( echo Creating symlink to cherrypy-garagepy.py; sudo ln -sf $CODE/garage-rpy/cherrypy-garagepy.py /usr/bin/cherrypy-garagepy.py )
ls /etc/init.d/garage-rpy &> /dev/null || ( echo Copying init configuration to /etc/init.d/garage-rpy; sudo cp $CODE/garage-rpy/init/garage-rpy /etc/init.d/ && sudo sed -i s:PATH_TO_GRPY_SOURCE:${CODE}/garage-rpy:g /etc/init.d/garage-rpy && sudo nano /etc/init.d/garage-rpy && sudo update-rc.d garage-rpy defaults )