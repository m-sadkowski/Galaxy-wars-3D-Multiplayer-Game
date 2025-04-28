import pygame as pg

class Sounds:
    def __init__(self, game):
        self.game = game
        pg.mixer.init()
        self.path = 'resources/sounds/'
        self.shoot_sound = pg.mixer.Sound(self.path + 'turret.wav')
        self.damage_sound = pg.mixer.Sound(self.path + 'damage.wav')
        self.death_sound = pg.mixer.Sound(self.path + 'death.wav')