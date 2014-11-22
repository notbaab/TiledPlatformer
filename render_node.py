import networking as n
import displayplatformer
import time
import json
import socket
import sys

json_file = open('network_settings.json', "r")
network_settings = json.load(json_file)
my_ip_address = ''

if network_settings['localhost'] == "True":
  if len(sys.argv) != 3:
    print("Network_settings curretly set to localhost, need an x and a y argument. Run `python render_node.py x y")
    sys.exit()
  json_file.close()  # we want to overwrite the tile with the values passed in
  json_file = open('network_settings.json', "r+")
  xindx = int(sys.argv[1])
  yindx = int(sys.argv[2])
  json_file.seek(0)  # lazy pass to game.py
  data = {"localhost": "True", "x": str(xindx), "y": str(yindx)}
  json.dump(data, json_file)
  my_ip_address = 'localhost'

else:
  myhostname = socket.gethostname()
  (_, xindx, yindx) = myhostname.split('-')
  xindx = int(xindx)
  yindx = int(yindx)
  print(yindx)
  print(xindx)
  first_hit = False
  for line in open('/etc/hosts').readlines():
    if line.find(myhostname) > -1:
      my_ip_address = line.split()[0]
      break
  if yindx == 2:
    yindx = 0
  elif yindx == 0:
    yindx = 2

json_file.close()

game = displayplatformer.ClientPlatformer([xindx, yindx])
connected = False
print(my_ip_address)
while not connected:
  try:
    server = n.Client(my_ip_address, 2000, game)
    connected = True
  except Exception:
    time.sleep(.5)
print(server.socket)
server.open_connection()  # open and receive the first data packet
while True:
  server.recev_connection()
