from time import time as tm
from lib.yml import YmlConfig
from discord.ext import commands, tasks



class Tasks(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.events = YmlConfig('resources/events.yml')
        self.announce_event.start()

    def cog_unload(self):
        self.announce_event.cancel()

    @tasks.loop(minutes=5)
    async def announce_event(self):
        temp: dict = self.events.get('events')
        for name, data in temp.items():
            if abs(data['time'] - data['time']%86400 - 86400 + 57600 - tm()) < 150:
                pass

    @announce_event.before_loop
    async def before_announce_event(self):
        await self.bot.wait_until_ready()
