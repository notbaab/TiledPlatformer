import pygame


def get_frames(filename, columns, rows, des_width=30, des_height=30):
  """returns a new sprite sheet and a list of rectangular coordinates in the
  file that correspond to frames in the file name"""
  image = pygame.image.load(filename)
  print(image.get_rect())
  # find how big we should make the sprite sheet
  image_width = columns * des_width
  image_height = rows * des_height

  image = pygame.transform.smoothscale(image, (image_width, image_height))
  image_rect = image.get_rect()
  frames = []
  for x in range(0, image_rect.width, des_width):
    for y in range(0, image_rect.height, des_height):
      frames.append(pygame.Rect(x, y, des_width, des_height))
  return image, frames

  # [pygame.Rect(x, y, self.rect.width, self.rect.height) for x in range(0, self.rect.width * 9, self.rect.width) for y in range(0, self.rect.height * 8, self.rect.height) if not (y == 7 and x > 6)]
  # print(image.get_rect())
