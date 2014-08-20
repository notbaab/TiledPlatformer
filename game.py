import pygame, sys
from pygame.locals import *
import world as wd
loc = [] 
FPS = pygame.time.Clock()

GRID_SIZEX = 100 # will probably need to be rectangular
GRID_SIZEY = 100
GRAVITY_VELOCITY = -1 # lets cheat for now
FLOOR_Y = 580
JUMP_VELOCITY = 20

class Player():
  def __init__(self, startloc, color):
    self.location = startloc
    self.color = color
    self.velocity = [0,0]
    self.velocity[0] = 0 # x vel
    self.velocity[1] = 0 # y vel
  def jump(self):
    self.velocity[1] = JUMP_VELOCITY
  def moveleft(self):
    self.velocity[0] = -1
  def moveright(self):
    self.velocity[0] = 1
  def update(self):
    self.location[0] += self.velocity[0]
    # apply gravity
    self.location[1] += self.velocity[1]
    self.velocity += GRAVITY_VELOCITY
    if self.location[1] < FLOOR_Y:
      self.location[1] = FLOOR_Y + 20
  def draw(self, surface):
    pygame.draw.rect(surface, (255,0,0), (self.location[0], self.location[1], 20, 20) )



if __name__ == '__main__':
  # Display stuff Should be segmented later
  pygame.init() 

  player = Player( [30,30], (255,0,0) )
  floor = wd.SimpleScenery(9, 9, 10, 10, (255,255,0) )
  window = pygame.display.set_mode( (600, 600) )


  # Make a floor
  pygame.draw.rect( window, (0,0,255), (0, 580, 600, 20) )


  # MAKE THIS OO!!!! 
  while True:
    floor.draw(window)
    # control block This will be the master node
    for event in pygame.event.get():
          if event.type == pygame.QUIT:
              sys.exit()
          if event.type == KEYDOWN:
              if event.key == K_LEFT:
                player.moveleft()
              if event.key == K_RIGHT:
                player.moveright()
              if event.key == K_UP:
                player.jump()
    player.draw(window)

    pygame.display.flip()
    FPS.tick(60)


