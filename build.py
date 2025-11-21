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


def build(mode="onedir"):
    """Build executable using PyInstaller.
    
    Args:
        mode: Build mode, either "onefile" or "onedir" (default: "onedir")
    """
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed.")
        print("Please install it with: pip install pyinstaller")
        sys.exit(1)

    # Validate mode
    if mode not in ["onefile", "onedir"]:
        print(f"Error: Invalid mode '{mode}'. Must be 'onefile' or 'onedir'")
        sys.exit(1)

    # Clean previous builds
    build_dirs = ["build", "dist"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

    # Use spec file only if it exists and we're using default onedir mode
    # When mode is explicitly specified, use command line to have full control
    spec_file = Path("montagepy.spec")
    # Use spec file only for default onedir mode (when no --mode is specified)
    # Note: This assumes spec file is configured for onedir mode
    use_spec = spec_file.exists() and mode == "onedir"
    
    if use_spec:
        print("Building executable using montagepy.spec (onedir mode)...")
        cmd = ["pyinstaller", "--clean", str(spec_file)]
    else:
        mode_name = "onefile" if mode == "onefile" else "directory"
        print(f"Building executable with PyInstaller ({mode_name} mode)...")
        cmd = [
            "pyinstaller",
            "--clean",
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
        ]
        
        # Add --onefile option if mode is onefile
        if mode == "onefile":
            cmd.insert(2, "--onefile")  # Insert after --clean
        
        cmd.append("montagepy/main.py")

    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print("\n✅ Build successful!")
        exe_name = "montagepy.exe" if sys.platform == "win32" else "montagepy"
        
        # Determine executable path based on mode
        if mode == "onefile":
            # Onefile mode: executable is directly in dist/
            exe_path = os.path.abspath(f"dist/{exe_name}")
        else:
            # Onedir mode: executable is in dist/montagepy/montagepy
            exe_path = os.path.abspath(f"dist/montagepy/{exe_name}")
            # Fallback: check if it's in dist/ directly (in case spec file uses onefile)
            if not os.path.exists(exe_path):
                exe_path = os.path.abspath(f"dist/{exe_name}")
        
        if os.path.exists(exe_path):
            print(f"Executable location: {exe_path}")
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"Executable size: {file_size:.2f} MB")
            
            # In directory mode, show directory size
            if mode == "onedir" and os.path.exists(os.path.dirname(exe_path)) and os.path.dirname(exe_path) != "dist":
                dir_size = sum(
                    f.stat().st_size for f in Path(os.path.dirname(exe_path)).rglob('*') if f.is_file()
                ) / (1024 * 1024)  # MB
                print(f"Directory size: {dir_size:.2f} MB")
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
  python build.py                    # Build executable (onedir mode, default)
  python build.py --build            # Build executable (explicit)
  python build.py --mode onefile     # Build as single executable file
  python build.py --mode onedir      # Build as directory (default)
  python build.py --clean            # Clean build artifacts
  python build.py --clean --build --mode onefile  # Clean then build as onefile
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
    parser.add_argument(
        "--mode",
        choices=["onefile", "onedir"],
        default="onedir",
        help="Build mode: 'onefile' creates a single executable file, 'onedir' creates a directory with executable and dependencies (default: onedir)",
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
        build(mode=args.mode)


if __name__ == "__main__":
    main()
