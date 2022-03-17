import discord
from discord.ext import commands


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
        eb.set_footer(text=f'{self.bot.user}', icon_url=self.bot.user.avatar_url)
        return eb


class Colors:
    MAIN = from_hex('#f123ff')
    ERROR = from_hex('#c70000')

    RED = from_hex('#ff0000')
    BLUE = from_hex('#ff0000')
    GREEN = from_hex('#00ff08')
    WHITE = from_hex('#ffffff')
    BLACK = from_hex('#000000')