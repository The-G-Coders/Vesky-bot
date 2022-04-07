import discord
from pymongo import MongoClient
from os import getenv


class Database:

    def __init__(self):
        self.client = MongoClient(getenv("DATABASE_URL"))
        self.db = self.client[getenv("DATABASE_NAME")]
        self.events = self.db["events"]
        self.shutdowns = self.db["shutdowns"]
        self.slowmode = self.db["users_slowmode"]

    def all_events(self):
        return list(self.events.find({}))

    def all_shutdowns(self):
        return list(self.shutdowns.find({}))

    def all_slowmodes(self):
        return list(self.slowmode.find({}))

    def user_has_slowmode(self, user: discord.User):
        return self.slowmode.find_one({'user_id': user.id}) is not None

    def event_exists(self, name: str):
        return self.events.find_one({'name': name.strip().replace(' ', '_')}) is not None

