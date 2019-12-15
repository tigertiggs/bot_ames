import discord
from discord.ext import commands
import datetime, glob, os, asyncio
from PIL import Image
dir = os.path.dirname(__file__)

class resCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = client.log
        self.name = '[res]'

    async def active_check(self, channel):
        if self.client.get_config('status') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True

    @commands.group(
        case_sensitive=False,
        invoke_without_command=True
    )
    async def res(self, ctx):
        if ctx.invoked_subcommand is None:
            res = self.fetch_res_server()
            await ctx.channel.send(embed=self.make_res_report(res[0]))
    
    def make_res_report(self, ser_list):
        embed=discord.Embed(
            title="Resource Servers",
            description="Server report",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Res | SHIN Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Servers",
            value=f"{len(self.client.res_servers)} ({len(ser_list)})",
            inline=False
        )
        embed.add_field(
            name="Name",
            value="\n".join([server.name for server in ser_list]),
            inline=True
        )
        embed.add_field(
            name="Slots",
            value="\n".join([str(server.emoji_limit) for server in ser_list]),
            inline=True
        )
        embed.add_field(
            name="Filled",
            value="\n".join([str(len(server.emojis)) for server in ser_list]),
            inline=True
        )
        return embed

    @res.command(aliases=['d'])
    async def detailed(self, ctx):
        channel = ctx.channel
        active = await self.active_check(channel)
        if not active:
            return
        
        author = ctx.message.author
        res = self.fetch_res_server()
        pages = [self.make_res_detailed(server) for server in res[0]]

        post = await channel.send(embed=pages[0])

        lr = ['⬅','➡']
        for arrow in lr:
            await post.add_reaction(arrow)
        
        def author_check(reaction, user):
            return str(user.id) == str(author.id) and\
                reaction.emoji in lr and\
                str(reaction.message.id) == str(post.id)
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=author_check)
            except asyncio.TimeoutError:
                for arrow in lr:
                    await post.remove_reaction(arrow, self.client.user)
                break
            else:
                if reaction.emoji == '⬅':
                    pages = pages[-1:] + pages[:-1]
                    await reaction.message.remove_reaction('⬅', user)
                    await reaction.message.edit(embed=pages[0])

                elif reaction.emoji == '➡':
                    pages = pages[1:] + pages[:1]
                    await reaction.message.remove_reaction('➡', user)
                    await reaction.message.edit(embed=pages[0])

                else:
                    continue

    def make_res_detailed(self, server):
        team = self.client.get_team()
        embed=discord.Embed(
            title=server.name,
            description="Server Report",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Resource | SHIN Ames",icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Slots",
            value=f"{str(server.emoji_limit)} ({len(server.emojis)})",
            inline=False
        )
        for chunk in list(self.chunks(list(server.emojis), 17)):
            chunk.sort(key=lambda x: x.name)
            chunk = [f"{team[emote.name]} {emote.name}" for emote in chunk]
            embed.add_field(
                name="Asset",
                value="\n".join(chunk),
                inline=True
            )
        return embed

    def chunks(self, l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n] 

    def fetch_res_server(self):
        ser_list = []
        res_emotes = []
        for server_id in self.client.res_servers:
            guild = self.client.get_guild(server_id)
            ser_list.append(guild)
            res_emotes = res_emotes + list(guild.emojis)

        return ser_list, [emote.name for emote in res_emotes]
    
    def fetch_res_local(self):
        local_list = []
        for filename in glob.glob(os.path.join(dir,'gacha/assets/units/*.webp')):
            local_list.append(filename)
        return local_list
    
    @res.command(aliases=['u'])
    async def update(self, ctx):
        channel = ctx.channel
        active = await self.active_check(channel)
        if not active:
            return
        
        new = []
        ser_list, emotes = self.fetch_res_server()
        loc_list = self.fetch_res_local()

        for loc_emote in loc_list:
            if not loc_emote in emotes:
                new.append(loc_emote)
        
        if len(loc_list) == 0:
            await channel.send('No new asset detected - servers are up-to-date!')
            return
        
        for update_emote_name in new:
            update_emote = Image.open(os.path.join(dir, f'gacha/assets/units/{update_emote_name}.webp'))

            flag = False
            for server in ser_list:
                if server.emoji_limit == len(server.emojis):
                    await self.logger.send(self.name, 'server full', server.name)
                else:
                    await self.logger.send(self.name, 'creating', update_emote_name, 'in', server.name, f"{server.emoji_limit} ({len(server.emojis)})")
                    try:
                        await server.create_custom_emoji(update_emote_name, update_emote)
                    except Exception as e:
                        await self.logger.send('failed to upload', e)
                    else:
                        await self.logger.send('success')
                        flag = True
        
            if not flag:
                await self.logger.send(self.name, 'update failed')
                await channel.send(f"Failed to add {update_emote_name}")
        
        
        


def setup(client):
    client.add_cog(resCog(client))