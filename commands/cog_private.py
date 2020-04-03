import discord
from discord.ext import commands
import datetime
from difflib import SequenceMatcher as sm

r1 = 613628290023948288
r2 = 613628508689793055
r3 = 639337169508630528

class privateCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[private]'

    async def find_user(self, guild, user:str):
        members = guild.members

        # check if user is a discord id
        try:
            user = user.replace('>', '').replace('<','').replace('@','').replace('!','')
            #print(user)
            user = guild.get_member(int(user))
        except Exception as e:
            await self.logger.send(self.name, 'dumb id mismatch', e)
            pass
        else:
            return user
        
        # do string match
        # search name
        cutoff = 0.3
        user = user.lower()
        fname = list(filter(lambda x: sm(None, user, x.name.lower(), None).ratio() >= cutoff and user in x.name.lower(), members))
        fnick = list(filter(lambda x: sm(None, user, x.nick.lower() if x.nick != None else '', None).ratio() >= cutoff and user in x.nick.lower(), members))
        #print(user, fname, fnick)
        if len(fname) != 0 and len(fnick) != 0:
            #print(fname[0].name, fnick[0].nick)
            a = sm(None, user, fname[0].name, None).ratio()
            b = sm(None, user, fnick[0].nick, None).ratio()
            if a == b:
                return fnick[0]
            elif a > b:
                return fname[0]
            else:
                return fnick[0]
        elif len(fname) != 0:
            #print(fname[0].name)
            return fname[0]
        elif len(fnick) != 0:
            #print(fnick[0].nick)
            return fnick[0]
        else:
            return None

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

    @commands.command(
        hidden=True
    )
    async def say(self, ctx, *message):
        if str(ctx.author.id) != '235361069202145280' or len(message) == 0:
            await ctx.channel.send(self.client.emj['ames'])
            return
        else:
            await ctx.message.delete()
        
        code = message[-1]

        if code[0] != '#':
            guild_id = ctx.message.channel.guild.id
            channel_id = ctx.message.channel.id
        else:
            message = message[:-1]
            guild_id, channel_id = code[1:].split('.')
            #guild_id, channel_id = int(guild_id), int(channel_id)

        guild_id = 419624511189811201
        guild = discord.utils.get(self.client.guilds, id=int(guild_id) if guild_id != '' else ctx.message.channel.guild.id)
        if guild == None:
            await self.client.log.send('failed to find guild')
        channel = discord.utils.get(guild.channels, id=int(channel_id) if channel_id != '' else ctx.message.channel.id)
        if channel == None:
            await self.client.log.send('failed to find guild')

        temp = []
        for section in message:
            if section[0] == ':':
                emote = section.strip(':')
                emote = list(filter(lambda x: not x.guild_id in [r1,r2,r3] and sm(None, emote.lower(), x.name.lower(), None).ratio() >= 0.4 and emote.lower() in x.name.lower(), self.client.emojis))
                if len(emote) > 0:
                    emote = emote[0]
                    if emote.animated:
                        temp.append(f"<a:{emote.name}:{emote.id}>")
                    else:
                        temp.append(f"<:{emote.name}:{emote.id}>")
                else:
                    temp.append(section)

            elif section[0] == '@':
                user = self.find_user(guild, section.strip('@'))
                if user != None:
                    temp.append(f"<@{user.id}>")
                else:
                    temp.append(section)

            else:
                temp.append(section)
        
        await channel.send(' '.join(temp))


def setup(client):
    client.add_cog(privateCog(client))