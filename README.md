# Galaxy Wars 3D

## Description

**Galaxy Wars 3D** is a multiplayer 3D space shooter inspired by classic raycasting games like *Wolfenstein 3D* and *Doom*. Face off against another player in dynamic 1v1 battles where reflexes, tactics, and precision are the keys to victory.

## Features

- Fast-paced 1v1 space battles
- Health kits, speed boosts, and powerful missiles on the map
- Smooth multiplayer experience with server-authoritative mechanics
- Classic raycasting-based 3D graphics

## Installation

```bash
git clone https://github.com/m-sadkowski/Galaxy-wars-3D-Multiplayer-Game.git
cd Galaxy-wars-3D-Multiplayer-Game
```

Make sure you have all necessary dependencies installed (e.g., PyGame or other libraries).

## Running the Game

To run the server:

```bash
# Example command
gcc server.c cJSON/cJSON.c -o server.exe -lws2_32
server.exe
```

To run the client:

```bash
# Example command
python client.py
```

*(Adjust commands depending on your environment and setup.)*

## Controls

- `W` – Move forward
- `A` – Move left
- `S` – Move backward
- `D` – Move right
- `Left Mouse Button` – Shoot
- `Right Mouse Button` – Launch missile
- `ESC` – Exit game

## Contributing

Feel free to fork the repository and create pull requests to add new features, fix bugs, or improve performance!

If you want to propose major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.
