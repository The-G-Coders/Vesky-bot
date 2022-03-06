import discord
import discord_slash
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

slash = discord_slash.SlashCommand(bot, sync_commands=True) 

TOKEN='OTIxNzA1Nzc1NzMzMzAxMjQ4.Yb2zZQ.JWRV8UE8VWaSEXEV7PkRwzOeSqU'
ABECEDA='abcdefghijklmnoprstuvxyz'
ABECEDA_REACTIONS=['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰','🇱','🇲','🇳','🇴','🇵','🇷','🇸','🇹','🇺','🇻','🇽','🇾','🇿']
POLL_CHANEL_ID=933736111010897920


moznosti=[discord_slash.manage_commands.create_option(name='otázka',description='napíšte otázku' ,option_type=3, required=True)]
for i in ABECEDA:
    moznosti.append(
        discord_slash.manage_commands.create_option(name=f'možnosť_{i}',description=f'napíšte možnosť {i}', option_type=3, required=False)
    )

@bot.event
async def on_ready():
    print("Bot is online") 


@slash.slash(name='poll', description='vytvorí hlasovanie', options=moznosti)
async def poll(ctx: discord_slash.SlashContext, **moznosti):

    embed=discord.Embed(title='Hlasovanie', description='', url='', color=discord.Color.blue())
    embed.set_author(name=ctx.author.display_name, url='', icon_url=ctx.author.avatar_url)
    
    if len(moznosti) == 1:
        embed.add_field(name=moznosti['otázka'], value='-------', inline=False)
        message = await ctx.send(embed=embed)
        ano = discord.utils.get(ctx.guild.emojis, name='YES')
        nie = discord.utils.get(ctx.guild.emojis, name='NO')
        await message.add_reaction(ano)
        await message.add_reaction(nie)
        return
    pouzite_pismena=[]
    obsah=' \n'
    for poradie, moznost in moznosti.items():

        if poradie != 'otázka':
            obsah += f':regional_indicator_{poradie[-1]}: {moznost}\n\n'
            pouzite_pismena.append(poradie[-1])

    embed.add_field(name=moznosti['otázka'], value=obsah, inline=False)
    message = await ctx.send(embed=embed)

    for k in pouzite_pismena:
        await message.add_reaction(ABECEDA_REACTIONS[ABECEDA.index(k)])
    
    return


bot.run(TOKEN)