"""
check_gpu.py — Quick AMD GPU status snapshot.

Prints GPU name, VRAM, driver version, DirectX level, and Vulkan support.
No dependencies required beyond the standard library.

Usage:
    python scripts/check_gpu.py
    python scripts/check_gpu.py --json
"""
import argparse
import json
import subprocess
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Quick AMD GPU status check")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    return p.parse_args()


def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1


def get_gpu_info():
    info = {}

    # WMI query for AMD GPU
    out, _, rc = run(
        'powershell -command "Get-WmiObject Win32_VideoController | '
        'Where-Object {$_.AdapterCompatibility -like \'*AMD*\' -or $_.Name -like \'*Radeon*\'} | '
        'Select-Object Name, AdapterRAM, DriverVersion, VideoModeDescription | ConvertTo-Json"'
    )
    if rc == 0 and out and out.strip() not in ("", "null", "[]"):
        try:
            data = json.loads(out)
            if isinstance(data, list):
                data = data[0]
            info["name"]        = data.get("Name", "Unknown AMD GPU")
            ram                 = data.get("AdapterRAM", 0)
            info["vram_bytes"]  = ram
            info["vram_gb"]     = round(ram / (1024 ** 3)) if ram else "?"
            info["driver"]      = data.get("DriverVersion", "?")
            info["resolution"]  = data.get("VideoModeDescription", "?")
            info["found"]       = True
        except Exception:
            info["found"] = False
    else:
        info["found"] = False

    # DirectX feature level
    dx_out, _, _ = run("dxdiag /t dxdiag_tmp.txt && type dxdiag_tmp.txt && del dxdiag_tmp.txt",
                       timeout=20)
    if "Feature Level: 12" in dx_out:
        info["dx_level"] = "12"
        info["dx_ok"] = True
    elif "Feature Level: 11" in dx_out:
        info["dx_level"] = "11"
        info["dx_ok"] = False
    else:
        info["dx_level"] = "unknown"
        info["dx_ok"] = info.get("found", False)  # assume OK if GPU found

    # Vulkan
    vk_out, _, vk_rc = run("vulkaninfo --summary 2>nul", timeout=8)
    if vk_rc == 0 and "Vulkan" in vk_out:
        for line in vk_out.splitlines():
            if "apiVersion" in line:
                info["vulkan"] = line.split("=")[-1].strip()
                break
        if "vulkan" not in info:
            info["vulkan"] = "detected"
        info["vulkan_ok"] = True
    else:
        info["vulkan"] = "not detected (vulkaninfo missing)"
        info["vulkan_ok"] = info.get("found", False)

    # Additional GPU info via PowerShell
    temp_out, _, _ = run(
        'powershell -command "Get-WmiObject Win32_VideoController | '
        'Where-Object {$_.Name -like \'*Radeon*\'} | '
        'Select-Object -First 1 -ExpandProperty CurrentRefreshRate"'
    )
    if temp_out.isdigit():
        info["refresh_hz"] = int(temp_out)

    return info


def print_status(info):
    print("\n=== AMD GPU Quick Check ===\n")
    found = info.get("found", False)
    print(f"  GPU     : {info.get('name', 'NOT FOUND')}")
    if found:
        print(f"  VRAM    : {info.get('vram_gb', '?')} GB")
        print(f"  Driver  : {info.get('driver', '?')}")
        if info.get("refresh_hz"):
            print(f"  Refresh : {info['refresh_hz']} Hz")
    print(f"  DirectX : {'12 ✓' if info.get('dx_ok') else 'UNKNOWN/UNSUPPORTED ✗'}")
    print(f"  Vulkan  : {info.get('vulkan', '?')} {'✓' if info.get('vulkan_ok') else '✗'}")

    if not found:
        print("\n  FIX: No AMD GPU detected.")
        print("  → Install AMD Adrenalin drivers: https://www.amd.com/en/support")
    if not info.get("dx_ok"):
        print("\n  FIX: DirectX 12 not confirmed.")
        print("  → Update AMD Adrenalin drivers: https://www.amd.com/en/support")

    print("\n  For full diagnostics: python scripts\\doctor.py\n")


def main():
    args = parse_args()
    info = get_gpu_info()

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print_status(info)

    ok = info.get("found", False) and info.get("dx_ok", False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
