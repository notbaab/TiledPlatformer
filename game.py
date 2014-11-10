import pygame
import sys
# import ipdb
from pygame.locals import *
import world as wd
import engine as eng
import socket
import cPickle
import os
import json

network_settings = json.load(open('network_settings.json'))

if network_settings['localhost'] == "True":
  json_data = open('master_settings_mac_local.json')
else:
  json_data = open('master_settings.json')

config = json.load(json_data)
# TODO: Maybe it's time to move away from the socket del? That will also require moving off pickling
SOCKET_DEL = config['package_delimeter'].encode('utf-8')
loc = []
FPS = pygame.time.Clock()
TICK = int(config['FPS_TICK'])
GRID_SPACE = [int(config['grid_space'][0]), int(config['grid_space'][1])]
# DISPLAY_SIZE = [600, 600]
DISPLAY_SIZE = {"x": int(config['display_size'][0]), "y": int(config['display_size'][1])}
BEZZEL_SIZE = [30, 30]
PLAYER_RECT = PLAYER_WIDTH, PLAYER_HEIGHT = 25, 40
DEBUG_CLASSES = []
# DEBUG_CLASSES = [wd.SimpleScenery, wd.Player]


# TODO: have a platformer game class that has all the similar components of the render and 
# master node, and inherit from that?
class MasterPlatformer(object):
  """Class for the platformer head node"""

  def __init__(self, localhosts=1, ip_file=None):
    global config
    super(MasterPlatformer, self).__init__()
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)  # move window to upper left corner
    pygame.init()
    self.game_objects = {}
    self.window = pygame.display.set_mode((60, 60))
    self.engine = eng.Engine()
    self.added = []  # list keeping track of which objects are added
    self.deleted = []  # list keeping track of the ids of objects that are deleted

    # load map
    self.game_objects = {}

    map_json = self.engine.parse_json(config['global_map_file'])
    asset_json = self.engine.parse_json(config['asset_file'])

    # TODO: abstract this parsing to dynamically call the constructor based on the 
    # attribute (reuse map)
    for tile in map_json['floors']:
      tmp = wd.SimpleScenery(int(tile["x"]), int(tile["y"]),
                             int(tile["width"]), int(tile["height"]), sprite_sheet=asset_json["SimpleScenery"])
      self.game_objects[tmp.id] = tmp

    for player in map_json['players']:
      tmp = wd.Player(int(player["x"]), int(player["y"]), PLAYER_WIDTH, PLAYER_HEIGHT,
                      sprite_sheet=asset_json["Player"])
      self.game_objects[tmp.id] = tmp

    for data in map_json['data_object']:
      tmp = wd.Data(int(data["x"]), int(data["y"]), int(data["width"]), int(data["height"]),
                    sprite_sheet=asset_json["Data"])
      self.game_objects[tmp.id] = tmp

    for data_device in map_json['data_device']:
      tmp = wd.DataDevice(int(data_device["x"]), int(data_device["y"]), int(data_device["width"]),
                          int(data_device["height"]), sprite_sheet=asset_json["DataDevice"], game=self)
      self.game_objects[tmp.id] = tmp

    for follower in map_json['followers']:
      tmp = wd.Follower(int(follower["x"]), int(follower["y"]), int(follower["width"]),
                        int(follower["height"]), sprite_sheet=asset_json["Follower"])
      self.game_objects[tmp.id] = tmp

    for patroler in map_json['patrollers']:
      tmp = wd.Patroller(int(patroler["x"]), int(patroler["y"]), int(patroler["width"]),
                         int(patroler["height"]), sprite_sheet=asset_json["Patroller"])
      self.game_objects[tmp.id] = tmp

    for comet in map_json['comet']:
      tmp = wd.DataCruncher(int(comet["x"]), int(comet["y"]), int(comet["width"]),
                            int(comet["height"]), sprite_sheet=asset_json["DataCruncher"])
      self.game_objects[tmp.id] = tmp

    for desk in map_json['Desk']:
      tmp = wd.Desk(int(desk["x"]), int(desk["y"]), int(desk["width"]),
                    int(desk["height"]), sprite_sheet=asset_json["DataCruncher"])
      self.game_objects[tmp.id] = tmp

    for publish_house in map_json['PublishingHouse']:
      tmp = wd.PublishingHouse(int(publish_house["x"]), int(publish_house["y"]), int(publish_house["width"]),
                               int(publish_house["height"]), sprite_sheet=asset_json["PublishingHouse"],
                               accept_stage=wd.DATA_STAGES["paper"])

      self.game_objects[tmp.id] = tmp

    for config in map_json['Meeting']:
      tmp = wd.Meeting(int(config["x"]), int(config["y"]), int(config["width"]),
                       int(config["height"]), sprite_sheet=asset_json["Meeting"])

      self.game_objects[tmp.id] = tmp

    print(self.game_objects)

    if DEBUG_CLASSES:
      new_game_obj = self.game_objects.copy()
      for obj in self.game_objects.values():
        if type(obj) not in DEBUG_CLASSES:
          print(str(type(obj)))
          del new_game_obj[obj.id]
      self.game_objects = new_game_obj.copy()
    send_struct = {'game_obj': []}
    # build the initial data packet
    for game_obj in self.game_objects.values():
      send_dict = {"rect": [game_obj.rect.x, game_obj.rect.y, game_obj.rect.width,
                            game_obj.rect.height], "id": game_obj.id, "sprite_sheet": game_obj.sprite_sheet,
                   "constructor": type(game_obj).__name__}
      send_struct['game_obj'].append(send_dict)

    data = cPickle.dumps(send_struct, cPickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    # TODO: Stop being lazy and read from file.
    # ip_list
    self.ip_list = []
    ips = open('tile-hosts.txt', 'r')
    address = ips.readline().strip()
    ip_list = []
    while address:
        ip_list.append(address)
        address = ips.readline().strip()
    idx = 0
    self.socket_list = []
    for ip in ip_list:
      self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
      self.socket_list[-1].connect((ip, 2000))
      self.socket_list[-1].sendall(data)
    # for x in range(0, DISPLAY_SIZE['x']):
    #   for y in range(0, DISPLAY_SIZE['y']):
    #     self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    #     self.socket_list[-1].connect((ip_list[idx], 20000))
    #     self.socket_list[-1].sendall(data)
    #     idx += 1
    # if ip_file:
    #   # self.ip_list.append(('tile-1-1', 2000))
    # else:
    #   for x in range(0, localhosts):
    #     self.ip_list.append(('localhost', 2000 + x))

    # self.socket_list = []
    # for node in self.ip_list:
    #   self.socket_list.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    #   print(node)
    #   self.socket_list[-1].connect(node)
    #   self.socket_list[-1].sendall(data)

    for node in self.socket_list:
      self.get_whole_packet(node)

    self.state = 'load'

  def run(self):
    while True:
      if self.state == 'play':
        data, self.state = self.play_frame()
      elif self.state == 'load':
        data, self.state = self.load()
      else:
        ipdb.set_trace()
      FPS.tick(TICK)
      # print(FPS.get_fps())

  def load(self):
    send_struct = {'state': 'load'}
    # clients handle the load state so wait for their response and play the game
    return self.serialize_and_sync(send_struct)

  def play_frame(self):
    game_dict = self.structured_list()  # Structure the game object list to manage easier. n time should be fast
    player1 = game_dict['Player'][0]
    player2 = game_dict['Player'][1]
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        self.quit()
        sys.exit()
      elif event.type == KEYDOWN:
        if event.key == K_ESCAPE:
          self.quit()
          sys.exit()          
        if event.key == K_LEFT:
          player1.move_left()
          player1.escape(1)
        elif event.key == K_RIGHT:
          player1.move_right()
          player1.escape(2)
        elif event.key == K_UP:
          player1.jump()
        elif event.key == K_t:
          player1.throw_data()
        elif event.key == K_a:
          player2.move_left()
          player2.escape(1)
        elif event.key == K_d:
          player2.move_right()
          player2.escape(2)
        elif event.key == K_w:
          player2.jump()
        elif event.key == K_SPACE:
          player1.interact(self.game_objects.values())  # TODO: We are passing in way to much data here, fix it.
      elif event.type == KEYUP:
        if event.key == K_LEFT:
          player1.stop_left()
        elif event.key == K_RIGHT:
          player1.stop_right()
        elif event.key == K_a:
          player2.stop_left()
        elif event.key == K_d:
          player2.stop_right()

    self.engine.physics_simulation(self.game_objects.values(), [wd.SimpleScenery])

    self.engine.map_attribute_flat(self.game_objects.values(), 'update')
    self.engine.map_attribute_flat(self.game_objects.values(), 'animate')

    # update the AI after the players have been updated
    self.engine.map_attribute_flat(game_dict['AI'], 'check_for_leader', game_dict['Player'])

    # update meetings/traps
    self.engine.map_attribute_flat(game_dict['Meeting'], 'check_player', game_dict['Player'])

    # construct packet
    send_struct = {'state': 'play', 'deleted_objs': [], 'added_objs': []}

    # check for objects that have been created and add them to the dict
    for game_obj in self.added:
      self.game_objects[game_obj.id] = game_obj
      send_struct['added_objs'].append({"rect": [game_obj.rect.x, game_obj.rect.y, game_obj.rect.width,
                                                 game_obj.rect.height], "id": game_obj.id,
                                        "sprite_sheet": game_obj.sprite_sheet,
                                        "constructor": type(game_obj).__name__})

    for game_obj_id in self.deleted:
      send_struct['deleted_objs'].append(game_obj_id)
      del self.game_objects[game_obj_id]

    # clear lists
    self.added = []
    self.deleted = []

    game_objects_packets = []  # accumulator for the build_packet function
    self.engine.map_attribute_flat(game_dict['NetworkedObject'], 'build_packet', game_objects_packets)
    send_struct['game_objects'] = game_objects_packets

    return self.serialize_and_sync(send_struct)

  def structured_list(self):
    """take the game object list and return a dict with the keys for static, AI, and player
    objects. An object can be added to multiple lists if it is multiple things i.e.
    a player is a movable game object"""
    ret_dict = {'AI': [], 'StaticObject': [], 'Player': [], 'MovableGameObject': [],
                'NetworkedObject': [], 'Meeting': []}
    for game_obj in self.game_objects.values():
      if isinstance(game_obj, wd.Player):
        ret_dict['Player'].append(game_obj)
      elif isinstance(game_obj, wd.SimpleScenery):
        ret_dict['StaticObject'].append(game_obj)
      elif isinstance(game_obj, wd.Follower):
        ret_dict['AI'].append(game_obj)
      if isinstance(game_obj, wd.MovableGameObject):
        ret_dict['MovableGameObject'].append(game_obj)
      if isinstance(game_obj, wd.NetworkedObject):
        ret_dict['NetworkedObject'].append(game_obj)
      if isinstance(game_obj, wd.Meeting):
        ret_dict['Meeting'].append(game_obj)
    return ret_dict

  def add_to_world(self, game_obj):
    self.game_objects[game_obj.id] = game_obj

  def get_whole_packet(self, sock):
    """ensures that we receive the whole stream of data"""
    data = ''.encode('utf-8')
    while True:
      data += sock.recv(4024)
      split = data.split(SOCKET_DEL)  # split at newline, as per our custom protocol
      if len(split) != 2:  # it should be 2 elements big if it got the whole message
        pass
      else:
        x = cPickle.loads(split[0])
        return x

  def serialize_and_sync(self, send_struct):
    """serialize data and send it to the nodes."""
    # serialize the data and send
    data = cPickle.dumps(send_struct, cPickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    for node in self.socket_list:
      node.sendall(data)

    return_list = []
    for node in self.socket_list:
      return_list.append(self.get_whole_packet(node))
    # TODO: return real data
    return '', 'play'

  def quit(self):
    data = cPickle.dumps({'state': 'kill'}, cPickle.HIGHEST_PROTOCOL) + '*ET*'.encode('utf-8')
    for node in self.socket_list:
      node.sendall(data)
    time.sleep(2)


if __name__ == '__main__':
  print(sys.argv)
  if len(sys.argv) != 2:
    game = MasterPlatformer(localhosts=1, ip_file=True)
  else:
    game = MasterPlatformer(localhosts=int(sys.argv[1]))
  game.run()
