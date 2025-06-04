#ifndef RESPONSE_BUILDER_H
#define RESPONSE_BUILDER_H

#include <stdint.h>
#include <stddef.h>

/*
   RESPONSE_HEADER_t is defined in config/protocol.h.  It looks roughly like:

   typedef struct {
       uint8_t sof;       // SOF_MARKER
       uint8_t board_id;  // BOARD_ID
       uint8_t addr7;     // target address from command
       uint8_t cmd;       // opcode
       uint8_t status;    // STATUS_OK, etc.
       uint8_t length;    // payload‐length in bytes
   } RESPONSE_HEADER_t;

   RESPONSE_HEADER_LENGTH and CHECKSUM_LENGTH are also defined in config/protocol.h:
     #define RESPONSE_HEADER_LENGTH  6   // sizeof(RESPONSE_HEADER_t)
     #define CHECKSUM_LENGTH         1
   and
     #define SOF_MARKER  0xAA        // for example
     #define BOARD_ID    0x05        // your board’s ID
*/

#include "config/protocol.h"   // for RESPONSE_HEADER_t, RESPONSE_HEADER_LENGTH, CHECKSUM_LENGTH
#include "task/sensor_manager.h" // for SensorSample_t, SM_Entry_t, etc.

/**
 * @brief Build a “status‐only” frame (no payload).  Equivalent to:
 *   [SOF][board_id][addr7][cmd][status][length=0][checksum]
 *
 * @param outbuf   Must be at least RESPONSE_HEADER_LENGTH + CHECKSUM_LENGTH bytes long.
 * @param addr7    The 7‐bit I²C address of the board being responded to.
 * @param cmd      The original command opcode (e.g. CMD_PING, CMD_ADD_SENSOR, etc.).
 * @param status   STATUS_OK, STATUS_ERROR, STATUS_NOT_FOUND, etc.
 * @return total number of bytes written (should be RESPONSE_HEADER_LENGTH + 1), or 0 on failure.
 */
size_t ResponseBuilder_BuildStatus(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status
);

/**
 * @brief Build a “field response” that has exactly one data byte of payload.
 * Used by CMD_GET_GAIN, CMD_GET_RANGE, CMD_GET_CAL, CMD_GET_PERIOD, CMD_GET_PAYLOAD_MASK, etc.
 *
 * Frame format:
 *   [SOF][board_id][addr7][cmd][status][length=1]
 *   [ payload‐byte ]
 *   [ checksum ]
 *
 * @param outbuf       Must be at least RESPONSE_HEADER_LENGTH + 1 + CHECKSUM_LENGTH bytes.
 * @param addr7        The 7‐bit I²C address of the board being responded to.
 * @param cmd          Which GET_… opcode this is (CMD_GET_GAIN, CMD_GET_RANGE, …).
 * @param field_value  The single‐byte payload value to return.
 * @return total number of bytes written, or 0 on error.
 */
size_t ResponseBuilder_BuildFieldResponse(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  field_value
);

/**
 * @brief Build a “bulk‐config” response for CMD_GET_CONFIG.
 * Payload is exactly 4 bytes: [period_units, gain, range, calib_lsb].
 *
 * Frame format:
 *   [SOF][board_id][addr7][CMD_GET_CONFIG][STATUS_OK][length=4]
 *   [ period_u100 ][ gain ][ range ][ calib_lsb ]
 *   [ checksum ]
 *
 * @param outbuf        Must be at least RESPONSE_HEADER_LENGTH + 4 + CHECKSUM_LENGTH bytes.
 * @param addr7         7‐bit I²C address of target board
 * @param period_u100   period in 100ms units
 * @param gain          last gain code
 * @param range         last range code
 * @param calib_lsb     low byte of calibration register
 * @return total number of bytes written, or 0 on error
 */
size_t ResponseBuilder_BuildGetConfig(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  period_u100,
    uint8_t  gain,
    uint8_t  range,
    uint8_t  calib_lsb
);

/**
 * @brief Build a “list sensors” response.  Each sensor entry is two bytes:
 *   [type_code][addr7], repeated `count` times.
 *
 * Frame format:
 *   [SOF][board_id][addr7][CMD_LIST_SENSORS][status][length=count*2]
 *     for (i=0..count-1):  [ entries[i].type_code ][ entries[i].addr7 ]
 *   [ checksum ]
 *
 * @param outbuf    Must be at least RESPONSE_HEADER_LENGTH + (count*2) + CHECKSUM_LENGTH bytes.
 * @param addr7     The 7‐bit I²C address of the board being responded to.
 * @param cmd       Should be CMD_LIST_SENSORS (just pass it in).
 * @param status    STATUS_OK or STATUS_ERROR.
 * @param entries   Pointer to array of SM_Entry_t (each has type_code and addr7).
 * @param count     Number of sensors (≤ SM_MAX_SENSORS).
 * @return total number of bytes written, or 0 on failure.
 */
size_t ResponseBuilder_BuildList(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status,
    const SM_Entry_t *entries,
    uint8_t  count
);

/**
 * @brief Build a “read‐samples” response.  Each sample is:
 *   [ 4‐byte big‐endian tick ] [ sample_data_bytes… ].
 *
 * Frame format:
 *   [SOF][board_id][addr7][CMD_READ_SAMPLES][STATUS_OK][length=payload_len]
 *     For each sample i:
 *       [ tick (32 bits, big‐endian) ] [ samples[i].buf (samples[i].len bytes) ]
 *   [ checksum ]
 *
 * @param outbuf       Must be at least RESPONSE_HEADER_LENGTH + payload_len + CHECKSUM_LENGTH.
 * @param addr7        7‐bit I²C address of board being responded to
 * @param samples      Pointer to array of SensorSample_t
 * @param count        Number of samples
 * @param sample_size  Maximum size of each sample’s buf (used only to verify `.len` ≤ sample_size)
 * @return total number of bytes written, or 0 on error.
 */
size_t ResponseBuilder_BuildSamples(
    uint8_t *outbuf,
    uint8_t  addr7,
    const SensorSample_t *samples,
    uint32_t count,
    uint8_t  sample_size
);

/**
 * @brief Build a compact CMD_GET_CONFIG response containing config values.
 *
 * Format:
 *   [SOF][board_id][addr7][CMD_GET_CONFIG][STATUS_OK][length=N]
 *   [ values[0] ... values[N-1] ]
 *   [ checksum ]
 *
 * This assumes host and device agree on field order and count.
 *
 * @param outbuf  Output buffer (must be at least 6 + count + 1 bytes)
 * @param addr7   Sensor address (7-bit)
 * @param values  Array of config values
 * @param count   Number of config values
 * @return        Total bytes written to outbuf, or 0 on error
 */
size_t ResponseBuilder_BuildConfigValues(
    uint8_t *outbuf,
    uint8_t addr7,
    const uint8_t *values,
    size_t count
);

#endif // RESPONSE_BUILDER_H
