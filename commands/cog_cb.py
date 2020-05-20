# this module takes care of cb functions
import discord
from discord.ext import commands
import datetime
import os, sys, json, asyncio

num_emj = ['1\u20E3','2\u20E3','3\u20E3','4\u20E3','5\u20E3']
REPEAT =  '\U0001f501'

class cbCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.name =     "[cb]"
        self.logger =   client.log
        self.colour =   discord.Colour.from_rgb(*client.config['command_colour']['cog_cb'])
        
        with open(os.path.join(self.client.dir, self.client.config['cbtag_config_path']), encoding='utf-8') as ccf:
            self.config = json.load(ccf)
            #self.last_message = self.config['guilds']
    
    def write_to_config(self):
        #self.config['guilds'] = guilds
        with open(os.path.join(self.client.dir, self.client.config['cbtag_config_path']), 'w') as ccf:
            ccf.write(json.dumps(self.config, indent=4))
    
    @commands.group(
        invoke_without_command=True,
        case_insensitive=True,
        usage=".cbtag [*options|optional]",
        help='This command is restricted to a certain server only. Show waiting list for all 3 guilds.'
    )
    async def cbtag(self, ctx, *options):
        channel = ctx.channel
        if not self.client.command_status['cb'] == 1:
            raise commands.DisabledCommand

        if ctx.invoked_subcommand is None:
            if len(options) != 0:
                await self.toggle_boss(ctx.message.author, channel, options)

            else:
                r, y, g = self.collect_data()
                embed = discord.Embed(
                    title="CB Tag",
                    description='Displaying waits for all 3 guilds.',
                    timestamp=datetime.datetime.utcnow(),
                    colour=self.colour
                )
                embed.set_footer(text='CB Tag | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
                embed.add_field(
                    name="No.",
                    value="\n".join([str(i) for i in range(1,6)]),
                    inline=True
                )
                embed.add_field(
                    name="Boss Name",
                    value="\n".join(self.get_boss_name(self.config['boss_roles'])),
                    inline=True
                )
                embed.add_field(
                    name='Awaiting',
                    value='\n'.join([str(r[boss] + y[boss] + g[boss]) for boss in list(r.keys())]),
                    inline=True
                )
                await ctx.channel.send(embed=embed)

    def get_role(self, id):
        return self.client.get_guild(self.config['target_guild']).get_role(id)

    async def toggle_boss(self, user, channel, requests):
        for boss_num in requests:
            try:
                boss_num = int(boss_num)
            except:
                await channel.send(f"Failed to toggle `{boss_num}`")
            else:
                request = self.config['boss_roles'][boss_num]
                if request in [role.id for role in user.roles]:
                    await user.remove_roles(self.get_role(request))
                    if channel != None:
                        await channel.send(f"Successfully removed `{self.get_role(request).name}`")
                else:
                    await user.add_roles(self.get_role(request))
                    if channel != None:
                        await channel.send(f"Successfully added `{self.get_role(request).name}`")
        return True

    def collect_data(self, guild='all'):
        target_guild = self.config['target_guild']
        bosses = self.config['boss_roles']

        red =       {'boss1':0,'boss2':0,'boss3':0,'boss4':0,'boss5':0}
        yellow =    red.copy()
        green =     red.copy()

        for member in self.client.get_guild(target_guild).members:
            cguild = self.get_member_guild(member)
            if cguild != None:
                if cguild['colour'].startswith('r'):
                    temp = red
                elif cguild['colour'].startswith('g'):
                    temp = green
                else:
                    temp = yellow
                
                for role in member.roles:
                    if role.id in bosses:
                        temp[f"boss{bosses.index(role.id)+1}"] += 1
        
        if guild is 'all':
            return red, yellow, green 
        elif guild[0] is 'g':
            return green
        elif guild[0] is 'y':
            return yellow
        elif guild[0] is 'r':
            return red
        else:
            print('invalid guild option in collate')

    def get_boss_name(self, boss_id):
        return [self.client.get_guild(self.config['target_guild']).get_role(bid).name.split('-')[-1].strip() for bid in boss_id]

    def get_member_guild(self, author):
        top_id = author.top_role.id
        alt = [[key, value['id']] for key, value in list(self.config['guilds'].items())]
        for guild_name, ids in alt:
            if top_id in ids:
                return self.config['guilds'][guild_name]
        return None

    @cbtag.command(
        usage=".cbtag post",
        help='Have Ames send an embed where you can assign yourself a boss role by reacting to the corresponding number.'
    )
    @commands.cooldown(1, 5, commands.BucketType.default)
    async def post(self, ctx):
        channel = ctx.channel
        author = ctx.message.author

        if not self.client.command_status['cb'] == 1:
            raise commands.DisabledCommand

        guild = self.get_member_guild(author)
        if guild == None:
            await channel.send(f"I did not find your guild role {self.client.emotes['ames']}")
            await self.logger.send(self.name,'Invalid top role for post',author.top_role.name)
            return
        
        try:
            if not None in list(guild['last_message'].values()):
                msg = await channel.guild.get_channel(guild['last_message']['channel']).fetch_message(guild['last_message']['message'])
                await msg.edit(embed=None, content="This `cbtag post` has been invalidated; please use the most recent post message "+self.client.emotes['ames'])
        except Exception as e:
            await self.logger.send(self.name, e)
        
        clan = self.collect_data(guild['colour'][0])
        embed = discord.Embed(
                title=f"{guild['name']}'s Boss reminders",
                description=f'React to a number to add/remove that boss tag.\nReact to {REPEAT} to refresh the list.',
                timestamp=datetime.datetime.utcnow(),
                colour=self.colour
            )
        embed.set_footer(text='CB Tag Post | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="No.",
            value="\n".join([str(i) for i in range(1,6)]),
            inline=True
        )
        embed.add_field(
            name="Boss Name",
            value="\n".join(self.get_boss_name(self.config['boss_roles'])),
            inline=True
        )
        embed.add_field(
            name='Awaiting',
            value='\n'.join([str(val) for val in list(clan.values())]),
            inline=True
        )
        post = await ctx.channel.send(embed=embed)
        for emj in [*num_emj, REPEAT]:
            await post.add_reaction(emj)

        guild['last_message']['message'] = post.id
        guild['last_message']['channel'] = post.channel.id
        self.config['guilds'][guild['colour']] = guild
        self.write_to_config()

        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        if user.bot:
            return
        
        emote = payload.emoji
        message_id = payload.message_id

        last_message_ids = [value['last_message']['message'] for value in list(self.config['guilds'].values())]

        if message_id in last_message_ids:
            message = await self.client.get_guild(payload.guild_id).get_channel(payload.channel_id).fetch_message(message_id)
            if emote.name in num_emj:
                complete = await self.toggle_boss(user, None, [num_emj.index(emote.name)])
                if complete:
                    await message.edit(embed=self.refresh_embed(message.embeds[0]))
            elif emote.name == REPEAT:
                await message.edit(embed=self.refresh_embed(message.embeds[0]))
            await message.remove_reaction(emote, user)
    
    def refresh_embed(self, embed):
        if '進撃のロリ' in embed.title:
            mode = 'g'
        elif '進撃の熟女' in embed.title:
            mode = 'y'
        elif '進撃の怠け' in embed.title:
            mode = 'r'
        else:
            print(self.name, 'refresh_embed: Failed to read embed title')
            return embed
        clan = self.collect_data(mode)
        embed_dict = embed.to_dict()
        embed_dict['fields'][1]['value'] = "\n".join(self.get_boss_name(self.config['boss_roles']))
        embed_dict['fields'][2]['value'] = '\n'.join([str(val) for val in list(clan.values())])
        return embed.from_dict(embed_dict)
        
    @cbtag.command(
        usage=".cbtag purge",
        help='Remove all boss roles from yourself.'
    )
    async def purge(self, ctx, *options):
        channel = ctx.channel
        if len(options) == 0:
            for role in ctx.message.author.roles:
                if role.id in self.config['boss_roles']:
                    await ctx.message.author.remove_roles(role)
            await ctx.channel.send(self.client.emotes['sarenh'])

        elif options[0] == 'all' and self.client._check_author(ctx.message.author):
            for member in self.client.get_guild(self.config['target_guild']).members:
                for role in member.roles:
                    if role.id in self.config['boss_roles']:
                        await member.remove_roles(role)
            await channel.send(self.client.emotes['sarenh'])
    
    @cbtag.command(
        usage='.cbtag edit [boss_num] [name]',
        help="Edit the bosses' name."
    )
    async def edit(self, ctx, boss_num:int, *name):
        channel = ctx.channel
        try:
            role = self.get_role(self.config['boss_roles'][boss_num-1])
            old_name = role.name.split(' - ')
            new_name = [old_name[0], " ".join(name)]
            await role.edit(name=" - ".join(new_name))
            await channel.send(self.client.emotes['sarenh'])
        except Exception as e:
            await self.logger.send(self.name, e)
            await channel.send(self.client.emotes['ames'])
            return

    @cbtag.command(
        usage=".cbtag reset",
        help="Reset all boss names.",
        hidden=True
    )
    async def reset(self, ctx):
        channel = ctx.channel
        reset_names = [f'boss {i} - N/A' for i in range(1,6)]
        for i, boss_id in enumerate(self.config['boss_roles']):
            role = self.get_role(boss_id)
            await role.edit(name=reset_names[i])
        await channel.send(self.client.emotes['sarenh'])

def setup(client):
    client.add_cog(cbCog(client))