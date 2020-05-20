# experimental cog that mainly serves as a playground for code stuff

import discord
from discord.ext import commands

class testCog(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.command(
        aliases=['cs']
    )
    async def command_set(self, ctx, command, state:int):
        channel = ctx.channel
        if not command in list(self.client.command_status.keys()):
            await channel.send('no such command found')
            return
        else:
            self.client.command_status[command] = state
            await channel.send(f"successfully set {command} to {state}")

def setup(client):
    client.add_cog(testCog(client))
