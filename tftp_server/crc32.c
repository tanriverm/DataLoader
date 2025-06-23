#include "crc32.h"

#define POLYNOMIAL 0xEDB88320

static uint32_t crc_table[256];
static int table_computed = 0;

static void make_crc_table(void) {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int j = 0; j < 8; j++) {
            c = (c & 1) ? (POLYNOMIAL ^ (c >> 1)) : (c >> 1);
        }
        crc_table[i] = c;
    }
    table_computed = 1;
}

uint32_t crc32(uint32_t crc, const uint8_t* buf, size_t len) {
    if (!table_computed) make_crc_table();
    crc = crc ^ 0xFFFFFFFF;
    for (size_t i = 0; i < len; i++) {
        crc = crc_table[(crc ^ buf[i]) & 0xFF] ^ (crc >> 8);
    }
    return crc ^ 0xFFFFFFFF;
}
