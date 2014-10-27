import networking as n
import displayplatformer
import time

# TODO: Figure out tile location based on hostname
if __name__ == '__main__':
  game = displayplatformer.ClientPlatformer([1, 0], [900, 0])
  connected = False
  while not connected:
    try:
      server = n.Server('localhost', 2001, game)
      connected = True
    except Exception:
      time.sleep(.5)
  server.open_connection()
  print(server.socket)
  while True:
    server.recev_connection()
