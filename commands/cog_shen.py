import discord
from discord.ext import commands
import datetime

class shenCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[Shen]'
        self.logger = client.log
        
    async def active_check(self, channel):
        if self.client.get_config('shen') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel = message.channel
        check = await self.active_check(channel)
        if not check:
            return
        if message.content.startswith(self.client.BOT_PREFIX):
            msg_pp = message.content.strip("".join(self.client.BOT_PREFIX))
            if msg_pp in list(self.client.emj.keys()):
                await message.delete()
                await message.channel.send(self.client.emj[message.content.strip("".join(self.client.BOT_PREFIX))])

def setup(client):
    client.add_cog(shenCog(client))