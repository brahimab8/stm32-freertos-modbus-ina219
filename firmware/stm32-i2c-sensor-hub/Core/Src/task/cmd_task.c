#include "task/cmd_task.h"
#include "task/sensor_manager.h"
#include "config/config.h"
#include "config/protocol.h"
#include "utils/response_builder.h"

extern UART_HandleTypeDef huart1;

static TaskHandle_t cmdTaskHandle = NULL;
QueueHandle_t cmdQueue = NULL;

// MAX_PACKET_SIZE to worst-case (header + payload + checksum)
#define MAX_PACKET_SIZE  (RESPONSE_HEADER_LENGTH + (QUEUE_DEPTH * (4 + SENSOR_MAX_PAYLOAD)) + CHECKSUM_LENGTH)
static uint8_t txbuf[MAX_PACKET_SIZE];

/**
 * @brief Send a status‐only response.
 *
 * @param cmd    Pointer to the original command frame (for addr7 and cmd fields)
 * @param status STATUS_OK, STATUS_ERROR, etc.
 */
static void send_status_response(const COMMAND_t *cmd, uint8_t status) {
    size_t len = ResponseBuilder_BuildStatus(txbuf, cmd->addr7, cmd->cmd, status);
    if (len > 0) {
        HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
    }
}

void CommandTask(void *argument) {
    SensorManager_t *mgr = (SensorManager_t *)argument;
    cmdTaskHandle = xTaskGetCurrentTaskHandle();
    COMMAND_t cmd;

    for (;;) {
        if (xQueueReceive(cmdQueue, &cmd, portMAX_DELAY) != pdPASS) {
            continue;
        }

        switch (cmd.cmd) {

            case CMD_PING: {
                send_status_response(&cmd, STATUS_OK);
                break;
            }

            case CMD_LIST_SENSORS: {
                SM_Entry_t list_entries[SM_MAX_SENSORS];
                uint8_t   n = SensorManager_List(
                    mgr,
                    list_entries,
                    SM_MAX_SENSORS
                );

                size_t len = ResponseBuilder_BuildList(
                    txbuf,
                    cmd.addr7,
                    CMD_LIST_SENSORS,
                    STATUS_OK,
                    list_entries,
                    n
                );

                if (len > 0) {
                    HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                } else {
                    send_status_response(&cmd, STATUS_ERROR);
                }
                break;
            }

            case CMD_READ_SAMPLES: {
                SensorTaskHandle_t *task = SensorManager_GetTask(mgr, cmd.addr7);
                if (!task) {
                    send_status_response(&cmd, STATUS_NOT_FOUND);
                } else {
                    SensorSample_t samples[QUEUE_DEPTH];
                    uint8_t ssize = SensorTask_GetSampleSize(task);

                    uint32_t count = 0;
                    HAL_StatusTypeDef st = SensorTask_ReadSamples(task, samples, QUEUE_DEPTH, &count);
                    if (st == HAL_OK && count > 0) {
                        size_t len = ResponseBuilder_BuildSamples(
                            txbuf,
                            cmd.addr7,
                            samples,
                            count,
                            ssize
                        );
                        if (len > 0) {
                            HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                        } else {
                            send_status_response(&cmd, STATUS_ERROR);
                        }
                    } else {
                        send_status_response(&cmd, STATUS_ERROR);
                    }
                }
                break;
            }

            case CMD_ADD_SENSOR: {
                const SensorDriverInfo_t *info = SensorRegistry_Find(cmd.param);
                uint32_t period = (info && info->get_default_period_ms)
                                    ? info->get_default_period_ms()
                                    : 500;  // fallback

                uint8_t status = SensorManager_AddByType(
                    mgr, cmd.param, cmd.addr7, period
                );
                send_status_response(&cmd, status);
                break;
            }

            case CMD_REMOVE_SENSOR: {
                uint8_t status = SensorManager_Remove(mgr, cmd.addr7);
                send_status_response(&cmd, status);
                break;
            }

            case CMD_SET_PAYLOAD_MASK: {
                uint8_t status = SensorManager_Configure(
                    mgr,
                    cmd.addr7,
                    CMD_SET_PAYLOAD_MASK,
                    cmd.param
                );
                if (status == SM_OK) {
                    SensorTaskHandle_t *task = SensorManager_GetTask(mgr, cmd.addr7);
                    if (task) {
                        SensorTask_Flush(task);
                    }
                }
                send_status_response(&cmd, status);
                break;
            }

            case CMD_GET_PAYLOAD_MASK: {
                {
                    uint8_t temp_buf[1];
                    size_t  out_len = 0;
                    SM_Status_t st = SensorManager_GetConfigBytes(
                        mgr, cmd.addr7, CMD_GET_PAYLOAD_MASK, temp_buf, &out_len
                    );
                    if (st == SM_OK && out_len == 1) {
                        size_t len = ResponseBuilder_BuildFieldResponse(
                            txbuf,
                            cmd.addr7,
                            CMD_GET_PAYLOAD_MASK,
                            temp_buf[0]
                        );
                        HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                    } else {
                        send_status_response(&cmd, STATUS_ERROR);
                    }
                }
                break;
            }

            case CMD_CONFIG_SETTERS_START ... CMD_CONFIG_SETTERS_END: {
                // Generic configure call for whatever setter this is
                uint8_t status = SensorManager_Configure(
                    mgr, cmd.addr7, cmd.cmd, cmd.param
                );

                // If it succeeded and it was SET_PERIOD, update the RTOS task interval
                if (status == SM_OK && cmd.cmd == CMD_SET_PERIOD) {
                    uint32_t new_ms = (uint32_t)cmd.param * 100;  // param=5 → 500ms
                    SM_Status_t st2 = SensorManager_SetPeriod(
                        mgr, cmd.addr7, new_ms
                    );
                    if (st2 != SM_OK) {
                        status = SM_ERROR;
                    }
                }

                send_status_response(&cmd, status == SM_OK ? STATUS_OK : STATUS_ERROR);
                break;
            }

            case CMD_CONFIG_GETTERS_START ... CMD_CONFIG_GETTERS_END: {
                // Use multi-byte reader for every GET_… command
                uint8_t  temp_buf[4];   // buffer for up to 4 returned bytes
                size_t   out_len = 0;
                SM_Status_t st = SensorManager_GetConfigBytes(
                    mgr, cmd.addr7, cmd.cmd, temp_buf, &out_len
                );
                if (st == SM_OK && out_len > 0) {
                    // Build a payload of length out_len
                    size_t len = ResponseBuilder_BuildPayload(
                        txbuf,
                        cmd.addr7,
                        cmd.cmd,
                        temp_buf,
                        out_len
                    );
                    HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                } else {
                    send_status_response(&cmd, STATUS_ERROR);
                }
                break;
            }

            case CMD_GET_CONFIG: {
                // “Bulk-fetch all config fields”
                const SensorDriverInfo_t *info = SensorRegistry_FindByAddr(mgr, cmd.addr7);
                if (!info || !info->get_config_fields) {
                    send_status_response(&cmd, STATUS_ERROR);
                    break;
                }

                size_t count = 0;
                const uint8_t *fields = info->get_config_fields(&count);
                if (!fields || count == 0 || count > 16) {
                    send_status_response(&cmd, STATUS_ERROR);
                    break;
                }

                // Concatenate each field's returned bytes into payload_buf[].
                // (Max 16 fields × max 4 bytes = 64 bytes total)
                uint8_t payload_buf[64];
                size_t  payload_idx = 0;

                for (size_t i = 0; i < count; ++i) {
                    uint8_t  temp_buf[4];
                    size_t   single_len = 0;
                    SM_Status_t st = SensorManager_GetConfigBytes(
                        mgr, cmd.addr7, fields[i], temp_buf, &single_len
                    );
                    if (st != SM_OK || single_len == 0) {
                        send_status_response(&cmd, STATUS_ERROR);
                        goto skip_get_config;
                    }
                    // Copy returned bytes into payload_buf
                    for (size_t b = 0; b < single_len; ++b) {
                        payload_buf[payload_idx++] = temp_buf[b];
                    }
                }

                {
                    size_t len = ResponseBuilder_BuildPayload(
                        txbuf,
                        cmd.addr7,
                        cmd.cmd,       // == CMD_GET_CONFIG
                        payload_buf,
                        payload_idx    // total concatenated length
                    );
                    HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                }

            skip_get_config:
                break;
            }

            // ─────────── Default: unknown command ───────────
            default: {
                send_status_response(&cmd, STATUS_UNKNOWN_CMD);
                break;
            }
        } // end switch
    } // end for(;;)
}

UBaseType_t CommandTask_GetStackHighWaterMark(void) {
    if (!cmdTaskHandle) {
        return 0;
    }
    return uxTaskGetStackHighWaterMark(cmdTaskHandle);
}
