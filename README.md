# garage-rpy
A Garage Door Home Automation Controller using a Rasberry Pi with functionality exposed via a webpage or a raw socket. Put your garage door online! 

#Huh?  What?  How?  Why? 
Why not??!!!??!   I dont want to spend $400 on some mostly pathetic garage door opener when what I really need is a 
whole new door besides the fact the new openers come with all sorts of vendor lock in (and shoveling your data online).
I also just wanted to be able to open the garage on my way in from commuting home. It may seem quite ugly and simple,
but more KISS would make the world a bit easier to navigate.

#Schematic
This is essentially just a solid state relay connected in parallel with the standard open/close buttons and a 10-turn pot
to detects where the door is physically located.  I used a zero-crossing 2-amp (WAY overkill) solid state relay and some
unknown 10-turn pot I found on amazon.  Sorry for the utter lack of theory - feel free to contact me if you want some more info.

![General Schematic](schematic/garage-pi.png)

Schematic is saved in a format QElectroTech can open.

#Installation

I have a few tools and tend to overbuild thing, but I am sure there are easier ways to attach this.  Just be sure you install the
pot/potentiometer in such a way that it can freely move across the entire cycle of the door opening and closing and do not create 
mechanical strains tha will eventually destroy stuff.  I counted that my tensioner rod only rotated ~6 times, so I bought a 10-turn
pot and slapped it in.  Your milage may vary.  The A2D frontend is generic enough that if you do something else it wont matter if
you can provide a decent enough tranfer function in your ini file.

My hacked install of the pot into a 1980s era garage door tensioner rod.

[Installed](README.d/pot.png)


#Configuration File Definitions
If you want a full example, you should probably look at sample_config.ini for a more detailed.
This is the config I have been using

```ini

	[general]
	tcp_port=5000
	loglevel=0
	adc_spi = mcp3008_adc
	open_close_switch = gpio_relay

	[mcp3008_adc]
	spidev_port=0
	spidev_ce=0
	sensors=door,temperature


	[door]
	a2d_port = 0
	# A R Divider where R1 attaches to Vcc and R2 connects to Gnd: the value of R2 is 
	# defined by cnt / bits * (R1+R2) where bits is the ADC resolution (1024 for MCP3008)
	# and R1+R2 is total value of the pot (5K, 10K, etc)
	#count_to_value = cnt / 1024 * ( 5000 )
	count_to_value = 100.0 * cnt / 4096
	name=Door Position
	description=Position of the Garage Door
	max=4096
	min=0
	units=%%

	[temperature]
	a2d_port = 1
	# A temperature couple connected in a R Divider where R1 attaches to Vcc
	# and R2=temp probe connects to Gnd. R2 is optimally 10k at room temp.
	# R2 is defined as R1 * (#bits/ (#bits - cnt))
	# Temp is given as 251.11-25.45*log(R2)
	# Putting them together gives 
	count_to_value = 251.11-25.45*math.log(4988*4096/(4096-cnt))
	name=Air Temperature
	description=Airtemp in the garage attic
	max=1024
	min=0
	units=C

	[gpio_relay]
	# Which GPIO pin are we using to control the relay
	pin = 19

	# What should the idle state of the pin be.  Normally
	# this should just remain to be low, but if you have
	# a active low relay, you should set this to 1.
	idle_state = 0

	#How long to pulse the pin high/low (in seconds)
	pulse= 0.500


```
# CherryPy Interface
There is a AJAX enabled web interface that is bundled to make it easier to deploy.  This can be started by running 

```sh 
	sudo python cherrypy-garagepy.py
```

Some screenshots

[Door Closed](README.d/web_ui.png)

[Door Partially Open](README.d/web_ui_open.png)

[On my Phone](README.d/web-phone.png)



# Socket Server Interface (needs some work)

Start the server with a valid configuration file as described above

```sh

	python socket-garagepy.py  ../scripts/config.ini

```

In this example, ``` tcp_port = 5000 ```.  You can use *netcat* / *nc* / *ncat* to interact with it such as below:


```sh

	nickp@lappy /home/nickp % ncat raspi 5000

	help

	Available commands:
	help              Show this message
	config            dump the ini configuration 
	count <channel>   Retrieves the raw count values of a2d <channel>
	value <channel>   Retrieves the converted value of the a2d <channel>
	v     <channel>   Retrieves the converted value of the a2d <channel> with units
	pulsegpio         Pulse gpio pin as set in the configuration
	quit|exit         Close the socket connection

	Additionally, if valid JSON document is passed, with the 
	key of "channels" defined to be an array of channels to 
	query such as:
	  
	  {
	    "channels": [0, 3, 4]
	  }

	A JSON document similar to below will be returned:
	  {
	    "counts": [514, 1024, 152], 
	    "values": [2.43, 4690, 25],
	    "units": ['V', 'mV', 'C']
	  }

	Where the indexes of the array are mapped to channel 
	#0, 3, and 4 respectively. It is also possible to set
	the "pulsegpio" via a "pulsegpio": 1 directive, or
	you can sever the socket connection after via setting a 
	"quit" or "exit" section.  Their values are ignored.

	EG:

	{"channels": [0], "pulsegpio": 1, "exit": 0} 

	would:

	- Return something like: {"counts": [514], "values": [2.5], "units": ['V'], "pulsed": 1}
	- Pulse the GPIO as per the config, and
	- Close the socket.

	count 0
	2110
	>v 0
	51.54 % 
	>value 0
	51.5869140625
	>{"channels": [0, 1], "quit": 1}
	{"units": ["%", "C"], "counts": [2111, 41], "values": [51.5380859375, 34.15474457157549]}


	Ncat: Broken pipe.

```

You can also do one-liners like this to feed directly to ncat to get values, just make sure you escape the shell items properly with *echo*.

```sh

	nickp@lappy /home/nickp %  echo {\"channels\": \[0\], \"quit\": 1 \} | ncat raspi 5000
	{"units": ["%"], "counts": [2111], "values": [51.5380859375]}
	nickp@lappy /home/nickp %

```



