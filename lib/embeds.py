import discord
from discord.ext import commands
from lib.yml import YmlConfig


def from_hex(hex_str: str):
    return discord.Colour(int(f'0x{hex_str.removeprefix("#")}', 16))


class Embeds:

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def error(self, error: str):
        embed = self.default(title=error, color=from_hex('#c70000'))
        return embed

    def default(self, desc: str = None, title: str = None, thumbnail: str = None, color: discord.Colour = None):
        eb = discord.Embed(color=Colors.MAIN if color is None else color)
        if desc is not None:
            eb.description = desc
        if title is not None:
            eb.title = title
        if thumbnail is not None:
            eb.set_thumbnail(url=thumbnail)
        guild: discord.Guild = self.bot.get_guild(YmlConfig('resources/config.yml').get('auth.debug-guild'))
        me: discord.Member = guild.me
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
