import pygame
import sys
import ipdb
from pygame.locals import *
import world as wd
import engine as eng
import socket
import pickle

# TODO: Maybe it's time to move away from the socket del? That will also require moving off pickling
SOCKET_DEL = '*ET*'.encode('utf-8')
loc = []
FPS = pygame.time.Clock()
TICK = 60


# TODO: have a platformer game class that has all the similar components of the render and 
# master node, and inherit from that?
class MasterPlatformer(object):
  """Class for the platformer head node"""

  def __init__(self):
    super(MasterPlatformer, self).__init__()
    pygame.init()

    self.game_objects = {}
    self.window = pygame.display.set_mode((60, 60))
    self.engine = eng.Engine()

    # TODO: Somehow figure out how to read all the map files that each node will have and build a map
    # off of those
    # load map
    self.floors = self.engine.parse_json("map.json")
    self.game_objects['terrain'] = []

    # TODO: make a unique map to each node
    for floor in self.floors:
      # TODO: MAP!!!!! Chanel the inner soring lerner and apply that functional programing 
      self.game_objects['terrain'].append(wd.SimpleScenery(int(floor["x"]), int(floor["y"]),
                                                           int(floor["width"]), int(floor["height"]), (255, 255, 000)))
      self.game_objects['terrain'].append(wd.SimpleScenery(int(floor["x"]) + 600, int(floor["y"]),
                                                           int(floor["width"]) + 600, int(floor["height"]), (255, 255, 000)))

    # TODO: Stop being lazy and read from file. 
    # ip_list
    self.ip_list = [('localhost', 2000), ('localhost', 2001)]
    self.socket_list = []
    for node in self.ip_list:
      self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
      print(node)
      self.socket_list[-1].connect(node)

    # TODO: add more players
    # players
    self.game_objects['players'] = []
    self.game_objects['players'].append(wd.Player(70, 500, (255, 0, 0)))

    # TODO: Send initial player objects to the nodes. That will require a kind 
    # Setup state to be added. 
    self.state = 'play'
    print(self.game_objects)

  def run(self):
    while True:
      if self.state == 'play':
        data, self.state = self.play_frame()
      else:
        ipdb.set_trace()

      FPS.tick(TICK)

  def play_frame(self):
    # TODO: Add ability to change controls
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        sys.exit()
      if event.type == KEYDOWN:
        for player in self.game_objects['players']:
          if event.key == K_LEFT:
            player.move_left()
          if event.key == K_RIGHT:
            player.move_right()
          if event.key == K_SPACE:
            player.jump()
      if event.type == KEYUP:
        for player in self.game_objects['players']:
          if event.key == K_LEFT:
            player.stop_left()
          if event.key == K_RIGHT:
            player.stop_right()

    self.engine.physics_simulation(self.game_objects['players'], self.game_objects['terrain'])

    # TODO: Build network packet in a little better
    # build network packet
    send_struct = {'state': 'play',
                   'player_loc': [self.game_objects['players'][0].rect.x, self.game_objects['players'][0].rect.y]}

    data = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    for node in self.socket_list:
      node.sendall(data)

    return_list = []
    for node in self.socket_list:
      return_list.append(self.get_whole_packet(node))
    # TODO: return real data
    return '', 'play'

  def get_whole_packet(self, sock):
    """ensures that we receive the whole stream of data"""
    data = ''.encode('utf-8')
    while True:
      data += sock.recv(4024)
      split = data.split(SOCKET_DEL)  # split at newline, as per our custom protocol
      if len(split) != 2:  # it should be 2 elements big if it got the whole message
        pass
      else:
        x = pickle.loads(split[0])
        return x


if __name__ == '__main__':
  game = MasterPlatformer()
  game.run()
