"""
setup_env.py — AMD Windows AI one-time environment setup wizard.

Detects your GPU, installs the correct backends, and verifies everything works.
Run once on a fresh machine or after a clean Python install.

Usage:
    python scripts/setup_env.py
    python scripts/setup_env.py --silent     # non-interactive, install all
    python scripts/setup_env.py --dry-run    # show what would be installed
"""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="AMD Windows AI one-time environment setup")
    p.add_argument("--silent",  action="store_true", help="Non-interactive mode, install all")
    p.add_argument("--dry-run", action="store_true", help="Show plan, do not install")
    return p.parse_args()


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1


def pip(pkg, extra=""):
    cmd = f'"{sys.executable}" -m pip install {pkg} {extra} -q'
    out, err, code = run(cmd, timeout=300)
    return code == 0


def try_import(name):
    try:
        m = __import__(name.replace("-", "_"))
        return True, getattr(m, "__version__", "?")
    except ImportError:
        return False, None


def detect_gpu():
    out, _, rc = run(
        'powershell -command "Get-WmiObject Win32_VideoController | '
        'Where-Object {$_.AdapterCompatibility -like \'*AMD*\' -or $_.Name -like \'*Radeon*\'} | '
        'Select-Object Name, AdapterRAM | ConvertTo-Json"'
    )
    if rc != 0 or not out or out.strip() in ("", "null", "[]"):
        return None, 0
    try:
        data = json.loads(out)
        if isinstance(data, list):
            data = data[0]
        name = data.get("Name", "Unknown AMD GPU")
        ram = data.get("AdapterRAM", 0)
        return name, round(ram / (1024 ** 3)) if ram else 0
    except Exception:
        return None, 0


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def ask(prompt, default="y"):
    resp = input(f"  {prompt} [{default.upper() if default=='y' else default}/{('N' if default=='y' else 'y')}]: ").strip().lower()
    if not resp:
        resp = default
    return resp == "y"


BACKENDS = [
    # (import_name, pip_name, description, required)
    ("torch_directml",  "torch-directml",       "PyTorch DirectML — Stable Diffusion, DirectML compute", True),
    ("onnxruntime",     "onnxruntime-directml",  "ONNX Runtime DirectML — model inference (BERT, Whisper, ResNet)", True),
    ("llama_cpp",       "llama-cpp-python",      "llama-cpp-python — local LLMs via Vulkan backend", True),
    ("faster_whisper",  "faster-whisper",        "Faster-Whisper — speech-to-text", True),
    ("diffusers",       "diffusers",             "HuggingFace Diffusers — Stable Diffusion pipeline", True),
    ("transformers",    "transformers",          "HuggingFace Transformers — NLP models", True),
    ("torch",           "torch",                 "PyTorch base (CPU) — required by diffusers/transformers", True),
    ("optimum",         "optimum[onnxruntime]",  "HuggingFace Optimum — ONNX export/optimization", False),
    ("huggingface_hub", "huggingface-hub",       "HuggingFace Hub — model downloads", False),
    ("accelerate",      "accelerate",            "HuggingFace Accelerate — model offloading", False),
]


