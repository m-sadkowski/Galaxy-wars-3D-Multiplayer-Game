import sys
from map import *
from player import *
from raycasting import *
from object_renderer import *
from object_handler import *
from turret import *
from sounds import *
from enemy import *


class Game:
    def __init__(self, client, initial_data):
        pg.init()
        pg.mouse.set_visible(False)
        self.client = client
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.player = Player(self, initial_data['pos'], initial_data['angle'])
        self.player.health = initial_data['health']
        self.enemy = None
        self.map = Map(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.turret = Turret(self)
        self.sounds = Sounds(self)
        self.init_enemy(initial_data)

    def init_enemy(self, initial_data):
        enemy_pos = PLAYER_2_POS if initial_data['player_id'] == 0 else PLAYER_1_POS
        enemy_sprite = EnemySprite(self, pos=enemy_pos)
        self.object_handler.add_enemy(enemy_sprite)
        self.enemy = enemy_sprite
        self.enemy.health = initial_data['health']

    def update_enemy(self, pos, angle):
        self.enemy.x, self.enemy.y = pos
        self.enemy.angle = angle

    def handle_shot(self):
        self.sounds.npc_damage.play()
        self.player.health -= 10
        if self.player.health <= 0:
            print("You have been defeated!")

    def handle_enemy_hit(self):
        self.enemy.pain = True
        self.enemy.health -= 10
        if self.enemy.health <= 0:
            self.enemy.alive = False

    def update(self):
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.turret.update()

        # Send player data including any actions
        actions = []
        if self.player.shot:
            actions.append({
                'type': 'shoot',
                'direction': self.player.angle
            })
            self.player.shot = False

        self.client.send_data((self.player.x, self.player.y), self.player.angle, actions)

        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f} - Health: {self.player.health}')

    def draw2d(self):
        self.screen.fill('black')
        self.map.draw()
        self.player.draw()
        self.enemy.draw()

    def draw(self):
        self.object_renderer.draw()
        self.turret.draw()

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.client.running = False
                pg.quit()
                sys.exit()
            self.player.single_fire_event(event)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()