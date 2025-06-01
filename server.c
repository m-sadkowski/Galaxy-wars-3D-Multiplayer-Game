#include <stdio.h>
#include <winsock2.h>
#include <process.h>
#include <windows.h>
#include <math.h>
#include "libs/cJSON/cJSON.h"

#pragma comment(lib, "ws2_32.lib")

#define PORT 5555
#define BUFFER_SIZE 1024
#define MAX_CLIENTS 2

#define DAMAGE 25

typedef struct {
    SOCKET socket;
    int player_id;
} ClientArgs;

typedef struct {
    double pos[2];
    double angle;
    int health;
    int shot;
} Player;

Player players[2] = {
    {{1.5, 5}, 0, 100, 0},
    {{14.5, 4}, 3.1425, 100, 0}
};

HANDLE mutex;
int hits[2] = {0};
int connected_clients = 0;
SOCKET client_sockets[MAX_CLIENTS];

typedef struct {
    double pos[2];
    int type;  // 1 - rocket, 2 - repair kit, 3 - star
    int collected;
} MapItem;

MapItem map_items[] = {
    {{1.5, 3.5}, 1, 0},  // Rocket
    {{1.5, 7.5}, 1, 0},  // Rocket
    {{11.5, 4.5}, 1, 0},  // Rocket
    {{3.5, 7.5}, 2, 0},  // Repair kit
    {{10.5, 3.5}, 2, 0},   // Repair kit
    {{5.5, 9.5}, 3, 0},   // Star
    {{8.5, 3.5}, 3, 0}   // Star
};
#define NUM_ITEMS (sizeof(map_items) / sizeof(MapItem))

void send_json(SOCKET sock, cJSON *json) {
    char *data = cJSON_PrintUnformatted(json);
    int len = strlen(data);
    send(sock, data, len, 0);
    free(data);
}

void broadcast_game_started() {
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddBoolToObject(msg, "game_started", 1);

    for(int i = 0; i < MAX_CLIENTS; i++) {
        send_json(client_sockets[i], msg);
    }

    cJSON_Delete(msg);
}

void process_hit(int shooter_id, int target_id) {
    WaitForSingleObject(mutex, INFINITE);

    int is_rocket = players[shooter_id].shot == 2;
    int damage = is_rocket ? 2 * DAMAGE : DAMAGE;

    players[target_id].health -= damage;
    hits[target_id] = 1;
    printf("Player %d hit player %d for %d damage (%s)! Health remaining: %d\n",
           shooter_id, target_id, damage,
           is_rocket ? "rocket" : "normal",
           players[target_id].health);

    if(players[target_id].health <= 0) {
        printf("Player %d defeated by player %d!\n", target_id, shooter_id);
    }

    ReleaseMutex(mutex);
}

void broadcast_disconnect(int disconnected_id) {
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddBoolToObject(msg, "enemy_disconnected", 1);

    for(int i = 0; i < MAX_CLIENTS; i++) {
        if (i != disconnected_id && client_sockets[i] != INVALID_SOCKET) {
            send_json(client_sockets[i], msg);
        }
    }

    cJSON_Delete(msg);
}

void broadcast_reconnect(int reconnected_id) {
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddBoolToObject(msg, "enemy_reconnected", 1);

    for(int i = 0; i < MAX_CLIENTS; i++) {
        if (i != reconnected_id && client_sockets[i] != INVALID_SOCKET) {
            send_json(client_sockets[i], msg);
        }
    }

    cJSON_Delete(msg);
}

