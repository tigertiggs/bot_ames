import discord
from discord.ext import commands
import datetime, time, os, sys, requests, random, ast
dir = os.path.dirname(__file__)

def compare(client):
    git = 'https://raw.githubusercontent.com/tigertiggs/bot_ames/master/version'
    c = client.version
    o = str(requests.get(git).text)
    c_num = [int(v) for v in c.split('.')]
    o_num = [int(v) for v in o.split('.')]
    update_status = [x - y for x,y in list(zip(o_num, c_num))]
    for num in update_status:
        if num > 0:
            return '{0:s} (update available: {1:s})'.format(c,o)
        elif num < 0:
            return '{0:s} {1:s}'.format(c, '(Unstable)')
        else:
            continue
    return f"{c} (current)"

class statusCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = client.log
        self.name = '[Status]'
        #self.active = client.config.get('status',True)
        self.emj = client.emj

    async def active_check(self, channel):
        if self.client.get_config('status') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True

    @commands.command(
        usage='.status',
        aliases=['toirland'],
        help='Use this to get Ames\' current status.',
        hidden=False
        )
    async def status(self, ctx):
        channel = ctx.channel
        #author = ctx.author
        check = await self.active_check(channel)
        if not check:
            return
        with open(os.path.join(dir,'status.txt')) as stf:
            st = [line.strip() for line in stf]
        s_time = self.client.s_time
        #init_time = self.client.init_time
        cogs =          self.client.get_cogs_status().keys()
        state =         self.client.get_cogs_status().values()
        uptime =        str(datetime.timedelta(seconds=int(round(time.time() - s_time))))
        num_guilds =    len(self.client.guilds)
        try:
            conn = self.client.database.db_pointer.get_connection()
        except Exception as e:
            await self.logger.send(e)
        v = compare(self.client)
        
        embed = discord.Embed(
            title="Status",
            description=random.choice(st),
            timestamp=datetime.datetime.utcnow()
            )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text="Status | SHIN Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name='Version',
            value=v,
            inline=False
        )
        embed.add_field(
            name="Uptime",
            value=uptime,
            inline=True
        )
        embed.add_field(
            name="Database",
            value='Connected' if conn.is_connected() else 'Disconnected',
            inline=True
        )
        embed.add_field(
            name='Latency',
            value='{}ms'.format(int(self.client.latency*1000)),
            inline=True
        )
        embed.add_field(
            name="Guilds",
            value=str(num_guilds),
            inline=True
        )
        embed.add_field(
            name='Command Group',
            value='\n'.join([item.split('.')[1] for item in cogs]),
            inline=True
        )
        embed.add_field(
            name='Status',
            value='\n'.join(['Loaded' if status else 'Not Loaded' for status in state]),
            inline=True
        )
        await channel.send(embed=embed)
    
    @commands.command(
        usage='.ping',
        help='Get Ames\' current latency in milliseconds.',
        hidden=False
    )
    async def ping(self, ctx):
        channel = ctx.channel
        check =  await self.active_check(channel)
        if not check:
            return
        t1 = time.perf_counter()
        pong = await channel.send(self.client.emj['ames'])
        t2 = time.perf_counter()
        await pong.edit(content='{} ({}ms)'.format(self.client.emj['ames'], round((t2-t1)*1000)))
    
    @commands.command(
        hidden=True,
        usage='.kill',
        aliases=['kys'],
        help='Bury Ames.'
    )
    async def kill(self,ctx):
        channel = ctx.channel
        if ctx.message.author.id != 235361069202145280:
            await channel.send(self.emj['ames'])
            return
        else:
            await channel.send('I\'ll be right back! '+self.emj['sarenh'])
            await self.logger.send(self.name, 'shutting down...')
            await self.client.close()
            return

    @commands.command(
        hidden=True,
        usage='.purge [depth=100]',
        help='Look through [depth] most recent messages in the current channel and delete Ames\' messages.'
    )
    async def purge(self, ctx, depth:int=100):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        
        def is_me(message):
            return message.author == self.client.user
        
        await channel.purge(limit=depth, check=is_me)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        elif self.client.user in message.mentions:
            await message.channel.send(self.client.emj['ames'])

def setup(client):
    client.add_cog(statusCog(client))