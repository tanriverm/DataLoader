#ifndef UDP_WIN_H
#define UDP_WIN_H

#include <stdint.h>

typedef struct {
    int sockfd;
} UdpSocket;

typedef struct {
    char ip[64];
    uint16_t port;
} UdpAddress;

void udp_open_server(UdpSocket* sock, int port);
int  udp_recv(UdpSocket* sock, uint8_t* buffer, int buflen, UdpAddress* addr);
void udp_send_ack(UdpSocket* sock, UdpAddress* addr, uint16_t block);
void udp_close(UdpSocket* sock);

#endif
