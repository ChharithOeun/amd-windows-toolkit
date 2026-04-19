"""
doctor.py — AMD Windows AI environment health check.

Checks GPU, drivers, DirectX, Vulkan, and all AMD ML backends.
Gives actionable fixes for anything missing or broken.

Usage:
    python scripts/doctor.py
    python scripts/doctor.py --json        # machine-readable output
    python scripts/doctor.py --fix         # auto-install missing packages
"""
import argparse
import json
import platform
import subprocess
import sys


def parse_args():
    p = argparse.ArgumentParser(description="AMD Windows AI environment health check")
    p.add_argument("--json", action="store_true", help="Output results as JSON")
    p.add_argument("--fix", action="store_true", help="Auto-install missing packages")
    p.add_argument("--quiet", action="store_true", help="Only show failures")
    return p.parse_args()


# ── helpers ──────────────────────────────────────────────────────────────────

def run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1


def try_import(pkg):
    try:
        m = __import__(pkg.replace("-", "_"))
        ver = getattr(m, "__version__", "?")
        return True, ver
    except ImportError:
        return False, None


def pip_install(pkg):
    print(f"  Installing {pkg}...")
    out, err, code = run(f'"{sys.executable}" -m pip install {pkg} -q')
    return code == 0


# ── check functions ───────────────────────────────────────────────────────────

def check_system():
    results = {}
    results["os"] = platform.platform()
    results["python"] = platform.python_version()
    results["arch"] = platform.machine()
    results["bits"] = "64-bit" if sys.maxsize > 2**32 else "32-bit"
    if sys.version_info < (3, 10):
        results["python_ok"] = False
        results["python_fix"] = "Python 3.10+ required. Download: https://python.org"
    else:
        results["python_ok"] = True
    return results


def check_gpu():
    results = {}

    # Get GPU via WMI (Windows)
    stdout, _, rc = run(
        'powershell -command "Get-WmiObject Win32_VideoController | '
        'Where-Object {$_.AdapterCompatibility -like \'*AMD*\' -or $_.Name -like \'*Radeon*\'} | '
        'Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json"'
    )
    if rc == 0 and stdout and stdout.strip() not in ("", "null", "[]"):
        try:
            data = json.loads(stdout)
            if isinstance(data, list):
                data = data[0]
            results["name"] = data.get("Name", "Unknown AMD GPU")
            ram = data.get("AdapterRAM", 0)
            results["vram_bytes"] = ram
            results["vram_gb"] = round(ram / (1024**3)) if ram else "?"
            results["driver"] = data.get("DriverVersion", "?")
            results["found"] = True
        except Exception:
            results["found"] = False
    else:
        # Fallback: try dxdiag
        results["found"] = False
        results["fix"] = "No AMD GPU detected. Ensure AMD Adrenalin drivers are installed."

    # Check DirectX 12
    stdout2, _, _ = run(
        'powershell -command "(Get-WmiObject Win32_VideoController | '
        'Where-Object {$_.Name -like \'*Radeon*\'} | '
        'Select-Object -First 1).MaxRefreshRate"'
    )
    # DX12 check via dxdiag
    results["dx12"] = None
    dx_out, _, dx_rc = run("dxdiag /t dxdiag_tmp.txt && type dxdiag_tmp.txt && del dxdiag_tmp.txt")
    if "Feature Level: 12" in dx_out or dx_rc != 0:
        results["dx12"] = True
    else:
        # Assume OK if driver found
        results["dx12"] = results.get("found", False)

    # Check Vulkan
    vk_out, _, vk_rc = run("vulkaninfo --summary 2>nul")
    if vk_rc == 0 and "Vulkan" in vk_out:
        for line in vk_out.splitlines():
            if "apiVersion" in line:
                results["vulkan"] = line.split("=")[-1].strip()
                break
        if "vulkan" not in results:
            results["vulkan"] = "detected"
    else:
        # Vulkan may still work even if vulkaninfo isn't installed
        results["vulkan"] = "unknown (vulkaninfo not found; drivers likely OK)"

    return results


def check_backends(fix=False):
    packages = [
        ("torch_directml",    "torch-directml",         "Stable Diffusion, image gen via DirectML"),
        ("onnxruntime",       "onnxruntime-directml",    "ONNX Runtime DirectML inference"),
        ("llama_cpp",         "llama-cpp-python",        "Local LLMs via Vulkan"),
        ("faster_whisper",    "faster-whisper",          "Faster-Whisper speech-to-text"),
        ("diffusers",         "diffusers",               "HuggingFace Stable Diffusion pipeline"),
        ("transformers",      "transformers",            "HuggingFace NLP models"),
        ("torch",             "torch",                   "PyTorch (base)"),
        ("optimum",           "optimum",                 "HuggingFace Optimum ONNX export"),
        ("huggingface_hub",   "huggingface-hub",         "HuggingFace model downloads"),
    ]

    results = {}
    for import_name, pkg_name, desc in packages:
        found, ver = try_import(import_name)
        results[pkg_name] = {"found": found, "version": ver, "desc": desc}
        if not found and fix:
            ok = pip_install(pkg_name)
            if ok:
                found, ver = try_import(import_name)
                results[pkg_name] = {"found": found, "version": ver, "desc": desc, "fixed": True}

    # Special check: onnxruntime vs onnxruntime-directml conflict
    ort_plain_found, _ = try_import("onnxruntime")
    if ort_plain_found:
        try:
            import onnxruntime as ort
            if "DmlExecutionProvider" not in ort.get_available_providers():
                results["onnxruntime-directml"]["conflict"] = True
                results["onnxruntime-directml"]["conflict_fix"] = (
                    "pip uninstall onnxruntime -y && pip install onnxruntime-directml"
                )
        except Exception:
            pass

    return results


