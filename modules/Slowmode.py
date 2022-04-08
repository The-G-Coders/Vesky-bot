import discord
from time import time
from datetime import datetime
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext, manage_commands
from lib.model import Database
from lib.embeds import Embeds


class Slowmode(commands.Cog):

    def __init__(self, bot: commands.Bot, slash: SlashCommand, db: Database, embeds: Embeds):

        self.bot = bot
        self.db = db
        self.embeds = embeds
        self.last_messages = self.fetch_last_messages()

        @slash.subcommand(
            base='slowmode',
            name='create',
            description="Pridá slowmode memberovi",
            options=[
                manage_commands.create_option(name='user', description='Vyber používateľa ktorého chceš nastaviť rýchlosť', option_type=6, required=True),
                manage_commands.create_option(name='duration-unit', description='Nastav jednotlu trvania', option_type=str, required=True, choices=[
                    'sekundy',
                    'minúty',
                    'hodiny'
                ]),
                manage_commands.create_option(name='duration', description='Nastav trvanie slowmodu v hodinách', option_type=int, required=True),
                manage_commands.create_option(name='interval-unit', description='Nastav jednotku intervalu', option_type=str, required=True, choices=[
                    'sekundy',
                    'minúty',
                    'hodiny'
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

            if db.user_has_slowmode(user):
                await ctx.reply(embed=embeds.error(f'{user.mention} už má slowmode'), hidden=True)
                return

            new_duration = duration if duration_unit == 'sekundy' else duration * 60 if duration_unit == 'minúty' else duration * 3600
            new_interval = interval if interval_unit == 'sekundy' else interval * 60 if interval_unit == 'minúty' else interval * 3600

            if reason is not None:
                await user.send(embed=embeds.default(title='Dostal si slowmode', desc=f'**Dôvod:** {reason}\nPre viac detailov použi **/slowmode status**'))

            db.slowmode.insert_one({'user_id': user.id, 'duration': new_duration, 'interval': new_interval, 'reason': reason, 'channel_id': channel.id if channel is not None else None, "issued_by": f'{ctx.author.mention}', 'issued_at': time()})

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
            if not db.user_has_slowmode(user):
                await ctx.reply(embed=embeds.error(f'Používateľ {user.name}#{user.discriminator} nemá nastavený slowmode'), hidden=True)
                return

            db.slowmode.delete_one({'user_id': user.id})
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

            if ctx.author.guild_permissions.administrator:
                if not db.user_has_slowmode(temp_user):
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

                if not db.user_has_slowmode(temp_user):
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

            eb.description = '**Nie sú žiadni používatelia s udeleným slowmode!**' if len(data) == 0 else desc if desc != '' else None

            await ctx.reply(embed=eb, hidden=True)

        async def check_slowmodes(ctx: SlashContext):
            for doc in db.all_slowmodes():
                await self.check_slowmode(discord.utils.get(ctx.guild.members, id=doc['user_id']))

    async def check_slowmode(self, user: discord.User):
        if self.db.user_has_slowmode(user):
            data = self.db.slowmode.find_one({'user_id': user.id})

            if data['issued_at'] + data['duration'] < time():
                await user.send(embed=self.embeds.default(title='Slowmode vypršal', desc='Môžeš znova písať bez obmedzení'))
                self.db.slowmode.delete_one({'user_id': user.id})
                return False
            else:
                return True
        else:
            return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if await self.check_slowmode(message.author):
            user = self.db.slowmode.find_one({'user_id': message.author.id})
            interval = user['interval']
            channel_id = user['channel_id']
            last_message = self.get_last_message(message.author.id)

            if last_message is not None and last_message + interval > time():
                if channel_id is None or message.channel.id == channel_id:
                    await message.delete()
                    await message.author.send(embed=self.embeds.error(title='Nemôžeš posielať správy, pretože si dostal slowmode' if channel_id is None else 'Nemôžeš posielať správy v tomto kanáli, pretože si dostal slowmode', desc='Pre viac detailov použi **/slowmode status**'))
            else:
                if channel_id is None or message.channel.id == channel_id:
                    self.last_messages[message.author.id] = time()

    def fetch_last_messages(self):
        temp = {}
        for doc in self.db.all_slowmodes():
            temp[doc['user_id']] = doc.get('last_message')
        return temp

    def get_last_message(self, user_id: int):
        local = self.last_messages.get(user_id)
        if local is not None:
            return local
        else:
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

    @staticmethod
    def slowmode_to_list(data, ctx: SlashContext):
        users_list = [f'**Interval:** {data["interval"]} sekúnd', f'**Trvanie:** {data["duration"]} hodín']
        users_list.append(f'**Dôvod:** {data["reason"]}') if data["reason"] is not None else None
        users_list.append(f'**Kanál:** #{discord.utils.get(ctx.guild.channels, id=data["channel_id"])}') if data["channel_id"] is not None else users_list.append(f'**Kanál:** Celý server')
        users_list.append(f'**Vyprší:** {datetime.fromtimestamp(data["issued_at"] + (data["duration"] * 3600)).strftime("%d.%m.%Y %H:%M:%S")}')

        if ctx.author.guild_permissions.administrator:
            users_list.append(f'**Dátum udelenia:** {datetime.fromtimestamp(data["issued_at"]).strftime("%d.%m.%Y %H:%M:%S")}')
            users_list.append(f'**Udelil:** {data["issued_by"]}')

        return users_list
