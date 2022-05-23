# Ames Nextcord (ReReRe:Ames)
# Author: tigertiggs#5376
# A complete makeover for Ames after the discontinuation of the official Discord API's python library

import os, sys, datetime, time, json, asyncio, random, traceback
import nextcord, logging
from nextcord.ext import commands
from difflib import SequenceMatcher as sm

# add ames_bot folder to the search path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, dir_path+'/data')

import utils as ut

BOT_PREFIX      = '.'
START_TIME      = None
MAIN_CONFIG     = 'ames_config.json'
OVERRIDE_CONFIG = "ames_config_override.json"

# for custom prefixes in different environments
def _prefix(client, message):
    if message.guild:
        if message.guild.id == 202403448694505473:
            return ["a.", client.prefix]
    return client.prefix

class Ames_nextcord(commands.AutoShardedBot):
    def __init__(self):
        self.dir    = dir_path
        self._start_log()
        self.name   = '[Ames_NC]'
        self.footer = 'Ames Nextcord'
        #self.prefix = BOT_PREFIX
        self.logger = ut.Ames_logger(self.name, self.Log)

        # read main config file
        self.logger.log('reading main config')
        with open(ut.full_path(self.dir, MAIN_CONFIG)) as cf:
            self.config = json.load(cf)

        # append private
        with open(ut.full_path(self.dir, self.config['private'])) as pcf:
            self.config.update(json.load(pcf))
        
        # override if necessary
        ocfp = ut.full_path(self.dir, OVERRIDE_CONFIG)
        if os.path.exists(ocfp):
            self.logger.log('override config found')
            with open(ocfp) as ocf:
                self.config.update(json.load(ocf))

        self.prefix = self.config['bot_prefix']

        # version
        with open(ut.full_path(self.dir, self.config['version'])) as vf:
            self.version = json.load(vf)

        # init parent
        super().__init__(
            command_prefix  = _prefix,
            description     = "PCRD Utility Bot",
            help_command    = None,
            intents         = nextcord.Intents(**self.config['intents'])
        )

        # read other configs
        self._read_configs()

    def _start_log(self):
        self.Log    = logging.getLogger('nextcord')
        self.Log.setLevel(logging.DEBUG)
        handler     = logging.FileHandler(filename=ut.full_path(self.dir, 'ames_nextcord.log'), encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.Log.addHandler(handler)

    def _read_configs(self):
        self.logger.log('reading other configs')
        configs = self.config['configs']

        # emote shortcuts
        with open(ut.full_path(self.dir, configs['emotes'])) as ecf:
            self.emotes = json.load(ecf)
            self.logger.log('loaded emotes')
        
        # server scopes
        with open(ut.full_path(self.dir, configs['server_scope'])) as sccf:
            self.server_scopes = json.load(sccf)
            self.logger.log('loaded server scopes')
        
    def _load_cogs(self):
        self.logger.log('loading cogs')
        self.cog_status = {}
        for cog, enabled in self.config['cogs'].items():
            status = False
            if enabled:
                try:
                    self.load_extension(cog)
                except Exception as e:
                    self.logger.log(f"failed to load {cog}")
                    print(traceback.print_exc())
                else:
                    self.logger.log(f"successfully loaded {cog}")
                    status = True
            else:
                self.logger.log(f"{cog} not loaded: is disabled")
            
            self.cog_status[cog] = status

    def check_perm(self, user, mode='admin'):
        if user.id in self.config['developers']:
            return True

        if mode == "admin":
            # server owner always have admin perm
            if user.guild.owner == user:
                return True
            # check if user has perm role
            try:
                with open(ut.full_path(self.dir, self.config['configs']['guilds'], f"{user.guild.id}.json")) as c:
                    cf = json.loads(c.read())
            except:
                #cf = tem.fetch('guild')
                #cf['id'] = user.guild.id
                #with open(ut.full_path(self.dir, self.config['guilds'], f"{user.guild.id}.json"), 'w+') as c:
                #    c.write(json.dumps(cf, indent=4))
                return False
            else:
                for role in user.roles:
                    if role.id == cf['role_admin']:
                        return True
                return False
            
        else:
            return False

    # set looping activity messages
    async def st(self):
        switchtime =    60*60
        playing =       0
        #streaming =     1
        #listening =     2
        #watching =      3
        default =       nextcord.Activity(name="Use .help",      type=nextcord.ActivityType(playing))
        act_list = [
            nextcord.Activity(name='with Hatsune',               type=nextcord.ActivityType(playing)),
            nextcord.Activity(name='with gacha rates',           type=nextcord.ActivityType(playing)),
            nextcord.Activity(name='PrincessConnectReDive',      type=nextcord.ActivityType(playing))
        ]
        while True:
            await self.change_presence(activity=default)
            await asyncio.sleep(switchtime)
            await self.change_presence(activity=random.choice(act_list))
            await asyncio.sleep(switchtime)

    async def on_ready(self):
        global START_TIME
        # uptime
        self.init_time  = datetime.datetime.utcnow()
        self.s_time     = START_TIME

        # init logger channel
        self.logger.init_client(self)

        # load res
        await self.hatsu_load_res()

        # load cogs
        self._load_cogs()

        ready_str = f'Ready: {self.user} (ID: {self.user.id})'
        await self.logger.report(ready_str)
        if self.config['debug'] == 1: 
            await self.logger.report('debug mode enabled')

        self.status_cycle = self.loop.create_task(self.st())

    async def process_commands(self, message, pf):
        ctx = await self.get_context(message)

        # check important commands
        #if ('kys' in message.content or 'kill' in message.content) and message.author.id in self.config['developers']:
        #    await message.channel.send("I'll be right back "+self.emotes['derp'])
        #    await self.close()
        #    return

        # process command
        cmd = ctx.command
        if cmd != None:
            cog_name = cmd.cog.qualified_name

            # check if the cog is actively disabled
            if cog_name in self.config['cogs_disabled']:
                raise commands.DisabledCommand
            
            # check if the cog is prohibited in the server
            if not isinstance(ctx.channel, nextcord.DMChannel):
                target_guild = str(ctx.message.guild.id)
                if target_guild in self.server_scopes:
                    if cog_name in self.server_scopes[target_guild]:
                        raise commands.DisabledCommand

            await self.invoke(ctx)
        else:
            # emote stuffs probs
            key = message.content[len(pf):]
            if key in self.emotes:
                await message.delete()
                await message.channel.send(self.emotes[key])
                return
            
    # welcome message when joining a guild
    async def on_guild_join(self, guild):
        await self.log.send(self.name, 'joined', guild.name)
        if guild.id == 598450517253029888:
            hello = self.emotes['sarenh']+'Thanks for having me here!\nMy prefix is `.` (but all blueoath commands will start with `.bo`) - Please use `.bo help` to get started!'
        else:
            hello = self.emotes['sarenh']+'Thanks for having me here!\nMy prefix is `.` - Please use `.help` to get started!'
        general = nextcord.utils.find(lambda x: x.name == 'general', guild.text_channels)
        if general != None and general.permissions_for(guild.me).send_messages:
            await general.send(hello)
            return
        else:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(hello)
                    return
        await self.log.send(self.name,'no available channel found!')
    
    # welcome message when a member joins a guild
    async def on_member_join(self, member):
        guild = member.guild

        # attempt to fetch welcome config
        try:
            with open(ut.full_path(self.dir, self.config['configs']['guids'], f"{guild.id}.json")) as gcf:
                guild_welcome = json.load(gcf).get("welcome", None)
        except:
            guild_welcome = None
        
        if not guild_welcome:
            return
        elif not guild_welcome.get("active", False):
            return
        elif not guild_welcome.get("channel", None):
            return
        elif not guild.get_channel(guild_welcome["channel"]):
            return
        else:
            ch = guild.get_channel(guild_welcome["channel"])
            if guild.id == 598450517253029888:
                text = f"Welcome to **{guild.name}**, <@!{member.id}>! I can fetch useful ship skills and stats from the Blue Oath EN Wiki, you can see my commands with `.bo help`\n(please) READ THE PINS, READ THE SHEETS, READ THE WIKI -Ladios"
            else:
                text = f"Welcome to **{guild.name}**, <@!{member.id}>! I'm a PCRD utility bot and you can see my commands with `.help`"
            
            await ch.send(text)

    # command listener
    async def on_message(self,message):
        pref = await self.get_prefix(message)
        if not isinstance(pref, list):
            pref = [pref]
            
        if not message.author.bot:
            for pf in pref:
                if message.content.startswith(pf):
                    if self.config['debug'] == 1:
                        if self.check_perm(message.author):
                            #print(message)
                            if message.guild:
                                await self.logger.report(message, pf)
                            await self.process_commands(message, pf)
                    else:
                        await self.process_commands(message, pf)

    def run(self):
        super().run(self.config['ames_core']['token'], reconnect=True)

    # error handling
    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)
        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.DisabledCommand):
            await ctx.channel.send(f"I\'m currently taking a break from this command {self.emotes['dead']} `(Command Disabled)`")
            await self.logger.report(f"Disabled command: {ctx.command.name}")
            return
        elif isinstance(error, commands.CommandOnCooldown):
            msg = await ctx.channel.send(f"This command is on cd - reusuable in `{round(error.retry_after,1)}s`")
            await asyncio.sleep(error.retry_after)
            await msg.delete()
            return
        elif isinstance(error, nextcord.Forbidden):
            try:
                await ctx.channel.send(f"{self.emotes['ames']} I don\'t have the required permission(s) to perform/finish this command `(Missing Permissions)`")
            except Exception as e:
                await self.logger.report("Failed to send error alert", ''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            await self.logger.report(f"Ames is missing permissions in: {ctx.command.name}")
        else:
            await self.logger.report('<@235361069202145280> command error in', ctx.command.name, f"```prolog\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```")

    async def close(self):
        # clean up
        await super().close()

    # utility functions that needs a client
    async def find_user(self, guild, user:str):
        members = guild.members

        # check if user is a discord id
        try:
            for tk in [">", "<", "@", "!"]:
                user = user.replace(tk,'')
            user = await self.fetch_user(int(user))
            print('banner', user.banner)
        except Exception as e:
            await self.logger.send(self.name, 'id mismatch', e)
        else:
            return user
        
        # do string match
        # search name
        cutoff = 0.3
        user = user.lower()
        fname = list(filter(lambda x: sm(None, user, x.name.lower(), None).ratio() >= cutoff and user in x.name.lower(), members))
        fnick = list(filter(lambda x: sm(None, user, x.nick.lower() if x.nick != None else '', None).ratio() >= cutoff and user in x.nick.lower(), members))
        if len(fname) != 0 and len(fnick) != 0:
            a = sm(None, user, fname[0].name, None).ratio()
            b = sm(None, user, fnick[0].nick, None).ratio()
            if a == b:
                return await self.fetch_user(fnick[0].id)
            elif a > b:
                return await self.fetch_user(fname[0].id)
            else:
                return await self.fetch_user(fnick[0].id)
        elif len(fname) != 0:
            return await self.fetch_user(fname[0].id)
        elif len(fnick) != 0:
            return await self.fetch_user(fnick[0].id)
        else:
            return None

    async def process_user(self, ctx, user, always_return:bool=True, ames=False):
        channel = ctx.channel
        if user != None:
            target = await self.find_user(ctx.guild, user)
            if target == None:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return False
            #check = await self.ames_check(target, channel)
            if ames:
                if await self.ames_check(user, channel):
                    return False
            user = target
        elif user == None and always_return:
            user = ctx.message.author
        elif user == None and not always_return:
            user = None
        else:
            await channel.send(self.emotes['ames'])
            return False
        return user

    async def ames_check(self, target, channel):
        if target == self.user:
            await channel.send(self.emotes['amesyan'])
            return True
        else:
            return False

    # loading various resources only possible after on_ready
    async def hatsu_load_res(self):
        server_ids = self.config['resource_servers']
        res = {}
        for id in server_ids:
            guild = await super().fetch_guild(id)
            for emote in guild.emojis:
                res[emote.name] = {
                    'name': emote.name,
                    'id': emote.id,
                    'full': f"<:{emote.name}:{emote.id}>"
                }
        
        self.hatsu_res = res

if __name__ == '__main__':
    START_TIME  = time.time()
    ames        = Ames_nextcord()
    ames.run()