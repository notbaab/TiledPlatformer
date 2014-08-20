import pygame

class GameObject(object):
  """the top level game object. All game objects inherit from this class"""
  def __init__(self):
    if "id" not in GameObject.__dict__: 
      self.id = 0 # static variable 
    else: 
      self.id += 1

class SimpleScenery(GameObject):
  """Simple SimpleScenery object. Game objects that are just simple shapes"""
  def __init__(self, startx, starty, width, height, color):
    super(SimpleScenery, self).__init__()
    self.startx = startx
    self.starty = starty
    self.width = width
    self.height = height
    self.color = color
    self.rect = pygame.Rect( (startx, starty, width, height) )

  def draw(self, surface):
    """Draw the simple scenery object""" 
    pygame.draw.rect(surface, self.color, self.rect)

class Player(GameObject):
  def __init__(self, startloc, color):
    super(Player, self)
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
    pygame.draw.rect(surface, (255,0,0), (self.location[0], self.location[1], 20, 20))

