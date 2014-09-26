import pygame
import sys
# import ipdb
from pygame.locals import *
import world as wd
import engine as eng
import socket
import pickle
import os

# TODO: Maybe it's time to move away from the socket del? That will also require moving off pickling
SOCKET_DEL = '*ET*'.encode('utf-8')
loc = []
FPS = pygame.time.Clock()
TICK = 60
GRID_SPACE = [0, 0]
# DISPLAY_SIZE = [600, 600]
DISPLAY_SIZE = {"x": 600, "y": 600}
BEZZEL_SIZE = [30, 30]


# TODO: have a platformer game class that has all the similar components of the render and 
# master node, and inherit from that?
class MasterPlatformer(object):
  """Class for the platformer head node"""

  def __init__(self, localhosts=1):
    super(MasterPlatformer, self).__init__()
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)  # move window to upper left corner
    pygame.init()

    self.game_objects = {}
    self.window = pygame.display.set_mode((60, 60))
    self.engine = eng.Engine()

    # load map
    self.game_objects['terrain'] = []
    self.game_objects['players'] = []
    self.game_objects['data_object'] = []
    self.game_objects['data_device'] = []
    self.game_objects['follower'] = []

    map_json = self.engine.parse_json("map.json")

    # TODO: abstract this parsing to dynamically call the constructor based on the 
    # attribute (reuse map)
    for tile in map_json['floors']:
      self.game_objects['terrain'].append(
        wd.SimpleScenery(int(tile["x"]), int(tile["y"]),
                         int(tile["width"]), int(tile["height"]), (255, 255, 000)))
    for player in map_json['players']:
      self.game_objects['players'].append(wd.Player(int(player["x"]),
                                                    int(player["y"]), 30, 30,
                                                    sprite_sheet='Player.png'))
    for data in map_json['data_object']:
      self.game_objects['data_object'].append(wd.Data(int(data["x"]),
                                                      int(data["y"]),
                                                      int(data["width"]),
                                                      int(data["height"]),
                                                      color=(255, 255, 0)))
    for data_device in map_json['data_device']:
      self.game_objects['data_device'].append(wd.DataDevice(int(data_device["x"]),
                                                            int(data_device["y"]),
                                                            int(data_device["width"]),
                                                            int(data_device["height"]),
                                                            color=eng.Colors.AQUA))
    for follower in map_json['follower']:
      self.game_objects['follower'].append(wd.Follower(int(follower["x"]),
                                                            int(follower["y"]),
                                                            int(follower["width"]),
                                                            int(follower["height"]),
                                                            color=eng.Colors.AQUA))

    # TEST:
    self.game_objects['follower'][-1].leader = self.game_objects['players'][0]

    send_struct = {}
    # build the initial data packet
    for obj_type, obj_list in self.game_objects.items():
      send_struct[obj_type] = []
      # print(obj_list)
      for game_obj in obj_list:
        send_dict = {"rect": [game_obj.rect.x, game_obj.rect.y, game_obj.rect.width,
                              game_obj.rect.height], "id": game_obj.id, "color": game_obj.color,
                     "constructor": type(game_obj).__name__}
        send_struct[obj_type].append(send_dict)

    print(send_struct)

    data = pickle.dumps(send_struct, pickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    # TODO: Stop being lazy and read from file.
    # ip_list
    self.ip_list = []
    for x in range(0, localhosts):
      self.ip_list.append(('localhost', 2000 + x))

    self.socket_list = []
    for node in self.ip_list:
      self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
      print(node)
      self.socket_list[-1].connect(node)
      self.socket_list[-1].sendall(data)

    for node in self.socket_list:
      self.get_whole_packet(node)

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
    player1 = self.game_objects['players'][0]
    player2 = self.game_objects['players'][1]
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        sys.exit()
      if event.type == KEYDOWN:
        if event.key == K_LEFT:
          player1.move_left()
        if event.key == K_RIGHT:
          player1.move_right()
        if event.key == K_UP:
          player1.jump()
        if event.key == K_t:
          player1.throw_data()
        if event.key == K_a:
          player2.move_left()
        if event.key == K_d:
          player2.move_right()
        if event.key == K_w:
          player2.jump()
      if event.type == KEYUP:
        if event.key == K_LEFT:
          player1.stop_left()
        if event.key == K_RIGHT:
          player1.stop_right()
        if event.key == K_a:
          player2.stop_left()
        if event.key == K_d:
          player2.stop_right()

    self.engine.physics_simulation(self.game_objects['players'] + self.game_objects['data_object'],
                                   self.game_objects['terrain'] + self.game_objects['data_object'] +
                                   self.game_objects['data_device'])

    self.engine.loop_over_game_dict_att(self.game_objects, 'update')
    self.engine.loop_over_game_dict_att(self.game_objects, 'animate')

    # construct packet
    send_struct = {'state': 'play'}
    game_objects_packets = []  # accumulator for the build_packet function
    self.engine.loop_over_game_dict_att(self.game_objects, 'build_packet', game_objects_packets)
    send_struct['game_objects'] = game_objects_packets

    # serialize the data and send
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
  print(sys.argv)
  if len(sys.argv) != 2:
    game = MasterPlatformer(localhosts=1)
  else:
    game = MasterPlatformer(localhosts=int(sys.argv[1]))
  game.run()
