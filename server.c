#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#pragma comment(lib, "ws2_32.lib")

#define PORT 5555
#define BUFFER_SIZE 1024

// Struktura gracza
typedef struct {
    int x, y;
    int angle;
    int health;
    bool shot;
} Player;

Player players[2];
HANDLE lock;

void send_data(SOCKET conn, const char *data) {
    send(conn, data, strlen(data), 0);
}

void receive_data(SOCKET conn, char *buffer, int size) {
    memset(buffer, 0, size);
    recv(conn, buffer, size, 0);
}

void process_hit(int shooter_id, int target_id) {
    players[target_id].health -= 35;
    if (players[target_id].health <= 0) {
        printf("Player %d has been defeated by player %d!\n", target_id, shooter_id);
    } else {
        printf("Player %d hit player %d! Remaining health: %d\n", shooter_id, target_id, players[target_id].health);
    }
}

DWORD WINAPI handle_client(LPVOID param) {
    SOCKET conn = (SOCKET)param;
    int player_id = (conn == INVALID_SOCKET) ? -1 : (conn == players[0].socket ? 0 : 1);
    char buffer[BUFFER_SIZE];

    // Wysłanie danych początkowych
    sprintf(buffer, "{\"player_id\": %d, \"x\": %d, \"y\": %d, \"angle\": %d, \"health\": %d}",
            player_id, players[player_id].x, players[player_id].y, players[player_id].angle, players[player_id].health);
    send_data(conn, buffer);

    while (1) {
        receive_data(conn, buffer, BUFFER_SIZE);
        if (strlen(buffer) == 0) {
            break;
        }

        WaitForSingleObject(lock, INFINITE);

        // Aktualizacja pozycji i przetwarzanie akcji
        int x, y, angle;
        bool shot;
        sscanf(buffer, "{\"x\": %d, \"y\": %d, \"angle\": %d, \"shot\": %d}", &x, &y, &angle, &shot);
        players[player_id].x = x;
        players[player_id].y = y;
        players[player_id].angle = angle;
        players[player_id].shot = shot;

        // Przetwarzanie strzału
        if (shot) {
            int target_id = 1 - player_id;
            process_hit(player_id, target_id);
        }

        // Przygotowanie odpowiedzi
        int enemy_id = 1 - player_id;
        sprintf(buffer, "{\"enemy_x\": %d, \"enemy_y\": %d, \"enemy_angle\": %d, \"enemy_health\": %d, \"your_health\": %d}",
                players[enemy_id].x, players[enemy_id].y, players[enemy_id].angle, players[enemy_id].health, players[player_id].health);

        send_data(conn, buffer);

        ReleaseMutex(lock);
    }

    closesocket(conn);
    return 0;
}

int main() {
    WSADATA wsa;
    SOCKET server_socket, client_socket;
    struct sockaddr_in server_addr, client_addr;
    int client_addr_size = sizeof(client_addr);

    // Inicjalizacja WinSock
    WSAStartup(MAKEWORD(2, 2), &wsa);

    // Tworzenie socketu
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == INVALID_SOCKET) {
        printf("Could not create socket: %d\n", WSAGetLastError());
        return 1;
    }

    // Konfiguracja adresu serwera
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Bindowanie socketu
    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        printf("Bind failed: %d\n", WSAGetLastError());
        return 1;
    }

    listen(server_socket, 2);

    printf("Waiting for connections...\n");

    lock = CreateMutex(NULL, FALSE, NULL);

    for (int i = 0; i < 2; i++) {
        client_socket = accept(server_socket, (struct sockaddr *)&client_addr, &client_addr_size);
        if (client_socket == INVALID_SOCKET) {
            printf("Accept failed: %d\n", WSAGetLastError());
            continue;
        }

        printf("Player %d connected\n", i);

        players[i] = (Player){.x = 0, .y = 0, .angle = i == 0 ? 0 : 180, .health = 100, .shot = false};
        CreateThread(NULL, 0, handle_client, (LPVOID)client_socket, 0, NULL);
    }

    WaitForSingleObject(lock, INFINITE);

    closesocket(server_socket);
    WSACleanup();

    return 0;
}
