# Galaxy Wars 3D

## Description

**Galaxy Wars 3D** is a multiplayer 3D space shooter inspired by classic raycasting games like *Wolfenstein 3D* and *Doom*. Face off against another player in dynamic 1v1 battles where reflexes, tactics, and precision are the keys to victory.

## Features

* Fast-paced 1v1 space battles
* Health kits, speed boosts, and powerful missiles on the map
* Smooth multiplayer experience with server-authoritative mechanics
* Classic raycasting-based 3D graphics

## Installation

```bash
git clone https://github.com/m-sadkowski/Galaxy-wars-3D-Multiplayer-Game.git
cd Galaxy-wars-3D-Multiplayer-Game
```

### Dependencies

Ensure you have the necessary dependencies installed:

* **Python 3.x** with PyGame
* **GCC** (for compiling the server on Windows/Linux)
* **cJSON** (included in `libs/cJSON/`)
* **Ngrok** (for multiplayer over internet) - [download here](https://ngrok.com/download)

## Running the Game

### Single Player (Local Testing)
```bash
# Compile and run server
gcc server.c libs/cJSON/cJSON.c -o server -lws2_32
./server

# Run client in separate terminal
python client.py
```

### Multiplayer Setup (Internet)

1. **Host Player (Server Owner)**
   ```bash
   # 1. Run the server
   gcc server.c libs/cJSON/cJSON.c -o server -lws2_32
   ./server

   # 2. In a new terminal, start ngrok tunnel
   ngrok tcp 5555
   ```

2. **Remote Player (Friend)**
   - Get the ngrok address from host (looks like `tcp://X.tcp.ngrok.io:XXXXX`)
   - Modify `settings.py`:
     ```python
     SERVER_IP = 'X.tcp.ngrok.io'  # Replace with host's ngrok address
     PORT = XXXXX                  # Replace with host's ngrok port
     ```
   - Run client normally:
     ```bash
     python client.py
     ```

3. **Host Client Setup**
   - Keep `settings.py` as default:
     ```python
     SERVER_IP = 'localhost'
     PORT = 5555
     ```

## Controls

* `W` – Move forward
* `A` – Move left
* `S` – Move backward
* `D` – Move right
* `Left Mouse Button` – Shoot
* `Right Mouse Button` – Launch missile
* `ESC` – Exit game

## Troubleshooting

- **Connection Issues**:
  - Ensure ngrok and server are running on host
  - Verify correct IP/port in remote client's settings.py
  - Check firewall allows TCP connections on port 5555

- **"Address already in use"**:
  ```bash
  # Linux/Mac
  kill $(lsof -t -i:5555)

  # Windows
  taskkill /F /PID $(netstat -ano | findstr :5555 | awk '{print $5}')
  ```

## Contributing

Feel free to fork the repository and create pull requests to add new features, fix bugs, or improve performance!

If you want to propose major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.
