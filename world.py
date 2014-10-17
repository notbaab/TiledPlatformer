import pygame
import engine as eng
# from graphics import *
from itertools import cycle
import graphics
import ipdb
import random

ASSET_FOLDER = "assets/"
GRAVITY_VELOCITY = 4  # lets cheat for now
FLOOR_Y = 580
PLAYER_SPEED = 10
PLAYER_THROW_SPEED = eng.Vector(20, -5)
FOLLOWER_SPEED = PLAYER_SPEED - 3  # just slower than the players
PATROL_SPEED = 4  # just slower than the players
JUMP_VELOCITY = -20
DATA_DEVICE_TIMER = .01
TIMER_WIDTH = 100
PLAYER_INTERACT_DIST = 50
EJECT_SPEED = eng.Vector(20, -20)
PLAYER_MASH_NUMBER = 10  # the number of times the player has to mash a button to escape


# TODO: add more things to do
class GameObject(object):
  """the top level game object. All game objects inherit from this class."""
  id = 0

  def __init__(self, startx, starty, width, height, obj_id=None):
    self.rect = pygame.Rect((startx, starty, width, height))
    if not obj_id:
      self.id = GameObject.id  # assign
      GameObject.id += 1
    else:
      self.id = obj_id
    self.render = True
    self.message_str = None  # info that is displayed above the object
    self.to_del = False
    self.physics = False  # Does this class need physics?

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

  def draw(self, window):
    if self.message_str:
      eng.FONT.set_bold(True)
      font_to_render = eng.FONT.render(str(self.message_str), True, (0, 0, 0))
      font_rect = font_to_render.get_rect()
      font_rect.centerx = self.rect.centerx
      font_rect.bottom = self.rect.top - 10
      window.blit(font_to_render, font_rect)


class SpriteGameObject(GameObject):
  pass

class Constructor(object):
  """A special object that contains a reference to the entire game. Inherited
  by classes that need to construct objects in the game world"""
  def __init__(self, game):
    super().__init__()
    self.game = game

  def add_to_world(self, obj):
    if self.game:
      self.game.added.append(obj)
    else:
      ipdb.set_trace()


class MovableGameObject(GameObject):
  """any game object that moves"""

  def __init__(self, startx, starty, width, height, obj_id=None):
    super().__init__(startx, starty, width, height, obj_id=obj_id)
    self.velocity = eng.Vector(0, 0)
    # self.rect = pygame.Rect((startx, starty, width, height))
    self.physics = True  # most movable game objects need physics

  def move(self, velocity):
    self.velocity = velocity

  def stop(self):
    self.velocity = [0, 0]

  def hide_object(self):
    """moves turns of physics and rendering for the object"""
    self.render = False
    self.physics = False
    self.rect.x, self.rect.y = -1000, -1000  # move somewhere far off screen to

  def unhide_object(self):
    """moves turns of physics and rendering for the object"""
    self.render = True
    self.physics = True

  def respond_to_collision(self, obj, axis=None):
    """Contains the callback for the collision between a move able object and the
    object passed in. If the object passed in is the environment (i.e. SimpleScenery)
    it will treate the environment as a wall and stop the object.
    :param obj: object player is colliding with
    :type obj: GameObject
    :param axis: which axis was the player moving along.
    :type axis: String """
    # if isinstance(obj, SimpleScenery):
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


