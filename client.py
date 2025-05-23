import socket
import json
import threading
from ready.settings import *
from game import Game


class Client:
    def __init__(self):
        self.host = SERVER_IP
        self.port = PORT
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.host, self.port))
            initial_data = json.loads(self.client.recv(4096).decode())
            self.player_id = initial_data['player_id']
            self.game = Game(self, initial_data)
            self.running = True
            threading.Thread(target=self.receive_data).start()
            self.game.run()
        except Exception as e:
            print(f"Connection error: {e}")
            self.running = False
            self.client.close()

    def receive_data(self):
        while self.running:
            try:
                data = json.loads(self.client.recv(4096).decode())
                if not data:
                    break
                if 'enemy_pos' in data and 'enemy_angle' in data:
                    self.game.update_enemy(data['enemy_pos'], data['enemy_angle'])
                if 'your_health' in data:
                    prev_health = self.game.player.health
                    self.game.player.health = data['your_health']
                    self.game.player.alive = (data['your_health'] > 0)
                    # Handle player death only once
                    if prev_health > 0 >= data['your_health']:
                        # print("Player died!")
                        self.game.handle_player_death()
                if 'enemy_health' in data:
                    self.game.enemy.health = data['enemy_health']
                    self.game.enemy.alive = (data['enemy_health'] > 0)
                if 'enemy_shot' in data:
                    if data['enemy_shot']:
                        # print("Enemy shot!")
                        self.game.notify_enemy_shot()
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
                'hit': True
            }
            print(data)
            self.client.send(json.dumps(data).encode())
        except Exception as e:
            print(f"Failed to send hit notification: {e}")
            self.running = False


if __name__ == '__main__':
    client = Client()