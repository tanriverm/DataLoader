#include "udp_win.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define TFTP_PORT 69
#define BLOCK_SIZE 512
#define MAX_PACKET_SIZE (BLOCK_SIZE + 4)

#define OPCODE_RRQ   1
#define OPCODE_WRQ   2
#define OPCODE_DATA  3
#define OPCODE_ACK   4
#define OPCODE_ERROR 5
#define OPCODE_CRC   0x10

typedef enum {
    STATE_IDLE,
    STATE_RECEIVING,
    STATE_COMPLETED
} ServerState;

static ServerState current_state = STATE_IDLE;
static FILE* output_file = NULL;
static uint16_t expected_block = 1;
static uint32_t calculated_crc = 0;

void handle_tftp(void) {
    uint8_t packet[MAX_PACKET_SIZE];
    UdpAddress client_addr;
    UdpSocket sock;

    udp_open_server(&sock, 69);

    while (1) {
        int recv_len = udp_recv(&sock, packet, MAX_PACKET_SIZE, &client_addr);
        if (recv_len < 4) continue;

        uint16_t opcode = (packet[0] << 8) | packet[1];
        uint16_t block = (packet[2] << 8) | packet[3];

        if (opcode == OPCODE_WRQ && current_state == STATE_IDLE) {  // WRQ
            const char* filename = (const char*)&packet[2];
            printf("WRQ for file: %s\n", filename);
            output_file = fopen("received.sre", "wb");
            if (!output_file) {
                printf("Cannot open output file\n");
                continue;
            }
            current_state = STATE_RECEIVING;
            expected_block = 1;
            calculated_crc = 0;
            udp_send_ack(&sock, &client_addr, 0);  // ACK(0)
        }
        else if (opcode == OPCODE_DATA && current_state == STATE_RECEIVING) {  // DATA
            if (block == expected_block) {
                int data_len = recv_len - 4;
                fwrite(&packet[4], 1, data_len, output_file);
                calculated_crc = crc32(calculated_crc, &packet[4], data_len);
                udp_send_ack(&sock, &client_addr, block);
                printf("Received DATA block %d (%d bytes)\n", block, data_len);
                expected_block++;

            }

        }
        else if (opcode == 0x10 && current_state == STATE_RECEIVING) {
            if (recv_len >= 6) {
                uint32_t received_crc = (packet[2] << 24) |
                    (packet[3] << 16) |
                    (packet[4] << 8) |
                    (packet[5]);

                printf(" Received CRC32 from client: 0x%08X\n", received_crc);
                printf(" Calculated CRC32 : 0x% 08X\n", calculated_crc);

                // Compare with locally computed CRC
                if (received_crc == calculated_crc) {
                    printf("CRC check passed\n");
                }
                else {
                    printf("CRC check failed! Expected: 0x%08X\n", calculated_crc);
                }
            }
            else {
                printf("Invalid CRC packet received\n");
            }

            printf("End of transfer, closing file\n");

            // End of transfer
            fclose(output_file);
            output_file = NULL;
            current_state = STATE_COMPLETED;
        }
    }
}
