

// main.c - Unified startup for TFTP and TCP control services

#include <stdio.h>
#include <windows.h>
#include <process.h>
#include "tftp_server.h"
#include "tcp_control_server.h"


void tcp_control_server_loop(void* arg);

int main() {
    printf("ARINC 615A Loader (TFTP + Control) started...\n");

    // Start TFTP server
    _beginthread(tftp_server_loop, 0, NULL);

    // Start TCP control server
    _beginthread(tcp_control_server_loop, 0, NULL);

    // Keep main thread alive
    while (1) {
        Sleep(1000);
    }

    return 0;
}
