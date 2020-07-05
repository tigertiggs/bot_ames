# Ames' core cog
# should contain all self diagnostics and logistical functions

import discord
from discord.ext import commands
import datetime, time, os, sys, requests, random, json, re, traceback
from difflib import SequenceMatcher as sm
from math import ceil

#dir = os.path.dirname(__file__)
SPACE = '\u200B'

class coreCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.logger =   self.client.log
        self.name =     "[core]"
        self.colour =   discord.Colour.from_rgb(*client.config['command_colour']['cog_core'])

    @commands.command(
        usage='.kill',
        aliases=['kys'],
        help="Bury Ames",
        hidden=True
    )
    async def kill(self, ctx):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['amesyan'])
        else:
            await channel.send("I'll be right back "+self.client.emotes['sarenh'])
            await self.client.close()

    def compare_version(self):            
        flag =      0
        keys =      ['major', 'update', 'patch']
        clientv =   ".".join([str(self.client.version[p]) for p in keys])
        try:
            git_version = json.loads(requests.get(self.client.version['tracker']).text)
        except:
            return clientv, "(check failed)"
        gitv =      ".".join([str(git_version[p]) for p in keys])
        
        for key in keys:
            if self.client.version[key] < git_version[key]:
                flag = 1
                break
            elif self.client.version[key] > git_version[key]:
                flag = -1
                break
            else:
                continue
        if flag == 0:
            update = "(UTD)"
        elif flag == 1:
            update = f"(update available: {gitv})"
        else:
            update = "(unreleased)"

        return clientv, update
    
    @commands.group(
        invoke_with_command=True,
        aliases=['toirland'],
    )
    async def status(self, ctx):
        # this command should always be active
        channel = ctx.channel
        if not self.client.command_status['status'] == 1:
            raise commands.DisabledCommand
        
        if ctx.invoked_subcommand is None:
            # fetch idle messages
            with open(os.path.join(self.client.dir, self.client.config['status_path'])) as sf:
                statusv = json.load(sf)
            
            # status report
            red =       ":red_circle:"
            green =     ":green_circle:"
            nguilds =   len(self.client.guilds)
            uptime =    str(datetime.timedelta(seconds=int(round(time.time() - self.client.s_time))))
            state =     [" ".join([red if v == False else green, k.split(".")[-1]]) for k,v in list(self.client.cogs_status.items())]
            """
            try:
                conn = self.client.database.db_pointer.get_connection()
                if conn.is_connected():
                    self.client.database.release(conn)
                    conn = True
                else:
                    self.client.database.release(conn)
                    conn = False
            except Exception as e:
                conn = False
                await self.logger.send(self.name,"[status]",e)
            """
            conn = False
            clientv, updatemsg = self.compare_version()

            # make embed
            embed = discord.Embed(
                title="Status",
                description=random.choice(statusv['messages']),
                timestamp=datetime.datetime.utcnow(),
                colour=self.colour
            )
            embed.set_thumbnail(url=self.client.user.avatar_url),
            embed.set_footer(text="Status | Ames Re:Re:Write", icon_url=self.client.user.avatar_url)
            embed.add_field(
                name="Version",
                value=f"[{' '.join([clientv, updatemsg])}](https://github.com/tigertiggs/bot_ames)",
                inline=True
            )
            embed.add_field(
                name="Creator",
                value="tigertiggs#5376",
                inline=True
            )
            embed.add_field(
                name="Uptime",
                value=uptime,
                inline=True
            )
            embed.add_field(
                name="Database",
                value='Connected' if conn else 'Disconnected',
                inline=True
            )
            embed.add_field(
                name='Latency',
                value='{}ms'.format(int(self.client.latency*1000)),
                inline=True
            )
            embed.add_field(
                name="Guilds",
                value=str(nguilds),
                inline=True
            )
            splice = ceil(len(state)/3)
            if len(state) > 5:
                for cstatus in self.client.chunks(state, splice):
                    embed.add_field(
                        name="Cog Status",
                        value="\n".join(cstatus),
                        inline=True
                    )
            else:
                embed.add_field(
                        name="Cog Status",
                        value="\n".join(state),
                        inline=True
                    )
            await channel.send(embed=embed)

    @status.command(aliases=["cmd"])
    async def cmds(self, ctx):
        channel = ctx.channel
        if not self.client.command_status['status'] == 1:
            raise commands.DisabledCommand
        else:
            red =       ":red_circle:"
            green =     ":green_circle:"
            embed = discord.Embed(
                title="Command Status",
                timestamp=datetime.datetime.utcnow(),
                colour=self.colour
            )
            embed.set_thumbnail(url=self.client.user.avatar_url),
            embed.set_footer(text="Command Status | Ames Re:Re:Write", icon_url=self.client.user.avatar_url)

            cmd_status = list(self.client.command_status.items())
            cmd_status.sort(key=lambda x: x[0])
            for chunk in self.client.chunks(cmd_status, ceil(len(cmd_status)/3)):
                embed.add_field(
                    name="Active Commands",
                    value="\n".join([f"{green if state == 1 else red} {cmd}" for cmd, state in chunk]),
                    inline=True
                )
            await channel.send(embed=embed)

    @commands.command(
        usage=".command_set [command] [state:0 or 1]",
        aliases=['cs'],
        help="Use this to enable/disable specific commands",
        hidden=True
    )
    async def command_set(self, ctx, command, state:int):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return
        elif not command in list(self.client.command_status.keys()):
            await channel.send('no such command found or command cannot be toggled')
            return
        else:
            self.client.command_status[command] = state
            await channel.send(f"successfully set {command} to {state}")
    
    @commands.command(
        usage='.ping',
        help='Get Ames\' current latency in milliseconds.',
        hidden=False
    )
    async def ping(self, ctx):
        channel = ctx.channel
        if not self.client.command_status['ping'] == 1:
            raise commands.DisabledCommand

        t1 = time.perf_counter()
        pong = await channel.send(self.client.emotes['ames'])
        t2 = time.perf_counter()
        await pong.edit(content='{} ({}ms)'.format(self.client.emotes['ames'], round((t2-t1)*1000)))
    
    @commands.command(
        hidden=True,
        usage='.purge [depth=100]',
        help='Look through [depth] most recent messages in the current channel and delete Ames\' messages.'
    )
    async def purge(self, ctx, depth:int=100):
        channel = ctx.channel
        if not self.client.command_status['purge'] == 1:
            raise commands.DisabledCommand
        elif not self.client._check_author(ctx.message.author, "admin"):
            await channel.send("Missing [admin] permission "+self.client.emotes['ames'])
            return

        def is_me(message):
            return message.author == self.client.user
        await channel.purge(limit=depth, check=is_me)
    
    @commands.command(
        usage=".resetdb",
        help="Use this should the database run out of connections in the current pool due to whatever reason"
    )
    async def resetdb(self, ctx):
        channel = ctx.channel
        if not self.client.command_status['resetdb'] == 1:
            raise commands.DisabledCommand

        await channel.send("Attempting to reset database - check logs")
        await self.client.database.connect()

    @commands.command(
        usage=".reload [cog]",
        aliases=['refresh'],
        help="Use this to reload a cog. Saves a restart",
        hidden=True
    )
    async def reload(self, ctx, cog):
        channel = ctx.channel 
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.emotes['ames'])
            return
        else:
            await channel.send(f"Attempting to reload {cog}")
        
        # perform checks
        if not cog in [seg.split('_')[-1] for seg in list(self.client.cogs_status.keys())]:
            await channel.send(f"Did not find {cog} in registered cogs")
            return
        elif cog == 'core':
            await channel.send("Cannot modify core")
            return
        elif not self.client.cogs_status[f"commands.cog_{cog}"]:
            await channel.send(f"{cog} is not loaded")
            return
        else:
            try:
                self.client.unload_extension(f"commands.cog_{cog}")
                self.client.load_extension(f"commands.cog_{cog}")
            except Exception as e:
                await self.logger.send(self.name, e)
                await channel.send("Something wrong happened - check logs")
                self.client.cogs_status[f"commands.cog_{cog}"] = 0
                return
            else:
                await channel.send("Reloaded!")
                await self.logger.send(self.name, f"reloaded commands.cog_{cog}")

    @commands.command(
        usage=".cog_set [cog] [state:0 or 1]",
        aliases=['es'],
        help="Load/unload a cog",
        hidden=True
    )
    async def ext_set(self, ctx, cog, state:int):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.emotes['ames'])
            return
        else:
            await channel.send("Attempting to set cog state")
        
        # checks
        if not cog in [seg.split('_')[-1] for seg in list(self.client.cogs_status.keys())]:
            await channel.send(f"Did not find {cog} in registered cogs")
            return
        elif cog == 'core':
            await channel.send("Cannot modify core")
            return
        elif self.client.cogs_status[f"commands.cog_{cog}"] == state:
            await channel.send(f"{cog} already set to {state}")
            return
        else:
            try:
                if state == 0:
                    self.client.unload_extension(f"commands.cog_{cog}")
                else:
                    self.client.load_extension(f"commands.cog_{cog}")
            except Exception as e:
                await channel.send("Something went wrong - check logs")
                await self.logger.send(self.name, e)
                return
            else:
                self.client.cogs_status[f"commands.cog_{cog}"] = state
                await channel.send("Succesfully set!")
                await self.logger.send(self.name, f"set {cog} to {state}")

    # have ames stare at you if you ping her
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        elif self.client.user in message.mentions:
            #await self.logger.send(self.name, "mention", message.content)
            messagev = message.content.split()

            if len(messagev) > 1:
                ctx = await self.client.get_context(message)
                # important commands
                if ("🔪" in message.content or "\uFE0F" in message.content):
                    await ctx.invoke(self.client.get_command("kill"))
                    return

                elif "ping" in message.content:
                    await ctx.invoke(self.client.get_command("ping"))
                    return

                else:
                    cmd = self.client.get_command(messagev[1])
                    if not cmd == None:
                        #ctx.content =   messagev[1:]
                        #ctx.command =   cmd
                        #origin =        [cmd.cog, ctx]
                        #ctx.args =      origin+messagev[2:] if len(messagev) > 2 else origin
                        #print(ctx.command, ctx.args)
                        #print(ctx.__dict__)
                        await ctx.invoke(cmd)
                        return

            await message.channel.send(self.client.emotes['ames'])

    # have ames say something (restricted)
    @commands.command(
        usage=".say [*args]",
        help="Have Ames say something",
        hidden=True
    )
    async def say(self, ctx, *, message):
        if not self.client._check_author(ctx.message.author, "admin") or len(message) == 0:
            await ctx.channel.send(self.client.emotes['ames'])
            return
        else:
            await ctx.message.delete()
        
        # new format: string is in a single line
        # use \n to signify line breaks
        # channel is now indicated by --#guild_id.channel.id

        # see if target channel is specified
        print(message)
        code = message.split("--#") # ['message', 'guild_id.channel_id']
        if len(code) == 1:
            guild_id = ctx.message.channel.guild.id
            channel_id = ctx.message.channel.id
        elif len(code) == 2:
            guild_id, channel_id = code[-1].split('.')
            #guild_id, channel_id = int(guild_id), int(channel_id)
        else:
            await ctx.channel.send(self.client.emotes['ames'])
            return
        
        message = code[0]

        guild_id = 419624511189811201
        guild = discord.utils.get(self.client.guilds, id=int(guild_id) if guild_id != '' else ctx.message.channel.guild.id)
        if guild == None:
            await self.client.log.send('failed to find guild')
        channel = discord.utils.get(guild.channels, id=int(channel_id) if channel_id != '' else ctx.message.channel.id)
        if channel == None:
            await self.client.log.send('failed to find guild')

        # break message by newline characters
        lines = message.split("\\n")
        #print(message)

        temp = []
        for line in lines:
            #r = re.search(r'\:\:[a-zA-Z0-9]+\-*[0-9]{,2}|\@[a-zA-Z0-9]+', line)
            #r = re.search(r'<?[<a]?\:[0-9a-zA-Z_]+\:[0-9]*>?|\@[a-zA-Z0-9]+', line)

            for match in re.finditer(r'<?a?\:([-\d\w_]+)\:?(\d*)>?|\@([^!][\d\w]+)', line):
                if match.group(3) != None: # found user
                    user = await self.client.find_user(guild, match.group(3).strip('@'))
                    if not user:
                        continue
                    else:
                        line = line.replace(match.group(), f"<@{user.id}>")
                else: #found emote
                    emote = None
                    if match.group(2): # found id
                        result = [emote for emote in self.client.emojis if not emote.guild_id in self.client.private['resource_servers'] and str(emote.id) == match.group(2)]
                        if result:
                            emote = result[0]
                    if match.group(1) and not emote: # if emote name
                        x = match.group(1).split('--')
                        search = x[0]
                        ind = 0
                        if len(x) > 1 and x[-1].isnumeric():
                            ind = int(x[-1])-1

                        result = list(filter(lambda x: not x.guild_id in self.client.private['resource_servers'] and sm(None, search.lower(), x.name.lower(), None).ratio() >= 0.25 and search.lower() in x.name.lower(), self.client.emojis))
                        if result:
                            result.sort(key=lambda x: x.name)
                            try:
                                emote = result[ind]
                            except:
                                emote = result[0]
                    if not emote:
                        continue

                    if emote.animated:
                        emote = f"<a:{emote.name}:{emote.id}>"
                    else:
                        emote = f"<:{emote.name}:{emote.id}>"

                    line = line.replace(match.group(), emote)
            
            temp.append(line)

        """    
            if section[0] == ':':
                emote = section.strip(':')
                emote = list(filter(lambda x: not x.guild_id in self.client.private['resource_servers'] and sm(None, emote.lower(), x.name.lower(), None).ratio() >= 0.4 and emote.lower() in x.name.lower(), self.client.emojis))
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
        """
        print(temp)
        await channel.send('\n'.join(temp))

    @commands.command(
        usage=".debug [args]",
        help="Set debug value for Ames",
        hidden=True
    )
    async def debug(self, ctx, val:int):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return

        if val not in [0, 1]:
            return
        
        self.client.config['debug'] = val
        if val == 1:
            await self.logger.send(self.name, "Ames debug now active")
        else:
            await self.logger.send(self.name, "Ames debug inactive")
        
        await channel.send("Changed debug state")

    @commands.command()
    async def choose(self, ctx, *, items):
        author = ctx.message.author
        channel = ctx.channel
        #print(items)
        items = [i.strip() for i in items.split(',')]
        #print(items)
        if len(items) == 0:
            await channel.send(self.client.emotes['ames'])
            return
        await channel.send(f"{author.name}, I choose **{random.choice(items)}** "+self.client.emotes['ames'])

    @commands.group(invoke_without_command=True, aliases=['perm'])
    async def permissions(self, ctx):
        channel = ctx.message.channel
        author = ctx.message.author
        if ctx.invoked_subcommand is None:
            try:
                with open(os.path.join(self.client.dir, self.client.config['guild_perms_path'], f"{author.guild.id}.json")) as pf:
                    perms = json.load(pf)
            except:
                perms = None
            await channel.send(embed=self.make_perm_embed(author.guild, perms))
            
    def get_perm_member_s(self, guild, perm_id:int):
        temp = []
        for member in guild.members:
            if perm_id in [role.id for role in member.roles]:
                temp.append(member.name)
        return ", ".join(temp) if len(temp) > 0 else "No users with role"

    def make_perm_embed(self, guild, perms):
        embed = discord.Embed(
            title="User Permissions on Ames",
            description="Lists all role(s) that give the access to some of Ames' restricted commands.",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Permissions | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        for key, item in list(self.client.perms.items()):
            embed.add_field(
                name=f"> {key}",
                value=item['help'],
                inline=False
            )
            role_s = "No set role"
            if perms != None:
                if perms.get(key, None) != None:
                    role_s = f"{guild.get_role(perms[key]).name}({perms[key]})" if guild.get_role(perms[key]) != None else "No set role"

            embed.add_field(
                name="Roles",
                value=role_s,
                inline=True
            )
            embed.add_field(
                name="Members",
                value=self.get_perm_member_s(guild, perms.get(key, None) if perms != None else None),
                inline=True
            )
        return embed
  
    @permissions.command()
    async def set(self, ctx, perm:str=None, role:discord.Role=None):
        channel = ctx.message.channel
        author = ctx.message.author

        # check
        if not self.client._check_author(author, "admin"):
            await channel.send("Missing [admin] permission "+self.client.emotes['ames'])
            return
        elif not perm in list(self.client.perms.keys()):
            await channel.send(f"{perm} is not a valid permission key - user `.perm` to see all available permissions.")
            return
        elif perm == None or role == None:
            await channel.send(f"Missing one or more inputs")
            return

        try:
            with open(os.path.join(self.client.dir, self.client.config['guild_perms_path'], f"{author.guild.id}.json")) as pf:
                perms = json.load(pf)
        except:
            perms = dict()
        
        if perms.get(perm, None) == None:
            msg = await channel.send(f"Assigning `{role.name}` to perm `{perm}`...")
        else:
            msg = await channel.send(f"Replacing perm `{perm}` role with `{role.name}`...")
        perms[perm] = role.id

        try:
            with open(os.path.join(self.client.dir, self.client.config['guild_perms_path'], f"{author.guild.id}.json"), "w+") as pf:
                    pf.write(json.dumps(perms,indent=4))
        except Exception as e:
            await self.logger.send(self.name, e)
            await msg.edit(content=msg.content+"Failed")
            return
        else:
            await msg.edit(content=msg.content+"Success")
        
    @permissions.command(aliases=['rm', 'clear', 'c'])
    async def remove(self, ctx, perm:str):
        channel = ctx.message.channel
        author = ctx.message.author

        # check
        if not self.client._check_author(author, "admin"):
            await channel.send("Missing [admin] permission "+self.client.emotes['ames'])
            return
        elif not perm in list(self.client.perms.keys()):
            await channel.send(f"{perm} is not a valid permission key - user `.perm` to see all available permissions.")
            return

        try:
            with open(os.path.join(self.client.dir, self.client.config['guild_perms_path'], f"{author.guild.id}.json")) as pf:
                perms = json.load(pf)
        except:
            perms = dict()
        
        msg = await channel.send(f"Clearing role from perm `{perm}`...")
        perms[perm] = None

        try:
            with open(os.path.join(self.client.dir, self.client.config['guild_perms_path'], f"{author.guild.id}.json"), "w+") as pf:
                    pf.write(json.dumps(perms,indent=4))
        except Exception as e:
            await self.logger.send(self.name, e)
            await msg.edit(content=msg.content+"Failed")
            return
        else:
            await msg.edit(content=msg.content+"Success")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        if user.bot:
            return
        elif not self.client.command_status['pin']:
            return

        guild_id =      payload.guild_id
        channel_id =    payload.channel_id
        message_id =    payload.message_id
        user_id =       user.id

        try:
            message = await self.client.get_guild(guild_id).get_channel(channel_id).fetch_message(message_id)
        except:
            traceback.print_exc()
            return
        with open(os.path.join(self.client.dir, self.client.config['pins_path'])) as pf:
            pins = json.load(pf)
        if payload.emoji.name == "\U0001F4CC" and not message.pinned and not guild_id in pins.get('no_pin', []):
            if not str(guild_id) in pins:
                pins[str(guild_id)] = []

            # try to pin the message
            try:
                await message.pin()
            except:
                traceback.print_exc()
                return
            else:
                pins[str(guild_id)].append({"channel_id":channel_id,"message_id":message_id,"user_id":user_id})
                with open(os.path.join(self.client.dir, self.client.config['pins_path']), "w+") as pf:
                    pf.write(json.dumps(pins,indent=4))
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        if user.bot:
            return
        elif not self.client.command_status['pin']:
            return

        guild_id =      payload.guild_id
        channel_id =    payload.channel_id
        message_id =    payload.message_id
        user_id =       user.id

        try:
            message = await self.client.get_guild(guild_id).get_channel(channel_id).fetch_message(message_id)
        except:
            traceback.print_exc()
            return

        with open(os.path.join(self.client.dir, self.client.config['pins_path'])) as pf:
            pins = json.load(pf)
        if payload.emoji.name == "\U0001F4CC" and message.pinned and not guild_id in pins.get('no_pin', []):    
            if not str(guild_id) in pins:
                return

            messages = list(filter(lambda x: x['message_id'] == message_id, pins[str(guild_id)]))
            if not messages:
                return
            
            pinned = messages[0]
            if not pinned['user_id'] == user_id and not self.client._check_author(user, "admin"):
                return

            # try to unpin the message
            try:
                await message.unpin()
            except:
                traceback.print_exc()
                return
            else:
                pins[str(guild_id)].pop(pins[str(guild_id)].index(pinned))
                with open(os.path.join(self.client.dir, self.client.config['pins_path']), "w+") as pf:
                    pf.write(json.dumps(pins,indent=4))

    @commands.command(aliases=['pin'])
    async def pins(self, ctx, option=""):
        channel = ctx.channel
        author = ctx.message.author
        guild_id = ctx.message.guild.id

        if not self.client.command_status['pin']:
            raise commands.DisabledCommand
        elif not self.client._check_author(author, "admin"):
            await channel.send(self.client.emotes['ames'])
        
        with open(os.path.join(self.client.dir, self.client.config['pins_path'])) as pf:
            all_pins = json.load(pf)
        
        if not all_pins.get('no_pin', None):
            all_pins['no_pin'] = []
        
        if not option:
            await channel.send(f"Ames `{'can' if not guild_id in all_pins['no_pin'] else 'cannot'}` pin messages via react")
        elif option.isnumeric():
            option = int(option)
            if option == 0:
                if not guild_id in all_pins['no_pin']:
                    all_pins['no_pin'].append(guild_id)
                    await channel.send("Disallow Ames to pin messages via react")
                else:
                    await channel.send("Ames already cannot pin messages via react")
            elif option == 1:
                if guild_id in all_pins['no_pin']:
                    all_pins['no_pin'].pop(all_pins['no_pin'].index(guild_id))
                    await channel.send("Allow Ames to pin messages via react")
                else:
                    await channel.send("Ames already can pin messages via react")
        elif option.lower().startswith('p'):
            i = 0
            for guild_id, pins in list(all_pins.items()):
                if guild_id.isnumeric():
                    temp = pins.copy()
                    for pin in pins:
                        try:
                            message = await self.client.get_guild(int(guild_id)).get_channel(pins['channel_id']).fetch_message(pins['message_id'])
                            if not message.pinned:
                                temp.pop(temp.index(pin))
                                i += 1
                        except:
                            temp.pop(temp.index(pin))
                            i += 1
                        
                    all_pins[guild_id] = temp

            await channel.send(f"Pruned {i} pins from tracker")

        with open(os.path.join(self.client.dir, self.client.config['pins_path']), "w+") as pf:
            pf.write(json.dumps(all_pins,indent=4))

def setup(client):
    client.add_cog(coreCog(client))
