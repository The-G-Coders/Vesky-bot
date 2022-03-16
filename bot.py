import re
import discord
import discord_slash
from discord import utils
from discord.ext import commands
from discord_slash import SlashContext, manage_commands
from Tasks import Tasks
from lib.utils import *
from lib.yml import YmlConfig
from lib.embeds import Embeds
from lib.regex import DATE_PATTERN, TIME_PATTERN, get_separator

startup = round(t() * 1000)
print('Starting up')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

config = YmlConfig('resources/config.yml')
events = YmlConfig('resources/events.yml')

embeds = Embeds(bot)

TOKEN = config.get('auth.token')
ALPHABET = 'abcdefghijklmnoprstuvyz'
ALPHABET_REACTIONS = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇷🇸🇹🇺🇻🇾🇿'
POLL_CHANNEL_ID = config.get('channel-ids.poll')
GUILD_ID = config.get('auth.debug-guild')


slash = discord_slash.SlashCommand(bot, sync_commands=False, debug_guild=GUILD_ID)

poll_options = [manage_commands.create_option(name='otázka', description='Napíšte otázku', option_type=3, required=True),
                manage_commands.create_option(name='ping', description='Pingne rolu', option_type=8, required=False)]
for i in ALPHABET:
    poll_options.append(
        manage_commands.create_option(name=f'možnosť_{i}', description=f'Napíšte možnosť {i}', option_type=3, required=False)
    )


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    print(f'Started up in {round(t() * 1000) - startup} milliseconds')


@slash.slash(name='poll', description='Vytvorí hlasovanie', options=poll_options)
async def poll(ctx: SlashContext, **kwargs):
    embed = discord.Embed(title='Hlasovanie', description='', url='', color=discord.Color.blue())
    embed.set_author(name=ctx.author.display_name, url='', icon_url=ctx.author.avatar_url)
    embed.set_footer(text=f'{bot.user}', icon_url=bot.user.avatar_url)
    description = ''
    role: discord.Role = kwargs.get('ping')

    channel = bot.get_channel(int(POLL_CHANNEL_ID))

    if channel is None:
        await ctx.reply("Invalid channel", hidden=True)
        return

    if role is None and len(kwargs) < 2 or role is not None and len(kwargs) < 3:
        description += f'**{kwargs["otázka"]}**'
        embed.description = description
        if role is not None:
            await channel.send(kwargs['ping'].mention())
        message = await channel.send(embed=embed)
        await message.add_reaction(utils.get(ctx.guild.emojis, name='YES'))
        await message.add_reaction(utils.get(ctx.guild.emojis, name='NO'))
        await ctx.reply(embed=embeds.default(title='Anketa úspešne vytvorená!'))
        return
    used_letters = []
    description += f'**{kwargs["otázka"]}**\n\n'
    for key, value in kwargs.items():

        if key != 'otázka' and key != 'ping':
            description += f':regional_indicator_{key[-1]}: {value}\n\n'
            used_letters.append(key[-1])
        elif key == 'ping':
            await channel.send(f'<@&{value.id}>')

    embed.description = description
    message = await channel.send(embed=embed)

    for k in used_letters:
        await message.add_reaction(ALPHABET_REACTIONS[ALPHABET.index(k)])

    await ctx.reply(embed=embeds.default(title='Anketa úspešne vytvorená!'))


@slash.slash(name='role-color', description='Mení farbu role', options=[
    manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
    manage_commands.create_option(name='farba', description='Nová farba role napr. #123abc', option_type=str, required=True)
])
@commands.has_permissions(administrator=True)
async def role_color(ctx: SlashContext, role, farba: str):
    if not re.match('(#[0-9a-fA-F]{6})', farba):
        await ctx.reply(embed=embeds.error('Farba musí byť vo formáte #1a2b3c'), hidden=True)
        return
    colour = discord.Colour(int(f'0x{farba.removeprefix("#")}', 16))
    await role.edit(colour=colour)
    await ctx.send(f'Farba role {role} bola zmenená na {colour}')


@slash.slash(name='role-name', description='Mení meno role', options=[
    manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
    manage_commands.create_option(name='nazov', description='Nový názov role', option_type=3, required=True),
])
@commands.has_permissions(administrator=True)
async def role_name(ctx: SlashContext, role, nazov):
    previous_role_name = role.name
    await role.edit(name=nazov)
    await ctx.send(f'Názov role {previous_role_name} bol zmenený na {role}')


@slash.slash(name='new_event', description='pridá udalosť do kalendára', options=[
    manage_commands.create_option(name='name', description='Názov udalosti', option_type=3, required=True),
    manage_commands.create_option(name='description', description='Opis udalosti', option_type=3, required=True),
    manage_commands.create_option(name='date', description='Dátum udalosti', option_type=3, required=True),
    manage_commands.create_option(name='time', description='Čas udalosti(oznámi 5 minut pred zaciatkon)', option_type=3, required=False),
    manage_commands.create_option(name='ping', description='Vyber koho má pingnúť', option_type=8, required=False)
])
async def new_event(ctx: SlashContext, name: str, description: str, date: str, time: str = None, ping: discord.Role = None):
    if event_exists(name):
        await ctx.reply(embed=embeds.error('Event s takýmto menom uz existuje'), hidden=True)
        return

    date_stripped = date.strip()

    if not DATE_PATTERN.match(date_stripped):
        await ctx.reply(embed=embeds.error('Neplatný formát dátumu!'), hidden=True)
        return
    date_list = date_stripped.split(get_separator(date_stripped))

    if time is not None:

        time_stripped = time.strip()

        if not TIME_PATTERN.match(time_stripped):
            await ctx.reply(embed=embeds.error('Neplatný formát ćasu!'), hidden=True)
            return

        time_list = time_stripped.split(':')

        ping_time = datetime_to_epoch(datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time_list[0]), int(time_list[1]), 0))
    else:
        ping_time = datetime_to_epoch(datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), 0, 0, 10))

    events.data['events'][name.strip().replace(' ', '_')] = {
        'description': description,
        'time': ping_time,
        'role': 'no-role' if ping is None else 'everyone' if ping.name == 'everyone' else ping.id
    }

    events.save()

    await ctx.reply(embed=embeds.default(title='Udalosť bola úspešne pridaná!'), hidden=True)


@slash.slash(name='clear', description="Vymaže správy v kanáli podľa parametrov dalej špefikovaných", options=[
    manage_commands.create_option(name='count', description='Počet správ ktoré budú vymazané', option_type=4, required=False),
    manage_commands.create_option(name='filter_by_user', description='Správy konkrétneho usera', option_type=6, required=False)
])
@commands.has_permissions(manage_messages=True)
async def clear(ctx: SlashContext, count: int = None, filter_by_user: discord.User = None):

    # TODO filter by user?

    if count is None:
        await ctx.channel.purge()
    else:
        if count > 100:
            await ctx.reply(embed=embeds.error('Môžeš vymazať najviac 100 správ naraz'), hidden=True)
            return
        else:
            await ctx.channel.purge(limit=count)
    await ctx.reply(embed=embeds.default(title='Správy úspešne vymazané'), hidden=True)


@bot.event
async def on_slash_command_error(ctx: SlashContext, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=embeds.error('Na použitie tohto príkazu nemáš oprávnenie'), hidden=True)
        return


def load_cogs():
    bot.add_cog(Tasks(bot))


def event_exists(name: str):
    for key in events.get("events"):
        if key == name.strip().replace(' ', '_'):
            return True
    return False


load_cogs()

bot.run(TOKEN)
