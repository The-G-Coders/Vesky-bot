import discord
from os import getenv
from dotenv import load_dotenv
from discord.ext import commands
import discord_slash

from lib.yml import YmlConfig

load_dotenv()

TOKEN = getenv('TOKEN')
GUILD_ID = int(getenv('DEBUG_GUILD_ID'))

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
slash = discord_slash.SlashCommand(bot, sync_commands=False, debug_guild=GUILD_ID)


@bot.event
async def on_ready():
    await discord_slash.manage_commands.remove_all_commands(bot_id=882236631891976233, bot_token=TOKEN)
    print("Removed all commands")


bot.run(TOKEN)
