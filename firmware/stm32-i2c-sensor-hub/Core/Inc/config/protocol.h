/* Auto-generated from protocol.json; do not edit! */
#pragma once
#include <stdint.h>
#include <stddef.h>

// Simple #defines
#define SOF_MARKER           170
#define TICK_BYTES           4
#define QUEUE_DEPTH          10
#define CHECKSUM_LENGTH      1

#define RESPONSE_HEADER_LENGTH  offsetof(RESPONSE_HEADER_t, length) + 1
#define CMD_FRAME_SIZE sizeof(COMMAND_t)

// Status codes
#define STATUS_OK            0
#define STATUS_ERROR         1
#define STATUS_NOT_FOUND     2
#define STATUS_UNKNOWN_CMD   3

// Command codes
#define CMD_READ_SAMPLES     0
#define CMD_ADD_SENSOR       1
#define CMD_REMOVE_SENSOR    2
#define CMD_SET_PERIOD       3
#define CMD_SET_MASK         4
#define CMD_SET_GAIN         5
#define CMD_SET_RANGE        6
#define CMD_SET_CAL          7
#define CMD_PING             8
#define CMD_LIST_SENSORS     9
#define CMD_GET_PERIOD       10
#define CMD_GET_GAIN         11
#define CMD_GET_RANGE        12
#define CMD_GET_CAL          13
#define CMD_GET_CONFIG       14
#define CMD_SET_PAYLOAD_MASK 15
#define CMD_GET_PAYLOAD_MASK 16

// Sensor type codes
#define SENSOR_TYPE_INA219   1

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
