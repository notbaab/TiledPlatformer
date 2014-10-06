import json
import math
import world as wd
import random
import pygame
import ipdb

GRAVITY_VELOCITY = 1


class Colors(object):
  """simple abstraction to have convenient color constants."""
  BLACK = (0, 0, 0)
  WHITE = (255, 255, 255)
  RED = (255, 0, 0)
  LRED = (128, 0, 0)
  GREEN = (0, 255, 0)
  LGREEN = (0, 128, 0)
  BLUE = (0, 0, 255)
  LBLUE = (0, 0, 128)
  AQUA = (0, 255, 255)


class Vector(object):
  def __init__(self, x, y):
    super().__init__()
    self.x = x
    self.y = y

  def add(self, vector):
    self.x += vector.x
    self.y += vector.y

  def subtract(self, vector):
    self.x -= vector.x
    self.y -= vector.y

  def to_tuple(self):
    return self.x, self.y

  def copy(self):
    return Vector(self.x, self.y)

  def distance(self, vector2):
    return math.sqrt((self.x - vector2.x) ** 2 + (self.y - vector2.y) ** 2)


def distance(rect1, rect2):
  return math.sqrt((rect1.centerx - rect2.centerx) ** 2 + (rect1.centery - rect2.centery) ** 2)


def distance_cart(cart1, cart2):
  return math.sqrt((cart1[0] - cart2[0]) ** 2 + (cart1[1] - cart2[1]) ** 2)


class Engine(object):
  """A game engine that handles managing physics and game related"""

  def __init__(self):
    super().__init__()

  def parse_json(self, file):
    json_data = open(file)
    data = json.load(json_data)
    # TODO: do more fancy things
    return data

  def loop_over_game_dict(self, game_objects, func, *args):
    """loop over nested (i.e game_objects[type] = list) game dictionary and apply function, with the game_obj as
      the first argument, followed by the other arguments with the arguments to
      all objects"""
    for obj_type, obj_list in game_objects.items():
      for game_obj in obj_list:
        func(game_obj, *args)

  def map_attribute_flat(self, game_objects, func_string, *args):
    """Maps the attribute (calls the attribute on each value) to list of GameObjects, with the 
    given arguments"""
    for game_obj in game_objects:
      func = getattr(game_obj, func_string)
      func(*args)

  def loop_over_game_dict_att(self, game_objects, func_string, *args):
    """Loops over a game dictionary and calls the passed in function on the game object. 
    The function must be an attribute of the game objects"""
    for obj_type, obj_list in game_objects.items():
      # TODO: replace with call to map flat
      for game_obj in obj_list:
        func = getattr(game_obj, func_string)
        func(*args)

  def slide_animation(self, game_obj, end_location):
    return

  def physics_simulation(self, objects, static_objects):
    """The worlds most bestest physics simulation. Updates objects with
        there velocities and checks if there is an collision with the static_objects
        objects.
        :param objects: list of game objects that could be in motion
        :type objects: list of objects with a pygame rect and velocity
        :param static_objects: list of game objects that don't move. Things like Scenery
        :type static_objects: list of objects with a pygame rect and velocity
        """
    # simulate
    for game_object in objects:
      if game_object in static_objects:
        continue
      game_object.rect.x += game_object.velocity.x

      for other_object in objects:
        if game_object == other_object:
          continue  # don't do things with itself
        if game_object.rect.colliderect(other_object.rect):
          game_object.respond_to_collision(other_object, 'x')

      game_object.rect.y += game_object.velocity.y
      game_object.velocity.y += GRAVITY_VELOCITY

      for other_object in objects:
        if game_object == other_object:
          continue  # don't do things with itself
        if game_object.rect.colliderect(other_object.rect):
          game_object.respond_to_collision(other_object, 'y')

  def load_animation(self, game_objects, clear_fun, window):
    # TODO: Add some randomness
    game_pieces = {}
    for game_obj in game_objects:
      game_pieces[game_obj] = self.split_sprite(game_obj, 8, 8)

    # move every object on screen out
    end_points = {}
    distance_to_move = {}
    step_dict = {}
    steps_total = 45

    print(game_pieces)
    for obj, list_pieces in game_pieces.items():
      step_dict[obj] = {}
      for i, (rect, area) in enumerate(list_pieces):
        start_pointx, start_pointy = random.randint(-500, 1200), random.randint(-2000, 0)
        # how much to change by
        dx, dy = (rect.x - start_pointx, rect.y - start_pointy)
        step_sizex, step_sizey = (dx / float(steps_total), dy / float(steps_total))
        step_dict[obj][i] = []
        for x in range(1, steps_total + 1):
          step_dict[obj][i].append((start_pointx + step_sizex * x, start_pointy + step_sizey * x))

        rect.x, rect.y = (start_pointx, start_pointy)

    for i in range(steps_total):
      # draw objects
      clear_fun()
      for game_obj, inner_step_dict in step_dict.items():
        for idx, (rect, area) in enumerate(game_pieces[game_obj]):
          window.blit(game_obj.sprite, rect, area=area)
          rect.x, rect.y = inner_step_dict[idx].pop(0)  # grap the new place

      pygame.display.flip()
      #ipdb.set_trace()
      FPS.tick(60)

  def split_sprite(self, game_obj, des_width_peices, des_height_peices):
    """split the sprite into various pieces"""
    width = int(math.ceil(game_obj.rect.width/des_width_peices))
    height = int(math.ceil(game_obj.rect.height/des_height_peices))
    split_peices = []
    for x in range(0, game_obj.rect.width, width):
      for y in range(0, game_obj.rect.height, height):
        rect = pygame.Rect(game_obj.rect.x + x, game_obj.rect.y + y, 0, 0)
        area = pygame.Rect(game_obj.current_frame.x + x, game_obj.current_frame.y + y, width, height)
        split_peices.append((rect, area))
        print("split_peices")
        print(split_peices[-1])
    return split_peices
