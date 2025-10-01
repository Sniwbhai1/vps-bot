import discord
from discord.ext import commands
import asyncio
import os
import re
from typing import List, Tuple
from vps_manager import VPSManager
from config import DISCORD_TOKEN, DISCORD_GUILD_ID

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize VPS Manager
vps_manager = VPSManager()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="VPS Resources"))

@bot.command(name='create')
async def create_vps(ctx, *, args: str = None):
    """
    Create a new VPS with specified resources
    Usage: !create <ram_gb> <cpu_cores> <disk_gb>
    Example: !create 8 4 30
    """
    if not args:
        await ctx.send("❌ **Usage:** `!create <ram_gb> <cpu_cores> <disk_gb>`\n"
                      "**Example:** `!create 8 4 30`\n"
                      "• 8 = RAM in GB\n"
                      "• 4 = CPU cores\n"
                      "• 30 = Disk space in GB")
        return
    
    # Parse arguments
    try:
        parts = args.strip().split()
        if len(parts) != 3:
            raise ValueError("Invalid number of arguments")
        
        ram_gb = int(parts[0])
        cpu_cores = int(parts[1])
        disk_gb = int(parts[2])
        
        # Validate input
        if ram_gb < 1 or ram_gb > 32:
            await ctx.send("❌ **Error:** RAM must be between 1-32 GB")
            return
        
        if cpu_cores < 1 or cpu_cores > 16:
            await ctx.send("❌ **Error:** CPU cores must be between 1-16")
            return
        
        if disk_gb < 5 or disk_gb > 500:
            await ctx.send("❌ **Error:** Disk space must be between 5-500 GB")
            return
        
    except ValueError as e:
        await ctx.send("❌ **Error:** Invalid arguments. Please use: `!create <ram_gb> <cpu_cores> <disk_gb>`")
        return
    
    # Show creation message
    embed = discord.Embed(
        title="🚀 Creating VPS...",
        description=f"**Specifications:**\n"
                   f"• RAM: {ram_gb} GB\n"
                   f"• CPU: {cpu_cores} cores\n"
                   f"• Disk: {disk_gb} GB",
        color=0x00ff00
    )
    embed.set_footer(text="This may take a few minutes...")
    message = await ctx.send(embed=embed)
    
    # Create VPS
    success, result_msg, vps_config = await vps_manager.create_vps(ram_gb, cpu_cores, disk_gb)
    
    if success:
        # Update message with success
        embed = discord.Embed(
            title="✅ VPS Created Successfully!",
            description=f"**VPS Name:** `{vps_config.name}`\n"
                       f"**Specifications:**\n"
                       f"• RAM: {ram_gb} GB\n"
                       f"• CPU: {cpu_cores} cores\n"
                       f"• Disk: {disk_gb} GB\n"
                       f"**Status:** {vps_config.status}",
            color=0x00ff00
        )
        
        # Wait a bit for tmate setup
        await asyncio.sleep(5)
        
        # Get updated VPS info
        vps_info = vps_manager.get_vps_info(vps_config.name)
        if vps_info and vps_info.get('tmate_session'):
            embed.add_field(
                name="🔗 Remote Access (tmate)",
                value=f"```bash\n{vps_info['tmate_session']}\n```",
                inline=False
            )
        else:
            embed.add_field(
                name="🔗 Remote Access (tmate)",
                value="Setting up tmate session...",
                inline=False
            )
        
        await message.edit(embed=embed)
        
        # Send follow-up message with tmate info after a delay
        await asyncio.sleep(10)
        vps_info = vps_manager.get_vps_info(vps_config.name)
        if vps_info and vps_info.get('tmate_session'):
            tmate_embed = discord.Embed(
                title="🔗 tmate Session Ready",
                description=f"**VPS:** `{vps_config.name}`\n"
                           f"**SSH Command:**\n```bash\n{vps_info['tmate_session']}\n```",
                color=0x0099ff
            )
            await ctx.send(embed=tmate_embed)
    else:
        # Update message with error
        embed = discord.Embed(
            title="❌ VPS Creation Failed",
            description=result_msg,
            color=0xff0000
        )
        await message.edit(embed=embed)

