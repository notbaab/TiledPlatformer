import json

GRAVITY_VELOCITY = 1


class Vector(object):
  def __init__(self, x, y):
    super(Vector, self).__init__()
    self.x = x
    self.y = y

  def add(self, vector):
    self.x += vector.x
    self.y += vector.y

  def subtract(self, vector):
    self.x -= vector.x
    self.y -= vector.y

  def toTuple(self):
    return self.x, self.y

  def copy(self):
    return Vector(self.x, self.y)


class Engine(object):
  """A game engine that handles managing physics and game related"""

  def __init__(self):
    super(Engine, self).__init__()

  def parse_json(self, file):
    json_data = open(file)
    data = json.load(json_data)
    # TODO: do more fancy things
    return data
    # if '__terrain__' in data:
    # return data['floors']

  def loop_over_game_dict(self, func, *args):
    """looop over the given game dictionary and apply function, with the game_obj as
      the first argument, followed by the other arguments with the arguments to
      all objects"""
    for obj_type, obj_list in self.game_objects.items():
      for game_obj in obj_list:
        func(game_obj, *args)

  def get_locations(self, game_obj):
    """returns a tuple with the game object locations, best used with the """
    return game_obj.rect.x, game_obj.rect.y

  def physics_simulation(self, moving_objects, static_objects):
    """The worlds most bestest physics simulation. Updates moving_objects with
        there velocities and checks if there is an collision with the static_objects
        objects.
        :param moving_objects: list of game objects that could be in motion
        :type moving_objects: list of objects with a pygame rect and velocity
        :param static_objects: list of game objects that don't move. Things like Scenery
        :type static_objects: list of objects with a pygame rect and velocity
        """
    # simulate
    for game_object in moving_objects:
      game_object.rect.x += game_object.velocity.x
      # TODO: either be smarter here or when you pass in the static objects
      for wall in static_objects:
        if game_object.rect.colliderect(wall.rect):
          # check which direction we have collided from
          if game_object.velocity.x > 0:
            game_object.rect.right = wall.rect.left
          else:
            game_object.rect.left = wall.rect.right
          game_object.velocity.x = 0

      game_object.rect.y += game_object.velocity.y
      game_object.velocity.y += GRAVITY_VELOCITY
      for wall in static_objects:
        if game_object.rect.colliderect(wall.rect):
          # check which direction we have collided from
          if game_object.velocity.y > 0:
            game_object.rect.bottom = wall.rect.top
          else:
            game_object.rect.top = wall.rect.bottom
          game_object.velocity.y = 0