class SimpleScenery(GameObject):
  """Simple SimpleScenery object. Game objects that are just simple shapes"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
    super().__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet
    if self.sprite_sheet:
      self.sprite, self.frames = graphics.get_frames(ASSET_FOLDER + self.sprite_sheet, 1, 1, des_width=width, des_height=height)
    else:
      self.sprite = None
    self.current_frame = self.frames[0]

  def draw(self, surface):
    """Draw the simple scenery object"""
    super().draw(surface)
    if self.sprite:
      surface.blit(self.sprite, self.rect, area=self.current_frame)
    else:
      pygame.draw.rect(surface, self.color, self.rect)

  def build_packet(self, accumulator):
    """Not needed for static objects"""
    return


class Player(MovableGameObject):
  def __init__(self, startx, starty, width, height, sprite_sheet=None, color=None, obj_id=None):
    super().__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    self.rect = pygame.Rect((startx, starty, width, height))
    self.sprite_sheet = sprite_sheet
    if self.sprite_sheet:
      self.sprite, moving_frames = graphics.get_frames(ASSET_FOLDER + sprite_sheet, 9, 8, des_width=width, des_height=height)
    else:
      self.sprite = None
    self.animation_frames = {'moving': moving_frames, 'hasdata': [pygame.Rect(0, 0, self.rect.width, self.rect.height)]}
    self.current_animation = 'moving'
    self.current_cycle = cycle(self.animation_frames[self.current_animation])
    self.current_frame = next(self.current_cycle)
    self.animation_time = 10
    self.animation_timer = 0
    self.data = None
    self.direction = 1
    self.moving = False
    self.mash_left = 0
    self.mash_right = 0
    self.interact_dist = PLAYER_INTERACT_DIST  # The max distance needed for the player to interact with something
    self.trapped = False
    self.mash_left = False
    self.mash_right = False
    self.escape_hit = 0
    self.message_str = "hello"

  def jump(self):
    if not self.trapped:
      self.velocity.y = JUMP_VELOCITY

  def update(self):
    """set velocity to be moved by the physics engine"""
    if self.moving and not self.trapped:
      self.velocity.x = self.direction * PLAYER_SPEED

  def escape(self, direction):
    """mash a button to escape students"""
    if self.trapped:
      print("trying to escape")
      if direction == 1:
        self.mash_left = True
      elif direction == 2:
        self.mash_right = True
      if self.mash_left and self.mash_right:
        self.mash_left = False
        self.mash_right = False
        self.escape_hit += 1
      if self.escape_hit > PLAYER_MASH_NUMBER:
        if self.trapper.rect.x < self.rect.x:
          # on the left, push back to the left
          self.trapper.velocity.x = -50
          self.trapper.velocity.y = -20
        else:
          self.trapper.velocity.x = 50
          self.trapper.velocity.y = -20
        self.trapped = False
        self.trapper.stun()
        self.trapper = None
        self.mash_left = False
        self.mash_right = False
        self.escape_hit = 0

  def move_right(self):
    """DEPRICATED: use move(1): sets velocity of player to move right"""
    self.move(1)

  def move_left(self):
    """DEPRICATED use move(-1): sets velocity of player to move left"""
    self.move(-1)

  def move(self, direction):
    """sets move to the direction passed in"""
    self.direction = direction
    self.moving = True

  def stop_right(self):
    """sets velocity to 0"""
    if self.direction == 1:
      self.velocity.x = 0
      self.moving = False

  # TODO: why have two methods for stop
  def stop_left(self):
    """sets velocity to 0"""
    if self.direction == -1:
      self.velocity.x = 0
      self.moving = False

  def interact(self, game_objs):
    """a catch all function that called when hitting the interact button. It will
    look through the game_objs and if it's with a minumum threshold(self.interact_dist), call specific functions
    based on what the objects are.
    :param game_objs: A list of game objects that the player can potentially interact
    with
    :type game_objs: list of GameObject"""
    for game_obj in game_objs:
      if isinstance(game_obj, DataDevice):
        if eng.distance(self.rect, game_obj.rect) < self.interact_dist:
          game_obj.start_data_spawn()

  def draw(self, surface):
    """Draws the player object onto surface
    :param surface: the surface to draw the object, typically the window
    :type surface: pygame.Surface"""
    super().draw(surface)
    if self.sprite:
      surface.blit(self.sprite, self.rect, area=self.current_frame)
    else:
      # Player is a black rectangle if there is no sprite sheet.
      pygame.draw.rect(surface, (0, 0, 0), self.rect)

  def change_animation(self, frame):
    """change the frames that player object is currently cycling through.
    :param frame: a key that maps to a list of animation frames in self.animation_frames
    :type frame: str"""
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
    :type axis: String """
    if type(obj) == Data:
      if self.data is None:
        self.data = obj
        self.data.hide_object()
        # obj.rect.x, obj.rect.y = -100, -100  # TODO: have better way than move off screen
        self.change_animation('hasdata')
    else:
      super().respond_to_collision(obj, axis)
      if isinstance(obj, Follower) and not self.trapped:
        self.trapped = True
        self.trapper = obj
        print('hit')


  def throw_data(self):
    """Through the data that the player is holding"""
    if self.data:
      if self.moving:
        exit_buff = PLAYER_SPEED  # if the player is moving, have to throw the data ahead a frame
      else:
        exit_buff = 0
      if self.direction == -1:
        self.data.rect.right = self.rect.left + (exit_buff * self.direction)
      else:
        self.data.rect.left = self.rect.right + (exit_buff * self.direction)

      self.data.velocity.x = (self.velocity.x + PLAYER_THROW_SPEED.x) * self.direction
      self.data.rect.y = self.rect.y
      self.data.velocity.y = PLAYER_THROW_SPEED.y
      self.data.unhide_object()
      self.data = None
      self.change_animation('moving')


