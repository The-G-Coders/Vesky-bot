import os
import discord
import discord_slash
from time import time
from dotenv import load_dotenv
from discord.ext import commands

startup = round(time() * 1000)
print('Starting up')

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
ABECEDA = os.getenv('ABECEDA')
ABECEDA_REACTIONS = os.getenv('ABECEDA_REACTIONS')

bot = commands.Bot(command_prefix='!')

slash = discord_slash.SlashCommand(bot, sync_commands=True)

moznosti = [discord_slash.manage_commands.create_option(name='otázka', description='napíšte otázku', option_type=3, required=True)]
for i in ABECEDA:
    moznosti.append(
        discord_slash.manage_commands.create_option(name=f'možnosť_{i}', description=f'napíšte možnosť {i}', option_type=3, required=False)
    )


@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    print(f'Started up in {round(time() * 1000) - startup} milliseconds')


@slash.slash(name='poll', description='vytvorí hlasovanie', options=moznosti)
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


@slash.slash(name='edit_role_color', description='mení farbu role',
             options=[
                 discord_slash.manage_commands.create_option(name='role', description='vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
                 discord_slash.manage_commands.create_option(name='farba',  description='nová farba role (treba zadať v 16 sústave a pred číslo napísať 0x)', option_type=4, required=True)
             ])
@commands.has_role('Moderator')
async def edit_role_color(ctx: discord_slash.SlashContext, role, farba):
    await role.edit(colour=discord.Colour(farba))
    await ctx.send(f'farba role {role} bola zmenená na {farba}')


@slash.slash(name='edit_role_name', description='mení farbu role',
             options=[
                 discord_slash.manage_commands.create_option(name='role', description='vyber rolu ktorú chceš zmeniť',
                                                             option_type=8, required=True),
                 discord_slash.manage_commands.create_option(name='nazov', description='nový názov role', option_type=3,
                                                             required=True),
             ]
             )
@commands.has_role('Moderator')
async def edit_role_name(ctx: discord_slash.SlashContext, role, nazov):
    povodny_nazov = role.name
    await role.edit(name=nazov)
    await ctx.send(f'názov role {povodny_nazov} bol zmenený na {role}')


bot.run(TOKEN)
