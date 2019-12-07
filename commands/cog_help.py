import discord
from discord.ext import commands
import datetime, time, os, sys, requests, random, ast
dir = os.path.dirname(__file__)

class helpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = client.log
        self.name = '[Help]'
        #self.active = client.config.get('help',True)
    
    async def active_check(self, channel):
        if self.client.get_config('help') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    @commands.command(
        usage='.help',
        help='Bring up this dialogue.'
    )
    async def help(self,ctx):
        channel=ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        functions = []
        #print(self.client.cogs)
        for cog in list(self.client.cogs.values()):
            for cmd in cog.get_commands():
                if not cmd.hidden and cmd.usage is not None:
                    if len(cmd.aliases) != 0:
                        txt = '{0}\nAliases: {1}\n{2}'.format(
                            cmd.usage, 
                            " ".join(cmd.aliases),
                            cmd.help
                        )
                    else:
                        txt = '{0}\n{1}'.format(
                            cmd.usage, 
                            cmd.help
                        )
                    functions.append(txt)
        functions.sort(key=lambda x: x[1])
        help_embed = '```css\n{}```'.format("\n\n".join(functions))
        embed = discord.Embed(
            title="Ames Help",
            timestamp=datetime.datetime.utcnow()
            )
        #embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="Help | SHIN Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Active Commands",
            value=help_embed
        )
        await channel.send(embed=embed)
                    
def setup(client):
    client.add_cog(helpCog(client))