class DataDevice(SimpleScenery, Constructor):
  """Devices that are scenery, but output data when interacted with"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet='Green.png', obj_id=None, game=None):
    super().__init__(startx, starty, width, height, color, obj_id=obj_id, sprite_sheet=sprite_sheet)
    Constructor.__init__(self, game)
    self.timer = None
    self.color = color
    self.data = None
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet
    if self.sprite_sheet:
      self.sprite, self.frames = graphics.get_frames(ASSET_FOLDER + self.sprite_sheet, 1, 1, des_width=width, des_height=height)
    else:
      self.sprite = None
    self.current_frame = self.frames[0]

  def build_packet(self, accumulator):
    packet = {'type': 'data_device', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id,
              'timer': self.timer, 'message': self.message_str}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.timer = packet['timer']
    self.message_str = packet['message']
    self.render = True

  def generate_data(self):
    game_obj = Data(20, 20, 10, 10)
    print(game_obj)
    game_obj.rect.centerx = self.rect.centerx
    game_obj.rect.bottom = self.rect.top
    game_obj.velocity.y = random.randint(EJECT_SPEED.y, EJECT_SPEED.y/2 )
    game_obj.velocity.x = random.randint(-EJECT_SPEED.x, EJECT_SPEED.x)
    self.add_to_world(game_obj)
    return game_obj

  def start_data_spawn(self, timer=DATA_DEVICE_TIMER):
    if not self.timer:  # only allow one timer at a time
      self.timer = timer


  def draw(self, surface):
    super().draw(surface)
    if self.sprite:
      surface.blit(self.sprite, self.rect, area=self.current_frame)
    else:
      pygame.draw.rect(surface, self.color, self.rect)
    if self.timer:
      outline_rect = pygame.Rect(0, 0, TIMER_WIDTH, 20)
      outline_rect.centerx = self.rect.centerx
      outline_rect.centery = self.rect.y - outline_rect.height
      timer_rect = pygame.Rect(outline_rect)
      timer_rect.width = TIMER_WIDTH * self.timer
      pygame.draw.rect(surface, (255, 0, 255), timer_rect)
      pygame.draw.rect(surface, (128, 0, 128), outline_rect, 1)

  def update(self):
    if self.timer:
      self.timer += DATA_DEVICE_TIMER
      if self.timer >= 1:
        self.generate_data()
        self.timer = None

  def respond_to_collision(self, obj, axis=None):
    return

  def get_data(self, data):
    self.timer = DATA_DEVICE_TIMER  # start timer
    self.data = data
    # TODO: Make a better hide/delete function
    data.rect.x, data.rect.y = (-100, -100)
    data.velocity.x = 0
    data.velocity.y = 0

class DataCruncher(DataDevice):
  """Second stage of collecting data"""
  def __init__(self, startx, starty, width, height, sprite_sheet, accept_stage=1, amount_data_needed=3, obj_id=None, game=None):    
    super().__init__(startx, starty, width, height, sprite_sheet=sprite_sheet, obj_id=obj_id, game=None)
    Constructor.__init__(self, game)
    self.accept_stage = accept_stage
    self.amount_data_needed = amount_data_needed
    self.data_collected = 0

  def handle_data(self, game_obj):    
    self.data_collected += 1
    if self.data_collected == self.amount_data_needed:
      self.timer = DATA_DEVICE_TIMER  # start timer
      self.message_str = None
    else:
      self.message_str = str(self.data_collected) + "/" + str(self.amount_data_needed)
    # TODO: THis is wrong, need a destructor 
    self.data = game_obj
    self.data.advance_data()
    # TODO: Make a better hide/delete function
    self.data.hide_object()

  def update(self):
    if self.timer:
      self.timer += DATA_DEVICE_TIMER
      if self.timer >= 1:
        self.generate_data()
        self.timer = None

  def generate_data(self):
    # ipdb.set_trace()
    self.data.rect.centerx = self.rect.centerx
    self.data.rect.bottom = self.rect.top
    self.data.velocity.y = random.randint(EJECT_SPEED.y, EJECT_SPEED.y/2 )
    self.data.velocity.x = random.randint(-EJECT_SPEED.x, EJECT_SPEED.x)
    self.data.unhide_object()
    # self.add_to_world(self.data)


class Data(MovableGameObject):
  def __init__(self, startx, starty, width, height, color=None, sprite_sheet='light_blue.png', obj_id=None):
    super().__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    self.sprite_sheet = sprite_sheet
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet
    if self.sprite_sheet:
      self.sprite, self.frames = graphics.get_frames(ASSET_FOLDER + self.sprite_sheet, 1, 1, des_width=width, des_height=height)
    else:
      self.sprite = None
    self.current_frame = self.frames[0]
    self.sprite2, self.frames2 = graphics.get_frames(ASSET_FOLDER + 'green.png', 1, 1, des_width=width, des_height=height)
    self.frame_idx = 1
    self.stage = 1  # 1 = raw data. 2 = crunched data, 3 i = paper

  def draw(self, surface):
    super().draw(surface)
    if self.sprite_sheet:
      if self.frame_idx == 1:
        surface.blit(self.sprite, self.rect, area=self.current_frame)
      elif self.frame_idx == 2:
        surface.blit(self.sprite2, self.rect, area=self.current_frame)
    else:
      pygame.draw.rect(surface, (155, 0, 0), self.rect)

  def build_packet(self, accumulator):
    packet = {'type': 'data', 'location': [self.rect.x, self.rect.y], 'frame': self.frame_idx, 'id': self.id}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.frame_idx = packet['frame']
    self.render = True

  def respond_to_collision(self, obj, axis=None):
    if isinstance(obj, Player):
      obj.respond_to_collision(self)
    elif isinstance(obj, DataCruncher) and self.stage == obj.accept_stage:
      obj.handle_data(self)
    else:
      # TODO: this makes the data go through players
      super().respond_to_collision(obj, axis)

  def advance_data(self):
    # TODO: hacked for now with no sprite sheet
    self.frame_idx += 1
    self.stage += 1


class Follower(MovableGameObject):
  """a class that follows it's leader"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None, site_range=200):
    super().__init__(startx, starty, width, height, obj_id=obj_id)
    self.color = color
    self.leader = None
    self.velocity = eng.Vector(0, 0)
    self.site = site_range
    self.stunned = False
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet
    if self.sprite_sheet:
      self.sprite, self.frames = graphics.get_frames(ASSET_FOLDER + self.sprite_sheet, 1, 1, des_width=width, des_height=height)
    else:
      self.sprite = None
    self.current_frame = self.frames[0]

  def update(self):
    if self.leader and eng.distance(self.rect, self.leader.rect) < self.site and not self.stunned:
      # figure out which direction to move
      if self.leader.rect.centerx - self.rect.centerx > 0:
        self.velocity.x = FOLLOWER_SPEED  # move right
      elif self.leader.rect.centerx - self.rect.centerx < 0:
        self.velocity.x = -FOLLOWER_SPEED  # move left
      else:
        self.velocity.x = 0
    elif self.leader:
      self.leader = None
      self.velocity.x = 0
    # self.rect.centerx += self.velocity.x

  def check_for_leader(self, leader_list):
    self.leader = None
    closest_leader = leader_list[0]
    closest_distance = eng.distance(self.rect, closest_leader.rect)
    for potential_leader in leader_list[1:]:
      distance = eng.distance(self.rect, potential_leader.rect)
      if distance < closest_distance:
        closest_leader = potential_leader
        closest_distance = distance
    if closest_distance < self.site:
      self.leader = closest_leader

  def draw(self, surface):
    super().draw(surface)
    if self.sprite:
      surface.blit(self.sprite, self.rect, area=self.current_frame)
    else:
      pygame.draw.rect(surface, self.color, self.rect)

  # TODO: move this to MoveableGameObject
  def build_packet(self, accumulator):
    packet = {'type': 'data', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id}
    accumulator.append(packet)

  def read_packet(self, packet):
    self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
    self.render = True

  def respond_to_collision(self, obj, axis=None):
    self.stunned = False
    if isinstance(obj, Player):
      obj.respond_to_collision(self, axis)
    super().respond_to_collision(obj, axis)

  def stun(self):
    self.stunned = True


