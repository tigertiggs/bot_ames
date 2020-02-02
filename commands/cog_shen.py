import discord
from discord.ext import commands
import datetime, asyncio
from difflib import SequenceMatcher as sm

r1 = 613628290023948288
r2 = 613628508689793055
r3 = 639337169508630528

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
        
    def chunks(self, l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n] 

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
    
    @commands.command(
        usage='.big [emote]',
        aliases=['b', 'e', 'emote'],
        help='Enlarge the emote.'
    )
    async def big(self, ctx, emote:str=None):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check or emote == None:
            return
        
        # try extracting id
        emote1 = emote[1:-1].split(':')
        if emote1[0] == '' and len(emote1) > 1:
            link = f"https://cdn.discordapp.com/emojis/{emote1[-1]}.png"
        elif emote1[0] == 'a' and len(emote1) > 1:
            link = f"https://cdn.discordapp.com/emojis/{emote1[-1]}.gif"
        else:
            targets = list(filter(lambda x: not x.guild_id in [r1,r2,r3] and sm(None, emote.lower(), x.name.lower(), None).ratio() >= 0.4 and emote.lower() in x.name.lower(), self.client.emojis))
            if len(targets) > 0:
                emote = targets[0]
                if not emote.animated:
                    link = f"https://cdn.discordapp.com/emojis/{emote.id}.png"
                else:
                    link = f"https://cdn.discordapp.com/emojis/{emote.id}.gif"
            else:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
        author = ctx.message.author
        embed = discord.Embed()
        embed.set_author(name=f"{author.name} sent:",icon_url=author.avatar_url)
        print(link)
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
        check = await self.active_check(channel)
        if not check:
            return
        # filter out restricted emojis
        emotes = list(filter(lambda x: not x.guild_id in [r1,r2,r3], self.client.emojis))
        emotes.sort(key=lambda x: x.name[0])

        if option is None:
            emotes_per_column = 20
            embeds_emotes = list(self.chunks(emotes, 3*emotes_per_column))
            embeds = [self.make_find_embed(emote, (i+1,len(embeds_emotes))) for i, emote in enumerate(embeds_emotes)]

            finder = await channel.send(embed=embeds[0])
            for arrow in ['⬅','➡']:
                await finder.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and\
                    reaction.emoji in ['⬅','➡'] and\
                    str(reaction.message.id) == str(finder.id)

            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=90.0, check=author_check)
                except asyncio.TimeoutError:
                    for arrow in ['⬅','➡']:
                        await finder.remove_reaction(arrow, self.client.user)
                    break
                else:
                    if reaction.emoji == '⬅':
                        embeds = embeds[-1:] + embeds[:-1]
                        await reaction.message.remove_reaction('⬅', user)
                        await reaction.message.edit(embed=embeds[0])

                    elif reaction.emoji == '➡':
                        embeds = embeds[1:] + embeds[:1]
                        await reaction.message.remove_reaction('➡', user)
                        await reaction.message.edit(embed=embeds[0])

                    else:
                        continue
        else:
            cutoff = 0.25
            max = 20
            approx = list(filter(lambda x: sm(None, option.lower(), x.name.lower(), None).ratio() >= cutoff and option in x.name.lower(), emotes))[:max]

            embed = discord.Embed(description=f'Listing the top {max} results correspoinding to `{option}`',
                                    timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='Find Page | SHIN Ames',icon_url=self.client.user.avatar_url)
            embed.set_author(name="Emotefinder")
            if len(approx) > 0:
                embed.add_field(
                    name='Emote',
                    value="\n".join([f"<:{emote.name}:{emote.id}>" if not emote.animated else f"<a:{emote.name}:{emote.id}>" for emote in approx]),
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
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_footer(text='Find Page | SHIN Ames',icon_url=self.client.user.avatar_url)
        embed.set_author(name=f"Emotedex - Page {page[0]} of {page[1]}")

        for column in self.chunks(emotes, 20):
            embed.add_field(
                name='Emotes',
                value="\n".join([f"<:{emote.name}:{emote.id}> {emote.name}" if not emote.animated else f"<a:{emote.name}:{emote.id}> {emote.name}" for emote in column]),
                inline=True
            )
        
        return embed

    """
    @commands.command(
        usage=".emoji [emote]",
        aliases=['e'],
        help='Have Ames send an emote she has access to on your behalf.'
    )
    async def emoji(self, ctx, emote:str):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        
        targets = list(filter(lambda x: not x.guild_id in [r1,r2,r3] and sm(None, emote.lower(), x.name.lower(), None).ratio() >= 0.4 and emote.lower() in x.name.lower(), self.client.emojis))
        if len(targets) > 0:
            emote = targets[0]
            if not emote.animated:
                link = f"https://cdn.discordapp.com/emojis/{emote.id}.png"
            else:
                link = f"https://cdn.discordapp.com/emojis/{emote.id}.gif"

            author = ctx.message.author
            embed = discord.Embed()
            embed.set_author(name=f"{author.name} sent:",icon_url=author.avatar_url)
            embed.set_image(url=link)
            await ctx.message.delete()
            await channel.send(embed=embed)
        else:
            await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
    """

    @commands.command(
        usage=".[REDACTED]",
        help="YABAI"
    )
    async def cal(self,ctx):
        embed=discord.Embed()
        embed.set_image(url='https://cdn.discordapp.com/icons/419624511189811201/a_7a7c06c8c403d9886a9b1fd26981126e.gif')
        await ctx.message.delete()
        await ctx.channel.send(embed=embed)

def setup(client):
    client.add_cog(shenCog(client))