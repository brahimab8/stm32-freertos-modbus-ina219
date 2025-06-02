#!/usr/bin/env python3
import os
import json
import re

CTYPE = {
    "uint8":  "uint8_t",
    "uint16": "uint16_t",
    "int16":  "int16_t",
    "uint32": "uint32_t",
    "int32":  "int32_t",
}
ARRAY_TYPE_RE = re.compile(r"^([a-z0-9]+)\[(\d+)\]$")

def snake_case(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower())

def CTYPEDTLS_IF_ARRAY(type_key: str, typedef: str) -> str:
    """
    If type_key is like "uint8[2]", return the typedef (e.g. "INA219_GAIN_t").
    Otherwise return CTYPE.get(type_key, "uint16_t").
    """
    m = ARRAY_TYPE_RE.match(type_key)
    if m:
        return typedef
    else:
        return CTYPE.get(type_key, "uint16_t")


def gen_sensor_config(meta: dict, out_dir: str):
    """
    Emit:
     • Core/Inc/config/<sensor>_config.h
     • Core/Src/config/<sensor>_config.c
    """
    name   = meta["name"]
    SC     = snake_case(name)
    UPPER  = name.upper()
    struct = f"{UPPER}_config_defaults_t"

    # ------- HEADER -------
    hdr = [
        f"/* Auto-generated {name} config */",
        "#pragma once",
        "#include <stdint.h>",
        f"#include \"drivers/{SC}.h\"",
        "",
        "typedef struct {"
    ]
    for fld_name, val in meta.get("config_defaults", {}).items():
        ctype = f"{UPPER}_{fld_name.upper()}_t"
        hdr.append(f"    {ctype} {fld_name};")
    hdr.append(f"}} {struct};")
    hdr.append("")

    # default payload‐size
    payload_list = meta.get("payload_fields", [])
    default_bits = meta.get("default_payload_bits", [])
    if default_bits:
        size = sum(payload_list[i]["size"] for i in default_bits)
    else:
        size = sum(fld["size"] for fld in payload_list)
    hdr.append(f"#define SENSOR_PAYLOAD_SIZE_{UPPER} {size}")
    hdr.append("")
    hdr.append(f"extern {struct} {SC}_defaults;")
    hdr.append("")

    inc_cfg_dir = os.path.join(out_dir, "Inc", "config")
    os.makedirs(inc_cfg_dir, exist_ok=True)
    out_h = os.path.join(inc_cfg_dir, f"{SC}_config.h")
    with open(out_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hdr))
    print(f"Wrote {out_h}")

    # ------- SOURCE -------
    src = [
        f"/* Auto-generated {name} defaults definition */",
        f"#include \"config/{SC}_config.h\"",
        ""
    ]
    src.append(f"{struct} {SC}_defaults = {{")
    for fld_name, val in meta.get("config_defaults", {}).items():
        src.append(f"    .{fld_name} = {val},")
    src.append("};")
    src.append("")

    src_cfg_dir = os.path.join(out_dir, "Src", "config")
    os.makedirs(src_cfg_dir, exist_ok=True)
    out_c = os.path.join(src_cfg_dir, f"{SC}_config.c")
    with open(out_c, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(src))
    print(f"Wrote {out_c}")


