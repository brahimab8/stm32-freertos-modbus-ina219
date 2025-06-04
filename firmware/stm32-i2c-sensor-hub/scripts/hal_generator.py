#!/usr/bin/env python3
import os
import re

# ——————————————————————————————————————————————————————————————————————
# Shared helpers (CTYPE, ARRAY_TYPE_RE, snake_case, CTYPEDTLS_IF_ARRAY)
# ——————————————————————————————————————————————————————————————————————
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


# ——————————————————————————————————————————————————————————————————————
# “HAL-wrapper” code-generation: header + source
# ——————————————————————————————————————————————————————————————————————
def build_hal_header_lines(name: str, meta: dict) -> list[str]:
    """
    Build lines for the HAL-wrapper header: Inc/drivers/<sensor>.h
    """
    SC = snake_case(name)
    UPPER = name.upper()
    lines = [
        f"/* Auto-generated from {SC}.json; do not edit! */",
        "#pragma once",
        "#include \"stm32l4xx_hal.h\"",
        "#include <stdint.h>",
        ""
    ]

    # 1a) typedefs for config_fields
    for cf in meta.get("config_fields", []):
        cf_name = cf["name"]
        type_key = cf["type"]
        typedef = f"{UPPER}_{cf_name.upper()}_t"
        enum_map = cf.get("enum_labels")

        m = ARRAY_TYPE_RE.match(type_key)
        if m:
            base_key, arr_n = m.groups()
            base_type = CTYPE.get(base_key, "uint8_t")
            lines.append(f"typedef {base_type} {typedef}[{arr_n}];")
            continue

        base_type = CTYPE.get(type_key, "uint16_t")
        if enum_map:
            lines.append("typedef enum {")
            for val, label in enum_map.items():
                enum_name = re.sub(r"[^A-Z0-9]+", "_", label.upper())
                lines.append(f"    {UPPER}_{cf_name.upper()}_{enum_name} = {val},")
            lines.append(f"}} {typedef};")
        else:
            lines.append(f"typedef {base_type} {typedef};")

    # 1b) config_field register-address defines
    for cf in meta.get("config_fields", []):
        ra = cf.get("reg_addr")
        if ra is None:
            continue
        tok = snake_case(cf["name"]).upper()
        lines.append(f"#define REG_{tok:<20} 0x{ra:02X}")
    lines.append("")

    # 1c) payload_field register-address defines (no duplicates)
    added = set()
    for pf in meta.get("payload_fields", []):
        ra = pf.get("reg_addr")
        if ra is not None and ra not in added:
            tok = snake_case(pf["name"]).upper()
            lines.append(f"#define REG_{tok:<20} 0x{ra:02X}")
            added.add(ra)
    lines.append("")

    # 1d) payload-bit macros
    lines.append("// Payload-bit definitions (each bit selects one field)")
    for idx, pf in enumerate(meta.get("payload_fields", [])):
        tok = snake_case(pf["name"]).upper()
        lines.append(f"#define BIT_{tok:<22} (1 << {idx})")
    lines.append("")

    # 1e) config_field prototypes for Set<Pascal>() / Read<Pascal>()
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        typedef = f"{UPPER}_{fld_name.upper()}_t"
        setter = cf.get("setter_cmd")
        getter = cf.get("getter_cmd")
        ra = cf.get("reg_addr")
        size = cf.get("size")

        if setter and ra is not None:
            lines.extend([
                "/**",
                f" * @brief Write to register 0x{ra:02X} (set {fld_name}).",
                " */",
                f"HAL_StatusTypeDef {UPPER}_Set{pascal}(",
                "    I2C_HandleTypeDef *hi2c,",
                "    uint16_t           addr8bit,",
                f"    {typedef}         value",
                ");",
                ""
            ])

        if getter and ra is not None:
            c_or_alias = CTYPEDTLS_IF_ARRAY(cf["type"], typedef)
            lines.extend([
                "/**",
                f" * @brief Read {fld_name} from register 0x{ra:02X}.",
                " */",
                f"HAL_StatusTypeDef {UPPER}_Read{pascal}(",
                "    I2C_HandleTypeDef *hi2c,",
                "    uint16_t           addr8bit,",
                f"    {c_or_alias} *out",
                ");",
                ""
            ])

    # Special case: SetPeriod with no reg_addr but driver_side=true
    for cf in meta.get("config_fields", []):
        if (
            cf["name"] == "period"
            and cf.get("driver_side")
            and cf.get("setter_cmd")
            and cf.get("reg_addr") is None
        ):
            typedef = f"{UPPER}_PERIOD_t"
            lines.extend([
                "/**",
                " * @brief Set period (handled internally; no register).",
                " */",
                f"HAL_StatusTypeDef {UPPER}_SetPeriod(",
                "    I2C_HandleTypeDef *hi2c,",
                "    uint16_t           addr8bit,",
                f"    {typedef}         value",
                ");",
                ""
            ])

    # 1f) payload_field Read<Pascal>(): only prototypes here
    for pf in meta.get("payload_fields", []):
        pascal = "".join(w.capitalize() for w in pf["name"].split("_"))
        base_ctype = pf["type"].replace("[", "").replace("]", "")
        ctype = CTYPE.get(base_ctype, "uint32_t")
        tok = snake_case(pf["name"]).upper()
        ra = pf.get("reg_addr")
        size = pf["size"]
        lines.extend([
            f"// Reads {pf['name']} from register 0x{ra:02X}",
            f"HAL_StatusTypeDef {UPPER}_Read{pascal}(",
            "    I2C_HandleTypeDef *hi2c,",
            "    uint16_t           addr8bit,",
            f"    {ctype}           *out",
            ");",
            ""
        ])

    return lines


