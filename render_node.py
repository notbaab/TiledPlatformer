import networking as n
import DisplayPlatformer

# TODO: Figure out tile location based on hostname
if __name__ == '__main__':
  game = DisplayPlatformer.ClientPlatformer([0, 0])
  server = n.Server('localhost', 2000, game)
  print(server.socket)
  server.open_connection()
  while True:
    server.recev_connection()
