# Installation Guide

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Windows | 10 21H2 | 11 23H2 |
| Python | 3.10 | 3.11 |
| AMD Adrenalin Drivers | 22.x | 24.x (latest) |
| DirectX | 12.0 | 12.1 |
| Vulkan | 1.2 | 1.3 |

## Step 1 — Install AMD Drivers

Download and install the latest AMD Adrenalin drivers:

- [amd.com/support](https://www.amd.com/en/support)

Select your GPU model and download the latest "Adrenalin Edition" driver. Reboot after install.

## Step 2 — Install Python

Download Python 3.11 (recommended):

- [python.org/downloads](https://www.python.org/downloads/)

During install, check **"Add Python to PATH"**.

Verify:

```bat
python --version
```

## Step 3 — Clone This Repo

```bat
git clone https://github.com/ChharithOeun/amd-windows-toolkit.git
cd amd-windows-toolkit
```

## Step 4 — Run the Setup Wizard

```bat
python scripts\setup_env.py
```

This will:
1. Detect your AMD GPU
2. Check for package conflicts
3. Install all AMD ML backends
4. Verify GPU is visible to each backend

## Step 5 — Verify Your Setup

```bat
python scripts\doctor.py
```

All checks should show ✓. If anything fails, doctor.py will show the exact fix command.

## Manual Backend Installation

If you prefer to install only what you need:

```bat
# For Stable Diffusion / image generation
pip install torch-directml diffusers transformers accelerate

# For ONNX inference (BERT, ResNet, Whisper ONNX)
pip install onnxruntime-directml

# For local LLMs (Llama, Mistral, Phi, Qwen)
pip install llama-cpp-python

# For speech-to-text
pip install faster-whisper
```

**Do not install both `onnxruntime` and `onnxruntime-directml`** — they conflict. Always use `onnxruntime-directml` on AMD Windows.

## Troubleshooting

**`No AMD GPU detected`**
- Confirm drivers are installed: open Device Manager → Display Adapters
- Run `dxdiag` → Display tab → confirm Feature Level shows 12_0 or higher

**`onnxruntime-directml` shows no DirectML provider**
```bat
pip uninstall onnxruntime -y
pip install onnxruntime-directml
```

**Slow first run**
All DirectML and Vulkan backends compile shaders on first use per model. This is normal — subsequent runs use cached shaders.

**Out of memory (SDXL, large LLMs)**
See the VRAM table in [README.md](README.md). Use `--attention-slicing` for SD or `--gpu-layers 20` for LLMs to reduce VRAM usage.
