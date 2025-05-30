# Communication protocol

This document describes the RS-485 (Half-Duplex & Master-Slave) binary protocol used by the STM32 I²C Sensor Hub: framing, commands, response formats, and sensor metadata schemas. The canonical definitions live in `metadata/protocol.json` and `metadata/sensors/`.

---

## 1. JSON Definition (excerpt)

```jsonc
{
  "constants": {
    "SOF_MARKER":      170, // 0xAA
    "QUEUE_DEPTH":     10,  // max 10 Readings per sensor
    /* … */
  },
  "commands": {
    "CMD_READ_SAMPLES":  0,
    "CMD_ADD_SENSOR":    1,
    "CMD_REMOVE_SENSOR": 2,
    /* … */
    "CMD_LIST_SENSORS":  9
  },
  "status_codes": {
    "STATUS_OK":          0,
    "STATUS_ERROR":       1,
    "STATUS_NOT_FOUND":   2,
    "STATUS_UNKNOWN_CMD": 3
  },
  "frames": {
    "command":         [ /* 6-byte master→node */ ],
    "response_header": [ /* 6-byte node→master header */ ]
  }
}
```

> Full definition: [`metadata/protocol.json`](../metadata/protocol.json)

---

## 2. Framing Overview

Every packet—command or response—begins and ends the same way:

* **SOF** (1 B): `0xAA`
* **Common fields** (4 B):

  1. **BoardID**: node identifier
  2. **Addr7**: I²C 7-bit address
  3. **CmdID**: command code
  4. *(commands only)* **Param** (1 B) or *(responses only)* **Status** (1 B) + **Length** (1 B)
* **Payload** (N B): command- or response-specific
* **Checksum** (1 B): XOR of all bytes from **BoardID** through end of payload

This lightweight framing ensures reliable sync and error detection on noisy RS-485.

---

## 3. STM32 ISR Behavior

The STM32’s `HAL_UART_RxCpltCallback` on USART1:

1. Waits for **SOF** (`0xAA`)
2. Reads the next 5 bytes (commands) or 5+Length bytes (responses) or times out after `UART_FRAME_TIMEOUT_MS`
3. Verifies:

   * Checksum: `checksum == XOR(BoardID, Addr7, CmdID, Param)` (for commands)
   * `BoardID == BOARD_ID`
4. On valid command, enqueues a `COMMAND_t` for the CommandTask
5. Discards invalid or timed-out frames

---

## 4. Command Packet (Host → STM32)

| Offset |   Field  | Size | Description                       |
| :----: | :------: | :--: | :-------------------------------- |
|    0   |    SOF   |  1 B | `0xAA`                            |
|    1   |  BoardID |  1 B | Node identifier                   |
|    2   |   Addr7  |  1 B | I²C address (0x01–0x7F)           |
|    3   |   CmdID  |  1 B | Command code (see table)          |
|    4   |   Param  |  1 B | Command-specific parameter        |
|    5   | Checksum |  1 B | `BoardID ^ Addr7 ^ CmdID ^ Param` |

### 4.1 Command Codes

| Code |         Name        | Description                                |
| :--: | :-----------------: | :----------------------------------------- |
|   0  |  `CMD_READ_SAMPLES` | Retrieve buffered samples                  |
|   1  |   `CMD_ADD_SENSOR`  | Add/configure sensor (Param = type code)   |
|   2  | `CMD_REMOVE_SENSOR` | Remove sensor at Addr7                     |
|   3  |   `CMD_SET_PERIOD`  | Set sampling period (Param = 100 ms units) |
|   5  |    `CMD_SET_GAIN`   | Set gain (sensor-specific)                 |
|   6  |   `CMD_SET_RANGE`   | Set range (sensor-specific)                |
|   7  |    `CMD_SET_CAL`    | Set calibration value                      |
|   8  |  `CMD_LIST_SENSORS` | List active sensors                        |
|   9  |      `CMD_PING`     | Ping node                                  |

---

## 5. Response Packet (STM32 → Host)

| Offset |   Field  | Size | Description               |
| :----: | :------: | :--: | :------------------------ |
|    0   |    SOF   |  1 B | `0xAA`                    |
|    1   |  BoardID |  1 B | Echoed node ID            |
|    2   |   Addr7  |  1 B | Echoed I²C address        |
|    3   |   CmdID  |  1 B | Echoed command code       |
|    4   |  Status  |  1 B | `STATUS_OK` or error code |
|    5   |  Length  |  1 B | Number of payload bytes   |
|   6..  |  Payload |  N B | See Section 6             |
|  last  | Checksum |  1 B | XOR of bytes 1–(5+N)      |

### 5.1 Status Codes

| Code |         Name         | Meaning            |
| :--: | :------------------: | :----------------- |
|   0  |      `STATUS_OK`     | Success            |
|   1  |    `STATUS_ERROR`    | General failure    |
|   2  |  `STATUS_NOT_FOUND`  | Sensor not present |
|   3  | `STATUS_UNKNOWN_CMD` | Unknown command    |

---

## 6. Payload Definitions

### 6.1 Read Samples

* **CmdID**: `CMD_READ_SAMPLES` (0)
* **Length**: `count × (TICK_BYTES + sample_size)`
* **Per sample**:

  1. **Timestamp** (4 B): big-endian tick
  2. **Data** (`sample_size` B): as defined in sensor metadata

Master parses using each `metadata/sensors/<name>.json`.

### 6.2 List Sensors

* **CmdID**: `CMD_LIST_SENSORS` (8)
* **Length**: `2 × count`
* **Entries**: \[type\_code, addr7] pairs (1 B each)

### 6.3 Other Commands

* **Add/Remove/Set-**\* have no payload (`Length=0`).
* Check **Status** for result.

---

## 7. Sensor Metadata Schema

Each sensor’s JSON under `metadata/sensors/` defines defaults and payload layout. Example **ina219.json**:

```json
{
  "name": "ina219",
  "config_defaults": {
    "gain":        "INA219_GAIN_8_320MV",
    "bus_range":   "INA219_BVOLTAGERANGE_32V",
    "calibration": 4096
  },
  "payload_fields": [
    { "name": "bus_voltage_mV", "type": "uint16", "size": 2 },
    { "name": "current_uA",     "type": "int32",  "size": 4 }
  ]
}
```

* **`config_defaults`** → generates `<sensor>_config.h/.c`.
* **`payload_fields`** → instructs packing order and size.

> All sensor definitions: [`metadata/sensors/`](../metadata/sensors/)

---

## 8. Adding New Sensors

See [docs/add-sensor.md](docs/add-sensor.md) for a step-by-step guide:

1. Create `metadata/sensors/<name>.json`.
2. Add its type code in `metadata/protocol.json`.
3. Regenerate headers:

   ```bash
   python scripts/generate_headers.py --meta metadata --out firmware/.../Core
   ```
4. Implement driver code in `firmware/.../Drivers` and update `driver_registry.c`.

---

[Home](index.md) • [Return (Architecture)](architecture.md) • [Next (Resource Usage)](ressource-usage.md)
