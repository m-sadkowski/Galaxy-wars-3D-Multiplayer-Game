import pygame as pg

class Sounds:
    def __init__(self, game):
        self.game = game
        pg.mixer.init()
        self.path = 'resources/sounds/'
        self.turret = pg.mixer.Sound(self.path + 'turret.wav')
        self.npc_damage = pg.mixer.Sound(self.path + 'npc_damage.wav')
        self.npc_death = pg.mixer.Sound(self.path + 'npc_damage.wav')