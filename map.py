import pygame as pg

_ = False
mini_map = [
   # 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15

    [2, 3, 2, 2, 2, 3, 2, 2, 5, 1, 1, 1, 1, 1, 1, 1], #0
    [4, _, _, _, _, _, _, _, _, _, _, 1, _, _, _, 2], #1
    [2, _, _, _, _, 2, 2, 2, _, _, _, 5, _, _, _, 2], #2
    [2, _, _, _, _, 3, _, _, _, _, 1, 1, _, _, _, 3], #3
    [3, _, _, _, _, 2, _, _, 2, _, _, _, _, _, _, 4], #4
    [2, _, _, 2, 4, 2, _, _, 4, _, _, _, _, _, _, 2], #5
    [5, _, _, _, _, _, _, _, 1, 5, 1, 1, _, _, _, 2], #6
    [1, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 3], #7
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1], #8
]

class Map:
    def __init__(self, game):
        self.game = game
        self.mini_map = mini_map
        self.world_map = {}
        self.get_map()

    def get_map(self):
        for j, row in enumerate(self.mini_map):
            for i, value in enumerate(row):
                if value:
                    self.world_map[(i, j)] = value

    def draw(self):
        [pg.draw.rect(self.game.screen, 'darkgray', (pos[0] * 100, pos[1] * 100, 100, 100), 2)
         for pos in self.world_map]