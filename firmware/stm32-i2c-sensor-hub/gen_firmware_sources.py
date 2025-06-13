#!/usr/bin/env python3
"""
gen_firmware_sources.py

In STM32CubeIDE pre-build steps (with current directory = Debug), add:
    python ../gen_firmware_sources.py

It locates <repo_root>/metadata for input, but writes generated files into
<stm32_project_root>/Core (i.e., alongside Debug, Src, Inc folders).
"""
import sys
from pathlib import Path

def find_repo_root(start: Path) -> Path:
    p = start
    while True:
        if (p / "metadata").is_dir():
            return p
        if p.parent == p:
            break
        p = p.parent
    sys.exit("Error: 'metadata' directory not found upward from script")

def main():
    # script is placed in STM32 project root folder
    script_dir = Path(__file__).resolve().parent
    # locate metadata in repo root
    repo_root = find_repo_root(script_dir)
    metadata_dir = repo_root / "metadata"
    if not metadata_dir.is_dir():
        sys.exit(f"Error: metadata directory missing: {metadata_dir}")
    # output into this STM32 project’s Core folder
    out_dir = script_dir / "Core"
    out_dir.mkdir(parents=True, exist_ok=True)

    tools_path = metadata_dir / "tools"
    if tools_path.is_dir():
        sys.path.insert(0, str(tools_path))
    try:
        from generator import run_codegen
    except ImportError:
        sys.exit("Error: cannot import generator.run_codegen (check metadata/tools)")

    try:
        run_codegen.main(metadata_dir, out_dir)
    except Exception as e:
        sys.exit(f"Code generation failed: {e!r}")

    print(f"gen_firmware_sources: done (metadata={metadata_dir}, output={out_dir})")

if __name__ == "__main__":
    main()