class Patroller(Follower):
  """class that patrols it's give x area"""

  def __init__(self, startx, starty, width, height, sprite_sheet=None, obj_id=None, patrol_range=100, site_range=200):
    super().__init__(startx, starty, width, height, obj_id=obj_id, sprite_sheet=sprite_sheet, site_range=site_range)
    self.patrol_range = patrol_range
    self.reset_patrol()
    self.direction = 1 # scaler to multiple speed by to get direction
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet
    if self.sprite_sheet:
      self.sprite, self.frames = graphics.get_frames(ASSET_FOLDER + self.sprite_sheet, 1, 1, des_width=width, des_height=height)
    else:
      self.sprite = None
    self.current_frame = self.frames[0]

  def update(self):
    if self.leader:
      super().update()
      if not self.leader:
        # leader moved out of range, set new start and end patrol to start from the middle
        self.reset_patrol()
        self.do_patrol()
    else:
      self.do_patrol()

  def do_patrol(self):
    # self.rect.centerx += self.velocity.x
    if self.velocity.x > 0 and self.rect.centerx > self.end_patrol:
      self.direction = -1
      # self.velocity.x = -PATROL_SPEED
    if self.velocity.x < 0  and self.rect.centerx < self.start_patrol:
      # self.velocity.x = PATROL_SPEED
      self.direction = 1
    self.velocity.x = PATROL_SPEED * self.direction

  def reset_patrol(self):
    """sets the partrol to be equidistance from the current center"""
    self.start_patrol = self.rect.centerx - self.patrol_range/2
    self.end_patrol = self.rect.centerx + self.patrol_range/2
    self.velocity.x = PATROL_SPEED

