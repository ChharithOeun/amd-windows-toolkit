# Contributing

Contributions are welcome. This toolkit is a living index of AMD Windows AI resources.

## What We Accept

- New repos added to the ecosystem table
- Fixes to broken links or outdated versions
- Better GPU detection logic for `doctor.py` or `check_gpu.py`
- New scripts useful across the ecosystem (benchmarking, model management, etc.)
- Documentation improvements
- Verified test results on new AMD GPU models

## How to Contribute

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Test on an AMD GPU on Windows if possible
5. Submit a pull request with a clear description

## Adding a Repo to the Ecosystem Table

If you have a repo that helps AMD GPU users on Windows:

1. Open an issue using the Feature Request template
2. Include: repo URL, what it does, which backend it uses (DirectML / Vulkan)
3. We'll verify it works before adding it to the table

## Code Style

- Python 3.10+ compatible
- No external dependencies for diagnostic scripts (`doctor.py`, `check_gpu.py`, `check_gpu.py`)
- Standard library only for the core toolkit; use `try_import` pattern for optional packages
- Docstring at the top of each script with usage example

## Reporting Issues

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:
- GPU model and VRAM
- AMD driver version
- Windows version
- Python version
- Full error output

The output of `python scripts\doctor.py` covers most of these automatically.

## License

By contributing you agree your code will be released under the [MIT License](LICENSE).
