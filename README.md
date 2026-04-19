# amd-windows-toolkit

> **Everything you need to run AI/ML on AMD GPUs on Windows — no ROCm, no Linux, no excuses.**

[![CI](https://github.com/ChharithOeun/amd-windows-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/ChharithOeun/amd-windows-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A curated collection of tools, guides, and scripts for running ML workloads on AMD GPUs on Windows. Each repo in this ecosystem solves one specific problem — this toolkit is the starting point that points you to the right one.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-FFDD00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/chharith)

---

## Quick Health Check

Run this first on any AMD Windows machine:

```bat
git clone https://github.com/ChharithOeun/amd-windows-toolkit.git
cd amd-windows-toolkit
pip install -r requirements.txt
python scripts\doctor.py
```

Sample output:

```
=== AMD Windows AI Toolkit — Environment Doctor ===

[System]
  OS             : Windows 11 23H2 (Build 22631)
  Python         : 3.11.9
  Architecture   : AMD64

[GPU]
  Adapter        : AMD Radeon RX 7800 XT
  VRAM           : 16 GB
  Driver         : 24.1.1
  DirectX 12     : ✓ Supported
  Vulkan         : ✓ Supported (1.3.275)

[Backends]
  torch-directml : ✓ 0.2.5.dev240214  (Stable Diffusion, image gen)
  onnxruntime-dm : ✓ 1.18.0           (ONNX inference, Whisper)
  llama-cpp-py   : ✓ 0.2.90           (Local LLMs)
  faster-whisper : ✓ 1.0.3            (Speech-to-text)
  diffusers      : ✓ 0.29.2           (SD / SDXL pipeline)
  transformers   : ✓ 4.41.2           (NLP models)

[Repos]
  stable-diffusion-amd-windows : ✓ Ready
  whisper-amd-windows          : ✓ Ready
  llm-amd-windows              : ✓ Ready
  onnxruntime-directml-setup   : ✓ Ready

[Summary]
  6/6 checks passed — Your AMD GPU is fully set up for AI on Windows.
```

---

## The Ecosystem

### Image Generation

| Repo | What it does | Backend |
|------|-------------|---------|
| [stable-diffusion-amd-windows](https://github.com/ChharithOeun/stable-diffusion-amd-windows) | SD 1.5, SD 2.x, SDXL image generation | DirectML |
| [comfyui-amd-windows-setup](https://github.com/ChharithOeun/comfyui-amd-windows-setup) | ComfyUI node-based workflow | DirectML |

### Speech & Audio

| Repo | What it does | Backend |
|------|-------------|---------|
| [whisper-amd-windows](https://github.com/ChharithOeun/whisper-amd-windows) | Faster-Whisper speech-to-text | DirectML |

### Language Models

| Repo | What it does | Backend |
|------|-------------|---------|
| [llm-amd-windows](https://github.com/ChharithOeun/llm-amd-windows) | Local LLMs (Llama 3, Mistral, Phi-3, Qwen2.5) | Vulkan |
| [ollama-amd-windows-setup](https://github.com/ChharithOeun/ollama-amd-windows-setup) | Ollama GUI/API for local LLMs | Vulkan |
| [claude-code-local-models-setup](https://github.com/ChharithOeun/claude-code-local-models-setup) | Claude Code with local model backends | Various |

### Model Infrastructure

| Repo | What it does | Backend |
|------|-------------|---------|
| [onnxruntime-directml-setup](https://github.com/ChharithOeun/onnxruntime-directml-setup) | ONNX Runtime inference (BERT, ResNet, Whisper) | DirectML |
| [torch-amd-setup](https://github.com/ChharithOeun/torch-amd-setup) | PyTorch with DirectML environment setup | DirectML |
| [jax-amd-gpu-setup](https://github.com/ChharithOeun/jax-amd-gpu-setup) | JAX on AMD GPU Windows | DirectML/IREE |
| [directml-benchmark](https://github.com/ChharithOeun/directml-benchmark) | GPU performance benchmarks | DirectML |

### ROCm / Linux Migration

| Repo | What it does |
|------|-------------|
| [rocm-migration-5x-to-6x](https://github.com/ChharithOeun/rocm-migration-5x-to-6x) | Migrate ROCm 5.x → 6.x on Linux |

### Utilities

| Repo | What it does |
|------|-------------|
| [gpu-doctor](https://github.com/ChharithOeun/gpu-doctor) | AMD GPU diagnostic tool |
| [wsl-benchmark](https://github.com/ChharithOeun/wsl-benchmark) | WSL2 performance benchmarking |
| [wsl-disk-doctor](https://github.com/ChharithOeun/wsl-disk-doctor) | WSL2 disk space cleanup |
| [cfa-safe-delete](https://github.com/ChharithOeun/cfa-safe-delete) | Safe file deletion utility |

---

## Which Backend Should I Use?

AMD GPUs on Windows can't use CUDA or ROCm. The three practical backends are:

```
Your use case
    │
    ├── Image generation (SD, SDXL, ComfyUI)
    │       └── DirectML  →  stable-diffusion-amd-windows / comfyui-amd-windows-setup
    │
    ├── Local LLMs (Llama, Mistral, Phi, Qwen)
    │       └── Vulkan    →  llm-amd-windows / ollama-amd-windows-setup
    │
    ├── Speech-to-text (Whisper)
    │       └── DirectML  →  whisper-amd-windows
    │
    ├── Custom model inference (ONNX, BERT, ResNet)
    │       └── DirectML  →  onnxruntime-directml-setup
    │
    ├── PyTorch training / research
    │       └── DirectML  →  torch-amd-setup
    │
    └── Need ROCm?
            └── Linux only → rocm-migration-5x-to-6x (guides Linux setup)
```

---

## One-Time Setup (New Machine)

Run this on a fresh Windows install to get everything working:

```bat
git clone https://github.com/ChharithOeun/amd-windows-toolkit.git
cd amd-windows-toolkit
python scripts\setup_env.py
```

This script will:
1. Check Python version and pip
2. Install the correct AMD GPU backends (`torch-directml`, `onnxruntime-directml`, `llama-cpp-python` with Vulkan)
3. Verify GPU is detected by each backend
4. Print a summary with links to the relevant repos

---

## VRAM Quick Reference

| Your VRAM | What runs well |
|-----------|---------------|
| 4GB | SD 1.5 (512px), small LLMs (Phi-3 Mini), ONNX inference |
| 8GB | SD 1.5 (768px), SDXL (with attention slicing), 7B LLMs (Q4), Whisper |
| 12GB | SDXL comfortable, 13B LLMs partial GPU, all ONNX models |
| 16GB | SDXL full, 13B LLMs full GPU, large ONNX batch |
| 20–24GB | SDXL + refiner, 70B LLMs partial, everything comfortable |

---

## Driver & Software Requirements

| Software | Minimum | Recommended |
|----------|---------|-------------|
| Windows | 10 21H2 | 11 23H2 |
| Python | 3.10 | 3.11 |
| AMD Adrenalin Drivers | 22.x | 24.x (latest) |
| DirectX | 12.0 | 12.1 |
| Vulkan | 1.2 | 1.3 |

Download latest AMD drivers: [amd.com/support](https://www.amd.com/en/support)

---

## Common Issues Across All Repos

### `No GPU found` / `DirectML not available`

1. Update drivers: [amd.com/support](https://www.amd.com/en/support)
2. Check DirectX 12: run `dxdiag` → Display → Feature Level must show `12_0` or higher
3. Run `python scripts\doctor.py` for a full diagnosis

### `onnxruntime` and `onnxruntime-directml` conflict

They cannot coexist. Always use `onnxruntime-directml`:

```bat
pip uninstall onnxruntime -y
pip install onnxruntime-directml
```

### Slow first run / shader compilation

All DirectML and Vulkan backends compile GPU shaders on first run for each model. This is normal — subsequent runs use the cache and are much faster.

### Out of memory on SDXL or large LLMs

See the VRAM table above. Use:
- `--attention-slicing` for Stable Diffusion
- `--gpu-layers 20` (instead of `-1`) for LLMs to partially offload
- fp16/Q4 quantized models where available

---

## Contributing

This toolkit is a living index. If you've tested something on AMD Windows that should be here, open an issue or PR. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).

---

*If this ecosystem saved you time, consider buying me a coffee:*

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/chharith)
