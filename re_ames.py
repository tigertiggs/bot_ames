"""
Ames bot for Princonne - rewrite
Mostly developed to brush up on python3
Created by tiggs

Primary purpose is to log CB scoress

TODO:
.cb conclude(cb_id)
.cb quota(cb_id) - given warning on cb_concluded
"""
# DEPENDENCIES
import datetime, time
import asyncio

from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
import random

import discord
from discord.ext.commands import Bot
from discord.ext import commands

import mysql.connector
from mysql.connector import errorcode

import ast

# set local dir as cd for import
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
import sys
sys.path.insert(1, dir_path+'/commands')
sys.path.insert(1, dir_path+'/commands/CB')

# SUBHEADERS
from _help          import *
from connection     import *
import shen         as sh
import roll         as roll
import hatsune      as hatsune
import hatsune_new  as hatsune_new
import guide        as gd
from misc           import _log, _errlog
import spray        as sp
import dumb         as dumb
import entypol      as entypol
import muimi        as mmi

import prototype    as proto
import gulag        as redclan

import cb_help
from cb_init        import *
import pcb          as cb_pcb
import startday     as cb_startday
import removelog    as cb_removelog
import listlogs     as cb_listlogs
import reload       as cb_reload
import updatemember as cb_updatemember
import removemember as cb_removemember
import listmembers  as cb_listmembers
import newcb        as cb_newcb
import setcb        as cb_setcb
import updatecb     as cb_updatecb
import listcb       as cb_listcb
import concludecb   as cb_concludecb
import log          as cb_log
import battle       as cb_battle
import mrep         as cb_mrep

import cbtag        as cbt
import status       as st

# COMMAND CENTER
# db
_con =              True    
_dcon =             True

# auth
_kill =             True
_help =             False

# shen
_shitpost =         True
__spray =           True and _shitpost
__mind =            True and _shitpost
__threat =          True and _shitpost
__nero =            True and _shitpost
__neroe =           True and _shitpost
__loc =             True and _shitpost  
__pol =             True and _shitpost
__big =             True and _shitpost
__dumb =            True and _shitpost
__enty =            True and _shitpost
__enty1 =           True and _shitpost
__enty2 =           True and _shitpost
__enty3 =           True and _shitpost
__muimi =           True and _shitpost

# pcrd
_gacha =            True

_hatsune =          True
__chara =           True and _hatsune
__ue =              True and _hatsune
__tag =             True and _hatsune
__pos =             True and _hatsune
__data =            True and _hatsune

_guide =            True

# cb
_cb =               False
__pcb =             True and _cb
__startday =        True and _cb
__log =             True and _cb
__removelog =       True and _cb
__listlogs =        True and _cb
__battle =          True and _cb
__reload =          True and _cb
__updatemember =    True and _cb
__removemember =    True and _cb
__listmembers =     True and _cb
__newcb =           True and _cb
__setcb =           True and _cb
__updatecb =        True and _cb
__removecb =        True and _cb
__statscb =         True and _cb
__listcb =          True and _cb
__concludecb =      True and _cb
__mrep =            True and _cb

# GLOBALS
author_lock = []
role_decor = ("<",">","@","&")
span_days = 8
start = time.time()

cc = dict()
cc['shitpost'] = _shitpost
cc['hatsune'] = _hatsune
cc['cb'] = _cb

# GLOBAL FLAGS
flags = {
    'cb_db':            False,
    'current_cb':       False,
    'db_isconnected':   False,
    'cb_concluded':     False,
    'span_days':        span_days
         }

__log = ""

# LOAD CREDENTIALS (global scope)
with open("_pass/token.txt") as token_file:
    token = token_file.read().strip()
    token_file.close()

with open("_pass/db.txt") as db_file:
    db = {}
    db['db_name'] =     db_file.readline().strip()
    db['db_pw'] =       db_file.readline().strip()
    db['db_host'] =     db_file.readline().strip()
    db['db_dbname'] =   db_file.readline().strip()
    db_file.close()

