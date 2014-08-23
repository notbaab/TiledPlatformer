import pygame
from networking import NetworkGame
import world as wd
import engine as eng
import ipdb


class ClientPlatformer(NetworkGame):
  def __init__(self, tile):
    """Sets up all the needed client settings"""
    super(ClientPlatformer, self).__init__(tile)
    pygame.init()

    self.engine = eng.Engine()
    self.window = pygame.display.set_mode((600, 600))
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
    self.game_objects['players'][0].rect.x = data['player_loc'][0]
    self.game_objects['players'][0].rect.y = data['player_loc'][1]
    for obj_type, obj_list in self.game_objects.items():
      # print(obj_list)
      for game_obj in obj_list:
        # print(game_obj)
        game_obj.draw(self.window)
    pygame.display.flip()

    data_struct = {'state': 'play'}
    return data_struct

  # TODO: actually do that. 
  def translate_to_local(self, data):
    """translates the given data to the local node. Wrapper for call to game
    """
    pass

  def tanslate_to_global(self):
    """tanstlates the data to the global data """
    pass