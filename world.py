import pygame
import engine as eng
# from graphics import *
from itertools import cycle
import ipdb
import random

DATA_STAGES = {"raw": 1, "crunched": 2, "paper": 3}
ASSET_FOLDER = "assets/"
GRAVITY_VELOCITY = 4  # lets cheat for now
FLOOR_Y = 580
PLAYER_SPEED = 50
PLAYER_THROW_SPEED = eng.Vector(20, -5)
FOLLOWER_SPEED = PLAYER_SPEED - 3  # just slower than the players
PATROL_SPEED = 4  # just slower than the players
JUMP_VELOCITY = -40
DATA_DEVICE_TIMER = 120
TIMER_WIDTH = 100
PLAYER_INTERACT_DIST = 50
EJECT_SPEED = eng.Vector(20, -20)
PLAYER_MASH_NUMBER = 10  # the number of times the player has to mash a button to escape
MEETING_EVENT_HORIZON = 100  # the distance where the player will need to escape
MEETING_GRAVITAIONAL_SPHERE = 150  # the distance where the player begins to be pulled in
MEETING_PULL = 5
MEETING_TIMER = .01
DEBUG = True
STUN_VELOCITY_LOSER = eng.Vector(30, -20)
STUN_VELOCITY_WINNER = eng.Vector(10, -10)
STUN_WINNER_TIMER = 10
STUN_LOSER_TIMER = 20
LEFT_FRAME_ID = 'l_'
LADDER_CLIMB_SPEED = eng.Vector(0, 30)
MAGIC_STAIR_CONSTANT = 2  # DO NOT TOUCH, THIS IS MAGIC


def extract_dict(obj_dict):
  """
  get the width, height, x and y from a json dict

  :param obj_dict: A dictionary containing rect data
  :type obj_dict: dict
  """
  x = int(obj_dict.get('x'))
  y = int(obj_dict.get('y'))
  width = int(obj_dict.get('width'))
  height = int(obj_dict.get('height'))
  return x, y, width, height


# TODO: add more things to do
class GameObject(object):

  id = 0

  def __init__(self, startx, starty, width, height, obj_id=None):
    """
    The top level game object. All game objects inherit from this class.
        Creates a game object with at least a Pygame rect and other attributes that are needed
        by all game object types
    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (sometimes not used in the child object, specifically sprite objects)
    :type width: int
    :param height: height of the object (sometimes not used in the child object, specifically sprite objects)
    :type height: int
    :param obj_id: a specified id, useful for making an object on the client side with the same id
    :type obj_id: int
    """
    self.rect = pygame.Rect((startx, starty, width, height))
    if not obj_id:
      self.id = GameObject.id  # assign
      GameObject.id += 1
    else:
      self.id = obj_id
    self.render = True
    self.to_del = False
    self.physics = False  # Does this class need physics? i.e. movement
    self.collision = True  # Does this class need collisions
    self.dirt_sprite = True  # only draw sprite if dirty

  def update(self):
    """Called every frame. Put behavior that the object needs to do every frame"""
    return


class NetworkedObject(object):

  def __init__(self, attribute_list):
    """
    An object that builds and reads packets. Packets are in the form of dictionaries with the 
        attribute as the key. Packets are NOT binary strings but python dicts, the serialization 
        of the objects is handled at a lower level. 
    :param attribute_list: the list of attributes that the object wants to send in the build packet methods
    :type attribute_list: list[str]
    """
    self.attribute_list = attribute_list
    self.send_data = True

  def build_packet(self, accumulator):
    """
    Builds the packet if send data is true. 

    :param accumulator: the running list to add this packet too. 
    :type accumulator: list[dict]
    """
    if self.send_data:
      packet = {}
      for attribute in self.attribute_list:
        packet[attribute] = self.__getattribute__(attribute)
      accumulator.append(packet)

  def read_packet(self, packet):
    """
    Reads the packet and updates this objects attributes. 

    :param packet: a packet containing the updated attributes
    :type packet: dict
    """
    for attribute in self.attribute_list:
      self.__setattr__(attribute, packet[attribute])


