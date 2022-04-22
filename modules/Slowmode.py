import discord
from time import time
from datetime import datetime
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext, manage_commands
from lib.embeds import Embeds
from lib.model import SlowmodeType
from lib.database import Database


class Slowmode(commands.Cog):
    SECONDS = 'sekundy'
    MINUTES = 'minúty'
    HOURS = 'hodiny'

    def __init__(self, bot: commands.Bot, slash: SlashCommand, db: Database, embeds: Embeds):

        self.bot = bot
        self.db = db
        self.embeds = embeds
        self.last_messages = {}

        @slash.subcommand(
            base='slowmode',
            name='create',
            description="Pridá slowmode memberovi",
            options=[
                manage_commands.create_option(name='user', description='Vyber používateľa ktorému chceš nastaviť slowmode', option_type=6, required=True),
                manage_commands.create_option(name='duration_unit', description='Nastav jednotlu trvania', option_type=str, required=True, choices=[
                    self.SECONDS,
                    self.MINUTES,
                    self.HOURS
                ]),
                manage_commands.create_option(name='duration', description='Nastav trvanie slowmodu v hodinách', option_type=int, required=True),
                manage_commands.create_option(name='interval_unit', description='Nastav jednotku intervalu', option_type=str, required=True, choices=[
                    self.SECONDS,
                    self.MINUTES,
                    self.HOURS
                ]),
                manage_commands.create_option(name='interval', description='Nastav interval posielania správ v sekundách', option_type=int, required=True),
                manage_commands.create_option(name='reason', description='Nastav dôvod', option_type=str, required=False),
                manage_commands.create_option(name='channel', description='Nastav kanál (ak nie je nastavený kanál, slowmode je na celý server)', option_type=7, required=False)
            ])
        @commands.has_permissions(administrator=True)
        async def _slowmode_create(ctx: SlashContext, user: discord.User, duration_unit: str, duration: int, interval_unit: str, interval: int, reason: str = None, channel: discord.TextChannel = None):

            if user.guild_permissions.administrator:
                await ctx.reply(embed=embeds.error('Nemôžeš nastaviť slowmode administrátorovi'), hidden=True)
                return

            slowmode_user = db.slowmode_user(user)
            if slowmode_user is not None:
                await ctx.reply(embed=embeds.error(f'{user.name}#{user.discriminator} už má slowmode'), hidden=True)
                return

            new_duration = duration if duration_unit == self.SECONDS else duration * 60 if duration_unit == self.MINUTES else duration * 3600
            new_interval = interval if interval_unit == self.SECONDS else interval * 60 if interval_unit == self.MINUTES else interval * 3600

            if reason is not None:
                await user.send(embed=embeds.default(title='Dostal si slowmode', desc=f'**Dôvod:** {reason}\nPre viac detailov použi **/slowmode status**'))
            else:
                await user.send(embed=embeds.default(title='Dostal si slowmode', desc='Pre viac detailov použi **/slowmode status**'))

            slowmode: SlowmodeType = {
                'user_id': user.id,
                'duration': new_duration,
                'duration_unit': duration_unit,
                'interval': new_interval,
                'interval_unit': interval_unit,
                'reason': reason,
                'channel_id': channel.id if channel is not None else None,
                "issued_by": f'{ctx.author.mention}',
                'issued_at': time()
            }
            db.slowmode.insert_one(slowmode)

            await ctx.reply(embed=embeds.default(title=f'Slowmode pre {user.name}#{user.discriminator} bol nastavený'), hidden=True)

        @slash.subcommand(
            base='slowmode',
            name='remove',
            description='Odstráni slowmode memberovi',
            options=[
                manage_commands.create_option(name='user', description='Vyber používateľa ktorého chceš odstrániť', option_type=6, required=True)
            ])
        @commands.has_permissions(administrator=True)
        async def _slowmode_remove(ctx: SlashContext, user: discord.User):
            slowmode_user = db.slowmode_user(user)
            if slowmode_user is None:
                await ctx.reply(embed=embeds.error(f'Používateľ {user.name}#{user.discriminator} nemá nastavený slowmode'), hidden=True)
                return

            db.slowmode.delete_one({'user_id': user.id})
            if user.id in self.last_messages:
                del self.last_messages[user.id]
            await ctx.reply(embed=embeds.default(title=f'Slowmode pre {user.name}#{user.discriminator} bol odstránený'), hidden=True)

        @slash.subcommand(
            base='slowmode',
            name='status',
            description='Zobrazí status slowmodu pre membera',
            options=[
                manage_commands.create_option(name='user', description='Vyber membera ktorého chceš zobraziť', option_type=6, required=False)
            ])
        async def _slowmode_status(ctx: SlashContext, user: discord.User = None):
            temp_user = user if user is not None else ctx.author

            await self.check_slowmode(temp_user)

            slowmode_user = db.slowmode_user(temp_user)
            if ctx.author.guild_permissions.administrator:
                if slowmode_user is None:
                    if temp_user == ctx.author:
                        await ctx.reply(embed=embeds.default(title=f'Nemáš nastavený slowmode'), hidden=True)
                        return

                    await ctx.reply(embed=embeds.default(title=f'Používateľ {temp_user.name}#{temp_user.discriminator} nemá nastavený slowmode'), hidden=True)
                    return

                eb = embeds.default(title=f'Slowmode pre {temp_user.name}', desc='\n'.join(self.slowmode_to_list(db.slowmode.find_one({'user_id': temp_user.id}), ctx)))
                await ctx.reply(embed=eb, hidden=True)
            else:
                if temp_user != ctx.author:
                    await ctx.reply(embed=embeds.error('Pre zobrazenie statusu slowmodu niekoho iného musíš byť admin'), hidden=True)
                    return

                if slowmode_user is None:
                    await ctx.reply(embed=embeds.default(title=f'Nemáš nastavený slowmode'), hidden=True)
                    return

                eb = embeds.default(title=f'Slowmode pre {temp_user.name}', desc='\n'.join(self.slowmode_to_list(db.slowmode.find_one({'user_id': temp_user.id}), ctx)))
                eb.title = "Tvoj slowmode"
                await ctx.reply(embed=eb, hidden=True)

        @slash.subcommand(
            base='slowmode',
            name='list',
            description='Zobrazí všetkých používateľov s udeleným slowmode'
        )
        async def _slowmode_list(ctx: SlashContext):

            await check_slowmodes(ctx)

            data = db.all_slowmodes()
            eb = embeds.default(title='Slowmode list:')
            desc = ''
            for doc in data:
                user = discord.utils.get(ctx.guild.members, id=doc['user_id'])
                if user is not None:
                    if ctx.author.guild_permissions.administrator:
                        eb.add_field(name=f'{user.name}#{user.discriminator}', value='\n'.join(self.slowmode_to_list(doc, ctx)), inline=False)
                    else:
                        desc += f'**{user.name}#{user.discriminator}**\n'

            eb.description = '**Nie sú žiadni používatelia s udeleným slowmode!**' if len(data) == 0 else desc

            await ctx.reply(embed=eb, hidden=True)

        async def check_slowmodes(ctx: SlashContext):
            for doc in db.all_slowmodes():
                await self.check_slowmode(discord.utils.get(ctx.guild.members, id=doc['user_id']))

    async def check_slowmode(self, user: discord.User):
        slowmode_user = self.db.slowmode_user(user)
        if slowmode_user is not None:
            if slowmode_user['issued_at'] + slowmode_user['duration'] < time():
                await user.send(embed=self.embeds.default(title='Slowmode vypršal', desc='Môžeš znova písať bez obmedzení'))
                self.db.slowmode.delete_one({'user_id': user.id})
                return None

            return slowmode_user
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        slowmode_user = await self.check_slowmode(message.author)
        if slowmode_user is not None:
            interval = slowmode_user['interval']
            channel_id = slowmode_user['channel_id']
            last_message = self.get_last_message(message.author.id)

            if last_message is not None and interval - (time() - last_message) > 0:
                if channel_id is None or message.channel.id == channel_id:
                    await message.delete()
                    await message.author.send(embed=self.embeds.error(title='Nemôžeš posielať správy, pretože si dostal slowmode' if channel_id is None else 'Nemôžeš posielať správy v tomto kanáli, pretože si dostal slowmode', desc=f'Pre viac detailov použi **/slowmode status**\nĎalšiu správu môžeš poslať za **{int(interval - (time() - last_message))}** sekúnd'))
            else:
                if channel_id is None or message.channel.id == channel_id:
                    self.last_messages[message.author.id] = time()

    def get_last_message(self, user_id: int):
        local = self.last_messages.get(user_id)
        if local is not None:
            return local

        from_db = self.db.slowmode.find_one({'user_id': user_id}).get('last_message')
        self.last_messages[user_id] = from_db
        return from_db

    @tasks.loop(minutes=2)
    async def save_last_messages(self):
        for user_id, last_deleted_message in self.last_messages.items():
            self.db.slowmode.update_one({'user_id': user_id}, {'$set': {'last_message': last_deleted_message}})

    @save_last_messages.before_loop
    async def before_save_last_deleted_messages(self):
        await self.bot.wait_until_ready()

    # noinspection PyUnusedLocal
    @commands.Cog.listener()
    async def on_bot_shutdown(self, password_used: bool):
        await self.save_last_messages()

    @classmethod
    def time_from_seconds(cls, _time: int, unit: str):
        if unit == cls.SECONDS:
            return f'{int(_time)}  {cls.time_unit_to_acronym(unit, int(_time))}'
        if unit == cls.MINUTES:
            return f'{int(_time / 60)}  {cls.time_unit_to_acronym(unit, int(_time / 60))}'
        if unit == cls.HOURS:
            return f'{int(_time / 3600)}  {cls.time_unit_to_acronym(unit, int(_time / 3600))}'

    @classmethod
    def time_unit_to_acronym(cls, unit: str, value: int = None):
        if unit == cls.SECONDS:
            return cls.time_unit(value, ['sekunda', 'sekundy', 'sekúnd'])
        if unit == cls.MINUTES:
            return cls.time_unit(value, ['minúta', 'minúty', 'minút'])
        if unit == cls.HOURS:
            return cls.time_unit(value, ['hodina', 'hodiny', 'hodín'])

    @staticmethod
    def time_unit(value: int, unit_possibilities: list):
        if value is None or value > 4:
            return unit_possibilities[0]
        if value == 1:
            return unit_possibilities[1]
        if 1 < value < 5:
            return unit_possibilities[2]

    @classmethod
    def slowmode_to_list(cls, data, ctx: SlashContext):
        users_list = [f'**Interval:** {cls.time_from_seconds(data["interval"], data["interval_unit"])}', f'**Trvanie:** {cls.time_from_seconds(data["duration"], data["duration_unit"])}']
        if data["reason"] is not None:
            users_list.append(f'**Dôvod:** {data["reason"]}')
        if data["channel_id"] is not None:
            users_list.append(f'**Kanál:** #{discord.utils.get(ctx.guild.channels, id=data["channel_id"])}')
        else:
            users_list.append(f'**Kanál:** Celý server')
        if not ctx.author.guild_permissions.administrator:
            users_list.append(f'**Vyprší:** {datetime.fromtimestamp(data["issued_at"] + data["duration"]).strftime("%d.%m.%Y %H:%M:%S")}')

        if ctx.author.guild_permissions.administrator:
            users_list.append(f'**Udelený:** {datetime.fromtimestamp(data["issued_at"]).strftime("%d.%m.%Y %H:%M:%S")}')
            users_list.append(f'**Vyprší:** {datetime.fromtimestamp(data["issued_at"] + data["duration"]).strftime("%d.%m.%Y %H:%M:%S")}')
            users_list.append(f'**Udelil:** {data["issued_by"]}')

        return users_list
