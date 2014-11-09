import networking as n
import displayplatformer
import time
import json


network_settings = json.load(open('network_settings.json'))

if network_settings['localhost'] == "True":
  HOST = 'localhost'
else:
  HOST = '10.0.0.249'

# TODO: Figure out tile location based on hostname
if __name__ == '__main__':
  game = displayplatformer.ClientPlatformer([0, 0], [200, 0])
  connected = False
  while not connected:
    try:
      server = n.Server('', 2000, game)
      connected = True
    except Exception:
      time.sleep(.5)
  print(server.socket)
  server.open_connection()  # open and receive the first data packet
  while True:
    server.recev_connection()
