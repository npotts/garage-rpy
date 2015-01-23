# garage-rpy
A Garage Door Home Automation Controller using a Rasberry Pi. Put your garage door online! 


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
	pin = 15

	# What should the idle state of the pin be.  Normally
	# this should just remain to be low, but if you have
	# a active low relay, you should set this to 1.
	idle_state = 0

	#How long to pulse the pin high/low (in seconds)
	pulse= 0.500


```

# Testing with 

Start the server with a valid configuration file as described above

```sh

	python sensor-server.py  ../scripts/config.ini

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
	pulsegpio <#>     Pulse gpio pin # as set in the configuration
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

	- Return something like: {"counts": [514], "values": [2.5], "units": ['V']}
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



