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
                uint8_t status = SensorManager_AddByType(
                    mgr,
                    cmd.param,             // sensor type from UART frame
                    cmd.addr7,             // I²C address
                    SENSOR_DEFAULT_POLL_PERIOD
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
                uint8_t mask_val;
                SM_Status_t st = SensorManager_GetConfig(
                    mgr, cmd.addr7, CMD_GET_PAYLOAD_MASK, &mask_val
                );
                if (st == SM_OK) {
                    // Build a single‐byte payload
                    size_t len = ResponseBuilder_BuildFieldResponse(
                        txbuf,
                        cmd.addr7,
                        CMD_GET_PAYLOAD_MASK,
                        mask_val
                    );
                    HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                } else {
                    send_status_response(&cmd, STATUS_ERROR);
                }
                break;
            }

            case CMD_SET_PERIOD: {
                uint8_t status = SensorManager_SetPeriod(mgr, cmd.addr7, cmd.param * 100);
                send_status_response(&cmd, status);
                break;
            }

            case CMD_SET_GAIN:
            case CMD_SET_RANGE:
            case CMD_SET_CAL: {
                uint8_t status = SensorManager_Configure(mgr, cmd.addr7, cmd.cmd, cmd.param);
                send_status_response(&cmd, status);
                break;
            }

            case CMD_GET_PERIOD: {
                uint8_t period_units;
                SM_Status_t st = SensorManager_GetConfig(
                    mgr, cmd.addr7, CMD_GET_PERIOD, &period_units
                );
                if (st == SM_OK) {
                    size_t len = ResponseBuilder_BuildFieldResponse(
                        txbuf,
                        cmd.addr7,
                        CMD_GET_PERIOD,
                        period_units
                    );
                    HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                } else {
                    send_status_response(&cmd, STATUS_ERROR);
                }
                break;
            }

            case CMD_GET_GAIN:
            case CMD_GET_RANGE:
            case CMD_GET_CAL: {
                uint8_t val;
                SM_Status_t st = SensorManager_GetConfig(
                    mgr, cmd.addr7, cmd.cmd, &val
                );
                if (st == SM_OK) {
                    size_t len = ResponseBuilder_BuildFieldResponse(
                        txbuf,
                        cmd.addr7,
                        cmd.cmd,
                        val
                    );
                    HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
                } else {
                    send_status_response(&cmd, STATUS_ERROR);
                }
                break;
            }

            case CMD_GET_CONFIG: {
                uint8_t payload[4];
                SM_Status_t st;

                st = SensorManager_GetConfig(mgr, cmd.addr7, CMD_GET_PERIOD, &payload[0]);
                if (st != SM_OK) { send_status_response(&cmd, STATUS_ERROR); break; }

                st = SensorManager_GetConfig(mgr, cmd.addr7, CMD_GET_GAIN, &payload[1]);
                if (st != SM_OK) { send_status_response(&cmd, STATUS_ERROR); break; }

                st = SensorManager_GetConfig(mgr, cmd.addr7, CMD_GET_RANGE, &payload[2]);
                if (st != SM_OK) { send_status_response(&cmd, STATUS_ERROR); break; }

                st = SensorManager_GetConfig(mgr, cmd.addr7, CMD_GET_CAL, &payload[3]);
                if (st != SM_OK) { send_status_response(&cmd, STATUS_ERROR); break; }

                size_t len = ResponseBuilder_BuildGetConfig(
                    txbuf,
                    cmd.addr7,
                    payload[0],  // period_u100
                    payload[1],  // gain
                    payload[2],  // range
                    payload[3]   // calib_lsb
                );
                HAL_UART_Transmit(&huart1, txbuf, len, HAL_MAX_DELAY);
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
