import re
import discord
import discord_slash
from time import time as tm
from discord import utils
from datetime import datetime
from discord.ext import commands
from lib.yml import YmlConfig
from Tasks import Tasks
from lib.regex import DATE_PATTERN, HOUR_PATTERN, get_separator

startup = round(tm() * 1000)
print('Starting up')

config = YmlConfig('resources/config.yml')
events = YmlConfig('resources/events.yml')

TOKEN = config.get('auth.token')
ALPHABET = 'abcdefghijklmnoprstuvyz'
ALPHABET_REACTIONS = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇷🇸🇹🇺🇻🇾🇿'
POLL_CHANNEL_ID = config.get('channel-ids.poll')
ANNOUNCEMENTS_CHANNEL_ID = config.get('channel-ids.announcements')
GUILD_ID = config.get('auth.debug-guild')

bot = commands.Bot(command_prefix='!')

slash = discord_slash.SlashCommand(bot, sync_commands=True, debug_guild=GUILD_ID)

poll_options = [discord_slash.manage_commands.create_option(name='otázka', description='Napíšte otázku', option_type=3,
                                                            required=True),
                discord_slash.manage_commands.create_option(name='ping', description='Pingne rolu', option_type=8,
                                                            required=False)]
for i in ALPHABET:
    poll_options.append(
        discord_slash.manage_commands.create_option(name=f'možnosť_{i}', description=f'Napíšte možnosť {i}',
                                                    option_type=3, required=False)
    )


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    print(f'Started up in {round(tm() * 1000) - startup} milliseconds')


@slash.slash(name='poll', description='Vytvorí hlasovanie', options=poll_options)
async def poll(ctx: discord_slash.SlashContext, **kwargs):
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
        await ctx.reply('Poll successfully created')
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

    await ctx.reply('Anketa vytvorená')


@slash.slash(name='role-color', description='Mení farbu role',
             options=[
                 discord_slash.manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť',
                                                             option_type=8, required=True),
                 discord_slash.manage_commands.create_option(name='farba', description='Nová farba role napr. #123abc',
                                                             option_type=str, required=True)
             ])
@commands.has_permissions(administrator=True)
async def role_color(ctx: discord_slash.SlashContext, role, farba: str):
    if not re.match('(#[0-9a-fA-F]{6})', farba):
        await ctx.reply('Farba musí byť vo formáte #1a2b3c', hidden=True)
        return
    colour = discord.Colour(int(f'0x{farba.removeprefix("#")}', 16))
    await role.edit(colour=colour)
    await ctx.send(f'Farba role {role} bola zmenená na {colour}')


@slash.slash(name='role-name', description='Mení meno role',
             options=[
                 discord_slash.manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť',
                                                             option_type=8, required=True),
                 discord_slash.manage_commands.create_option(name='nazov', description='Nový názov role', option_type=3,
                                                             required=True),
             ])
@commands.has_permissions(administrator=True)
async def role_name(ctx: discord_slash.SlashContext, role, nazov):
    previous_role_name = role.name
    await role.edit(name=nazov)
    await ctx.send(f'Názov role {previous_role_name} bol zmenený na {role}')


@slash.slash(name='new_event', description='pridá udalosť do kalendára',
             options=[
                 discord_slash.manage_commands.create_option(name='name', description='Názov udalosti', option_type=3,
                                                             required=True),
                 discord_slash.manage_commands.create_option(name='description', description='Opis udalosti',
                                                             option_type=3,
                                                             required=True),
                 discord_slash.manage_commands.create_option(name='date', description='Dátum udalosti', option_type=3,
                                                             required=True),
                 discord_slash.manage_commands.create_option(name='time',
                                                             description='Čas udalosti(oznámi 5 minut pred zaciatkon)',
                                                             option_type=3,
                                                             required=False),
                 discord_slash.manage_commands.create_option(name='ping', description='Vyber koho má pingnúť',
                                                             option_type=8,
                                                             required=False)
             ]
             )
async def new_event(ctx: discord_slash.SlashContext, name: str, description: str, date: str, time: str = None, ping=None):
    date_stripped = date.strip()
    if not DATE_PATTERN.match(date_stripped):
            await ctx.reply("Neplatný formát dátumu", hidden=True)
            return
    date_list = date_stripped.split(get_separator(date_stripped))

    if time is not None:
        
        time_stripped = time.strip()

        if not HOUR_PATTERN.match(time_stripped):
            await ctx.reply("Neplatný formát času", hidden=True)
            return

        time_list = time_stripped.split(':')

    else:
        time_list=[16, 0]
    ping_time = round(
            datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time_list[0]), int(time_list[1]),
                    0).timestamp())
    if ping is None:
        events.data['events'][name.strip().replace(' ', '_')] = {
            'description': description,
            'time': ping_time,
            'ping': 'no-ping'
        }
    else:
        events.data['events'][name.strip().replace(' ', '_')] = {
            'description': description,
            'time': ping_time,
            'ping': f'<@&{ping.id}>'
        }
    events.save()

    await ctx.send('Udalosť bola úspešne pridaná.')


def load_cogs():
    bot.add_cog(Tasks(bot))

load_cogs()

bot.run(TOKEN)
