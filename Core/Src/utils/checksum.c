#include "utils/checksum.h"

uint8_t xor_checksum(const uint8_t *buf, size_t start, size_t len) {
    uint8_t c = 0;
    for (size_t i = 0; i < len; i++) c ^= buf[start + i];
    return c;
}
