import pygame


def get_frames(filename, columns, rows, des_width=30, des_height=30):
  """returns a new sprite sheet and a list of rectangular coordinates in the
  file that correspond to frames in the file name. It also manipulates the spritesheet 
  so each frame will have the des_width and des_height
  :param filename: sprite sheet file
  :type filename: str
  :param columns: the number of columns in the sprite sheet
  :type columns: int
  :param rows: the number of rows in the sprite sheet
  :type rows: int
  :param des_width: the desired width of a single frame
  :type des_width: int
  :param des_height: the desired height of a single frame
  :type des_height: int"""
  image = pygame.image.load(filename)
  image_width = columns * des_width
  image_height = rows * des_height

  image = pygame.transform.smoothscale(image, (image_width, image_height))
  image_rect = image.get_rect()
  frames = []
  for x in range(0, image_rect.width, des_width):
    for y in range(0, image_rect.height, des_height):
      frames.append(pygame.Rect(x, y, des_width, des_height))
  return image, frames
