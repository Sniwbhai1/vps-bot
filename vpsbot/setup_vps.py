#!/usr/bin/env python3
"""
VPS Bot Setup Script
This script helps set up the VPS bot environment and prepares the Ubuntu ISO
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_docker():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker installation...")
    
    success, stdout, stderr = run_command("docker --version", check=False)
    if not success:
        print("❌ Docker is not installed. Please install Docker first.")
        return False
    
    print(f"✅ Docker found: {stdout.strip()}")
    
    # Check if Docker daemon is running
    success, stdout, stderr = run_command("docker info", check=False)
    if not success:
        print("❌ Docker daemon is not running. Please start Docker.")
        return False
    
    print("✅ Docker daemon is running")
    return True

def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")
    
    directories = [
        "/var/lib/vpsbot",
        "/var/lib/vpsbot/containers",
        "/var/lib/vpsbot/iso"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except PermissionError:
            print(f"❌ Permission denied creating {directory}. Run with sudo or create manually.")
            return False
    
    return True

def setup_ubuntu_iso():
    """Set up Ubuntu ISO for VPS creation"""
    print("🖥️ Setting up Ubuntu ISO...")
    
    iso_path = "/var/lib/vpsbot/iso/ubuntu-24.04.3-server.iso"
    
    # Check if ISO already exists
    if os.path.exists(iso_path):
        print(f"✅ Ubuntu ISO already exists at {iso_path}")
        return True
    
    # Look for ISO in common locations
    possible_locations = [
        "./ubuntu-24.04.3-server.iso",
        "~/ubuntu-24.04.3-server.iso",
        "/home/*/ubuntu-24.04.3-server.iso",
        "/tmp/ubuntu-24.04.3-server.iso"
    ]
    
    found_iso = None
    for location in possible_locations:
        if os.path.exists(os.path.expanduser(location)):
            found_iso = os.path.expanduser(location)
            break
    
    if found_iso:
        print(f"📋 Found Ubuntu ISO at: {found_iso}")
        try:
            shutil.copy2(found_iso, iso_path)
            print(f"✅ Copied ISO to {iso_path}")
            return True
        except PermissionError:
            print(f"❌ Permission denied copying ISO. Please copy manually:")
            print(f"sudo cp {found_iso} {iso_path}")
            return False
    else:
        print("❌ Ubuntu ISO not found. Please download ubuntu-24.04.3-server.iso and place it in:")
        print(f"  {iso_path}")
        print("Or run this script from the directory containing the ISO file.")
        return False

def create_docker_image():
    """Create a custom Docker image for VPS containers"""
    print("🔨 Creating custom Docker image...")
    
    # Create Dockerfile
    dockerfile_content = """
FROM ubuntu:24.04

# Install essential packages
RUN apt-get update && apt-get install -y \\
    openssh-server \\
    tmate \\
    curl \\
    wget \\
    vim \\
    htop \\
    && rm -rf /var/lib/apt/lists/*

# Configure SSH
RUN mkdir /var/run/sshd
RUN echo 'root:password' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create startup script
RUN echo '#!/bin/bash' > /start.sh && \\
    echo 'service ssh start' >> /start.sh && \\
    echo 'tmate -S /tmp/tmate.sock new-session -d' >> /start.sh && \\
    echo 'tmate -S /tmp/tmate.sock display -p "#{tmate_ssh}" > /tmp/tmate_info' >> /start.sh && \\
    echo 'while true; do sleep 30; done' >> /start.sh && \\
    chmod +x /start.sh

EXPOSE 22

CMD ["/start.sh"]
"""
    
    try:
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        print("📝 Created Dockerfile")
        
        # Build Docker image
        success, stdout, stderr = run_command("docker build -t vpsbot-ubuntu:24.04 .")
        if success:
            print("✅ Docker image built successfully")
            os.remove("Dockerfile")  # Clean up
            return True
        else:
            print(f"❌ Failed to build Docker image: {stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Error creating Docker image: {e}")
        return False

def update_vps_manager():
    """Update VPS manager to use the custom image"""
    print("🔧 Updating VPS manager configuration...")
    
    # Read current vps_manager.py
    try:
        with open("vps_manager.py", "r") as f:
            content = f.read()
        
        # Replace the image name
        updated_content = content.replace(
            'image="ubuntu:24.04"',
            'image="vpsbot-ubuntu:24.04"'
        )
        
        # Write back
        with open("vps_manager.py", "w") as f:
            f.write(updated_content)
        
        print("✅ Updated VPS manager to use custom image")
        return True
    
    except Exception as e:
        print(f"❌ Error updating VPS manager: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 VPS Bot Setup Script")
    print("=" * 50)
    
    # Check if running as root for directory creation
    if os.geteuid() != 0:
        print("⚠️  Warning: Not running as root. Some operations may require sudo.")
        print("   If you encounter permission errors, run: sudo python3 setup_vps.py")
        print()
    
    # Run setup steps
    steps = [
        ("Checking Docker", check_docker),
        ("Setting up directories", setup_directories),
        ("Setting up Ubuntu ISO", setup_ubuntu_iso),
        ("Creating Docker image", create_docker_image),
        ("Updating VPS manager", update_vps_manager)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            print("Please fix the issue and run the script again.")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ VPS Bot setup completed successfully!")
    print("\nNext steps:")
    print("1. Create a .env file with your Discord bot token:")
    print("   DISCORD_TOKEN=your_bot_token_here")
    print("   DISCORD_GUILD_ID=your_guild_id_here")
    print("2. Install Python dependencies:")
    print("   pip install -r requirements.txt")
    print("3. Run the bot:")
    print("   python3 bot.py")

if __name__ == "__main__":
    main()
