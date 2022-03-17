import discord
from discord.ext import commands
import discord_slash

from lib.yml import YmlConfig

config = YmlConfig('resources/config.yml')
TOKEN = config.get('auth.token')
GUILD_ID = config.get('auth.debug-guild')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
slash = discord_slash.SlashCommand(bot, sync_commands=False, debug_guild=GUILD_ID)


@bot.event
async def on_ready():
    await discord_slash.manage_commands.remove_all_commands(bot_id=882236631891976233, bot_token=TOKEN)
    print("remoede")


bot.run(TOKEN)
