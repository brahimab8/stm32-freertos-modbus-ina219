/* Auto-generated from protocol.json; do not edit! */
#pragma once
#include <stdint.h>
#include <stddef.h>

// Simple #defines
#define SOF_MARKER           170
#define STATUS_OK            0
#define STATUS_ERROR         1
#define TICK_BYTES           4
#define QUEUE_DEPTH          10
#define CHECKSUM_LENGTH     1

// Size of response header before the trailing checksum
#define RESPONSE_HEADER_LENGTH  offsetof(RESPONSE_HEADER_t, length) + 1

// Command codes
#define CMD_READ_SAMPLES     0
#define CMD_ADD_SENSOR       1
#define CMD_REMOVE_SENSOR    2
#define CMD_SET_PERIOD       3
#define CMD_SET_MASK         4
#define CMD_SET_GAIN         5
#define CMD_SET_RANGE        6
#define CMD_SET_CAL          7

// Master → node: always 6 bytes
typedef struct {
    uint8_t sof;
    uint8_t board_id;
    uint8_t addr7;
    uint8_t cmd;
    uint8_t param;
    uint8_t checksum;
} COMMAND_t;

// Node → master: 6 + N bytes + Checksum
typedef struct {
    uint8_t sof;
    uint8_t board_id;
    uint8_t addr7;
    uint8_t cmd;
    uint8_t status;
    uint8_t length;
} RESPONSE_HEADER_t;
