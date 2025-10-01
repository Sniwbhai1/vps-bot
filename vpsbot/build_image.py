#!/usr/bin/env python3
"""
Build the custom VPS Docker image
"""

import docker
import os

def build_custom_image():
    """Build the custom VPS Docker image with tmate pre-installed"""
    
    # Create Dockerfile content
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
        # Write Dockerfile
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        print("📝 Created Dockerfile")
        
        # Build Docker image
        client = docker.from_env()
        print("🔨 Building custom Docker image...")
        
        image, build_logs = client.images.build(
            path=".",
            tag="vpsbot-ubuntu:24.04",
            rm=True
        )
        
        print("✅ Docker image built successfully!")
        print(f"Image ID: {image.id}")
        
        # Clean up Dockerfile
        os.remove("Dockerfile")
        print("🧹 Cleaned up Dockerfile")
        
        return True
        
    except Exception as e:
        print(f"❌ Error building Docker image: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Building VPS Bot Docker Image")
    print("=" * 40)
    
    if build_custom_image():
        print("\n✅ Build completed successfully!")
        print("You can now create VPS instances with tmate pre-installed.")
    else:
        print("\n❌ Build failed!")
        print("Please check the error messages above.")
