import json

GRAVITY_VELOCITY = 1

class VelocityStruct(object):
    """A simple struct to hold velocities"""
    def __init__(self, dx, dy):
        super(VelocityStruct, self).__init__()
        self.dx = dx
        self.dy = dy


class Engine(object):
  """A game engine that handles managing physics and game related"""
  def __init__(self):
    super(Engine, self).__init__()
  
  def parse_json(self, file):

    json_data = open(file)
    data = json.load(json_data)

    if '__terrain__' in data:
      return data['floors']

  def physics_simulation(self, moving_objects, static_objects):
    """The worlds most bestest physics simulation. Updates moving_objects with
    there velocities and checks if there is an collision with the static_objects
    objects.
    :param moving_objects: list of game objects that could be in motion
    :type moving_objects: list of objects with a pygame rect and velocity
    :param static_objects: list of game objects that don't move. Things like Scenery
    :type static_objects: list of objects with a pygame rect and velocity
    """
    for game_object in moving_objects:
      game_object.rect.x += game_object.velocity.dx
      # TODO: either be smarter here or when you pass in the static objects
      for wall in static_objects:
        if game_object.rect.colliderect(wall.rect):
          # check which direction we have collided from
          if game_object.velocity.dx > 0:
            game_object.rect.right = wall.rect.left
          else:
            game_object.rect.left = wall.rect.right
           
      game_object.rect.y += game_object.velocity.dy
      game_object.velocity.dy += GRAVITY_VELOCITY
      for wall in static_objects:
        if game_object.rect.colliderect(wall.rect):
          # check which direction we have collided from
          if game_object.velocity.dy > 0:
            game_object.rect.bottom = wall.rect.top
          else:
            game_object.rect.top = wall.rect.bottom



