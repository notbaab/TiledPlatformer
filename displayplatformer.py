import pygame
from networking import NetworkedTileGame
import world as wd
import engine as eng
import json
# import ipdb
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


class ClientPlatformer(NetworkedTileGame):
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
    if tile[0] == 2 and tile[1] == 0:
      self.score_node = True
      self.blue_score = 0
      self.blue_score_loc = 400, 400
      self.red_score = 0
      self.red_score_loc = 1400, 400
    else:
      self.score_node = False

    bg_map_file = open('bg_map.json')
    self.bg_map = json.load(bg_map_file)
    bg_map_file.close()
    bg_file = self.bg_map['dir'] + self.bg_map[str(self.tile[0]) + str(self.tile[1])]
    if os.path.isfile(bg_file):
      self.background = pygame.image.load(bg_file).convert()
    else:
      self.background = pygame.image.load("assets/BG30.png").convert()
    self.background_rect = self.background.get_rect()

  def init_game(self, data):
    """Get the initial configuration of the game from the master node."""
    for game_obj in data['game_obj']:
      constructor = getattr(wd, game_obj['constructor'])
      if not issubclass(constructor, wd.NetworkedObject):
        continue  # we really only need objects that won't be updated. This could be modified to include static objects
                  #  that will stay on one tile and not move, but we really don't need even that.
      translate_pos = self.translate_to_local((game_obj['rect'][0], game_obj['rect'][1]))
      if translate_pos != 0:
        startx, starty = translate_pos[0], translate_pos[1]
        to_render = True
      else:
        startx, starty = game_obj['rect'][0], game_obj['rect'][1]
        to_render = False

      if 'sprite_sheet' in game_obj:
        self.game_objects[game_obj['id']] = constructor(startx, starty, game_obj['rect'][2],
                                                        game_obj['rect'][3],
                                                        sprite_sheet=game_obj['sprite_sheet'],
                                                        obj_id=game_obj['id'])
      else:
        self.game_objects[game_obj['id']] = constructor(startx, starty, game_obj['rect'][2],
                                                        game_obj['rect'][3],
                                                        obj_id=game_obj['id'])

      self.game_objects[game_obj['id']].render = to_render

    self.clear_rects = []
    self.old_time = None
    return data

  def update(self, data):
    """override this method, only hook needed for the server
    :param data: A python dict with data passed from the server
    :type data: dict"""
    if data['state'] == 'play':
      return self.play_state(data)
    elif data['state'] == 'load':
      return self.load_state(data)
    elif data['state'] == 'win':
      return self.win_state()
    else:
      ipdb.set_trace()

  def win_state(self):
    return {'state': 'play'}

  def clear(self, rects=()):
    """clear where the previous game objects were + whatever rects are specified
    in the passed in rect(good for timers and debug messages"""
    update_rects = []
    for game_obj in self.game_objects.values():
      if game_obj.render and (isinstance(game_obj, wd.MovableGameObject)):
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
      if self.score_node:
        self.draw_message(self.blue_score_loc[0], self.blue_score_loc[1], self.blue_score)
        self.draw_message(self.red_score_loc[0], self.red_score_loc[1], self.red_score)

      pygame.display.flip()
    return {'state': 'play'}

  def play_state(self, data):
    """the main loop of the game. Takes the python dict and checks if the game 
    object is in the nodes area. If so it sets it to render
    :para data: python dict with various game object packets
    :type data: dict"""
    if 'localhost' in data:
      self._handle_localhost(data['localhost'])
    update_rects = self.clear(self.clear_rects)
    if self.score_node:
      if 'score' in data:
        if data['score'][0] != self.blue_score:
          self.blue_score = data['score'][0]
          update_rects.append(self.draw_message(self.blue_score_loc[0], self.blue_score_loc[1], self.blue_score))
        if data['score'][1] != self.red_score:
          self.red_score = data['score'][1]
          update_rects.append(self.draw_message(self.red_score_loc[0], self.red_score_loc[1], self.red_score))
      if 'time' in data and data['time'] != self.old_time:
        self.draw_message(1920 / 2, 200, data['time'])
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
    if ((self.tile[0] + 1) * (SCREEN_WIDTH + BEZEL_SIZE) > pos[0] >= self.tile[0] * SCREEN_WIDTH and
                (self.tile[1] + 1) * (SCREEN_HEIGHT + BEZEL_SIZE) > pos[1] >= self.tile[1] * SCREEN_HEIGHT):
      translated_pos = [pos[0] - self.tile[0] * (SCREEN_WIDTH + BEZEL_SIZE),
                        pos[1] - (self.tile[1]) * (SCREEN_HEIGHT + BEZEL_SIZE)]
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

  def draw_message(self, centerx, bottom, message):
    """draw text somewhere on the screen"""
    eng.FONT.set_bold(True)
    font_to_render = eng.FONT.render(str(message), True, (255, 0, 0))
    font_rect = font_to_render.get_rect()
    font_rect.centerx = centerx
    font_rect.bottom = bottom
    self.window.blit(self.background, (font_rect.x, font_rect.y), font_rect)
    # pygame.display.update(font_rect)
    self.window.blit(font_to_render, font_rect)
    return font_rect



