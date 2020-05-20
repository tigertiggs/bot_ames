# ReReAmes bot
# author: tigertiggs#5376
# 2nd rewrite for better expansion, automation and future proofing
# rewrite will try to add more comments should I drop the project

# ames prefix (do not touch)
BOT_PREFIX = (".")

# dependencies
import datetime, time
import os, sys, traceback
import aiohttp, asyncio, random, traceback, json
from difflib import SequenceMatcher as sm
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import mysql.connector
from mysql.connector import pooling
from mysql.connector import errorcode

# add ames_bot folder to the search path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, dir_path+'/commands')

# utility classes
class logger:
    def __init__(self, client):
        self.logc = None
        self.client = client
        self.private = client.private['ames_logger']
    
    async def send(self, *msg):
        if self.logc == None:   
            self.logc = self.client.get_guild(self.private['guild_id']).get_channel(self.private['channel_id'])
        try:
            await self.logc.send(" ".join([str(w) for w in msg]))
        except:
            pass

class database:
    def __init__(self, client, size=10):
        self.name =         '[database]'
        self.db_pointer =   None
        self.response =     None
        self.pool =         None
        self.pool_size =    size
        self.reset_conn =   True
        self.logger =       client.log
        self.private =      client.private['panda_database']
    
    async def connect(self):
        if self.db_pointer != None:
            await self.logger.send(self.name,'database is connected - forcing reconnect')
            #self.disconnect()
        try:
            self.db_pointer = mysql.connector.pooling.MySQLConnectionPool(
                pool_name =             'hatsune_pool',
                pool_size =             self.pool_size,
                pool_reset_session =    self.reset_conn,
                user =                  self.private['username'],
                password =              self.private['password'],
                host =                  self.private['host'],
                database =              self.private['db_name']
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                await self.logger.send(self.name,'connection failed - access denied')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                await self.logger.send(self.name,'connection failed - database does not exist')
            else:
                await self.logger.send(self.name,'connection failed - ',err)
            self.db_pointer = None
            return False
        else:
            await self.logger.send(self.name,'connection successful')
            return True
    
    def release(self, conn):
        #mysql.connector.pooling.PooledMySQLConnection(self.db_pointer, conn).close()
        conn.close()
    
    """
    def disconnect(self):
        if self.db_pointer == None:
            self.logger.send(self.name,'database already disconnected')
        else:
            try:
                self.db_pointer.close()
            except mysql.connector.Error as err:
                self.logger.send(self.name,'disconnection failed - ', err)
            else:
                self.logger.send(self.name,'disconnection successful')
    """

    async def execute(self, statement):
        conn = self.db_pointer.get_connection()
        if conn.is_connected(): 
            self.response = conn.cursor(buffered=True).execute(statement)
            return self.response
        else:
            await self.logger.send(self.name,'execution failed - could not connect')
    
    async def status(self):
        conn = self.db_pointer.get_connection()
        if conn.is_connected():
            info = conn.get_server_info()
            await self.logger.send(self.name,info)
        else:
            await self.logger.send(self.name,'server disconnected')

# for custom prefixes in different environments
def _prefix(client, message):
    #
    # currently empty but here for futureproofing
    #
    return BOT_PREFIX

# main
class Ames(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix= _prefix,
            description=    None,
            help_command=   None
        )
        self.name = "[Ames]"
        self.dir = dir_path
        self.prefix = BOT_PREFIX
        # load configs
        print(self.name, "starting")
        with open("commands/_config/amesconfig.json") as cf:
            self.config = json.load(cf)
            self.command_status = self.config['command_status']

        with open(self.config['emote_path']) as ef:
            self.emotes = json.load(ef)

        with open(self.config['private_path']) as pf:
            self.private = json.load(pf)

        with open('version') as vf:
            self.version = json.load(vf)
        
        # check bot_ames folder tree hierarchy
        self.init_success = self.__check_init()
        if not self.init_success:
            print('failure during initialisation - exiting')
            return
        
        # set logger and db
        self.log = logger(self)
        self.database = database(self)
        
        # load cogs
        self.cogs_status = dict()
        for extension in self.config['command_cogs']:
            try:
                print('loading',extension,end="")
                self.load_extension(extension)
                print('\tsuccess!',flush=True)
            except Exception as err:
                print('{0} failed to load:'.format(str(extension)),err,flush=True)
                traceback.print_exc()
                self.cogs_status[str(extension)] = False
            else:
                self.cogs_status[str(extension)] = True

    def __check_init(self):
        print(self.name, "checking critical folders and files")

        for path in self.config['required_folders']:
            print(self.name, "checking folder", path, "...", end="")

            full_path = os.path.join(dir_path, path)

            if not os.path.exists(full_path):
                print("\n", self.name, "creating", path, "...")

                try:
                    os.makedirs(full_path)
                except:
                    traceback.print_exc()
                    return False
            
            print("success", flush=True)
        
        for file in self.config['required_files']:
            print(self.name, "checking file", path, "...", end="")
        
            full_path = os.path.join(dir_path, path)

            if not os.path.exists(full_path):
                print("\n", self.name, "creating", path, "...", end="")

                try:
                    with open(full_path, "w+") as rf:
                        rf.write("{}")
                except:
                    traceback.print_exc()
                    return False 
            
            print("success", flush=True)

        return True

    # handy function to split list l into chunks of length n
    def chunks(self, l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n] 

    # for critical functions
    def _check_author(self, user):
        return user.id == 235361069202145280

    # load emote resources from servers
    def _load_resource(self):
        self.team = dict()
        self.res_servers = self.private['resource_servers']
        for server in self.res_servers:
            for emj in super().get_guild(server).emojis:
                self.team[emj.name] = f"<:{emj.name}:{emj.id}>"

    # set looping activity messages
    async def st(self):
        switchtime =    60*60
        playing =       0
        #streaming =     1
        #listening =     2
        #watching =      3
        default =       discord.Activity(name="Use .help",      type=discord.ActivityType(playing))
        act_list = [
            discord.Activity(name='with Hatsune',               type=discord.ActivityType(playing)),
            discord.Activity(name='with gacha rates',           type=discord.ActivityType(playing)),
            discord.Activity(name='PrincessConnectReDive',      type=discord.ActivityType(playing))
        ]
        while True:
            await self.change_presence(activity=default)
            await asyncio.sleep(switchtime)
            await self.change_presence(activity=random.choice(act_list))
            await asyncio.sleep(switchtime)

    async def on_ready(self):
        # uptime
        self.init_time = datetime.datetime.utcnow()
        self.s_time = time.time()

        # connect the database and grab resources
        await self.database.connect()
        self._load_resource()

        print(f'Ready: {self.user} (ID: {self.user.id})')
        if self.config['debug'] == 1:
            print('----Ames is in debug mode----')

        await self.log.send(self.name,'I\'m back!')

        self.loop.create_task(self.st())

    # welcome message
    async def on_guild_join(self, guild):
        await self.log.send(self.name, 'joined', guild.name)
        hello = self.emotes['sarenh']+'Thanks for having me here!\nMy prefix is `.` - Please use `.help` to get started!'
        general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
        if general != None and general.permissions_for(guild.me).send_messages:
            await general.send(hello)
            return
        else:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(hello)
                    return
        await self.log.send(self.name,'no available channel found!')
    
    async def process_commands(self, message):
        ctx = await self.get_context(message)
        #
        # currently empty put is availble for expansion
        #
        if self.config['debug'] == 1:
            if self._check_author(message.author):
                await self.log.send(str(ctx.command))
                await self.invoke(ctx)
            else:
                msg = await message.channel.send(f"Ames is currently MT/in debug and will be unresponsive {self.emotes['ames']}\nThis message will delete itself in `5s`")
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except:
                    pass

        else:
            try:
                if ctx.command != None:
                    await self.log.send('[{0.user.name}] `{1}` `{2.channel.guild.name}` `{2.channel.name}` `{2.author.name}` `{2.content}`'.format(
                        self, datetime.datetime.now(), message))
                await self.invoke(ctx)
            except Exception as e:
                await self.log.send(self.name, 'failed to process command', e)
            finally:
                pass
                #await ctx.release()

    # command listener
    async def on_message(self,message):
        if message.content.startswith(BOT_PREFIX) and not message.author.bot:
            if self.config['debug'] == 1 and self._check_author(message.author):
                await self.log.send('`[DEBUG MODE]` [{0.user.name}] `{1}` `{2.channel.guild.name}` `{2.channel.name}` `{2.author.name}` `{2.content}`'.format(
                    self, datetime.datetime.now(), message))
                await self.process_commands(message)
            else:
                await self.process_commands(message)

    # error handling
    async def on_command_error(self, ctx, error):
        #if debug == False:
        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)
        #print(error)
        #_errlog(ctx, str(error), __log)
        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.DisabledCommand):
            await ctx.channel.send(f"I\'m currently taking a break from this command {self.emotes['dead']} `(Command Disabled)`")
            await self.log.send(f"Disabled command: {ctx.command.name}")
            return
        elif isinstance(error, commands.CommandOnCooldown):
            msg = await ctx.channel.send(f"This command is on cd - reusuable in `{round(error.retry_after,1)}s`")
            await asyncio.sleep(error.retry_after)
            await msg.delete()
            return
        elif isinstance(error, discord.Forbidden):
            try:
                await ctx.channel.send(f"{self.emotes['ames']} I don\'t have the required permission(s) to perform/finish this command `(Missing Permissions)`")
            except Exception as e:
                await self.log.send("Failed to send error alert", ''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            await self.log.send(f"Ames is missing permissions in: {ctx.command.name}")
        else:
            await self.log.send('<@235361069202145280> command error in', ctx.command.name, f"```prolog\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```")

    async def close(self):
        #await super().session.close()
        #self.database.db_pointer.end()
        await self.log.send(self.name, 'shutting down')
        if self.config['save_config_on_exit'] == 1:
            await self.log.send(self.name, 'saving config')
            self.config['command_status'] = self.command_status
            try:
                with open('commands/_config/amesconfig.json', 'w') as config:
                    config.write(json.dumps(self.config, indent=4))
            except Exception as e:
                await self.log.send('failed', e)
            else:
                await self.log.send('success')
        await super().close()

    def run(self):
        if self.init_success:
            try:
                super().run(self.private['ames_core']['token'], bot=True, reconnect=True)
            except:
                traceback.print_exc()
    
    def error(self):
        error_msg = dict()
        error_msg['inactive'] = 'This command is currently disabled '+self.emotes['maki']
        return error_msg

    # utility classes
    class page_controller():
        def __init__(self, client, make_embed_func, data, chunk_length, index=False):
            self.arrows =   ['⬅','➡']
            self.make =     make_embed_func
            self.data =     data
            self.chunk_l =  chunk_length
            self.index =    index
            self.client =   client
            
            self.pages = []

            self.make_pages()
        
        def make_pages(self):
            chunk = list(self.client.chunks(self.data, self.chunk_l))
            total = len(chunk)

            for i, block in enumerate(chunk):
                if self.index:
                    self.pages.append(self.make(block, (i+1,total)))
                else:
                    self.pages.append(self.make(block))
        
        def start(self):
            return self.pages[0]
        
        def flip(self, mode='r'):
            if mode == 'r':
                self.pages = self.pages[1:] + [self.pages[0]]
            else:
                self.pages = [self.pages[-1]] + self.pages[:-1]
            
            return self.pages[0]

    # utility functions
    async def find_user(self, guild, user:str):
        members = guild.members

        # check if user is a discord id
        try:
            for tk in [">", "<", "@", "!"]:
                user = user.replace(tk,'')
            #print(user)
            user = guild.get_member(int(user))
        except Exception as e:
            await self.log.send(self.name, 'id mismatch', e)
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

    def get_full_name(self, target):
        with open(os.path.join(self.dir, self.config['hatsune_config_path'])) as hcf:
            hconfig = json.load(hcf)
        if len(target) > 1:
            if target[1].isupper():
                prefix = hconfig['prefix_title'].get(target[0].lower(), '???')
                return f"{target[1:]} ({prefix})"
        return target

if __name__ == "__main__":
    AmesBot = Ames()
    AmesBot.run()