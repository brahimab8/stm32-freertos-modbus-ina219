#include "utils/response_builder.h"
#include "utils/checksum.h"
#include "config/config.h"
#include "config/protocol.h"
#include <string.h>

size_t ResponseBuilder_BuildStatus(
    uint8_t *outbuf,
    uint8_t  addr7,
    uint8_t  cmd,
    uint8_t  status
) {
    if (!outbuf) return 0;
    RESPONSE_HEADER_t hdr = {
        .sof      = SOF_MARKER,
        .board_id = BOARD_ID,
        .addr7    = addr7,
        .cmd      = cmd,
        .status   = status,
        .length   = 0
    };
    memcpy(outbuf, &hdr, RESPONSE_HEADER_LENGTH);
    uint8_t chk = xor_checksum(outbuf, 1, RESPONSE_HEADER_LENGTH - 1);
    outbuf[RESPONSE_HEADER_LENGTH] = chk;
    return RESPONSE_HEADER_LENGTH + CHECKSUM_LENGTH;
}

size_t ResponseBuilder_BuildSamples(
    uint8_t *outbuf,
    uint8_t  addr7,
    const SensorSample_t *samples,
    uint32_t count,
    uint8_t  sample_size
) {
    if (!outbuf || !samples || count == 0 || sample_size == 0) return 0;

    uint32_t payload_len = count * (4 + sample_size);
    size_t   total_len   = RESPONSE_HEADER_LENGTH + payload_len + CHECKSUM_LENGTH;

    RESPONSE_HEADER_t hdr = {
        .sof      = SOF_MARKER,
        .board_id = BOARD_ID,
        .addr7    = addr7,
        .cmd      = CMD_READ_SAMPLES,
        .status   = STATUS_OK,
        .length   = (uint8_t)payload_len
    };
    memcpy(outbuf, &hdr, RESPONSE_HEADER_LENGTH);

    size_t off = RESPONSE_HEADER_LENGTH;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t tick = samples[i].tick;
        outbuf[off++] = tick >> 24;
        outbuf[off++] = tick >> 16;
        outbuf[off++] = tick >>  8;
        outbuf[off++] = tick & 0xFF;
        memcpy(&outbuf[off], samples[i].buf, sample_size);
        off += sample_size;
    }

    uint8_t chk = xor_checksum(outbuf, 1, (int)(total_len - 2));
    outbuf[total_len - 1] = chk;
    return total_len;
}

size_t ResponseBuilder_BuildList(
    uint8_t       *outbuf,
    uint8_t        addr7,
    uint8_t        cmd,
    uint8_t        status,
    const uint8_t *addrs,
    uint8_t        count
) {
    if (!outbuf || (count > SM_MAX_SENSORS)) return 0;

    // total payload length = 1 (count) + count addresses
    uint8_t payload_len = 1 + count;
    size_t  total_len   = RESPONSE_HEADER_LENGTH + payload_len + CHECKSUM_LENGTH;

    // fill header
    RESPONSE_HEADER_t hdr = {
        .sof      = SOF_MARKER,
        .board_id = BOARD_ID,
        .addr7    = addr7,
        .cmd      = cmd,
        .status   = status,
        .length   = payload_len
    };
    memcpy(outbuf, &hdr, RESPONSE_HEADER_LENGTH);

    // payload
    size_t off = RESPONSE_HEADER_LENGTH;
    outbuf[off++] = count;
    if (count) {
        memcpy(&outbuf[off], addrs, count);
        off += count;
    }

    // checksum over bytes [1 .. total_len-2]
    uint8_t chk = xor_checksum(outbuf, 1, (int)(total_len - 2));
    outbuf[total_len - 1] = chk;

    return total_len;
}
