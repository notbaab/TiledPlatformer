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
        self.render = True

    def update(self):
        return


class MovableGameObject(GameObject):
    """any game object that moves"""

    def __init__(self, startx, starty, startvelocity, width, height):
        super(MovableGameObject, self).__init__()
        print(self.render)
        self.velocity = startvelocity
        self.rect = pygame.Rect((startx, starty, width, height))

    def move(self, velocity):
        self.velocity = velocity


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
    def __init__(self, startx, starty, color=None, sprite_sheet=None):
        super(Player, self).__init__()
        self.color = color
        self.velocity = eng.Vector(0, 0)
        self.sprite = sprite_sheet
        if not sprite_sheet:
            self.rect = pygame.Rect((startx, starty, 30, 30))
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


class DataDevice(SimpleScenery):
    """Devices that are scenery, but output data when interacted with"""

    def __init__(self, startx, starty, width, height, color, sprite=None):
        super(DataDevice, self).__init__(startx, starty, width, height, color)
        print(self.startx)


class Data(MovableGameObject):
    def __init__(self, startx, starty, width, height, sprite=None, color=None):
        super(Data, self).__init__(startx, starty, eng.Vector(0, 0), width, height)
        self.color = color
        self.sprite = sprite

    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, self.rect)
        else:
            pygame.draw.rect(surface, (155, 0, 0), self.rect)



    