"""
Setup Environment - Bootstrap Python environment for JLAW.

Creates virtual environment and installs dependencies.

Usage:
    python scripts/setup_environment.py
"""

import sys
import subprocess
import venv
from pathlib import Path


def setup_environment():
    """Setup Python virtual environment."""
    project_root = Path(__file__).resolve().parent.parent
    venv_dir = project_root / 'venv'
    requirements_file = project_root / 'requirements.txt'
    
    print("=" * 80)
    print("JLAW Environment Setup")
    print("=" * 80 + "\n")
    
    # Check Python version
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 10):
        print(f"❌ Python 3.10+ required (you have {version.major}.{version.minor})")
        return False
    
    print("✅ Python version compatible\n")
    
    # Check if virtual environment already exists
    if venv_dir.exists():
        print(f"⚠️  Virtual environment already exists at {venv_dir}")
        response = input("Recreate? (y/N): ").strip().lower()
        if response != 'y':
            print("Using existing virtual environment.")
        else:
            import shutil
            shutil.rmtree(venv_dir)
            print(f"Removed existing virtual environment")
    
    # Create virtual environment
    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}...")
        try:
            venv.create(venv_dir, with_pip=True)
            print("✅ Virtual environment created\n")
        except Exception as e:
            print(f"❌ Failed to create virtual environment: {str(e)}")
            return False
    
    # Determine pip path
    if sys.platform == 'win32':
        pip_path = venv_dir / 'Scripts' / 'pip.exe'
        python_path = venv_dir / 'Scripts' / 'python.exe'
    else:
        pip_path = venv_dir / 'bin' / 'pip'
        python_path = venv_dir / 'bin' / 'python'
    
    # Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.run([str(python_path), '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        print("✅ Pip upgraded\n")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to upgrade pip: {str(e)}\n")
    
    # Install requirements
    if not requirements_file.exists():
        print(f"⚠️  requirements.txt not found at {requirements_file}")
        print("Skipping dependency installation.")
    else:
        print(f"Installing dependencies from {requirements_file}...")
        print("(This may take several minutes...)\n")
        try:
            subprocess.run(
                [str(pip_path), 'install', '-r', str(requirements_file)],
                check=True
            )
            print("\n✅ Dependencies installed\n")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to install dependencies: {str(e)}")
            return False
    
    # Print activation instructions
    print("=" * 80)
    print("✅ Environment setup complete!")
    print("=" * 80 + "\n")
    print("To activate the virtual environment:")
    if sys.platform == 'win32':
        print(f"  {venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")
    
    print("\nNext steps:")
    print("  1. Activate virtual environment")
    print("  2. Create .env file: python scripts/generate_env_template.py")
    print("  3. Run pre-flight check: python -m tests.preflight_check")
    print("  4. Run full test suite: python -m tests.jlaw_master_test_suite --full")
    
    return True


def main():
    """Main entry point."""
    success = setup_environment()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
