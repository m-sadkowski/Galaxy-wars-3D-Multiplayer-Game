from sprite_object import *

class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_list = []
        self.item_sprites = {}
        self.static_sprite_path = 'resources/static_sprites/'
        self.anim_sprite_path = 'resources/animated_sprites/'
        self.npc_sprite_path = 'resources/npc/'
        self.enemy_sprite = None

    def update_map_items(self, items_data):
        to_remove = [id for id in self.item_sprites if id not in [item['id'] for item in items_data]]
        for id in to_remove:
            if id in self.item_sprites:
                self.sprite_list.remove(self.item_sprites[id])
                del self.item_sprites[id]

        for item in items_data:
            if item['id'] not in self.item_sprites:
                pos = (item['pos'][0], item['pos'][1])
                if item['type'] == 1:  # Rocket
                    sprite = AnimatedSprite(self.game,
                                            path=self.anim_sprite_path + 'rocket/0.png',
                                            pos=pos)
                elif item['type'] == 2:  # Repair kit
                    sprite = AnimatedSprite(self.game,
                                            path=self.anim_sprite_path + 'repair_kit/0.png',
                                            pos=pos)
                elif item['type'] == 3:  # Star
                    sprite = SpriteObject(self.game, pos=pos)
                self.item_sprites[item['id']] = sprite
                self.sprite_list.append(sprite)

    def update(self):
        [sprite.update() for sprite in self.sprite_list]
        self.enemy_sprite.update()

    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)

    def add_enemy(self, enemy_sprite):
        self.enemy_sprite = enemy_sprite