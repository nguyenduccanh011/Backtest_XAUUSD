"""
Quick script to run all tests
Usage: python run_tests.py
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run all tests with pytest."""
    print("=" * 60)
    print("🧪 Running Backtest XAUUSD Tests")
    print("=" * 60)
    print()
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest is not installed!")
        print("   Please install: pip install pytest pytest-cov")
        return 1
    
    # Run tests
    test_dir = Path(__file__).parent / "tests"
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    print(f"📁 Test directory: {test_dir}")
    print()
    
    # Run with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short"
    ]
    
    print("🚀 Running tests...")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())