class AnimateSpriteObject(object):

  def __init__(self, animation_dict, start_animation='idle', convert_alpha=True):
    """
    A stand alone object that allows the inherited game object to have animation sprites
        Initilize all the frames of the animated sprite object

    :param animation_dict: a dictionary that is keyed on the name of the animation. The dictionary 
      contains a tuple pair, with the name of the file at [0] and the number of frames of the sprite sheet
      at [1][0] for the x and [1][1] for the y. So animation_dict[animation_name] -> (sprite_sheet_filename, 
      (sprite_sheet_x, sprite_sheet_y) 
    :type animation_dict: dict
    """
    object.__init__(self)
    frame_dict = {}
    self.animation_frames = {}
    self.sprite_sheets = {}
    # not to self, don't ever unpack a tuple like this again
    for animation_name, (filename, (width, height), vertical_offset, (frame_width, frame_height)) in animation_dict.items():
      self.sprite_sheets[animation_name], self.animation_frames[animation_name] = self._get_frames(
        ASSET_FOLDER + filename, int(width),
        int(height), vertical_offset=int(vertical_offset),frame_width=int(frame_width), 
        frame_height=int(frame_height), convert_alpha=convert_alpha)

      # get the left facing sprite
      left_animation = LEFT_FRAME_ID + animation_name
      self.sprite_sheets[left_animation] = pygame.transform.flip(self.sprite_sheets[animation_name], 1, 0)
      self.animation_frames[left_animation] = self.animation_frames[animation_name][::-1]

    self.current_animation = start_animation
    self.current_cycle = cycle(self.animation_frames[self.current_animation])
    self.current_frame = next(self.current_cycle)
    self.animation_time = 3
    self.animation_timer = 0
    self.pause = False  # set to true for animations where the end should be held (like falling)
    self.pause_frame = None

  def pause_animation(self):
    """Pauses the current animation by setting it's pause attribute true"""
    self.pause = True

  def stop_pause_animation(self):
    """
    Unsets pause. Yes I know this isn't java and a getter and setter are dumb but I forgot why I 
        did this so I'm just leaving it here cause I am not coding anymore on this project merely 
        documenting it and crying as I see my mistakes and mishaps. 
    """
    self.pause = False

  def reset_current_animation(self):
    """
    Resets the current animation to the start
    """
    self.change_animation(self.current_animation)

  def change_animation(self, frame):
    """
    change the frames that player object is currently cycling through.

    :param frame: a key that maps to a list of animation frames in self.animation_frames
    :type frame: str
    """
    if not frame in self.animation_frames:
      frame = 'idle'

    previous_rect = self.rect.copy()
    self.current_animation = frame  # TODO: evaluate if we need this member
    self.current_cycle = cycle(self.animation_frames[self.current_animation])
    self.rect = self.animation_frames[self.current_animation][0].copy()
    self.rect.centerx = previous_rect.centerx
    self.rect.bottom = previous_rect.bottom

  def reverse_animation(self, direction):
    """
    take the current animation and point it in the other direction specified
        returns new animation name the object needs to change to or None
    """
    is_left = True if LEFT_FRAME_ID in self.current_animation else False
    new_animation = None
    if direction == -1 and not is_left:
      # moving right, but trying to flip to the left
      new_animation = LEFT_FRAME_ID + self.current_animation
    elif direction == 1 and is_left:
      # moving left, but trying to flip right
      new_animation = self.current_animation[len(LEFT_FRAME_ID):]
    return new_animation

  def animate(self):
    """
    Updates the animation timer goes to next frame in current animation cycle
        after the alloted animation time has passed.
    """
    if not self.pause:
      self.animation_timer += 1
      if self.animation_timer == self.animation_time:
        self.current_frame = next(self.current_cycle)
        self.animation_timer = 0

  def draw(self, surface):
    """Draws the player object onto surface
    :param surface: the surface to draw the object, typically the window
    :type surface: pygame.Surface"""
    surface.blit(self.sprite_sheets[self.current_animation], self.rect, area=self.current_frame)

  def _get_frames(self, filename, columns, rows,vertical_offset=None, frame_width=None, 
                  frame_height=None, convert_alpha=True):
    """
    Returns a new sprite sheet and a list of rectangular coordinates in the
      file that correspond to frames in the file name. It also manipulates the spritesheet 
      so each frame will have the des_width and des_height
    :param filename: sprite sheet file
    :type filename: str
    :param columns: the number of columns in the sprite sheet
    :type columns: int
    :param rows: the number of rows in the sprite sheet
    :type rows: int
    :param vertical_offset: how far down to crop out the frames
    :type frame_width: int
    :param frame_width: the native width of a single frame
    :type frame_width: int
    :param frame_height: the native width of a single frame
    :type frame_height: int
    """
    # OLD code cause rick insisted on using actual sizes but was a neat bit of code for resizing 
    # sprite sheets dynamically so I can't part with it
    # if convert_alpha:
    #   sheet = pygame.image.load(filename).convert_alpha()
    # else:
    #   sheet = pygame.image.load(filename).convert()
    # sheet_rect = sheet.get_rect()
    # sheet_width = columns * des_width
    # sheet_height = rows * des_height

    # sheet = pygame.transform.smoothscale(sheet, (sheet_width, sheet_height))
    # sheet_rect = sheet.get_rect()
    # for x in range(0, sheet_rect.width, des_width):
    #  for y in range(0, sheet_rect.height, des_height):
    #    frames.append(pygame.Rect(x, y, des_width, des_height))
    # Note: des_width and des_height are ignored, assuming sprites are at
    # correct size already.

    if convert_alpha:
      sheet = pygame.image.load(filename).convert_alpha()
    else:
      sheet = pygame.image.load(filename).convert()
    sheet_rect = sheet.get_rect()
    full_frame_width = sheet_rect.width / columns
    left_offset = int((full_frame_width - frame_width) / 2)
    full_frame_height = sheet_rect.height / rows

    frames = []
    for x in range(0, columns):
      # next for loop assumes vertical_offset is less than frame height
      for y in range(0, rows):
        frames.append(pygame.Rect(x * full_frame_width + left_offset,
                                  y * full_frame_height + vertical_offset, frame_width, frame_height))
    return sheet, frames


class Constructor(object):

  def __init__(self, game):
    """
    A special object that contains a reference to the entire game. Inherited
        by classes that need to construct objects in the game world

    :param game: an instance of a game object
    :type game: MasterPlatformer
    """
    object.__init__(self)
    self.game = game

  def add_to_world(self, obj):
    """
    Adds the object to the games added list. Note, the game object needs an added list attribute

    :param obj: a game object to be added to the game world
    :type obj: GameObject
    """
    if self.game:
      self.game.added.append(obj)
    else:
      ipdb.set_trace()


