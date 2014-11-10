import networking as n
import displayplatformer
import time
import json
import socket

network_settings = json.load(open('network_settings.json'))

if network_settings['localhost'] == "True":
  HOST = 'localhost'
else:
  HOST = '10.0.0.249'

# TODO: Figure out tile location based on hostname
if __name__ == '__main__':
  myhostname = socket.gethostname()
  (_,xindx,yindx) = myhostname.split('-')
  xindx = int(xindx)
  yindx = int(yindx)
  print yindx
  print xindx
  first_hit = False
  for line in open('/etc/hosts').readlines():
    if line.find(myhostname) > -1:
      my_ip_address = line.split()[0]
      break
  if yindx == 2:
    yindx = 0
  elif yindx == 0:
    yindx = 2
  game = displayplatformer.ClientPlatformer([xindx, yindx])
  connected = False
  print my_ip_address
  while not connected:
    try:
      server = n.Server(my_ip_address, 2000, game)
      connected = True
    except Exception:
      time.sleep(.5)
  print(server.socket)
  server.open_connection()  # open and receive the first data packet
  while True:
    server.recev_connection()
