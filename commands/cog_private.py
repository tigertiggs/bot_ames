import discord
from discord.ext import commands
import datetime

class privateCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[private]'

    @commands.group()
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=f"Config",
                description=f"{self.client.emj['ames']}",
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text='Config | SHIN Ames',icon_url=self.client.user.avatar_url)

            # get load status and active
            cogs_status = self.client.get_cogs_status()
            cmds_status = self.client.get_full_config()
            order = list(cogs_status.keys())

            embed.add_field(
                name="Command Groups",
                value="\n".join([name.split('.')[-1] for name in order]),
                inline=True
            )
            embed.add_field(
                name="Cog",
                value="\n".join(['Loaded' if cogs_status[name] else 'Not Loaded' for name in order]),
                inline=True
            )
            embed.add_field(
                name="Active",
                value="\n".join(['True' if cmds_status.get(name.split('_')[-1],True) else 'False' for name in order])
            )
            await ctx.channel.send(embed=embed)
    
    def check_perm(self, user):
        return user.id == 235361069202145280
    
    @config.command()
    async def toggle(self, ctx, name):
        channel = ctx.channel
        if not self.check_perm(ctx.message.author):
            await channel.send(self.client.emj['amesyan'])
            return

        if not name in list(self.client.get_full_config().keys()):
            await channel.send(self.client.emj['ames'])
            return
        elif name == 'private':
            await channel.send(self.client.emj['ames'])
            return
        else:
            current = self.client.get_config(name)
            if self.client.update_config(name, not current):
                await channel.send(f"Successfully set {name} to {not current}")
            else:
                await channel.send(self.client.emj['sarens'])
    
    @config.command()
    async def ctoggle(self, ctx, name):
        channel = ctx.channel
        if not self.check_perm(ctx.message.author):
            await channel.send(self.client.emj['amesyan'])
            return
        
        if not f"commands.cog_{name}" in list(self.client.get_cogs_status().keys()):
            await channel.send(self.client.emj['ames'])
            return
        elif name == 'private':
            await channel.send(self.client.emj['ames'])
            return
        else:
            current = self.client.get_cogs_status()[f"commands.cog_{name}"]
            await self.client.update_cogs_status(name, not current)
    
    @config.command(
        aliases=['reload']
    )
    async def refresh(self, ctx, name):
        channel = ctx.channel
        if not self.check_perm(ctx.message.author):
            await channel.send(self.client.emj['amesyan'])
            return
        
        if not f"commands.cog_{name}" in list(self.client.get_cogs_status().keys()):
            await channel.send(self.client.emj['ames'])
            return
        elif name == 'private':
            await channel.send(self.client.emj['ames'])
            return
        else:
            await self.client.reload_cog(name)
        return

def setup(client):
    client.add_cog(privateCog(client))