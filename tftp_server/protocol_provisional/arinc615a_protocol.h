// arinc615a_protocol.h - Protocol definitions for embedded target

/*

Purpose of arinc615a_protocol.h
This header defines binary protocol structures — i.e., how the embedded target internally represents ARINC 615A command packets in C structs.

When is it useful?
It’s useful only if you're exchanging structured binary messages over the TCP control channel — like a real embedded protocol handler might do with tightly packed memory-aligned packets (as in embedded RTOS environments).


 But what are we actually doing right now?
We are not exchanging binary packets.

Instead, the current implementation of the control server uses JSON strings over TCP like:

{"command": "SEND_LSE", "file_name": "fcc1_boot.sre", "memory_address": 0x08000000}

This is what you're parsing with strstr(json, "SEND_LSE"), and it’s far easier for prototyping, simulation, or use on Windows/Linux.

So do you need arinc615a_protocol.h now?
No — not in your current JSON-based TCP control server.

You may want to keep it if:

You plan to switch to binary protocol for efficiency or low-level parsing on target

You want to mirror the same structure in both client and embedded side with strict field formats

But for the current JSON setup, it’s not needed at all.


*/

#ifndef ARINC615A_PROTOCOL_H
#define ARINC615A_PROTOCOL_H

#include <stdint.h>

#define MAX_FILE_NAME_LENGTH 64
#define MAX_DEVICE_ID_LENGTH 16
#define MAX_LSE_ID_LENGTH 32
#define MAX_VERSION_LENGTH 16
#define MAX_MESSAGE_LENGTH 256

// Protocol Command Opcodes
typedef enum {
    CMD_INIT_LOAD = 1,
    CMD_SEND_LSE = 2,
    CMD_VERIFY_LSE = 3,
    CMD_COMMIT_LOAD = 4,
    CMD_ABORT = 5,
    CMD_REPORT_STATUS = 6,
    CMD_GET_DEVICE_INFO = 7
} Arinc615aCommand;

// Command structure - common header
typedef struct {
    uint8_t command;           // One of Arinc615aCommand
} CommandHeader;

// INIT_LOAD structure
typedef struct {
    CommandHeader header;
    char device_id[MAX_DEVICE_ID_LENGTH];
    uint32_t session_id;
} InitLoadCommand;

// SEND_LSE structure
typedef struct {
    CommandHeader header;
    char lse_id[MAX_LSE_ID_LENGTH];
    char version[MAX_VERSION_LENGTH];
    uint32_t memory_address;
    char file_name[MAX_FILE_NAME_LENGTH];
    uint32_t crc32;
} SendLseCommand;

// VERIFY_LSE structure
typedef struct {
    CommandHeader header;
    char lse_id[MAX_LSE_ID_LENGTH];
} VerifyLseCommand;

// COMMIT_LOAD structure
typedef struct {
    CommandHeader header;
    uint32_t session_id;
} CommitLoadCommand;

// ABORT structure
typedef struct {
    CommandHeader header;
    char reason[MAX_MESSAGE_LENGTH];
} AbortCommand;

// GET_DEVICE_INFO has only the header
// REPORT_STATUS has only the header

// Response types
typedef enum {
    RESP_OK = 0,
    RESP_ERROR = 1
} ResponseCode;

typedef struct {
    ResponseCode status;
    char message[MAX_MESSAGE_LENGTH];
} GenericResponse;

#endif // ARINC615A_PROTOCOL_H