class MovableGameObject(GameObject):

  def __init__(self, startx, starty, width, height, obj_id=None):
    """
    Any game object that moves can. 

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (sometimes not used in the child object, specifically sprite objects)
    :type width: int
    :param height: height of the object (sometimes not used in the child object, specifically sprite objects)
    :type height: int
    :param obj_id: a specified id, useful for making an object on the client side with the same id
    :type obj_id: int
    """
    super(MovableGameObject, self).__init__(startx, starty, width, height, obj_id=obj_id)
    self.velocity = eng.Vector(0, 0)
    self.physics = True  # most movable game objects need physics
    self.last_rect = self.rect.copy()
    self.on_ground = True

  def move(self, velocity):
    """
    sets the objects velocity. Movement is handled by the physics engine

    :param velocity: the velocity vector along the x and they y axis
    :type velocity: Vector
    """
    self.velocity = velocity

  def stop(self):
    """Sets the objects velocity to 0"""
    self.velocity = eng.Vector(0, 0)

  def hide_object(self):
    """Hides the object and turns off physics"""
    self.render = False
    self.physics = False
    self.rect.x, self.rect.y = -1000, -1000  # move somewhere far off screen to

  def unhide_object(self):
    """
    Unhides object by turning on phyics and rendering. Function calling will need to 
        move the object into view though.
    """
    self.render = True
    self.physics = True

  def respond_to_collision(self, obj, axis=None):
    """
    Contains the callback for the collision between a move able object and the
        object passed in. If the object passed in is the environment (i.e. SimpleScenery)
        it will treate the environment as a wall and stop the object.
    :param obj: object player is colliding with
    :type obj: GameObject
    :param axis: which axis was the player moving along.
    :type axis: str 
    """
    if isinstance(obj, BackGroundScenery):
      if axis == 'y':
        self._handle_background_collision(obj)
      return
    if axis == 'x':
      if self.velocity.x > 0:
        self.rect.right = obj.rect.left
      if self.velocity.x < 0:
        self.rect.left = obj.rect.right
      self.velocity.x = 0
    if axis == 'y':
      if self.velocity.y > 0:
        self.rect.bottom = obj.rect.top
        self.on_ground = True
      if self.velocity.y < 0:
        self.rect.top = obj.rect.bottom
      self.velocity.y = 0

  def _handle_background_collision(self, obj):
    """
    collisions with things that are in the background i.e. things you can
        jump on but walk through
    """
    if self.velocity.y >= 0 and self.last_rect.bottom <= obj.rect.top:
      # only collide going down (rember +y = down)
      self.rect.bottom = obj.rect.top
      self.velocity.y = 0  # stop the object
      self.on_ground = True

  def update(self):
    """Update the last rect attribute and checks if the object is no longer on the ground"""
    self.last_rect = self.rect.copy()
    if self.velocity.y != 0:
      # no longer on ground 
      self.on_ground = False


class BackGroundScenery(GameObject):
  """
  objects that you can jump on top of but can run through. Think of them as
      in the background that the player jumps up on. For example a platform in mario. 
      TODO: This is should really just be incorporated as an attribute of simple 
      scenery as the backgroundness of the object comes from other objects checking
      if it's a BackGroundScenery type.  
  """

  def draw(self, surface):
    pygame.draw.rect(surface, (128, 0, 128), self.rect, 3)

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: BackGroundScenery
    """
    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, width, height, obj_id=obj_id) 


class SimpleScenery(GameObject):
  """
  Simple SimpleScenery object. Game objects that are just simple shapes, don't 
      move and can't have objects pass through them.
      TODO: Why does this and BackGroundScenery exist? It seems like it's just
      to allow other objects to check for this type in collision, maybe it would 
      be better served as an attribute in gameobject?
  """

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: SimpleScenery
    """
    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, width, height, obj_id=obj_id) 


