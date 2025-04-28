import os
from ready.settings import *
import pygame as pg

class ObjectRenderer:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.wall_textures = self.load_wall_textures()
        self.sky_images = self.load_sky_images()
        self.current_sky_index = 0
        self.sky_offset = 0
        self.animation_speed = 10
        self.frame_count = 0

    def draw(self):
        self.draw_background()
        self.render_game_objects()

    def draw_background(self):
        self.frame_count += 1
        if self.frame_count >= self.animation_speed:
            self.frame_count = 0
            self.current_sky_index = (self.current_sky_index + 1) % len(self.sky_images)

        current_sky_image = self.sky_images[self.current_sky_index]
        self.sky_offset = (self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        self.screen.blit(current_sky_image, (-self.sky_offset, 0))
        self.screen.blit(current_sky_image, (-self.sky_offset + WIDTH, 0))

        pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))

    def render_game_objects(self):
        list_objects = sorted(self.game.raycasting.objects_to_render, key=lambda t: t[0], reverse=True)
        for depth, image, pos in list_objects:
            self.screen.blit(image, pos)

    @staticmethod
    def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
        texture = pg.image.load(path).convert_alpha()
        return pg.transform.scale(texture, res)

    def load_wall_textures(self):
        return {
            1: self.get_texture('resources/textures/1.png'),
            2: self.get_texture('resources/textures/2.png'),
            3: self.get_texture('resources/textures/3.png'),
            4: self.get_texture('resources/textures/4.png'),
            5: self.get_texture('resources/textures/5.png'),
        }

    def load_sky_images(self):
        sky_images = []
        sky_folder = 'resources/textures/sky'
        for file_name in sorted(os.listdir(sky_folder)):
            if file_name.endswith('.png'):
                path = os.path.join(sky_folder, file_name)
                sky_images.append(self.get_texture(path, (WIDTH, HALF_HEIGHT)))
        return sky_images
