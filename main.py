import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Słownik aktywnych przerzucań
move_tasks = {}

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

class StopButton(ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @ui.button(label="🛑 Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        task = move_tasks.pop(self.member.id, None)
        if task:
            task.cancel()
            await interaction.response.edit_message(
                content=f"Zatrzymano przenoszenie {self.member.display_name}.", view=None)
        else:
            await interaction.response.edit_message(
                content=f"{self.member.display_name} nie był przenoszony.", view=None)

async def move_user(member: discord.Member, channel1: discord.VoiceChannel, channel2: discord.VoiceChannel, original_channel: discord.VoiceChannel):
    try:
        toggling = False
        in_toggle = False

        while True:
            if member.voice is None:
                await asyncio.sleep(2)
                continue

            voice_state = member.voice
            is_muted = voice_state.mute or voice_state.self_mute

            if is_muted and not in_toggle:
                in_toggle = True
                print(f"{member.display_name} został wyciszony – rozpoczynam przenoszenie.")

            elif not is_muted and in_toggle:
                await member.move_to(original_channel)
                in_toggle = False
                print(f"{member.display_name} nie jest już wyciszony – kończę przenoszenie.")

            if in_toggle:
                target_channel = channel2 if toggling else channel1
                if voice_state.channel != target_channel:
                    await member.move_to(target_channel)
                toggling = not toggling

            await asyncio.sleep(2)

    except asyncio.CancelledError:
        print(f"Zatrzymano przenoszenie {member.display_name}")
        return
    except Exception as e:
        print(f"Błąd podczas przenoszenia {member.display_name}: {e}")
        await asyncio.sleep(2)

@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="toggle_move", description="Zaczyna przenosić użytkownika dopóki jest wyciszony")
async def toggle_move(interaction: discord.Interaction, member: discord.Member):
    channel1 = discord.utils.get(interaction.guild.voice_channels, name="ping")
    channel2 = discord.utils.get(interaction.guild.voice_channels, name="pong")

    if not channel1 or not channel2:
        await interaction.response.send_message("Nie znaleziono kanałów 'ping' i 'pong'.", ephemeral=True)
        return

    if member.voice is None or member.voice.channel is None:
        await interaction.response.send_message(f"{member.display_name} nie jest na kanale głosowym.", ephemeral=True)
        return

    if member.id in move_tasks:
        await interaction.response.send_message(f"{member.display_name} już jest przenoszony!", ephemeral=True)
        return

    original_channel = member.voice.channel
    task = asyncio.create_task(move_user(member, channel1, channel2, original_channel))
    move_tasks[member.id] = task
    view = StopButton(member)
    await interaction.response.send_message(f"Rozpoczęto przenoszenie {member.display_name}.", view=view)

@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="stop", description="Zatrzymuje przenoszenie wybranego użytkownika")
async def stop(interaction: discord.Interaction, member: discord.Member):
    task = move_tasks.pop(member.id, None)
    if task:
        task.cancel()
        await interaction.response.send_message(f"Zatrzymano przenoszenie {member.display_name}.")
    else:
        await interaction.response.send_message(f"{member.display_name} nie był przenoszony.", ephemeral=True)

@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="stopall", description="Zatrzymuje przenoszenie wszystkich użytkowników")
async def stopall(interaction: discord.Interaction):
    count = len(move_tasks)
    for task in move_tasks.values():
        task.cancel()
    move_tasks.clear()
    await interaction.response.send_message(f"Zatrzymano przenoszenie {count} użytkowników.")
