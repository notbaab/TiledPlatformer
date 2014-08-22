import pygame
import sys
import ipdb
from pygame.locals import *
import world as wd
import engine as eng
loc = [] 
FPS = pygame.time.Clock()

GRID_SIZEX = 100  # will probably need to be rectangular
GRID_SIZEY = 100


if __name__ == '__main__':
  # Display stuff Should be segmented later
  pygame.init() 

  game_objects = {}
  window = pygame.display.set_mode((600, 600))
  engine = eng.Engine()

  # load map
  floors = engine.parse_json("map.json")
  game_objects['terrain'] = []

  for floor in floors:
    # TODO: MAP!!!!
    game_objects['terrain'].append(wd.SimpleScenery(int(floor["x"]), int(floor["y"]), 
                                   int(floor["width"]), int(floor["height"]), (255, 255, 000)))

  # players
  game_objects['players'] = []
  game_objects['players'].append(wd.Player(70, 500, (255, 0, 0)))

  print(game_objects)

  # MAKE THIS OO!!!! 
  while True:
    window.fill((0, 0, 0))

    # control block This will be the master node
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
          sys.exit()
      if event.type == KEYDOWN:
        for player in game_objects['players']:
          if event.key == K_LEFT:
            player.move_left()
          if event.key == K_RIGHT:
            player.move_right()
          if event.key == K_SPACE:
            player.jump()
      if event.type == KEYUP:
        for player in game_objects['players']:
          if event.key == K_LEFT:
            player.stop_left()
          if event.key == K_RIGHT:
            player.stop_right()
            
    engine.physics_simulation(game_objects['players'], game_objects['terrain'])

    # This will be the call to the network to send the new rect and draw them.
    for obj_type, obj_list in game_objects.items():
      for game_obj in obj_list:
        game_obj.draw(window)

    pygame.display.flip()
    FPS.tick(10)


