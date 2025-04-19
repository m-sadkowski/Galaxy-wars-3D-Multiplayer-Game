import sys
from map import *
from player import *
from raycasting import *
from object_renderer import *
from object_handler import *
from turret import *
from sounds import *

class Game:
    def __init__(self, client, initial_data):
        pg.init()
        pg.mouse.set_visible(False)
        self.client = client
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1

        self.map = Map(self)
        self.player = Player(self, initial_data['pos'], initial_data['angle'])
        self.enemy = Player(self, PLAYER_2_POS if initial_data['player_id'] == 0 else PLAYER_1_POS, 0)
        self.enemy.color = 'red'
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.turret = Turret(self)
        self.sounds = Sounds(self)

    def update(self):
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.turret.update()
        self.send_player_data()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f}')

    def draw(self):
        # self.screen.fill('black')
        self.object_renderer.draw()
        self.turret.draw()
        # self.map.draw()
        # self.player.draw()
        # self.enemy.draw()

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.client.running = False
                pg.quit()
                sys.exit()
            # Possbily will need change
            self.player.single_fire_event(event)

    def send_player_data(self):
        pos = (self.player.x, self.player.y)
        self.client.send_data(pos, self.player.angle)

    def update_enemy(self, pos, angle):
        self.enemy.x, self.enemy.y = pos
        self.enemy.angle = angle

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()