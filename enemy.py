from ready.sprite_object import *
import math


class EnemySprite(AnimatedSprite):
    def __init__(self, game, path='resources/enemy/0.png', pos=(0, 0), scale=0.6, shift=0.38, animation_time=1000):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.damage_images = self.get_images(self.path + '/damage')
        self.walk_images = self.get_images(self.path + '/walk')
        self.shot_animation_time = 0

        self.health = 100
        self.alive = True
        self.damage = False
        self.shot = False
        self.ray_cast_value = False
        self.frame_counter = 0

    def update(self):
        self.check_animation_time()
        self.get_sprite()

        if self.alive:
            self.ray_cast_value = self.ray_cast_player()
            self.check_hit_in_player()

            if self.shot:
                self.animate(self.attack_images)
            elif self.damage:
                if self.animation_trigger:
                    self.damage = False
                self.animate(self.damage_images)
            else:
                self.animate(self.walk_images)
        else:
            self.animate(self.death_images)

    def check_hit_in_player(self):
        if self.ray_cast_value and self.game.player.shot:
            if HALF_WIDTH - self.sprite_half_width < self.screen_x < HALF_WIDTH + self.sprite_half_width:
                self.game.sounds.damage_sound.play()
                self.game.player.shot = False
                self.damage = True
                self.frame_counter = 0
                self.health -= 50
                try:
                    self.game.client.send_hit_notification()
                except Exception as e:
                    print(f"Failed to send hit notification: {e}")

    def ray_cast_player(self):
        if self.game.player.map_pos == self.map_pos:
            return True

        wall_dist_v, wall_dist_h = 0, 0
        player_dist_v, player_dist_h = 0, 0

        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        ray_angle = self.theta

        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # verticals
        x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

        depth_vert = (x_vert - ox) / cos_a
        y_vert = oy + depth_vert * sin_a

        delta_depth = dx / cos_a
        dy = delta_depth * sin_a

        for i in range(MAX_DEPTH):
            tile_vert = int(x_vert), int(y_vert)
            if tile_vert == self.map_pos:
                player_dist_v = depth_vert
                break
            if tile_vert in self.game.map.world_map:
                wall_dist_v = depth_vert
                break
            x_vert += dx
            y_vert += dy
            depth_vert += delta_depth

        # horizontals
        y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

        depth_hor = (y_hor - oy) / sin_a
        x_hor = ox + depth_hor * cos_a

        delta_depth = dy / sin_a
        dx = delta_depth * cos_a

        for i in range(MAX_DEPTH):
            tile_hor = int(x_hor), int(y_hor)
            if tile_hor == self.map_pos:
                player_dist_h = depth_hor
                break
            if tile_hor in self.game.map.world_map:
                wall_dist_h = depth_hor
                break
            x_hor += dx
            y_hor += dy
            depth_hor += delta_depth

        player_dist = max(player_dist_v, player_dist_h)
        wall_dist = max(wall_dist_v, wall_dist_h)

        if 0 < player_dist < wall_dist or not wall_dist:
            return True
        return False

    @property
    def map_pos(self):
        return int(self.x), int(self.y)