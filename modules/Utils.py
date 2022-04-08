from discord.ext import commands
from discord_slash import SlashCommand, SlashContext, manage_commands
from lib.embeds import Embeds, from_hex
from lib.regex import HEX_COLOR_PATTERN


class UtilCommands(commands.Cog):

    def __init__(self, slash: SlashCommand, embeds: Embeds):

        @slash.subcommand(
            base='role',
            name='color',
            description='Zmení farbu role',
            options=[
                manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
                manage_commands.create_option(name='farba', description='Nová farba role napr. #123abc', option_type=str, required=True)
            ])
        @commands.has_permissions(administrator=True)
        async def _role_color(ctx: SlashContext, role, farba: str):
            if not HEX_COLOR_PATTERN.match(farba):
                await ctx.reply(embed=embeds.error('Farba musí byť vo formáte #1a2b3c'), hidden=True)
                return
            color = from_hex(farba.removeprefix("#"))
            await role.edit(colour=color)
            await ctx.reply(embeds.default(f'Farba role {role} bola zmenená na {color}'), hidden=True)

        @slash.subcommand(
            base='role',
            name='name',
            description='Zmení meno role',
            options=[
                manage_commands.create_option(name='role', description='Vyber rolu ktorú chceš zmeniť', option_type=8, required=True),
                manage_commands.create_option(name='nazov', description='Nový názov role', option_type=3, required=True),
            ])
        @commands.has_permissions(administrator=True)
        async def _role_name(ctx: SlashContext, role, nazov):
            previous_role_name = role.name
            await role.edit(name=nazov)
            await ctx.reply(embed=embeds.default(f'Názov role {previous_role_name} bol zmenený na {role.name}'), hidden=True)

        @slash.slash(
            name='clear',
            description="Vymaže správy v kanáli",
            options=[
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
