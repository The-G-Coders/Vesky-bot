import re
import discord
import discord_slash
from os import getenv
from time import time as t
from discord import utils
from datetime import datetime
from pymongo import MongoClient
from discord.ext import commands
from time import strftime, localtime
from Tasks import EventAnnouncementTask
from discord_slash import SlashContext, manage_commands
from lib.embeds import Embeds, CommandDescription, from_hex
from lib.regex import DATE_PATTERN, TIME_PATTERN, get_separator
from lib.utils import init_env, datetime_to_epoch, capitalize_first_letter, wrap_text, is_7210_secs, intents, slowmode_to_list, epoch, sorted_event_list

startup = round(t() * 1000)
print('Starting up')

init_env()

bot = commands.Bot(command_prefix='!', intents=intents(), activity=discord.Activity(type=discord.ActivityType.listening, name="/help"), self_bot=True)

db = MongoClient(getenv('DATABASE_URL'))[getenv('DATABASE_NAME')]

events = db['events']
shutdowns = db['shutdowns']
users_slowmode = db['users_slowmode']

embeds = Embeds(bot)

TOKEN = getenv('TOKEN')
ALPHABET = 'abcdefghijklmnoprstuvyz'
ALPHABET_REACTIONS = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇷🇸🇹🇺🇻🇾🇿'
POLL_CHANNEL_ID = int(getenv('POLL_CHANNEL_ID'))
GUILD_ID = int(getenv('DEBUG_GUILD_ID'))
SHUTDOWN_PASSWORD = getenv("SHUTDOWN_PASSWORD")

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


@slash.slash(name='slowmode_create', description="Pridá slowmode memberovi", options=[manage_commands.create_option(name='user', description='Vyber používateľa ktorého chceš nastaviť rýchlosť', option_type=6, required=True),
                                                                                      manage_commands.create_option(name='duration', description='Nastav trvanie slowmodu v hodinách', option_type=int, required=True),
                                                                                      manage_commands.create_option(name='interval', description='Nastav interval posielania správ v sekundách', option_type=int, required=True),
                                                                                      manage_commands.create_option(name='reason', description='Nastav dôvod', option_type=str, required=False),
                                                                                      manage_commands.create_option(name='channel', description='Nastav kanál (ak nie je nastavený kanál, slowmode je na celý server)', option_type=7, required=False)
                                                                                      ])
@commands.has_permissions(administrator=True)
async def slowmode_create(ctx: SlashContext, user: discord.User, duration: int, interval: int, reason: str = None, channel: discord.TextChannel = None):
    if user_has_slowmode(user):
        await ctx.send(embed=embeds.error(f'{user.mention} už má slowmode'))
        return

    if reason is not None:
        await user.send(embed=embeds.default(title='Dostal si slowmode', desc=f'**Dôvod:** {reason}'))

    users_slowmode.insert_one({'user_id': user.id, 'duration': duration, 'interval': interval, 'reason': reason, 'channel_id': channel.id if channel is not None else None, "issued_by": f'{ctx.author.name}#{ctx.author.discriminator}', 'issued_at': epoch()})

    await ctx.reply(embed=embeds.default(title=f'Slowmode pre {user.name}#{user.discriminator} bol nastavený'), hidden=True)


@slash.slash(name='slowmode_remove', description='Odstráni slowmode memberovi', options=[manage_commands.create_option(name='user', description='Vyber používateľa ktorého chceš odstrániť', option_type=6, required=True)])
@commands.has_permissions(administrator=True)
async def slowmode_remove(ctx: SlashContext, user: discord.User):
    if not user_has_slowmode(user):
        await ctx.reply(embed=embeds.error(f'Užívateľ {user.name}#{user.discriminator} nemá nastavený slowmode'))
        return

    users_slowmode.delete_one({'user_id': user.id})
    await ctx.reply(embed=embeds.default(title=f'Slowmode pre {user.name}#{user.discriminator} bol odstránený'), hidden=True)