class Player(AnimateSpriteObject, MovableGameObject, NetworkedObject):
  def __init__(self, startx, starty, width, height, sprite_sheet=None, obj_id=None, team='blue'):
    """
    The object that that the user controls. 

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    :param sprites_heet: the spritesheet dict of the object
    :type sprite_sheet: dict
    :param obj_id: a specified id, useful for making an object on the client side with the same id
    :type obj_id: int
    """

    MovableGameObject.__init__(self, startx, starty, width, height, obj_id=obj_id)
    AnimateSpriteObject.__init__(self, sprite_sheet)
    NetworkedObject.__init__(self, ['rect', 'current_frame', 'current_animation', 'id', 'render'])
    self.rect = self.animation_frames[self.current_animation][0].copy()
    self.sprite_sheet = sprite_sheet
    self.data = None
    self.direction = 1
    self.moving = False
    self.mash_left = 0
    self.mash_right = 0
    self.interact_dist = PLAYER_INTERACT_DIST  # The max distance needed for the player to interact with something
    self.trapped = False
    self.trapper = None  # Object trapping the player
    self.mash_left = False
    self.mash_right = False
    self.escape_hit = 0
    self.score = 0
    self.movement_event = False  # set to true if another object is mucking with the players velocity
    self.escape_mash_number = PLAYER_MASH_NUMBER
    self.stunned_timer = 0
    self.stunned_velocity = eng.Vector(0, 0)
    self.invincible_timer = 0
    self.invincible = False
    self.jumping = False
    self.on_ladder = False
    self.near_ladder = False
    self.climbing = 0  # climbing modifier 1 for DOWN, -1 for up
    self.team = team

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: Player
    """
    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    team = obj_dict.get('team')
    sprite_sheet = obj_dict.get('sprite_sheet')
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, 1, 1, sprite_sheet=sprite_sheet, obj_id=obj_id, team=team) 


  def jump(self):
    """Sets the player y velocity up"""
    if not self.trapped and not self.stunned_timer and self.on_ground:
      self.jumping = True
      self.velocity.y = JUMP_VELOCITY

  def up_interact(self, climable_objects):
    """
    Player pressed up so may be attempting to climb something. Checks the objects
        to see if any objects are close enough to climb

    :param climable_objects: a list of objects that the player can climb
    :type climable_objects: list[ClimableObject]
    """
    if self.on_ladder:
      self.climbing = -1
      return
    for game_obj in climable_objects:
      # Check if the center of the player is inbwteen the left and right coordinates
      if self.rect.colliderect(game_obj.rect):
        # if (game_obj.rect.left < self.rect.centerx < game_obj.rect.right and
        # game_obj.rect.top < self.rect.centery < game_obj.rect.bottom):
        # On ladder, turn off physics
        self.physics = False
        self.on_ladder = True
        self.climbing = -1
        self.ladder = game_obj
        self.rect.centerx = self.ladder.rect.centerx
        break

  def down_interact(self, climable_objects):
    """
    Player pressed up so may be attempting to climb something. Checks the objects
        to see if any objects are close enough to climb

    :param climable_objects: a list of objects that the player can climb
    :type climable_objects: list[ClimableObject]

    """
    # ipdb.set_trace()
    if self.on_ladder:
      self.climbing = 1
      return
    for game_obj in climable_objects:
      # Check if the center of the player is inbwteen the left and right coordinates
      if (game_obj.rect.left < self.rect.centerx < game_obj.rect.right and
            (game_obj.rect.top < self.rect.bottom < game_obj.rect.bottom or
                 game_obj.rect.top == self.rect.bottom)):
        # On ladder, turn off physics
        self.physics = False
        self.on_ladder = True
        self.climbing = 1
        self.ladder = game_obj
        self.rect.centerx = self.ladder.rect.centerx
        break

  def do_door(self, door):
    """
    Do door like things, like go to the doors end_point

    :param door: the doo the player is walking through
    :type door: Door
    """
    self.rect.x = door.end_point[0]
    self.rect.y = door.end_point[1]

  def cancel_up_down_interact(self):
    """stop climbing"""
    self.climbing = 0

  def update(self):
    """set velocity to be moved by the physics engine"""
    MovableGameObject.update(self)
    if self.stunned_timer:
      self.stunned_timer -= 1
      # self.velocity.x = self.stunned_velocity.x
    elif not self.movement_event and self.moving and not self.trapped:
      self.velocity.x = self.direction * PLAYER_SPEED
    if self.jumping:  # do things that involve jumping
      self.jumping = False
    if self.invincible_timer:
      self.invincible_timer -= 1
    else:
      self.invincible = False
    if self.climbing:
      self.handle_ladddery_things()
      # self.rect.y += self.ladder.climb_speed.y

  def escape(self, direction):
    """
    mash a button to escape students or meetings. An escape hit is only added when
        the player hits both left and right. 

    :param direction: The direction the player is pressing.
    :type direction: int

    """
    if self.trapped:
      if direction == 1:
        self.mash_left = True
      elif direction == 2:
        self.mash_right = True
      if self.mash_left and self.mash_right:
        self.mash_left = False
        self.mash_right = False
        self.escape_hit += 1
      if self.escape_hit > self.escape_mash_number:
        self.trapper.un_trap(self)
        self.trapper = None
        self.trapped = False
        self.mash_left = False
        self.mash_right = False
        self.escape_hit = 0
        self.invincible_timer = 60
        self.invincible = True

  def move_right(self):
    """DEPRICATED: use move(1): sets velocity of player to move right"""
    self.move(1)

  def move_left(self):
    """DEPRICATED use move(-1): sets velocity of player to move left"""
    self.move(-1)

  def move(self, direction):
    """
    Sets move to the direction passed in.

    :param direction: the direction to move the player. -1  for left, 1 for right
    :type direction: int
    """
    if self.on_ladder:
      self._turn_physics_on()  # cancel being on ladder so we can move
    self.direction = direction
    self.moving = True
    self.change_animation('moving')
    new_animation = self.reverse_animation(direction)  # change animation frame if need be
    if new_animation:
      self.change_animation(new_animation)

  def stop_right(self):
    """sets velocity to 0"""
    if self.direction == 1:
      self.velocity.x = 0
      self.moving = False
      self.change_animation('idle')

  # TODO: why have two methods for stop
  def stop_left(self):
    """sets velocity to 0"""
    if self.direction == -1:
      self.velocity.x = 0
      self.moving = False
      self.change_animation('idle')

  def read_packet(self, packet):
    """
    Same as the NetworkedObject read packet but a little more work to change the 
        animation
    :param packet: the packet containing updated information for the player
    :type packet: dict
    """
    if packet['current_animation'] != self.current_frame:
      self.change_animation(packet['current_animation'])
    super(Player, self).read_packet(packet)

  def interact(self, game_objs):
    """
    a catch all function that called when hitting the interact button. It will
        look through the game_objs and if it's with a minimum threshold(self.interact_dist), call specific functions
        based on what the objects are.
    :param game_objs: A list of game objects that the player can potentially interact with
    :type game_objs: list of GameObject
    """
    if self.data:
      throw_data = True
    else:
      throw_data = False
    interact_obj = None
    for game_obj in game_objs:
      if isinstance(game_obj, DataDevice):
        if self.rect.colliderect(game_obj.rect):
          interact_obj = game_obj

    if not interact_obj and throw_data:
      self.throw_data()
    elif isinstance(interact_obj, DataCruncher) and self.data:
      interact_obj.interact(self)
    elif isinstance(interact_obj, DataDevice) and self.data:
      self.throw_data()
    elif isinstance(interact_obj, DataDevice) and not self.data:
      interact_obj.interact(self)

  def handle_ladddery_things(self):
    """do laddery things like climb up and down"""
    self.rect.y += (self.ladder.climb_speed.y * self.climbing)
    if self.rect.bottom <= self.ladder.top:  # hit the top
      self.last_rect = self.rect.copy()
      self.last_rect.bottom = self.ladder.top - 1  # this is the most hacked thing I've ever done ever
      # at the top
      self.rect.bottom = self.ladder.top
      self._turn_physics_on()
    elif self.rect.bottom >= self.ladder.bottom:
      self.rect.bottom = self.ladder.bottom
      self._turn_physics_on()

  def _turn_physics_on(self):
    """turn the player physics on"""
    self.physics = True
    self.on_ladder = False
    self.climbing = False

  def draw(self, surface):
    """
    Draws the player object onto surface

    :param surface: the surface to draw the object, typically the window
    :type surface: pygame.Surface
    """
    AnimateSpriteObject.draw(self, surface)


  def respond_to_collision(self, obj, axis=None):
    """
    Contains the callback for the collision between a player object and a game object passed in. Axis is needed
        for collisions that halt movement

    :param obj: object player is colliding with
    :type obj: GameObject
    :param axis: which axis was the player moving along.
    :type axis: str 
    """
    if type(obj) == Data:
      if self.data is None and obj.team == self.team:
        self.data = obj
        self.data.hide_object()
        self.change_animation('hasdata')
        self.data.player = self
    elif type(obj) == Door:
      self.do_door(obj)
    else:
      if self.on_ladder and type(obj) == SimpleScenery:
        if type(obj) != SimpleScenery:
          super(Player, self).respond_to_collision(obj, axis)
      else:
        super(Player, self).respond_to_collision(obj, axis)
      if isinstance(obj, Player) and not self.stunned_timer:
        self.joust_attack(obj)
      if (isinstance(obj, Meeting) or isinstance(obj, Follower)) and not self.trapped:
        # got sucked trapped by something
        obj.trap(self)

  def joust_attack(self, other_player):
    """The player collided with another, determine who 'won' and properly stun the player"""
    if self.rect.centery < other_player.rect.centery:
      dominate_player = self
      losing_player = other_player
    elif self.rect.centery > other_player.rect.centery:
      dominate_player = other_player
      losing_player = self
    else:
      return  # are currently on the same plane
    # figure out which way the dominate player bumped into the loser were going
    if dominate_player.rect.centerx > losing_player.rect.centerx:
      # hit right side of loser, push to the left
      losing_player.velocity.x = -STUN_VELOCITY_LOSER.x
      dominate_player.velocity.x = STUN_VELOCITY_WINNER.x
    elif dominate_player.rect.centerx < losing_player.rect.centerx:
      losing_player.velocity.x = STUN_VELOCITY_LOSER.x
      dominate_player.velocity.x = -STUN_VELOCITY_WINNER.x
    else:
      # on top of the other player, pick one at random
      modifier = random.randint(0, 1) * 2 - 1
      losing_player.velocity.x = STUN_VELOCITY_LOSER.x * modifier
      dominate_player.velocity.x = STUN_VELOCITY_WINNER.x * -modifier

    losing_player.stunned_timer = STUN_LOSER_TIMER
    dominate_player.stunned_timer = STUN_WINNER_TIMER
    dominate_player.velocity.y = STUN_VELOCITY_WINNER.y
    losing_player.velocity.y = STUN_VELOCITY_LOSER.y
    if losing_player.data:
      losing_player.drop_data()

  def drop_data(self):
    """drop the data by calling the throw data funciton."""
    self.throw_data()

  def throw_data(self):
    """Through the data that the player is holding"""
    # ipdb.set_trace()
    if self.data:
      if self.moving:
        exit_buff = PLAYER_SPEED  # if the player is moving, have to throw the data ahead a frame
      else:
        exit_buff = 20
      if self.direction == -1:
        self.data.rect.right = self.rect.left + (exit_buff * self.direction)
      else:
        self.data.rect.left = self.rect.right + (exit_buff * self.direction)

      self.data.velocity.x = self.velocity.x + PLAYER_THROW_SPEED.x * self.direction
      self.data.rect.y = self.rect.y
      self.data.velocity.y = PLAYER_THROW_SPEED.y
      self.data.unhide_object()
      self.data = None


class DataDevice(BackGroundScenery, Constructor, NetworkedObject):

  def __init__(self, startx, starty, width, height, obj_id=None, game=None):
    """
    Devices that are scenery, but output data when interacted with. The inte

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object 
    :type width: int
    :param height: height of the object 
    :type height: int
    :param obj_id: a specified id, useful for making an object on the client side with the same id
    :type obj_id: int
    """
    BackGroundScenery.__init__(self, startx, starty, width, height, obj_id=obj_id)
    Constructor.__init__(self, game)
    NetworkedObject.__init__(self, ['rect', 'id'])
    self.active_timer = None
    self.timer_count = 0
    self.data = None
    self.collision = False  # for now, only interaction comes with explicit buttons

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: SimpleScenery
    """
    startx, starty, width, height = extract_dict(obj_dict)
    game = obj_dict.get('game')
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    tmp = self(startx, starty, width, height, obj_id=obj_id, game=game) 
    effect_json = obj_dict.get('effect_json')
    if 'rawdata' in obj_dict:
      tmp.load_data(obj_dict['rawdata'], effect_json)
    if effect_json:
      timer_blue, timer_red = tmp.load_effects(obj_dict['timer'], effect_json,
                                               obj_dict['timer-red-pos'], obj_dict['timer-blue-pos'])
      return [tmp, timer_red, timer_blue]
    else:
      return tmp


  def generate_data(self):
    """Create a data object and eject it """
    if self.active_timer == self.blue_timer:
      game_obj = Data(20, 20, 40, 40, self.data_dict_blue, team='blue')
    else:
      game_obj = Data(20, 20, 40, 40, self.data_dict_red, team='red')
    game_obj.rect.center = self.active_timer.rect.center
    game_obj.velocity.y = random.randint(EJECT_SPEED.y, EJECT_SPEED.y / 2)
    game_obj.velocity.x = random.randint(-EJECT_SPEED.x, EJECT_SPEED.x)
    self.add_to_world(game_obj)
    return game_obj

  def interact(self, player):
    """
    Called when a player is trying to start a timer on this object. 

    :param player: the player that is trying to start a timer
    :type player: Player
    """
    if not self.active_timer:  # only allow one timer at a time
      if player.team == 'blue':
        self.active_timer = self.blue_timer
      else:
        self.active_timer = self.red_timer
      self.timer_count = 0
      self.active_timer.reset_current_animation()
      self.active_timer.render = True
      self.active_timer.pause = False
      self.active_timer.send_data = True
      self.active_timer.clear = False

  def load_effects(self, effect_name, effect_dict, red_loc=(0,0), blue_loc=(0,0)):
    """
    Load the effects for this data object. Effects are stored
        as the red and blue timer.

    :param effect_name: the name of the timer to load
    :type effect_name: str
    :param effect_dict: the dict containing all the effect information. 
    :type effect_dict: dict
    :param red_loc: the location to place the red timer
    :type red_loc: tuple
    :param blue_loc: the location to place the blue timer
    :type blue_loc: tuple
    :returns: the blue and red timer objects
    :rtype: Effect
    """
    self.red_timer = self.__load_effect(effect_name, effect_dict, 'Red', red_loc)
    self.blue_timer = self.__load_effect(effect_name, effect_dict, 'Blue', blue_loc)
    self.timer_total = self.red_timer.animation_time * len(
                       self.red_timer.animation_frames[self.red_timer.current_animation]) + self.red_timer.animation_time
    return self.blue_timer, self.red_timer

  def __load_effect(self, effect_name, effect_dict, team, location):
    """Loads effects based on the team passed in."""
    animation_dict = effect_dict[effect_name + '-' + team]
    effect = Effect(self.rect.x + int(location[0]), self.rect.y - int(location[1]), 200,
                    200, animation_dict)
    effect.physics = False
    effect.collision = False
    effect.animation_time = DATA_DEVICE_TIMER / len(effect.animation_frames[effect.current_animation])
    return effect

  def load_data(self, data_name, data_json):
    """
    Stores the data_dict that is needed later to create a data object after a timer expires

    :param data_name: the name of the data object, used as a key in data json + teamname
    :type data_name: str
    :param data_json: the dict containing all the sprite information of the data objects
    :type data_json: dict
    """
    self.data_dict_blue = data_json[data_name + '-Blue']
    self.data_dict_red = data_json[data_name + '-Red']

  def draw(self, surface):
    """should never be called, but just in case, set render to false so it wouldn't be called"""
    self.render = False  # nothing to draw. Should never be called but just a safefy net

  def update(self):
    """
    Checks if a timer is running and ticks down if that is the case. Genereates data 
        once the timer runs down

    :returns: Whether or not the the timer finished and created more data
    :rtype: bool
    """
    if self.active_timer:
      self.timer_count += 1
      if self.timer_count >= self.timer_total:
        self.generate_data()
        self.active_timer.render = False
        self.active_timer.reset_current_animation()
        self.active_timer.pause_animation()
        self.active_timer.clear = True
        self.active_timer = None
        self.timer_count = 0
        return True  # tell the sub classes that the timer is done
    return False

