import re
import discord
import discord_slash
from discord import utils
from discord.ext import commands
from time import strftime, localtime
from discord_slash import SlashContext, manage_commands
from Tasks import Tasks
from lib.utils import *
from lib.embeds import *
from lib.yml import YmlConfig
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

slash = discord_slash.SlashCommand(bot, sync_commands=True, debug_guild=GUILD_ID)

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
    embed = embeds.default(title='Hlasovanie', thumbnail='https://clipart.info/images/ccovers/1484942349ios-emoji-white-question-mark-ornament.png')
    embed.set_author(name=ctx.author.display_name, url='', icon_url=ctx.author.avatar_url)
    description = ''
    role: discord.Role = kwargs.get('ping')

    channel = bot.get_channel(int(POLL_CHANNEL_ID))

    if channel is None:
        await ctx.reply("Invalid channel", hidden=True)
        return

    if role is None and len(kwargs) < 2 or role is not None and len(kwargs) < 3:
        description += f'> **{kwargs["otázka"]}**'
        embed.description = description
        if role is not None:
            await channel.send(kwargs['ping'].mention())
        message = await channel.send(embed=embed)
        await message.add_reaction(utils.get(ctx.guild.emojis, name='YES'))
        await message.add_reaction(utils.get(ctx.guild.emojis, name='NO'))
        await ctx.reply(embed=embeds.default(title='Anketa úspešne vytvorená!'), hidden=True)
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


@slash.slash(name='role-color', description='Zmení farbu role', options=[
    manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
    manage_commands.create_option(name='farba', description='Nová farba role napr. #123abc', option_type=str, required=True)
])
@commands.has_permissions(administrator=True)
async def role_color(ctx: SlashContext, role, farba: str):
    if not re.match('(#[0-9a-fA-F]{6})', farba):
        await ctx.reply(embed=embeds.error('Farba musí byť vo formáte #1a2b3c'), hidden=True)
        return
    color = from_hex(farba.removeprefix("#"))
    await role.edit(colour=color)
    await ctx.send(f'Farba role {role} bola zmenená na {color}')


@slash.slash(name='role-name', description='Zmení meno role', options=[
    manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
    manage_commands.create_option(name='nazov', description='Nový názov role', option_type=3, required=True),
])
@commands.has_permissions(administrator=True)
async def role_name(ctx: SlashContext, role, nazov):
    previous_role_name = role.name
    await role.edit(name=nazov)
    await ctx.send(f'Názov role {previous_role_name} bol zmenený na {role}')


@slash.slash(name='new_event', description='Pridá udalosť do kalendára', options=[
    manage_commands.create_option(name='name', description='Názov udalosti', option_type=3, required=True),
    manage_commands.create_option(name='description', description='Opis udalosti', option_type=3, required=True),
    manage_commands.create_option(name='date', description='Dátum udalosti', option_type=3, required=True),
    manage_commands.create_option(name='time', description='Čas udalosti(oznámi 5 minut pred zaciatkon)', option_type=3, required=False),
    manage_commands.create_option(name='ping', description='Vyber koho má pingnúť', option_type=8, required=False)
])
async def new_event(ctx: SlashContext, name: str, description: str, date: str, time: str = None, ping: discord.Role = None):
    if event_exists(name):
        used_names = ', '.join(used_name for used_name in events.get('events').keys())
        await ctx.reply(embed=embeds.error('Event s takýmto menom uz existuje\n'
                                           'použité mená:\n'
                                           f'{used_names}'), hidden=True)
        return

    date_stripped = date.strip()

    if not DATE_PATTERN.match(date_stripped):
        await ctx.reply(embed=embeds.error('Neplatný formát dátumu!'), hidden=True)
        return
    date_list = date_stripped.split(get_separator(date_stripped))

    time_list = []

    if time is not None:

        time_stripped = time.strip()

        if not TIME_PATTERN.match(time_stripped):
            await ctx.reply(embed=embeds.error('Neplatný formát času!'), hidden=True)
            return

        time_list = time_stripped.split(':')

        ping_time = datetime_to_epoch(datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time_list[0]), int(time_list[1]), 0),
                                      int(time_list[0]), int(time_list[1]))
    else:
        ping_time = datetime_to_epoch(datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), 2, 0, 10),
                                      2, 0, 10)

    events.data['events'][name.strip().replace(' ', '_')] = {
        'description': description,
        'time': ping_time,
        'role': 'no-role' if ping is None else 'everyone' if ping.name == 'everyone' else ping.id,
        'utc-time': datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time_list[0]), int(time_list[1]), 0).timestamp() if time is not None else datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), 2, 0, 10).timestamp()
    }

    events.save()

    await ctx.reply(embed=embeds.default(title='Udalosť bola úspešne pridaná!'), hidden=True)