void check_item_collection(int player_id) {
    WaitForSingleObject(mutex, INFINITE);

    for(int i = 0; i < NUM_ITEMS; i++) {
        if(!map_items[i].collected) {
            double dx = players[player_id].pos[0] - map_items[i].pos[0];
            double dy = players[player_id].pos[1] - map_items[i].pos[1];
            double dist = sqrt(dx*dx + dy*dy);

            if(dist < 0.5) {
                map_items[i].collected = 1;
                printf("Player %d collected item %d at (%.1f, %.1f)\n",
                       player_id, map_items[i].type,
                       map_items[i].pos[0], map_items[i].pos[1]);

                // Apply item effects
                if(map_items[i].type == 1) {  // Rocket
                    cJSON *msg = cJSON_CreateObject();
                    cJSON_AddNumberToObject(msg, "item_collected", i);
                    cJSON_AddNumberToObject(msg, "rockets", 1);
                    send_json(client_sockets[player_id], msg);
                    cJSON_Delete(msg);
                    printf("Player %d collected rocket\n", player_id);
                    continue;
                }
                if(map_items[i].type == 2) {  // Repair kit
                    players[player_id].health += DAMAGE;
                    if(players[player_id].health > 100) {
                        players[player_id].health = 100;
                    }
                    printf("Player %d health restored to %d\n", player_id, players[player_id].health);
                }
                if(map_items[i].type == 3) {  // Star
                    cJSON *msg = cJSON_CreateObject();
                    cJSON_AddNumberToObject(msg, "item_collected", i);
                    cJSON_AddNumberToObject(msg, "speed_boost", 1);
                    send_json(client_sockets[player_id], msg);
                    cJSON_Delete(msg);
                    continue;
                }

                // Notify both players about the collected item (excluding stars)
                cJSON *msg = cJSON_CreateObject();
                cJSON_AddNumberToObject(msg, "item_collected", i);
                for(int j = 0; j < MAX_CLIENTS; j++) {
                    if(client_sockets[j] != INVALID_SOCKET) {
                        send_json(client_sockets[j], msg);
                    }
                }
                cJSON_Delete(msg);
            }
        }
    }

    ReleaseMutex(mutex);
}

unsigned __stdcall client_handler(void *args) {
    ClientArgs *client = (ClientArgs *)args;
    SOCKET sock = client->socket;
    int player_id = client->player_id;
    int other_id = 1 - player_id;
    char buffer[BUFFER_SIZE];

    // Send initial data
    cJSON *init_data = cJSON_CreateObject();
    cJSON_AddNumberToObject(init_data, "player_id", player_id);
    cJSON_AddItemToObject(init_data, "pos", cJSON_CreateDoubleArray(players[player_id].pos, 2));
    cJSON_AddNumberToObject(init_data, "angle", players[player_id].angle);
    cJSON_AddNumberToObject(init_data, "health", players[player_id].health);
    cJSON_AddNumberToObject(init_data, "enemy_health", players[other_id].health);

    // Send initial map items
    cJSON *items_array = cJSON_CreateArray();
    for(int i = 0; i < NUM_ITEMS; i++) {
        if(!map_items[i].collected) {
            cJSON *item = cJSON_CreateObject();
            cJSON_AddNumberToObject(item, "id", i);
            cJSON_AddNumberToObject(item, "type", map_items[i].type);
            cJSON_AddItemToObject(item, "pos", cJSON_CreateDoubleArray(map_items[i].pos, 2));
            cJSON_AddItemToArray(items_array, item);
        }
    }
    cJSON_AddItemToObject(init_data, "map_items", items_array);

    send_json(sock, init_data);
    cJSON_Delete(init_data);

    if(connected_clients == MAX_CLIENTS) {
        broadcast_game_started();
    }

    while(1) {
        int bytes = recv(sock, buffer, BUFFER_SIZE - 1, 0);
        if(bytes <= 0) {
            printf("Player %d disconnected\n", player_id);
            broadcast_disconnect(player_id);
            break;
        }
        buffer[bytes] = '\0';

        WaitForSingleObject(mutex, INFINITE);
        cJSON *data = cJSON_Parse(buffer);

        if(data) {
            cJSON *disconnect = cJSON_GetObjectItem(data, "disconnect");
            if(disconnect && disconnect->valueint) {
                printf("Player %d disconnected\n", player_id);
                broadcast_disconnect(player_id);
                cJSON_Delete(data);
                ReleaseMutex(mutex);
                break;
            }

            cJSON *pos = cJSON_GetObjectItem(data, "pos");
            if(pos) {
                players[player_id].pos[0] = cJSON_GetArrayItem(pos, 0)->valuedouble;
                players[player_id].pos[1] = cJSON_GetArrayItem(pos, 1)->valuedouble;
            }

            cJSON *angle = cJSON_GetObjectItem(data, "angle");
            if(angle) players[player_id].angle = angle->valuedouble;

            // Process actions
            cJSON *actions = cJSON_GetObjectItem(data, "actions");
            if(actions) {
                for(int i=0; i<cJSON_GetArraySize(actions); i++) {
                    cJSON *action = cJSON_GetArrayItem(actions, i);
                    if(cJSON_GetObjectItem(action, "type") &&
                       strcmp(cJSON_GetObjectItem(action, "type")->valuestring, "shoot") == 0) {
                        cJSON *is_rocket = cJSON_GetObjectItem(action, "is_rocket");
                        players[player_id].shot = (is_rocket && cJSON_IsTrue(is_rocket)) ? 2 : 1;
                    }
                }
            }

            // Process hits
            cJSON *hit = cJSON_GetObjectItem(data, "hit");
            if(hit && hit->valueint) {
                cJSON *is_rocket = cJSON_GetObjectItem(data, "is_rocket");
                if(is_rocket && cJSON_IsTrue(is_rocket)) {
                    players[player_id].shot = 2;
                }
                process_hit(player_id, other_id);
            }
        }

        // Check for item collection
        check_item_collection(player_id);

        // Prepare response
        cJSON *response = cJSON_CreateObject();
        cJSON_AddItemToObject(response, "enemy_pos", cJSON_CreateDoubleArray(players[other_id].pos, 2));
        cJSON_AddNumberToObject(response, "enemy_angle", players[other_id].angle);
        cJSON_AddNumberToObject(response, "enemy_health", players[other_id].health);
        cJSON_AddNumberToObject(response, "your_health", players[player_id].health);
        cJSON_AddBoolToObject(response, "enemy_shot", players[other_id].shot);
        players[other_id].shot = 0;

        if(hits[player_id]) {
            cJSON_AddBoolToObject(response, "hit", 1);
            hits[player_id] = 0;
        }

        // Send current map items
        cJSON *current_items_array = cJSON_CreateArray();
        for(int i = 0; i < NUM_ITEMS; i++) {
            if(!map_items[i].collected) {
                cJSON *item = cJSON_CreateObject();
                cJSON_AddNumberToObject(item, "id", i);
                cJSON_AddNumberToObject(item, "type", map_items[i].type);
                cJSON_AddItemToObject(item, "pos", cJSON_CreateDoubleArray(map_items[i].pos, 2));
                cJSON_AddItemToArray(current_items_array, item);
            }
        }
        cJSON_AddItemToObject(response, "map_items", current_items_array);

        send_json(sock, response);
        cJSON_Delete(response);
        ReleaseMutex(mutex);
    }

    closesocket(sock);
    client_sockets[player_id] = INVALID_SOCKET;
    connected_clients--;
    free(client);
    return 0;
}

