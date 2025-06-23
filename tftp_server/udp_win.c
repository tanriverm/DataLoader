#include "udp_win.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>

#pragma comment(lib, "ws2_32.lib")

static struct sockaddr_in client_addr;
static int winsock_initialized = 0;

void udp_open_server(UdpSocket* sock, int port) {
    if (!winsock_initialized) {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            printf("WSAStartup failed!\n");
            return;
        }
        winsock_initialized = 1;
    }

    sock->sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock->sockfd == INVALID_SOCKET) {
        printf("Failed to create socket\n");
        return;
    }

    struct sockaddr_in server;
    server.sin_family = AF_INET;
    server.sin_port = htons(port);
    server.sin_addr.s_addr = INADDR_ANY;

    if (bind(sock->sockfd, (struct sockaddr*)&server, sizeof(server)) == SOCKET_ERROR) {
        printf("Bind failed\n");
        closesocket(sock->sockfd);
        return;
    }

    printf("UDP server started on port %d\n", port);
}

int udp_recv(UdpSocket* sock, uint8_t* buffer, int buflen, UdpAddress* addr) {
    int client_len = sizeof(client_addr);
    int received = recvfrom(sock->sockfd, (char*)buffer, buflen, 0,
        (struct sockaddr*)&client_addr, &client_len);

    if (received == SOCKET_ERROR) return -1;

    if (addr) {
        inet_ntop(AF_INET, &client_addr.sin_addr, addr->ip, sizeof(addr->ip));
        addr->port = ntohs(client_addr.sin_port);
    }

    return received;
}

void udp_send_ack(UdpSocket* sock, UdpAddress* addr, uint16_t block) {
    uint8_t ack[4] = { 0, 4, (block >> 8), (block & 0xFF) };
    sendto(sock->sockfd, (const char*)ack, 4, 0,
        (struct sockaddr*)&client_addr, sizeof(client_addr));
}

void udp_close(UdpSocket* sock) {
    closesocket(sock->sockfd);
    if (winsock_initialized) {
        WSACleanup();
        winsock_initialized = 0;
    }
}
