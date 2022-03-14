import discord
from time import time as tm
from lib.yml import YmlConfig
from discord.ext import commands, tasks


class Tasks(commands.Cog):
    interval = 60

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = YmlConfig('resources/config.yml')
        self.events = YmlConfig('resources/events.yml')
        self.channel: discord.TextChannel = bot.get_channel(self.config.get('channel-ids.announcements'))
        self.announce_event.start()

    def cog_unload(self):
        self.announce_event.cancel()

    @tasks.loop(seconds=interval)
    async def announce_event(self):
        temp: dict = self.events.get('events')
        _16_hours = 57600
        one_day = 86400
        interval_halved = self.interval / 2
        for name, data in temp.items():
            announce_time = data['time']
            if abs(announce_time - announce_time % one_day - one_day + _16_hours - tm()) < interval_halved:
                await self.channel.send(f"Zajtra bude event menom {name.replace('_', ' ')}")
                if announce_time % one_day == 10:
                    self.delete_event(name)

            elif announce_time % one_day != 10 and abs(announce_time - self.interval - tm()) < interval_halved:
                await self.channel.send(f"O chvilu bude event menom {name.replace('_', ' ')}")
                self.delete_event(name)

    def delete_event(self, name: str):
        temp_data = {
            'events': {}
        }
        for event_name, event in self.events.get('events').items():
            if event_name != name:
                temp_data['events'][event_name] = event
        self.events.save()

    @announce_event.before_loop
    async def before_announce_event(self):
        await self.bot.wait_until_ready()
