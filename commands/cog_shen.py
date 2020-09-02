# this module takes care of all shitpost commands that does not require the PIL module
import discord
from discord.ext import commands
import datetime, asyncio, os
from difflib import SequenceMatcher as sm
import random

class shenCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = "[shen]"
        self.logger = client.log
        self.colour = discord.Colour.from_rgb(*self.client.config['command_colour']['cog_shen'])

    #@commands.command(usage=".[REDACTED]",help="YABAI")
    #async def cal(self,ctx):
    #    embed=discord.Embed()
    #    embed.set_image(url='https://cdn.discordapp.com/icons/419624511189811201/a_7a7c06c8c403d9886a9b1fd26981126e.gif')
    #    await ctx.message.delete()
    #    await ctx.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        channel = message.channel
        if not self.client.command_status['emote'] == 1:
            raise commands.DisabledCommand
            
        if message.content.startswith(self.client.prefix):
            msg_pp = message.content.strip("".join(self.client.prefix))
            guild_shen = {
                "actually":             "actually.gif",
                "objection":            "actually.gif",
                "somuchwinning":        "somuchwinning.png",
                "drum":                 "drum.png",
                "mem":                  "mem.png"
            }
            if msg_pp in list(self.client.emotes.keys()):
                await message.delete()
                await message.channel.send(self.client.emotes[msg_pp])
            elif guild_shen.get(msg_pp, None) and message.guild.id == 419624511189811201:
                await message.channel.send(file=discord.File(os.path.join(self.client.dir, self.client.config['shen_path'], "other", guild_shen.get(msg_pp, None))))

    @commands.command(
        usage='.big [arg:discord_emote_animated_okay]',
        aliases=['b', 'e', 'emote'],
        help='Enlarge the emote.'
    )
    async def big(self, ctx, emote:str="",num:int=1):
        channel = ctx.channel
        if not self.client.command_status['big'] == 1:
            raise commands.DisabledCommand
        elif not emote:
            return
        # try extracting id
        emote1 = emote[1:-1].split(':')
        if emote1[0] == '' and len(emote1) > 1:
            link = f"https://cdn.discordapp.com/emojis/{emote1[-1]}.png"
        elif emote1[0] == 'a' and len(emote1) > 1:
            link = f"https://cdn.discordapp.com/emojis/{emote1[-1]}.gif"
        else:
            targets = list(filter(lambda x: not x.guild_id in (self.client.private['resource_servers'] + self.client.private['bo_resource_servers']) and sm(None, emote.lower(), x.name.lower(), None).ratio() >= 0.25 and emote.lower() in x.name.lower(), self.client.emojis))
            if len(targets) > 0:
                targets.sort(key=lambda x: x.name)
                try:
                    emote = targets[num-1]
                except:
                    emote = targets[0]
                if not emote.animated:
                    link = f"https://cdn.discordapp.com/emojis/{emote.id}.png"
                else:
                    link = f"https://cdn.discordapp.com/emojis/{emote.id}.gif"
            else:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
        author = ctx.message.author
        embed = discord.Embed(colour=self.colour)
        embed.set_author(name=f"{author.name} sent:",icon_url=author.avatar_url)
        #print(link)
        embed.set_image(url=link)
        await ctx.message.delete()
        await channel.send(embed=embed)

    @commands.command(
        usage=".find [emote|optional]",
        aliases=['f'],
        help='List all emotes available to Ames or search for an emote.'
    )
    async def find(self, ctx, option:str=None):
        channel = ctx.channel
        author = ctx.message.author
        if not self.client.command_status['efinder'] == 1:
            raise commands.DisabledCommand
        # filter out restricted emojis
        emotes = list(filter(lambda x: not x.guild_id in (self.client.private["resource_servers"] + self.client.private['bo_resource_servers']), self.client.emojis))
        emotes.sort(key=lambda x: x.name)

        if option == None:
            emotes_per_column = 20
            find_controller = self.client.page_controller(self.client, self.make_find_embed, emotes, 3*emotes_per_column, True)

            finder = await channel.send(embed=find_controller.start())
            for arrow in find_controller.arrows:
                await finder.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and\
                    reaction.emoji in find_controller.arrows and\
                    str(reaction.message.id) == str(finder.id)

            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=90.0, check=author_check)
                except asyncio.TimeoutError:
                    for arrow in find_controller.arrows:
                        await finder.remove_reaction(arrow, self.client.user)
                    break
                else:
                    if reaction.emoji == find_controller.arrows[0]:
                        await reaction.message.edit(embed=find_controller.flip('l'))
                    elif reaction.emoji == find_controller.arrows[1]:
                        await reaction.message.edit(embed=find_controller.flip('r'))
                    else:
                        continue
                    await reaction.message.remove_reaction(reaction.emoji, user)
        else:
            cutoff = 0.25
            max = 20
            approx = list(filter(lambda x: sm(None, option.lower(), x.name.lower(), None).ratio() >= cutoff and option in x.name.lower(), emotes))[:max]
            embed = discord.Embed(description=f'Listing the top {max} results correspoinding to `{option}`',
                                    timestamp=datetime.datetime.utcnow(),colour=self.colour)
            embed.set_footer(text='Find Page | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
            embed.set_author(name="Emotefinder")
            if len(approx) > 0:
                #approx.sort(key=lambda x: x.name)
                embed.add_field(
                    name='Emote',
                    value="\n".join([f"<:{emote.name}:{emote.id}> [{str(i+1) if len(str(i+1)) == 2 else str(i+1)+' '}]" if not emote.animated else f"<a:{emote.name}:{emote.id}> [{str(i+1) if len(str(i+1)) == 2 else str(i+1)+' '}]" for i, emote in enumerate(approx)]),
                    inline=True
                )
                embed.add_field(
                    name="Name",
                    value="\n".join([emote.name for emote in approx]),
                    inline=True
                )
                embed.add_field(
                    name="Guild",
                    value="\n".join([self.client.get_guild(emote.guild_id).name for emote in approx]),
                    inline=True
                )
            else:
                embed.add_field(
                    name="Hmmm",
                    value="Nothing found",
                )
            await channel.send(embed=embed)
            
    def make_find_embed(self, emotes, page):
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), colour=self.colour)
        embed.set_footer(text='Find Page | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        embed.set_author(name=f"Emotedex - Page {page[0]} of {page[1]}")

        for column in self.client.chunks(emotes, 20):
            embed.add_field(
                name='Emotes',
                value="\n".join([f"<:{emote.name}:{emote.id}> {emote.name}" if not emote.animated else f"<a:{emote.name}:{emote.id}> {emote.name}" for emote in column]),
                inline=True
            )
        
        return embed

    @commands.command()
    async def bruh(self, ctx):
        channel=ctx.channel
        if not self.client.command_status['bruh'] == 1:
            raise commands.DisabledCommand
        
        await channel.send(file=discord.File(os.path.join(self.client.dir,self.client.config['shen_path'],"other/bruh.png")))

    @commands.command()
    async def broke(self, ctx, *num:int):
        channel=ctx.channel
        if ctx.message.guild.id != 419624511189811201:
            return
        else:
            available = [1,2]
            if not num:
                request = None
            else:
                request = num[0]
            
            if not request or not request in available:
                await channel.send(file=discord.File(os.path.join(self.client.dir,self.client.config['shen_path'],f"other/broke_{random.choice(available)}.png")))
            else:
                await channel.send(file=discord.File(os.path.join(self.client.dir,self.client.config['shen_path'],f"other/broke_{request}.png")))

def setup(client):
    client.add_cog(shenCog(client))