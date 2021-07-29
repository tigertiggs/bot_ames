# this module takes care of cb functions
from commands.cog_gacha import SPACE
import discord
from discord.ext import commands, tasks
import datetime, pytz
import os, json, asyncio

num_emj = ['1\u20E3','2\u20E3','3\u20E3','4\u20E3','5\u20E3']
REPEAT =  '\U0001f501'
BROOM =   '\U0001f9f9'

timer = 30

class cbCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.name =     "[cb]"
        self.logger =   client.log
        self.colour =   discord.Colour.from_rgb(*client.config['command_colour']['cog_cb'])
        
        with open(os.path.join(self.client.dir, self.client.config['cbtag_config_path']), encoding='utf-8') as ccf:
            self.config = json.load(ccf)
            #self.last_message = self.config['guilds']
        
        self.timeout_checker.start()
    
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
            if ctx.message.author.guild.id != self.client.config['target_guild']:
                await channel.send("This command is unavailable "+self.client.emotes['ames'])
                return
            elif len(options) != 0:
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
                    name="Janitors",
                    value=str(sum([clan['janitor']['janitor'] for clan in [r, g, y]])),
                    inline=False
                )
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
                    value='\n'.join([str(r['bosses'][boss] + y['bosses'][boss] + g['bosses'][boss]) for boss in list(r['bosses'].keys())]),
                    inline=True
                )
                await ctx.channel.send(embed=embed)

    def get_role(self, id):
        return self.client.get_guild(self.config['target_guild']).get_role(id)

    async def toggle_boss(self, user, channel, requests):
        for boss_num in requests:
            if isinstance(boss_num, int):
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
            elif boss_num.lower().startswith('j'):
                if self.config['janitor'][0] in [role.id for role in user.roles]:
                    await user.remove_roles(self.get_role(self.config['janitor'][0]))
                    if channel != None:
                        await channel.send("Removed janitor role")
                else:
                    await user.add_roles(self.get_role(self.config['janitor'][0]))
                    if channel != None:
                        await channel.send("Added janitor role")
        return True

    def collect_data(self, guild='all'):
        target_guild = self.config['target_guild']
        bosses = self.config['boss_roles']

        red =       {'bosses':
                        {
                        'boss1':0,'boss2':0,'boss3':0,'boss4':0,'boss5':0
                        },
                    'janitor':
                    {
                        'janitor': 0
                    }
        }
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
                        temp['bosses'][f"boss{bosses.index(role.id)+1}"] += 1
                    elif role.id in self.config['janitor']:
                        temp['janitor']['janitor'] += 1
        
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

        if ctx.message.author.guild.id != self.client.config['target_guild']:
            await channel.send("This command is unavailable "+self.client.emotes['ames'])
            return

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
            name="Janitors",
            value=str(sum(list(clan['janitor'].values()))),
            inline=False
        )
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
            value='\n'.join([str(val) for val in list(clan['bosses'].values())]),
            inline=True
        )
        post = await ctx.channel.send(embed=embed)
        for emj in [*num_emj, REPEAT, BROOM]:
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
            if emote.name in num_emj or emote.name == BROOM:
                complete = await self.toggle_boss(user, None, [num_emj.index(emote.name) if not emote.name == BROOM else 'j'])
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
        embed_dict['fields'][0]['value'] = str(sum(list(clan['janitor'].values())))
        embed_dict['fields'][2]['value'] = "\n".join(self.get_boss_name(self.config['boss_roles']))
        embed_dict['fields'][3]['value'] = '\n'.join([str(val) for val in list(clan['bosses'].values())])
        return embed.from_dict(embed_dict)
        
    @cbtag.command(
        usage=".cbtag purge",
        help='Remove all boss roles from yourself.'
    )
    async def purge(self, ctx, *options):
        channel = ctx.channel
        if not self.client.command_status['cb'] == 1:
            raise commands.DisabledCommand

        if ctx.message.author.guild.id != self.client.config['target_guild']:
            await channel.send("This command is unavailable "+self.client.emotes['ames'])
            return

        if len(options) == 0:
            for role in ctx.message.author.roles:
                if role.id in self.config['boss_roles'] or role.id in self.config['janitor']:
                    await ctx.message.author.remove_roles(role)
            await ctx.channel.send(self.client.emotes['sarenh'])

        elif options[0] == 'all' and self.client._check_author(ctx.message.author):
            for member in self.client.get_guild(self.config['target_guild']).members:
                for role in member.roles:
                    if role.id in self.config['boss_roles'] or role.id in self.config['janitor']:
                        await member.remove_roles(role)
            await channel.send(self.client.emotes['sarenh'])
    
    @cbtag.command(
        usage='.cbtag edit [boss_num] [name]',
        help="Edit the bosses' name."
    )
    async def edit(self, ctx, boss_num:int, *name):
        channel = ctx.channel
        if not self.client.command_status['cb'] == 1:
            raise commands.DisabledCommand

        if ctx.message.author.guild.id != self.client.config['target_guild']:
            await channel.send("This command is unavailable "+self.client.emotes['ames'])
            return
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
        if not self.client.command_status['cb'] == 1:
            raise commands.DisabledCommand
        
        if ctx.message.author.guild.id != self.client.config['target_guild']:
            await channel.send("This command is unavailable "+self.client.emotes['ames'])
            return
        reset_names = [f'boss {i} - N/A' for i in range(1,6)]
        for i, boss_id in enumerate(self.config['boss_roles']):
            role = self.get_role(boss_id)
            await role.edit(name=reset_names[i])
        await channel.send(self.client.emotes['sarenh'])

    @commands.command(aliases=['q'])
    async def queue(self, ctx, *options):
        channel = ctx.message.channel
        author = ctx.message.author
        guild_id = str(ctx.message.author.guild.id)

        #options = options.split()
        if not options:
            embed = self.display_queue(guild_id, author)
            if embed != None:
                msg = await channel.send(embed=embed)
                await asyncio.sleep(60)
                await msg.edit(content="This queue list has expired "+self.client.emotes['ames'], embed=None)
            else:
                await channel.send("The current queue is empty. Go wild! "+self.client.emotes['amesblob'])
            return
        elif 'help' in options:
            msg = await channel.send(embed=self.queue_help())
            return
        elif 'kill' in options or 'wipe' in options:
            if not self.client._check_author(author,'admin'):
                await channel.send(self.client.emotes['ames'])
                return
            await self.queue_wipe(author.guild, channel, options)
            return

        queue_flag = True
        target_boss = None
        for option in options:
            if option.startswith('d'):
                queue_flag = False
                continue
            if option.startswith('b'):
                option = option[1:]
            if option.isnumeric():
                try:
                    target_boss = int(option)
                except:
                    await channel.send(f"failed to read boss number {option}")
                    return
                else:
                    if target_boss < 1 or target_boss > 5:
                        await channel.send(f"boss number out of range: {target_boss}")
                        return

        try:
            with open(os.path.join(self.client.config['cb_q_path'], f"{guild_id}.json"), "r") as qf:
                q = json.load(qf)   
        except:
            q = {'q':[]}

        if target_boss == None and queue_flag == False:
            await channel.send("Withdrawn from all queues")
            q['q'] = [item for item in q['q'] if item[0] != author.id]
        elif target_boss == None:
            await channel.send("unable to process inputs")
            return
        else:
            active_author_q = list(filter(lambda x: x[0] == author.id and x[1] == target_boss, q['q']))

            if queue_flag:
                if len(active_author_q) > 0:
                    await channel.send(f"You have already queued for boss {target_boss}!")
                    return
                else:
                    q['q'].append((author.id, target_boss, str(datetime.datetime.now(datetime.timezone.utc))))
                    await channel.send(f"queued for boss {target_boss}")
            else:
                q['q'] = [item for item in q['q'] if not (item[0] == author.id and item[1] == target_boss)]
                await channel.send(f'unqueued for boss {target_boss}')
        
        with open(os.path.join(self.client.config['cb_q_path'], f"{guild_id}.json"), "w+") as qf:
            qf.write(json.dumps(q, indent=4))
        
    def cog_unload(self):
        self.timeout_checker.cancel()
    
    @tasks.loop(seconds=timer)
    async def timeout_checker(self):
        with open(os.path.join(self.client.config['cb_q_path'],'config.json')) as cf:
            increment = datetime.timedelta(seconds=json.load(cf)['timeout'])

        for filename in os.listdir(self.client.config['cb_q_path']):
            if filename != "config.json":
                with open(os.path.join(self.client.config['cb_q_path'], filename)) as qf:
                    q = json.load(qf)
                
                current_time = datetime.datetime.now(datetime.timezone.utc)
                q['q'] = [item for item in q['q'] if datetime.datetime.strptime(item[-1], '%Y-%m-%d %H:%M:%S.%f%z') + increment >= current_time]

                with open(os.path.join(self.client.config['cb_q_path'], filename), "w+") as qf:
                    qf.write(json.dumps(q,indent=4))
    
    def display_queue(self, guild_id, author):
        with open(os.path.join(self.client.config['cb_q_path'],'config.json')) as cf:
            increment = json.load(cf)['timeout']
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        try:
            with open(os.path.join(self.client.config['cb_q_path'], f"{guild_id}.json"), "r") as qf:
                q = json.load(qf)
        except:
            q = {'q':[]}
        
        if not q['q']:
            return None

        total_queue = [[],[],[],[],[]]
        for item in q['q']:
            member = author.guild.get_member(item[0])
            member = member.nick if member.nick else member.name
            t = datetime.datetime.strptime(item[2], '%Y-%m-%d %H:%M:%S.%f%z')
            clean = (member if item[0] != author.id else f"**{member}**", item[1], f"{self.timetz_to_tz(t,pytz.timezone('Asia/Tokyo')).strftime('%H%M JST')} ({round((now-t).total_seconds()/60,1)}min elapsed)")
            total_queue[item[1]-1].append(clean)
        
        for boss_queue_list in total_queue:
            boss_queue_list.sort(key=lambda x: x[-1])

        embed=discord.Embed(
            title="Clan Battle Queue",
            description=f"Current queue's automatic timeout is **{round(increment/60,1)}min**. Only displaying bosses with active queues. See `.q help` or `.help queue` for details on usage. Happy Clan Battling!",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text='CB Queue | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        
        icons = [":one:",":two:",":three:",":four:",":five:"]
        roles = [self.get_role(r) for r in self.config['boss_roles']]
        for i in range(5):
            embed.add_field(
                name=SPACE,
                value=f"{icons[i]} **{roles[i].name}**",
                inline=False
            )
            
            empty=False
            if total_queue[i]:
                name=[item[0] for item in total_queue[i]]
                #time=[self.timetz_to_tz(item[-1],pytz.timezone('Asia/Tokyo')).strftime('%H%M JST') for item in total_queue[i]]
                time=[item[-1] for item in total_queue[i]]
            else:
                name=['Empty Queue']
                time=['N/A']
                empty=True
                continue

            embed.add_field(
                name="No.",
                value="\n".join([str(i) for i in range(1,len(name)+1)] if not empty else ['.'])
            )
            embed.add_field(
                name="Name",
                value="\n".join(name)
            )
            embed.add_field(
                name="Time Queued",
                value="\n".join(time)
            )
        
        return embed
    
    async def queue_wipe(self, guild, channel, options):
        target_boss = None
        target_member = None
        for option in options:
            if option.isnumeric():
                target_boss = int(option)
                if target_boss < 1 or target_boss > 5:
                    await channel.send('invalid boss entry')
                    return
            elif len(option) > 4:
                try:
                    author_id = int(option[3:-1])
                except:
                    await channel.send("could not read member")
                    return
                else:
                    target_member = guild.get_member(int(author_id))

        try:
            with open(os.path.join(self.client.config['cb_q_path'], f"{guild.id}.json"), "r") as qf:
                q = json.load(qf)
        except:
            q = {'q':[]}
        
        if target_boss and target_member:
            q['q'] = [item for item in q['q'] if not (item[0] == target_member.id and item[1] == target_boss)]
            await channel.send(f"cleared all entries from {target_member.name} under boss {target_boss}")
        elif target_boss:
            q['q'] = [item for item in q['q'] if not item[1] == target_boss]
            await channel.send(f"cleared all entries under boss {target_boss}")
        elif target_member:
            q['q'] = [item for item in q['q'] if not item[0] == target_member.id]
            await channel.send(f"cleared all entries from {target_member.name}")
        else:
            q['q'] = []
            await channel.send('wiped all')
        
        with open(os.path.join(self.client.config['cb_q_path'], f"{guild.id}.json"), "w+") as qf:
            qf.write(json.dumps(q, indent=4))
    
    def queue_help(self):
        embed=discord.Embed(
            title="CB Queue Help",
            description="Help section for `.q`. See `.help queue` for extended documentation.",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text='CB Queue Help | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Syntax",
            value="`.q optional[boss_number] optional[done]`",
            inline=False
        )
        embed.add_field(
            name="Usage",
            value="1) To see the current queue, use `.q`\n\n2) To add yourself to the queue of some boss, use `.q [boss_nume]`\n\n3) To remove yourself from the queue of a certain boss, use `.q [boss_num] done`, alternatively, use `.q done` to remove yourself from all queues"
        )
        embed.add_field(
            name="Notes",
            value="1) You will automatically be unqueued if you do not clear yourself from the queue after a specific amount of time has passed. See `.q` for the exact duration.",
            inline=False
        )
        return embed

    def timetz_to_tz(self, t, tz_out):
        return t.astimezone(tz_out).timetz()

def setup(client):
    client.add_cog(cbCog(client))