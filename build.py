#!/usr/bin/env python3
"""Build script for PyInstaller."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean():
    """Clean all build artifacts and output files."""
    removed_items = []

    # Clean build directories
    build_dirs = ["build", "dist"]
    for dir_name in build_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                removed_items.append(f"Directory: {dir_name}")
            except Exception as e:
                print(f"Warning: Failed to remove {dir_name}: {e}")

    # Clean all __pycache__ directories recursively (excluding .venv)
    for pycache_dir in Path(".").rglob("__pycache__"):
        if pycache_dir.is_dir():
            # Skip .venv directory
            if ".venv" in pycache_dir.parts:
                continue
            try:
                shutil.rmtree(pycache_dir)
                removed_items.append(f"Directory: {pycache_dir}")
            except Exception as e:
                print(f"Warning: Failed to remove {pycache_dir}: {e}")

    # Clean .pyc files (in case any are left, excluding .venv)
    for pyc_file in Path(".").rglob("*.pyc"):
        # Skip .venv directory
        if ".venv" in pyc_file.parts:
            continue
        try:
            pyc_file.unlink()
            removed_items.append(f"File: {pyc_file}")
        except Exception as e:
            print(f"Warning: Failed to remove {pyc_file}: {e}")

    # Also clean PyInstaller generated files
    spec_file = Path("montagepy.spec")
    if spec_file.exists():
        # PyInstaller may create .spec.bak files
        bak_file = Path("montagepy.spec.bak")
        if bak_file.exists():
            try:
                bak_file.unlink()
                removed_items.append(f"File: {bak_file}")
            except Exception as e:
                print(f"Warning: Failed to remove {bak_file}: {e}")

    if removed_items:
        print("🧹 Cleaned the following items:")
        for item in removed_items:
            print(f"  - {item}")
        print("✅ Clean complete!")
    else:
        print("✅ Nothing to clean (all build artifacts already removed)")


def build():
    """Build executable using PyInstaller."""
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed.")
        print("Please install it with: pip install pyinstaller")
        sys.exit(1)

    # Clean previous builds
    build_dirs = ["build", "dist"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

    # Use spec file if it exists, otherwise use command line
    spec_file = Path("montagepy.spec")
    if spec_file.exists():
        print("Building executable using montagepy.spec...")
        cmd = ["pyinstaller", "--clean", str(spec_file)]
    else:
        print("Building executable with PyInstaller...")
        cmd = [
            "pyinstaller",
            "--clean",
            "--onefile",
            "--name=montagepy",
            "--add-data=config.sample.yaml:.",
            "--hidden-import=av",
            "--hidden-import=av.codec",
            "--hidden-import=av.format",
            "--hidden-import=av.video",
            "--hidden-import=av.audio",
            "--hidden-import=av.container",
            "--hidden-import=av.stream",
            "--hidden-import=av.frame",
            "--hidden-import=PIL",
            "--hidden-import=PIL.Image",
            "--hidden-import=PIL.ImageDraw",
            "--hidden-import=PIL.ImageFont",
            "--hidden-import=click",
            "--hidden-import=yaml",
            "--hidden-import=montagepy",
            "--hidden-import=montagepy.cli",
            "--hidden-import=montagepy.cli.main",
            "--hidden-import=montagepy.cli.commands",
            "--hidden-import=montagepy.cli.commands.jpg",
            "--hidden-import=montagepy.cli.commands.gif",
            "--hidden-import=montagepy.cli.options",
            "--hidden-import=montagepy.cli.options.common",
            "--hidden-import=montagepy.cli.options.appearance",
            "--hidden-import=montagepy.cli.types",
            "--hidden-import=montagepy.core",
            "--hidden-import=montagepy.core.config",
            "--hidden-import=montagepy.core.logger",
            "--hidden-import=montagepy.core.handlers",
            "--hidden-import=montagepy.core.models",
            "--hidden-import=montagepy.converters",
            "--hidden-import=montagepy.converters.gif_converter",
            "--hidden-import=montagepy.extractors",
            "--hidden-import=montagepy.extractors.clip_extractor",
            "--hidden-import=montagepy.extractors.frame_extractor",
            "--hidden-import=montagepy.renderers",
            "--hidden-import=montagepy.renderers.gif_montage_renderer",
            "--hidden-import=montagepy.renderers.montage_renderer",
            "--hidden-import=montagepy.utils",
            "--hidden-import=montagepy.utils.file_utils",
            "--hidden-import=montagepy.utils.color_utils",
            "--hidden-import=montagepy.utils.format_utils",
            "--hidden-import=montagepy.utils.grid_utils",
            "--hidden-import=montagepy.video_info",
            "montagepy/main.py",
        ]

    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print("\n✅ Build successful!")
        exe_name = "montagepy.exe" if sys.platform == "win32" else "montagepy"
        exe_path = os.path.abspath(f"dist/{exe_name}")
        if os.path.exists(exe_path):
            print(f"Executable location: {exe_path}")
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"Executable size: {file_size:.2f} MB")
        else:
            print("Warning: Executable not found in dist/")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build script for MontagePy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py          # Build executable
  python build.py --build # Build executable (explicit)
  python build.py --clean # Clean build artifacts
  python build.py --clean --build  # Clean then build
        """
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build executable using PyInstaller",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts and output files",
    )

    args = parser.parse_args()

    # If no arguments, default to build
    if not args.build and not args.clean:
        args.build = True

    # Clean first if requested
    if args.clean:
        clean()
        print()  # Empty line for readability

    # Build if requested
    if args.build:
        build()


if __name__ == "__main__":
    main()
