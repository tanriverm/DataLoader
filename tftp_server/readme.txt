| File             | Purpose                                     |
| ---------------- | ------------------------------------------- |
| `main.c`         | Main function for the TFTP server simulator |
| `udp.h`          | UDP socket abstraction header               |
| `udp_win.c`      | Windows-specific UDP socket implementation  |
| `tftp_server.h`  | TFTP server interface                       |
| `tftp_server.c`  | TFTP WRQ + DATA handling                    |
| `flash_driver.h` | Interface for flash simulation              |
| `flash_driver.c` | Writes to a `.bin` file as flash simulation |
| `test_app.sre`   | Example binary file for testing             |



tftp_loader/
├── main.c              --> Entry point (sets up TFTP loop)
├── tftp_server.c/h     --> TFTP protocol logic and state machine
├── flash_driver.c/h    --> Simulates writing to flash and computes CRC32
├── crc32.c/h           --> CRC32 implementation
├── udp_win.c/h         --> UDP wrapper (for simulation on Windows/Linux)
