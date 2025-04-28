from sprite_object import *
import pygame as pg
import math


class EnemySprite(AnimatedSprite):
    def __init__(self, game, path='resources/enemy/0.png', pos=(0, 0), scale=0.6, shift=0.38, animation_time=1000):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.damage_images = self.get_images(self.path + '/damage')
        self.walk_images = self.get_images(self.path + '/walk')

        self.health = 100
        self.alive = True
        self.pain = False
        self.pain_time = 0  # Track pain animation duration
        self.ray_cast_value = False
        self.frame_counter = 0
        self.player_search_trigger = False
        self.dying_trigger = False
        self.death_time = 0

    def update(self):
        self.check_animation_time()
        self.get_sprite()

        if self.alive:
            self.ray_cast_value = self.ray_cast_player_npc()
            self.check_hit_in_npc()

            if self.pain:
                # Odtwarzaj animację damage i sprawdź, czy osiągnęła ostatnią klatkę
                self.animate(self.damage_images)
                if self.frame_counter >= len(self.damage_images) - 1:  # Jeśli animacja się skończyła
                    self.pain = False
                    self.frame_counter = 0  # Resetuj licznik
            elif self.ray_cast_value:
                if not pg.mouse.get_pressed()[0]:
                    self.animate(self.idle_images)
                else:
                    self.animate(self.attack_images)
            else:
                self.animate(self.walk_images)
        else:
            if not self.dying_trigger:
                self.animate_death()
            else:
                self.animate(self.death_images)

    def animate(self, images):
        if self.animation_trigger:
            images.rotate(-1)
            self.image = images[0]
            self.frame_counter += 1  # Licznik klatek rośnie z każdym wywołaniem

    def animate_death(self):
        if not self.dying_trigger:
            self.dying_trigger = True
            self.animation_time_prev = pg.time.get_ticks()
            self.frame_counter = 0
        self.animate(self.death_images)
        if self.frame_counter == len(self.death_images) - 1:
            self.death_time = pg.time.get_ticks()

    def check_hit_in_npc(self):
        if self.ray_cast_value and self.game.player.shot:
            if HALF_WIDTH - self.sprite_half_width < self.screen_x < HALF_WIDTH + self.sprite_half_width:
                self.game.sounds.damage_sound.play()
                self.game.player.shot = False
                self.pain = True
                self.frame_counter = 0
                self.health -= 10
                self.image.fill((255, 0, 0, 50), special_flags=pg.BLEND_ADD)
                try:
                    self.game.client.send_hit_notification()
                except Exception as e:
                    print(f"Failed to send hit notification: {e}")

    def ray_cast_player_npc(self):
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