class DataCruncher(DataDevice):
  ACCEPT_STAGE = 1
  def __init__(self, startx, starty, width, height, obj_id=None, game=None):
    """
    Second stage of collecting data. Works like a data device in terms of timer 
        creation but doesn't create data, only advances it.

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    :param obj_id: the id of the object
    :type obj_id: int
    :param game: An instance of a game to be used for adding data to the game world
    :type game: int

    """
    super(DataCruncher, self).__init__(startx, starty, width, height, obj_id=obj_id, game=game)
    self.player = None
    self.collision = True  # for now, only interaction comes with explicit buttons

  def generate_data(self):
    """Advances and ejects the data"""
    self.data.rect.centerx = self.rect.centerx
    self.data.rect.bottom = self.rect.top
    self.data.velocity.y = random.randint(EJECT_SPEED.y, EJECT_SPEED.y / 2)
    self.data.velocity.x = random.randint(-EJECT_SPEED.x, EJECT_SPEED.x)
    self.data.advance_data()
    self.data.unhide_object()
    self.data = None

  def interact(self, player):
    """
    Starts a timer if the player has data and its the correct stage

    :param player: the player interacting with the object
    :type player: Player
    """
    return self._interact(player, DataCruncher.ACCEPT_STAGE)

  def _interact(self, player, accept_stage):
    """Starts a timer if the data is at the accept_stage"""
    if (not self.player and player.data and player.data.stage == accept_stage and 
        not self.active_timer):
      super(DataCruncher, self).interact(player)
      self.player = player
      self.data = self.player.data
      self.player.data = None
      return True
    return False


