import docker
import asyncio
import os
import subprocess
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import psutil

@dataclass
class VPSConfig:
    name: str
    ram_gb: int
    cpu_cores: int
    disk_gb: int
    container_id: Optional[str] = None
    status: str = "creating"
    tmate_session: Optional[str] = None
    created_at: Optional[float] = None

class VPSManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
            # Test the connection
            self.client.ping()
        except Exception as e:
            print(f"Docker connection error: {e}")
            print("Please ensure Docker is running and accessible")
            raise
        self.vps_instances: Dict[str, VPSConfig] = {}
        self.load_existing_containers()
    
    def load_existing_containers(self):
        """Load existing VPS containers on startup"""
        try:
            containers = self.client.containers.list(all=True, filters={"label": "vpsbot=true"})
            for container in containers:
                if container.name.startswith("vps-"):
                    # Extract VPS config from container labels
                    ram = int(container.labels.get("vps.ram", "1"))
                    cpu = int(container.labels.get("vps.cpu", "1"))
                    disk = int(container.labels.get("vps.disk", "10"))
                    
                    vps_config = VPSConfig(
                        name=container.name,
                        ram_gb=ram,
                        cpu_cores=cpu,
                        disk_gb=disk,
                        container_id=container.id,
                        status="running" if container.status == "running" else "stopped"
                    )
                    self.vps_instances[container.name] = vps_config
        except Exception as e:
            print(f"Error loading existing containers: {e}")
    
    async def create_vps(self, ram_gb: int, cpu_cores: int, disk_gb: int) -> Tuple[bool, str, Optional[VPSConfig]]:
        """Create a new VPS with specified resources"""
        try:
            # Generate unique VPS name
            vps_name = f"vps-{int(time.time())}"
            
            # Validate resource limits
            if not self._validate_resources(ram_gb, cpu_cores, disk_gb):
                return False, "Invalid resource specifications", None
            
            # Check if we can create more VPS instances
            if len(self.vps_instances) >= 10:  # MAX_VPS_COUNT from config
                return False, "Maximum VPS limit reached", None
            
            # Create VPS configuration
            vps_config = VPSConfig(
                name=vps_name,
                ram_gb=ram_gb,
                cpu_cores=cpu_cores,
                disk_gb=disk_gb,
                created_at=time.time()
            )
            
            # Start VPS creation process
            asyncio.create_task(self._create_vps_container(vps_config))
            
            self.vps_instances[vps_name] = vps_config
            return True, f"VPS {vps_name} creation started", vps_config
            
        except Exception as e:
            return False, f"Error creating VPS: {str(e)}", None
    
    def _validate_resources(self, ram_gb: int, cpu_cores: int, disk_gb: int) -> bool:
        """Validate resource specifications"""
        if ram_gb < 1 or ram_gb > 32:
            return False
        if cpu_cores < 1 or cpu_cores > 16:
            return False
        if disk_gb < 5 or disk_gb > 500:
            return False
        return True
    
    async def _create_vps_container(self, vps_config: VPSConfig):
        """Create the actual VPS container"""
        try:
            # Create container with resource limits
            container = self.client.containers.run(
                image="vpsbot-ubuntu:24.04",
                name=vps_config.name,
                detach=True,
                privileged=True,
                mem_limit=f"{vps_config.ram_gb}g",
                cpu_quota=int(vps_config.cpu_cores * 100000),
                cpu_period=100000,
                volumes={
                    f"/var/lib/vpsbot/containers/{vps_config.name}": {
                        "bind": "/vps-storage",
                        "mode": "rw"
                    }
                },
                labels={
                    "vpsbot": "true",
                    "vps.ram": str(vps_config.ram_gb),
                    "vps.cpu": str(vps_config.cpu_cores),
                    "vps.disk": str(vps_config.disk_gb)
                },
                command="/bin/bash -c 'while true; do sleep 30; done'"
            )
            
            vps_config.container_id = container.id
            vps_config.status = "running"
            
            # Install and setup tmate
            await self._setup_tmate(vps_config)
            
        except Exception as e:
            vps_config.status = "error"
            print(f"Error creating container for {vps_config.name}: {e}")
    
    async def _setup_tmate(self, vps_config: VPSConfig):
        """Install and setup tmate for remote access"""
        try:
            container = self.client.containers.get(vps_config.container_id)
            
            # Wait for container to be fully ready
            await asyncio.sleep(5)
            
            # Install tmate
            print(f"Installing tmate for {vps_config.name}...")
            exec_result = container.exec_run(
                "apt-get update && apt-get install -y tmate curl",
                stdout=True,
                stderr=True
            )
            
            if exec_result.exit_code == 0:
                print(f"tmate installed for {vps_config.name}, starting session...")
                
                # Start tmate session in background
                tmate_result = container.exec_run(
                    "nohup tmate -S /tmp/tmate.sock new-session -d > /tmp/tmate.log 2>&1 &",
                    stdout=True,
                    stderr=True
                )
                
                # Wait a bit for tmate to start
                await asyncio.sleep(3)
                
                # Try to get session info with retries
                for attempt in range(5):
                    try:
                        session_info = container.exec_run(
                            "tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'",
                            stdout=True,
                            stderr=True
                        )
                        
                        if session_info.exit_code == 0 and session_info.output:
                            ssh_info = session_info.output.decode().strip()
                            if ssh_info and "tmate.io" in ssh_info:
                                vps_config.tmate_session = ssh_info
                                print(f"tmate session ready for {vps_config.name}: {ssh_info}")
                                break
                        
                        # If not ready, wait and try again
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed for {vps_config.name}: {e}")
                        await asyncio.sleep(2)
                
                # If still no session, try alternative method
                if not vps_config.tmate_session:
                    print(f"Trying alternative tmate setup for {vps_config.name}...")
                    alt_result = container.exec_run(
                        "tmate -S /tmp/tmate.sock new-session -d; sleep 2; tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'",
                        stdout=True,
                        stderr=True
                    )
                    
                    if alt_result.exit_code == 0 and alt_result.output:
                        ssh_info = alt_result.output.decode().strip()
                        if "tmate.io" in ssh_info:
                            vps_config.tmate_session = ssh_info
                            print(f"Alternative tmate setup successful for {vps_config.name}")
            
        except Exception as e:
            print(f"Error setting up tmate for {vps_config.name}: {e}")
            # Try to get any existing session info
            try:
                container = self.client.containers.get(vps_config.container_id)
                session_info = container.exec_run(
                    "tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}' 2>/dev/null || echo 'no session'",
                    stdout=True,
                    stderr=True
                )
                if session_info.exit_code == 0 and "tmate.io" in session_info.output.decode():
                    vps_config.tmate_session = session_info.output.decode().strip()
            except:
                pass
    
    def get_vps_info(self, vps_name: str) -> Optional[Dict]:
        """Get VPS information including specs and tmate session"""
        if vps_name not in self.vps_instances:
            return None
        
        vps = self.vps_instances[vps_name]
        
        # Get container status
        try:
            if vps.container_id:
                container = self.client.containers.get(vps.container_id)
                vps.status = container.status
        except:
            vps.status = "unknown"
        
        return {
            "name": vps.name,
            "ram_gb": vps.ram_gb,
            "cpu_cores": vps.cpu_cores,
            "disk_gb": vps.disk_gb,
            "status": vps.status,
            "tmate_session": vps.tmate_session,
            "created_at": vps.created_at
        }
    
    def list_vps(self) -> List[Dict]:
        """List all VPS instances"""
        vps_list = []
        for vps_name in self.vps_instances:
            info = self.get_vps_info(vps_name)
            if info:
                vps_list.append(info)
        return vps_list
    
    async def stop_vps(self, vps_name: str) -> Tuple[bool, str]:
        """Stop a VPS instance"""
        if vps_name not in self.vps_instances:
            return False, "VPS not found"
        
        try:
            vps = self.vps_instances[vps_name]
            if vps.container_id:
                container = self.client.containers.get(vps.container_id)
                container.stop()
                vps.status = "stopped"
                return True, f"VPS {vps_name} stopped"
            return False, "No container found for VPS"
        except Exception as e:
            return False, f"Error stopping VPS: {str(e)}"
    
    async def delete_vps(self, vps_name: str) -> Tuple[bool, str]:
        """Delete a VPS instance"""
        if vps_name not in self.vps_instances:
            return False, "VPS not found"
        
        try:
            vps = self.vps_instances[vps_name]
            if vps.container_id:
                container = self.client.containers.get(vps.container_id)
                container.remove(force=True)
            
            # Remove from our tracking
            del self.vps_instances[vps_name]
            return True, f"VPS {vps_name} deleted"
        except Exception as e:
            return False, f"Error deleting VPS: {str(e)}"
    
    async def refresh_tmate_session(self, vps_name: str) -> Tuple[bool, str]:
        """Manually refresh tmate session for a VPS"""
        if vps_name not in self.vps_instances:
            return False, "VPS not found"
        
        try:
            vps = self.vps_instances[vps_name]
            if not vps.container_id:
                return False, "No container found for VPS"
            
            container = self.client.containers.get(vps.container_id)
            
            # Kill existing tmate session
            container.exec_run("pkill -f tmate", stdout=True, stderr=True)
            await asyncio.sleep(1)
            
            # Start new tmate session
            tmate_result = container.exec_run(
                "tmate -S /tmp/tmate.sock new-session -d",
                stdout=True,
                stderr=True
            )
            
            if tmate_result.exit_code == 0:
                # Wait for session to be ready
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
                        vps.tmate_session = ssh_info
                        return True, f"New tmate session created: {ssh_info}"
                
                return False, "tmate session created but couldn't get SSH info"
            else:
                return False, f"Failed to create tmate session: {tmate_result.output.decode()}"
                
        except Exception as e:
            return False, f"Error refreshing tmate session: {str(e)}"
    
    def get_system_resources(self) -> Dict:
        """Get current system resource usage"""
        return {
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "used_ram_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "cpu_cores": psutil.cpu_count(),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "disk_used_gb": round(psutil.disk_usage('/').used / (1024**3), 2)
        }
