# backend/setup_check.py
"""
Script to verify backend setup and create missing directories/files
"""
import os
from pathlib import Path

def create_directory_structure():
    """Create necessary directories."""
    directories = [
        "uploads",
        "outputs", 
        "agents",
        "models",
        "graph",
        "utils"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created/verified directory: {directory}")

def create_init_files():
    """Create __init__.py files in packages."""
    init_files = [
        "agents/__init__.py",
        "models/__init__.py", 
        "graph/__init__.py",
        "utils/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"✓ Created/verified: {init_file}")

def check_env_file():
    """Check if .env file exists."""
    if not Path(".env").exists():
        print("⚠️  .env file not found. Copy .env.example to .env and add your OpenAI API key")
        return False
    print("✓ .env file exists")
    return True

def verify_required_files():
    """Verify all required Python files exist."""
    required_files = [
        "main.py",
        "config.py",
        "agents/prompts.py",
        "agents/csv_loader_agent.py",
        "agents/preprocessor_agent.py", 
        "agents/llm_agent.py",
        "agents/output_agent.py",
        "models/schemas.py",
        "utils/file_handler.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ Missing: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def main():
    print("🚀 HG AI Platform Backend Setup Check\n")
    
    # Create directories
    create_directory_structure()
    print()
    
    # Create __init__.py files
    create_init_files()
    print()
    
    # Check environment
    env_ok = check_env_file()
    print()
    
    # Verify files
    print("📁 Checking required files:")
    files_ok = verify_required_files()
    print()
    
    if files_ok and env_ok:
        print("✅ Backend setup complete! You can now run: python main.py")
    else:
        print("❌ Setup incomplete. Please check the missing files above.")

if __name__ == "__main__":
    main()