# SERVER EMOJIS
shiori =        '<:shioread:449255102721556490> '
kasumi =        '<:KasumiInvestigate:591503783645806592> '
sarenheh =      '<:sarenheh:449255102566498305> '
sarensweat =    '<:sarensweat:447366342795067392> '
maki =          '<:tamakiS:595054639309651978> '
zeik =          '<:feelszeik:606111207287422979> '
dead =          '<:makotodead:610417622655172608> '
sarenf =        '<:SarenFall:604557991617888256> '
panda =         '<:feelspanda:588405851505819682> '
ames =          '<:amesStare:621378193021992961> '
amesyan =       '<:amesYan:621378194112512030> '
emj = {
    'shiori':   shiori,
    'kasumi':   kasumi,
    'sarenh':   sarenheh,
    'sarens':   sarensweat,
    'maki':     maki,
    'zeik':     zeik,
    'dead':     dead,
    'sarenf':   sarenf,
    'panda':    panda,
    'ames':     ames,
    'amesyan':  amesyan
    }

# BOT PREFERENCES
BOT_PREFIX = (".", "$")
client = Bot(command_prefix = BOT_PREFIX)
client.remove_command('help')

# STARTUP
@client.event
async def on_ready():
    global flags, __log
    print('on_ready: Logged in as {0.user}'.format(client))

    # connect to db
    print('on_ready: Attempting to connect to DB')
    flags = connect_db(flags,db)

    # loop status
    client.loop.create_task(playing())
    client.loop.create_task(expression())

    #time = datetime.datetime.utcnow()
    #date = time.strftime("%Y-%m-%d")

    #name = '_log/'+'Ames log '+date+'.txt'
    #__log = name
    
    #flog = open(name, mode='a+')
    #flog.write(" ".join([time.strftime("%Y-%m-%d %H:%M:%S"), 'Startup', '\n']))
    #flog.close()
    
# TASK
DURATION =      60*30
COOLDOWN =      60*15
PLAYING =       0
STREAMING =     1
LISTENING =     2
WATCHING =      3
ACTIVITIES = [
    discord.Activity(name='with Hatsune',               type=discord.ActivityType(PLAYING)),
    discord.Activity(name='Panda\'s complaints',        type=discord.ActivityType(LISTENING)),
    discord.Activity(name='with Aria\'s luck',          type=discord.ActivityType(PLAYING)),
    discord.Activity(name='with gacha rates',           type=discord.ActivityType(PLAYING)),
    discord.Activity(name='the collapse of the USSR',   type=discord.ActivityType(WATCHING)),
    discord.Activity(name='PrincessConnect Re:dive',    type=discord.ActivityType(STREAMING))
    ]

async def playing():
    while True:
        await client.change_presence(activity=random.choice(ACTIVITIES))
        await asyncio.sleep(random.randrange(DURATION-60*5,DURATION+60*20))
        await client.change_presence(activity=None)
        await asyncio.sleep(random.randrange(COOLDOWN-60*5,COOLDOWN+60*15))

EXPRESSIONS = [
    'ames.png',
    'ames_yan.png'
    ]

async def expression():
    while True:
        dp = open(random.choice(EXPRESSIONS), 'rb')
        await client.user.edit(avatar=dp.read())
        await asyncio.sleep(random.randrange(240*60, 300*60))

# MAIN
@client.event
async def on_message(message):
    func = 'on_message:'
    global author_lock
    # ignore messages from bots including self
    if message.author.bot:
        return
    
    # pass commands
    if message.content.startswith(BOT_PREFIX):
        #print("current locks: ", author_lock)
        print(datetime.datetime.now(),
              func,
              message.channel.guild.name,
              message.channel.name,
              ''.join(c for c in message.author.name if c <= '\uFFFF'),
              message.content)
        #_log(message, __log)
        
        # ignore commands from authors who are in a 'locked function'
        if str(message.author.id) in author_lock:
            print(func+'author is currently in author_lock - exiting')
            return
        
        msg = message.content.strip("".join(BOT_PREFIX))
        await client.process_commands(message)

@client.event
async def on_guild_join(guild):
    await st.intro(guild, emj)

@client.command()
async def status(ctx):
    await st.status(ctx, flags, client, start, cc)

# DATABASE RELATED
@client.command(enabled=_con and _dcon)
async def resetdb(ctx):
    func = 'resetdb: '
    channel = ctx.message.channel
    try:
        await _disconnectdb.invoke(ctx)
        await _connectdb.invoke(ctx)
    except Exception as err:
        print(func, err)
        await channel.send(emj['ames']+'Connection reset unsuccessful')
        return
    else:
        await channel.send('Database connection successfully reset!')

