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
        self.init_enemy(initial_data)
        self.enemy_shot_event = False

        # On-screen effects
        self.effect_alpha = 0
        self.effect_duration = PLAYER_DEATH_EFFECT_DURATION
        self.effect_start_time = 0
        self.permanent_effect_alpha = DEATH_SCREEN_ALPHA
        self.effect_color = None
        self.flash_color = None
        self.player_dead = False
        self.enemy_disconnected = False
        self.death_color = DEATH_COLOR
        self.flash_death_color = DEATH_FLASH_COLOR
        self.disconnect_color = DISCONNECT_COLOR
        self.win_color = WIN_COLOR

        # Effect text settings
        self.font = pg.font.SysFont('Arial', 72, bold=True)
        self.text_pos = (HALF_WIDTH, HALF_HEIGHT)
        self.text_color = (255, 255, 255)

        # Effect messages
        self.effect_messages = {
            'death': "YOU DIED",
            'win': "VICTORY!",
            'disconnect': "OPPONENT DISCONNECTED"
        }

    # Enemy

    def init_enemy(self, initial_data):
        enemy_pos = PLAYER_2_POS if initial_data['player_id'] == 0 else PLAYER_1_POS
        enemy_sprite = EnemySprite(self, pos=enemy_pos)
        self.object_handler.add_enemy(enemy_sprite)
        self.enemy = enemy_sprite
        self.enemy.health = initial_data['health']

    def notify_enemy_shot(self):
        self.enemy_shot_event = True

    def handle_enemy_shot(self):
        self.sounds.shoot_sound.play()
        self.enemy.attack = True

    def handle_enemy_hit_player(self):
        self.sounds.damage_sound.play()

    def update_enemy(self, pos, angle):
        self.enemy.x, self.enemy.y = pos
        self.enemy.angle = angle

    # Drawing

    def handle_player_death(self):
        if not self.player.alive and not self.player_dead:
            self.sounds.death_sound.play()
            self.effect_alpha = 255
            self.effect_start_time = pg.time.get_ticks()
            self.player_dead = True

    def draw_screen_effect(self, effect_type):
        if effect_type not in ['death', 'disconnect', 'win']:
            return

        # Set colors based on effect type
        if effect_type == 'death':
            self.effect_color = self.death_color
            self.flash_color = self.flash_death_color
        elif effect_type == 'disconnect':
            self.effect_color = self.disconnect_color
            self.flash_color = self.disconnect_color
        elif effect_type == 'win':
            self.effect_color = self.win_color
            self.flash_color = self.win_color

        # Final pulse effect
        pulse = abs(pg.time.get_ticks() % 2000 - 1000) / 1000
        current_alpha = self.permanent_effect_alpha + int(30 * pulse)
        permanent_overlay = pg.Surface(RES)
        permanent_overlay.fill(self.effect_color)
        permanent_overlay.set_alpha(current_alpha)
        self.screen.blit(permanent_overlay, (0, 0))

        # Flash effect
        if self.effect_alpha > 0:
            elapsed = pg.time.get_ticks() - self.effect_start_time
            if elapsed < self.effect_duration:
                self.effect_alpha = 255 * (1 - elapsed / self.effect_duration)
            else:
                self.effect_alpha = 0

            flash_overlay = pg.Surface(RES)
            flash_overlay.fill(self.flash_color)
            flash_overlay.set_alpha(self.effect_alpha)
            self.screen.blit(flash_overlay, (0, 0))

        # Draw effect message
        if effect_type in self.effect_messages:
            text_surface = self.font.render(self.effect_messages[effect_type], True, self.text_color)
            text_rect = text_surface.get_rect(center=self.text_pos)

            # Add background for better readability
            bg_surface = pg.Surface((text_rect.width + 20, text_rect.height + 20), pg.SRCALPHA)
            bg_surface.fill((0, 0, 0, 150))
            bg_rect = bg_surface.get_rect(center=self.text_pos)

            self.screen.blit(bg_surface, bg_rect)
            self.screen.blit(text_surface, text_rect)

    def draw(self):
        self.object_renderer.draw()
        self.turret.draw()

        if self.player.alive:
            rocket_text = f"Rockets: {self.player.rockets}"
            text_surface = pg.font.SysFont('Arial', 24).render(rocket_text, True, (255, 255, 255))
            self.screen.blit(text_surface, (20, 20))

        if self.player_dead:
            self.draw_screen_effect('death')
        elif self.enemy.health <= 0:
            self.draw_screen_effect('win')
        elif self.enemy_disconnected and self.player.alive:
            self.draw_screen_effect('disconnect')

    def draw2d(self):
        self.screen.fill('black')
        self.map.draw()
        self.player.draw()
        self.enemy.draw()

    # Game

    def update_map_items(self, items_data):
        self.object_handler.update_map_items(items_data)

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
                'direction': self.player.angle,
                'is_rocket': self.player.using_rocket
            })
            self.player.did_shot = False

        self.client.send_data((self.player.x, self.player.y), self.player.angle, actions)

        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f} - Health: {self.player.health}')

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()