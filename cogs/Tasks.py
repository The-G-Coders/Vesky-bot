from lib.yml import YmlConfig
from discord.ext import commands, tasks
from bot import events


class Tasks(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.events = YmlConfig('events')
        self.announce_event.start()

    def cog_unload(self):
        self.announce_event.cancel()

    @tasks.loop(minutes=5)
    async def announce_event(self):
        temp: dict = events.data.get('events')
        for name, data in temp.items():
            pass
            # TODO: add announcement

    @announce_event.before_loop
    async def before_announce_event(self):
        await self.bot.wait_until_ready()
