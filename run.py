#!/usr/bin/env python3
"""
SignLang AI - Startup Script
Comprehensive machine learning application for sign language recognition
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'opencv-python', 'mediapipe', 'tensorflow', 
        'numpy', 'pyttsx3', 'flask-cors', 'pillow', 'werkzeug',
        'flask-sqlalchemy', 'flask-login'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    return missing_packages

def install_dependencies(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"\n📦 Installing missing packages: {', '.join(packages)}")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade'
        ] + packages)
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = '.env'
    if not os.path.exists(env_path):
        print("📝 Creating .env file...")
        with open(env_path, 'w') as f:
            f.write("""# SignLang AI Environment Configuration
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
DATABASE_URL=sqlite:///signlang.db
PORT=5000
""")
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")

def create_directories():
    """Create necessary directories"""
    directories = [
        'app/static/uploads',
        'data/raw',
        'data/processed',
        'data/models',
        'logs'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")

def check_camera():
    """Check if camera is available"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("✅ Camera is available")
                return True
            else:
                print("⚠️  Camera detected but unable to capture frames")
                return False
        else:
            print("⚠️  No camera detected")
            return False
    except Exception as e:
        print(f"⚠️  Camera check failed: {e}")
        return False

def display_system_info():
    """Display system information"""
    print(f"""
🖥️  System Information:
   OS: {platform.system()} {platform.release()}
   Architecture: {platform.machine()}
   Python: {sys.version.split()[0]}
   Platform: {platform.platform()}
""")

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                          SignLang AI                            ║
║              Real-time Sign Language Recognition                 ║
║                                                                  ║
║  🤟 Bridging communication through AI technology 🤟            ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def run_application():
    """Start the Flask application"""
    print("\n🚀 Starting SignLang AI application...")
    print("📍 Access the application at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the application\n")
    
    try:
        from app import create_app
        app = create_app()
        
        # Create upload directory
        upload_dir = os.path.join('app', 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Run the application
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development'
        )
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")
        print("💡 Check the logs for more details")

def main():
    """Main startup function"""
    print_banner()
    display_system_info()
    
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if not check_python_version():
        print("\n💡 Please install Python 3.8 or higher")
        return
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        response = input("📥 Install missing packages? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            if not install_dependencies(missing_packages):
                print("❌ Failed to install dependencies. Please install manually:")
                print(f"pip install {' '.join(missing_packages)}")
                return
        else:
            print("❌ Cannot proceed without required dependencies")
            return
    
    print("\n🔧 Setting up application...")
    
    # Create environment file
    create_env_file()
    
    # Create directories
    create_directories()
    
    # Check camera
    print("\n📷 Checking camera availability...")
    camera_available = check_camera()
    if not camera_available:
        print("⚠️  Camera not available. You can still explore the application,")
        print("   but real-time recognition will not work.")
    
    print("\n✅ Setup complete!")
    
    # Ask user if they want to start the application
    response = input("\n🚀 Start the application now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        run_application()
    else:
        print("""
🎯 To start the application later, run:
   python run.py
   
   or
   
   python app.py

📚 For more information, see README.md
""")

if __name__ == '__main__':
    main()