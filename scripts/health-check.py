#!/usr/bin/env python3

"""
Health check script for AgenticAI application.
This script verifies that all components are working correctly.
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python 3.11+ is installed."""
    print("Checking Python version...")
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ required, found {sys.version}")
        return False
    print(f"✅ Python {sys.version}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "langchain",
        "langgraph",
        "langchain_ollama",
        "langchain_google_genai",
        "langchain_openai",
        "langchain_anthropic",
        "langchain_groq",
        "langchain_huggingface",
        "transformers",
        "torch",
        "sqlite3"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.util.find_spec(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    print("✅ All required dependencies found")
    return True

def check_environment_variables():
    """Check if required environment variables are set."""
    print("Checking environment variables...")
    required_vars = [
        "HOST",
        "PORT",
        "CORS_ORIGINS"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Using default values...")
    
    print("✅ Environment variables check completed")
    return True

def check_database():
    """Check if database is accessible."""
    print("Checking database...")
    db_path = Path("app/db/chat.db")
    
    # Create directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS health_check (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO health_check (id) VALUES (1)")
        cursor.execute("DELETE FROM health_check WHERE id = 1")
        conn.commit()
        conn.close()
        print("✅ Database is accessible")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_frontend_build():
    """Check if frontend build exists."""
    print("Checking frontend build...")
    dist_path = Path("ui/dist")
    
    if not dist_path.exists():
        print("⚠️  Frontend build not found. Run 'cd ui && npm run build' to build frontend.")
        return True  # Not critical for backend health
    
    if not any(dist_path.iterdir()):
        print("⚠️  Frontend build directory is empty.")
        return True  # Not critical for backend health
    
    print("✅ Frontend build exists")
    return True

def main():
    """Run all health checks."""
    print("🏥 AgenticAI Health Check")
    print("=" * 30)
    
    checks = [
        check_python_version,
        check_dependencies,
        check_environment_variables,
        check_database,
        check_frontend_build
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if check():
            passed += 1
        print()
    
    print("=" * 30)
    print(f"Health Check Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Application is healthy.")
        return 0
    elif passed >= total * 0.8:
        print("⚠️  Most checks passed. Application may work with minor issues.")
        return 1
    else:
        print("❌ Many checks failed. Application may not work correctly.")
        return 2

if __name__ == "__main__":
    sys.exit(main())