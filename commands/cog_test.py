import discord
from discord.ext import commands
import time

class testCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = client.log
        self.name = '[test]'
        #self.active = client.config.get('test',True)
    
    async def active_check(self, channel):
        if self.client.get_config('test') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True

    @commands.command(
        usage='.test [command]',
        help='Get the execution time of the said command.',
        hidden=True
    )
    async def test(self, ctx, message):
            channel = ctx.channel
            check = await self.active_check(channel)
            if not check:
                return
            if 'test' in  message.split(" "):
                return
            cmd = self.client.get_command(message.split()[0])
            if cmd == None:
                print('No command found')
                return

            st = time.perf_counter()
            await ctx.invoke(cmd)
            dt = round((time.perf_counter() - st)*1000)

            await channel.send('Command executed in {}ms'.format(dt))
            await self.logger.send(self.name, 'execution time:',dt,'ms')

def setup(client):
    client.add_cog(testCog(client))