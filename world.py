import pygame
import engine as eng

GRAVITY_VELOCITY = 1  # lets cheat for now
FLOOR_Y = 580
PLAYER_SPEED = 10
JUMP_VELOCITY = -10


# TODO: add more things to do
class GameObject(object):
    """the top level game object. All game objects inherit from this class"""
    id = 0

    def __init__(self, obj_id=None):
        if not obj_id:
            self.id = GameObject.id  # assign
            GameObject.id += 1
        else:
            self.id = obj_id
        self.render = True

    def update(self):
        return

    def respond_to_y_collision(self, object):
        return

    def respond_to_x_collision(self, object):
        return

    def build_packet(self, packet):
        """accumulator function that will build the packet for each game object"""
        import ipdb
        ipdb.set_trace()


class MovableGameObject(GameObject):
    """any game object that moves"""

    def __init__(self, startx, starty, startvelocity, width, height, obj_id=None):
        super(MovableGameObject, self).__init__(obj_id)
        # print(self.render)
        self.velocity = startvelocity
        self.rect = pygame.Rect((startx, starty, width, height))

    def move(self, velocity):
        self.velocity = velocity


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
class Player(GameObject):
    def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
        super(Player, self).__init__(obj_id=obj_id)
        self.color = color
        self.velocity = eng.Vector(0, 0)
        self.sprite = sprite_sheet
        if not sprite_sheet:
            self.rect = pygame.Rect((startx, starty, width, height))
        else:
            # TODO: Add sprite sheet parsing to engine
            self.sprite = pygame.image.load(sprite_sheet).convert_alpha()
            self.rect = self.sprite.get_rect()

    def jump(self):
        self.velocity.y = JUMP_VELOCITY

    def move_left(self):
        self.velocity.x = -PLAYER_SPEED

    def move_right(self):
        self.velocity.x = PLAYER_SPEED

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
            pygame.draw.rect(surface, (255, 0, 0), self.rect)

    def change_sprite(self, image):
        # TODO: cycle through sprite sheet, not load another image
        self.sprite = pygame.image.load(image)

    def build_packet(self, accumulator):
        packet = {'type': 'player', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id}
        accumulator.append(packet)

    def read_packet(self, packet):
        self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
        self.render = True

    def respond_to_x_collision(self, obj):
        if type(obj) == SimpleScenery:
            if self.velocity.x > 0:
                self.rect.right = obj.rect.left
            if self.velocity.x < 0:
                self.rect.left = obj.rect.right
            self.velocity.x = 0

    def respond_to_y_collision(self, obj):
        if type(obj) == SimpleScenery:
            if self.velocity.y > 0:
                self.rect.bottom = obj.rect.top
            if self.velocity.y < 0:
                self.rect.top = obj.rect.bottom
            self.velocity.y = 0


class DataDevice(SimpleScenery):
    """Devices that are scenery, but output data when interacted with"""

    def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
        super(DataDevice, self).__init__(startx, starty, width, height, color, obj_id=obj_id)
        print(self.startx)

    def build_packet(self, accumulator):
        packet = {'type': 'data_device', 'location': [self.rect.x, self.rect.y], 'frame': '', 'id': self.id}
        accumulator.append(packet)

    def read_packet(self, packet):
        self.rect.x, self.rect.y = packet['location'][0], packet['location'][1]
        self.render = True


class Data(MovableGameObject):
    def __init__(self, startx, starty, width, height, color=None, sprite_sheet=None, obj_id=None):
        super(Data, self).__init__(startx, starty, eng.Vector(0, 0), width, height, obj_id=obj_id)
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

