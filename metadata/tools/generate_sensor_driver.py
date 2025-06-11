#!/usr/bin/env python3
import os
import re

# ——————————————————————————————————————————————————————————————————————
# Shared helpers (CTYPE, ARRAY_TYPE_RE, snake_case)
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


# ——————————————————————————————————————————————————————————————————————
# Helper for “payload size” logic
# ——————————————————————————————————————————————————————————————————————
def emit_get_sample_size(meta: dict, ctx_struct: str) -> list[str]:
    """
    Emit code for a dynamic get_sample_size() function based on payload_mask.
    """
    lines = []
    lines.append("static uint8_t get_sample_size(void *ctx) {")
    lines.append(f"    {ctx_struct} *c = ({ctx_struct} *)ctx;")
    lines.append("    uint8_t size = 0;")
    for idx, pf in enumerate(meta.get("payload_fields", [])):
        fld_size = pf.get("size", 2)
        lines.append(f"    if (c->payload_mask & (1 << {idx})) size += {fld_size};")
    lines.append("    return size;")
    lines.append("}")
    lines.append("")
    return lines


def build_driver_header_lines(name: str, meta: dict) -> list[str]:
    """
    Build lines for the driver-layer header: Inc/drivers/<sensor>_driver.h
    """
    SC = snake_case(name)
    UPPER = name.upper()
    ctx_struct = f"{UPPER}_Ctx_t"

    lines = [
        f"/* Auto-generated {name}_driver.h; do not edit! */",
        "#pragma once",
        "",
        "#include \"task/sensor_task.h\"  /**< SensorDriver_t, SensorSample_t */",
        "#include \"driver_registry.h\"   /**< SensorRegistry_Register */",
        f"#include \"drivers/{SC}.h\"        /**< HAL-IF–based wrapper */",
        "#include <hal_if.h>",
        "#include <stdint.h>",
        "#include <stdbool.h>",
        "",
        "// ---------------- Public callbacks ----------------",
        f"void {SC}_init_ctx(void *vctx, halif_handle_t h_i2c, uint8_t addr7);",
        f"bool {SC}_configure(void *vctx, uint8_t field_id, uint8_t value);",
        "",
        "// Reader that returns N bytes for each GET_… command:",
        f"bool {SC}_read_config_bytes(void *vctx, uint8_t field_id, uint8_t *out_buf, size_t *out_len);",
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
        "    halif_handle_t   h_i2c;      /**< HAL-IF handle */",
        "    uint8_t          addr7;     /**< 7-bit I²C address */"
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
            lines.append(f"    {c_bas} {key}[{arr_n}];")
        else:
            lines.append(f"    {UPPER}_{key.upper()}_t {key};")

    # 3b) Always add “payload_mask”
    lines.append(f"    uint8_t payload_mask;   /**< which payload bits are enabled */")
    lines.append(f"}} {ctx_struct};")
    lines.append("")

    return lines


def build_driver_source_lines(name: str, meta: dict) -> list[str]:
    """
    Build lines for the driver-layer implementation: Src/drivers/<sensor>_driver.c
    """
    SC = snake_case(name)
    UPPER = name.upper()
    ctx_struct = f"{UPPER}_Ctx_t"
    vtable_name = f"{SC}_driver"

    lines = [
        f"/* Auto-generated {name}_driver.c; do not edit! */",
        f'#include "drivers/{SC}_driver.h"',
        f'#include "config/{SC}_config.h"',
        "#include \"config/protocol.h\"",
        "#include <string.h>",
        "#include <stdbool.h>",
        ""
    ]

    # 4a) ini(): initialize driver (apply defaults + set default mask)
    lines.append("static halif_status_t ini(void *ctx) {")
    lines.append(f"    {ctx_struct} *c = ({ctx_struct} *)ctx;")
    for fld_name in meta.get("config_defaults", {}):
        if fld_name == "all":
            continue
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        lines.append(
            f"    if ({UPPER}_Set{pascal}(c->h_i2c, c->addr7, {SC}_defaults.{fld_name}) != HALIF_OK) return HALIF_ERROR;"
        )
    for fld_name in meta.get("config_defaults", {}):
        if fld_name == "all":
            continue
        lines.append(f"    c->{fld_name} = {SC}_defaults.{fld_name};")

    default_bits = meta.get("default_payload_bits", [])
    default_mask = 0
    for bit in default_bits:
        default_mask |= (1 << bit)
    lines.append(f"    c->payload_mask = 0x{default_mask:02X};  /* default mask */")
    lines.append("    return HALIF_OK;")
    lines.append("}")
    lines.append("")

    # 4b) rd(): pack only selected payload bits into out_buf
    lines.append("static halif_status_t rd(void *ctx, uint8_t out_buf[], uint8_t *out_len) {")
    lines.append(f"    {ctx_struct} *c = ({ctx_struct} *)ctx;")
    lines.append("    uint8_t *cursor = out_buf;")
    lines.append("    uint8_t mask = c->payload_mask;")
    lines.append("    int total_bytes = 0;")
    lines.append("")

    for idx, pf in enumerate(meta.get("payload_fields", [])):
        bitname = f"BIT_{snake_case(pf['name']).upper()}"
        pascal = "".join(w.capitalize() for w in pf["name"].split("_"))
        size = pf["size"]
        read_fn = f"{UPPER}_Read{pascal}"
        lines.append(f"    if (mask & {bitname}) {{")
        base_ctype = pf["type"].replace("[", "").replace("]", "")
        ctype = CTYPE.get(base_ctype, "uint32_t")
        tmp_name = f"var_{pf['name']}"
        lines.extend([
            f"        {ctype} {tmp_name};",
            f"        if ({read_fn}(c->h_i2c, c->addr7, &{tmp_name}) != HALIF_OK) {{",
            "            *out_len = 0;",
            "            return HALIF_ERROR;",
            "        }"
        ])
        if size == 2:
            lines.extend([
                f"        *cursor++ = (uint8_t)({tmp_name} >> 8);",
                f"        *cursor++ = (uint8_t)({tmp_name} & 0xFF);",
                "        total_bytes += 2;"
            ])
        elif size == 4:
            lines.extend([
                f"        *cursor++ = (uint8_t)(({tmp_name} >> 24) & 0xFF);",
                f"        *cursor++ = (uint8_t)(({tmp_name} >> 16) & 0xFF);",
                f"        *cursor++ = (uint8_t)(({tmp_name} >> 8)  & 0xFF);",
                f"        *cursor++ = (uint8_t)(({tmp_name})       & 0xFF);",
                "        total_bytes += 4;"
            ])
        else:
            # General N-byte case
            for b in range(size):
                shift_amt = 8 * (size - 1 - b)
                lines.append(f"        *cursor++ = (uint8_t)(({tmp_name} >> {shift_amt}) & 0xFF);")
            lines.append(f"        total_bytes += {size};")
        lines.append("    }")
        lines.append("")

    lines.extend([
        "    *out_len = total_bytes;",
        "    return HALIF_OK;",
        "}",
        ""
    ])

    # 4c) Multi-byte read_config_bytes()
    lines.append(f"bool {SC}_read_config_bytes(void *vctx, uint8_t field, uint8_t *out_buf, size_t *out_len) {{")
    lines.append(f"    {ctx_struct} *c = ({ctx_struct} *)vctx;")
    lines.append("    switch (field) {")
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        getter = cf.get("getter_cmd")
        size = cf.get("size")
        if fld_name == "all" or getter is None:
            continue
        lines.append(f"      case {getter}:")
        if size == 1:
            lines.append(f"        out_buf[0] = (uint8_t)c->{fld_name};")
            lines.append("        *out_len = 1;")
            lines.append("        return true;")
            lines.append("")
        else:
            # Emit N-byte big-endian splitting
            lines.append(f"        // return {size} bytes (big-endian) for field `{fld_name}`")
            lines.append("        {")
            for i in range(size):
                shift_amt = 8 * (size - 1 - i)
                lines.append(
                    f"            out_buf[{i}] = "
                    f"(uint8_t)((c->{fld_name} >> {shift_amt}) & 0xFF);"
                )
            lines.append(f"            *out_len = {size};")
            lines.append("            return true;")
            lines.append("        }")
            lines.append("")
    # 4c2) payload-mask (always 1 byte)
    lines.extend([
        "      case CMD_GET_PAYLOAD_MASK:",
        "        out_buf[0] = c->payload_mask;",
        "        *out_len = 1;",
        "        return true;",
        ""
    ])

    lines.extend([
        "      default:",
        "        return false;",
        "    }",
        "}",
        ""
    ])

    # 4d) List of supported config field IDs (for get_config_fields())
    field_ids = [
        cf["getter_cmd"]
        for cf in meta.get("config_fields", [])
        if cf.get("getter_cmd") is not None
           and cf.get("setter_cmd") is not None
           and cf["name"] != "all"
    ]
    if field_ids:
        lines.append(f"static const uint8_t {SC}_config_fields[] = {{")
        for fid in field_ids:
            lines.append(f"    {fid},")
        lines.append("};")
        lines.append("")
        lines.extend([
            f"const uint8_t *{SC}_get_config_fields(size_t *count) {{",
            f"    if (count) *count = sizeof({SC}_config_fields) / sizeof({SC}_config_fields[0]);",
            f"    return {SC}_config_fields;",
            "}",
            ""
        ])

    # 4e) get_sample_size() helper
    lines.extend(emit_get_sample_size(meta, ctx_struct))

    # 4f) vtable + GetDriver()
    lines.extend([
        f"static const SensorDriver_t {vtable_name} = {{",
        f"    .init        = (HAL_StatusTypeDef (*)(void *)) ini,",
        f"    .read        = (HAL_StatusTypeDef (*)(void *, uint8_t *, uint8_t *)) rd,",
        f"    .sample_size = get_sample_size,",
        f"    .read_config_bytes = {SC}_read_config_bytes,",
        "};",
        "",
        f"const SensorDriver_t *{UPPER}_GetDriver(void) {{",
        f"    return &{vtable_name};",
        "}",
        ""
    ])

    # 4g) default_period helper
    default_period = meta.get("config_defaults", {}).get("period", 10)
    lines.extend([
        f"static uint32_t {SC}_default_period_ms(void) {{",
        f"    return {default_period} * 100;",  # convert “units of 100ms” to ms
        "}",
        ""
    ])

    # 4h) SensorDriverInfo_t + RegisterDriver()
    lines.extend([
        f"static const SensorDriverInfo_t {SC}_info = {{",
        f"    .type_code            = SENSOR_TYPE_{UPPER},",
        f"    .ctx_size             = sizeof({ctx_struct}),",
        f"    .init_ctx             = {SC}_init_ctx,",
        f"    .get_driver           = {UPPER}_GetDriver,",
        f"    .configure            = {SC}_configure,",
        f"    .read_config_bytes    = {SC}_read_config_bytes,",
        f"    .get_config_fields    = {'NULL' if not field_ids else f'{SC}_get_config_fields'},",
        f"    .get_default_period_ms = {SC}_default_period_ms,  // {default_period} * 100ms",
        "};",
        "",
        f"void {SC}_RegisterDriver(void) {{",
        f"    SensorRegistry_Register(&{SC}_info);",
        "}",
        ""
    ])

    # 4i) init_ctx() and configure()
    lines.extend([
        f"void {SC}_init_ctx(void *vctx, halif_handle_t h_i2c, uint8_t addr7) {{",
        f"    {ctx_struct} *c = ({ctx_struct} *)vctx;",
        "    c->h_i2c  = h_i2c;",
        "    c->addr7  = addr7;",
        "}",
        ""
    ])

    # Gather “computed” fields, their dependencies, and raw formulas
    computed_info = {}
    for cf in meta.get("config_fields", []):
        if cf.get("computed", False):
            computed_info[cf["name"]] = {
                "depends_on": cf.get("depends_on", []),
                "formula":    cf.get("formula", "").strip()
            }

    # 4j) configure() switch, injecting computed logic
    lines.append(f"bool {SC}_configure(void *vctx, uint8_t field_id, uint8_t param) {{")
    lines.append(f"    {ctx_struct} *c = ({ctx_struct} *)vctx;")
    lines.append("    halif_status_t rc;")
    lines.append("")
    lines.append("    switch (field_id) {")
    for cf in meta.get("config_fields", []):
        fld_name = cf["name"]
        setter_cmd = cf.get("setter_cmd")
        is_computed = cf.get("computed", False)

        if not setter_cmd or is_computed:
            continue
        pascal = "".join(w.capitalize() for w in fld_name.split("_"))
        lines.extend([
            f"      case {setter_cmd}:",
            f"        rc = {UPPER}_Set{pascal}(c->h_i2c, c->addr7, ({UPPER}_{fld_name.upper()}_t)param);",
            "        if (rc == HALIF_OK) {",
            f"            c->{fld_name} = ({UPPER}_{fld_name.upper()}_t)param;",
            ""
        ])
        # Recompute any “computed” fields that depend on fld_name
        for comp_name, info in computed_info.items():
            if fld_name in info["depends_on"]:
                raw = info["formula"]
                # Assign the computed field using the raw formula string
                lines.append(f"            // Recompute `{comp_name}` because `{fld_name}` changed")
                lines.append(f"            c->{comp_name} = {raw};")
                # Now push it out via the HAL-IF setter:
                comp_pascal = comp_name.capitalize()
                lines.append(f"            {UPPER}_Set{comp_pascal}(c->h_i2c, c->addr7, c->{comp_name});")
                lines.append("")


        lines.extend([
            "            return true;",
            "        } else {",
            "            return false;",
            "        }",
            ""
        ])

    # (b) No‐op “SET” for any getter‐only field except “all”
    for cf in meta.get("config_fields", []):
        getter_cmd = cf.get("getter_cmd")
        setter_cmd = cf.get("setter_cmd")
        name       = cf.get("name")

        if getter_cmd is None or setter_cmd is not None or name == "all":
            continue

        # getter_cmd is in [CMD_CONFIG_GETTERS_START..CMD_CONFIG_GETTERS_END],
        # so subtracting (30−20)=10 yields the matching SET code in [20..29].
        lines.append(f"      case {getter_cmd} - (CMD_CONFIG_GETTERS_START - CMD_CONFIG_SETTERS_START):")
        lines.append("        // no-op for a read-only (getter-only) field (e.g. calibration)")
        lines.append("        return true;")
        lines.append("")

    # (c) payload-mask setter + default
    lines.extend([
        "      case CMD_SET_PAYLOAD_MASK:",
        "        c->payload_mask = param;",
        "        return true;",
        "",
        # (d) fallback default
        "      default:",
        "        return false;",
        "    }",
        "}",
        ""
    ])

    return lines


def gen_sensor_driver_files(meta: dict, out_dir: str):
    """
    Emit:
      • Core/Inc/drivers/<sensor>_driver.h
      • Core/Src/drivers/<sensor>_driver.c
      • Core/Inc/drivers/<sensor>.h      (HAL-IF wrapper)
      • Core/Src/drivers/<sensor>.c      (HAL-IF wrapper)
    """
    # First generate the HAL-IF–wrapper
    from .hal_generator import gen_sensor_hal_wrapper
    gen_sensor_hal_wrapper(meta, out_dir)

    # Then generate the driver-layer
    SC = snake_case(meta["name"])

    inc_drv_dir = os.path.join(out_dir, "Inc", "drivers")
    src_drv_dir = os.path.join(out_dir, "Src", "drivers")
    os.makedirs(inc_drv_dir, exist_ok=True)
    os.makedirs(src_drv_dir, exist_ok=True)

    # Write driver header
    out_drv_h = os.path.join(inc_drv_dir, f"{SC}_driver.h")
    drv_hdr_lines = build_driver_header_lines(meta["name"], meta)
    with open(out_drv_h, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(drv_hdr_lines))
    print(f"Wrote {out_drv_h}")

    # Write driver source
    out_drv_c = os.path.join(src_drv_dir, f"{SC}_driver.c")
    drv_src_lines = build_driver_source_lines(meta["name"], meta)
    with open(out_drv_c, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(drv_src_lines))
    print(f"Wrote {out_drv_c}")
