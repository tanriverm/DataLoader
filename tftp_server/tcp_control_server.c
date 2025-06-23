// tcp_control_server.c - TCP Control Server for ARINC 615A commands

/*

 What’s Now Supported on Target Control Server:
INIT_LOAD → Starts a session, stores a dummy session ID

SEND_LSE → Accepts file_name and crc32, stores state

VERIFY_LSE → Echoes file name back

COMMIT_LOAD → Flags session as committed

ABORT → Resets session and state

REPORT_STATUS → Summarizes current state

GET_DEVICE_INFO → Returns device ID/version

*/

#include "tcp_control_server.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

#define CONTROL_PORT 61500
#define BUFFER_SIZE 1024

static char g_device_id[] = "FCC1";
static uint32_t g_session_id = 0;
static char g_last_lse_id[64] = {0};
static char g_last_file_name[128] = {0};
static uint32_t g_last_crc32 = 0;
static int g_committed = 0;

static void handle_json_command(const char* json, char* response_buf, size_t response_buf_size) {

    printf("Received JSON command: %s\n", json);

    if (strstr(json, "INIT_LOAD")) {
        g_session_id = 12345;  // Dummy session ID
        g_committed = 0;
        snprintf(response_buf, response_buf_size, "{\"status\":\"OK\",\"session_id\":%u}", g_session_id);
    }
    else if (strstr(json, "SEND_LSE")) {
        const char* fname = strstr(json, "file_name");
        const char* crcstr = strstr(json, "crc32");
        if (fname && crcstr) {
            sscanf(fname, "\\\"file_name\\\":\\\"%127[^\"]", g_last_file_name);
            sscanf(crcstr, "\"crc32\":%u", &g_last_crc32);
            snprintf(g_last_lse_id, sizeof(g_last_lse_id), "LSE1");
            snprintf(response_buf, response_buf_size, "{\"status\":\"OK\",\"message\":\"LSE %s accepted\"}", g_last_file_name);
        } else {
            snprintf(response_buf, response_buf_size, "{\"status\":\"ERROR\",\"message\":\"Missing file_name or crc32\"}");
        }
    }
    else if (strstr(json, "VERIFY_LSE")) {
        snprintf(response_buf, response_buf_size, "{\"status\":\"OK\",\"message\":\"LSE %s verified\"}", g_last_file_name);
    }
    else if (strstr(json, "COMMIT_LOAD")) {
        g_committed = 1;
        snprintf(response_buf, response_buf_size, "{\"status\":\"OK\",\"message\":\"Session %u committed\"}", g_session_id);
    }
    else if (strstr(json, "ABORT")) {
        g_session_id = 0;
        g_committed = 0;
        g_last_file_name[0] = '\0';
        snprintf(response_buf, response_buf_size, "{\"status\":\"OK\",\"message\":\"Aborted\"}");
    }
    else if (strstr(json, "REPORT_STATUS")) {
        snprintf(response_buf, response_buf_size,
            "{\"status\":\"OK\",\"session\":%u,\"file\":\"%s\",\"committed\":%s}",
            g_session_id,
            g_last_file_name,
            g_committed ? "true" : "false");
    }
    else if (strstr(json, "GET_DEVICE_INFO")) {
        snprintf(response_buf, response_buf_size,
            "{\"status\":\"OK\",\"device\":\"%s\",\"version\":\"v1.0\"}", g_device_id);
    }
    else {
        snprintf(response_buf, response_buf_size, "{\"status\":\"ERROR\",\"message\":\"Unknown command\"}");
    }
}

void tcp_control_server_loop(void* arg) {
    WSADATA wsa;
    SOCKET listen_sock, client_sock;
    struct sockaddr_in server_addr, client_addr;
    int client_len = sizeof(client_addr);
    char recv_buf[BUFFER_SIZE];
    char response[BUFFER_SIZE];

    WSAStartup(MAKEWORD(2,2), &wsa);

    listen_sock = socket(AF_INET, SOCK_STREAM, 0);
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(CONTROL_PORT);
    bind(listen_sock, (struct sockaddr*)&server_addr, sizeof(server_addr));
    listen(listen_sock, 5);

    printf("TCP control server started on port %d...\n", CONTROL_PORT);

    while (1) {
        client_sock = accept(listen_sock, (struct sockaddr*)&client_addr, &client_len);

        printf("TCP control connection established\n");

        if (client_sock == INVALID_SOCKET) continue;

        int received = recv(client_sock, recv_buf, BUFFER_SIZE - 1, 0);
        if (received > 0) {
            recv_buf[received] = '\0';
            printf("Received: %s\n", recv_buf);

            handle_json_command(recv_buf, response, BUFFER_SIZE);
            send(client_sock, response, (int)strlen(response), 0);
        }
        closesocket(client_sock);
    }

    closesocket(listen_sock);
    WSACleanup();
}
