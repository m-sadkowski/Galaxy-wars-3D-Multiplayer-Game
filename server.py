import socket
import threading
import json
from settings import PLAYER_1_POS, PLAYER_2_POS


class Server:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5555
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(2)

        self.players = [{'pos': PLAYER_1_POS, 'angle': 0}, {'pos': PLAYER_2_POS, 'angle': 180}]
        self.lock = threading.Lock()
        self.conns = []

    def handle_client(self, conn, player_id):
        try:
            conn.send(json.dumps({'player_id': player_id, 'pos': self.players[player_id]['pos'],
                                  'angle': self.players[player_id]['angle']}).encode())
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                with self.lock:
                    self.players[player_id] = json.loads(data)
                    other_id = 1 - player_id
                    conn.send(json.dumps(
                        {'pos': self.players[other_id]['pos'], 'angle': self.players[other_id]['angle']}).encode())
        except:
            pass
        finally:
            conn.close()

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