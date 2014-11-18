import pygame
from networking import NetworkGame
import world as wd
import engine as eng
import json
import ipdb
import os
import os.path
import random
# os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

DEBUG = False
network_settings = json.load(open('network_settings.json'))

if network_settings['localhost'] == "True":
  json_data = open('master_settings_mac_local.json')
  PYGAME_FLAGS = 0
else:
  json_data = open('master_settings.json')
  PYGAME_FLAGS = pygame.FULLSCREEN

config = json.load(json_data)

SCREEN_WIDTH = int(config['display_size'][0])
SCREEN_HEIGHT = int(config['display_size'][1])
BEZEL_SIZE = 120




class ClientPlatformer(NetworkGame):
  def __init__(self, tile, window_coordinates=None):
    """Sets up all the needed client settings"""
    super(ClientPlatformer, self).__init__(tile)
    if window_coordinates:
      # passed in the location for the window to be at. Used for debugging
      os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (window_coordinates[0], window_coordinates[1])
    pygame.init()
    self.load_time = .01
    
    self.engine = eng.Engine()
    self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), PYGAME_FLAGS)
    self.game_objects = {}

    # self.background = pygame.image.load("assets/background" + str(self.tile[0]) + str(self.tile[1]) + ".png")
    bg_map_file = open('bg_map.json')
    self.bg_map = json.load(bg_map_file)
    bg_map_file.close()
    bg_file = self.bg_map['dir'] + self.bg_map[str(self.tile[0]) + str(self.tile[1])]
    print(bg_file)
    # Crop here
    # background_file = "assets/backgrounds/BG" + str(self.tile[0]) + str(self.tile[1]) + ".png"
    if os.path.isfile(bg_file):
      self.background = pygame.image.load(bg_file)
    else:
      self.background = pygame.image.load("assets/BG30.png") 
    self.background_rect = self.background.get_rect()

  def init_game(self, data):
    """Get the initial configuration of the game from the master node."""
    for game_obj in data['game_obj']:
      constructor = getattr(wd, game_obj['constructor'])
      translate_pos = self.translate_to_local((game_obj['rect'][0], game_obj['rect'][1]))
      if constructor == wd.Player:
        print(translate_pos)
        print(game_obj['rect'])
      if translate_pos != 0:
        startx, starty = translate_pos[0], translate_pos[1]
        to_render = True
      else:
        startx, starty = game_obj['rect'][0], game_obj['rect'][1]
        to_render = False
        
      if 'sprite_sheet' in game_obj:
        try:
          
          self.game_objects[game_obj['id']] = constructor(startx, starty, game_obj['rect'][2], 
                                                          game_obj['rect'][3], 
                                                          sprite_sheet=game_obj['sprite_sheet'], 
                                                          obj_id=game_obj['id'])
        except Exception as e:
            ipdb.set_trace()
      else:
       # if issubclass(constructor, wd.Constructor):
       #  self.game_objects[game_obj['id']] = constructor(startx, starty, game_obj['rect'][2], 
       #                                                    game_obj['rect'][3], 
       #                                                    obj_id=game_obj['id'],)
       #  else:
       #    self.game_objects[game_obj['id']] = constructor(startx, starty, game_obj['rect'][2], 
       #                                                    game_obj['rect'][3], 
       #                                                    obj_id=game_obj['id'])
        try:
          self.game_objects[game_obj['id']] = constructor(startx, starty, game_obj['rect'][2], 
                                                          game_obj['rect'][3], 
                                                          obj_id=game_obj['id'])
        except Exception as e:
          ipdb.set_trace()

      self.game_objects[game_obj['id']].render = to_render


    print (self.game_objects)
    self.clear_rects = []
    return data

  def update(self, data):
    """override this method, only hook needed for the server
    :param data: A python dict with data passed from the server
    :type data: dict"""
    if data['state'] == 'play':
      return self.play_state(data)
    elif data['state'] == 'load':
      return self.load_state(data)
    else:
      ipdb.set_trace()

  def clear(self, rects=()):
    """clear where the previous game objects were + whatever rects are specified
    in the passed in rect(good for timers and debug messages"""
    update_rects = []
    for game_obj in self.game_objects.values():
      if game_obj.render == True and (isinstance(game_obj, wd.MovableGameObject)):
        self.window.blit(self.background, (game_obj.rect.x, game_obj.rect.y), game_obj.rect)
        update_rects.append(game_obj.rect)
    for rect in rects:
      self.window.blit(self.background, (rect.x, rect.y), rect)
      update_rects.append(rect)
    return update_rects

  def clear_entire_screen(self):
    self.window.blit(self.background, self.background_rect)

  def load_state(self, data):
    """Fires off a load animation for every game object that is on this nodes screen
    :param data: TODO: make this fire off a specific load animation
    :type data: dict"""
    self.clear_entire_screen()
    if True:  # skip the fancy loading animation for now...the pi's can't handle it :(
      for obj_id, game_obj in self.game_objects.items():
        if isinstance(game_obj, wd.SimpleScenery):
          game_obj.draw(self.window)
          game_obj.dirt_sprite = False  # DOn't draw again unless it moves
          game_obj.render = False
      pygame.display.flip()
      # return {'state':'play'} 
    # obj_on_screen = [game_obj for game_obj in self.game_objects.values() if game_obj.render]
    # self.engine.load_animation(obj_on_screen, self.background, self.window)
    update_rects = []
    for obj_id, game_obj in self.game_objects.items():
      if isinstance(game_obj, wd.SimpleScenery):
        game_obj.draw(self.window)
        game_obj.dirt_sprite = False  # DOn't draw again unless it moves
        update_rects.append(game_obj.rect)
    pygame.display.update(update_rects)
    return {'state': 'play'}

  def play_state(self, data):
    """the main loop of the game. Takes the python dict and checks if the game 
    object is in the nodes area. If so it sets it to render
    :para data: python dict with various game object packets
    :type data: dict"""
    if 'localhost' in data:
      self._handle_localhost(data['localhost'])
    update_rects = self.clear(self.clear_rects)
    self.clear_rects = []
    for obj_id in data['deleted_objs']:
      del self.game_objects[obj_id]
    for game_obj in data['added_objs']:
      constructor = getattr(wd, game_obj['constructor'])
      self.game_objects[game_obj['id']] = constructor(game_obj['rect'][0], game_obj['rect'][1],
                                                      game_obj['rect'][2], game_obj['rect'][3],
                                                      sprite_sheet=game_obj['sprite_sheet'], obj_id=game_obj['id'])

      self.game_objects[game_obj['id']].render = False

    for packet in data['game_objects']:
      translated_pos = self.translate_to_local((packet['rect'].x, packet['rect'].y))
      if translated_pos != 0:
        # TODO: don't translate here, do it in a better place
        packet['rect'].x, packet['rect'].y = translated_pos
        self.game_objects[packet['id']].read_packet(packet)
      else:
        self.game_objects[packet['id']].render = False

    # TODO: this is what loop over game dict is for
    # update_rects = []
    for obj_id, game_obj in self.game_objects.items():
      if game_obj.render:
        if isinstance(game_obj, wd.Effect):
          clear_rect = game_obj.draw(self.window, self)
        else:
          clear_rect = game_obj.draw(self.window)
        if game_obj.dirt_sprite:
          update_rects.append(game_obj.rect)
        if clear_rect:
          self.clear_rects.append(clear_rect)
    pygame.display.update(update_rects)

    data_struct = {'state': 'play'}
    return data_struct

  def translate_to_local(self, pos):
    """translates the given data to the local node. Wrapper for call to game
    :param pos: a tuple of an x and y coordinate
    :type pos: tuple
    :rtype: int or tuple
            pos[1] < (self.tile[1]+1)*(self.bezely) and 
        pos[1] >= self.tile[1]*(self.bezely)):
    """
    if ((self.tile[0] + 1) * (SCREEN_WIDTH + BEZEL_SIZE) > pos[0] >= self.tile[0] * (SCREEN_WIDTH) and
        (self.tile[1] + 1) * (SCREEN_HEIGHT + BEZEL_SIZE) > pos[1] >= self.tile[1] * (SCREEN_HEIGHT)):
      translated_pos = [pos[0] - self.tile[0] * (SCREEN_WIDTH+BEZEL_SIZE),  pos[1] - (self.tile[1]) * (SCREEN_HEIGHT+BEZEL_SIZE) ]
    else:
      translated_pos = 0
    return translated_pos  # , translated_pos_2)

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    pass

  def _handle_localhost(self, tile_packet):
    """running on local host, some work needs to be done in order to switch screens"""
    draw_background = False
    if tile_packet['x'] != self.tile[0]:
      self.tile[0] = tile_packet['x']
      draw_background = True
    if tile_packet['y'] != self.tile[1]:
      self.tile[1] = tile_packet['y']
      draw_background = True
    if draw_background:
      bg_file = self.bg_map['dir'] + self.bg_map[str(self.tile[0]) + str(self.tile[1])]
      self.background = pygame.image.load(bg_file)
      self.background_rect = self.background.get_rect()
      self.clear_entire_screen()


  def draw_grid(self, surface):
    """Dev function to draw the grid space of the display wall"""
    SCREEN_WIDTH = int(config['display_size'][0])
    SCREEN_HEIGHT = int(config['display_size'][1])
    pygame.draw.line(surface, color, start_pos, end_pos, width=1)
    grid = [5, 3]
    display_size_x = 200
    display_size_y = 200 
    bezel_x = 30
    bezel_y = 30
    for x in range(grid[0]):
      for y in range(grid[1]):
        pygame.draw.line(surface, (255, 255, 255), start_pos, end_pos, width=1)