@client.command(enabled=_con)
async def _connectdb(ctx):
    global flags
    func = '_connectdb: '
    channel = ctx.channel
    if not flags['db_isconnected']:
        flags = connect_db(flags,db)
    else:
        pass
    return

@client.command(enabled=_dcon)
async def _disconnectdb(ctx):
    global flags
    func = '_disconnectdb: '
    channel = ctx.channel

    if flags['db_isconnected']:
        flags = connect_db(flags,db,0)
    else:
        pass
    return

# kill command
@client.command(aliases=['kys'], enabled=_kill)
async def kill(ctx):
    global flags
    func = '_kill: '
    channel = ctx.channel
    # only allow author to kill
    if str(ctx.message.author.id) == '235361069202145280':
        await channel.send(emj['sarenh']+"I'll be right back!")
        print(func+'logging off...')
        flags = connect_db(flags,db,0)
        await client.logout()
    else:
        print(func+'user has no authorisation')
        await channel.send(emj['maki'])
        return

# HELP
@client.command(enabled=_help)
async def help(ctx, *inp:str):
    await ames_help(ctx, inp, emj)

# GULAG
@client.command(aliases=['gulag'])
async def jail(ctx, user):
    await redclan.jail(ctx, user, emj, client)

# MUIMI THIS
@client.command(enabled=__muimi)
async def muimi(ctx, *links:str):
    await mmi.muimi(ctx, links, emj)

# ENTY ROULETTE
@client.command(enabled = __enty)
async def enty(ctx, *member:discord.Member):
    await entypol.enty(ctx, 0, member, emj)

# ENTY1 - ENTYCHSE
@client.command(enabled = __enty1)
async def enty1(ctx, *member:discord.Member):
    await entypol.enty(ctx, 1, member, emj)

# ENTY2 - ENTYRAID
@client.command(enabled = __enty2)
async def enty2(ctx, *member:discord.Member):
    await entypol.enty(ctx, 2, member, emj)

# ENTY3 - ENTYDEJAVU
@client.command(enabled = __enty3)
async def enty3(ctx, *member:discord.Member):
    await entypol.enty(ctx, 3, member, emj)

# DUMB
@client.command(enabled=__dumb, aliases=['dumb'])
async def dumbass(ctx, *member:discord.Member):
    await dumb.dumbass(ctx, member)

# SPRAY
@client.command(aliases=['s'],enabled=__spray)
async def spray(ctx, *member:discord.Member):
    await sp.spray(ctx, member, emj)

# MIND
@client.command(enabled=__mind)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def mind(ctx, *text:str):
    await sh.changemymind(ctx, text, emj)

# THREAT
@client.command(enabled=__threat)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def threat(ctx, *user:discord.Member):
    await sh.kalina(ctx, user)

# NEROE
@client.command(enabled=__neroe)
@commands.cooldown(1, 1, commands.BucketType.guild)
async def neroe(ctx, emoji:str):
    await sh.nero_emoji(ctx, emoji)

# NERO
@client.command(enabled=__nero)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def nero(ctx, *text:str):
    await sh.nero_says(ctx, text, emj)

# LOCATION
@client.command(aliases=['loc'],enabled=__loc)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def location(ctx, *user:discord.Member):
    await sh.knowyour(ctx, user)

# POLICE
@client.command(aliases=['pol','lolipol'],enabled=__pol)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def police(ctx, *user:discord.Member):
    await sh.jail(ctx, user)

# GACHA
@client.command(enabled=_gacha)
@commands.cooldown(1, 2, commands.BucketType.guild)
async def gacha(ctx, t=10, mode=''):
    await roll.roll(ctx, emj, t, mode)

# SPARK
@client.command(enabled=_gacha)
async def spark(ctx, *t):
    await roll.spark(ctx, t, emj, client)

"""
# HATSUNE - CHARA
@client.command(aliases=['c'], enabled=__chara)
async def chara(ctx, name="", ue=""):
    await hatsune.hatsune_chara(ctx, name, ue, flags, emj, client)
"""

# HATSUNE - CHARA
@client.command(aliases=['c'], enabled=__chara)
async def chara(ctx, *name:str):
    if flags['db_isconnected']:
        await hatsune_new.hatsune_chara(ctx, name, flags, emj, client)
    else:
        await ctx.channel.send(emj['sarenf']+'The database isn\'t connected!')

