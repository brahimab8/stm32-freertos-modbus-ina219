#include "utils/response_builder.h"
#include "utils/checksum.h"       // for xor_checksum( buf, start_index, end_index )
#include "config/protocol.h"      // for RESPONSE_HEADER_t, RESPONSE_HEADER_LENGTH, CHECKSUM_LENGTH, SOF_MARKER
#include "config/config.h"      // for BOARD_ID
#include <string.h>               // for memcpy

/**
 * @brief Central helper: write the 6‐byte header [SOF][board_id][addr7][cmd][status][length],
 *        and return the pointer offset where the payload should start.
 *
 * @param outbuf    Buffer to fill (must be at least RESPONSE_HEADER_LENGTH + ...).
 * @param addr7     7‐bit I²C address of the board being responded to.
 * @param cmd       The command opcode (CMD_PING, CMD_LIST_SENSORS, CMD_READ_SAMPLES, etc.).
 * @param status    STATUS_OK, STATUS_ERROR, ...
 * @param length    The number of payload bytes that will follow.
 * @return the offset into outbuf where the payload should be written (== RESPONSE_HEADER_LENGTH),
 *         or 0 on error (e.g. outbuf == NULL).
 */
static size_t Build_Header(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status,
    uint8_t  length
) {
    if (!outbuf) {
        return 0;
    }

    // Pack into a local header struct
    RESPONSE_HEADER_t hdr = {
        .sof      = SOF_MARKER,  // e.g. 0xAA
        .board_id = BOARD_ID,    // e.g. 0x05
        .addr7    = addr7,
        .cmd      = cmd,
        .status   = status,
        .length   = length
    };

    // Copy exactly RESPONSE_HEADER_LENGTH bytes into outbuf
    memcpy(outbuf, &hdr, RESPONSE_HEADER_LENGTH);

    // Return offset where payload begins
    return RESPONSE_HEADER_LENGTH;
}

/**
 * @brief Append an XOR checksum over all bytes from index `start` up to `end - 1`, and place it at outbuf[end].
 *
 * @param outbuf    Buffer in which header+payload are already written.
 * @param start     Starting index in `outbuf` to begin XOR (usually 1 to skip SOF).
 * @param end       The index *of the checksum byte* (so we XOR bytes [start .. end-1] and write at outbuf[end]).
 * @return none
 */
static void Build_Checksum(uint8_t *outbuf, size_t start, size_t end) {
    uint8_t chk = xor_checksum(outbuf, (int)start, (int)(end - 1));
    outbuf[end] = chk;
}


/*--------------------------------------------------------------------
 * 1) Status‐only response:
 *      [SOF][board_id][addr7][cmd][status][length=0]
 *      [ checksum ]
 *-------------------------------------------------------------------*/
size_t ResponseBuilder_BuildStatus(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status
) {
    // Header (length = 0)
    size_t payload_off = Build_Header(outbuf, addr7, cmd, status, 0);
    if (payload_off == 0) {
        return 0;
    }

    // Compute checksum over bytes [1 .. (RESPONSE_HEADER_LENGTH-1)], write at index RESPONSE_HEADER_LENGTH
    Build_Checksum(outbuf, 1, RESPONSE_HEADER_LENGTH);

    // Total length = header + checksum
    return RESPONSE_HEADER_LENGTH + CHECKSUM_LENGTH;
}


/*--------------------------------------------------------------------
 * 2) One‐byte field response:
 *      [SOF][board_id][addr7][cmd][status][length=1]
 *      [ field_value ]
 *      [ checksum ]
 *-------------------------------------------------------------------*/
size_t ResponseBuilder_BuildFieldResponse(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  field_value
) {
    // Header (length = 1)
    size_t payload_off = Build_Header(outbuf, addr7, cmd, STATUS_OK, 1);
    if (payload_off == 0) {
        return 0;
    }

    // Place the single‐byte payload
    outbuf[payload_off] = field_value;

    // Checksum is at index (payload_off + 1)
    size_t checksum_index = payload_off + 1;
    Build_Checksum(outbuf, 1, checksum_index);

    // Total length
    return checksum_index + 1;
}


/*--------------------------------------------------------------------
 * 3) Bulk‐config response (4 bytes: [period_u100][gain][range][calib_lsb])
 *      [SOF][board_id][addr7][CMD_GET_CONFIG][STATUS_OK][length=4]
 *      [ period_u100 ][ gain ][ range ][ calib_lsb ]
 *      [ checksum ]
 *-------------------------------------------------------------------*/
