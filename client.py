import socket
import json
import threading
import time
import pygame as pg

class Menu:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((800, 600))
        pg.display.set_caption("Game Settings")
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont('Arial', 32)
        self.small_font = pg.font.SysFont('Arial', 24)
        
        self.resolutions = [
            (1280, 720),
            (1366, 768),
            (1600, 900),
            (1920, 1080)
        ]
        self.current_res_index = 0
        
        self.sensitivities = [0.0001, 0.0002, 0.0003, 0.0004, 0.0005]
        self.current_sens_index = 2
        
        self.selected = 0
        self.running = True
        
    def draw(self):
        self.screen.fill((30, 30, 30))
        
        title = self.font.render("Game Settings", True, (255, 255, 255))
        self.screen.blit(title, (400 - title.get_width()//2, 100))
        
        res_text = f"Resolution: {self.resolutions[self.current_res_index][0]}x{self.resolutions[self.current_res_index][1]}"
        color = (255, 255, 0) if self.selected == 0 else (255, 255, 255)
        res_surface = self.font.render(res_text, True, color)
        self.screen.blit(res_surface, (400 - res_surface.get_width()//2, 200))
        
        left_arrow = self.small_font.render("<", True, (255, 255, 255))
        right_arrow = self.small_font.render(">", True, (255, 255, 255))
        self.screen.blit(left_arrow, (250, 200))
        self.screen.blit(right_arrow, (550, 200))
        
        sens_text = f"Mouse Sensitivity: {self.sensitivities[self.current_sens_index]}"
        color = (255, 255, 0) if self.selected == 1 else (255, 255, 255)
        sens_surface = self.font.render(sens_text, True, color)
        self.screen.blit(sens_surface, (400 - sens_surface.get_width()//2, 300))
        
        self.screen.blit(left_arrow, (250, 300))
        self.screen.blit(right_arrow, (550, 300))
        
        color = (255, 255, 0) if self.selected == 2 else (255, 255, 255)
        start_surface = self.font.render("START GAME", True, color)
        self.screen.blit(start_surface, (400 - start_surface.get_width()//2, 400))
        
        instructions = self.small_font.render("Use arrow keys to navigate, ENTER to select", True, (200, 200, 200))
        self.screen.blit(instructions, (400 - instructions.get_width()//2, 500))
        
        pg.display.flip()
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                return False
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
                    return False
                
                if event.key == pg.K_RETURN:
                    if self.selected == 2:
                        return True
                
                if event.key == pg.K_UP:
                    self.selected = (self.selected - 1) % 3
                
                if event.key == pg.K_DOWN:
                    self.selected = (self.selected + 1) % 3
                
                if event.key == pg.K_LEFT:
                    if self.selected == 0:
                        self.current_res_index = (self.current_res_index - 1) % len(self.resolutions)
                    elif self.selected == 1:
                        self.current_sens_index = max(0, self.current_sens_index - 1)
                
                if event.key == pg.K_RIGHT:
                    if self.selected == 0:
                        self.current_res_index = (self.current_res_index + 1) % len(self.resolutions)
                    elif self.selected == 1:
                        self.current_sens_index = min(len(self.sensitivities)-1, self.current_sens_index + 1)
        
        return None
    
    def run(self):
        while self.running:
            result = self.handle_events()
            if result is not None:
                return result
            self.draw()
            self.clock.tick(30)
        
        return False
    
    def get_settings(self):
        return {
            'resolution': self.resolutions[self.current_res_index],
            'sensitivity': self.sensitivities[self.current_sens_index]
        }

class Client:
    def __init__(self):
        # Show menu first
        menu = Menu()
        start_game = menu.run()
        
        if not start_game:
            pg.quit()
            return
        
        settings = menu.get_settings()
        selected_width, selected_height = settings['resolution']
        selected_sensitivity = settings['sensitivity']
        
        with open('settings.py', 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if line.startswith('RES = WIDTH, HEIGHT ='):
                line = f"RES = WIDTH, HEIGHT = {selected_width}, {selected_height}\n"
            elif line.startswith('HALF_WIDTH ='):
                line = f"HALF_WIDTH = {selected_width // 2}\n"
            elif line.startswith('HALF_HEIGHT ='):
                line = f"HALF_HEIGHT = {selected_height // 2}\n"
            elif line.startswith('MOUSE_SENSITIVITY ='):
                line = f"MOUSE_SENSITIVITY = {selected_sensitivity}\n"
            new_lines.append(line)
        
        with open('settings.py', 'w') as f:
            f.writelines(new_lines)
        
        from importlib import reload
        import settings
        reload(settings)
        from game import Game
        
        pg.quit()
        
        # Initialize connection
        self.host = settings.SERVER_IP
        self.port = settings.PORT
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = settings.MAX_RECCONECT_ATTEMPS

        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.client.connect((self.host, self.port))
                initial_data = json.loads(self.client.recv(4096).decode())
                self.player_id = initial_data['player_id']
                
                pg.init()
                self.game = Game(self, initial_data)
                self.running = True
                threading.Thread(target=self.receive_data).start()
                self.game.run()
                break
            except Exception as e:
                print(f"Connection error: {e}")
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    print(f"Attempting to reconnect... ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
                    time.sleep(2)
                else:
                    print("Max reconnection attempts reached. Exiting.")
                    self.running = False
                    self.client.close()

    def disconnect(self):
        try:
            data = {
                'disconnect': True,
                'player_id': self.player_id
            }
            self.client.send(json.dumps(data).encode())
            self.client.close()
            self.running = False
            print("Disconnected from server.")
        except Exception as e:
            print(f"Error during disconnect: {e}")

    def receive_data(self):
        while self.running:
            try:
                data = json.loads(self.client.recv(4096).decode())
                if not data:
                    break
                if 'game_started' in data and data['game_started']:
                    print("Game started!")
                    self.game.started = True
                if 'enemy_disconnected' in data and data['enemy_disconnected']:
                    print("Enemy disconnected!")
                    self.game.enemy_disconnected = True
                if 'enemy_reconnected' in data and data['enemy_reconnected']:
                    print("Enemy reconnected!")
                    self.game.enemy_disconnected = False
                if 'enemy_pos' in data and 'enemy_angle' in data:
                    self.game.update_enemy(data['enemy_pos'], data['enemy_angle'])
                if 'rockets' in data:
                    self.game.player.rockets = min(self.game.player.rockets + data['rockets'], MAX_ROCKETS)
                    print(f"Rockets updated: {self.game.player.rockets}")
                if 'your_health' in data:
                    prev_health = self.game.player.health
                    self.game.player.health = data['your_health']
                    if data['your_health'] != prev_health:
                        print(f"Your life has been changed - prev: {prev_health} -> current: {data['your_health']}!")
                    self.game.player.alive = (data['your_health'] > 0)
                    if prev_health > 0 >= data['your_health']:
                        print("You died!")
                        self.game.handle_player_death()
                if 'enemy_health' in data:
                    self.game.enemy.health = data['enemy_health']
                    self.game.enemy.alive = (data['enemy_health'] > 0)
                if 'enemy_shot' in data:
                    if data['enemy_shot']:
                        print("Enemy shot!")
                        self.game.notify_enemy_shot()
                if 'item_collected' in data:
                    item_id = data['item_collected']
                    if item_id in self.game.object_handler.item_sprites:
                        sprite = self.game.object_handler.item_sprites[item_id]
                        self.game.object_handler.sprite_list.remove(sprite)
                        del self.game.object_handler.item_sprites[item_id]
                        print(f"Collected item {item_id}")
                        if 'speed_boost' in data and data['speed_boost']:
                            self.game.player.apply_speed_boost()
                if 'map_items' in data:
                    self.game.update_map_items(data['map_items'])
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Connection error: {e}")
                self.running = False
                break

    def send_data(self, pos, angle, actions=None):
        try:
            data = {
                'pos': pos,
                'angle': angle
            }
            if actions:
                data['actions'] = actions
            self.client.send(json.dumps(data).encode())
        except Exception as e:
            print(f"Failed to send data: {e}")
            self.running = False

    def send_hit_notification(self):
        try:
            data = {
                'pos': self.game.player.pos,
                'angle': self.game.player.angle,
                'hit': True,
                'is_rocket': self.game.player.using_rocket
            }
            print(data)
            self.client.send(json.dumps(data).encode())
        except Exception as e:
            print(f"Failed to send hit notification: {e}")
            self.running = False

if __name__ == '__main__':
    client = Client()