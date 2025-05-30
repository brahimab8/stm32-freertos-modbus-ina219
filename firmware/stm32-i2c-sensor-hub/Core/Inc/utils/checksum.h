#pragma once
#include <stdint.h>
#include <stddef.h>

uint8_t xor_checksum(const uint8_t *buf, size_t start, size_t len);
