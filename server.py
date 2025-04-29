import socket
import threading
import json
from ready.settings import PLAYER_1_POS, PLAYER_2_POS
import time


class Server:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5555
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(2)

        self.players = [
            {'pos': PLAYER_1_POS, 'angle': 0, 'health': 100, 'actions': []},
            {'pos': PLAYER_2_POS, 'angle': 180, 'health': 100, 'actions': []}
        ]
        self.lock = threading.Lock()
        self.conns = []
        self.hits = []

    def handle_client(self, conn, player_id):
        try:
            # Send initial data
            initial_data = {
                'player_id': player_id,
                'pos': self.players[player_id]['pos'],
                'angle': self.players[player_id]['angle'],
                'health': self.players[player_id]['health'],
                'enemy_health': self.players[1 - player_id]['health']
            }
            conn.send(json.dumps(initial_data).encode())

            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break

                with self.lock:
                    data = json.loads(data)
                    self.players[player_id]['pos'] = data['pos']
                    self.players[player_id]['angle'] = data['angle']

                    # Process actions
                    if 'actions' in data:
                        for action in data['actions']:
                            if action['type'] == 'shoot':
                                self.players[player_id]['shot'] = True

                    # Process hits
                    if 'hit' in data and data['hit']:
                        other_id = 1 - player_id
                        self.process_hit(player_id, other_id)

                    # Prepare response
                    other_id = 1 - player_id
                    response = {
                        'enemy_pos': self.players[other_id]['pos'],
                        'enemy_angle': self.players[other_id]['angle'],
                        'enemy_health': self.players[other_id]['health'],
                        'your_health': self.players[player_id]['health'],
                        'enemy_shot': self.players[other_id].pop('shot', False)
                    }

                    # Add hit information if player was hit
                    for hit in self.hits:
                        if hit['target_id'] == player_id:
                            response['hit'] = True
                            break

                    conn.send(json.dumps(response).encode())
                    self.hits = [h for h in self.hits if h['target_id'] != player_id]

        except Exception as e:
            print(f"Error with player {player_id}: {e}")
        finally:
            conn.close()

    def process_hit(self, shooter_id, target_id):
        try:
            self.players[target_id]['health'] -= 35
            self.hits.append({
                'shooter_id': shooter_id,
                'target_id': target_id,
                'timestamp': time.time()
            })
            print(f"Player {shooter_id} hit player {target_id}! Health remaining: {self.players[target_id]['health']}")

            if self.players[target_id]['health'] <= 0:
                print(f"Player {target_id} has been defeated by player {shooter_id}!")
        except Exception as e:
            print(f"Error processing hit: {e}")

    def run(self):
        print("Waiting for connections...")
        for i in range(2):
            conn, addr = self.server.accept()
            self.conns.append(conn)
            print(f"Player {i} connected from {addr}")
            threading.Thread(target=self.handle_client, args=(conn, i)).start()


if __name__ == '__main__':
    server = Server()
    server.run()