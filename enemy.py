from sprite_object import *


class EnemySprite(AnimatedSprite):
    def __init__(self, game, path='resources/enemy/0.png', pos=(0, 0), scale=0.6, shift=0.38, animation_time=1000):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.damage_images = self.get_images(self.path + '/damage')
        self.walk_images = self.get_images(self.path + '/walk')

    def update_position(self, pos, angle):
        self.x, self.y = pos
        self.theta = angle

    def update(self):
        super().update()
        self.animate(self.walk_images)