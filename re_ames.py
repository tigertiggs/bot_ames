# dependencies
import datetime, time
import os, sys, traceback
import ast, aiohttp, asyncio, random
import discord
from discord.ext.commands import Bot
from discord.ext import commands

# add ames dir into search path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, dir_path+'/commands')

# Ames bot config
import utility
BOT_PREFIX = (".")

def _prefix(client, msg):
    #
    # currently empty put is availble for expansion
    #
    return BOT_PREFIX

class Ames(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=_prefix,
            description=None,
            help_command=None
        )
        self.log = utility.logger(self)
        #self.session = aiohttp.ClientSession(loop=self.loop)
        self.name = '[Ames]'
        self.database = utility.database(self.log)
        self.BOT_PREFIX = BOT_PREFIX

        # load emojis
        with open('commands/_config/emoji.txt') as emjf:
            self.emj = ast.literal_eval(emjf.read())

        # load version
        with open('version') as vf:
            self.version = vf.read()

        # load config
        with open('commands/_config/active_cmd.txt') as cmdf:
            self.config = ast.literal_eval(cmdf.read())

        # load cogs
        self.cogs_status = dict()
        with open('cogs') as COGS:
            for extension in COGS:
                extension = extension.strip()
                try:
                    print('loading',extension)
                    self.load_extension(extension)
                except Exception as err:
                    print('{0} failed to load:'.format(str(extension)),err)
                    traceback.print_exc()
                    self.cogs_status[str(extension)] = False
                else:
                    self.cogs_status[str(extension)] = True 
        
        # final check
        self.check_init()

    def check_init(self):
        # check if commands/shen/post exists
        print('checking folders...')
        if not os.path.exists(os.path.join(dir_path,'commands/shen/post')):
            print('creating commands/shen/post...')
            try:
                os.makedirs(os.path.join(dir_path,'commands/shen/post'))
            except:
                traceback.print_exc()
        if not os.path.exists(os.path.join(dir_path,'commands/gacha/assets/units/png')):
            print('commands/gacha/assets/units/png...')
            try:
                os.makedirs(os.path.join(dir_path,'commands/gacha/assets/units/png'))
            except:
                traceback.print_exc()
        print('finshed!')
        # add more checks here

    def get_config(self, option):
        self.config[option] = self.config.get(option, True)
        return self.config[option]
    
    def get_full_config(self):
        return self.config

    def update_config(self, config, status:bool):
        #if config not in list(self.config.keys()):
        #    return False
        #else:
        #    self.config[config] = status

        # note that this does not perform the check that the config key requested is actually valid.
        # since its a dict the following will add the key nevertheless
        self.config[config] = status
        with open('commands/_config/active_cmd.txt', 'w') as cmdf:
            cmdf.write(str(self.config))
        return True
    
    async def reload_help(self):
        try:
            self.unload_extension('commands.cog_help')
            self.load_extension('commands.cog_help')
        except Exception as e:
            await self.log.send(self.name, 'Failed to refresh help cog', e)

    async def update_cogs_status(self, cog, status:bool):
        self.cogs_status[f"commands.cog_{cog}"] = status
        try:
            if status:
                self.load_extension(f"commands.cog_{cog}")
                await self.log.send(self.name, 'loaded', cog)
            else:
                self.unload_extension(f"commands.cog_{cog}")
                await self.log.send(self.name, 'unloaded', cog)
        except Exception as e:
            await self.log.send(self.name, 'failed to update cog status', e)
        finally:
            await self.reload_help()
    
    async def reload_cog(self, cog):
        if not self.cogs_status[f"commands.cog_{cog}"]:
            return
        else:
            try:
                self.unload_extension(f"commands.cog_{cog}")
                self.load_extension(f"commands.cog_{cog}")
            except Exception as e:
                await self.log.send(self.name, 'failed to reload', e)
            else:
                await self.log.send(self.name, 'reloaded', cog)
            finally:
                await self.reload_help()
    
    def get_cogs_status(self):
        return self.cogs_status

    def load_resource(self):
        servers = []
        with open('commands/_config/res.txt') as rf:
            for res_id in rf:
                servers.append(int(res_id))

        team = dict()
        for server in servers:
            for emj in super().get_guild(server).emojis:
                team[emj.name] = f"<:{emj.name}:{emj.id}>"

        self.team = team
        self.res_servers = servers
    
    def get_team(self):
        return self.team
    
    def team_append(self, name, id):
        self.team[name] = id

    async def on_ready(self):
        self.init_time = datetime.datetime.utcnow()
        self.s_time = time.time()
        await self.database.connect()
        self.load_resource()
        print(f'Ready: {self.user} (ID: {self.user.id})')
        await self.log.send(self.name,'I\'m back!')
        self.loop.create_task(self.st())

    async def on_guild_join(self, guild):
        await self.log.send(self.name, 'joined', guild.name)
        hello = self.emj['sarenh']+'Thanks for having me here!\nMy prefix is `.` - Please use `.help` to get started!'
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
        return
    
    async def process_commands(self, message):
        ctx = await self.get_context(message)
        #
        # currently empty put is availble for expansion
        #
        try:
            await self.invoke(ctx)
        except Exception as e:
            await self.log.send(self.name, 'failed to process command', e)
        finally:
            pass
            #await ctx.release()

    async def on_message(self,message):
        if message.author.bot:
            return
        elif message.content.startswith(BOT_PREFIX):
            await self.log.send('[{0.user.name}] `{1}` `{2.channel.guild.name}` `{2.channel.name}` `{2.author.name}` `{2.content}`'.format(
                self, datetime.datetime.now(), message))
            await self.process_commands(message)

    async def close(self):
        #await self.session.close()
        await super().close()

    def run(self):
        try:
            with open('commands/_pass/token') as tf:
                super().run(tf.read().strip(), bot=True, reconnect=True)
        except:
            traceback.print_exc()
    
    def error(self):
        error_msg = dict()
        error_msg['inactive'] = 'This command is currently disabled '+self.emj['maki']
        return error_msg

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
    
if __name__ == "__main__":
    AmesBot = Ames()
    AmesBot.run()