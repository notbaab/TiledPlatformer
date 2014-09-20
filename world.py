import pygame
import engine as eng
from itertools import cycle


GRAVITY_VELOCITY = 1  # lets cheat for now
FLOOR_Y = 580
PLAYER_SPEED = 10
JUMP_VELOCITY = -10


# TODO: add more things to do
class GameObject(object):
  """the top level game object. All game objects inherit from this class"""
  id = 0

  def __init__(self, obj_id=None):
    self.rect = None
    if not obj_id:
      self.id = GameObject.id  # assign
      GameObject.id += 1
    else:
      self.id = obj_id
    self.render = True

  def update(self):
    return

  def build_packet(self, packet):
    """accumulator function that will build the packet for each game object"""
    import ipdb
    ipdb.set_trace()

  def read_packet(self, packet):
    import ipdb
    ipdb.set_trace()    

  def animate(self):
    return


class MovableGameObject(GameObject):
  """any game object that moves"""

  def __init__(self, startx, starty, width, height, obj_id=None):
    super(MovableGameObject, self).__init__(obj_id=obj_id)
    # print(self.render)
    self.velocity = eng.Vector(0, 0)
    self.rect = pygame.Rect((startx, starty, width, height))

  def move(self, velocity):
    self.velocity = velocity

  def respond_to_collision(self, obj, axis=None):
    """Contains the callback for the collision between a player object and a game object passed in. Axis is needed
    for collisions that halt movement
    :param obj: object player is colliding with
    :type obj: GameObject
    :param axis: which axis was the player moving along.
    :type axis: String """
    if type(obj) == SimpleScenery:
      if axis == 'x':
        if self.velocity.x > 0:
          self.rect.right = obj.rect.left
        if self.velocity.x < 0:
          self.rect.left = obj.rect.right
        self.velocity.x = 0
      if axis == 'y':
        if self.velocity.y > 0:
          self.rect.bottom = obj.rect.top
        if self.velocity.y < 0:
          self.rect.top = obj.rect.bottom
        self.velocity.y = 0


# TODO: add sprites
class SimpleScenery(GameObject):
  """Simple SimpleScenery object. Game objects that are just simple shapes"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super(SimpleScenery, self).__init__(obj_id=obj_id)
    self.startx = startx
    self.starty = starty
    self.width = width
    self.height = height
    self.color = color
    self.rect = pygame.Rect((startx, starty, width, height))

  def draw(self, surface):
    """Draw the simple scenery object"""
    pygame.draw.rect(surface, self.color, self.rect)

  def build_packet(self, accumulator):
    """Not needed for static objects"""
    return


# TODO: add sprites
class Player(MovableGameObject):
  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super(Player, self).__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    self.sprite = sprite_sheet
    if not sprite_sheet:
      self.rect = pygame.Rect((startx, starty, width, height))
    else:
      # TODO: Add sprite sheet parsing to engine
      self.sprite = pygame.image.load(sprite_sheet).convert_alpha()
      self.rect = self.sprite.get_rect()
    # TODO: Each frame will be a tuple of where to go in the sprite sheet, not a color. With no graphics, it's now
    # just a list of colors to cycle throug
    self.animation_frames = {'moving':[eng.Colors.RED, eng.Colors.GREEN], 'hasdata':[eng.Colors.BLUE]}
    self.current_animation = 'moving'
    self.current_cycle = cycle(self.animation_frames[self.current_animation])
    self.current_frame = next(self.current_cycle)
    self.animation_time = 10
    self.animation_timer = 0
    self.data = None
    self.direction = 'left'

  def jump(self):
    self.velocity.y = JUMP_VELOCITY

  def move_left(self):
    self.velocity.x = -PLAYER_SPEED
    self.direction = 'left'

  def move_right(self):
    self.velocity.x = PLAYER_SPEED
    self.direction = 'right'

  def stop_left(self):
    if self.velocity.x < 0:
      self.velocity.x = 0

  def stop_right(self):
    if self.velocity.x > 0:
      self.velocity.x = 0

  def draw(self, surface):
    if self.sprite:
      surface.blit(self.sprite, self.rect)
    else:
      pygame.draw.rect(surface, self.current_frame, self.rect)

  def change_sprite(self, image):
    # TODO: cycle through sprite sheet, not load another image
    self.sprite = pygame.image.load(image)

  def change_animation(self, frame):
    """change the frames that player object is currently cycling through"""
    if not frame in self.animation_frames:
      import ipdb
      ipdb.set_trace()
    self.current_animation = frame
    self.current_cycle = cycle(self.animation_frames[self.current_animation])

  def animate(self):
    """goes to next frame in current animation frame"""
    self.animation_timer += 1
    if self.animation_timer == self.animation_time:
      self.current_frame = next(self.current_cycle)
      self.animation_timer = 0

  def build_packet(self, accumulator):
    packet = {'type': 'player', 'location': [self.rect.x, self.rect.y], 'frame': self.current_frame, 'id': self.id}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.current_frame = packet['frame']
    self.render = True

  def respond_to_collision(self, obj, axis=None):
    """Contains the callback for the collision between a player object and a game object passed in. Axis is needed
    for collisions that halt movement
    :param obj: object player is colliding with
    :type obj: GameObject
    :param axis: which axis was the player moving along.
    ":type axis: String """
    super().respond_to_collision(obj, axis)
    if type(obj) == Data:
      if self.data == None:
        self.data = obj
        obj.rect.x, obj.rect.y = -100, -100 # TODO: have better way than move off screen
        self.change_animation('hasdata')

  def throw_data(self):
    if self.data:
      if self.direction == 'left':
        x_throw = self.rect.left + self.data.rect.width
      else:
        x_throw = self.rect.right - self.data.rect.width        
      self.data.rect.x = x_throw
      self.data.rect.y = self.rect.y 
      self.data.velocity.y = 10
      self.data.velocity.x = 10


class DataDevice(SimpleScenery):
  """Devices that are scenery, but output data when interacted with"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super(DataDevice, self).__init__(startx, starty, width, height, color, obj_id=obj_id)
    print(self.startx)
    self.timer = None
    self.color = color

  def build_packet(self, accumulator):
    packet = {'type': 'data_device', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id,}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.render = True

  def draw(self, surface):
    pygame.draw.rect(surface, self.color, self.rect)


class Data(MovableGameObject):
  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super(Data, self).__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    self.sprite_sheet = sprite_sheet

  def draw(self, surface):
    if self.sprite_sheet:
      surface.blit(self.sprite_sheet, self.rect)
    else:
      pygame.draw.rect(surface, (155, 0, 0), self.rect)

  def build_packet(self, accumulator):
    packet = {'type': 'data', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.render = True

