import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests
from io import BytesIO

def setup(client):
    client.add_cog(hatsuneCog(client))

class hatsuneCog(commands.Cog):
    def __init__(self, client):
        self.client = client 
        self.name = '[test-hatsune]'
    