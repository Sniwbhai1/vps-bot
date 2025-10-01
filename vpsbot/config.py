import os
from dotenv import load_dotenv

load_dotenv()

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))

# VPS Configuration
UBUNTU_ISO_PATH = "/path/to/ubuntu-24.04.3-live-server-amd64.iso"  # Update this path
CONTAINER_BASE_PATH = "/var/lib/vpsbot/containers"
MAX_VPS_COUNT = 10  # Maximum number of VPS instances
DEFAULT_VPS_PREFIX = "vps-"

# Resource Limits
MAX_RAM_GB = 32
MAX_CPU_CORES = 16
MAX_DISK_GB = 500

# Tmate Configuration
TMATE_SESSION_TIMEOUT = 3600  # 1 hour in seconds
