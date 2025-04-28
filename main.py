import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Słownik aktywnych przerzucań
rape_tasks = {}

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

async def rape_user(member: discord.Member, channel1: discord.VoiceChannel, channel2: discord.VoiceChannel):
    try:
        while True:
            if member.voice is None:
                pass
            else:
                current_channel = member.voice.channel
                if current_channel == channel1:
                    await member.move_to(channel2)
                else:
                    await member.move_to(channel1)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print(f"Zatrzymano anihilacje {member.display_name}")
        return
    except Exception as e:
        print(f"Błąd podczas anihilacji {member.display_name}: {e}")
        await asyncio.sleep(1)

class StopButton(ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @ui.button(label="🛑 Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        task = rape_tasks.pop(self.member.id, None)
        if task:
            task.cancel()
            await interaction.response.edit_message(content=f"Zatrzymano anihilacje {self.member.display_name}.", view=None)
        else:
            await interaction.response.edit_message(content=f"{self.member.display_name} nie był przerzucany.", view=None)

# KOMENDA: rape
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="rape")
async def rape(interaction: discord.Interaction, member: discord.Member):
    """Zaczyna anihilować pojedynczego użytkownika"""
    channel1 = discord.utils.get(interaction.guild.voice_channels, name="ping")
    channel2 = discord.utils.get(interaction.guild.voice_channels, name="pong")
    if not channel1 or not channel2:
        await interaction.response.send_message("Nie znaleziono kanałów 'ping' i 'pong'", ephemeral=True)
        return

    if member.id in rape_tasks:
        await interaction.response.send_message(f"{member.display_name} już jest anihilowany!", ephemeral=True)
    else:
        task = asyncio.create_task(rape_user(member, channel1, channel2))
        rape_tasks[member.id] = task
        view = StopButton(member)
        await interaction.response.send_message(f"Rozpoczęto anihilacje {member.display_name}!", view=view)

@rape.error
async def rape_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił błąd: {error}", ephemeral=True)

# KOMENDA: stop
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction, member: discord.Member):
    """Zatrzymuje przerzucanie pojedynczego użytkownika"""
    task = rape_tasks.pop(member.id, None)
    if task:
        task.cancel()
        await interaction.response.send_message(f"Zatrzymano anihilacje {member.display_name}.")
    else:
        await interaction.response.send_message(f"{member.display_name} nie był przerzucany.", ephemeral=True)

@stop.error
async def stop_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił błąd: {error}", ephemeral=True)

# KOMENDA: rapeall
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="rapeall")
async def rapeall(interaction: discord.Interaction):
    """Zaczyna anihilować wszystkich użytkowników"""
    channel1 = discord.utils.get(interaction.guild.voice_channels, name="ping")
    channel2 = discord.utils.get(interaction.guild.voice_channels, name="pong")
    if not channel1 or not channel2:
        await interaction.response.send_message("Nie znaleziono kanałów 'ping' i 'pong'", ephemeral=True)
        return

    count = 0
    for member in interaction.guild.members:
        if member.bot:
            continue
        if member.voice is None:
            continue
        if member.id not in rape_tasks:
            task = asyncio.create_task(rape_user(member, channel1, channel2))
            rape_tasks[member.id] = task
            count += 1

    await interaction.response.send_message(f"Rozpoczęto anihilacje {count} użytkowników!")

@rapeall.error
async def rapeall_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił błąd: {error}", ephemeral=True)

# KOMENDA: stopall
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="stopall")
async def stopall(interaction: discord.Interaction):
    """Zatrzymuje anihilacje wszystkich użytkowników"""
    count = len(rape_tasks)
    for task in rape_tasks.values():
        task.cancel()
    rape_tasks.clear()
    await interaction.response.send_message(f"Zatrzymano anihilacje {count} użytkowników.")

@stopall.error
async def stopall_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy!", ephemeral=True)
    else:
        await interaction.response.send_message(f"Wystąpił błąd: {error}", ephemeral=True)

# Start bota
bot.run(os.getenv('token'))
