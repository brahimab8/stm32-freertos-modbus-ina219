#ifndef CMD_TASK_H
#define CMD_TASK_H

#include "FreeRTOS.h"
#include "queue.h"

/**
 * @brief Queue for complete command frames received via UART.
 *
 * This queue is filled from the UART interrupt and processed by the CommandTask.
 */
extern QueueHandle_t cmdQueue;

/**
 * @brief Task function for handling incoming sensor hub commands.
 *
 * This task receives parsed command frames from the queue and dispatches them
 * to the appropriate handlers in the sensor manager.
 *
 * @param argument A pointer to the SensorManager instance (cast to void*).
 */
void CommandTask(void *argument);

/**
 * @brief Get the minimum remaining stack space (high watermark) for the command task.
 *
 * Useful for debugging and monitoring memory usage.
 *
 * @return The minimum number of words that remained on the stack.
 */
UBaseType_t CommandTask_GetStackHighWaterMark(void);

#endif // CMD_TASK_H
