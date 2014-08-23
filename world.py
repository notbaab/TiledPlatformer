import pygame
import engine as eng

GRAVITY_VELOCITY = 1  # lets cheat for now
FLOOR_Y = 580
PLAYER_SPEED = 10
JUMP_VELOCITY = -10

# TODO: add more things to do
class GameObject(object):
  """the top level game object. All game objects inherit from this class"""

  def __init__(self):
    if "id" not in GameObject.__dict__:
      self.id = 0  # static variable
    else:
      self.id += 1

  def update(self):
    return

# TODO: add sprites
class SimpleScenery(GameObject):
  """Simple SimpleScenery object. Game objects that are just simple shapes"""

  def __init__(self, startx, starty, width, height, color):
    super(SimpleScenery, self).__init__()
    self.startx = startx
    self.starty = starty
    self.width = width
    self.height = height
    self.color = color
    self.rect = pygame.Rect((startx, starty, width, height))

  def draw(self, surface):
    """Draw the simple scenery object"""
    pygame.draw.rect(surface, self.color, self.rect)


# TODO: add sprites
class Player(GameObject):
  def __init__(self, startx, starty, color, sprite_sheet=None):
    super(Player, self).__init__()
    self.color = color
    self.velocity = eng.VelocityStruct(0, 0)
    if not sprite_sheet:
      self.rect = pygame.Rect((startx, starty, 30, 30))

  def jump(self):
    self.velocity.dy = JUMP_VELOCITY

  def move_left(self):
    self.velocity.dx = -PLAYER_SPEED

  def move_right(self):
    self.velocity.dx = PLAYER_SPEED

  # def update(self):
  # self.rect.x += self.velocity.dx
  # # sprite_hit_list = pygame.sprite.spritecollide(self, walls)
  # # apply gravity
  #   self.rect.y += self.velocity.dy
  #   self.velocity.dy += GRAVITY_VELOCITY

  def stop_left(self):
    if self.velocity.dx < 0:
      self.velocity.dx = 0

  def stop_right(self):
    if self.velocity.dx > 0:
      self.velocity.dx = 0

  def draw(self, surface):
    pygame.draw.rect(surface, (255, 0, 0), self.rect)

