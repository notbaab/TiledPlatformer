import pygame
from networking import NetworkGame
import world as wd
import engine as eng
#import ipdb

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600


class ClientPlatformer(NetworkGame):
  def __init__(self, tile):
    """Sets up all the needed client settings"""
    super(ClientPlatformer, self).__init__(tile)
    pygame.init()
    self.load_time = .01

    self.engine = eng.Engine()
    self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.game_objects = {}

    # load map
    self.game_objects['terrain'] = []
    self.game_objects['players'] = []
    self.game_objects['data_object'] = []

  def init_game(self, data):
    """Get hte initial configuration of the game from the master node."""
    for obj_type, obj_list in data.items():
      self.game_objects[obj_type] = []
      for game_obj in obj_list:
        constructor = getattr(wd, game_obj['constructor'])
        self.game_objects[obj_type].append(constructor(game_obj["rect"][0], game_obj["rect"][1],
                                                       game_obj["rect"][2], game_obj["rect"][3],
                                                       color=game_obj["color"], obj_id=game_obj["id"]))
    print(self.game_objects['players'])
    return data

  def update(self, data):
    """override this method, only hook needed for the server"""
    if data['state'] == 'play':
      return self.play_state(data)
    else:
      pass#ipdb.set_trace()

  def clear(self, data):
    """override this method, only hook needed for the server"""
    self.window.fill((0, 0, 0))

  def play_state(self, data):
    # TODO: why am I passing data in here?
    self.clear('Why does this need an argument?')
    # test
    # pygame.draw.rect(self.window, (255,0,255), pygame.Rect(20,20,100*self.load_time,20))
    # pygame.draw.rect(self.window, (128,0,128), pygame.Rect(20,20,100,20), 1)
    # self.load_time += .01
    for i in range(len(data['player_locs'])):
      translated_pos = self.translate_to_local(data['player_locs'][i])
      if translated_pos != 0:
        self.game_objects['players'][i].rect.x = translated_pos[0]
        self.game_objects['players'][i].rect.y = translated_pos[1]
        self.game_objects['players'][i].render = True
      else:
        self.game_objects['players'][i].render = False

    self.game_objects['data_object'] = []
    # print(data)
    # TODO: Don't make a new object, send the object IDs with the packet
    for data_pos_object in data['data_object']:
      translated_pos = self.translate_to_local(data_pos_object)
      self.game_objects['data_object'].append(wd.Data(translated_pos[0],
                                                      translated_pos[1], 20, 20,
                                                      color=(255, 255, 0)))

    for obj_type, obj_list in self.game_objects.items():
      for game_obj in obj_list:
        if game_obj.render:
          game_obj.draw(self.window)
    pygame.display.flip()

    data_struct = {'state': 'play'}
    return data_struct

  # TODO: actually do that.
  def translate_to_local(self, pos):
    """translates the given data to the local node. Wrapper for call to game
    """
    if (pos[0] < (self.tile[0] + 1) * SCREEN_WIDTH and
            pos[0] >= self.tile[0] * SCREEN_WIDTH and
            pos[1] < (self.tile[1] + 1) * SCREEN_HEIGHT and
            pos[1] >= self.tile[1] * SCREEN_HEIGHT):
      translated_pos = [pos[0] - self.tile[0] * SCREEN_WIDTH,
                        (self.tile[1]) * SCREEN_HEIGHT + pos[1]]
      # print("player 1 trans at " + str(translated_pos))
    else:
      translated_pos = 0
    return translated_pos  # , translated_pos_2)

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    pass