@slash.slash(name='slowmode_status', description='Zobrazí status slowmodu pre membera', options=[manage_commands.create_option(name='user', description='Vyber membera ktorého chceš zobraziť', option_type=6, required=False)])
async def slowmode_status(ctx: SlashContext, user: discord.User = None):
    temp_user = user if user is not None else ctx.author

    user_data = users_slowmode.find_one({'user_id': user.id})

    eb = embeds.default(title=f'Slowmode pre {user.name}', desc='\n'.join(slowmode_to_list(user_data, ctx)))
    if temp_user.guild_permissions.administrator:

        if not user_has_slowmode(temp_user):
            await ctx.reply(embed=embeds.error(f'Užívateľ {user.name} nemá nastavený slowmode'))
            return

        await ctx.reply(embed=eb, hidden=True)
    else:
        if temp_user != ctx.author:
            await ctx.reply(embed=embeds.error('Pre zobrazenie statusu slowmodu niekoho iného musíš byť admin'), hidden=True)
            return

        if not user_has_slowmode(temp_user):
            await ctx.reply(embed=embeds.error(f'Nemáš nastavený slowmode'))
            return

        eb.title = "Tvoj slowmode"
        await ctx.reply(embed=eb, hidden=True)


@slash.slash(name='slowmode_list', description='Zobrazí všetkých používateľov s nastaveným slowmode')
async def slowmode_list(ctx: SlashContext):
    data = list(users_slowmode.find({}))
    eb = embeds.default(title='Slowmode list')
    for doc in data:
        user = discord.utils.get(ctx.guild.members, id=doc['user_id'])
        if user is not None:
            if ctx.author.guild_permissions.administrator:
                eb.add_field(name=f'{user.name}#{user.discriminator}', value='\n'.join(slowmode_to_list(doc, ctx)), inline=False)
            else:
                eb.add_field(name=f'{user.name}#{user.discriminator}', value='', inline=False)

    await ctx.reply(embed=eb)


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
        used_names = ', '.join(event['name'] for event in events.find({}))
        await ctx.reply(embed=embeds.error('Event s takýmto menom uz existuje.\n', desc=f'**Použité mená:**\n{used_names}'), hidden=True)
        return

    date_stripped = date.strip()

    if not DATE_PATTERN.match(date_stripped):
        await ctx.reply(embed=embeds.error('Neplatný formát dátumu!'), hidden=True)
        return

    date_list = date_stripped.split(get_separator(date_stripped))

    if time is not None:

        time_stripped = time.strip()

        if not TIME_PATTERN.match(time_stripped):
            await ctx.reply(embed=embeds.error('Neplatný formát času!'), hidden=True)
            return

        time_list = time_stripped.split(':')

        ping_time = datetime_to_epoch(datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time_list[0]), int(time_list[1]), 0), int(time_list[0]),
                                      int(time_list[1]))
    else:
        ping_time = datetime_to_epoch(datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), 2, 0, 10), 2, 0, 10)

    events.insert_one(
        {
            'name': name.strip().replace(' ', '_'),
            'author_id': ctx.author.id,
            'description': capitalize_first_letter(description),
            'time': ping_time,
            'role': 'no-role' if ping is None else 'everyone' if ping.name == 'everyone' else ping.id,
            'utc-time': datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time_list[0]), int(time_list[1]), 0).timestamp() if time is not None else datetime(
                int(date_list[2]), int(date_list[1]), int(date_list[0]), 2, 0, 10).timestamp()
        })

    await ctx.reply(embed=embeds.default(title='Udalosť bola úspešne pridaná!'), hidden=True)


@slash.slash(name='show_events', description='Zobrazí naplánované udalosti')
async def show_events(ctx: SlashContext):
    temp = list(events.find({}))
    embed = embeds.default(title='Kalendár')
    if len(temp) == 0:
        embed.description = "**Kalendár je prázdny...**"
        await ctx.reply(embed=embed, hidden=True)
        return
    for event in sorted_event_list(temp, key='time'):
        desc = wrap_text(event['description'], 45)
        if is_7210_secs(event['time']):
            value = desc + '\n**Dátum:** ' + strftime('%d.%m.%Y', localtime(event['utc-time']))
        else:
            value = desc + '\n**Dátum:** ' + strftime('%H:%M:%S %d.%m.%Y', localtime(event['utc-time']))
        embed.add_field(name=event['name'].replace('_', ' '), value=value, inline=False)
    await ctx.send(embed=embed, hidden=True)