class Desk(DataCruncher):
  """Where the player will sit and write the paper after collecting data"""
  ACCEPT_STAGE = 2

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: SimpleScenery
    """

    obj_list = super(Desk, self).create_from_dict(obj_dict)
    if 'chair' in obj_dict:
      class_obj = obj_list[0]  # the first object is the 'main' object
      class_obj.player_sit_loc = (class_obj.rect.x + int(obj_dict['chair'][0]), class_obj.rect.y + int(obj_dict['chair'][1]))
    return obj_list

  def update(self):
    """Update the timer and release the player if the timer is up"""
    if super(Desk, self).update():
      self.player.trapped = False
      self.player = None
    if self.player:
      self.player.escape_hit = 0  # keep them trapped!!!
      self.player.trapped = True

  def interact(self, player):
    """
    Starts a timer and traps the player. It's a desk, you gotta sit down to use it!

    :param player: the player interacting with the desk
    :type player: Player
    """
    if super(Desk, self)._interact(player, Desk.ACCEPT_STAGE):
      self.player.trapped = True
      self.player.escape_hit = 0
      self.move_player(player)

  def move_player(self, player):
    """move the player to the sitting locaiton"""
    player.rect.x, player.rect.y = self.player_sit_loc


class PublishingHouse(DataCruncher):
  """Where the player brings the final paper and scores a point"""
  ACCEPT_STAGE = 3

  def generate_data(self):
    """score a point"""
    if self.scoring_team == 'blue':
      self.game.blue_score += 1
    else:
      self.game.red_score += 1
    print("red's score " + str(self.game.red_score))
    print("blue's score " + str(self.game.blue_score))

  def interact(self, player):
    """A player is trying to score a paper"""
    if super(PublishingHouse, self)._interact(player, PublishingHouse.ACCEPT_STAGE):
      self.scoring_team = player.team


class Data(AnimateSpriteObject, MovableGameObject, NetworkedObject):

  def __init__(self, startx, starty, width, height, sprite_sheet, team=None, obj_id=None):
    """
    Data is an objects that the player is trying to gather and analyze


    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    :param sprites_heet: the spritesheet dict of the object
    :type sprite_sheet: dict
    :param team: the team that data is associated with
    :type team: str
    :param obj_id: a specified id, useful for making an object on the client side with the same id
    :type obj_id: int
    """
    MovableGameObject.__init__(self, startx, starty, width, height, obj_id=obj_id)
    AnimateSpriteObject.__init__(self, sprite_sheet, convert_alpha=False)
    NetworkedObject.__init__(self, ['rect', 'current_frame', 'id', 'current_animation', 'render', 'stage'])
    self.rect = self.animation_frames[self.current_animation][0].copy()
    self.sprite_sheet = sprite_sheet
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet
    self.stage = 1
    self.frame = 'idle'
    self.player = None
    self.team = team

  def respond_to_collision(self, obj, axis=None):
    """
    A data object behaves normally with collision except when it encounters a 
        player object

    :param obj: object data is colliding with
    :type obj: GameObject
    :param axis: which axis was the data moving along.
    :type axis: str 
    """
    if isinstance(obj, Player):
      if obj.team == self.team:
        obj.respond_to_collision(self)
    else:
      # TODO: this makes the data go through players
      super(Data, self).respond_to_collision(obj, axis)

  def advance_data(self):
    """Move the data to the next stage and change it's animation"""    
    self.stage += 1
    self.frame = str(self.stage)
    self.change_animation(str(self.stage))


