import signal
import discord
import discord_slash
from os import getenv
from time import time as t
from discord import utils
from datetime import datetime
from discord.ext import commands
from discord_slash import SlashContext
from lib.database import Database
from lib.utils import init_env, intents
from lib.embeds import Embeds, CommandDescription

startup = round(t() * 1000)
print('Starting up')

init_env()

bot = commands.Bot(command_prefix='!', intents=intents(), activity=discord.Activity(type=discord.ActivityType.listening, name="/help"), self_bot=True)

db = Database()

events = db.events
shutdowns = db.shutdowns
users_slowmode = db.slowmode

embeds = Embeds(bot)

TOKEN = getenv('TOKEN')
GUILD_ID = int(getenv('DEBUG_GUILD_ID'))
SHUTDOWN_PASSWORD = getenv("SHUTDOWN_PASSWORD")

slash = discord_slash.SlashCommand(bot, sync_commands=True, debug_guild=GUILD_ID)


@slash.slash(
    name='help',
    description='Vypíše všetky príkazy'
)
async def _help(ctx: SlashContext):
    category_id = int(getenv('BOT_CATEGORY_ID'))
    if ctx.channel.category_id != category_id:
        await ctx.reply(embed=embeds.error(f"Tento command môžeš použiť len v {utils.get(bot.get_guild(GUILD_ID).categories, id=category_id).name} kategórii"), hidden=True)
        return
    desc = CommandDescription()
    if getenv("POLLS") == 'true':
        desc.add_command('poll', 'Vytvorí hlasovanie')
    if getenv('EVENTS') == 'true':
        desc.add_command('event add', 'Pridá udalosť do kalendára')
        desc.add_command('event list', 'Zobrazí naplánované udalosti')
        desc.add_command("event remove", "Zmaže udalosť z kalendára")
    if getenv('SLOWMODE') == 'true':
        desc.add_command('slowmode status', 'Zobrazí status slowmodu pre membera')
        desc.add_command('slowmode list', 'Zobrazí všetkých memberov so slowmode')
    if getenv('UTILS') == 'true' or getenv('SLOWMODE') == 'true':
        desc.add_break('> **:warning: Obmedzenie:** Funkcie vyhradené len pre ľudí s oprávnením')
    if getenv('UTILS') == 'true':
        desc.add_command('clear', 'Vymaže správy v kanáli')
        desc.add_command('role color', 'Zmení farbu role')
        desc.add_command('role name', 'Zmení meno role')
    if getenv('SLOWMODE') == 'true':
        desc.add_command('slowmode create', 'Pridá slowmode memberovi')
        desc.add_command('slowmode remove', 'Odstráni slowmode memberovi')
    eb = embeds.default(title="Zoznam príkazov", desc=desc.to_string())
    await ctx.reply(embed=eb, hidden=False)


@bot.event
async def on_slash_command_error(ctx: SlashContext, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=embeds.error('Na použitie tohto príkazu nemáš oprávnenie'), hidden=True)
        return
    if isinstance(error, discord.client.Forbidden):
        await ctx.reply(embed=embeds.error('Na vykonanie tohto príkazu nemám oprávnenie.\nKontaktuj administrátora'), hidden=True)
        return
    raise error


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user} in {utils.get(bot.guilds, id=GUILD_ID)}')
    print(f'Started up in {round(t() * 1000) - startup} milliseconds')


@bot.event
async def on_message(message: discord.Message):
    author: discord.Member = message.author
    if message.content == SHUTDOWN_PASSWORD:
        if author.guild_permissions.administrator:
            print('Shutting down...')
            await message.delete()
            await author.send('Bot bol uspesne vypnuty a jeho vypnutie zaznamenané!')
            if author.id != 381390718196908032:
                owner = bot.get_user(381390718196908032)
                await owner.send(f'{author.mention} použil shutdown password a vypol bota!')
            await bot.change_presence(status=discord.Status.offline)
            bot.dispatch('bot_shutdown', True)
            shutdowns.insert_one({'user': author.name + '#' + author.discriminator, 'time': datetime.now().__format__('%d.%m.%Y %H:%M:%S')})
            await bot.close()


@bot.event
async def on_bot_shutdown(password_used: bool):
    if not password_used:
        await bot.change_presence(status=discord.Status.offline)
        await bot.close()


def load_modules():
    if getenv('EVENTS') == 'true':
        from modules.Events import EventCommands, EventAnnouncementTask
        bot.add_cog(EventCommands(slash, db, embeds))
        bot.add_cog(EventAnnouncementTask(bot, embeds, db))
        print('Module loaded: Events')

    if getenv('SLOWMODE') == 'true':
        from modules.Slowmode import Slowmode
        bot.add_cog(Slowmode(bot, slash, db, embeds))
        print('Module loaded: Slowmode')

    if getenv('POLLS') == 'true':
        from modules.Polls import PollCommands
        bot.add_cog(PollCommands(bot, slash, embeds))
        print('Module loaded: Polls')

    if getenv('UTILS') == 'true':
        from modules.Utils import UtilCommands
        bot.add_cog(UtilCommands(slash, embeds))
        print('Module loaded: Utils')


load_modules()

signal.signal(signal.SIGINT, lambda s, f: bot.dispatch('bot_shutdown', False))

bot.run(TOKEN)