def main():
    args = parse_args()
    silent = args.silent
    dry_run = args.dry_run

    print("\n" + "="*60)
    print("  AMD Windows AI Toolkit — One-Time Setup Wizard")
    print("="*60)
    print(f"  Python  : {platform.python_version()}  ({platform.machine()})")
    print(f"  OS      : {platform.platform()[:55]}")

    # Python check
    if sys.version_info < (3, 10):
        print("\n  ERROR: Python 3.10+ required.")
        print("  Download: https://python.org/downloads")
        sys.exit(1)
    print(f"  Python OK: {platform.python_version()}")

    # GPU detection
    section("Step 1 — GPU Detection")
    gpu_name, vram_gb = detect_gpu()
    if gpu_name:
        print(f"  Found : {gpu_name} ({vram_gb} GB VRAM)")
    else:
        print("  WARNING: No AMD GPU detected via WMI.")
        print("  Make sure AMD Adrenalin drivers are installed.")
        print("  Install anyway? This may still work after driver install.")
        if not silent and not ask("Continue setup?", "y"):
            print("  Aborted.")
            sys.exit(0)

    # Check onnxruntime conflict
    section("Step 2 — Conflict Check")
    plain_ort, _ = try_import("onnxruntime")
    if plain_ort:
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "DmlExecutionProvider" not in providers:
                print("  CONFLICT: plain 'onnxruntime' is installed without DirectML support.")
                print("  This must be replaced with 'onnxruntime-directml'.")
                if dry_run:
                    print("  [DRY RUN] Would run: pip uninstall onnxruntime -y")
                else:
                    if silent or ask("Remove plain onnxruntime and install onnxruntime-directml?", "y"):
                        print("  Removing plain onnxruntime...")
                        run(f'"{sys.executable}" -m pip uninstall onnxruntime -y')
                        print("  Done.")
            else:
                print("  onnxruntime-directml: OK (DmlExecutionProvider available)")
        except Exception:
            pass
    else:
        print("  No onnxruntime conflict detected.")

    # Install backends
    section("Step 3 — Backend Installation")

    results = []
    for import_name, pkg_name, desc, required in BACKENDS:
        already, ver = try_import(import_name)
        if already:
            print(f"  ✓ {pkg_name:<28} (already installed: {ver})")
            results.append((pkg_name, True, ver, False))
            continue

        label = "REQUIRED" if required else "optional"
        if dry_run:
            print(f"  [DRY RUN] Would install: {pkg_name}  ({label})")
            results.append((pkg_name, False, None, True))
            continue

        do_install = silent or ask(f"Install {pkg_name}? ({label}) — {desc}", "y")
        if not do_install:
            print(f"  — Skipped {pkg_name}")
            results.append((pkg_name, False, None, False))
            continue

        print(f"  Installing {pkg_name}...")
        ok = pip(pkg_name)
        if ok:
            _, ver = try_import(import_name)
            print(f"  ✓ {pkg_name} installed ({ver})")
        else:
            print(f"  ✗ Failed to install {pkg_name}")
        results.append((pkg_name, ok, ver if ok else None, True))

    # Verify GPU visibility per backend
    section("Step 4 — Backend Verification")

    # torch-directml verification
    tdml_ok, _ = try_import("torch_directml")
    if tdml_ok:
        try:
            import torch_directml
            device_count = torch_directml.device_count()
            if device_count > 0:
                print(f"  ✓ torch-directml: {device_count} DirectML device(s) found")
            else:
                print("  ✗ torch-directml: 0 devices — update AMD drivers")
        except Exception as e:
            print(f"  ✗ torch-directml error: {e}")

    # onnxruntime-directml verification
    ort_ok, _ = try_import("onnxruntime")
    if ort_ok:
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "DmlExecutionProvider" in providers:
                print(f"  ✓ onnxruntime-directml: DmlExecutionProvider available")
            else:
                print(f"  ✗ onnxruntime: DmlExecutionProvider NOT available (providers: {providers})")
        except Exception as e:
            print(f"  ✗ onnxruntime error: {e}")

    # llama-cpp-python verification
    lcpp_ok, _ = try_import("llama_cpp")
    if lcpp_ok:
        print("  ✓ llama-cpp-python: importable (Vulkan backend active if drivers OK)")

    # Summary
    section("Setup Complete")
    installed = [r for r in results if r[1] and r[3]]
    failed    = [r for r in results if r[3] and not r[1]]
    skipped   = [r for r in results if not r[3] and not r[1]]

    print(f"  Installed : {len(installed)} packages")
    print(f"  Failed    : {len(failed)} packages")
    print(f"  Skipped   : {len(skipped)} packages")

    if failed:
        print("\n  Failed packages:")
        for name, *_ in failed:
            print(f"    pip install {name}")

    print("\n  Run the health check anytime:")
    print("    python scripts\\doctor.py\n")

    if not dry_run and gpu_name:
        print("  Your AMD GPU is set up. Pick your use case:")
        print("    Image gen  →  github.com/ChharithOeun/stable-diffusion-amd-windows")
        print("    Local LLMs →  github.com/ChharithOeun/llm-amd-windows")
        print("    Whisper    →  github.com/ChharithOeun/whisper-amd-windows")
        print("    ONNX       →  github.com/ChharithOeun/onnxruntime-directml-setup\n")


if __name__ == "__main__":
    main()
