import json
import asyncore
import socket

class CommandHandler(asyncore.dispatcher_with_send):
  def parseCommand(self, cmd):
    """Parses the actual commands and returns a string of what the"""
    cmd = cmd.lower()
    rtn = "Unknown command '%s'.  Try 'help'" % cmd
    if cmd == "help":
      self.send("""
Available commands:
help              Show this message
count <channel>   Retrieves the raw count values of a2d <channel>
value <channel>   Retrieves the converted value of the a2d <channel>
pulsegpio         Pulse Close the socket connection
gpio <#> <high|low|?> Set GPIO pin or query it
quit|exit         Close the socket connection

Additionally, if valid JSON document is passed, with the 
key of "channels" defined to be an array of channels to 
query such as:
  
  {
    "channels": [0, 3, 4]
    <"exit">
  }

A JSON document similar to below will be returned:
  {
    "counts": [514, 1024, 152], 
    "values": [2.43, 4690, 25],
    "units": ['V', 'mV', 'C']
  }

Where the indexes of the array are mapped to channel 
#0, 3, and 4 respectively. If the key 'exit' is set,
the server will close the connection after sending the
measured value.
""")
    if cmd == "quit" or cmd == "exit":
      self.send("Closing connection\n")
      self.close() 
    if cmd.startswith("count"):
      print("counted baby!")
    if cmd.startswith("value"):
      print("value baby!")
    try:
      j = json.loads(cmd)
      print(j)
      if j.contains("channels"):
        print("JSON mode!")
    except:
      pass

  def handle_read(self):
    data = self.recv(8192)
    if data:
      commands = data.splitlines()
      for cmd in commands:
        if cmd == '':
          continue
        self.parseCommand(cmd.strip())
  
class SensorServer(asyncore.dispatcher):
  def __init__(self, host, port):
    asyncore.dispatcher.__init__(self)
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.set_reuse_addr()
    self.bind((host, port))
    self.listen(5)

  def handle_accept(self):
    pair = self.accept()
    if pair is not None:
      sock, addr = pair
      print 'Incoming connection from %s' % repr(addr)
      handler = CommandHandler(sock)

server = SensorServer('', 8080)
asyncore.loop()
