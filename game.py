import pygame
import sys
import ipdb
from pygame.locals import *
import world as wd
import engine as eng
from networking import NetworkedMasterGame

if sys.version_info > (3, 0):
  import pickle as pickle
else:
  import cPickle as pickle
import os
import json

network_settings = json.load(open('network_settings.json'))

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
BEZZEL_SIZE = 120
DISPLAY_SIZE['x'] += BEZZEL_SIZE
DISPLAY_SIZE['y'] += BEZZEL_SIZE
print(DISPLAY_SIZE)
DEBUG_CLASSES = []
# DEBUG_CLASSES = [wd.SimpleScenery, wd.Player]
GAME_LENGTH = 3  # in minutes


# TODO: have a platformer game class that has all the similar components of the render and 
# master node, and inherit from that?
class MasterPlatformer(NetworkedMasterGame):
  """Class for the platformer head node"""

  def __init__(self):
    """initialize the game and all the game objects.
    """
    global config, network_settings
    super(MasterPlatformer, self).__init__()
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)  # move window to upper left corner
    pygame.init()
    self.game_objects = {}
    self.window = pygame.display.set_mode((60, 60))
    self.engine = eng.Engine()
    self.added = []  # list keeping track of which objects are added
    self.deleted = []  # list keeping track of the ids of objects that are deleted
    self.blue_score = 0
    self.red_score = 0
    self.game_length = GAME_LENGTH * 60 * 1000

    self.game_objects = self.load_map()

    # remove none debugin classes if we want to test a specific class
    if DEBUG_CLASSES:
      new_game_obj = self.game_objects.copy()
      for obj in self.game_objects.values():
        if type(obj) not in DEBUG_CLASSES:
          print(str(type(obj)))
          del new_game_obj[obj.id]
      self.game_objects = new_game_obj.copy()

    self.make_structured_dict()  # structure the game objects into a structured dictionary
    self.el_time = 0
    self.localhost = False

  def init_game(self):
    """ 
    build the initial data packet and return the dictionary that will be
        sent to the display nodes
    """
    send_struct = {'game_obj': []}
    for game_obj in self.game_objects.values():
      if isinstance(game_obj, wd.NetworkedObject):
        send_dict = {"x": game_obj.rect.x, "y":game_obj.rect.y, "width": game_obj.rect.width,
                      "height":game_obj.rect.height, "id": game_obj.id,
                     "constructor": type(game_obj).__name__}
        if hasattr(game_obj, "sprite_sheet"):
          send_dict["sprite_sheet"] = game_obj.sprite_sheet
        send_struct['game_obj'].append(send_dict)
    self.state = 'load'
    return send_struct

  def setup_local_host(self):
    """
    Testing one local node, read from the setting to find out which tile we are testing and read
        move the player to the correct place
        spawn each player in the corner of the screen
    """
    self.localhost = True
    left_side = DISPLAY_SIZE["x"] * 0
    top_side = DISPLAY_SIZE["y"] * 0
    player1 = self.struct_game_dict['Player'][0]
    player1.rect.x = left_side + 1000
    player1.rect.y = top_side + 200

  def win_state(self):
    """
    The win state stays in a frozen state until the explicit kill event is triggered
    """
    while True:  # wait until explicit shutdown
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.quit()
          sys.exit()
        elif event.type == KEYDOWN:
          if event.key == K_ESCAPE:
            self.quit()
            sys.exit()

  def load(self):
    """
    The load state of the game is sent to the display nodes. On the master it's
        simply sending the state load
    """
    send_struct = {'state': 'load'}  # Clients do most of the load state 
    return 'play', send_struct

  def get_time(self):
    """Returns the real time string of the elapsed time"""
    minutes, milliseconds = divmod(self.el_time, 60000)
    seconds = float(milliseconds) / 1000
    real_minutes = GAME_LENGTH - minutes - 1
    real_seconds = 60 - seconds
    real_time = "%02i:%02.0f" % (real_minutes, real_seconds)
    return real_time

  def update(self, recieved_packet):
    """
    Update the game and return the next packet to be sent to the clients

    :param recieved_packet: the packets received from the display nodes.
    :type recieved_packet: list[dict]
    :returns: Data to be sent to the display nodes
    :rtype: dict
    """
    if self.state == 'play':
      self.state, send_struct = self.play_frame(recieved_packet)
    elif self.state == 'load':
      self.state, send_struct = self.load()
    elif self.state == 'kill':
      return
    return send_struct

  def play_frame(self, recieved_packets):
    """
    Play one frame of game play. Main game 'loop'

    :param recieved_packets: packets that are sent from the display nodes (not used for anything but could be)
    :type recieved_packets: list[dict]
    :returns: Updated game objects 
    :rtype: list[dict]
    """
    if self.localhost:
      quit_game = self.handle_keypress_local(self.struct_game_dict)
    else:
      quit_game = self.handle_keypress(self.struct_game_dict)
    if quit_game:
      return 'kill', ''

    self.engine.physics_simulation(self.game_objects.values(), [wd.SimpleScenery])
    self.engine.map_attribute_flat(self.game_objects.values(), 'update')

    self.engine.map_attribute_flat(self.struct_game_dict['AnimateSpriteObject'], 'animate')

    # update the AI after the players have been updated
    self.engine.map_attribute_flat(self.struct_game_dict['AI'], 'check_for_leader', self.struct_game_dict['Player'])

    # update meetings/traps
    self.engine.map_attribute_flat(self.struct_game_dict['Meeting'], 'check_player', self.struct_game_dict['Player'])

    # construct packet
    send_struct = {'state': 'play', 'deleted_objs': [], 'added_objs': []}
    if network_settings['localhost']:
      send_struct['localhost'] = self.handle_localhost(self.struct_game_dict['Player'][0])

    # check for objects that have been created and add them to the dict
    for game_obj in self.added:
      self.game_objects[game_obj.id] = game_obj
      self.add_to_structured_list(game_obj)
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
    self.engine.map_attribute_flat(self.struct_game_dict['NetworkedObject'], 'build_packet', game_objects_packets)
    send_struct['game_objects'] = game_objects_packets
    send_struct['score'] = [self.blue_score, self.red_score]
    send_struct['time'] = self.get_time()

    return 'play', send_struct

  def add_to_structured_list(self, game_obj):
    """
    Add to the maintained structured GameObject dictionary

    :param game_obj: the GameObject to be added
    :type game_dict: GameObject
    """
    if isinstance(game_obj, wd.Player):
      self.struct_game_dict['Player'].append(game_obj)
    elif isinstance(game_obj, wd.SimpleScenery):
      self.struct_game_dict['StaticObject'].append(game_obj)
    elif isinstance(game_obj, wd.Follower):
      self.struct_game_dict['AI'].append(game_obj)
    elif isinstance(game_obj, wd.Effect):
      self.struct_game_dict['Effect'].append(game_obj)

    if isinstance(game_obj, wd.MovableGameObject):
      self.struct_game_dict['MovableGameObject'].append(game_obj)
    if isinstance(game_obj, wd.NetworkedObject):
      self.struct_game_dict['NetworkedObject'].append(game_obj)
    if isinstance(game_obj, wd.ClimableObject):
      self.struct_game_dict['ClimableObject'].append(game_obj)
    if isinstance(game_obj, wd.Meeting):
      self.struct_game_dict['Meeting'].append(game_obj)
    if isinstance(game_obj, wd.AnimateSpriteObject):
      self.struct_game_dict['AnimateSpriteObject'].append(game_obj)

  def make_structured_dict(self):
    """
    take the game object list and return a dict with the keys for static, AI, and player
        objects. An object can be added to multiple lists if it is multiple things i.e.
        a player is a movable game object
    """
    self.struct_game_dict = {'AI': [], 'StaticObject': [], 'Player': [],
                             'MovableGameObject': [], 'NetworkedObject': [],
                             'Meeting': [], 'ClimableObject': [], 'Effect': [],
                             'AnimateSpriteObject':[]}

    for game_obj in self.game_objects.values():
      self.add_to_structured_list(game_obj)

  def handle_localhost(self, follow_player):
    """
    special function used to handle things like switching the screens when playing on one local host

    :param follow_player: The player that the screens should be following
    :type follow_player: Player
    """
    # first, find out which tile player one is in. 
    tile_x = follow_player.rect.centerx / (DISPLAY_SIZE['x'] + BEZZEL_SIZE)
    tile_y = follow_player.rect.bottom / (DISPLAY_SIZE['y'])
    if tile_x == -1:
      tile_x = 0
    if tile_x > 4:
      tile_x = 4

    return {'x': tile_x, 'y': tile_y}

  def add_to_world(self, game_obj):
    """
    Adds a game object to game_object dictionary

    :param game_obj: The game object to be added to the world
    :type game_obj: GameObject

    """
    self.game_objects[game_obj.id] = game_obj

  def load_map(self):
    """
    this function is stupid as shit. I hope you look back at this and feel 
        bad about how awful you approached this. You deserve to feel bad for writing it 
        like this.
        I did look back at it past me and I made it worse so fuck you past me and 
        fuck you future me. Fuck present me for having to deal with this. I am probably
        never going to be hired if anyone ever looks at this code as an example of my 
        ability. 
    """
    global config
    # load map
    game_objects = {}

    map_json = self.engine.parse_json(config['global_map_file'])
    asset_json = self.engine.parse_json(config['asset_file'])
    effect_json = self.engine.parse_json(config['effect_file'])

    for key in map_json:
      constructor = getattr(wd, key)
      for obj_dict in map_json[key]:
        if "tile" in obj_dict:
          # translate the x and y coordinates
          obj_dict['x'], obj_dict['y'] = self.translate_to_tile(obj_dict['tile'][0], int(obj_dict['x']),
                                        obj_dict['tile'][1], int(obj_dict['y']))
        else:
          obj_dict['x'], obj_dict['y'] = int(obj_dict['x']), int(obj_dict['y'])
        obj_dict['sprite_sheet'] = asset_json.get(key +  "-" + obj_dict.get('team', ''))
        obj_dict['effect_json'] = effect_json
        obj_dict['game'] = self

        tmp = constructor.create_from_dict(obj_dict)
        if isinstance(tmp, list):
          for obj in tmp:
            game_objects[obj.id] = obj
        else:
          game_objects[tmp.id] = tmp

    return game_objects

  def _handle_effect(self, obj_dict, x, y, effect_json):
    """
    handle loading the effect objects. Effects can be things from timers to electricity dancing.

    :param obj_dict: The json dictionary read from map.json containing the attributes of the door object
    :type obj_dict: dict[str]
    :param x: x location of the effect
    :type x: int
    :param y: y location of the effect
    :type y: int
    :param effect_json: json dictionary containing the animation frame information for every effect
    :type effect_json: dict[str]
    """
    print(effect_json)
    animation_dict = effect_json[obj_dict['effect_name']]
    tmp = wd.Effect(x, y, int(obj_dict['width']), int(obj_dict['height']), animation_dict,
                    animation_time=int(obj_dict['animation-time']))
    tmp.render = True
    tmp.pause = False
    tmp.clear = False
    return tmp

  def translate_to_tile(self, tile_x, pos_x, tile_y, pos_y):
    """
    Tranlate global coordinates to relative positions to a tile

    :param tile_x: The x coordinates of the tile to translate to 
    :type tile_x: int
    :param pos_x: The global x coordinates to be translated
    :type pos_x: int
    :param tile_y: The y coordinates of the tile to translate to 
    :type tile_y: int
    :param pos_y: The global y coordinates to be translated
    :type pos_y: int
    """
    x = int(tile_x) * DISPLAY_SIZE['x'] + pos_x
    y = int(tile_y) * DISPLAY_SIZE['y'] + pos_y
    return x, y

  def handle_keypress_local(self, game_dict):
    """
    Handles keypresses from the a keyboard

    :param game_dict: The organized game_object dictionary
    :type game_dict: dict[GameObjects]
    :returns: Kill signal
    :rtype: bool
    """
    player1 = game_dict['Player'][0]
    player2 = game_dict['Player'][1]
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return True
      elif event.type == KEYDOWN:
        if event.key == K_ESCAPE:
          return True
        if event.key == K_LEFT:
          player1.move_left()
          player1.escape(1)
        elif event.key == K_RIGHT:
          player1.move_right()
          player1.escape(2)
        elif event.key == K_UP:
          player1.up_interact(game_dict['ClimableObject'])
        elif event.key == K_DOWN:
          player1.down_interact(game_dict['ClimableObject'])
        elif event.key == K_t:
          player1.throw_data()
        elif event.key == K_z:
          player1.jump()
        if event.key == K_r:
          self.el_time = 0

          # player2
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
        elif event.key == K_UP:
          player1.cancel_up_down_interact()
        elif event.key == K_DOWN:
          player1.cancel_up_down_interact()
        elif event.key == K_d:
          player2.stop_right()
    return False

  def handle_keypress(self, game_dict):
    """
    Handles keypresses from the ArcadeX tankstick    

    :param game_dict: The organized game_object dictionary
    :type game_dict: dict[GameObjects]
    :returns: Kill signal
    :rtype: bool
    """
    player1 = game_dict['Player'][0]
    player2 = game_dict['Player'][1]
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return True
      elif event.type == KEYDOWN:
        if event.key == K_ESCAPE:
          return True
        if event.key == K_r:
          self.el_time = 0
          print("restarted")
        if event.key == K_KP4:
          player1.move_left()
          player1.escape(1)
        elif event.key == K_KP6:
          player1.move_right()
          player1.escape(2)
        elif event.key == K_KP8:
          player1.up_interact(game_dict['ClimableObject'])
        elif event.key == K_KP2:
          player1.down_interact(game_dict['ClimableObject'])
        elif event.key == K_c:
          player1.interact(self.game_objects.values())  # TODO: We are passing in way to much data here, fix it.
        elif event.key == K_5:
          player1.jump()

        # player2
        elif event.key == K_d:
          player2.move_left()
          player2.escape(1)
        elif event.key == K_g:
          player2.move_right()
          player2.escape(2)
        elif event.key == K_r:
          player2.up_interact(game_dict['ClimableObject'])
        elif event.key == K_f:
          player2.down_interact(game_dict['ClimableObject'])
        elif event.key == K_6:
          player2.jump()
        elif event.key == K_RIGHTBRACKET:
          player2.interact(self.game_objects.values())

      elif event.type == KEYUP:
        if event.key == K_KP4:
          player1.stop_left()
        elif event.key == K_KP6:
          player1.stop_right()
        elif event.key == K_KP8:
          player1.cancel_up_down_interact()
        elif event.key == K_KP2:
          player1.cancel_up_down_interact()
        elif event.key == K_d:
          player2.stop_left()
        elif event.key == K_g:
          player2.stop_right()
        elif event.key == K_f:
          player2.cancel_up_down_interact()
        elif event.key == K_r:
          player2.cancel_up_down_interact()
