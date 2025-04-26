import discord
import asyncio
import os

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

PING_CHANNEL_NAME = "ping"
PONG_CHANNEL_NAME = "pong"

# Aktywne przerzucanie pojedynczych osób
active_rapes = {}

# Aktywne przerzucanie wszystkich osób
rape_all_active = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Zalogowano jako {bot.user}")

# /rape - pojedyncza osoba
@tree.command(name="rape", description="Przerzucaj użytkownika między ping a pong.")
async def rape(interaction: discord.Interaction, member: discord.Member):
    ping = discord.utils.get(interaction.guild.voice_channels, name=PING_CHANNEL_NAME)
    pong = discord.utils.get(interaction.guild.voice_channels, name=PONG_CHANNEL_NAME)

    if not ping or not pong:
        await interaction.response.send_message("Nie znalazłem kanałów 'ping' lub 'pong'.", ephemeral=True)
        return

    await interaction.response.send_message(f"Zaczynam przerzucać {member.display_name}!", ephemeral=False)
    active_rapes[member.id] = True

    while active_rapes.get(member.id, False):
        if member.voice:
            await member.move_to(pong)
            await asyncio.sleep(1)
            await member.move_to(ping)
            await asyncio.sleep(1)
        else:
            await interaction.channel.send(f"{member.display_name} wyszedł z kanału głosowego, zatrzymuję.")
            break

# /stop - zatrzymanie pojedynczej osoby
@tree.command(name="stop", description="Zatrzymaj przerzucanie użytkownika.")
async def stop(interaction: discord.Interaction, member: discord.Member):
    active_rapes[member.id] = False
    await interaction.response.send_message(f"Zatrzymałem przerzucanie {member.display_name}.", ephemeral=False)

# /rapeall - wszyscy użytkownicy
@tree.command(name="rapeall", description="Przerzucaj wszystkich z kanału ping i pong w kółko.")
async def rapeall(interaction: discord.Interaction):
    ping = discord.utils.get(interaction.guild.voice_channels, name=PING_CHANNEL_NAME)
    pong = discord.utils.get(interaction.guild.voice_channels, name=PONG_CHANNEL_NAME)

    if not ping or not pong:
        await interaction.response.send_message("Nie znalazłem kanałów 'ping' lub 'pong'.", ephemeral=True)
        return

    await interaction.response.send_message("Zaczynam przerzucać wszystkich!", ephemeral=False)
    rape_all_active[interaction.guild.id] = True

    while rape_all_active.get(interaction.guild.id, False):
        all_members = [m for m in ping.members + pong.members]
        for member in all_members:
            try:
                if member.voice:
                    current_channel = member.voice.channel
                    target_channel = pong if current_channel == ping else ping
                    await member.move_to(target_channel)
            except Exception as e:
                print(f"Błąd przenoszenia {member.display_name}: {e}")
        await asyncio.sleep(1)

# /stopall - zatrzymanie wszystkich
@tree.command(name="stopall", description="Zatrzymaj przerzucanie wszystkich.")
async def stopall(interaction: discord.Interaction):
    rape_all_active[interaction.guild.id] = False
    await interaction.response.send_message("Zatrzymałem przerzucanie wszystkich!", ephemeral=False)

bot.run(os.getenv('token'))

