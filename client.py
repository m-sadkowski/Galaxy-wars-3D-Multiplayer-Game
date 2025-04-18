import socket
import json
import threading
from game import Game


class Client:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5555
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))

        initial_data = json.loads(self.client.recv(1024).decode())
        self.player_id = initial_data['player_id']
        self.game = Game(self, initial_data)

        self.running = True
        threading.Thread(target=self.receive_data).start()
        self.game.run()

    def receive_data(self):
        while self.running:
            try:
                data = json.loads(self.client.recv(1024).decode())
                self.game.update_enemy(data['pos'], data['angle'])
            except:
                self.running = False
                break

    def send_data(self, pos, angle):
        self.client.send(json.dumps({'pos': pos, 'angle': angle}).encode())


if __name__ == '__main__':
    client = Client()