@slash.slash(name='show_events', description='Zobrazí naplánované udalosti')
async def show_events(ctx: SlashContext):
    temp: dict = events.get('events')
    embed = embeds.default(title='Kalendár')
    if len(temp) == 0:
        embed.description = "**Kalendár je prázdny...**"
        await ctx.reply(embed=embed, hidden=True)
        return
    for name, data in sorted_event_dict(temp, key='time'):
        desc = wrap_text(data['description'], 45)
        if is_7210_secs(data['time']):
            value = desc + '\n**Dátum:** ' + strftime('%d.%m.%Y', localtime(data['utc-time']))
        else:
            value = desc + '\n**Dátum:** ' + strftime('%H:%M:%S %d.%m.%Y', localtime(data['utc-time']))
        embed.add_field(name=capitalize_first_letter(name.replace('_', ' ')), value=capitalize_first_letter(value), inline=False)
    await ctx.send(embed=embed, hidden=True)


@slash.slash(name='clear', description="Vymaže správy v kanáli", options=[
    manage_commands.create_option(name='count', description='Počet správ ktoré budú vymazané', option_type=4, required=True)
])
@commands.has_permissions(manage_messages=True)
async def clear(ctx: SlashContext, count: int):
    await ctx.defer(hidden=True)
    if count > 100:
        await ctx.reply(embed=embeds.error('Môžeš vymazať najviac 100 správ naraz'), hidden=True)
        return
    else:
        await ctx.channel.purge(limit=count)

    await ctx.reply(embed=embeds.default(title='Správy úspešne vymazané'), hidden=True)


@slash.slash(name='help', description='Vypíše všetky príkazy')
async def help(ctx: SlashContext):
    category_id = config.get('category-ids.bot')
    if ctx.channel.category_id != category_id:
        await ctx.reply(embed=embeds.error(f"Tento command môžeš použiť len v {utils.get(bot.get_guild(GUILD_ID).categories, id=category_id).name} kategórii"), hidden=True)
        return
    desc = CommandDescription()
    desc.add_command('poll', 'Vytvorí hlasovanie')
    desc.add_command('new_event', 'Pridá udalosť do kalendára')
    desc.add_command('show_events', 'Zobrazí naplánované udalosti')
    desc.add_break('> **:warning: Obmedzenie:** Funkcie vyhradené len pre ľudí s oprávnením')
    desc.add_command('clear', 'Vymaže správy v kanáli')
    desc.add_command('role-color', 'Zmení farbu role')
    desc.add_command('role-name', 'Zmení meno role')
    eb = embeds.default(title="Zoznam príkazov", desc=desc.to_string())
    await ctx.reply(embed=eb, hidden=False)


@bot.event
async def on_slash_command_error(ctx: SlashContext, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=embeds.error('Na použitie tohto príkazu nemáš oprávnenie'), hidden=True)
        return
    raise error


@bot.event
async def on_message(message: discord.Message):
    author: discord.Member = message.author
    if message.content == config.get('auth.shutdown-password'):
        if author.guild_permissions.administrator:
            await message.delete()
            await author.send('Bot bol uspesne vypnuty a jeho vypnutie zaznamenané!')
            with open('resources/shutdown.log', 'w') as file:
                file.write(f"Bot turned off by {author} at {epoch()} timezone epoch!\n")
            await bot.close()
            exit(69)


def load_cogs():
    bot.add_cog(Tasks(bot))


def event_exists(name: str):
    for key in events.get("events"):
        if key == name.strip().replace(' ', '_'):
            return True
    return False


load_cogs()

bot.run(TOKEN)
