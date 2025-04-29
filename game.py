import sys
from ready.map import *
from ready.player import *
from ready.raycasting import *
from ready.object_renderer import *
from ready.object_handler import *
from ready.turret import *
from ready.sounds import *
from enemy import *


class Game:
    def __init__(self, client, initial_data):
        # PyGame, screen, server data
        pg.init()
        pg.mouse.set_visible(False)
        self.client = client
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)  # Timer dla animacji

        # Reszta inicjalizacji pozostaje bez zmian...
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
        self.enemy_shot_event = False


    def init_enemy(self, initial_data):
        enemy_pos = PLAYER_2_POS if initial_data['player_id'] == 0 else PLAYER_1_POS
        enemy_sprite = EnemySprite(self, pos=enemy_pos)
        self.object_handler.add_enemy(enemy_sprite)
        self.enemy = enemy_sprite
        self.enemy.health = initial_data['health']

    def handle_enemy_shot(self):
        self.sounds.shoot_sound.play()
        self.enemy.attack = True

    def handle_enemy_hit_player(self):
        self.sounds.damage_sound.play()

    def update_enemy(self, pos, angle):
        self.enemy.x, self.enemy.y = pos
        self.enemy.angle = angle

    def notify_enemy_shot(self):
        self.enemy_shot_event = True

    def update(self):
        self.player.update()

        if self.enemy_shot_event:
            self.enemy.attack = True
            self.enemy_shot_event = False

        self.raycasting.update()
        self.object_handler.update()
        self.turret.update()

        # Send player data including any actions
        actions = []
        if self.player.did_shot:
            actions.append({
                'type': 'shoot',
                'direction': self.player.angle
            })
            self.player.did_shot = False
            print("Wyslal informacje o lokalnym strzale")

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
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.client.running = False
                pg.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            self.player.single_fire_event(event)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()