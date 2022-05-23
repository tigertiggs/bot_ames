from operator import ne
import nextcord, math, random, traceback
from nextcord.ext import commands
import datetime, time, json, requests
import utils as ut
import templates as tem

class coreCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name   = '[core]'
        self.logger = ut.Ames_logger(self.name, self.client.Log)
        self.logger.init_client(self.client)

    def compare_version(self):            
        flag    = 0
        keys    = ['major', 'update', 'patch']
        clientv = ".".join([str(self.client.version[p]) for p in keys])
        try:
            git_version = json.loads(requests.get(self.client.version['tracker']).text)
        except:
            return clientv, "(check failed)"
        
        gitv = ".".join([str(git_version[p]) for p in keys])
        
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

    @commands.command(
        aliases=['toirland']
    )
    async def status(self, ctx):
        RED                 = ':red_circle:'
        GREEN               = ':green_circle:'
        nguilds             = str(len(self.client.guilds))
        uptime              = str(datetime.timedelta(seconds=int(round(time.time() - self.client.s_time))))
        clientv, updatemsg  = self.compare_version()

        status_embed_dict = {
            'title': 'Status',
            'descr': 'Ames is a utility bot made for *Princess Connect! Re:Dive* by *CyGames*. Currently under overhaul.',
            'thumb': self.client.user.avatar.url,
            'footer': {'text': ' | '.join(['Status', self.client.footer])},
            'fields': [
                {
                    'name': 'Developer',
                    'value': 'tigertiggs#5376'
                },
                {
                    'name': 'Version',
                    'value': ' '.join([clientv, updatemsg]),
                    'inline': True
                },
                {
                    'name': 'Uptime',
                    'value': uptime,
                    'inline': True
                },
                {
                    'name': 'Bot Latency',
                    'value': '{}ms'.format(int(self.client.latency*1000)),
                    'inline': True
                },
                {
                    'name': 'Guilds',
                    'value': nguilds,
                    'inline': True
                }
            ]
        }
        cmd_status_embed_dict = {
            'title' : 'Cog Status',
            'footer': {'text': ' | '.join(['Cog Status', self.client.footer])},
            'fields': []
        }
        cog_status = list(self.client.cog_status.items())
        cog_status.sort(key=lambda x: x[0])
        cog_status = [" ".join([GREEN if v else RED, k.split('.')[-1]]) for k,v in list(cog_status)]
        splice = math.ceil(len(cog_status)/3)
        for chunk in ut.chunks(cog_status, splice if splice > 5 else len(cog_status)):
            cmd_status_embed_dict['fields'].append(
                {
                    'name'  : 'status:cog',
                    'value' : "\n".join(chunk),
                    'inline': True
                }
            )
        embeds = {
            'ames': ut.embed_contructor(**status_embed_dict),
            'cog': ut.embed_contructor(**cmd_status_embed_dict)
        }

        response = self.statusPage(ctx, embeds, self.statusPageView(60, self.client.config))
        await response.start()

    class statusPage(ut.basePageHandler):
        def __init__(self, ctx, embed_dict, view):
            self.ctx            = ctx
            self.embeds         = embed_dict
            self.view           = view
            self.mode           = 'ames'

            super().__init__(ctx.channel)
            self.view.pass_pageHandler(self)

        async def start(self):
            await super().main_message_send(embed=self.embeds[self.mode], view=self.view)
    
    class statusPageView(ut.baseViewHandler):
        def __init__(self, timeout, config):
            super().__init__(timeout)
            self.base_id = 'ames_statusPageView_'
            self.config = config
            self.make_buttons_static()

        def make_buttons_static(self):
            button_gh_repo = nextcord.ui.Button(
                #custom_id=self.base_id+'git',
                url=self.config['REPO_LINK'],
                label="Github Repo",
                emoji="🖥️"
            )
            button_join_dev = nextcord.ui.Button(
                #custom_id=self.base_id+'dev',
                url=self.config['DEV_SERVER_INVITE'],
                label="Join Ames Dev Server"
            )
            button_toggle_status = nextcord.ui.Button(
                custom_id=self.base_id+"toggle",
                label="Toggle Ames/Cog"
            )
            self.buttons_static = [
                button_toggle_status,
                button_gh_repo,
                button_join_dev
            ]
            for button in self.buttons_static:
                super().add_item(button)

        async def interaction_check(self, interaction:nextcord.Interaction):
            #print(interaction.data)
            #print(self.children)
            inter_id = interaction.data.get('custom_id', None)
            if inter_id == self.base_id+'toggle':
                if self.pageHandler.mode == 'ames':
                    self.pageHandler.mode = 'cog'
                else:
                    self.pageHandler.mode = 'ames'
                
                await interaction.message.edit(embed=self.pageHandler.embeds[self.pageHandler.mode])
            return True
    
    @commands.command()
    async def ping(self, ctx):
        t1 = time.perf_counter()
        pong = await ctx.send(self.client.emotes['ames'])
        t2 = time.perf_counter()
        await pong.edit(content='{} pong! ({}ms)'.format(self.client.emotes['ames'], round((t2-t1)*1000)))

    @commands.command()
    async def purge(self, ctx, depth:int=100):
        if not self.client.check_perm(ctx.message.author, "admin"):
            await ctx.send("Missing [ames_admin] permission "+self.client.emotes['ames'])
            return
        await ctx.message.delete()
        def is_me(message):
            return message.author == self.client.user
        await ctx.channel.purge(limit=depth, check=is_me)
    
    @commands.command(aliases=['kys'])
    async def kill(self, ctx):
        channel = ctx.channel
        if not self.client.check_perm(ctx.message.author):
            await channel.send(self.client.emotes['amesyan'])
        else:
            await channel.send("I'll be right back "+self.client.emotes['derp'])
            await self.client.close()

    @commands.command()
    async def debug(self, ctx, val:int):
        channel = ctx.channel
        if not self.client.check_perm(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return

        if val not in [0, 1]:
            return
        
        self.client.config['debug'] = val
        if val == 1:
            await self.logger.report(self.name, "Ames now in debug mode")
        else:
            await self.logger.report(self.name, "Ames exiting debug mode")
        
        await channel.send("Changed debug state")

    @commands.command()
    async def invite(self, ctx):
        channel = ctx.message.channel
        msg = f"Looking to add Ames to your server? Here's the link:\n{self.client.config['ADD_BOT_LINK']}\nGot feedback? You can pop them in her development server:\n{self.client.config['DEV_SERVER_INVITE']}"
        await channel.send(msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        elif self.client.user in message.mentions:
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
                        ctx.invoked_with = messagev[1]
                        await ctx.invoke(cmd, *messagev[2:])
                        return

            await message.channel.send(self.client.emotes['ames'])

    @commands.command()
    async def choose(self, ctx, *, items):
        author = ctx.message.author
        channel = ctx.channel
        items = [i.strip() for i in items.split(',')]
        if len(items) == 0:
            await channel.send(self.client.emotes['ames'])
            return
        await channel.send(f"{author.name}, I choose **{random.choice(items)}** "+self.client.emotes['ames'])

    @commands.command(aliases=['ava','icon','dp', 'banner'])
    async def avatar(self, ctx, user=None):
        channel=ctx.message.channel
        author=ctx.message.author

        banner = False
        if ctx.invoked_with == 'banner':
            banner = True
        print('here')
        if user:
            target = await self.client.process_user(ctx, user, False)
            if target == False:
                return
            else:
                active = target
        else:
            active = await self.client.fetch_user(author.id)

        url = str(active.display_avatar) if not banner else str(active.banner.with_size(2048))
        embed = ut.embed_contructor(
            **{
                'author': {
                    'text': f'{active.name}#{active.discriminator}',
                    'url': url
                },
                    'footer': {
                    'text': 'Avatar' if not banner else 'Banner', 
                    'url': self.client.user.display_avatar
                },
                'image': url if url else ut.EMPTY
            }
        )
        await channel.send(embed=embed)

    @commands.command(aliases=['refresh'])
    async def reload(self, ctx, cog):
        channel = ctx.channel 
        if not self.client.check_perm(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return
        else:
            await channel.send(f"Attempting to reload {cog}")
        
        # perform checks
        loaded = True
        if not cog in [seg.split('_')[-1] for seg in list(self.client.cog_status.keys())]:
            await channel.send(f"Did not find {cog} in registered cogs")
            return
        elif cog == 'core':
            await channel.send("Cannot modify core")
            return
        elif not self.client.cog_status[f"{self.client.config['cog_prefix_full']}{cog}"]:
            await channel.send(f"{cog} is not loaded - attempting to load instead")
            loaded = False
        else:
            try:
                if loaded:
                    self.client.unload_extension(f"{self.client.config['cog_prefix_full']}{cog}")
                self.client.load_extension(f"{self.client.config['cog_prefix_full']}{cog}")
            except Exception as e:
                await self.logger.send(self.name, e)
                await channel.send("Something wrong happened - check logs")
                self.client.cog_status[f"{self.client.config['cog_prefix_full']}{cog}"] = 0
                return
            else:
                self.client.cog_status[f"{self.client.config['cog_prefix_full']}{cog}"] = 1
                await channel.send("Reloaded!")
                await self.logger.send(self.name, f"reloaded commands.cog_{cog}")

    @commands.group(invoke_without_command=True, aliases=['perm', 'perms'])
    async def permissions(self, ctx):
        channel = ctx.message.channel
        author = ctx.message.author
        if ctx.invoked_subcommand is None:
            await channel.send(embed=ut.embed_contructor(**self.make_perm_embed(author.guild)))

    def get_perm_member_s(self, guild, perm_id:int):
        temp = []
        for member in guild.members:
            if perm_id in [role.id for role in member.roles]:
                temp.append(member.name)
        return "\n".join(sorted(temp)) if len(temp) > 0 else "No users with role"

    def make_perm_embed(self, guild):
        embed = {
            'title': "User Permissions on Ames",
            'descr': "Lists all role(s) that give the access to some of Ames' restricted commands.",
            'footer': {'text': 'Permissions'},
            'fields': []
        }
        # load perms
        try:
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{guild.id}.json")) as pf:
                    cf = json.load(pf)
        except:
            cf = {}

        for perm_pos in self.client.config['perm_positions']:
            key = 'role_'+perm_pos
            role = guild.get_role(cf[key])
            role = '???(Role not found)' if role is None else f"<@&{role.id}>"
            embed['fields'].append(
                {
                    'name': f"{perm_pos}" if cf.get(key, None) else f"{perm_pos} (no role set)",
                    'value': f"> {role}\n"+self.get_perm_member_s(guild, cf.get(key, None)),
                    'inline': False
                }
            )

        return embed
    
    @permissions.command()
    async def set(self, ctx, role:nextcord.Role=None, position='admin'):
        author = ctx.author
        channel = ctx.channel

        # check if user has perms
        if not self.client.check_perm(author, 'admin'):
            await channel.send("you do not have permission to set perms")
            return
        elif role is None:
            await channel.send('No input')
            return
        elif not position in self.client.config['perm_positions']:
            await channel.send('Invalid role position')
            return
        elif not isinstance(role, nextcord.Role):
            await channel.send('Invalid role')
            return
        
        # load perms
        try:
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json")) as pf:
                guild = json.load(pf)
        except:
            guild = tem.fetch('guild')
            guild['id'] = author.guild.id

        # set new role
        key = 'role_'+position
        if guild[key] != None:
            await channel.send(f'Set {position} role as `{role.name}({role.id})`')
        else:
            await channel.send(f'Replaced {position} role as `{role.name}({role.id})`')
        guild[key] = role.id

        # save guild config
        with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json"), 'w+') as pf:
            pf.write(json.dumps(guild, indent=4))
            await channel.send('Saved')
    
    @permissions.command(aliases=['rm'])
    async def remove(self, ctx, position=None):
        author = ctx.author
        channel = ctx.channel

        # check if user has perms
        if not self.client.check_perm(author, 'admin'):
            await channel.send("you do not have permission to remove perms")
            return
        elif position is None:
            await channel.send('No input')
            return
        elif not position in self.client.config['perm_positions']:
            await channel.send('Invalid role position')
            return
        
        # load perms
        try:
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json")) as pf:
                    guild = json.load(pf)
        except:
            guild = tem.fetch('guild')
            guild['id'] = author.guild.id

        key = 'role_'+position
        guild[key] = None
        # save guild config
        with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json"), 'w+') as pf:
            pf.write(json.dumps(guild, indent=4))
            await channel.send(f'Reset {position} role')
        
    @commands.command(aliases=['pin'])
    async def pins(self, ctx, *, options):
        channel = ctx.channel
        author = ctx.author
        options = options.split()

        # load pins
        try:
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json")) as pf:
                guild = json.load(pf)
        except:
            guild = tem.fetch('guild')
            guild['id'] = author.guild.id
        
        pins_cf = guild['pins']
        
        if not options:
            if not pins_cf['active']:
                await channel.send('Ames cannot pin messages via react anywhere in this server')
            elif channel.id in pins_cf['no_pin']:
                await channel.send('Ames cannot pin messages via react in this channel')
            else:
                await channel.send('Ames can pin messages via react in this channel')
            return
        
        if not self.client.check_perm(author, 'admin'):
            await channel.send('You do not have permission to set pins')
            return
        
        if len(options) > 1 and options[1] == 'all':
            glob = True
        else:
            glob = False
        option = options[0].lower()

        if option in ['on', '1']:
            if glob:
                await channel.send('Allowing Ames to pin messages via react everywhere (including this channel)')
                pins_cf['active'] = True
            else:
                await channel.send('Allowed Ames to pin messages via react in this channel')
            try:
                ind = pins_cf['no_pin'].index(channel.id)
                pins_cf['no_pin'].pop(ind)
            except ValueError:
                pass
        elif option in ['off', '0']:
            if glob:
                await channel.send('Disallowing Ames to pin messages via react everywhere (including this channel)')
                pins_cf['active'] = False
            else:
                await channel.send('Disallowing Ames to pin messages via react in this channel')
            pins_cf['no_pin'].append(channel.id)
        else:
            await channel.send('Invalid input(s)')
            return
        
        guild['pins'] = pins_cf
        with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json"), 'w+') as pf:
            pf.write(json.dumps(guild, indent=4))
            await channel.send('Saved')
       
    def pin_validator(self, payload):
        user = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        channel_id =    payload.channel_id
        try:
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{user.guild.id}.json")) as pf:
                guild = json.load(pf)
        except:
            return False

        if user.bot:
            return False
        elif payload.emoji.name != "\U0001F4CC":
            return False
        elif not guild['pins']['active']:
            return False
        elif channel_id in guild['pins']['no_pin']:
            return False
        else: 
            return True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.pin_validator(payload):
            return
        try:
            channel = self.client.get_guild(payload.guild_id).get_channel(payload.channel_id)
            if not channel: 
                channel = self.client.get_guild(payload.guild_id).get_thread(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        except:
            traceback.print_exc()
            return
        else:
            if not message.pinned:
                await message.pin()
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not self.pin_validator(payload):
            return
        try:
            channel = self.client.get_guild(payload.guild_id).get_channel(payload.channel_id)
            if not channel: 
                channel = self.client.get_guild(payload.guild_id).get_thread(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        except:
            traceback.print_exc()
            return
        else:
            if message.pinned:
                await message.unpin()
        
    @commands.command(aliases=['welc'])
    async def welcome(self, ctx, onoff=None, target_channel=None):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        #options = options.split()

        # load cf
        try:
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json")) as pf:
                guild = json.load(pf)
        except:
            guild = tem.fetch('guild')
            guild['id'] = author.guild.id
        
        welc_cf = guild['welcome']

        if not (onoff or target_channel):
            if welc_cf['channel']:
                target_channel = guild.get_channel(welc_cf['channel'])
                if target_channel:
                    welc_channel = f"is bound to <#{welc_cf['channel']}>"
                else:
                    welc_channel = "is bound to an unknown channel"
            else:
                welc_channel = "is not bound to a channel"

            await channel.send(f"Welcoming message is {'active' if welc_cf['active'] else 'inactive'} and "+welc_channel)
            return
        else:
            onoff = onoff.lower()
            if onoff in ['on', '1']:
                welc_cf['active'] = True
                active_msg = 'Welcoming message is now active'
            elif onoff in ['off', '2']:
                welc_cf['active'] = False
                active_msg = 'Welcoming message is now inactive'
            else:
                await channel.send('Unknown first input')
                return
            
            if target_channel != None:
                if not target_channel.startswith('<#'):
                    await channel.send("Invalid channel input - either specified channel is invalid or a thread")
                    return
                
                welc_cf['channel'] = int(target_channel[2:-1])
                await channel.send(active_msg+f" and is bound to <#{welc_cf['channel']}>")
            else:
                await channel.send(active_msg)
            
            guild['welcome'] = welc_cf
            with open(ut.full_path(self.client.dir, self.client.config['configs']['guilds'], f"{author.guild.id}.json"), 'w+') as pf:
                pf.write(json.dumps(guild, indent=4))
                await channel.send('Saved')

def setup(client):
    client.add_cog(coreCog(client))