def gen_sensor_driver_files(meta: dict, out_dir: str):
    """
    Emit:
      1) Core/Inc/drivers/<sensor>.h
      2) Core/Src/drivers/<sensor>.c
      3) Core/Inc/drivers/<sensor>_driver.h
      4) Core/Src/drivers/<sensor>_driver.c
    """
    name        = meta["name"]
    SC          = snake_case(name)
    UPPER       = name.upper()
    ctx_struct  = f"{UPPER}_Ctx_t"
    vtable_name = f"{SC}_driver"

    # ——— 1) HAL‐wrapper header: Inc/drivers/<sensor>.h ———
    hal_hdr = [
        f"/* Auto-generated from {SC}.json; do not edit! */",
        "#pragma once",
        "#include \"stm32l4xx_hal.h\"",
        "#include <stdint.h>",
        ""
    ]

    # 1a) typedefs for config_fields
    for cf in meta.get("config_fields", []):
        name_cf   = cf["name"]
        type_key  = cf["type"]        # e.g. "uint8", "uint16", or "uint8[2]"
        m = ARRAY_TYPE_RE.match(type_key)
        if m:
            base_key, arr_n = m.groups()
            base_type = CTYPE.get(base_key, "uint8_t")
            typedef   = f"{UPPER}_{name_cf.upper()}_t"
            hal_hdr.append(f"typedef {base_type} {typedef}[{arr_n}];")
        else:
            base_type = CTYPE.get(type_key, "uint16_t")
            typedef   = f"{UPPER}_{name_cf.upper()}_t"
            hal_hdr.append(f"typedef {base_type} {typedef};")
    hal_hdr.append("")

    # 1b) config_field register‐address defines
    for cf in meta.get("config_fields", []):
        ra = cf.get("reg_addr")
        if ra is None:
            continue
        tok = snake_case(cf["name"]).upper()
        hal_hdr.append(f"#define REG_{tok:<20} 0x{ra:02X}")
    hal_hdr.append("")

    # 1c) payload_field register‐address defines (no duplicates)
    added = set()
    for pf in meta.get("payload_fields", []):
        ra = pf.get("reg_addr")
        if ra is not None and ra not in added:
            tok = snake_case(pf["name"]).upper()
            hal_hdr.append(f"#define REG_{tok:<20} 0x{ra:02X}")
            added.add(ra)
    hal_hdr.append("")

    # 1d) payload-bit macros
    hal_hdr.append("// Payload-bit definitions (each bit selects one field)")
    for idx, pf in enumerate(meta.get("payload_fields", [])):
        tok = snake_case(pf["name"]).upper()
        hal_hdr.append(f"#define BIT_{tok:<22} (1 << {idx})")
    hal_hdr.append("")

    # 1e) config_field prototypes for Set<Pascal>() / Read<Pascal>()
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        pascal   = "".join(w.capitalize() for w in fld_name.split("_"))
        typedef  = f"{UPPER}_{fld_name.upper()}_t"
        setter   = cf.get("setter_cmd")
        getter   = cf.get("getter_cmd")
        ra       = cf.get("reg_addr")
        size     = cf.get("size")

        if setter and ra is not None:
            hal_hdr.append("/**")
            hal_hdr.append(f" * @brief Write to register 0x{ra:02X} (set {fld_name}).")
            hal_hdr.append(" */")
            hal_hdr.append(f"HAL_StatusTypeDef {UPPER}_Set{pascal}(")
            hal_hdr.append("    I2C_HandleTypeDef *hi2c,")
            hal_hdr.append("    uint16_t           addr8bit,")
            hal_hdr.append(f"    {typedef}         value")
            hal_hdr.append(");")
            hal_hdr.append("")

        if getter and ra is not None:
            c_or_alias = CTYPEDTLS_IF_ARRAY(cf["type"], typedef)
            hal_hdr.append("/**")
            hal_hdr.append(f" * @brief Read {fld_name} from register 0x{ra:02X}.")
            hal_hdr.append(" */")
            hal_hdr.append(f"HAL_StatusTypeDef {UPPER}_Read{pascal}(")
            hal_hdr.append("    I2C_HandleTypeDef *hi2c,")
            hal_hdr.append("    uint16_t           addr8bit,")
            hal_hdr.append(f"    {c_or_alias} *out")
            hal_hdr.append(");")
            hal_hdr.append("")

    # 1f) payload_field Read<Pascal>()
    for pf in meta.get("payload_fields", []):
        pascal     = "".join(w.capitalize() for w in pf["name"].split("_"))
        base_ctype = pf["type"].replace("[", "").replace("]", "")
        ctype      = CTYPE.get(base_ctype, "uint32_t")
        tok        = snake_case(pf["name"]).upper()
        ra         = pf.get("reg_addr")
        size       = pf["size"]
        hal_hdr.append(f"// Reads {pf['name']} from register 0x{ra:02X}")
        hal_hdr.append(f"HAL_StatusTypeDef {UPPER}_Read{pascal}(")
        hal_hdr.append("    I2C_HandleTypeDef *hi2c,")
        hal_hdr.append("    uint16_t           addr8bit,")
        hal_hdr.append(f"    {ctype}           *out")
        hal_hdr.append(");")
        hal_hdr.append("")

    inc_drv_dir = os.path.join(out_dir, "Inc", "drivers")
    os.makedirs(inc_drv_dir, exist_ok=True)
    out_hal_h = os.path.join(inc_drv_dir, f"{SC}.h")
    with open(out_hal_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hal_hdr))
    print(f"Wrote {out_hal_h}")


    # ——— 2) HAL‐wrapper implementation: Src/drivers/<sensor>.c ———
    hal_src = [
        f"/* Auto-generated from {SC}.json; do not edit! */",
        f'#include "drivers/{SC}.h"',
        "#include \"stm32l4xx_hal.h\"",
        ""
    ]

    # 2a) Implement Set<Pascal>()
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        pascal   = "".join(w.capitalize() for w in fld_name.split("_"))
        ra       = cf.get("reg_addr")
        size     = cf.get("size")
        setter   = cf.get("setter_cmd")
        if setter and ra is not None:
            if size == 1:
                hal_src.append(f"HAL_StatusTypeDef {UPPER}_Set{pascal}("
                               f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {UPPER}_{fld_name.upper()}_t value) {{")
                hal_src.append(f"    uint8_t buf[2] = {{ 0x{ra:02X}, (uint8_t)value }};")
                hal_src.append("    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 2, 100);")
                hal_src.append("}")
                hal_src.append("")
            else:
                hal_src.append(f"HAL_StatusTypeDef {UPPER}_Set{pascal}("
                               f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {UPPER}_{fld_name.upper()}_t value) {{")
                hal_src.append("    uint8_t buf[3] = {")
                hal_src.append(f"        0x{ra:02X},")
                hal_src.append(f"        (uint8_t)(value >> 8),")
                hal_src.append(f"        (uint8_t)(value & 0xFF)")
                hal_src.append("    };")
                hal_src.append("    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 3, 100);")
                hal_src.append("}")
                hal_src.append("")

    # 2b) Implement Read<Pascal>()
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        pascal   = "".join(w.capitalize() for w in fld_name.split("_"))
        ra       = cf.get("reg_addr")
        size     = cf.get("size")
        getter   = cf.get("getter_cmd")
        if getter and ra is not None:
            base_key = cf["type"].replace("[", "").replace("]", "")
            ctype    = CTYPE.get(base_key, "uint16_t")
            hal_src.append(f"HAL_StatusTypeDef {UPPER}_Read{pascal}("
                           f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {ctype} *out) {{")
            hal_src.append(f"    uint8_t cmd = 0x{ra:02X};")
            hal_src.append(f"    uint8_t data[{size}];")
            hal_src.append("    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;")
            hal_src.append(f"    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, {size}, 100) != HAL_OK) return HAL_ERROR;")
            if size == 1:
                hal_src.append("    *out = data[0];")
            else:
                hal_src.append("    uint16_t raw = (data[0] << 8) | data[1];")
                if cf.get("shift", 0) > 0:
                    hal_src.append(f"    raw = raw >> {cf['shift']};")
                if cf.get("mask"):
                    hal_src.append(f"    raw = raw & {cf['mask']};")
                hal_src.append("    *out = raw;")
            hal_src.append("    return HAL_OK;")
            hal_src.append("}")

    # 2c) Implement payload‐field Read<Pascal>()
    for pf in meta.get("payload_fields", []):
        pascal     = "".join(w.capitalize() for w in pf["name"].split("_"))
        base_ctype = pf["type"].replace("[", "").replace("]", "")
        ctype      = CTYPE.get(base_ctype, "uint32_t")
        size       = pf["size"]
        tok        = snake_case(pf["name"]).upper()
        scale      = pf.get("scale_factor", 1)
        hal_src.append(f"HAL_StatusTypeDef {UPPER}_Read{pascal}("
                       f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {ctype} *out) {{")
        hal_src.append(f"    uint8_t cmd = REG_{tok};")
        hal_src.append(f"    uint8_t data[{size}];")
        hal_src.append("    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;")
        hal_src.append(f"    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, {size}, 100) != HAL_OK) return HAL_ERROR;")
        if size == 2:
            hal_src.append("    uint16_t raw = (data[0] << 8) | data[1];")
        else:
            hal_src.append("    uint32_t raw = ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | data[3];")
        if pf.get("shift", 0) > 0:
            hal_src.append(f"    raw = raw >> {pf['shift']};")
        if pf.get("mask"):
            hal_src.append(f"    raw = raw & {pf['mask']};")
        hal_src.append(f"    *out = raw * {scale};")
        hal_src.append("    return HAL_OK;")
        hal_src.append("}")

    src_drv_dir = os.path.join(out_dir, "Src", "drivers")
    os.makedirs(src_drv_dir, exist_ok=True)
    out_hal_c = os.path.join(src_drv_dir, f"{SC}.c")
    with open(out_hal_c, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hal_src))
    print(f"Wrote {out_hal_c}")


    # ——— 3) Driver‐layer header: Inc/drivers/<sensor>_driver.h ———
    drv_hdr = [
        f"/* Auto-generated {name}_driver.h; do not edit! */",
        "#pragma once",
        "",
        "#include \"task/sensor_task.h\"  /**< SensorDriver_t, SensorSample_t */",
        "#include \"driver_registry.h\"   /**< SensorRegistry_Register */",
        f"#include \"drivers/{SC}.h\"        /**< HAL-level wrapper */",
        "#include \"stm32l4xx_hal.h\"       /**< I2C_HandleTypeDef */",
        "#include <stdint.h>",
        "#include <stdbool.h>",
        "",
        "// ---------------- Public callbacks ----------------",
        f"void {SC}_init_ctx(void *vctx, I2C_HandleTypeDef *hi2c, uint8_t addr7);",
        f"bool {SC}_configure(void *vctx, uint8_t field_id, uint8_t value);",
        f"bool {SC}_read_config(void *vctx, uint8_t field_id, uint8_t *value);",
        "",
        "// vtable getter:",
        f"const SensorDriver_t *{UPPER}_GetDriver(void);",
        "",
        "// Register this driver into the global registry:",
        f"void {SC}_RegisterDriver(void);",
        "",
        "/**",
        " * @brief   Context for a sensor instance.",
        " */",
        f"typedef struct {{",
        "    I2C_HandleTypeDef *hi2c;      /**< I2C handle */",
        "    uint16_t           addr8;     /**< 8-bit I²C address */"
    ]

    # 3a) Add one member per config_field (skip “all”)
    for cf in meta.get("config_fields", []):
        key = cf["name"]
        if key == "all":
            continue
        tm = cf["type"]
        arr_match = ARRAY_TYPE_RE.match(tm)
        if arr_match:
            base_key, arr_n = arr_match.groups()
            c_bas = CTYPE.get(base_key, "uint8_t")
            drv_hdr.append(f"    {c_bas} {key}[{arr_n}];")
        else:
            drv_hdr.append(f"    {UPPER}_{key.upper()}_t {key};")

    # 3b) Always add “payload_mask”
    drv_hdr.append(f"    uint8_t payload_mask;   /**< which payload bits are enabled */")
    drv_hdr.append(f"}} {ctx_struct};")
    drv_hdr.append("")

    inc_drv_dir = os.path.join(out_dir, "Inc", "drivers")
    os.makedirs(inc_drv_dir, exist_ok=True)
    out_drv_h = os.path.join(inc_drv_dir, f"{SC}_driver.h")
    with open(out_drv_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(drv_hdr))
    print(f"Wrote {out_drv_h}")


    # ——— 4) Driver‐layer implementation: Src/drivers/<sensor>_driver.c ———
    drv_src = [
        f"/* Auto-generated {name}_driver.c; do not edit! */",
        f'#include "drivers/{SC}_driver.h"',
        f'#include "config/{SC}_config.h"',
        "#include \"config/protocol.h\"",
        "#include <string.h>",
        "#include <stdbool.h>",
        ""
    ]

    # 4a) ini(): initialize driver (apply defaults + set default mask)
    drv_src.append(f"static HAL_StatusTypeDef ini(void *ctx) {{")
    drv_src.append(f"    {ctx_struct} *c = ({ctx_struct} *)ctx;")
    for fld_name in meta.get("config_defaults", {}).keys():
        if fld_name == "all":
            continue
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        drv_src.append(f"    if ({UPPER}_Set{pascal}(c->hi2c, c->addr8, {SC}_defaults.{fld_name}) != HAL_OK) return HAL_ERROR;")
    for fld_name in meta.get("config_defaults", {}).keys():
        if fld_name == "all":
            continue
        drv_src.append(f"    c->{fld_name} = {SC}_defaults.{fld_name};")

    default_bits = meta.get("default_payload_bits", [])
    default_mask = 0
    for bit in default_bits:
        default_mask |= (1 << bit)
    drv_src.append(f"    c->payload_mask = 0x{default_mask:02X};  /* default mask */")
    drv_src.append("    return HAL_OK;")
    drv_src.append("}")
    drv_src.append("")

    # 4b) rd(): pack only selected payload bits into out_buf
    drv_src.append("static HAL_StatusTypeDef rd(void *ctx, uint8_t out_buf[], uint8_t *out_len) {")
    drv_src.append(f"    {ctx_struct} *c = ({ctx_struct} *)ctx;")
    drv_src.append("    uint8_t *cursor = out_buf;")
    drv_src.append("    uint8_t mask = c->payload_mask;")
    drv_src.append("    int total_bytes = 0;")
    drv_src.append("")

    for idx, pf in enumerate(meta.get("payload_fields", [])):
        bitname = f"BIT_{snake_case(pf['name']).upper()}"
        pascal  = "".join(w.capitalize() for w in pf["name"].split("_"))
        size    = pf["size"]
        read_fn = f"{UPPER}_Read{pascal}"
        drv_src.append(f"    if (mask & {bitname}) {{")
        base_ctype = pf["type"].replace("[", "").replace("]", "")
        ctype      = CTYPE.get(base_ctype, "uint32_t")
        tmp_name   = f"var_{pf['name']}"
        drv_src.append(f"        {ctype} {tmp_name};")
        drv_src.append(f"        if ({read_fn}(c->hi2c, c->addr8, &{tmp_name}) != HAL_OK) {{")
        drv_src.append("            *out_len = 0;")
        drv_src.append("            return HAL_ERROR;")
        drv_src.append("        }")
        if size == 2:
            drv_src.append(f"        *cursor++ = (uint8_t)({tmp_name} >> 8);")
            drv_src.append(f"        *cursor++ = (uint8_t)({tmp_name} & 0xFF);")
            drv_src.append("        total_bytes += 2;")
        elif size == 4:
            drv_src.append(f"        *cursor++ = (uint8_t)(({tmp_name} >> 24) & 0xFF);")
            drv_src.append(f"        *cursor++ = (uint8_t)(({tmp_name} >> 16) & 0xFF);")
            drv_src.append(f"        *cursor++ = (uint8_t)(({tmp_name} >> 8)  & 0xFF);")
            drv_src.append(f"        *cursor++ = (uint8_t)(({tmp_name})       & 0xFF);")
            drv_src.append("        total_bytes += 4;")
        else:
            for b in range(size):
                shift_amt = 8 * (size - 1 - b)
                drv_src.append(
                    f"        *cursor++ = (uint8_t)(({tmp_name} >> {shift_amt}) & 0xFF);"
                )
            drv_src.append(f"        total_bytes += {size};")
        drv_src.append("    }")
        drv_src.append("")

    drv_src.append("    *out_len = total_bytes;")
    drv_src.append("    return HAL_OK;")
    drv_src.append("}")
    drv_src.append("")

    # 4c) read_config(): return a single byte for each getter + mask getter
    drv_src.append(f"bool {SC}_read_config(void *vctx, uint8_t field, uint8_t *out) {{")
    drv_src.append(f"    {ctx_struct} *c = ({ctx_struct} *)vctx;")
    drv_src.append("    switch (field) {")
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        getter   = cf.get("getter_cmd")
        size     = cf.get("size")
        if fld_name == "all" or getter is None:
            continue
        drv_src.append(f"      case {getter}:")
        if size == 1:
            drv_src.append(f"        *out = (uint8_t)c->{fld_name};")
        else:
            drv_src.append(f"        *out = (uint8_t)(c->{fld_name} & 0xFF);")
        drv_src.append("        return true;")
        drv_src.append("")

    # 4c2) payload-mask getter
    drv_src.append("      case CMD_GET_PAYLOAD_MASK:")
    drv_src.append("        *out = c->payload_mask;")
    drv_src.append("        return true;")
    drv_src.append("")

    drv_src.append("      default:")
    drv_src.append("        return false;")
    drv_src.append("    }")
    drv_src.append("}")
    drv_src.append("")

    # 4d) vtable + GetDriver()
    drv_src.append(f"static const SensorDriver_t {vtable_name} = {{")
    drv_src.append("    .init        = ini,")
    drv_src.append("    .read        = rd,")
    drv_src.append(f"    .sample_size = SENSOR_PAYLOAD_SIZE_{UPPER},")
    drv_src.append(f"    .read_config = {SC}_read_config,")
    drv_src.append("};")
    drv_src.append("")
    drv_src.append(f"const SensorDriver_t *{UPPER}_GetDriver(void) {{")
    drv_src.append(f"    return &{vtable_name};")
    drv_src.append("}")
    drv_src.append("")

    # 4e) static SensorDriverInfo_t + RegisterDriver()
    drv_src.append(f"static const SensorDriverInfo_t {SC}_info = {{")
    drv_src.append(f"    .type_code   = SENSOR_TYPE_{UPPER},")
    drv_src.append(f"    .ctx_size    = sizeof({ctx_struct}),")
    drv_src.append(f"    .init_ctx    = {SC}_init_ctx,")
    drv_src.append(f"    .get_driver  = {UPPER}_GetDriver,")
    drv_src.append(f"    .configure   = {SC}_configure,")
    drv_src.append(f"    .read_config = {SC}_read_config,")
    drv_src.append("};")
    drv_src.append("")
    drv_src.append(f"void {SC}_RegisterDriver(void) {{")
    drv_src.append(f"    SensorRegistry_Register(&{SC}_info);")
    drv_src.append("}")
    drv_src.append("")

    # 4f) init_ctx() and configure()
    drv_src.append(f"void {SC}_init_ctx(void *vctx, I2C_HandleTypeDef *hi2c, uint8_t addr7) {{")
    drv_src.append(f"    {ctx_struct} *c = ({ctx_struct} *)vctx;")
    drv_src.append("    c->hi2c  = hi2c;")
    drv_src.append("    c->addr8 = addr7 << 1;")
    drv_src.append("}")
    drv_src.append("")

    drv_src.append(f"bool {SC}_configure(void *vctx, uint8_t field_id, uint8_t param) {{")
    drv_src.append(f"    {ctx_struct} *c = ({ctx_struct} *)vctx;")
    drv_src.append("    HAL_StatusTypeDef rc;")
    drv_src.append("")
    drv_src.append("    switch (field_id) {")
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        setter   = cf.get("setter_cmd")
        size     = cf.get("size")
        if not setter:
            continue
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        drv_src.append(f"      case {setter}:")
        drv_src.append(f"        rc = {UPPER}_Set{pascal}(c->hi2c, c->addr8, ({UPPER}_{fld_name.upper()}_t)param);")
        drv_src.append("        if (rc == HAL_OK) {")
        drv_src.append(f"            c->{fld_name} = ({UPPER}_{fld_name.upper()}_t)param;")
        drv_src.append("            return true;")
        drv_src.append("        } else {")
        drv_src.append("            return false;")
        drv_src.append("        }")
        drv_src.append("")

    # 4f2) payload-mask setter
    drv_src.append("      case CMD_SET_PAYLOAD_MASK:")
    drv_src.append("        c->payload_mask = param;")
    drv_src.append("        return true;")
    drv_src.append("")

    drv_src.append("      default:")
    drv_src.append("        return false;")
    drv_src.append("    }")
    drv_src.append("}")
    drv_src.append("")

    out_drv_c = os.path.join(os.path.join(out_dir, "Src", "drivers"), f"{SC}_driver.c")
    with open(out_drv_c, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(drv_src))
    print(f"Wrote {out_drv_c}")
