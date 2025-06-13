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
#define CMD_FRAME_SIZE          sizeof(COMMAND_t)

 // Status codes
#define STATUS_OK            0
#define STATUS_ERROR         1
#define STATUS_NOT_FOUND     2
#define STATUS_UNKNOWN_CMD   3

 // Command codes
#define CMD_READ_SAMPLES     0
#define CMD_ADD_SENSOR       1
#define CMD_REMOVE_SENSOR    2
#define CMD_PING             3
#define CMD_LIST_SENSORS     4
#define CMD_SET_PAYLOAD_MASK 5
#define CMD_GET_PAYLOAD_MASK 6
#define CMD_GET_CONFIG       7
#define CMD_SET_PERIOD       20
#define CMD_SET_GAIN         21
#define CMD_SET_RANGE        22
#define CMD_SET_CAL          23
#define CMD_SET_SHUNT        24
#define CMD_SET_CURRENT_LSB  25
#define CMD_GET_PERIOD       30
#define CMD_GET_GAIN         31
#define CMD_GET_RANGE        32
#define CMD_GET_CAL          33
#define CMD_GET_SHUNT        34
#define CMD_GET_CURRENT_LSB  35

 // Command ID ranges
#define CMD_CONFIG_SETTERS_START 20
#define CMD_CONFIG_SETTERS_END   29
#define CMD_CONFIG_GETTERS_START 30
#define CMD_CONFIG_GETTERS_END   39

 // Sensor type codes
#define SENSOR_TYPE_INA219     1

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

