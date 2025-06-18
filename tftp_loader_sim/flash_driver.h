#ifndef FLASH_DRIVER_H
#define FLASH_DRIVER_H

#include <stdint.h>

void flash_open_file(const char* filename);
void flash_write(const uint8_t* data, int len);
void flash_close(void);

#endif