@slash.slash(name='delete-event', description='Zmaže udalosť z kalendára', options=[
    manage_commands.create_option(name='name', description='Názov udalosti', option_type=3, required=True)
])
async def delete_event(ctx: SlashContext, name: str):
    if not event_exists(name):
        await ctx.reply(embed=embeds.error('Event s takýmto menom neexistuje'), hidden=True)
        return

    if not ctx.author.guild_permissions.administrator and ctx.author.id != events.find_one({'name': name})['author_id']:
        await ctx.reply(embed=embeds.error('Nemáš práva na zmazanie tejto udalosti'), hidden=True)
        return

    events.delete_one({'name': name.strip().replace(' ', '_')})

    await ctx.reply(embed=embeds.default(title='Udalosť bola úspešne zmazaná!'), hidden=True)


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


# TODO: test slowmodes

@slash.slash(name='help', description='Vypíše všetky príkazy')
async def help(ctx: SlashContext):
    category_id = int(getenv('BOT_CATEGORY_ID'))
    if ctx.channel.category_id != category_id:
        await ctx.reply(embed=embeds.error(f"Tento command môžeš použiť len v {utils.get(bot.get_guild(GUILD_ID).categories, id=category_id).name} kategórii"), hidden=True)
        return
    desc = CommandDescription()
    desc.add_command('poll', 'Vytvorí hlasovanie')
    desc.add_command('new_event', 'Pridá udalosť do kalendára')
    desc.add_command('show_events', 'Zobrazí naplánované udalosti')
    desc.add_command("delete-event", "Zmaže udalosť z kalendára")
    desc.add_command('slowmode_list', 'Zobrazí všetkých memberov s slowmode')
    desc.add_break('> **:warning: Obmedzenie:** Funkcie vyhradené len pre ľudí s oprávnením')
    desc.add_command('clear', 'Vymaže správy v kanáli')
    desc.add_command('role-color', 'Zmení farbu role')
    desc.add_command('role-name', 'Zmení meno role')
    desc.add_command('slowmode_create', 'Pridá slowmode memberovi')
    desc.add_command('slowmode_remove', 'Odstráni slowmode memberovi')
    desc.add_command('slowmode_status', 'Zobrazí status slowmodu pre membera')
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
    await check_slowmode(message)

    author: discord.Member = message.author
    if message.content == SHUTDOWN_PASSWORD:
        if author.guild_permissions.administrator:
            await message.delete()
            await author.send('Bot bol uspesne vypnuty a jeho vypnutie zaznamenané!')
            await bot.change_presence(status=discord.Status.offline)
            shutdowns.insert_one({'user': author.name + '#' + author.discriminator, 'time': datetime.now().__format__('%d.%m.%Y %H:%M:%S')})
            await bot.close()
            exit(69)


async def check_slowmode(message: discord.Message):
    if not user_has_slowmode(message.author):
        return

    data = users_slowmode.find_one({'user_id': message.author.id})

    if data['issued_at'] + (data['duration'] * 3600) < t():
        users_slowmode.delete_one({'id': message.author.id})
        await message.author.send(embed=embeds.default(title='Slowmode vypršal', desc='Môžeš znova písať bez obmedzení'))
    else:
        await message.delete()
        await message.author.send(embed=embeds.error(title='Nemôžeš tu posielať správy, pretože si dostal slowmode', desc='Pre viac detailov použi **/slowmode_status**'))


def load_cogs():
    bot.add_cog(EventAnnouncementTask(bot))


def user_has_slowmode(user: discord.User):
    return users_slowmode.find_one({'user_id': user.id}) is not None


def event_exists(name: str):
    for event in events.find({}):
        if event['name'] == name.strip().replace(' ', '_'):
            return True
    return False


load_cogs()

bot.run(TOKEN)
