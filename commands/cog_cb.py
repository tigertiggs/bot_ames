import ast
import discord
from discord.ext import commands
import datetime
import os, sys
dir = os.path.dirname(__file__)

# Boss Roles IDs
BOSS_1 =                616120855277076490
BOSS_2 =                616121000228290561
BOSS_3 =                616121101604618259
BOSS_4 =                616121290243178497
BOSS_5 =                616121405423091723
bosses =                [BOSS_1,BOSS_2,BOSS_3,BOSS_4,BOSS_5]
#rbosses =               {str(BOSS_1):1,str(BOSS_2):2,str(BOSS_3):3,str(BOSS_4):4,str(BOSS_5):5}

num_emj =               ['1\u20E3','2\u20E3','3\u20E3','4\u20E3','5\u20E3']
#num =                   ['1','2','3','4','5']
guild_name = dict()
guild_name['green'] =   '進撃のロリ'
guild_name['yellow'] =  '進撃の熟女'
guild_name['red'] =     '進撃の怠け'

# guild ID
guild_d = dict()
guild_d['435067795919863808'] = 'green'
guild_d['435067668241055785'] = 'yellow'
guild_d['547685646001504256'] = 'red'
guild_d['434628129357824000'] = 'green'
guild_d['434628671387467788'] = 'yellow'
guild_d['547686074302857218'] = 'red'

# reacts
REPEAT =    '\U0001f501'
#STOP =      '\U0001f6d1'

# target guild
target_guild = 419624511189811201

class cbCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.last_message = None
        self.name = '[cb]'
        #self.active = client.get_config('cb')
        self.logger = client.log
        with open(os.path.join(dir,'_config/cbtag.txt')) as cf:
            self.last_embed = ast.literal_eval(cf.read())
    
    async def active_check(self, channel):
        if self.client.get_config('cb') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    def collate(self, guild='all'):
        red =       {'boss1':0,'boss2':0,'boss3':0,'boss4':0,'boss5':0}
        yellow =    red.copy()
        green =     red.copy()

        for member in self.client.get_guild(target_guild).members:
            if guild_d.get(str(member.top_role.id), None) is 'red':
                for role in member.roles:
                    if role.id in bosses:
                        red[f"boss{bosses.index(role.id)+1}"] = red[f"boss{bosses.index(role.id)+1}"] + 1
            elif guild_d.get(str(member.top_role.id), None) is 'yellow':
                for role in member.roles:
                    if role.id in bosses:
                        yellow[f"boss{bosses.index(role.id)+1}"] = yellow[f"boss{bosses.index(role.id)+1}"] + 1
            elif guild_d.get(str(member.top_role.id), None) is 'green':
                for role in member.roles:
                    if role.id in bosses:
                        green[f"boss{bosses.index(role.id)+1}"] = green[f"boss{bosses.index(role.id)+1}"] + 1
            else:
                continue
                #print(f"invalid top role {member.top_role.name}")
        
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
        return [self.client.get_guild(target_guild).get_role(bid).name.split('-')[-1].strip() for bid in boss_id]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.client.user.id:
            return

        user = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        emote = payload.emoji
        message_id = payload.message_id

        last_message_ids = [self.last_embed['r']['message'], 
                            self.last_embed['g']['message'], 
                            self.last_embed['y']['message']]
        if message_id in last_message_ids:
            message = await self.client.get_guild(payload.guild_id).get_channel(payload.channel_id).fetch_message(message_id)
            if emote.name in num_emj:
                await self.toggle_boss(user, None, num_emj.index(emote.name))
                await message.edit(embed=self.refresh_embed(message.embeds[0]))
            elif emote.name == REPEAT:
                await message.edit(embed=self.refresh_embed(message.embeds[0]))
            else:
                pass
            await message.remove_reaction(emote, user)
    
    def get_role(self, boss_id):
        return self.client.get_guild(target_guild).get_role(boss_id)

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
        clan = self.collate(mode)
        embed_dict = embed.to_dict()
        embed_dict['fields'][1]['value'] = "\n".join(self.get_boss_name(bosses))
        embed_dict['fields'][2]['value'] = '\n'.join([str(val) for val in list(clan.values())])
        return embed.from_dict(embed_dict)

    async def toggle_boss(self, user, channel=None, *num):
        for boss_num in num:
            try:
                boss_num = int(boss_num)
            except:
                if channel != None:
                    await channel.send(f"I failed to toggle boss {boss_num} {self.client.emj['ames']}")
            else:
                request = bosses[boss_num]
                if request in [role.id for role in user.roles]:
                    await user.remove_roles(self.get_role(request))
                    if channel != None:
                        await channel.send(f"Successfully removed {self.get_role(request).name}!")
                else:
                    await user.add_roles(self.get_role(request))
                    if channel != None:
                        await channel.send(f"Successfully added {self.get_role(request).name}!")

    @commands.group(
        invoke_without_command=True,
        case_insensitive=True,
        usage='.cbtag [*options]',
        help='This command is restricted to a certain server only. Show waiting list for all 3 guilds.'
    )
    async def cbtag(self, ctx, *options):
        check = await self.active_check(ctx.channel)
        if not check:
            return
        
        if ctx.invoked_subcommand is None:
            if len(options) != 0:
                for i in options:
                    try:
                        await self.toggle_boss(ctx.message.author, ctx.channel, int(i)-1)
                    except:
                        continue
            else:
                red, yellow, green = self.collate()
                embed = discord.Embed(
                    title="CB Tag",
                    description='Displaying waits for all 3 guilds.',
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_footer(text='CB Tag | SHIN Ames',icon_url=self.client.user.avatar_url)
                embed.add_field(
                    name="No.",
                    value="\n".join([str(i) for i in range(1,6)]),
                    inline=True
                )
                embed.add_field(
                    name="Boss Name",
                    value="\n".join(self.get_boss_name(bosses)),
                    inline=True
                )
                embed.add_field(
                    name='Awaiting',
                    value='\n'.join([str(red[boss] + yellow[boss] + green[boss]) for boss in list(red.keys())]),
                    inline=True
                )
                await ctx.channel.send(embed=embed)
    
    @cbtag.command(
        usage='.cbtag post',
        help='Have Ames send an embed where you can assign yourself a boss role by reacting to the corresponding number.'
    )
    async def post(self, ctx):
        channel = ctx.channel
        author = ctx.message.author

        # read last message
        with open(os.path.join(dir,'_config/cbtag.txt')) as cf:
            self.last_embed = ast.literal_eval(cf.read())
        
        # get author top role
        top = guild_d.get(str(author.top_role.id), None)
        if top is None:
            await channel.send(f"I did not find your guild role {self.client.emj['ames']}")
            await self.logger.send(self.name,'Invalid top role for post',author.top_role.name)
            return

        # invalidate last post
        try:
            last_channel = self.last_embed[top[0]].get('channel', None)
            last_message = self.last_embed[top[0]].get('message', None)
            if last_channel != None and last_message != None:
                msg = await channel.guild.get_channel(self.last_embed[top[0]]['channel']).fetch_message(self.last_embed[top[0]]['message'])
                await msg.edit(content=f"There used to be a `cbtag post` here, but now there isn't {self.client.emj['ames']}",embed=None)
        except Exception as e:
            await self.logger.send(self.name, 'Failed to invalidate last post:', e)
        
        # post
        clan = self.collate(top)
        embed = discord.Embed(
                title=f"{guild_name[top]}'s Boss reminders",
                description=f'React to a number to add/remove that boss tag.\nReact to {REPEAT} to refresh the list.',
                timestamp=datetime.datetime.utcnow()
            )
        embed.set_footer(text='CB Tag Post | SHIN Ames',icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="No.",
            value="\n".join([str(i) for i in range(1,6)]),
            inline=True
        )
        embed.add_field(
            name="Boss Name",
            value="\n".join(self.get_boss_name(bosses)),
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
        
        self.last_embed[top[0]]['message'] = post.id
        self.last_embed[top[0]]['channel'] = post.channel.id

        with open(os.path.join(dir,'_config/cbtag.txt'), 'w') as cf:
            cf.write(str(self.last_embed))
    
    @cbtag.command(
        usage='.cbtag purge',
        help='Remove all boss roles from yourself.'
    )
    async def purge(self, ctx, *options):
        channel = ctx.channel
        if len(options) != 0:
            if options[0] == 'all':
                for member in self.client.get_guild(target_guild).members:
                    for role in member.roles:
                        if role.id in bosses:
                            await member.remove_roles(role)
                await channel.send(self.client.emj['sarenh'])
        else:
            for role in ctx.message.author.roles:
                if role.id in bosses:
                    await ctx.message.author.remove_roles(role)
            await ctx.channel.send(self.client.emj['sarenh'])
    
    @cbtag.command(
        usage='.cbtag edit [boss_num] [name]',
        help="Edit the bosses' name."
    )
    async def edit(self, ctx, boss_num:int, *name):
        channel = ctx.channel
        try:
            role = self.get_role(bosses[boss_num-1])
            old_name = role.name.split(' - ')
            new_name = [old_name[0], " ".join(name)]
            await role.edit(name=" - ".join(new_name))
            await channel.send(self.client.emj['sarenh'])
        except Exception as e:
            print(e)
            await channel.send(self.client.emj['ames'])
            return
    
    @cbtag.command(
        usage=".cbtag reset",
        help="Reset all boss names.",
        hidden=True
    )
    async def reset(self, ctx):
        channel = ctx.channel
        reset_names = [f'boss {i} - N/A' for i in range(1,6)]
        for i, boss_id in enumerate(bosses):
            role = self.get_role(boss_id)
            await role.edit(name=reset_names[i])
            await channel.send(self.client.emj['sarenh'])

def setup(client):
    client.add_cog(cbCog(client))