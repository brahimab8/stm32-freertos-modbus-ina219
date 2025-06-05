#pragma once

// We only define osThreadId_t and osMutexId_t so that code compiles.
// Real RTOS behavior is not needed in unit tests.

typedef void *osThreadId_t;
typedef void *osMutexId_t;