# HATSUNE - UE
@client.command(enabled=__ue)
async def ue(ctx, *name:str):
    if flags['db_isconnected']:
        await hatsune_new.hatsune_chara(ctx, name, flags, emj, client, mode="UE")
    else:
        await ctx.channel.send(emj['sarenf']+'The database isn\'t connected!')

# HATSUNE - DATA
@client.command(enabled=__data, aliases=['r14'])
async def data(ctx, *name:str):
    if flags['db_isconnected']:
        await hatsune_new.hatsune_chara(ctx, name, flags, emj, client, mode="Data")
    else:
        await ctx.channel.send(emj['sarenf']+'The database isn\'t connected!')
    
# HATSUNE - TAG
@client.command(enabled=__tag)
async def tag(ctx, *tags:str):
    if flags['db_isconnected']:
        await hatsune.hatsune_tag(ctx, tags, flags, emj, client)
    else:
        await ctx.channel.send(emj['sarenf']+'The database isn\'t connected!')

# HATSUNE - POS
@client.command(enabled=__pos)
async def pos(ctx, *tags:str):
    if flags['db_isconnected']:
        await hatsune.hatsune_pos(ctx, tags, flags, emj, client)
    else:
        await ctx.channel.send(emj['sarenf']+'The database isn\'t connected!')

# BIG
@client.command(aliases=['b'], enabled=__big)
async def big(ctx, emoji:str):
    await enlarge(ctx, emoji, emj)

# GUIDE
@client.command(enabled=_guide)
async def guide(ctx, chara=""):
    if chara.lower() == 'rima':
        await ctx.channel.send(maki+'This character doesnt exist')
        return

    if flags['db_isconnected']:
        await gd.guide(ctx, chara, flags, emj)
    else:
        await ctx.channel.send(emj['sarenf']+'The database isn\'t connected!')

# CBTAG
@client.command()
async def cbtag(ctx, *options):
    await cbt.cbtag(ctx, options, emj, client)

@client.event
async def on_reaction_add(reaction, user):
    re = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣']
    #print(user.name, reaction.emoji)
    if user.bot:
        return

    # open message
    file = open('commands/CB/_post.txt', 'r')
    post = ast.literal_eval(file.read())
    file.close()

    #print(list(post.values()))
    
    post_id = [id[1] for id in list(post.values()) if id != None]
    
    #print(reaction.message.id, post_id, reaction.message.id in post_id)

    if reaction.message.id in post_id:
        #print(reaction.emoji)
        if reaction.emoji in re:
            await cbt.assign(user,
                             reaction.message.guild,
                             reaction.message.channel,
                             str(re.index(reaction.emoji)+1),
                             _mode="event")
        elif reaction.emoji == cbt.REPEAT:
            await reaction.message.edit(embed=cbt.cbtag_embed(user,
                                                              reaction.message.guild,
                                                              mode='post')
                                        )
        await reaction.remove(user)
    
    

# CB COMMAND GROUP
@client.group(pass_context=True,case_insensitive=True,enabled=_cb)
async def cb(ctx):
    if ctx.invoked_subcommand is None:
        print('cb: invalid subcommand or no subcommand found')

@cb.before_invoke
async def before_cb(ctx):
    global flags
    flags = await cb_init(ctx, flags)

# CB PCB
@cb.command(enabled=__pcb)
async def pcb(ctx):
    await cb_pcb.pcb(ctx, flags, emj)

# CB STARTDAY
@cb.command(aliases=['sd'],enabled=__startday)
async def startday(ctx):
    if await perm(ctx, emj): await cb_startday.startday(ctx, flags, emj)
    
# CB LOG - locked command
@cb.command(enabled=__log)
async def log(ctx, *inp):
    global author_lock
    a_id = str(ctx.message.author.id)
    
    author_lock.append(a_id)
    print(author_lock)
    try:
        await cb_log.log(ctx, inp, flags, emj, client)
    except Exception as e:
        print(e)
        pass
    author_lock.remove(a_id)

# CB REMOVELOG
@cb.command(aliases=['rl'],enabled=__removelog)
async def removelog(ctx, eid=0):
    if await perm(ctx, emj): await cb_removelog.removelog(ctx, eid, flags, emj)
    
