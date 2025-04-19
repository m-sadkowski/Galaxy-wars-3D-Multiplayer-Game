from sprite_object import *
from npc import *

class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_list = []
        self.npc_list = []
        self.static_sprite_path = 'resources/static_sprites/'
        self.anim_sprite_path = 'resources/animated_sprites/'
        self.npc_sprite_path = 'resources/npc/'
        self.enemy_sprite = None
        add_sprite = self.add_sprite
        add_npc = self.add_npc

        """
        # sprite map
        add_sprite(SpriteObject(game, pos=(1.5, 5.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 3.5)))
        add_sprite(AnimatedSprite(game, pos=(1.5, 6.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'rocket/0.png', pos=(1.5, 4.5)))
        add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + 'rocket/0.png', pos=(1.5, 7.5)))

        # npc map
        add_npc(NPC(game))
        """

    def update(self):
        [sprite.update() for sprite in self.sprite_list]
        [npc.update() for npc in self.npc_list]

    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)

    def add_npc(self, npc):
        self.npc_list.append(npc)

    def add_enemy(self, enemy_sprite):
        self.enemy_sprite = enemy_sprite
        self.npc_list.append(enemy_sprite)