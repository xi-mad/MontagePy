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
    items_to_remove = [
        "build",
        "dist",
        "__pycache__",
    ]

    # Also clean PyInstaller generated files
    spec_file = Path("montagepy.spec")
    if spec_file.exists():
        # PyInstaller may create .spec.bak files
        bak_file = Path("montagepy.spec.bak")
        if bak_file.exists():
            items_to_remove.append(str(bak_file))

    # Clean montagepy package __pycache__
    montagepy_cache = Path("montagepy/__pycache__")
    if montagepy_cache.exists():
        items_to_remove.append(str(montagepy_cache))

    removed_items = []
    for item in items_to_remove:
        item_path = Path(item)
        if item_path.exists():
            try:
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                    removed_items.append(f"Directory: {item}")
                else:
                    item_path.unlink()
                    removed_items.append(f"File: {item}")
            except Exception as e:
                print(f"Warning: Failed to remove {item}: {e}")

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
            "--hidden-import=montagepy.config",
            "--hidden-import=montagepy.logger",
            "--hidden-import=montagepy.processor",
            "--hidden-import=montagepy.utils",
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
