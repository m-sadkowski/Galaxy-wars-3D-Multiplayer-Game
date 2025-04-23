from sprite_object import *

class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_list = []
        self.enemy_list = []
        self.static_sprite_path = 'resources/static_sprites/'
        self.anim_sprite_path = 'resources/animated_sprites/'
        self.npc_sprite_path = 'resources/npc/'
        self.enemy_sprite = None
        add_sprite = self.add_sprite

        # sprite map
        add_sprite(SpriteObject(game, pos=(1.5, 5.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 3.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 6.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'rocket/0.png', pos=(1.5, 4.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'rocket/0.png', pos=(1.5, 7.5)))

    def update(self):
        [sprite.update() for sprite in self.sprite_list]
        [enemy.update() for enemy in self.enemy_list]

    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)

    def add_enemy(self, enemy_sprite):
        self.enemy_sprite = enemy_sprite
        self.enemy_list.append(enemy_sprite)