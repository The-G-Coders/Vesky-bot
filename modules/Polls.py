import discord
from os import getenv
from discord import utils
from datetime import datetime
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext, manage_commands
from lib.embeds import Embeds


class PollCommands(commands.Cog):
    ALPHABET = 'abcdefghijklmnoprstuvyz'
    ALPHABET_REACTIONS = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇷🇸🇹🇺🇻🇾🇿'
    POLL_CHANNEL_ID = int(getenv('POLL_CHANNEL_ID'))

    def __init__(self, bot: commands.Bot, slash: SlashCommand, embeds: Embeds):

        poll_options = [manage_commands.create_option(name='otázka', description='Napíšte otázku', option_type=3, required=True),
                        manage_commands.create_option(name='ping', description='Pingne rolu', option_type=8, required=False)]
        for i in self.ALPHABET:
            poll_options.append(
                manage_commands.create_option(name=f'možnosť_{i}', description=f'Napíšte možnosť {i}', option_type=3, required=False)
            )

        @slash.slash(
            name='poll',
            description='Vytvorí hlasovanie',
            options=poll_options
        )
        async def poll(ctx: SlashContext, **kwargs):
            embed = embeds.default(title='Hlasovanie', thumbnail='https://clipart.info/images/ccovers/1484942349ios-emoji-white-question-mark-ornament.png')
            embed.set_footer(text=f'{ctx.author.name}#{ctx.author.discriminator} {datetime.now().__format__("%d.%m.%Y %H:%M:%S")}', icon_url=ctx.author.avatar_url)
            description = ''
            role: discord.Role = kwargs.get('ping')

            channel = bot.get_channel(self.POLL_CHANNEL_ID)

            if channel is None:
                await ctx.reply("Invalid channel", hidden=True)
                return

            if role is None and len(kwargs) < 2 or role is not None and len(kwargs) < 3:
                description += f'**{kwargs["otázka"]}**'
                embed.description = description
                if role is not None:
                    await channel.send(kwargs['ping'].mention())
                message = await channel.send(embed=embed)
                await message.add_reaction(utils.get(ctx.guild.emojis, name='YES'))
                await message.add_reaction(utils.get(ctx.guild.emojis, name='NO'))
                await ctx.reply(embed=embeds.default(title='Anketa úspešne vytvorená!'), hidden=True)
                return
            used_letters = []
            description += f'**{kwargs["otázka"]}**\n\n'
            for key, value in kwargs.items():

                if key != 'otázka' and key != 'ping':
                    description += f':regional_indicator_{key[-1]}: {value}\n\n'
                    used_letters.append(key[-1])
                elif key == 'ping':
                    await channel.send(f'<@&{value.id}>')

            embed.description = description
            message = await channel.send(embed=embed)

            for k in used_letters:
                await message.add_reaction(self.ALPHABET_REACTIONS[self.ALPHABET.index(k)])

            await ctx.reply(embed=embeds.default(title='Anketa úspešne vytvorená!'), hidden=True)
