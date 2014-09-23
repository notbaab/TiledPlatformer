import networking as n
import displayplatformer

# TODO: Figure out tile location based on hostname
if __name__ == '__main__':
  game = displayplatformer.ClientPlatformer([0, 0])
  server = n.Server('localhost', 2000, game)
  print(server.socket)
  server.open_connection()  # open and receive the first data packet
  while True:
    server.recev_connection()
