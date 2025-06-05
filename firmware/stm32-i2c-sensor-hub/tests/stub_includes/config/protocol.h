#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

#define SOF_MARKER             0xAA

// “serialize” constants
#define TICK_BYTES             4
#define QUEUE_DEPTH            10
#define CHECKSUM_LENGTH        1

// When building responses, code uses RESPONSE_HEADER_LENGTH and CMD_FRAME_SIZE.
// We can define RESPONSE_HEADER_LENGTH as 6 (size of RESPONSE_HEADER_t), since that’s
// what the code expects.  CMD_FRAME_SIZE is not used by the response builder stubs, but
// define it anyway.
#define RESPONSE_HEADER_LENGTH 6
#define CMD_FRAME_SIZE         6

// Status codes
#define STATUS_OK            0
#define STATUS_ERROR         1
#define STATUS_NOT_FOUND     2
#define STATUS_UNKNOWN_CMD   3

// Command codes (we only need the ones that the code under test references; add more if needed)
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
#define CMD_GET_PERIOD       30
#define CMD_GET_GAIN         31
#define CMD_GET_RANGE        32
#define CMD_GET_CAL          33

// Command ID ranges (not strictly needed for response builder tests, but harmless)
#define CMD_CONFIG_SETTERS_START     20
#define CMD_CONFIG_SETTERS_END       29
#define CMD_CONFIG_GETTERS_START     30
#define CMD_CONFIG_GETTERS_END       39

// Sensor type codes (only INA219 is used in examples)
#define SENSOR_TYPE_INA219   1

// “Master → node” command frame (not needed by response builder, but define for completeness)
typedef struct {
    uint8_t sof;
    uint8_t board_id;
    uint8_t addr7;
    uint8_t cmd;
    uint8_t param;
    uint8_t checksum;
} COMMAND_t;

// “Node → master” response header (always 6 bytes)
typedef struct {
    uint8_t sof;
    uint8_t board_id;
    uint8_t addr7;
    uint8_t cmd;
    uint8_t status;
    uint8_t length;
} RESPONSE_HEADER_t;

#endif // PROTOCOL_H
