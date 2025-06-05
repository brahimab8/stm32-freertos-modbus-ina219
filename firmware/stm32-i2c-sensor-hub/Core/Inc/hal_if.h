#pragma once

#include <stdint.h>

/**
 * @file hal_if.h
 * @brief Hardware Abstraction Layer Interface for I²C communication.
 */

/**
 * @typedef halif_handle_t
 * @brief Opaque handle type for I²C communication.
 *
 * At runtime, this points to an I2C_HandleTypeDef instance (e.g., &hi2c1).
 * In unit tests, the stub implementation returns a dummy non-NULL value.
 */
typedef void *halif_handle_t;

/**
 * @enum halif_status_t
 * @brief Return codes for HAL-IF functions.
 */
typedef enum {
    HALIF_OK    = 0, /**< Operation completed successfully. */
    HALIF_ERROR = 1  /**< Operation encountered an error.       */
} halif_status_t;

/**
 * @brief Initialize an I²C bus and obtain a handle.
 *
 * This function sets up the specified I²C peripheral with the given
 * baud rate and returns an opaque handle to the underlying HAL handle.
 *
 * @param[in] i2c_bus   Identifier of the I²C bus to initialize (e.g., 1 for I2C1).
 * @param[in] baudrate  Communication speed in hertz (e.g., 100000 for 100 kHz).
 *
 * @return On success, returns a non-NULL handle which, in production, points to
 *         the real I2C_HandleTypeDef (e.g., &hi2c1). In test builds, returns
 *         a dummy non-NULL value. If initialization fails, behavior depends on
 *         the underlying HAL implementation (often NULL).
 */
halif_handle_t halif_i2c_init(uint32_t i2c_bus, uint32_t baudrate);

/**
 * @brief Write a sequence of bytes to a device on the I²C bus.
 *
 * In production, this function calls HAL_I2C_Master_Transmit. In unit tests,
 * the stub implementation returns HALIF_OK.
 *
 * @param[in] handle        Opaque handle obtained from halif_i2c_init().
 * @param[in] device_addr   7-bit I²C address of the target device.
 * @param[in] data          Pointer to the buffer containing data to write.
 * @param[in] length        Number of bytes to write from the data buffer.
 * @param[in] timeout_ms    Timeout duration in milliseconds for the operation.
 *
 * @return HALIF_OK on success, or HALIF_ERROR on failure.
 */
halif_status_t halif_i2c_write(
    halif_handle_t handle,
    uint8_t        device_addr,
    const uint8_t *data,
    uint16_t       length,
    uint32_t       timeout_ms
);

/**
 * @brief Read a sequence of bytes from a device on the I²C bus.
 *
 * This function reads `length` bytes from the specified `device_addr` into
 * the provided data buffer. In production, it calls HAL_I2C_Master_Receive;
 * in unit tests, the stub returns HALIF_OK.
 *
 * @param[in]  handle        Opaque handle obtained from halif_i2c_init().
 * @param[in]  device_addr   7-bit I²C address of the target device.
 * @param[out] data          Pointer to the buffer where read data is stored.
 * @param[in]  length        Number of bytes to read into the data buffer.
 * @param[in]  timeout_ms    Timeout duration in milliseconds for the operation.
 *
 * @return HALIF_OK on successful read, or HALIF_ERROR on failure.
 */
halif_status_t halif_i2c_read(
    halif_handle_t handle,
    uint8_t        device_addr,
    uint8_t       *data,
    uint16_t       length,
    uint32_t       timeout_ms
);
