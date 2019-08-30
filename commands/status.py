"""
Ames
status
"""
import discord
import datetime, time
import random
from misc import randcolour as rc

s1 = 'A checkup?'
s2 = 'Overtime again?'
s3 = 'I\'m not getting paid enough for this'
s4 = 'I can do with a coffee about now'

st = [s1,s2,s3,s4]

async def status(ctx, flags, client, s_time, cc):
    channel = ctx.channel
    author = client.user

    uptime = int(round(time.time() - s_time))
    uptime = str(datetime.timedelta(seconds=uptime))
    num_guilds = len(client.guilds)
    
    if flags['db_isconnected']: db = 'connected'
    else: db = 'disconnected'

    embed = discord.Embed(
        title="Status",
        description=random.choice(st),
        timestamp=datetime.datetime.utcnow(),
        colour=rc()
        )

    embed.set_thumbnail(url=author.avatar_url)

    embed.add_field(
        name="Uptime",
        value=uptime,
        inline=False)

    embed.add_field(
        name="Database",
        value=db,
        inline=False)
    
    embed.add_field(
        name="Guilds",
        value=str(num_guilds),
        inline=False)

    embed.add_field(
        name="Command Group",
        value="\n".join(list(cc.keys())),
        inline=True)

    embed.add_field(
        name="Active",
        value="\n".join([str(b) for b in list(cc.values())]),
        inline=True)

    await channel.send(embed=embed)

async def intro(guild, emj):
    print('joined', guild.name)
    hello = emj['sarenh']+'Thank\'s for having me here!\n'\
              'My prefix is `.` - Please use `.help` to get started!'
    
    general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
    
    if general != None and general.permissions_for(guild.me).send_messages:
        await general.send(hello)
        return
    else:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(hello)
                return

    print('no available channel found!')
    return













