import pygame

class spriteSheet:
	def __init__(self, filename):
		self.sheet = pygame.image.load(filename)
	def getSprite(self, rect):
		sprite = pygame.Surface(rect.size)
		sprite.blit(self.sheet, (0, 0), area = rect)
		return sprite