size_t ResponseBuilder_BuildGetConfig(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  period_u100,
    uint8_t  gain,
    uint8_t  range,
    uint8_t  calib_lsb
) {
    // Header (length = 4)
    size_t payload_off = Build_Header(outbuf, addr7, CMD_GET_CONFIG, STATUS_OK, 4);
    if (payload_off == 0) {
        return 0;
    }

    // Append the 4‐byte payload
    outbuf[payload_off + 0] = period_u100;
    outbuf[payload_off + 1] = gain;
    outbuf[payload_off + 2] = range;
    outbuf[payload_off + 3] = calib_lsb;

    // Checksum at index payload_off + 4
    size_t checksum_index = payload_off + 4;
    Build_Checksum(outbuf, 1, checksum_index);

    // Total length = header (6) + 4 payload + 1 checksum = 11
    return checksum_index + 1;
}


/*--------------------------------------------------------------------
 * 4) List‐sensors response (each entry is two bytes [type_code][addr7])
 *      [SOF][board_id][addr7][CMD_LIST_SENSORS][status][length=N*2]
 *        for i in 0..N-1:
 *          [ entries[i].type_code ]
 *          [ entries[i].addr7 ]
 *      [ checksum ]
 *-------------------------------------------------------------------*/
size_t ResponseBuilder_BuildList(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status,
    const SM_Entry_t *entries,
    uint8_t  count
) {
    if (!outbuf || !entries || count == 0 || count > SM_MAX_SENSORS) {
        return 0;
    }
    uint8_t payload_len = (uint8_t)(count * 2);

    // Header
    size_t payload_off = Build_Header(outbuf, addr7, cmd, status, payload_len);
    if (payload_off == 0) {
        return 0;
    }

    // Fill payload
    size_t idx = payload_off;
    for (uint8_t i = 0; i < count; ++i) {
        outbuf[idx++] = entries[i].type_code;
        outbuf[idx++] = entries[i].addr7;
    }

    // Checksum at idx
    size_t checksum_index = idx;
    Build_Checksum(outbuf, 1, checksum_index);

    return checksum_index + 1;
}


/*--------------------------------------------------------------------
 * 5) Read‐samples response:
 *      [SOF][board_id][addr7][CMD_READ_SAMPLES][STATUS_OK][length=payload_len]
 *        for each sample i:
 *          [ tick (4 bytes big‐endian) ]
 *          [ samples[i].buf (samples[i].len bytes) ]
 *      [ checksum ]
 *
 * Each SensorSample_t is defined like:
 *   typedef struct {
 *     uint32_t tick;       // OS tick at read time
 *     uint8_t  len;        // number of data bytes in buf[]
 *     uint8_t  buf[SENSOR_MAX_PAYLOAD];
 *   } SensorSample_t;
 *-------------------------------------------------------------------*/
size_t ResponseBuilder_BuildSamples(
    uint8_t *outbuf,
    uint8_t  addr7,
    const SensorSample_t *samples,
    uint32_t count,
    uint8_t  sample_size
) {
    if (!outbuf || !samples || count == 0 || sample_size == 0) {
        return 0;
    }

    // Compute total payload length: sum of (4 + len) for each sample
    uint32_t payload_len = 0;
    for (uint32_t i = 0; i < count; ++i) {
        if (samples[i].len > sample_size) {
            // sample too large
            return 0;
        }
        payload_len += 4 + samples[i].len;
    }
    if (payload_len > 0xFF) {
        // length field is 1 byte, so max is 255
        return 0;
    }

    // Header (length = payload_len)
    size_t payload_off = Build_Header(outbuf, addr7, CMD_READ_SAMPLES, STATUS_OK, (uint8_t)payload_len);
    if (payload_off == 0) {
        return 0;
    }

    // Write each sample’s 32-bit tick (big‐endian) + its data bytes
    size_t idx = payload_off;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t tick = samples[i].tick;
        outbuf[idx++] = (uint8_t)((tick >> 24) & 0xFF);
        outbuf[idx++] = (uint8_t)((tick >> 16) & 0xFF);
        outbuf[idx++] = (uint8_t)((tick >> 8) & 0xFF);
        outbuf[idx++] = (uint8_t)( tick        & 0xFF);

        // Copy the data payload
        memcpy(&outbuf[idx], samples[i].buf, samples[i].len);
        idx += samples[i].len;
    }

    // Checksum at idx
    size_t checksum_index = idx;
    Build_Checksum(outbuf, 1, checksum_index);

    return checksum_index + 1;
}
