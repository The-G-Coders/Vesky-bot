import discord
from os import getenv
from dotenv import load_dotenv
from pymongo import MongoClient
from discord.ext import commands, tasks
from lib.embeds import Embeds
from lib.utils import epoch, is_7210_secs, seconds_to_time


class EventAnnouncementTask(commands.Cog):
    interval = 60

    def __init__(self, bot: commands.Bot):
        load_dotenv()
        self.channel = None
        self.bot = bot
        self.embeds = Embeds(bot)
        self.announce_event.start()
        self.events_db = MongoClient(getenv("DATABASE_URL"))[getenv('DATABASE_NAME')]["events"]

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
                if is_7210_secs(announce_time):
                    self.delete_event(event['name'])

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
