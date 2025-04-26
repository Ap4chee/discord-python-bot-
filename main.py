import discord
from discord.ext import commands
from discord import app_commands
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
                # User nie jest na żadnym kanale głosowym
                pass
            else:
                current_channel = member.voice.channel
                if current_channel == channel1:
                    await member.move_to(channel2)
                else:
                    await member.move_to(channel1)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print(f"Zatrzymano przerzucanie {member.display_name}")
        return
    except Exception as e:
        print(f"Błąd podczas przerzucania {member.display_name}: {e}")
        await asyncio.sleep(1)

@bot.tree.command(name="rape")
async def rape(interaction: discord.Interaction, member: discord.Member):
    """Zaczyna przerzucać pojedynczego użytkownika"""
    channel1 = discord.utils.get(interaction.guild.voice_channels, name="ping")
    channel2 = discord.utils.get(interaction.guild.voice_channels, name="pong")
    if not channel1 or not channel2:
        await interaction.response.send_message("Nie znaleziono kanałów 'ping' i 'pong'", ephemeral=True)
        return

    if member.id in rape_tasks:
        await interaction.response.send_message(f"{member.display_name} już jest przerzucany!", ephemeral=True)
    else:
        task = asyncio.create_task(rape_user(member, channel1, channel2))
        rape_tasks[member.id] = task
        await interaction.response.send_message(f"Rozpoczęto przerzucanie {member.display_name}!")

@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction, member: discord.Member):
    """Zatrzymuje przerzucanie pojedynczego użytkownika"""
    task = rape_tasks.pop(member.id, None)
    if task:
        task.cancel()
        await interaction.response.send_message(f"Zatrzymano przerzucanie {member.display_name}.")
    else:
        await interaction.response.send_message(f"{member.display_name} nie był przerzucany.", ephemeral=True)

@bot.tree.command(name="rapeall")
async def rapeall(interaction: discord.Interaction):
    """Zaczyna przerzucać wszystkich użytkowników"""
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

    await interaction.response.send_message(f"Rozpoczęto przerzucanie {count} użytkowników!")

@bot.tree.command(name="stopall")
async def stopall(interaction: discord.Interaction):
    """Zatrzymuje przerzucanie wszystkich użytkowników"""
    count = len(rape_tasks)
    for task in rape_tasks.values():
        task.cancel()
    rape_tasks.clear()
    await interaction.response.send_message(f"Zatrzymano przerzucanie {count} użytkowników.")

bot.run(os.getenv('token'))
