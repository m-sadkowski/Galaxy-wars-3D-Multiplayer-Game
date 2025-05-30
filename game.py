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
        # PyGame, screen, server data init
        pg.init()
        pg.mouse.set_visible(False)
        self.client = client
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)  # Timer for animations

        # Game init
        self.started = False
        self.player = Player(self, initial_data['pos'], initial_data['angle'])
        self.player.health = initial_data['health']
        self.enemy = None
        self.map = Map(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.turret = Turret(self)
        self.sounds = Sounds(self)

        # Enemy handling init
        self.init_enemy(initial_data)
        self.enemy_shot_event = False

        # On-screen death effect
        self.death_effect_alpha = 0
        self.death_effect_duration = PLAYER_DEATH_EFFECT_DURATION
        self.death_effect_start_time = 0
        self.permanent_death_alpha = DEATH_SCREEN_ALPHA
        self.death_color = DEATH_COLOR
        self.flash_color = DEATH_FLASH_COLOR
        self.player_dead = False

        # On-screen disconnect effect
        self.enemy_disconnected = False
        self.disconnect_effect_alpha = 0
        self.disconnect_color = (255, 255, 0)

        # On-screen win effect
        self.win_color = (0, 255, 0)


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

    def draw_disconnect_effect(self):
        if self.enemy.health <= 0:
            overlay = pg.Surface(RES)
            overlay.fill(self.win_color)
            overlay.set_alpha(150)
            self.screen.blit(overlay, (0, 0))
        elif self.enemy_disconnected:
            overlay = pg.Surface(RES)
            overlay.fill(self.disconnect_color)
            overlay.set_alpha(150)
            self.screen.blit(overlay, (0, 0))

    def update(self):
        self.handle_player_death()
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
            # print("Player shot has been sent to server")

        self.client.send_data((self.player.x, self.player.y), self.player.angle, actions)

        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f} - Health: {self.player.health}')

    def draw2d(self):
        self.screen.fill('black')
        self.map.draw()
        self.player.draw()
        self.enemy.draw()

    def draw_death_effect(self):
        if self.player_dead:
            # Final pulse blood effect
            pulse = abs(pg.time.get_ticks() % 2000 - 1000) / 1000
            current_alpha = self.permanent_death_alpha + int(30 * pulse)
            permanent_overlay = pg.Surface(RES)
            permanent_overlay.fill(self.death_color)
            permanent_overlay.set_alpha(current_alpha)
            self.screen.blit(permanent_overlay, (0, 0))

            # Blood flash
            if self.death_effect_alpha > 0:
                elapsed = pg.time.get_ticks() - self.death_effect_start_time
                if elapsed < self.death_effect_duration:
                    self.death_effect_alpha = 255 * (1 - elapsed / self.death_effect_duration)
                else:
                    self.death_effect_alpha = 0

                flash_overlay = pg.Surface(RES)
                flash_overlay.fill(self.flash_color)
                flash_overlay.set_alpha(self.death_effect_alpha)
                self.screen.blit(flash_overlay, (0, 0))

    def handle_player_death(self):
        if not self.player.alive and not self.player_dead:
            self.sounds.death_sound.play()
            self.death_effect_alpha = 255
            self.death_effect_start_time = pg.time.get_ticks()
            self.player_dead = True

    def draw(self):
        self.object_renderer.draw()
        self.turret.draw()
        self.draw_death_effect()
        # print(self.player.angle)
        self.draw_disconnect_effect()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.client.running = False
                self.client.disconnect()
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