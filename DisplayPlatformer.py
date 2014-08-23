import pygame
from networking import NetworkGame
import world as wd
import engine as eng
import ipdb
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600


class ClientPlatformer(NetworkGame):
  def __init__(self, tile):
    """Sets up all the needed client settings"""
    super(ClientPlatformer, self).__init__(tile)
    pygame.init()

    self.engine = eng.Engine()
    self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.game_objects = {}

    # load map 
    self.floors = self.engine.parse_json('map.json')
    self.game_objects['terrain'] = []
    for floor in self.floors:
      # TODO: MAP!!!!
      self.game_objects['terrain'].append(wd.SimpleScenery(int(floor["x"]), int(floor["y"]),
                                                           int(floor["width"]), int(floor["height"]), (255, 255, 000)))

    # players
    self.game_objects['players'] = []
    self.game_objects['players'].append(wd.Player(70, 500, (255, 0, 0)))
    print(self.game_objects)

  def update(self, data):
    """override this method, only hook needed for the server"""
    if data['state'] == 'play':
      return self.play_state(data)
    else:
      ipdb.set_trace()

  def clear(self, data):
    """override this method, only hook needed for the server"""
    self.window.fill((0, 0, 0))

  def play_state(self, data):
    # TODO: why am I passing data in here?
    self.clear('Why does this need an argument?')
    translated_pos = self.translate_to_local(data['player_loc'])
    if translated_pos != 0:
      self.game_objects['players'][0].rect.x = translated_pos[0]
      self.game_objects['players'][0].rect.y = translated_pos[1]
      self.game_objects['players'][0].render = True
    else:
      self.game_objects['players'][0].render = False      
    
    for obj_type, obj_list in self.game_objects.items():
      # print(obj_list)
      for game_obj in obj_list:
        # print(game_obj)
        if game_obj.render:
          game_obj.draw(self.window)
    pygame.display.flip()

    data_struct = {'state': 'play'}
    return data_struct

  # TODO: actually do that. 
  def translate_to_local(self, pos):
    """translates the given data to the local node. Wrapper for call to game
    """
    if (pos[0] < (self.tile[0]+1)*(SCREEN_WIDTH) and 
      pos[0] >= self.tile[0]*(SCREEN_WIDTH) and 
      pos[1] < (self.tile[1]+1)*(SCREEN_HEIGHT) and 
      pos[1] >= self.tile[1]*(SCREEN_HEIGHT)):
      translated_pos = [pos[0] - self.tile[0]*(SCREEN_WIDTH),
                         (self.tile[1])*(SCREEN_HEIGHT) + pos[1]] 
      print("player 1 trans at " + str(translated_pos))
    else: translated_pos = 0
    return translated_pos #, translated_pos_2)

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    pass