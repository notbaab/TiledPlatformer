from networking import Server
from game import MasterPlatformer
import json


if __name__ == '__main__':
  json_file = open('network_settings.json', "r")
  network_settings = json.load(json_file)
  vidja_game = MasterPlatformer()
  if network_settings['localhost'] == "True":
    server = Server(vidja_game)
  else:
    server = Server(vidja_game, network_settings['ip_file'], network_settings['port'])
  server.start_game()
  server.run()


