import discord
from discord.ext import commands, tasks
from lib.utils import epoch
from lib.yml import YmlConfig


class Tasks(commands.Cog):
    interval = 60

    def __init__(self, bot: commands.Bot):
        self.channel = None
        self.bot = bot
        self.config = YmlConfig('resources/config.yml')
        self.events = YmlConfig('resources/events.yml')
        self.announce_event.start()

    def cog_unload(self):
        self.announce_event.cancel()

    @tasks.loop(seconds=interval)
    async def announce_event(self):
        self.events = YmlConfig('resources/events.yml')
        temp: dict = self.events.get('events')
        _5_minutes = 300
        _16_hours = 57900
        one_day = 86400
        interval_halved = self.interval / 2
        # print(f'Current time {epoch()}')
        for name, data in temp.items():
            announce_time = data['time']
            if announce_time - epoch() < -interval_halved:
                self.delete_event(name)
                continue
            day_before_16_00 = announce_time - announce_time % one_day - one_day + _16_hours
            # print(f'{name} day before', epoch() - day_before_16_00)
            if abs(day_before_16_00 - epoch()) <= interval_halved:
                await self.channel.send(f"Zajtra bude event menom {name.replace('_', ' ')}")
                if announce_time % one_day == 10:
                    self.delete_event(name)

            elif announce_time % one_day != 10 and abs(announce_time - _5_minutes - epoch()) <= interval_halved:
                await self.channel.send(f"O chvilu bude event menom {name.replace('_', ' ')}")
                self.delete_event(name)

    def delete_event(self, name: str):
        temp_data = {
            'events': {}
        }
        for event_name, event in self.events.get('events').items():
            if event_name != name:
                temp_data['events'][event_name] = event
        self.events.overwrite(temp_data)

    @announce_event.before_loop
    async def before_announce_event(self):
        await self.bot.wait_until_ready()
        self.channel: discord.TextChannel = discord.utils.get(self.bot.get_guild(self.config.get('auth.debug-guild')).channels, id=self.config.get('channel-ids.announcements'))
