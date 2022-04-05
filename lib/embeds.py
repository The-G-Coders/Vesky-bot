import discord as ds
from os import getenv as env
from dotenv import load_dotenv as ld
from discord.ext import commands as cmd


def from_hex(hex_str: str):
    return ds.Colour(int(f'0x{hex_str.removeprefix("#")}', 16))


class Embeds:

    def __init__(self, bot: cmd.Bot):
        ld()
        self.bot = bot
        self.get = env

    def error(self, title: str, desc: str = None):
        return self.default(title=title, desc=desc, color=Colors.ERROR)

    def default(self, desc: str = None, title: str = None, thumbnail: str = None, color: ds.Colour = None):
        eb = ds.Embed(color=Colors.MAIN if color is None else color)
        if desc is not None:
            eb.description = desc
        if title is not None:
            eb.title = title
        if thumbnail is not None:
            eb.set_thumbnail(url=thumbnail)
        guild: ds.Guild = self.bot.get_guild(int(self.get('DEBUG_GUILD_ID')))
        me: ds.Member = guild.me
        name = me.display_name if me is not None else self.bot.user
        eb.set_footer(text=name, icon_url=self.bot.user.avatar_url)
        return eb


class Colors:
    MAIN = from_hex('#e8e8e8')
    ERROR = from_hex('#c70000')

    RED = from_hex('#ff0000')
    BLUE = from_hex('#ff0000')
    GREEN = from_hex('#00ff08')
    WHITE = from_hex('#ffffff')
    BLACK = from_hex('#000000')


class CommandDescription:

    def __init__(self):
        self.commands = []

    def add_command(self, name: str, description: str):
        self.commands.append(f'[/{name}](https://help.demizon.me)  `{description}`\n')

    def add_break(self, text: str):
        self.commands.append(f'\n{text}\n\n')

    def to_string(self):
        string = ''
        for s in self.commands:
            string += s
        return string