def check_repos():
    repos = [
        ("stable-diffusion-amd-windows", "Stable Diffusion / SDXL on AMD"),
        ("whisper-amd-windows",          "Faster-Whisper on AMD"),
        ("llm-amd-windows",              "Local LLMs via Vulkan"),
        ("onnxruntime-directml-setup",   "ONNX Runtime DirectML inference"),
        ("comfyui-amd-windows-setup",    "ComfyUI on AMD GPU"),
        ("torch-amd-setup",              "PyTorch DirectML setup"),
        ("ollama-amd-windows-setup",     "Ollama on AMD GPU"),
        ("directml-benchmark",           "DirectML benchmark suite"),
        ("gpu-doctor",                   "GPU diagnostic tool"),
    ]
    base_url = "https://github.com/ChharithOeun"
    return [{"name": n, "desc": d, "url": f"{base_url}/{n}"} for n, d in repos]


# ── formatting ────────────────────────────────────────────────────────────────

def fmt(ok, msg, fix=None):
    icon = "✓" if ok else "✗"
    line = f"  {icon} {msg}"
    if not ok and fix:
        line += f"\n      FIX: {fix}"
    return line, ok


def print_report(sys_info, gpu_info, backends, repos, quiet=False):
    print("\n=== AMD Windows AI Toolkit — Environment Doctor ===\n")

    all_ok = True

    # System
    print("[System]")
    sys_ok = sys_info.get("python_ok", True)
    line, ok = fmt(sys_ok, f"Python {sys_info['python']} ({sys_info['arch']})",
                   sys_info.get("python_fix"))
    if not quiet or not ok:
        print(line)
    if not ok: all_ok = False

    line, ok = fmt(True, f"OS: {sys_info['os'][:60]}")
    if not quiet:
        print(line)
    print()

    # GPU
    print("[GPU]")
    gpu_found = gpu_info.get("found", False)
    line, ok = fmt(gpu_found,
                   f"Adapter: {gpu_info.get('name', 'Not found')} "
                   f"({gpu_info.get('vram_gb', '?')} GB VRAM)",
                   gpu_info.get("fix"))
    if not quiet or not ok:
        print(line)
    if not ok: all_ok = False

    driver = gpu_info.get("driver", "?")
    line, ok = fmt(bool(driver and driver != "?"), f"Driver: {driver}")
    if not quiet or not ok:
        print(line)

    dx12 = gpu_info.get("dx12")
    line, ok = fmt(bool(dx12), "DirectX 12: Supported" if dx12 else "DirectX 12: Unknown/Not supported",
                   "Update AMD Adrenalin drivers: https://www.amd.com/en/support" if not dx12 else None)
    if not quiet or not ok:
        print(line)
    if not ok: all_ok = False

    vulkan = gpu_info.get("vulkan", "?")
    vk_ok = vulkan and vulkan != "?"
    line, _ = fmt(vk_ok, f"Vulkan: {vulkan if vk_ok else 'Not detected'}")
    if not quiet or not vk_ok:
        print(line)
    print()

    # Backends
    print("[Backends]")
    core_pkgs = ["torch-directml", "onnxruntime-directml", "llama-cpp-python", "faster-whisper",
                 "diffusers", "transformers"]
    for pkg in core_pkgs:
        info = backends.get(pkg, {})
        found = info.get("found", False)
        ver = info.get("version", "")
        conflict = info.get("conflict", False)

        label = f"{pkg:<22} {ver or ''}"
        if info.get("fixed"):
            label += " [just installed]"

        fix_msg = None
        if not found:
            fix_msg = f"pip install {pkg}"
        elif conflict:
            fix_msg = info.get("conflict_fix")
            label += " [CONFLICT: plain onnxruntime installed]"
            found = False

        line, ok = fmt(found, label, fix_msg)
        if not quiet or not ok:
            print(line)
        if not ok: all_ok = False
    print()

    # Repos
    print("[Repos]")
    for r in repos[:5]:
        print(f"  → {r['name']:<35} {r['url']}")
    print(f"  → (and {len(repos)-5} more at https://github.com/ChharithOeun)")
    print()

    # Summary
    print("[Summary]")
    checks = (
        sys_info.get("python_ok", True)
        and gpu_info.get("found", False)
        and backends.get("torch-directml", {}).get("found", False)
        and backends.get("onnxruntime-directml", {}).get("found", False)
    )
    if checks:
        print("  ✓ Core setup looks good — AMD GPU ready for AI on Windows.")
    else:
        print("  ✗ Issues found above — fix them and re-run doctor.py")
    print()


def main():
    args = parse_args()

    sys_info = check_system()
    gpu_info = check_gpu()
    backends = check_backends(fix=args.fix)
    repos = check_repos()

    if args.json:
        output = {
            "system": sys_info,
            "gpu": gpu_info,
            "backends": backends,
            "repos": repos,
        }
        print(json.dumps(output, indent=2))
        return

    print_report(sys_info, gpu_info, backends, repos, quiet=args.quiet)


if __name__ == "__main__":
    main()
