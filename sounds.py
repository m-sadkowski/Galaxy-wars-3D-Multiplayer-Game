import pygame as pg

class Sounds:
    def __init__(self, game):
        self.game = game
        pg.mixer.init()
        self.path = 'resources/sounds/'
        self.turret = pg.mixer.Sound(self.path + 'turret.wav')