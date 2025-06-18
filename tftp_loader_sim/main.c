#include <stdio.h>
#include "tftp_server.h"

int main() {
    printf("TFTP loader (modular) started...\n");
    handle_tftp();  // infinite loop inside
    return 0;
}