int main() {
    WSADATA wsa;
    SOCKET server_socket;
    struct sockaddr_in server;

    WSAStartup(MAKEWORD(2,2), &wsa);
    server_socket = socket(AF_INET, SOCK_STREAM, 0);

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons(PORT);

    bind(server_socket, (struct sockaddr*)&server, sizeof(server));
    listen(server_socket, MAX_CLIENTS);

    mutex = CreateMutex(NULL, FALSE, NULL);
    printf("Waiting for connections...\n");

    for(int i=0; i<MAX_CLIENTS; i++) {
        SOCKET client_socket = accept(server_socket, NULL, NULL);
        printf("Player %d connected\n", i);

        ClientArgs *args = malloc(sizeof(ClientArgs));
        args->socket = client_socket;
        args->player_id = i;

        client_sockets[i] = client_socket;
        connected_clients++;

        _beginthreadex(NULL, 0, client_handler, args, 0, NULL);
    }

    while(1) {
        for(int i=0; i<MAX_CLIENTS; i++) {
            if(client_sockets[i] == INVALID_SOCKET) {
                SOCKET client_socket = accept(server_socket, NULL, NULL);
                if(client_socket != INVALID_SOCKET) {
                    printf("Player %d connected%s\n", i, connected_clients > 0 ? " (reconnected)" : "");

                    ClientArgs *args = malloc(sizeof(ClientArgs));
                    args->socket = client_socket;
                    args->player_id = i;

                    client_sockets[i] = client_socket;
                    connected_clients++;

                    _beginthreadex(NULL, 0, client_handler, args, 0, NULL);

                    if(connected_clients > 1) {
                        broadcast_reconnect(i);
                    }
                }
            }
        }
        Sleep(100);
    }

    getchar();
    closesocket(server_socket);
    WSACleanup();
    CloseHandle(mutex);
    return 0;
}