import pygame
import engine as eng
from itertools import cycle


GRAVITY_VELOCITY = 1  # lets cheat for now
FLOOR_Y = 580
PLAYER_SPEED = 10
FOLLOWER_SPEED = PLAYER_SPEED - 6 # just slower than the players
JUMP_VELOCITY = -10
DATA_DEVICE_TIMER = .01


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
    """anything that the object needs to do every frame"""
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

  def stop(self):
    self.velocity = [0, 0]

  def respond_to_collision(self, obj, axis=None):
    """Contains the callback for the collision between a move able object and the
    object passed in. If the object passed in is the environment (i.e. SimpleScenery)
    it will treate the environment as a wall and stop the object.
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
    # just a list of colors to cycle through
    self.animation_frames = {'moving': [eng.Colors.RED, eng.Colors.GREEN], 'hasdata': [eng.Colors.BLUE]}
    self.current_animation = 'moving'
    self.current_cycle = cycle(self.animation_frames[self.current_animation])
    self.current_frame = next(self.current_cycle)
    self.animation_time = 10
    self.animation_timer = 0
    self.data = None
    self.direction = 'left'

  def jump(self):
    self.velocity.y = JUMP_VELOCITY

  # TODO: Why have two methods for move?
  def move_left(self):
    """sets velocity of player to move left"""
    self.velocity.x = -PLAYER_SPEED
    self.direction = 'left'

  def move_right(self):
    """sets velocity of player to move right"""
    self.velocity.x = PLAYER_SPEED
    self.direction = 'right'

  # TODO: why have two methods for stop
  def stop_left(self):
    """sets velocity to 0"""
    if self.velocity.x < 0:
      self.velocity.x = 0

  def stop_right(self):
    """sets velocity to 0"""
    if self.velocity.x > 0:
      self.velocity.x = 0

  def draw(self, surface):
    """Draws the player object onto surface
    :param surface: the surface to draw the object, typically the window
    :type surface: pygame.Surface"""
    if self.sprite:
      surface.blit(self.sprite, self.rect)
    else:
      pygame.draw.rect(surface, self.current_frame, self.rect)

  def change_animation(self, frame):
    """change the frames that player object is currently cycling through.
    :param frame: a key that maps to a list of animation frames in self.animation_frames
    :type frame: String"""
    if not frame in self.animation_frames:
      import ipdb

      ipdb.set_trace()
    self.current_animation = frame  # TODO: evaluate if we need this member
    self.current_cycle = cycle(self.animation_frames[self.current_animation])

  def animate(self):
    """Updates the animation timer goes to next frame in current animation cycle 
    after the alloted animation time has passed."""
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
      if self.data is None:
        self.data = obj
        obj.rect.x, obj.rect.y = -100, -100  # TODO: have better way than move off screen
        self.change_animation('hasdata')

  def throw_data(self):
    if self.data:
      if self.direction == 'left':
        x_throw = self.rect.left + self.data.rect.width
        self.data.velocity.x = -10
      else:
        x_throw = self.rect.right - self.data.rect.width
        self.data.velocity.x = 10
      self.data.rect.x = x_throw
      self.data.rect.y = self.rect.y
      self.data.velocity.y = 10


class DataDevice(SimpleScenery):
  """Devices that are scenery, but output data when interacted with"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super(DataDevice, self).__init__(startx, starty, width, height, color, obj_id=obj_id)
    print(self.startx)
    self.timer = None
    self.color = color
    self.data = None

  def build_packet(self, accumulator):
    packet = {'type': 'data_device', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id,
              'timer': self.timer}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    if packet['timer']:
      print(packet['timer'])
      self.timer = packet['timer']
    else:
      self.timer = None
    self.render = True

  def draw(self, surface):
    pygame.draw.rect(surface, self.color, self.rect)
    if self.timer:
      pygame.draw.rect(surface, (255, 0, 255), pygame.Rect(20, 20, 100 * self.timer, 20))
      pygame.draw.rect(surface, (128, 0, 128), pygame.Rect(20, 20, 100, 20), 1)

  def update(self):
    if self.data:
      self.timer += DATA_DEVICE_TIMER
      if self.timer >= 1:
        print('ented')
        # self.data.rect.right = self.rect.left + 10
        # self.data.rect.bottom = self.rect.y + self.height
        self.data.rect.right = self.rect.left - self.data.rect.width
        self.data.rect.y = self.rect.y
        self.data.velocity.y = -50
        self.data.velocity.x = -20
        print(self.data.rect)
        print(self.rect)
        self.data = None
        self.timer = None

  def respond_to_collision(self, obj, axis=None):
    if type(obj) == Data:
      self.timer = DATA_DEVICE_TIMER  # start timer
      self.data = obj
      # TODO: Make a better hide/delete function
      obj.rect.move_ip(-100, -100)

  def get_data(self, data):
    self.timer = DATA_DEVICE_TIMER  # start timer
    self.data = data
    # TODO: Make a better hide/delete function
    data.rect.x, data.rect.y = (-100, -100)
    data.velocity.x = 0
    data.velocity.y = 0


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

  def respond_to_collision(self, obj, axis=None):
    super().respond_to_collision(obj, axis)
    if type(obj) == DataDevice:
      obj.get_data(self)

class Follower(MovableGameObject):
  """a class that follows it's leader"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super(Follower, self).__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    self.sprite_sheet = sprite_sheet
    self.leader = None
    self.velocity = eng.Vector(0, 0)

  def update(self):
    if self.leader:
      # figure out which direction to move
      if self.leader.rect.x - self.rect.x > 0:
        self.velocity.x = FOLLOWER_SPEED  # move right
      elif self.leader.rect.x - self.rect.x < 0:
        self.velocity.x = -FOLLOWER_SPEED  # move left
      else:
        self.velocity.x = 0
    self.rect.x += self.velocity.x

  def draw(self, surface):
    pygame.draw.rect(surface, (0, 0, 155), self.rect)

  # TODO: move this to MoveableGameObject
  def build_packet(self, accumulator):
    packet = {'type': 'data', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.render = True


