import socket
import json
import threading
from game import Game


class Client:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5555
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

                # Update enemy position and angle
                if 'enemy_pos' in data and 'enemy_angle' in data:
                    self.game.update_enemy(data['enemy_pos'], data['enemy_angle'])

                # Update health values
                if 'enemy_health' in data:
                    self.game.enemy.health = data['enemy_health']
                if 'your_health' in data:
                    self.game.player.health = data['your_health']
                # Handle enemy shot
                if 'enemy_shot' in data and data['enemy_shot']:
                    self.game.handle_enemy_shot()
                # Handle hit on player
                if 'hit' in data and data['hit']:
                    self.game.handle_enemy_hit()

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
            # print(f"Sending data: {data}")
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