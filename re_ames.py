# dependencies
import datetime, time
import os, sys, traceback
import ast, aiohttp
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
        self.config[config] = status
        with open('commands/_config/active_cmd.txt', 'w') as cmdf:
            cmdf.write(str(self.config))
        return True
    
    def update_cogs_status(self, cog, status:bool):
        self.cogs_status[f"commands.cog_{cog}"] = status
        if status:
            self.load_extension(f"commands.cog_{cog}")
        else:
            self.unload_extension(f"commands.cog_{cog}")
    
    def reload_cog(self, cog):
        if not self.cogs_status[f"commands.cog_{cog}"]:
            return
        else:
            self.unload_extension(f"commands.cog_{cog}")
            self.load_extension(f"commands.cog_{cog}")
    
    def get_cogs_status(self):
        return self.cogs_status

    def load_resource(self):
        servers = [613628290023948288,613628508689793055,639337169508630528]
        team = dict()
        for server in servers:
            for emj in super().get_guild(server).emojis:
                team[emj.name] = f"<:{emj.name}:{emj.id}>"
        self.team = team

    async def on_ready(self):
        self.init_time = datetime.datetime.utcnow()
        self.s_time = time.time()
        await self.database.connect()
        self.load_resource()
        print(f'Ready: {self.user} (ID: {self.user.id})')
        await self.log.send(self.name,'I\'m back!')

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
        except:
            pass
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

if __name__ == "__main__":
    AmesBot = Ames()
    AmesBot.run()