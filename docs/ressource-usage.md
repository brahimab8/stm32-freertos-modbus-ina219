# Resource Usage & Debug Output

This document analyzes runtime heap and stack utilization for the STM32 I²C Sensor Hub firmware, clarifying configured allocations, observed defaults, and per-sensor costs.

---

## 1. Configured Resource Allocations

| RTOS Object    | Configured Size                                                         | Purpose                                   |
| -------------- | ----------------------------------------------------------------------- | ----------------------------------------- |
| CommandTask    | `192 * 4 = 768 bytes`                                                   | UART/RS-485 framing & dispatch            |
| SensorTask\[i] | `128 * 4 = 512 bytes`                                                   | Periodic I²C sampling per sensor          |
| DefaultTask    | `128 * 4 = 512 bytes`                                                   | Debug console (USART2) logging heap/stack |
| MessageQueue   | `QUEUE_DEPTH × sizeof(SensorSample_t)`<br>(default 10 × \~16 B ≈ 160 B) | Per-sensor sample FIFO queue              |
| SensorManager  | Context size per sensor (e.g. `~32 B`) + table entries                  | Driver contexts and entry tracking        |

Heap total is set via `configTOTAL_HEAP_SIZE` in `FreeRTOSConfig.h` (default: **8192 bytes**).

---

## 2. DefaultTask Debug Output

The `DefaultTask` (USART2 debug console) prints heap and stack watermarks at runtime. Captured outputs while running the Python CLI on a separate host:

```
No sensors:
[CmdTask] stack left: 408 bytes
[Sys] Free heap: 6192 bytes

1 sensor:
[CmdTask] stack left: 168 bytes
[Sensor 0] stack left: 208 bytes
[Sys] Free heap: 5192 bytes

2 sensors:
[Sensor 0] stack left: 208 bytes
[Sensor 1] stack left: 200 bytes
[CmdTask] stack left: 168 bytes
[Sys] Free heap: 4192 bytes

4 sensors:
[Sensor 0] stack left: 200 bytes
[Sensor 1] stack left: 200 bytes
[Sensor 2] stack left: 208 bytes
[Sensor 3] stack left: 192 bytes
[CmdTask] stack left: 168 bytes
[Sys] Free heap: 2192 bytes

6 sensors:
[Sensor 0] stack left: 200 bytes
[Sensor 1] stack left: 200 bytes
[Sensor 2] stack left: 208 bytes
[Sensor 3] stack left: 192 bytes
[Sensor 4] stack left: 228 bytes
[Sensor 5] stack left: 228 bytes
[CmdTask] stack left: 168 bytes
[Sys] Free heap: 192 bytes
```

---

## 3. Interpretation & Recommendations

* **Initial overhead (\~2000 B)**: Before sensors, free heap drops from 8192 to \~6192 B. This covers:

  * RTOS structures, default queues, SensorManager allocation, and CommandTask stack reservation.

* **CommandTask heap impact (\~1000 B)**: Upon adding the first sensor, free heap reduces by \~1000 B (to \~5192 B). This includes:

  * SensorManager context for that sensor (\~32 B).
  * Message queue (\~160 B).
  * Thread stack reservation (512 B).

* **Per-sensor cost (\~1000 B each)**: Each additional SensorTask consumes \~1000 B of heap (queue + stack + context).

* **Stack watermarks**:

  * CommandTask: configured 768 B, watermark shows \~360–600 B used.
  * SensorTask: configured 512 B, watermark shows \~280–312 B used.
  * DefaultTask: similarly sized and margin remains.
  * You can reduce configured stack sizes based on these watermarks to reclaim heap.

* **Scaling beyond 6 sensors**: With default 8192 B heap, \~192 B remains after 6 sensors—no capacity for a 7th. To support more sensors:

  * Increase `configTOTAL_HEAP_SIZE` (e.g. to 10 KB+).
  * Reduce `QUEUE_DEPTH` or stack sizes.

---
