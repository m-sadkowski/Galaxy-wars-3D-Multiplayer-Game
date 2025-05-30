#include <stdio.h>
#include <winsock2.h>
#include <process.h>
#include <windows.h>
#include "cJSON/cJSON.h"

#pragma comment(lib, "ws2_32.lib")

#define PORT 5555
#define BUFFER_SIZE 1024
#define MAX_CLIENTS 2

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
int connected_clients = 0;  // Licznik podłączonych graczy
SOCKET client_sockets[MAX_CLIENTS];  // Przechowuje gniazda klientów

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

    players[target_id].health -= 35;
    hits[target_id] = 1;
    printf("Player %d hit player %d! Health remaining: %d\n",
           shooter_id, target_id, players[target_id].health);

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
                        players[player_id].shot = 1;
                    }
                }
            }

            // Process hits
            cJSON *hit = cJSON_GetObjectItem(data, "hit");
            if(hit && hit->valueint) {
                process_hit(player_id, other_id);
            }
        }

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

        // Zapisz gniazdo klienta
        client_sockets[i] = client_socket;
        connected_clients++;
        
        _beginthreadex(NULL, 0, client_handler, args, 0, NULL);
    }

    getchar();
    closesocket(server_socket);
    WSACleanup();
    CloseHandle(mutex);
    return 0;
}