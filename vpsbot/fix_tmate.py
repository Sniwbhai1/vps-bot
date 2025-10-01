#!/usr/bin/env python3
"""
Fix tmate installation for existing VPS containers
"""

import docker
import asyncio

async def fix_tmate_for_vps(vps_name):
    """Install tmate in an existing VPS container"""
    try:
        client = docker.from_env()
        container = client.containers.get(vps_name)
        
        print(f"🔧 Installing tmate in {vps_name}...")
        
        # Install tmate
        result = container.exec_run(
            "apt-get update && apt-get install -y tmate",
            stdout=True,
            stderr=True
        )
        
        if result.exit_code == 0:
            print(f"✅ tmate installed successfully in {vps_name}")
            
            # Start tmate session
            print(f"🚀 Starting tmate session...")
            tmate_result = container.exec_run(
                "tmate -S /tmp/tmate.sock new-session -d",
                stdout=True,
                stderr=True
            )
            
            if tmate_result.exit_code == 0:
                # Wait a moment for session to be ready
                await asyncio.sleep(3)
                
                # Get session info
                session_info = container.exec_run(
                    "tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'",
                    stdout=True,
                    stderr=True
                )
                
                if session_info.exit_code == 0 and session_info.output:
                    ssh_info = session_info.output.decode().strip()
                    if "tmate.io" in ssh_info:
                        print(f"🔗 tmate session ready: {ssh_info}")
                        return True, ssh_info
                
                print("⚠️ tmate session created but couldn't get SSH info")
                return True, "Session created but no SSH info"
            else:
                print(f"❌ Failed to start tmate session: {tmate_result.output.decode()}")
                return False, "Failed to start tmate session"
        else:
            print(f"❌ Failed to install tmate: {result.output.decode()}")
            return False, "Failed to install tmate"
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, str(e)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 fix_tmate.py <vps_name>")
        print("Example: python3 fix_tmate.py vps-1759334476")
        sys.exit(1)
    
    vps_name = sys.argv[1]
    
    print(f"🔧 Fixing tmate for VPS: {vps_name}")
    print("=" * 40)
    
    success, result = asyncio.run(fix_tmate_for_vps(vps_name))
    
    if success:
        print(f"\n✅ Success! {result}")
    else:
        print(f"\n❌ Failed: {result}")
