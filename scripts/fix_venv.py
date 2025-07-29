#!/usr/bin/env python3
"""
Virtual environment diagnostic and fix script.

This script checks if the virtual environment is properly set up
and fixes common issues like missing packages or broken environments.

Usage:
    python scripts/fix_venv.py
"""

import os
import sys
import subprocess
from pathlib import Path


def check_venv():
    """Check if we're in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✅ Running in virtual environment")
        print(f"   Virtual env: {sys.prefix}")
        return True
    else:
        print("❌ Not running in virtual environment")
        return False


def check_packages():
    """Check if required packages are installed"""
    required_packages = [
        'pydantic', 'fastapi', 'pytest', 'python_dotenv',
        'requests', 'pandas', 'numpy'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            installed_packages.append(package)
        except ImportError:
            missing_packages.append(package)
    
    print(f"📦 Package Status:")
    print(f"   Installed: {len(installed_packages)}/{len(required_packages)}")
    
    if missing_packages:
        print(f"   Missing: {missing_packages}")
        return False
    else:
        print("   ✅ All required packages installed")
        return True


def install_packages():
    """Install missing packages"""
    print("📦 Installing packages from requirements.txt...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Packages installed successfully")
            return True
        else:
            print(f"❌ Failed to install packages: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing packages: {e}")
        return False


def check_python_path():
    """Check Python path configuration"""
    project_root = Path(__file__).parent.parent
    python_path = os.environ.get('PYTHONPATH', '')
    
    if str(project_root) in python_path:
        print("✅ PYTHONPATH includes project root")
        return True
    else:
        print("⚠️  PYTHONPATH doesn't include project root")
        print(f"   Current PYTHONPATH: {python_path}")
        print(f"   Should include: {project_root}")
        return False


def main():
    """Main diagnostic function"""
    print("🔍 Diagnosing virtual environment...")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    venv_ok = check_venv()
    
    # Check packages
    packages_ok = check_packages()
    
    # Check Python path
    path_ok = check_python_path()
    
    print("\n" + "=" * 50)
    
    if not venv_ok:
        print("❌ Please activate the virtual environment first:")
        print("   source venv/bin/activate")
        return False
    
    if not packages_ok:
        print("📦 Installing missing packages...")
        if install_packages():
            print("✅ Environment fixed!")
            return True
        else:
            print("❌ Failed to fix environment")
            return False
    
    if not path_ok:
        print("⚠️  Setting PYTHONPATH...")
        project_root = Path(__file__).parent.parent
        os.environ['PYTHONPATH'] = f"{project_root}:{os.environ.get('PYTHONPATH', '')}"
        print(f"   PYTHONPATH set to: {os.environ['PYTHONPATH']}")
    
    print("✅ Environment is healthy!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 