# CB LISTLOGS
@cb.command(enabled=__listlogs)
async def listlogs(ctx, *inp:str):
    await cb_listlogs.listlogs(ctx, inp, flags, emj)

# CB BATTLE
@cb.command(enabled=__battle)
async def battle(ctx, bat:str):
    await cb_battle.battle(ctx, bat, flags, emj)

# CB RELOAD
@cb.command(enabled=__reload)
async def reload(ctx, guild=""):
    if await perm(ctx, emj): await cb_reload.reload(ctx, guild ,flags, emj)

# CB UPDATEMEMBER
@cb.command(enabled=__updatemember)
async def updatemember(ctx, *inp):
    if await perm(ctx, emj): await cb_updatemember.updatemember(ctx, inp, flags, emj)

# CB REMOVEMEMBER
@cb.command(enabled=__removemember)
async def removemembed(ctx, *inp):
    if await perm(ctx, emj): await cb_removemember.removemember(ctx, inp, flags, emj)

# CB LISTMEMBERS
@cb.command(enabled=__listmembers)
async def listmembers(ctx, *mode):
    await cb_listmembers.listmembers(ctx, mode, flags, emj)

# CB NEWCB
@cb.command(enabled=__newcb)
async def newcb(ctx, *inp):
    global flags
    if await perm(ctx, emj): flags = await cb_newcb.newcb(ctx, inp, flags, emj)

# CB SETCB
@cb.command(enabled=__setcb)
async def setcb(ctx, *inp):
    global flags
    if await perm(ctx, emj): flags = await cb_setcb.setcb(ctx, inp, flags, emj)

# CB UPDATECB
@cb.command(enabled=__updatecb)
async def updatecb(ctx, *inp):
    if await perm(ctx, emj): await cb_updatecb.updatecb(ctx, inp, flags, emj)

# CB REMOVECB
@cb.command(enabled=__removecb)
async def removecb(ctx, *inp):
    if await perm(ctx, emj): await cb_removecb.removecb(ctx, inp, flags, emj)

# CB STATSCB
@cb.command(enabled=__statscb)
async def statscb(ctx, *inp):
    await cb_statscb.statscb(ctx, inp, flags, emj)

# CB LISTCB
@cb.command(enabled=__listcb)
async def listcb(ctx):
    await cb_listcb.listcb(ctx, flags, emj)

# CB CONCLUDECB
@cb.command(enabled=__concludecb)
async def concludecb(ctx):
    global flags
    if await perm(ctx, emj): flags = await cb_concludecb.concludecb(ctx, flags, emj)
    
# CB MREP
@cb.command(enabled=__mrep)
async def mrep(ctx, search = "", cb_id = 0):
    await cb_mrep.mrep(ctx, search, cb_id, flags, emj)

# MISC
# CB perm
async def perm(ctx, emj):
    author = ctx.message.author
    channel = ctx.channel
    tiggs = '235361069202145280'
    if str(author.id) != tiggs:
        await channel.send(emj['maki'])
        return False
    else:
        return True

@client.command()
async def read(ctx):
    await ctx.message.delete()
    await ctx.channel.send(emj['shiori'])

@client.command()
async def dead(ctx):
    await ctx.message.delete()
    await ctx.channel.send(emj['dead'])

@client.command()
async def panda(ctx):
    await ctx.channel.send(emj['panda'])
    
# test
@client.command()
async def sandbox(ctx, **args):
    print(args)
    
@client.command(aliases=['e'], enabled=True)
async def emoji(ctx, target=""):
    await proto.emoji(ctx, target, client, emj)

@client.command()
async def find(ctx, target=""):
    await proto.listemoji(ctx, target, client, emj)

@client.command()
async def reload_emotes(ctx):
    await proto.reload_emotes(client)

"""
@client.event
async def on_command_error(ctx, error):
    ignored = (commands.CommandNotFound, commands.UserInputError)
    error = getattr(error, 'original', error)
    print(error)
    #_errlog(ctx, str(error), __log)
    if isinstance(error, ignored):
        return
    elif isinstance(error, commands.DisabledCommand):
        return await ctx.channel.send('I\'m currently taking a break '+emj['dead'])
    else:
        await ctx.channel.send(emj['shiori'])
"""

# RUN
client.run(token)