@bot.command(name='list')
async def list_vps(ctx):
    """List all VPS instances"""
    vps_list = vps_manager.list_vps()
    
    if not vps_list:
        await ctx.send("📋 **No VPS instances found**")
        return
    
    embed = discord.Embed(
        title="📋 VPS Instances",
        color=0x0099ff
    )
    
    for vps in vps_list:
        status_emoji = "🟢" if vps['status'] == "running" else "🔴" if vps['status'] == "stopped" else "🟡"
        
        vps_info = f"**Specs:** {vps['ram_gb']}GB RAM, {vps['cpu_cores']} CPU, {vps['disk_gb']}GB Disk\n"
        vps_info += f"**Status:** {status_emoji} {vps['status']}\n"
        
        if vps.get('tmate_session'):
            vps_info += f"**tmate:** `{vps['tmate_session']}`"
        
        embed.add_field(
            name=f"🖥️ {vps['name']}",
            value=vps_info,
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def vps_status(ctx, vps_name: str = None):
    """Get status of a specific VPS or all VPS instances"""
    if vps_name:
        vps_info = vps_manager.get_vps_info(vps_name)
        if not vps_info:
            await ctx.send(f"❌ VPS `{vps_name}` not found")
            return
        
        status_emoji = "🟢" if vps_info['status'] == "running" else "🔴" if vps_info['status'] == "stopped" else "🟡"
        
        embed = discord.Embed(
            title=f"🖥️ VPS Status: {vps_name}",
            color=0x0099ff
        )
        
        embed.add_field(name="Specifications", value=f"• RAM: {vps_info['ram_gb']} GB\n• CPU: {vps_info['cpu_cores']} cores\n• Disk: {vps_info['disk_gb']} GB", inline=True)
        embed.add_field(name="Status", value=f"{status_emoji} {vps_info['status']}", inline=True)
        
        if vps_info.get('tmate_session'):
            embed.add_field(name="Remote Access", value=f"```bash\n{vps_info['tmate_session']}\n```", inline=False)
        
        await ctx.send(embed=embed)
    else:
        await list_vps(ctx)

@bot.command(name='stop')
async def stop_vps(ctx, vps_name: str):
    """Stop a VPS instance"""
    if not vps_name:
        await ctx.send("❌ **Usage:** `!stop <vps_name>`")
        return
    
    success, message = await vps_manager.stop_vps(vps_name)
    
    if success:
        embed = discord.Embed(
            title="⏹️ VPS Stopped",
            description=message,
            color=0xffa500
        )
    else:
        embed = discord.Embed(
            title="❌ Error",
            description=message,
            color=0xff0000
        )
    
    await ctx.send(embed=embed)

@bot.command(name='delete')
async def delete_vps(ctx, vps_name: str):
    """Delete a VPS instance"""
    if not vps_name:
        await ctx.send("❌ **Usage:** `!delete <vps_name>`")
        return
    
    # Confirmation
    embed = discord.Embed(
        title="⚠️ Confirm Deletion",
        description=f"Are you sure you want to delete VPS `{vps_name}`?\nThis action cannot be undone!",
        color=0xff0000
    )
    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
    
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        
        if str(reaction.emoji) == "✅":
            success, result_msg = await vps_manager.delete_vps(vps_name)
            
            if success:
                embed = discord.Embed(
                    title="🗑️ VPS Deleted",
                    description=result_msg,
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=result_msg,
                    color=0xff0000
                )
            
            await message.edit(embed=embed)
        else:
            await message.edit(embed=discord.Embed(title="❌ Deletion Cancelled", color=0xffa500))
    
    except asyncio.TimeoutError:
        await message.edit(embed=discord.Embed(title="⏰ Timeout", description="Deletion cancelled due to timeout", color=0xffa500))

@bot.command(name='resources')
async def system_resources(ctx):
    """Show system resource usage"""
    resources = vps_manager.get_system_resources()
    
    embed = discord.Embed(
        title="💻 System Resources",
        color=0x0099ff
    )
    
    embed.add_field(
        name="Memory",
        value=f"Used: {resources['used_ram_gb']:.1f} GB / {resources['total_ram_gb']:.1f} GB",
        inline=True
    )
    
    embed.add_field(
        name="CPU",
        value=f"Usage: {resources['cpu_usage_percent']:.1f}%\nCores: {resources['cpu_cores']}",
        inline=True
    )
    
    embed.add_field(
        name="Disk",
        value=f"Used: {resources['disk_used_gb']:.1f} GB / {resources['disk_total_gb']:.1f} GB",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='tmate')
async def tmate_command(ctx, vps_name: str = None, action: str = None):
    """Get tmate SSH session for a VPS"""
    if not vps_name:
        await ctx.send("❌ **Usage:** `!tmate <vps_name> [refresh]`\n**Example:** `!tmate vps-1234567890`\n**Refresh:** `!tmate vps-1234567890 refresh`")
        return
    
    vps_info = vps_manager.get_vps_info(vps_name)
    if not vps_info:
        await ctx.send(f"❌ VPS `{vps_name}` not found")
        return
    
    # Handle refresh action
    if action and action.lower() == "refresh":
        embed = discord.Embed(
            title="🔄 Refreshing tmate Session...",
            description=f"**VPS:** `{vps_name}`\nCreating a new tmate session...",
            color=0xffa500
        )
        message = await ctx.send(embed=embed)
        
        success, result_msg = await vps_manager.refresh_tmate_session(vps_name)
        
        if success:
            # Get updated VPS info
            vps_info = vps_manager.get_vps_info(vps_name)
            embed = discord.Embed(
                title="✅ tmate Session Refreshed",
                description=f"**VPS:** `{vps_name}`\n"
                           f"**Status:** {vps_info['status']}\n\n"
                           f"**New SSH Command:**\n```bash\n{vps_info['tmate_session']}\n```",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Refresh tmate Session",
                description=f"**VPS:** `{vps_name}`\n**Error:** {result_msg}",
                color=0xff0000
            )
        
        await message.edit(embed=embed)
        return
    
    # Regular tmate command
    if not vps_info.get('tmate_session'):
        embed = discord.Embed(
            title="⏳ tmate Session Not Ready",
            description=f"**VPS:** `{vps_name}`\n"
                       f"tmate session is still being set up.\n\n"
                       f"**Try:** `!tmate {vps_name} refresh` to create a new session",
            color=0xffa500
        )
        embed.add_field(
            name="💡 Tip",
            value="If this persists, the VPS might still be starting up. Wait a moment and try the refresh command.",
            inline=False
        )
    else:
        embed = discord.Embed(
            title="🔗 tmate SSH Session",
            description=f"**VPS:** `{vps_name}`\n"
                       f"**Status:** {vps_info['status']}\n\n"
                       f"**SSH Command:**\n```bash\n{vps_info['tmate_session']}\n```",
            color=0x00ff00
        )
        embed.add_field(
            name="💡 Usage",
            value="Copy and paste the SSH command above into your terminal to connect to your VPS",
            inline=False
        )
        embed.add_field(
            name="🔄 Refresh",
            value=f"Use `!tmate {vps_name} refresh` to create a new session",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='commands')
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="🤖 VPS Bot Commands",
        description="Manage your VPS resources with these commands:",
        color=0x0099ff
    )
    
    commands_list = [
        ("!create <ram> <cpu> <disk>", "Create a new VPS (e.g., !create 8 4 30)"),
        ("!list", "List all VPS instances"),
        ("!status [vps_name]", "Get VPS status"),
        ("!tmate <vps_name> [refresh]", "Get tmate SSH session for VPS"),
        ("!stop <vps_name>", "Stop a VPS instance"),
        ("!delete <vps_name>", "Delete a VPS instance"),
        ("!resources", "Show system resource usage"),
        ("!commands", "Show this help message")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument provided")
    else:
        print(f"Error: {error}")
        await ctx.send("❌ An error occurred while processing the command")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in environment variables")
        print("Please create a .env file with your Discord bot token")
        exit(1)
    
    print("🚀 Starting VPS Bot...")
    bot.run(DISCORD_TOKEN)