def build_hal_source_lines(name: str, meta: dict) -> list[str]:
    """
    Build lines for the HAL-wrapper implementation: Src/drivers/<sensor>.c
    """
    SC = snake_case(name)
    UPPER = name.upper()
    lines = [
        f"/* Auto-generated from {SC}.json; do not edit! */",
        f'#include "drivers/{SC}.h"',
        "#include \"stm32l4xx_hal.h\"",
        ""
    ]

    # 2a) Implement Set<Pascal>()
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        ra = cf.get("reg_addr")
        size = cf.get("size")
        setter = cf.get("setter_cmd")

        if setter and ra is not None:
            if size == 1:
                lines.extend([
                    f"HAL_StatusTypeDef {UPPER}_Set{pascal}(",
                    f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {UPPER}_{fld_name.upper()}_t value) {{",
                    f"    uint8_t buf[2] = {{ 0x{ra:02X}, (uint8_t)value }};",
                    "    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 2, 100);",
                    "}",
                    ""
                ])
            else:
                lines.extend([
                    f"HAL_StatusTypeDef {UPPER}_Set{pascal}(",
                    f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {UPPER}_{fld_name.upper()}_t value) {{",
                    "    uint8_t buf[3] = {",
                    f"        0x{ra:02X},",
                    f"        (uint8_t)(value >> 8),",
                    f"        (uint8_t)(value & 0xFF)",
                    "    };",
                    "    return HAL_I2C_Master_Transmit(hi2c, addr8bit, buf, 3, 100);",
                    "}",
                    ""
                ])

    # Special case: stub for SetPeriod with no reg_addr
    for cf in meta.get("config_fields", []):
        if (
            cf["name"] == "period"
            and cf.get("driver_side")
            and cf.get("setter_cmd")
            and cf.get("reg_addr") is None
        ):
            lines.extend([
                f"HAL_StatusTypeDef {UPPER}_SetPeriod(",
                "    I2C_HandleTypeDef *hi2c,",
                "    uint16_t           addr8bit,",
                f"    {UPPER}_PERIOD_t   value",
                ") {",
                "    (void)hi2c; (void)addr8bit; (void)value;",
                "    return HAL_OK;  // Period is handled internally",
                "}",
                ""
            ])

    # 2b) Implement Read<Pascal>()
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        ra = cf.get("reg_addr")
        size = cf.get("size")
        getter = cf.get("getter_cmd")

        if getter and ra is not None:
            base_key = cf["type"].replace("[", "").replace("]", "")
            ctype = CTYPE.get(base_key, "uint16_t")
            lines.extend([
                f"HAL_StatusTypeDef {UPPER}_Read{pascal}(",
                f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {ctype} *out) {{",
                f"    uint8_t cmd = 0x{ra:02X};",
                f"    uint8_t data[{size}];",
                "    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;",
                f"    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, {size}, 100) != HAL_OK) return HAL_ERROR;",
            ])
            if size == 1:
                lines.append("    *out = data[0];")
            else:
                lines.append("    uint16_t raw = (data[0] << 8) | data[1];")
                if cf.get("shift", 0) > 0:
                    lines.append(f"    raw = raw >> {cf['shift']};")
                if cf.get("mask"):
                    lines.append(f"    raw = raw & {cf['mask']};")
                lines.append("    *out = raw;")
            lines.append("    return HAL_OK;")
            lines.append("}")
            lines.append("")

    # 2c) Implement payload-field Read<Pascal>()
    for pf in meta.get("payload_fields", []):
        pascal = "".join(w.capitalize() for w in pf["name"].split("_"))
        base_ctype = pf["type"].replace("[", "").replace("]", "")
        ctype = CTYPE.get(base_ctype, "uint32_t")
        size = pf["size"]
        tok = snake_case(pf["name"]).upper()
        scale = pf.get("scale_factor", 1)

        lines.extend([
            f"HAL_StatusTypeDef {UPPER}_Read{pascal}(",
            f"I2C_HandleTypeDef *hi2c, uint16_t addr8bit, {ctype} *out) {{",
            f"    uint8_t cmd = REG_{tok};",
            f"    uint8_t data[{size}];",
            "    if (HAL_I2C_Master_Transmit(hi2c, addr8bit, &cmd, 1, 100) != HAL_OK) return HAL_ERROR;",
            f"    if (HAL_I2C_Master_Receive(hi2c, addr8bit, data, {size}, 100) != HAL_OK) return HAL_ERROR;",
        ])
        if size == 2:
            lines.append("    uint16_t raw = (data[0] << 8) | data[1];")
        else:
            lines.append("    uint32_t raw = ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | data[3];")
        if pf.get("shift", 0) > 0:
            lines.append(f"    raw = raw >> {pf['shift']};")
        if pf.get("mask"):
            lines.append(f"    raw = raw & {pf['mask']};")
        lines.append(f"    *out = raw * {scale};")
        lines.append("    return HAL_OK;")
        lines.append("}")

    return lines


def gen_sensor_hal_wrapper(meta: dict, out_dir: str):
    """
    Emit:
      • Core/Inc/drivers/<sensor>.h
      • Core/Src/drivers/<sensor>.c
    """
    name = meta["name"]
    SC = snake_case(name)

    inc_drv_dir = os.path.join(out_dir, "Inc", "drivers")
    src_drv_dir = os.path.join(out_dir, "Src", "drivers")
    os.makedirs(inc_drv_dir, exist_ok=True)
    os.makedirs(src_drv_dir, exist_ok=True)

    # Write HAL header
    out_hal_h = os.path.join(inc_drv_dir, f"{SC}.h")
    hal_hdr_lines = build_hal_header_lines(name, meta)
    with open(out_hal_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hal_hdr_lines))
    print(f"Wrote {out_hal_h}")

    # Write HAL source
    out_hal_c = os.path.join(src_drv_dir, f"{SC}.c")
    hal_src_lines = build_hal_source_lines(name, meta)
    with open(out_hal_c, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(hal_src_lines))
    print(f"Wrote {out_hal_c}")
