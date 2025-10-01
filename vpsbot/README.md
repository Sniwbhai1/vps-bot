# VPS Bot - Discord VPS Management Bot

A Discord bot that manages VPS instances using Docker containers with resource limits. Create, manage, and access VPS instances directly from Discord with tmate integration for remote access.

## Features

- 🚀 **Create VPS instances** with custom RAM, CPU, and disk specifications
- 🖥️ **Resource management** with Docker container limits
- 🔗 **Remote access** via tmate sessions
- 📊 **System monitoring** and resource usage tracking
- 🛠️ **Full VPS lifecycle management** (create, stop, delete, status)

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!create <ram> <cpu> <disk>` | Create a new VPS | `!create 8 4 30` |
| `!list` | List all VPS instances | `!list` |
| `!status [vps_name]` | Get VPS status | `!status vps-1234567890` |
| `!stop <vps_name>` | Stop a VPS instance | `!stop vps-1234567890` |
| `!delete <vps_name>` | Delete a VPS instance | `!delete vps-1234567890` |
| `!resources` | Show system resource usage | `!resources` |
| `!help` | Show all commands | `!help` |

## Installation

### Prerequisites

- Python 3.8+
- Docker installed and running
- Ubuntu 24.04.3 Server ISO file
- Discord bot token

### Quick Setup

1. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd vpsbot
   pip install -r requirements.txt
   ```

2. **Run the setup script:**
   ```bash
   sudo python3 setup_vps.py
   ```

3. **Configure environment:**
   ```bash
   cp env_example.txt .env
   # Edit .env with your Discord bot token and guild ID
   ```

4. **Start the bot:**
   ```bash
   python3 bot.py
   ```

### Manual Setup

If the automated setup doesn't work, follow these manual steps:

1. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Create directories:**
   ```bash
   sudo mkdir -p /var/lib/vpsbot/containers
   sudo mkdir -p /var/lib/vpsbot/iso
   ```

3. **Place Ubuntu ISO:**
   ```bash
   sudo cp ubuntu-24.04.3-server.iso /var/lib/vpsbot/iso/
   ```

4. **Build custom Docker image:**
   ```bash
   # Create Dockerfile (see setup_vps.py for content)
   docker build -t vpsbot-ubuntu:24.04 .
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
UBUNTU_ISO_PATH=/var/lib/vpsbot/iso/ubuntu-24.04.3-server.iso
CONTAINER_BASE_PATH=/var/lib/vpsbot/containers
```

### Resource Limits

Default limits (configurable in `config.py`):
- **RAM:** 1-32 GB
- **CPU:** 1-16 cores  
- **Disk:** 5-500 GB
- **Max VPS instances:** 10

## Usage Examples

### Creating a VPS

```
!create 8 4 30
```

This creates a VPS with:
- 8 GB RAM
- 4 CPU cores
- 30 GB disk space

### Accessing Your VPS

After creation, the bot will provide a tmate SSH command:

```bash
ssh <session_id>@nyc1.tmate.io
```

### Managing VPS Instances

```bash
# List all VPS instances
!list

# Check specific VPS status
!status vps-1234567890

# Stop a VPS
!stop vps-1234567890

# Delete a VPS (with confirmation)
!delete vps-1234567890
```

## Architecture

### Components

- **`bot.py`** - Main Discord bot with command handlers
- **`vps_manager.py`** - VPS lifecycle management and Docker integration
- **`config.py`** - Configuration and environment variables
- **`setup_vps.py`** - Automated setup script

### Docker Integration

The bot uses Docker containers to create isolated VPS instances with:
- Resource limits (CPU, memory, disk)
- Custom Ubuntu 24.04 image with SSH and tmate
- Persistent storage volumes
- Network isolation

### Security Considerations

- Containers run with resource limits
- SSH access via tmate (temporary sessions)
- Discord command validation
- Container isolation

## Troubleshooting

### Common Issues

1. **Docker not running:**
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **Permission denied:**
   ```bash
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **ISO not found:**
   - Ensure `ubuntu-24.04.3-server.iso` is in the correct location
   - Check file permissions

4. **Bot not responding:**
   - Verify Discord token is correct
   - Check bot permissions in Discord server
   - Ensure bot is in the correct guild

### Logs

Check Docker logs for container issues:
```bash
docker logs <container_id>
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Docker and Discord bot documentation
3. Open an issue on GitHub

---

**⚠️ Important:** This bot manages system resources and creates containers. Use responsibly and ensure you have proper backups and monitoring in place.
