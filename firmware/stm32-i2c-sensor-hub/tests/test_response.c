#include <stdio.h>
#include <string.h>
#include <assert.h>

#include "utils/response_builder.h"
#include "utils/checksum.h"

int main(void) {
    uint8_t buf[64];
    size_t out_len;

    // ---------- 1) Test BuildStatus (no payload) ----------
    memset(buf, 0xFF, sizeof(buf));
    out_len = ResponseBuilder_BuildStatus(buf, /*addr7=*/0x12, /*cmd=*/CMD_PING, /*status=*/STATUS_OK);
    // Expected layout:
    // [0]=SOF (0xAA)
    // [1]=BOARD_ID (e.g. 0x05)
    // [2]=addr7   (0x12)
    // [3]=cmd     (CMD_PING)
    // [4]=status  (STATUS_OK)
    // [5]=length  (0)
    // [6]=checksum
    assert(out_len == RESPONSE_HEADER_LENGTH + CHECKSUM_LENGTH);
    assert(buf[0] == SOF_MARKER);
    assert(buf[1] == BOARD_ID);
    assert(buf[2] == 0x12);
    assert(buf[3] == CMD_PING);
    assert(buf[4] == STATUS_OK);
    assert(buf[5] == 0);  // no payload
    // Checksum should be XOR of bytes [1..5]
    {
        uint8_t chk = xor_checksum(buf, 1, 5);
        assert(buf[6] == chk);
    }

    // ---------- 2) Test BuildFieldResponse (1-byte payload) ----------
    memset(buf, 0x00, sizeof(buf));
    out_len = ResponseBuilder_BuildFieldResponse(
        buf,
        /*addr7=*/0x34,
        /*cmd=*/CMD_LIST_SENSORS,
        /*value=*/0x77
    );
    // Layout:
    // [0]=SOF
    // [1]=BOARD_ID
    // [2]=addr7 (0x34)
    // [3]=cmd (CMD_LIST_SENSORS)
    // [4]=status (implicitly STATUS_OK in builder)
    // [5]=length=1
    // [6]=field_value (0x77)
    // [7]=checksum
    assert(out_len == RESPONSE_HEADER_LENGTH + 1 + CHECKSUM_LENGTH);
    assert(buf[0] == SOF_MARKER);
    assert(buf[1] == BOARD_ID);
    assert(buf[2] == 0x34);
    assert(buf[3] == CMD_LIST_SENSORS);
    assert(buf[4] == STATUS_OK);
    assert(buf[5] == 1);
    assert(buf[6] == 0x77);
    {
        uint8_t chk = xor_checksum(buf, 1, 6);
        assert(buf[7] == chk);
    }

    // ---------- 3) Test BuildGetConfig (4-byte payload) ----------
    memset(buf, 0, sizeof(buf));
    out_len = ResponseBuilder_BuildGetConfig(
        buf,
        /*addr7=*/0x56,
        /*period=*/0x12,
        /*gain=*/0x34,
        /*range=*/0x56,
        /*calib_lsb=*/0x78
    );
    // Header: [0]=SOF, [1]=BOARD_ID, [2]=0x56, [3]=CMD_GET_CONFIG, [4]=STATUS_OK, [5]=4
    // Payload: [6]=0x12, [7]=0x34, [8]=0x56, [9]=0x78
    // Checksum: at index 10
    assert(out_len == RESPONSE_HEADER_LENGTH + 4 + CHECKSUM_LENGTH);
    assert(buf[2] == 0x56);
    assert(buf[3] == CMD_GET_CONFIG);
    assert(buf[5] == 4);
    assert(buf[6] == 0x12);
    assert(buf[7] == 0x34);
    assert(buf[8] == 0x56);
    assert(buf[9] == 0x78);
    {
        uint8_t chk = xor_checksum(buf, 1, 9);
        assert(buf[10] == chk);
    }

    // ---------- 4) Test BuildList (2 entries) ----------
    // Prepare two entries: type=0xA1, addr7=0x10; and type=0xB2, addr7=0x20.
    SM_Entry_t entries[2] = {
        { .type_code = 0xA1, .addr7 = 0x10 },
        { .type_code = 0xB2, .addr7 = 0x20 },
    };
    memset(buf, 0, sizeof(buf));
    out_len = ResponseBuilder_BuildList(
        buf,
        /*addr7=*/0x12,
        /*cmd=*/CMD_LIST_SENSORS,
        /*status=*/STATUS_OK,
        entries,
        /*count=*/2
    );
    // Header: [2]=0x12, [3]=CMD_LIST_SENSORS, [4]=STATUS_OK, [5]=payload_len=4
    // Payload (4 bytes): [6]=0xA1,[7]=0x10,[8]=0xB2,[9]=0x20
    // Checksum: at [10]
    assert(buf[5] == 4);
    assert(buf[6] == 0xA1);
    assert(buf[7] == 0x10);
    assert(buf[8] == 0xB2);
    assert(buf[9] == 0x20);
    {
        uint8_t chk = xor_checksum(buf, 1, 9);
        assert(buf[10] == chk);
    }

    // ---------- 5) Test BuildSamples (1 sample with 3 data bytes) ----------
    SensorSample_t sample;
    sample.tick = 0x11223344;     // arbitrary
    sample.len  = 3;
    sample.buf[0] = 0x01;
    sample.buf[1] = 0x02;
    sample.buf[2] = 0x03;

    memset(buf, 0, sizeof(buf));
    out_len = ResponseBuilder_BuildSamples(
        buf,
        /*addr7=*/0x12,
        &sample,
        /*count=*/1,
        /*sample_size=*/SENSOR_MAX_PAYLOAD
    );
    // Header: [2]=0x12, [3]=CMD_READ_SAMPLES, [4]=STATUS_OK, [5]=payload_len=7 (4 tick + 3 data)
    // Tick (big-endian): [6]=0x11,[7]=0x22,[8]=0x33,[9]=0x44
    // Data: [10]=0x01,[11]=0x02,[12]=0x03
    // Checksum: at [13]
    assert(buf[5] == 7);
    assert(buf[6] == 0x11);
    assert(buf[7] == 0x22);
    assert(buf[8] == 0x33);
    assert(buf[9] == 0x44);
    assert(buf[10] == 0x01);
    assert(buf[11] == 0x02);
    assert(buf[12] == 0x03);
    {
        uint8_t chk = xor_checksum(buf, 1, 12);
        assert(buf[13] == chk);
    }

    // ---------- 6) Test BuildConfigValues (3 values) ----------
    uint8_t vals[3] = { 0xAA, 0xBB, 0xCC };
    memset(buf, 0, sizeof(buf));
    out_len = ResponseBuilder_BuildConfigValues(
        buf,
        /*addr7=*/0x12,
        vals,
        /*count=*/3
    );
    // Header: [2]=0x12,[3]=CMD_GET_CONFIG,[4]=STATUS_OK,[5]=3
    // Payload: [6]=0xAA,[7]=0xBB,[8]=0xCC
    // Checksum: [9]
    assert(buf[5] == 3);
    assert(buf[6] == 0xAA);
    assert(buf[7] == 0xBB);
    assert(buf[8] == 0xCC);
    {
        uint8_t chk = xor_checksum(buf, 1, 8);
        assert(buf[9] == chk);
    }

    printf("All response_builder tests passed!\n");
    return 0;
}