class Follower(AnimateSpriteObject, MovableGameObject, NetworkedObject):
  """a class that follows it's leader"""

  def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None, site_range=200):
    MovableGameObject.__init__(self, startx, starty, width, height, obj_id=obj_id)
    AnimateSpriteObject.__init__(self, sprite_sheet)
    NetworkedObject.__init__(self, ['rect', 'current_frame', 'id', 'render'])
    self.color = color
    self.leader = None
    self.velocity = eng.Vector(0, 0)
    self.site = site_range
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet

  def trap(self, game_obj):
    if not game_obj.invincible:
      game_obj.trapped = True
      game_obj.trapper = self

  def update(self):
    MovableGameObject.update(self)
    if self.leader and eng.distance(self.rect, self.leader.rect) < self.site:
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

  def check_for_leader(self, leader_list):
    self.leader = None
    closest_leader = leader_list[0]
    closest_distance = eng.distance(self.rect, closest_leader.rect)
    for potential_leader in leader_list[1:]:
      distance = eng.distance(self.rect, potential_leader.rect)
      if distance < closest_distance and (not potential_leader.trapped or potential_leader.trapper == self):
        closest_leader = potential_leader
        closest_distance = distance
    if closest_distance < self.site and (not closest_leader.trapped or potential_leader.trapper == self):
      self.leader = closest_leader

  def respond_to_collision(self, obj, axis=None):
    if isinstance(obj, Player):
      obj.respond_to_collision(self, axis)
    super(Follower, self).respond_to_collision(obj, axis)

  def un_trap(self, game_obj):
    """Called after a player has escaped the patrollers grasp"""
    if self.rect.x < game_obj.rect.x:
      # on the left, push back to the left
      self.velocity.x = -10
      self.velocity.y = -20
    else:
      self.velocity.x = 10
      self.velocity.y = -20


class Patroller(Follower):
  """class that patrols it's give x area"""

  def __init__(self, startx, starty, width, height, sprite_sheet=None, obj_id=None, patrol_range=100, site_range=200):
    super(Patroller, self).__init__(startx, starty, width, height, obj_id=obj_id, sprite_sheet=sprite_sheet,
                                    site_range=site_range)
    self.patrol_range = patrol_range
    self.reset_patrol()
    self.direction = 1  # scaler to multiple speed by to get direction
    # TODO: Since we are just giving primitives but want to treat them as a sprite, we have to get creative
    self.sprite_sheet = sprite_sheet

  def update(self):
    if self.leader:
      super(Patroller, self).update()
      if not self.leader:
        # leader moved out of range, set new start and end patrol to start from the middle
        self.reset_patrol()
        self.do_patrol()
    else:
      self.do_patrol()

  def do_patrol(self):
    if self.velocity.x > 0 and self.rect.centerx > self.end_patrol:
      self.direction = -1
    if self.velocity.x < 0 and self.rect.centerx < self.start_patrol:
      self.direction = 1
    self.velocity.x = PATROL_SPEED * self.direction

  def reset_patrol(self):
    """sets the partrol to be equidistance from the current center"""
    self.start_patrol = self.rect.centerx - self.patrol_range / 2
    self.end_patrol = self.rect.centerx + self.patrol_range / 2
    self.velocity.x = PATROL_SPEED


class Meeting(GameObject):
  """A meeting trap that will pull the players into at a certain range"""

  def __init__(self, startx, starty, width, height, obj_id=None):
    """
    A meeting object traps a player object when they get close enough

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    """
    GameObject.__init__(self, startx, starty, width, height, obj_id=obj_id)
    self.pulling_player = None
    self.timer = None
    self.collision = False

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: SimpleScenery
    """

    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, width, height, obj_id=obj_id) 

  def check_player(self, players):
    """check if the player is close enough to be pulled in"""
    if self.timer:
      # cooling down
      return

    for player in players:
      distance = eng.distance(self.rect, player.rect)

      if eng.distance(self.rect, player.rect) < MEETING_GRAVITAIONAL_SPHERE:
        player.movement_event = True  # inform the player that the meeting is in control now!!
        # ipdb.set_trace()
        self.pull_event(player)
      else:
        player.movement_event = False

  def pull_event(self, player, **kwargs):
    """a function to give the player"""
    # distance = kwargs['distance']
    if player.trapped:
      player.change_animation('sitmeeting')  # HACK
      return
    distance = eng.distance(self.rect, player.rect)
    if self.rect.x >= player.rect.centerx:
      # on the right side of it, pull to the right
      if not player.moving or distance < MEETING_EVENT_HORIZON:
        pull_velocity = MEETING_PULL
      else:
        pull_velocity = player.direction * PLAYER_SPEED + MEETING_PULL
    elif self.rect.x < player.rect.centerx:
      # on the left side of it, pull to the left
      if not player.moving or distance < MEETING_EVENT_HORIZON:
        pull_velocity = -MEETING_PULL
      else:
        pull_velocity = player.direction * PLAYER_SPEED - MEETING_PULL
    if distance < MEETING_EVENT_HORIZON:
      self.trap(player)
    player.velocity.x = pull_velocity

  def un_trap(self, game_obj):
    """Release the mortal from the bonds of responsibility"""
    self.timer = MEETING_TIMER
    game_obj.movement_event = False
    game_obj.change_animation('running')

  def trap(self, game_obj):
    """
    Trap the game object if their is no timer

    :param game_obj: the game object to trap
    :type game_obj: Player
    """
    if not self.timer:
      game_obj.trapped = True
      game_obj.trapper = self
      game_obj.change_animation('sitmeeting')

  def update(self):
    """Tick down cooldown timer if active"""
    super(Meeting, self).update()
    if self.timer:
      self.timer += MEETING_TIMER
      if self.timer >= 1:
        self.timer = None


class ClimableObject(BackGroundScenery):

  def __init__(self, startx, starty, width, height, obj_id=None):
    """
    Simple ladder object. The player can climb up and down it


    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    """
    BackGroundScenery.__init__(self, startx, starty, width, height, obj_id=obj_id)
    self.top = self.rect.top
    self.bottom = self.rect.bottom
    self.climb_speed = LADDER_CLIMB_SPEED

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: SimpleScenery
    """
    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, width, height, obj_id=obj_id) 


