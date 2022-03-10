import os
import re
import json
import discord
import discord_slash
from time import time
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands

startup = round(time() * 1000)
print('Starting up')

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
ABECEDA = 'abcdefghijklmnoprstuvyz'
ABECEDA_REACTIONS = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇷🇸🇹🇺🇻🇾🇿'
POLL_CHANNEL_ID = os.getenv('POLL_CHANNEL_ID')

kalendar=[]

bot = commands.Bot(command_prefix='!')

slash = discord_slash.SlashCommand(bot, sync_commands=True, debug_guild=os.getenv('DEBUG_GUILD_ID'))

moznosti = [discord_slash.manage_commands.create_option(name='otázka', description='Napíšte otázku', option_type=3,
                                                        required=True),
            discord_slash.manage_commands.create_option(name='ping', description='Pingne rolu', option_type=8,
                                                        required=False)]
for i in ABECEDA:
    moznosti.append(
        discord_slash.manage_commands.create_option(name=f'možnosť_{i}', description=f'Napíšte možnosť {i}',
                                                    option_type=3, required=False)
    )


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    print(f'Started up in {round(time() * 1000) - startup} milliseconds')


@slash.slash(name='poll', description='Vytvorí hlasovanie', options=moznosti)
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
        ano = discord.utils.get(ctx.guild.emojis, name='YES')
        nie = discord.utils.get(ctx.guild.emojis, name='NO')
        await message.add_reaction(ano)
        await message.add_reaction(nie)
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
        await message.add_reaction(ABECEDA_REACTIONS[ABECEDA.index(k)])

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
    povodny_nazov = role.name
    await role.edit(name=nazov)
    await ctx.send(f'Názov role {povodny_nazov} bol zmenený na {role}')

@slash.slash(name='new_event', description='pridá udalosť do kalendára', 
    options= [
    discord_slash.manage_commands.create_option(name= 'name', description= 'názov udalosti', option_type=3,
                                                required=True),
    discord_slash.manage_commands.create_option(name= 'description', description= 'opis udalosti', option_type=3,
                                                required=True),
    discord_slash.manage_commands.create_option(name='date', description='dátum udalosti', option_type=3,
                                                required=True),
    discord_slash.manage_commands.create_option(name= 'ping', description='vyber koho má pingnúť', option_type=8,
                                                required=False)
    ]
)
async def new_event(ctx: discord_slash.SlashContext, name: str, description: str, date: str, ping=None):

    date_list=date.split('.')
    if len(date_list) == 2:
        ping_time = datetime(2022, int(date_list[1]), int(date_list[0]), 16, 0, 0).timestamp()
    else:
        ping_time = datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), 16, 0, 0).timestamp()
    
    ping_time_index=0
    for i in kalendar:
        if ping_time>i[2]:
            break
        ping_time_index+=1

    kalendar.insert(ping_time_index, (name, description, ping_time, ping.name))

    with open('calendar.txt', 'w') as subor:
        json.dump(kalendar, subor)

    await ctx.send('Udalosť bola úspešne pridaná.')

bot.run(TOKEN)
