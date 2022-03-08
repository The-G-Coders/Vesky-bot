import os
import re
import discord
import discord_slash
from time import time
from dotenv import load_dotenv
from discord.ext import commands

startup = round(time() * 1000)
print('Starting up')

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
ABECEDA = 'abcdefghijklmnoprstuvyz'
ABECEDA_REACTIONS = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇷🇸🇹🇺🇻🇾🇿'

bot = commands.Bot(command_prefix='!')

slash = discord_slash.SlashCommand(bot, sync_commands=True, debug_guild=900429095215718430)


moznosti = [discord_slash.manage_commands.create_option(name='otázka', description='Napíšte otázku', option_type=3, required=True),
            discord_slash.manage_commands.create_option(name='ping', description='Pingne rolu', option_type=8, required=False)]
for i in ABECEDA:
    moznosti.append(
        discord_slash.manage_commands.create_option(name=f'možnosť_{i}', description=f'Napíšte možnosť {i}', option_type=3, required=False)
    )


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    print(f'Started up in {round(time() * 1000) - startup} milliseconds')


@slash.slash(name='poll', description='Vytvorí hlasovanie', options=moznosti)
async def poll(ctx: discord_slash.SlashContext, **args):
    embed = discord.Embed(title='Hlasovanie', description='', url='', color=discord.Color.blue())
    embed.set_author(name=ctx.author.display_name, url='', icon_url=ctx.author.avatar_url)

    if len(args) == 1:
        embed.add_field(name=args['otázka'], value='-------', inline=False)
        message = await ctx.send(embed=embed)
        ano = discord.utils.get(ctx.guild.emojis, name='YES')
        nie = discord.utils.get(ctx.guild.emojis, name='NO')
        await message.add_reaction(ano)
        await message.add_reaction(nie)
        return
    pouzite_pismena = []
    obsah = ' \n'
    for poradie, moznost in args.items():

        if poradie != 'otázka':
            obsah += f':regional_indicator_{poradie[-1]}: {moznost}\n\n'
            pouzite_pismena.append(poradie[-1])

    embed.add_field(name=args['otázka'], value=obsah, inline=False)
    message = await ctx.send(embed=embed)

    for k in pouzite_pismena:
        await message.add_reaction(ABECEDA_REACTIONS[ABECEDA.index(k)])

    return


@slash.slash(name='role-color', description='Mení farbu role',
             options=[
                 discord_slash.manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
                 discord_slash.manage_commands.create_option(name='farba',  description='Nová farba role napr. #123abc', option_type=str, required=True)
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


bot.run(TOKEN)