class Stairs(GameObject):
  def __init__(self, startx, starty, width, height, obj_id=None):
    """
    A wrapper that makes a step objects from the bottom to the top of the object


    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    """
    GameObject.__init__(self, startx, starty, width, height, obj_id=obj_id)
    self.collision = False


  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: SimpleScenery
    """

    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    stairs = self(startx, starty, width, height, obj_id=obj_id) 
    steps = stairs.make_stairs(obj_dict['dir'])

    return [stairs] + steps

  def make_stairs(self, orientation):
    """
    make step objects from the bottom to the top of this object in the orientation
        passed in. The steps will be equally spaced from each other

    :param orientation: the direction to make the stairs
    :type orientation: str
    """
    if orientation == 'right':
      bottom = self.rect.left, self.rect.bottom
      top = self.rect.right, self.rect.top
      direct = 1
    else:
      bottom = self.rect.right, self.rect.bottom
      top = self.rect.left, self.rect.top
      direct = -1
    return self.__make_steps(12, bottom, top, direct)

  def __make_steps(self, num_of_steps, bottom, top, direct, width=102, height=36):
    """Makes the step objects and returns them"""
    self.steps = []
    total_height = bottom[1] - top[1]
    height_space = total_height / num_of_steps
    height_padding = height_space - height
    total_width = abs(bottom[0] - top[0])
    width_padding = total_width / num_of_steps
    # ipdb.set_trace()
    for x in range(0, num_of_steps):
      if direct == -1:
        startx = bottom[0] - x * width_padding
      else:
        startx = x * width_padding + (bottom[0])

      if startx != bottom[0]:
        startx -= MAGIC_STAIR_CONSTANT
      starty = bottom[1] - ((x + 1) * height + (x + 1) * height_padding)
      self.steps.append(Step(startx, starty, width, height))
      if direct == -1:
        self.steps[-1].rect.right = startx
    return self.steps

class Step(BackGroundScenery):
  def __init__(self, startx, starty, width, height, obj_id=None):
    """
    A simple block spanning the rect passed in

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param height: height of the object (ignored)
    :type height: int
    """
    BackGroundScenery.__init__(self, startx, starty, width, height)

class Effect(AnimateSpriteObject, NetworkedObject, GameObject):

  def __init__(self, startx, starty, width, height, sprite_sheet=None, obj_id=None, total_time=120,
               animation_time=None):
    """
    Effect objects. Just a simple object that doesn't interact with anything,
        its just a sprite that gets sent over the network and is told to stop or start

    :param startx: the starting x position of the object
    :type startx: int
    :param starty: the starting y position of the object
    :type starty: int
    :param width: width of the object (ignored)
    :type width: int
    :param sprite_sheet: the dict containing the spritesheet information
    :type sprite_sheet: dict
    :param height: height of the object (ignored)
    :type height: int
    """
    GameObject.__init__(self, startx, starty, width, height)
    AnimateSpriteObject.__init__(self, sprite_sheet)
    NetworkedObject.__init__(self, ['rect', 'current_frame', 'current_animation', 'id', 'render', 'clear'])
    self.sprite_sheet = sprite_sheet
    # total time is in frames cause I'm bad at time.
    if not animation_time:
      self.animation_time = total_time / len(self.animation_frames[self.current_animation])
    else:
      self.animation_time = animation_time
    self.render = False
    self.pause_animation()
    self.render_frames = 0
    self.clear = True
    self.collision = False
    self.physics = False

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: Effect
    """
    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    sprite_sheet = obj_dict.get('sprite_sheet')
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, width, height, sprite_sheet=sprite_sheet, obj_id=obj_id) 


  def animate(self):
    """
    Updates the animation timer goes to next frame in current animation cycle
        after the alloted animation time has passed.
    """
    if not self.pause:
      self.animation_timer += 1
      self.render = False
      self.send_data = False
      if self.animation_timer == self.animation_time:
        self.current_frame = next(self.current_cycle)
        self.animation_timer = 0
        self.render = True
        self.send_data = True
    else:
      self.send_data = False

  def build_packet(self, accumulator):
    if self.send_data:
      if self.render:
        super(Effect, self).build_packet(accumulator)
      elif self.clear:
        super(Effect, self).build_packet(accumulator)
        self.clear = False

  def read_packet(self, packet):
    for attribute in self.attribute_list:
      self.__setattr__(attribute, packet[attribute])
    if self.clear:
      self.render = True

  def draw(self, surface, game):
    """Draws the player object onto surface
    :param surface: the surface to draw the object, typically the window
    :type surface: pygame.Surface"""
    if self.clear:
      surface.blit(game.background, (self.rect.x, self.rect.y), self.rect)
      self.render = False
      self.clear = False
    else:
      surface.blit(game.background, (self.rect.x, self.rect.y), self.rect)
      surface.blit(self.sprite_sheets[self.current_animation], self.rect, area=self.current_frame)
    self.render = False


class Door(BackGroundScenery):

  def __init__(self, startx, starty, width, height, obj_id=None, end_point=None):
    """
    A door object has an end point that the player is tranported to when they walk
        through the door
    """
    # ipdb.set_trace()
    super(Door, self).__init__(startx, starty, width, height, obj_id=obj_id)
    if end_point:
      self.end_point = int(end_point[0]), int(end_point[1])

  @classmethod
  def create_from_dict(self, obj_dict):
    """
    Create an instance of this object from a dictionary

    :param obj_dict: dictionary containing various inital values needed to instantiate object
    :type obj_dict: dict
    :returns: an instance of this object
    :rtype: Door
    """

    startx = int(obj_dict.get('x'))
    starty = int(obj_dict.get('y'))
    width = int(obj_dict.get('width'))
    height = int(obj_dict.get('height'))
    end_point = obj_dict.get('end_point')
    obj_id = obj_dict.get('id') 
    obj_id = int(obj_id) if obj_id else None
    return self(startx, starty, width, height, obj_id=obj_id, end_point=end_point) 
