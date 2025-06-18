#include "flash_driver.h"
#include "crc32.h"
#include <stdio.h>

static FILE* fout = NULL;
static uint32_t crc = 0;
static int total_bytes = 0;

void flash_open_file(const char* filename) {
    fout = fopen(filename, "wb");
    crc = 0;
    total_bytes = 0;
}

void flash_write(const uint8_t* data, int len) {
    if (!fout) return;
    fwrite(data, 1, len, fout);
    crc = crc32(crc, data, len);
    total_bytes += len;
}

void flash_close(void) {
    if (fout) {
        fclose(fout);
        fout = NULL;
        printf("Flash write complete (%d bytes)\n", total_bytes);
        printf("Final CRC32: 0x%08X\n", crc);
    }
}
