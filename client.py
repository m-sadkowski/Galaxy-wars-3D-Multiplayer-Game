import socket
import json
import threading
import time

from settings import *
from game import Game

class Client:
    def __init__(self):
        self.host = SERVER_IP
        self.port = PORT
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = MAX_RECCONECT_ATTEMPS

        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.client.connect((self.host, self.port))
                initial_data = json.loads(self.client.recv(4096).decode())
                self.player_id = initial_data['player_id']
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