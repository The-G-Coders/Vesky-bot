import discord
from os import getenv
from datetime import datetime
from time import strftime, localtime
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext, manage_commands
from lib.embeds import Embeds
from lib.model import Event
from lib.database import Database
from lib.regex import DATE_PATTERN, TIME_PATTERN, get_separator
from lib.utils import datetime_to_epoch, capitalize_first_letter, is_7210_secs, wrap_text, epoch, seconds_to_time


class EventCommands(commands.Cog):

    def __init__(self, slash: SlashCommand, db: Database, embeds: Embeds):

        @slash.subcommand(
            base='event',
            name='add',
            description='Pridá udalosť do kalendára',
            options=[
                manage_commands.create_option(name='name', description='Názov udalosti', option_type=3, required=True),
                manage_commands.create_option(name='description', description='Opis udalosti', option_type=3, required=True),
                manage_commands.create_option(name='date', description='Dátum udalosti', option_type=3, required=True),
                manage_commands.create_option(name='time', description='Čas udalosti(oznámi 5 minut pred zaciatkon)', option_type=3, required=False),
                manage_commands.create_option(name='ping', description='Vyber koho má pingnúť', option_type=8, required=False)
            ])
        async def _event_add(ctx: SlashContext, name: str, description: str, date: str, time: str = None, ping: discord.Role = None):
            if db.event_exists(name):
                used_names = ', '.join(event['name'] for event in db.all_events())
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

            event: Event = {
                'name': name.strip().replace(' ', '_'),
                'author_id': ctx.author.id,
                'description': capitalize_first_letter(description),
                'time': ping_time,
                'role': 'no-role' if ping is None else 'everyone' if ping.name == 'everyone' else ping.id,
                'utc_time': datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), 2, 0, 10).timestamp() if time is None else datetime(int(date_list[2]), int(date_list[1]), int(date_list[0]), int(time.strip().split(':')[0]), int(time.strip().split(':')[1]), 0).timestamp()
            }
            db.events.insert_one(event)

            await ctx.reply(embed=embeds.default(title='Udalosť bola úspešne pridaná!'), hidden=True)

        @slash.subcommand(
            base='event',
            name='remove',
            description='Vymaže udalosť z kalendára',
            options=[
                manage_commands.create_option(name='name', description='Názov udalosti', option_type=3, required=True)
            ])
        async def _event_remove(ctx: SlashContext, name: str):
            if not db.event_exists(name):
                await ctx.reply(embed=embeds.error('Event s takýmto menom neexistuje'), hidden=True)
                return

            if not ctx.author.guild_permissions.administrator and ctx.author.id != db.events.find_one({'name': name})['author_id']:
                await ctx.reply(embed=embeds.error('Nemáš práva na zmazanie tejto udalosti'), hidden=True)
                return

            db.events.delete_one({'name': name.strip().replace(' ', '_')})

            await ctx.reply(embed=embeds.default(title='Udalosť bola úspešne zmazaná!'), hidden=True)

        @slash.subcommand(
            base='event',
            name='list',
            description='Zobrazí naplánované udalosti'
        )
        async def _event_list(ctx: SlashContext):
            temp = db.all_events()
            embed = embeds.default(title='Kalendár')
            if len(temp) == 0:
                embed.description = "**Kalendár je prázdny...**"
                await ctx.reply(embed=embed, hidden=True)
                return
            for event in temp:
                desc = wrap_text(event['description'], 45)
                if is_7210_secs(event['time']):
                    value = desc + '\n**Dátum:** ' + strftime('%d.%m.%Y', localtime(event['utc_time']))
                else:
                    value = desc + '\n**Dátum:** ' + strftime('%H:%M:%S %d.%m.%Y', localtime(event['utc_time']))
                embed.add_field(name=event['name'].replace('_', ' '), value=value, inline=False)
            await ctx.reply(embed=embed, hidden=True)


class EventAnnouncementTask(commands.Cog):
    interval = 60

    def __init__(self, bot: commands.Bot, embeds: Embeds, db: Database):

        self.channel = None
        self.bot = bot
        self.embeds = embeds
        self.announce_event.start()
        self.db = db
        self.events_db = db.events

    def cog_unload(self):
        self.announce_event.cancel()

    @tasks.loop(seconds=interval)
    async def announce_event(self):
        events: list = list(self.events_db.find({}))
        _5_minutes = 300
        announcement_time = 57600  # 16h atm
        one_day = 86400
        interval_halved = self.interval / 2
        to_announce: dict = {}
        for event in events:
            announce_time = event['time']
            if announce_time - epoch() < -interval_halved:
                self.delete_event(event['name'])
                continue
            day_before_16_00 = announce_time - announce_time % one_day - one_day + announcement_time
            if abs(day_before_16_00 - epoch()) <= interval_halved:
                to_announce[event['name']] = event

            elif not is_7210_secs(announce_time) and abs(announce_time - _5_minutes - epoch()) <= interval_halved:
                desc = f'{event.get("description")} \n'
                desc += f'**Čas:** {seconds_to_time(event.get("time"))} \n'
                eb = self.embeds.default(title=f"O chvíľu začina event...")
                eb.add_field(name=event['name'].replace('_', ' '), value=desc, inline=False)
                role = event.get('role')
                ping = '@everyone' if role == 'everyone' else self.bot.get_guild(int(getenv("DEBUG_GUILD_ID"))).get_role(role).mention if role != 'no-role' else None
                if ping is not None:
                    await self.channel.send(ping)
                await self.channel.send(embed=eb)
                self.delete_event(event['name'])

            if is_7210_secs(announce_time) and abs(announce_time + one_day - epoch()) <= interval_halved:
                self.delete_event(event['name'])

        if len(to_announce) == 0:
            return
        eb = self.embeds.default(title="Oznam eventov na zajtra")
        for name, event in to_announce.items():
            desc = event.get('description') + '\n'
            value = event.get('role')
            role: discord.Role = self.bot.get_guild(int(getenv("DEBUG_GUILD_ID"))).get_role(value)
            if value == 'everyone':
                desc += '**Ping:** @everyone\n'
                await self.channel.send('@everyone')
            elif role is not None:
                desc += f'**Ping:** {role.mention}\n'
                await self.channel.send(role.mention)
            time = event.get('time')
            if not is_7210_secs(time):
                desc += f'**Čas:** {seconds_to_time(time)}'
            eb.add_field(name=name, value=desc, inline=False)
        await self.channel.send(embed=eb)

    def delete_event(self, name: str):
        self.events_db.delete_one({'name': name})

    @announce_event.before_loop
    async def before_announce_event(self):
        await self.bot.wait_until_ready()
        self.channel: discord.TextChannel = discord.utils.get(self.bot.get_guild(int(getenv("DEBUG_GUILD_ID"))).channels, id=int(getenv("ANNOUNCEMENTS_CHANNEL_ID")))
