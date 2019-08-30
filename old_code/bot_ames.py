"""
Ames bot for Princonne - rewrite
Mostly developed to brush up on python3
Created by tiggs

Primary purpose is to log CB scoress

TODO:
.cb conclude(cb_id)
.cb quota(cb_id) - given warning on cb_concluded
"""

# changelog - rewrite
# v1.0.200719   rewrite version finished

# DEPENDENCIES
import datetime

from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
import random

import discord
from discord.ext.commands import Bot
from discord.ext import commands

import mysql.connector
from mysql.connector import errorcode

# GLOBALS
author_lock = []
role_decor = ("<",">","@","&")
span_days = 8

# GLOBAL FLAGS
cb_db = False
current_cb = False
db_isconnected = False
cb_concluded = False

# LOAD CREDENTIALS
with open("pass/token.txt") as token_file:
    token = token_file.read().strip()
    token_file.close()

with open("pass/db.txt") as db_file:
    db_name = db_file.readline().strip()
    db_pw = db_file.readline().strip()
    db_host = db_file.readline().strip()
    db_dbname = db_file.readline().strip()
    db_file.close()

# BOT PREFERENCES
BOT_PREFIX = (".")
client = Bot(command_prefix = BOT_PREFIX)
client.remove_command('help')

# STARTUP
@client.event
async def on_ready():
    print('on_ready: Logged in as {0.user}'.format(client))

    # connect to db
    print('on_ready: Attempting to connect to DB')
    connect_db()

# MAIN
@client.event
async def on_message(message):
    global author_lock
    # ignore messages from bots including self
    if message.author.bot:
        return
    
    # ignore commands from authors who are in a 'locked function'
    if message.author in author_lock:
        print('on_message: author is currently in author_lock - exiting')
        return
    
    # pass commands
    if message.content.startswith(BOT_PREFIX):
        print('on_message: passing command: ' + message.content)
        msg = message.content.strip("".join(BOT_PREFIX))
        await client.process_commands(message)

# kill command
@client.command()
async def _kill(ctx):
    channel = ctx.channel
    if str(ctx.message.author.id) == '235361069202145280':
        await channel.send("I'll be right back!")
        print('_kill: logging off...')
        connect_db(0)
        await client.logout()
    else:
        print('_kill: user has no authorisation')
        await channel.send('<:shioread:449255102721556490>')
        return

# MIND
@client.command()
async def mind(ctx, *text:str):
    channel = ctx.channel
    author = ctx.message.author.avatar_url
    length = len(text)
    change = Image.open('mind/change.jpg')

    response = requests.get(author)
    author = Image.open(BytesIO(response.content))
    if author.is_animated:
        author.seek(author.n_frames//2)
        author = author.convert(mode="RGB")

    # find good font and size set depending on text length
    print(length)
    if length <= 30:
        limit = 22
        fontsize = 22
    elif length <= 60:
        limit = 22
        fontsize = 17
    else:
        await channel.send('<:shioread:449255102721556490>')
        print('nero: input text length exceeds maximum allowable')

    # breaking text up to fit
    breaks = []
    words = list(text)
    templine = words[0]
    lines = 1

    for i in range(len(words[1:])):
        word = words[i+1]
        if len(templine + word + " ") >= limit:
            j = 0
            while words.index(word, j) < i:
                j += 1
            breaks.append(words.index(word, j))
            templine = word
            lines += 1
        else:
            templine += (" " + word)
            
    pos = 0
    line = []

    # break text
    if breaks:
        for _break in breaks:
            line.append(" ".join(words[pos:_break]))
            pos = _break
        line.append(" ".join(words[pos:]))
        temptext = "\n".join(line)
    else:
        temptext = templine

    async with ctx.typing():
        #pos = (25, -10*lines+80)
        text = temptext
        font = ImageFont.truetype("arial.ttf", fontsize)

        size = (100,100)
        author.resize(size,resample=Image.ANTIALIAS)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)
        author = ImageOps.fit(author, mask.size, centering=(0.5, 0.5))
        author.putalpha(mask)

        #txt = Image.new('RGBA',(185,80),"blue")
        txt = Image.new('L', (185,80))
        dtxt = ImageDraw.Draw(txt)
        w, h = dtxt.textsize(text,font=font)
        #print(w, h)
        dtxt.text(((185-w)/2,(80-h)/2), text, font=font, fill=255)
        dtxt2 = txt.rotate(6, expand=1)
        change.paste(ImageOps.colorize(dtxt2, (0,0,0), (0,0,0)), (220,210), dtxt2)
        change.paste(author, (140,5), author)
        #change.paste(dtxt2,(220,210),dtxt2)
        change.save('mind/changemymind.png')
        change.close()
        
    await channel.send(file=discord.File('mind/changemymind.png'))

# THREAT
@client.command()
async def threat(ctx, *user:discord.Member):
    channel = ctx.channel
    threater = ctx.message.author
    async with ctx.typing():
        if len(user) == 0:
            threatened = threater
        else:
            threatened = user[0]

        t1 = requests.get(threater.avatar_url)
        t2 = requests.get(threatened.avatar_url)

        threat = Image.open('threaten/threaten.png')
        threater = Image.open(BytesIO(t1.content))
        threatened = Image.open(BytesIO(t2.content))

        if threater.is_animated:
            threater.seek(threater.n_frames//2)
            threater = threater.convert(mode="RGB")
        if threatened.is_animated:
            threatened.seek(threatened.n_frames//2)
            threatened = threatened.convert(mode="RGB")

        size = (90, 90)
        threater.resize(size,resample=Image.ANTIALIAS)
        threatened.resize(size,resample=Image.ANTIALIAS)

        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)

        threater = ImageOps.fit(threater, mask.size, centering=(0.5, 0.5))
        threater.putalpha(mask)
        threatened = ImageOps.fit(threatened, mask.size, centering=(0.5, 0.5))
        threatened.putalpha(mask)

        threat.paste(threater, (20,100), threater)
        threat.paste(threatened, (210,50), threatened)

        threat.save('threaten/threat.png')

    await channel.send(file=discord.File('threaten/threat.png'))
    print('location: success')

# NERO SAYS EMOJI
@client.command()
async def neroe(ctx, emoji:str):
    channel = ctx.channel
    author = ctx.message.author
    png = 'https://cdn.discordapp.com/emojis/{:s}.png'
    raw_emoji = emoji[1:-1].strip().split(':')
    
    if raw_emoji[0] == 'a':
        print('neroe: no support for animated emojis yet')
        await channel.send('<:shioread:449255102721556490>')
        return
    elif raw_emoji[0] == "":
        emoji_url = png.format(raw_emoji[-1])
        response = requests.get(emoji_url)
    else:
        print('neroe: invalue input')
        await channel.send('<:shioread:449255102721556490>')
        return

    # params
    size = 150
    image = Image.open(BytesIO(response.content))
    image = image.convert(mode="RGBA")
    image = image.resize((size,size),resample=Image.ANTIALIAS)
    image = image.rotate(10, expand=1)
    nero = Image.open('nerosays/nero.jpg')
    nero = nero.convert(mode="RGB")
    nero.paste(image, (100,20), image)
    nero.save('nerosays/nerosayse.png')
    nero.close()

    # send image
    async with ctx.typing():
        result = discord.File("nerosays/nerosayse.png", filename="nerosayse.png")
        embed = discord.Embed()
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_author(name="{:s} wanted you to know that:".format(author.name), icon_url=author.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://nerosayse.png")
    await channel.send(file=result, embed=embed)
    print('neroe: success')
    return

# NERO SAYS
@client.command()
async def nero(ctx):
    channel = ctx.channel
    author = ctx.message.author
    text = ctx.message.content[5:]
    length = len(text)
    
    if text == "" or length > 170:
        print('nero: input text length exceeds maximum allowable')
        await channel.send('<:shioread:449255102721556490>')
        return
    
    # find good font and size set depending on text length
    if length <= 30:
        limit = 15
        fontsize = 40
    elif length <= 60:
        limit = 18
        fontsize = 35
    elif length <= 120:
        limit = 20
        fontsize = 22
    else:
        limit = 35
        fontsize = 18

    # breaking text up to fit
    breaks = []
    words = text.strip().split(" ")
    templine = words[0]
    lines = 1
    
    for word in words[1:]:
        if len(templine + word + " ") >= limit:
            breaks.append(words.index(word))
            templine = word
            lines += 1
        else:
            templine += (" " + word)
            
    pos = 0
    line = []

    # break text
    if breaks:
        for _break in breaks:
            line.append(" ".join(words[pos:_break]))
            pos = _break
        line.append(" ".join(words[pos:]))
        temptext = "\n".join(line)
    else:
        temptext = templine

    pos = (25, -10*lines+80)
    text = temptext
    nero = Image.open('nerosays/nero.jpg')
    font = ImageFont.truetype("arial.ttf", fontsize)

    #txt = Image.new('RGBA',(350,200),"blue")
    txt = Image.new('L', (350,200))
    dtxt = ImageDraw.Draw(txt)
    w, h = dtxt.textsize(text,font=font)
    #print(w, h)
    dtxt.text(((350-w)/2,(200-h)/2), text, font=font, fill=255)
    dtxt2 = txt.rotate(10, expand=1)
    nero.paste(ImageOps.colorize(dtxt2, (0,0,0), (0,0,0)), (-10,-20), dtxt2)
    #nero.paste(dtxt2,(-10,-20),dtxt2)
    nero.save('nerosays/nerosays.png')
    nero.close()

    async with ctx.typing():
        result = discord.File("nerosays/nerosays.png", filename="nerosays.png")
        embed = discord.Embed()
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_author(name="{:s} wanted you to know that:".format(author.name), icon_url=author.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://nerosays.png")
    await channel.send(file=result, embed=embed)
    print('nero: success')
    return

# GACHA
@client.command()
@commands.cooldown(1, 5, commands.BucketType.guild)
async def gacha(ctx, t=10):
    channel = ctx.channel
    author = ctx.message.author
    if t > 10:
        print('gacha: roll > 10')
        await channel.send('You\'re being a bit too ambitious')
        return
    elif t < 1:
        print('gacha: invalid roll input')
        await channel.send('<:shioread:449255102721556490>')
        return
    raw_result = gacha_result(t)
    async with ctx.typing():
        create_gacha_result(raw_result)
        result = discord.File("gacha/gresult.png", filename="gresult.png")
        embed = discord.Embed()
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_author(name="{:s} rolled:".format(author.name), icon_url=author.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://gresult.png")
    await channel.send(file=result, embed=embed)
    print('gacha: success')
    return

def create_gacha_result(result):
    #print('cgr: start init')
    # open images
    gacha = Image.open('gacha/gbg2.png')
    rare = Image.open('gacha/r2.png')
    srare = Image.open('gacha/sr2.png')
    ssrare = Image.open('gacha/ssr2.png')
    new = Image.open('gacha/new.png')
    none = Image.open('gacha/test.png')
    
    # sizes
    row1 = 80
    row2 = 370
    spacing = 221
    psize = (197,270)
    csize = (141,141)
    nsize = (80,80)
    rs = Image.ANTIALIAS
    gscalef = 0.5
    gsizef =  (round(gacha.size[0]*gscalef),
               round(gacha.size[1]*gscalef))
    pxstart = 200
    cxstart = 227
    cos = 79
    nos = -25

    # resize
    rare = rare.resize(psize, resample=rs)
    srare = srare.resize(psize, resample=rs)
    ssrare = ssrare.resize(psize, resample=rs)
    new = new.resize(nsize, resample=rs)

    #print('cgr: end init')
    #print('cgr: start reading avatars')
    # get avatars
    final = []
    for chara, rarity in result:
        try:
            avatar = Image.open('gacha/units/{:s}.webp'.format(chara))
        except:
            avatar = none
        avatar = avatar.resize(csize, resample=rs)
        if abs(rarity) == 1:
            bg = rare
        elif abs(rarity) == 2:
            bg = srare
        else:
            bg = ssrare
        final.append((avatar, bg, rarity))

    #print('cgr: end reading avatars')
    #print('cgr: start drawing')
    
    # draw result
    i = 0
    for profile, bg, rarity in final:
        if i < 5:
            gacha.paste(bg, (pxstart + i*spacing, row1), bg)
            gacha.paste(profile, (cxstart + i*spacing, row1 + cos), profile)
            if rarity < 0:
                gacha.paste(new, (pxstart - 25 + i*spacing, row1 - 25), new)
        else:
            j = i - 5
            gacha.paste(bg, (pxstart + j*spacing, row2), bg)
            gacha.paste(profile, (cxstart + j*spacing, row2 + cos), profile)
            if rarity < 0:
                gacha.paste(new, (pxstart - 25 + j*spacing, row2 - 25), new)
        i += 1
        profile.close()

    
    gacha = gacha.resize(gsizef, resample=rs)
    gacha.save('gacha/gresult.png')

    # shutdown
    gacha.close()
    rare.close()
    srare.close()
    ssrare.close()
    new.close()
    none.close()
    #print('cgr: end drawing')
    print('cgr: success')
    return

def gacha_result(t=10):
    r_pool, sr_pool, ssr_pool = read_pool()
    ssr_rate = 0.025
    sr_rate = 0.18
    r_rate = 0.79

    # LIMITED/SEASONAL ADDITION - PLEASE MANUALLY FILL
    # DOES NOT APPLY TO RATEUPS FOR NORMAL POOL CHARAS!
    ssr_up = ['ssaren']
    ssr_up_rate_indiv = 0.007
    
    rolls = []
    grain = 100000
    for i in range(t):
        roll = random.randint(0,grain)
        if (i+1) != 10:
            if roll < r_rate * grain:
                chara = random.choice(r_pool)
                rolls.append((chara,1))
            elif roll < (r_rate + sr_rate) * grain:
                chara = random.choice(sr_pool)
                rolls.append((chara,2))
            else:
                chara = random.choice(ssr_pool)
                rolls.append(tier(3, ssr_pool, ssr_rate, ssr_up, ssr_up_rate_indiv))
        else:
            if roll < (r_rate + sr_rate) * grain:
                chara = random.choice(sr_pool)
                rolls.append((chara,2))
            else:
                rolls.append(tier(3, ssr_pool, ssr_rate, ssr_up, ssr_up_rate_indiv))
    print('gacha_result: success')
    return rolls

def tier(pool_rarity, pool, pool_rate ,pool_limited, limited_rate_indiv):
    # assumes equal draw rate for rate ups!
    limited_rate = len(pool_limited)*limited_rate_indiv/pool_rate

    grain = 100000
    roll = random.randint(0,grain)
    if roll < limited_rate*grain:
        chara = random.choice(pool_limited)
        return (chara,-1*pool_rarity)
    else:
        chara = random.choice(pool)
        return (chara,pool_rarity)

def read_pool():
    with open('gacha/r.txt') as file:
        r_pool = file.read().splitlines() 
    with open('gacha/sr.txt') as file:
        sr_pool = file.read().splitlines()
    with open('gacha/ssr.txt') as file:
        ssr_pool = file.read().splitlines()
    print('read_pool: success')
    return r_pool, sr_pool, ssr_pool

# LOCATION
@client.command(aliases=['loc'])
async def location(ctx, *user: discord.Member):
    if len(user) == 0:
        user = ctx.message.author
    else:
        user = user[0]
    channel = ctx.channel
    author = user.name
    await ctx.message.delete()
    async with ctx.typing():
        font = ImageFont.truetype("arial.ttf", 22)
        loc = Image.open('location/location.png')
        draw = ImageDraw.Draw(loc)
        draw.text((35, 45),author+" wants to",(0,0,0),font=font)
        loc.save('location/loc.png')
    await channel.send(file=discord.File('location/loc.png'))
    print('location: success')
    return

# LMAO LOLIPOLICE
@client.command(aliases=['pol', 'lolipolice'])
@commands.cooldown(1, 5, commands.BucketType.guild)
async def police(ctx, *user: discord.Member):
    channel = ctx.channel
    await ctx.message.delete()

    if len(user) == 0:
        user = ctx.message.author
    else:
        user = user[0]
    
    async with ctx.typing():
        # get images
        response = requests.get(user.avatar_url)
        avatar = Image.open(BytesIO(response.content))
        police_base = Image.open('police/police.gif')
        
        # check if avatar is animated
        if avatar.is_animated:
            animated = True
            #avatar.seek(avatar.n_frames//2)
            #avatar = avatar.convert(mode="RGB")
            #avatar.seek(0)
            #avatar = avatar.convert(mode="RGB")
        else:
            animated = False
            pass
            
        size = (120, 120)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)
        
        if animated:
            aframes = [frame.copy() for frame in ImageSequence.Iterator(avatar)]
            nframes = len(aframes)
            
            if nframes < 7:
                pass
            else:
                skip = nframes // 2
                aframes = aframes[skip-3:skip+3]
            
            aframes = [frame.resize(size,Image.ANTIALIAS) for frame in aframes]
            aframes = [frame.convert(mode="RGB") for frame in aframes]
            aframes = [ImageOps.fit(frame, mask.size, centering=(0.5, 0.5)) for frame in aframes]

            #print(aframes)
            n_frames = len(aframes)
        
        else:
            avatar = avatar.resize(size,Image.ANTIALIAS)
            #mask = Image.new('L', size, 0)
            #draw = ImageDraw.Draw(mask) 
            #draw.ellipse((0, 0) + size, fill=255)
            avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
            avatar.putalpha(mask)

        #print(aframes)
        
        counter = 0
        frames = []
        for frame in ImageSequence.Iterator(police_base):
            frame = frame.copy()
            #print(counter, n_frames)
            
            if animated:
                if counter == (n_frames-1):
                    counter = 0
                aframe = aframes[counter]
                aframe.putalpha(mask)
                frame.paste(aframe.convert(mode="RGB").quantize(palette=frame), (320,150), aframe)
                frames.append(frame)
            
            else:
                frame.paste(avatar.convert(mode="RGB").quantize(palette=frame), (320,150), avatar)
                frames.append(frame)
            counter += 1

        frames[0].save('police/pol.gif',
                       format='GIF',
                       append_images=frames[1:],
                       save_all=True,
                       duration=80,
                       loop=0)
        
        result = discord.File("police/pol.gif", filename="pol.gif")
        embed = discord.Embed()
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_author(name="{:s} is going to jail:".format(user.name), icon_url=user.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://pol.gif")
        
    await channel.send(file=result, embed=embed)
    #await channel.send(file=discord.File('police/pol.gif'))
    print('police: success')
    return

# HATSUNE BACKUP - CHARA
@client.command(aliases=['c'])
async def chara(ctx, name:str, ue=""):
    channel = ctx.channel
    members = ctx.message.guild.members
    target = name.lower()
    # check hatsune
    for member in members:
        if str(member.id) == '580194070958440448' and str(member.status) == 'online':
            print('chara: hatsune is online - exiting lmao')
            await channel.send('<:KasumiInvestigate:591503783645806592> Hatsune is currently available. Please bother her instead.')
            return
    print('chara: hatsune offline')
    # thi should always return something
    get_chara_list = ("SELECT unit_id, unit_name_eng "
                      "FROM princonne.chara_data_final")
    try:
        cursor = cb_db.cursor()
        cursor.execute(get_chara_list, )
    except mysql.connector.Error as err:
        print('chara:\n', err)
        cursor.close()
        await channel.send('<:shioread:449255102721556490>')
        return
    else:
        chara_list = []
        id_list = []
        for (_uid, _name) in cursor:
            chara_list.append(str(_name).lower())
            id_list.append(str(_uid))

    if target not in chara_list:
        cursor.close()
        await channel.send('<:shioread:449255102721556490> I didnt find that character. Please use their full name.')
        return
    else:
        target_id = id_list[chara_list.index(target)]

    # this should always return 1 non-Null result
    get_chara_data = ("SELECT image, unit_name_eng, "
                      "ub_trans, skill_1_translation, skill_2_trans, "
                      "comment_trans, tag, skill_1_plus_trans "
                      "FROM princonne.chara_data_final "
                      "WHERE unit_id = {:d}".format(int(target_id)))
    try:
        cursor.execute(get_chara_data, )
    except mysql.connector.Error as err:
        print('chara:\n', err)
        cursor.close()
        await channel.send('<:shioread:449255102721556490>')
        return
    else:
        for (_i, _name, _ub, _sk1, _sk2, _c, _t, _sk1p) in cursor:
            image_url = str(_i)
            unit_name = str(_name)
            ub = str(_ub)
            sk1 = str(_sk1)
            sk2 = str(_sk2)
            comment = str(_c)
            tags = str(_t)
            sk1p = str(_sk1p)
        cursor.close()

    print('chara: successful!')
    data = [image_url, unit_name, ub, sk1, sk2, comment, tags, sk1p]
    await channel.send(embed=charaembed(data, ue))
    return

def charaembed(data, ue):
    embed = discord.Embed(title=data[1], description=data[5], timestamp=datetime.datetime.utcnow())
    embed.set_author(name="Character Profile", icon_url=client.user.avatar_url)
    embed.set_footer(text="still in testing")
    if data[0] != 'None':
        embed.set_thumbnail(url=data[0])
    embed.add_field(name="Union Burst", value=data[2])
    if ue == "":
        embed.add_field(name="Skill 1", value=data[3])
    else:
        embed.add_field(name="Skill 1 +", value=data[7])
    embed.add_field(name="Skill 2",value=data[4])
    print(data[6])
    if len(data[6]) == 0: 
        embed.add_field(name='Tags', value="No tags yet")
    else:
        embed.add_field(name='Tags', value=data[6])
    return embed
        
# BIG EMOJI
@client.command(aliases=['b'])
async def big(ctx, emoji:str):
    channel = ctx.channel
    author = ctx.message.author
    await ctx.message.delete()
    png = 'https://cdn.discordapp.com/emojis/{:s}.png'
    gif = 'https://cdn.discordapp.com/emojis/{:s}.gif'
    raw_emoji = emoji[1:-1].strip().split(':')
    print(raw_emoji)
    if raw_emoji[0] == 'a':
        emoji_url = gif.format(raw_emoji[-1])
    elif raw_emoji[0] == "":
        emoji_url = png.format(raw_emoji[-1])
    else:
        await channel.send('<:shioread:449255102721556490>')
        return
    embed = discord.Embed()
    embed.set_author(name="{:s} sent:".format(author.name), icon_url=author.avatar_url)
    embed.set_image(url=emoji_url)
    await channel.send(embed=embed)
    return
    
# CLAN BATTLE COMMAND GROUP
@client.group(pass_context=True,
              case_insensitive=True)
async def cb(ctx):
    
    if ctx.invoked_subcommand is None:
        print('cb: invalid subcommand or no subcommand found')
        
    #if not await cb_init(ctx):
    #    return

@cb.before_invoke
async def before_cb(ctx):
    await cb_init(ctx)

# cb pcb
@cb.command()
async def pcb(ctx):
    """
    Have Ames say the current CB. This should never throw an error.
    """
    channel = ctx.channel
    author = ctx.message.author
    nick = author.nick
    
    if not check_current_cb():
        print('pcb: current_cb not set')
        await channel.send("No CB set!")
        return 
    
    cb_id = int(current_cb)
    day = _getday(cb_id)
    query_cb = ("SELECT start_date, span_days "
                "FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_cb, )
    except mysql.connector.Error as err:
        print('pcb:\n', err)
        cb_cursor.close()
        await channel.send("Error upon requesting CB data, check console!")
        return
    else:
        for (_sd, _span) in cb_cursor:
            sd = str(_sd)
            span = int(_span)
        cb_cursor.close()
        if check_cb_concluded():
            status = 'has concluded. Otsukaresama!'
        else:
            status = 'is ongoing. Ganbare!'
            
        print('pcb: success')
        await channel.send("We are currently on **Day {0:s} of {4:d}** of the CB that started on {1:s} with `cb_id = {2:d}`. The CB {3:s}"\
               .format(str(day), sd, cb_id, status, span))
        return

# cb startday
@cb.command(aliases=['sd'])
async def startday(ctx):
    """
    Inserts 0s into cb.cb_log. Replaced _endday
    """
    channel = ctx.channel
    
    if not check_current_cb():
        print('startday: current_cb is not set!')
        await channel.send('Could not start day: current CB not set!')
        return
    if cb_concluded:
        print('startday: cb_concluded flag set')
        await channel.send('Could not start new day: CB has ended!')
        return
    
    cb_id = int(current_cb)
    
    # get the current day
    day = _getday(cb_id)
    
    # get m_id
    get_mid = ("SELECT m_id FROM cb.members WHERE active = 1")
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(get_mid, )
    except mysql.connector.Error as err:
        print('startday:\n', err)
        cb_cursor.close()
        await channel.send('Could not start new day!')
        return
    
    mid = []
    for (_mid) in cb_cursor:
        mid.append(int(_mid[0]))
    if len(mid) == 0:
        print('startday: no active members')
        await channel.send('No active members - Nothing to insert!')
        return

    # insert
    insert_log = "INSERT INTO cb.cb_log "\
                 "(cb_id, day, hit1, hit2, hit3, hits, m_id, hit1meta, hit2meta, hit3meta) "\
                 "VALUES ({0:d}, {1:d}, {2:d}, {3:d}, {4:d}, {5:d}, {6:d}, '{7:s}', '{8:s}', '{9:s}')"

    #print(mid, day, cb_id)
    try:
        for m_id in mid:
            cb_cursor.execute((insert_log.format(cb_id, day+1, 0, 0, 0, 0, int(m_id), '0-0:0', '0-0:0', '0-0:0')))
            cb_db.commit()
    except mysql.connector.Error as err:
        print('startday:\n', err)
        cb_cursor.close()
        await channel.send('Failed to start today\'s log')
        return
    else:
        cb_cursor.close()
        print('startday: success')
        await channel.send('Successfully started new day!')
        return


# cb logmaster
@cb.command(enabled=False)
async def logmaster_old(ctx, nick:str, *hit_v:str):
    channel = ctx.channel
    user_id = ctx.message.author.id
    name = ctx.message.author.name

    print(hit_v)
    # checks
    if len(hit_v) > 3:
        print('logmaster: too many inputs')
        await channel.send('<:shioread:449255102721556490>')
        return
    
    hit_v = list(hit_v)
    for i in range(len(hit_v)):
        hit_v[i] = int(eval(hit_v[i]))
    
    if cb_concluded:
        print('logmaster: cb has concluded')
        await channel.send('Could not log - CB has ended')
        return
    
    if not check_current_cb():
        print('logmaster: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return
    
    cb_id = int(current_cb)
    day = _getday(cb_id)
    
    if day == 0:
        print('log: day was None - start a new day!')
        await channel.send('Could not log - CB hasn\'t started!')
        return
    
    # find m_id
    find_mid = ("SELECT m_id, nick FROM cb.members "
                "WHERE nick LIKE '%{:s}%' LIMIT 1".format(nick))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(find_mid)
        for _m_id, nick in cb_cursor:
            m_id = int(_m_id)
            nick = str(nick)
    except mysql.connector.Error as err:
        print("logmaster:\n:", err)
        cb_cursor.close()
        await channel.send('I could not find you in our guild records, {:s}'.format(name))
        return

    # find existing records and append if nessecary
    find_log = ("SELECT entry_id, hit1, hit2, hit3 from cb.cb_log WHERE "
                "cb_id = {0:d} AND day = {1:d} AND m_id = {2:d} "
                "LIMIT 1".format(cb_id, int(day), m_id))

    try:
        cb_cursor.execute(find_log, )
        for eid, hit1, hit2, hit3 in cb_cursor:
            ex_hits = [int(hit1), int(hit2), int(hit3)]
            eid = int(eid)  
    except mysql.connector.Error as err:
        print("logmaster:\n:", err)
        cb_cursor.close()
        await channel.send('Oops, something went wrong...')
        return
    
    hits_left = ex_hits.count(0)

    if hits_left != 3:
        warn = True
        await channel.send('Warning: user has prexisting logs')
    else:
        warn = False

    if not warn or True:
        if warn:
            await channel.send('Updating despite warning...')
        if len(hit_v) == 3:
            hit1, hit2, hit3 = hit_v
            hits = 3 - hit_v.count(0)
            
        elif (hits_left - len(hit_v)) == 0:
            split = ex_hits.index(0)
            hit1, hit2, hit3 = (ex_hits[:split] + hit_v)
            hits = 3 - (ex_hits[:split] + hit_v).count(0)
            
        elif (hits_left - len(hit_v)) > 0:
            for hit in hit_v:
                ex_hits[ex_hits.index(0)] = hit_v.pop(0)
            hit1, hit2, hit3 = ex_hits
            hits = 3 - ex_hits.count(0)
            
        else:
            print('logmaster: invalid update inputs')
            await channel.send('Something went wrong - they have {0:d} hits left '\
                               'and you tried to update {1:d} hits'.format(hits_left, len(hit_v)))
            return
        
        # update
        update_log = ("UPDATE cb.cb_log SET "
                      "hit1 = {0:d}, "
                      "hit2 = {1:d}, "
                      "hit3 = {2:d}, "
                      "hits = {3:d} "
                      "WHERE entry_id = {4:d}".format(hit1, hit2, hit3, hits, eid))

        try:
            cb_cursor.execute(update_log, )
            cb_db.commit()
        except mysql.connector.Error as err:
            print("logmaster:\n:", err)
            cb_cursor.close()
            await channel.send('Oops, something went wrong while writing their log...')
            return

        await channel.send("Successfully updated **day {0:d}** log for **{1:s}**!"\
                           " They have **{2:d} hits remaining**. Ganbarimasu!".format(day, nick, 3-hits))
        print('logmaster: success')
        return
    else:
        print('logmaster: warn exit')
        return


# cb log
@cb.command(enabled=False)
async def log_old(ctx, *hit_v:str):
    channel = ctx.channel
    user_id = ctx.message.author.id
    name = ctx.message.author.name

    print(ctx.message.content)
    print(hit_v)
    
    # checks
    if len(hit_v) > 3:
        print('log: too many inputs')
        await channel.send('<:shioread:449255102721556490>')
        return

    hit_v = list(hit_v)
    temp = []
    for dmg in hit_v:
        dmg = dmg.split('+')
        for i in range(len(dmg)):
            try:
                dmg[i] = int(dmg[i])
            except:
                print('log: incorrect values input')
                await channel.send('<:shioread:449255102721556490>')
                return
        temp.append(sum(dmg))

    print(temp)
    hit_v = temp
    
    if cb_concluded:
        print('log: cb has concluded')
        await channel.send('Could not log - CB has ended')
        return
    
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return
    
    cb_id = int(current_cb)
    day = _getday(cb_id)
    
    if day == 0:
        print('log: day was None - start a new day!')
        await channel.send('Could not log - CB hasn\'t started!')
        return
    
    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE discord_tag LIKE '%{:d}%' LIMIT 1".format(user_id))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(find_mid, )
        m_id = 0
        for _m_id in cb_cursor:
            m_id = int(_m_id[0]) 
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        await channel.send('Something went wrong while fetching your records!')
        return
    print(m_id)
    if m_id == 0:
        print('log: no matching m_id')
        await channel.send('<:shioread:449255102721556490> I couldn\'t find your records, {:s}'.format(name))
        return
                           
    # find existing records and append if nessecary
    find_log = ("SELECT entry_id, hit1, hit2, hit3 from cb.cb_log WHERE "
                "cb_id = {0:d} AND day = {1:d} AND m_id = {2:d} "
                "LIMIT 1".format(cb_id, int(day), m_id))

    try:
        cb_cursor.execute(find_log, )
        for eid, hit1, hit2, hit3 in cb_cursor:
            ex_hits = [int(hit1), int(hit2), int(hit3)]
            eid = int(eid)  
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        await channel.send('Oops, something went wrong...')
        return
    
    hits_left = ex_hits.count(0)

    if len(hit_v) != 0:
        if len(hit_v) == 3:
            hit1, hit2, hit3 = hit_v
            hits = 3 - hit_v.count(0)
            
        elif (hits_left - len(hit_v)) == 0:
            split = ex_hits.index(0)
            hit1, hit2, hit3 = (ex_hits[:split] + hit_v)
            hits = 3 - (ex_hits[:split] + hit_v).count(0)
            
        elif (hits_left - len(hit_v)) > 0:
            for hit in hit_v:
                ex_hits[ex_hits.index(0)] = hit
            hit1, hit2, hit3 = ex_hits
            hits = 3 - ex_hits.count(0)
            
        else:
            print('log: invalid update inputs')
            await channel.send('Something went wrong - you have {0:d} hits left '\
                               'and you tried to update {1:d} hits'.format(hits_left, len(hit_v)))
            return
        
        # update
        update_log = ("UPDATE cb.cb_log SET "
                      "hit1 = {0:d}, "
                      "hit2 = {1:d}, "
                      "hit3 = {2:d}, "
                      "hits = {3:d} "
                      "WHERE entry_id = {4:d}".format(hit1, hit2, hit3, hits, eid))

        try:
            cb_cursor.execute(update_log, )
            cb_db.commit()
        except mysql.connector.Error as err:
            print("log:\n:", err)
            cb_cursor.close()
            await channel.send('Oops, something went wrong while writing your log...')
            return

        await channel.send("Successfully updated your **day {0:d}** log, **{1:s}**!"\
                           " You have **{2:d} hits remaining**. Ganbarimasu!".format(day, name, 3-hits))
        print('log: success')
        return
    else:
        await channel.send("**{0:s}**, it is currently **day {1:d}** of CB and you have **{2:d} hits** remaining. "\
                           "Ganbarimasu!".format(name, day, hits_left))
        print('log: success')
        return
    
"""
# cb logmaster
@cb.command()
async def logmaster(ctx, nick:str, *hit_v:int, mode=0):
    channel = ctx.channel
    #msgv = splitctx(ctx)
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return

    if len(hit_v) > 3:
        print('log: insufficient input')
        await channel.send('Could not log - too many inputs!')
        return

    hits = 0
    hits_default = [0 ,0, 0]
    for i in range(len(hit_v)):
        hits_default[i] = hit_v[i]
        if hit_v[i] > 0:
            hits += 1

    hit1, hit2, hit3 = hits_default
    
    cb_id = int(current_cb)
    #nick = msgv[0]
    #(hit1, hit2, hit3, hits) = msgv[1:5]

    #print(cb_id, nick, hit1, hit2, hit3)

    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE nick LIKE '%{:s}%' LIMIT 1".format(nick))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(find_mid)
        for _m_id in cb_cursor:
            m_id = int(_m_id[0])
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        await channel.send('Could not log - failed to fetch member data!')
        return

    # find_day
    day = _getday(cb_id)

    if day == 0:
        print('log: day was None - start a new day!')
        await channel.send('Could not log - no records to update - start a new day!')
        return

    #print(m_id)
    if str(mode) == '1':
        log_hit = ("INSERT INTO cb.cb_log "
                   "(hit1, hit2, hit3, hits, cb_id, m_id, day) "
                   "VALUES "
                   "({0:d}, {1:d}, {2:d}, {3:d}, {4:d}, {5:d}, {6:d})".format(hit1, hit2, hit3, hits, cb_id, m_id, day))
    else:
        log_hit = ("UPDATE cb.cb_log SET "
                   "hit1= {3:d}, "
                   "hit2 = {4:d}, "
                   "hit3 = {5:d}, "
                   "hits = {6:d} "
                   "WHERE cb_id = {1:d} "
                   "AND day = {2:d} "
                   "AND m_id = {0:d}".format(m_id, cb_id, day, int(hit1), int(hit2), int(hit3), int(hits))
                   )

    try:
        cb_cursor.execute(log_hit, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        await channel.send('Could not log - failed to update details!')
        return
    else:
        cb_cursor.close()
        print('log: success')
        await channel.send('Data successfully logged!')
        return
"""

# cb updatelog
@cb.command(aliases=['ul'])
async def updatelog(ctx):
    """
    Updates a field on a log
    Expects:
    [<e_id:str>, <field :str>, <value: str>]
    options:
        day
        hit1
        hit2
        hit3
        hits
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    if len(msgv) < 3:
        print('updatelog: insufficient inputs')
        await channel.send('Could not update - insufficient inputs!')
        return

    if msgv[1] not in ["day","hit1","hit2","hit3","hits"]:
        print('updatelog: invalid field param')
        await channel.send('Could not update - invalid field parameter supplied!')
        return
    
    e_id = int(msgv[0])
    field = str(msgv[1])
    value = int(msgv[2])
    if field[0] == "d":
        field = "day"

    update_log = ("UPDATE cb.cb_log "
                  "SET {0:s} = {1:d} "
                  "WHERE entry_id = {2:d}".format(field, value, e_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(update_log, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print('updatelog:\n', err)
        cb_cursor.close()
        await channel.send('Could not update log!')
        return
    else:
        cb_cursor.close()
        print('updatelog: success')
        await channe.send('Log successfully updated!')
        return

# cb removelog
@cb.command(aliases=['rl'])
async def removelog(ctx):
    """
    removes a log entry
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    if len(msgv) == 0:
        print('removelog: no entry_id supplied')
        await channel.send('Could not remove log - no `entry_id` supplied!')
        return

    e_id = int(msgv[0])
    remove_log = ("DELETE FROM cb.cb_log "
                  "WHERE entry_id = {:d}".format(e_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(remove_log, )
    except mysql.connector.Error as err:
        print('removelog:\n', err)
        cb_cursor.close()
        await channel.send('Could not remove log!')
        return
    else:
        cb_cursor.close()
        print('removelog: success')
        await channel.send('Successfully removed log!')
        return

# cb listlogs
@cb.command(aliases=['ll'])
async def listlogs(ctx):
    """
    Lists the complete log for a cb
    Expects:
    [<cb_id: str, default = 0>, <day: str, default = 0>]
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    if len(msgv) == 0:
        if not check_current_cb():
            print('listlogs: Unable to get current day or current CB!')
            await channel.send('Could not fetch current day or current CB!')
            return
        cb_id = int(current_cb)
        day = _getday(cb_id)

    elif len(msgv) == 1:
        print('listlogs: Insufficient inputs!')
        await channel.send('Insufficient inputs!')
        return
    
    elif len(msgv) > 1:
        if msgv[0] == '0':
            if not check_current_cb():
                print('listlogs: Unable to get current CB!')
                await channel.send('Could not fetch current CB!')
                return
            cb_id = int(current_cb)
        else:
            cb_id = int(msgv[0])
            
        day = int(msgv[1])

    get_date = ("SELECT start_date FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    
    get_logs = ("SELECT l.entry_id, cb.members.nick, "
                "l.hits, (l.hit1 + l.hit2 + l.hit3) AS tot "
                "FROM cb.cb_log AS l "
                "INNER JOIN cb.members ON cb.members.m_id = l.m_id "
                "WHERE l.cb_id = {0:d} "
                "AND l.day = {1:d} "
                "ORDER BY l.hits DESC".format(cb_id, day))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(get_date)
        for _date in cb_cursor:
            date = _date[0]
        cb_cursor.execute(get_logs, )
    except mysql.connector.Error as err:
        print("listlog:\n:", err)
        cb_cursor.close()
        await channel.send('Could not fetch log data!')
        return
    else:
        c1 = []
        c2 = []
        c3 = []
        for (_e_id, _tag, _hits, _tot) in cb_cursor:
            if len(str(_tag)) > 10:
                _tag = str(_tag)[:10] + '...'
            c1.append(" - ".join((str((_e_id)), _tag)))
            c3.append(str(_hits))
            c2.append(str(_tot))
        cb_cursor.close()
        print('listlogs: success')
        data = [day, c1, c2, c3, str(date)]
        print(data)
        if isempty(data):
            print('listlogs: empty data')
            await channel.send('No data fetched!')
            return
        await channel.send(embed=listlogsembed(ctx, data))
        return

"""
def _endday(msgv):

    'concludes the current day. Depreciated'

    if len(msgv) == 0:
        print('endday: insufficient inputs')
        return False
    if not check_current_cb():
        print('endday: current CB is not set')
        return False

    cb_id = int(current_cb)
    day = int(msgv[0])

    # find all members who are active and did not hit
    find_slackers = ("SELECT m.m_id "
                     "FROM cb.members m "
                     "LEFT JOIN cb.cb_log l "
                     "ON l.m_id = m.m_id "
                     "AND m.active <> 0 "
                     "AND l.day = {0:d} "
                     "AND l.cb_id = {1:d} "
                     "WHERE hits IS NULL".format(day, cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(find_slackers, )
    except mysql.connector.Error as err:
        print('endday:\n', err)
        cb_cursor.close()
        return False

    # checking returned results, check if 0, 1 or multiple results
    m_id = []
    for (_m_id) in cb_cursor:
        m_id.append(_m_id[0])

    if len(m_id) == 0:
        print('endday: no m_id found')
        cb_cursor.close()
        return True
    #if len(m_id) == 1:
    #    m_id[0] = m_id[0][0]
    print(m_id)
    # insert data for slackers
    insert_slackers = "INSERT INTO cb.cb_log "\
                      "SET m_id = {0:d}, "\
                      "hit1 = 0, hit2 = 0, hit3 = 0, hits = 0, "\
                      "day = {1:d}, cb_id = {2:d}"
    try:
        for mid in m_id:
            cb_cursor.execute((insert_slackers.format(int(mid), day, cb_id)))
            cb_db.commit()
    except mysql.connector.Error as err:
        print('endday:\n', err)
        cb_cursor.close()
        return False
    else:
        cb_cursor.close()
        return True
"""

# cb forceReload
@cb.command()
async def forceReload(ctx, guild:str):
    channel = ctx.channel
    author = ctx.message.author
    if str(author.id) != '235361069202145280':
        print('forceReload: author has no permission')
        return

    role_id, guild = getrole(guild)
    if role_id == 'None':
        print('forceReload: no role found')
        return
    
    roster = []
    for member in ctx.message.guild.members:
        for role in member.roles:
            if str(role.id) == role_id:
                roster.append((member, guild))

    update = "UPDATE cb.members SET discord_tag = '{0:s}' "\
             "WHERE discord_tag LIKE '%{1:s}%'"
    print(len(roster))
    try:
        cursor = cb_db.cursor()
        for member, guild in roster:
            cursor.execute((update.format(str(member.id), str(member.name))),)
        cb_db.commit()
    except mysql.connector.Error as err:
        print("forceReload:\n:", err)
        cb_cursor.close()
        return
    else:
        cursor.close()
        print('forceReload: success')
        return                 

# cb reload
@cb.command()
async def reload(ctx):
    """
    Updates cb.members with all members in context guild with the same role specified by msgv
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    
    if len(msgv) == 0:
        print('reload: no role supplied')
        return 'Could not refresh roster - no role supplied!'
    
    role_id, guild = getrole(msgv[0])
    if role_id == 'None':
        print('reload: no role found')
        await channel.send('Invalid guild input!')
        return

    print('reload: role received: ' + role_id)

    data = getmembers(guild)
    if not isempty(data[:-1]):
        data = data[1] # d_tag
    roster = []
    
    for member in ctx.message.guild.members:
        if not ("#".join((member.name, member.discriminator)) in data):
            for role in member.roles:
                if str(role.id) == role_id:
                    roster.append((member, guild))
        #elif ("#".join((member.name, member.discriminator)) in data):
        #    data.remove("#".join((member.name, member.discriminator)))
                
    if len(roster) == 0:
        print('reload: no members with role found')
        await channel.send('No new members with role found - Roster remains unchanged!')
        return
    else:
        print('reload: success')
        await _addmember(ctx, roster)
        return

# cb updatemember
@cb.command(aliases=['um'])
async def updatemember(ctx):
    """
    Updates a certain field in cb.members
    Expects:
    [<nick :str>,
    <field: str, nick|active>,
    value: str, nick|active>
    ]
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    
    if len(msgv) < 3:
        print('updatemember: insufficient input')
        await channel.send('Could not update member - insufficient input supplied!')
        return
    if msgv[1] not in ["nick","active"]:
        print('updatemember: invalid field supplied')
        await channel.send('Could not update member - invalid field supplied!')
        return

    nick = msgv[0]
    
    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE nick LIKE '%{:s}%' LIMIT 1".format(nick))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(find_mid)
        for _m_id in cb_cursor:
            m_id = int(_m_id[0])
    except mysql.connector.Error as err:
        print("updatemember:\n:", err)
        cb_cursor.close()
        await channel.send('Could not update member - failed to find member data!')
        return
    
    field = msgv[1]
    value = msgv[2]

    update_member_nick = ("UPDATE cb.members "
                     "SET {0:s} = '{1:s}' "
                     "WHERE m_id = {2:d}".format(field, value, m_id))

    update_member_active = ("UPDATE cb.members "
                     "SET {0:s} = {1:s} "
                     "WHERE m_id = {2:d}".format(field, value, m_id))
    try:
        cb_cursor = cb_db.cursor()
        if field == 'nick':
            cb_cursor.execute(update_member_nick, )
        if field == 'active':
            cb_cursor.execute(update_member_active, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print("updatemember:\n:", err)
        cb_cursor.close()
        await channel.send('Could not update member - failed to update!')
        return
    else:
        cb_cursor.close()
        print('updatemember: success')
        await channel.send('Successfully updated member record!')
        return

# cb removemember
@cb.command(aliases=['rm'])
async def removemember(ctx):
    """
    Deletes a member's record given m_id
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    
    if len(msgv) == 0:
        print('removemember: no m_id supplied')
        await channel.send('Could not remove member record - no `m_id` supplied!')
        return
    else:
        m_id = int(msgv[0])

    query_delete_child = ("DELETE FROM cb.cb_log "
                    "WHERE m_id = {:d}".format(m_id))
    
    query_delete = ("DELETE FROM cb.members "
                    "WHERE m_id = {:d}".format(m_id))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_delete_child)
        cb_db.commit()
        cb_cursor.execute(query_delete)
        cb_db.commit()
        cb_cursor.close()
    except mysql.connector.Error as err:
        print("removemember:\n:", err)
        cb_cursor.close()
        await channel.send('Could not remove member record - failed to remove record!')
        return
    else:
        print('removemember: success')
        await channel.send('Successfully removed member record!')
        return

# cb listmembers
@cb.command()
async def listmembers(ctx):
    """
    Creates data needed for listmembersembed
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    if len(msgv) > 0:
        if msgv[0] == '0':
            mode = 0
            mode_name = 'Inactive'
        elif msgv[0] == '1':
            mode = -1
            mode_name = 'Full'
        else:
            print('listmembers: received incorrect command: ' + msgv[0])
            await channel.send('Invalid input!')
            return
    else:
        mode = 1
        mode_name = 'Active'

    if mode == -1:
        query_listmembers = (
                "SELECT m_id, discord_tag, nick, active, guild "
                "FROM cb.members ORDER BY active DESC")
    else:
        query_listmembers = (
            "SELECT m_id, discord_tag, nick, active, guild "
            "FROM cb.members "
            "WHERE active = {:d}".format(mode))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_listmembers, )
        m_id = []
        d_tag = []
        nick = []
        active = []
        guild = ""
        for (_m_id, _d_tag, _nick, _active, _guild) in cb_cursor:
            m_id.append(str(_m_id))
            d_tag.append(_d_tag)
            active.append(str(_active))
            if len(_nick) > 23:
                nick.append(str(_nick)[:22]+"...")
            else:
                nick.append(str(_nick))
            guild = str(_guild)
    except mysql.connector.Error as err:
        print("listmembers:\n:", err)
        cb_cursor.close()
        await channel.send('Could not fetch data!')
        return
    else:
        cb_cursor.close()
        print('listmembers: success')
        guild = guildname(guild)
        data = [m_id, d_tag, nick, active, mode_name, guild]
        if isempty(data[:-2]):
            print('listmembers: empty data')
            await channel.send('No data fetched!')
            return
        print(data)
        await channel.send(embed=listmembersembed(ctx, data))
        return

# cb newcb
@cb.command(aliases=['new'])
async def newcb(ctx):
    # .cb newcb [start date yyyy-mm-dd] [span default = SPAN_DAYS] [set default = 1]
    """
    Inserts a cb entry into cb.cb_lists.
    Expects:
    [<start_date: str, format yyyy-mm-dd>,
    <current: int, optional, default = 1>,
    <span_days: int, optional, default = span_days>]
    """
    global current_cb, cb_concluded
    channel = ctx.channel
    msgv = splitctx(ctx)
    
    #print(msgv)
    if len(msgv) == 0:
        print('newcb: insufficient inputs')
        await channel.send('Could not add new CB - insufficient inputs supplied!')
        return
    
    inpdate = datetime.datetime.strptime(msgv[0], '%Y-%m-%d')
    #print(inpdate.strftime('%Y-%m-%d'))
    default = 1
    span = span_days
    
    if len(msgv) > 1:
        span = msgv[1]
        if len(msgv) > 2:
            default = msgv[2]
    
    new_cb = ("INSERT INTO cb.cb_list "
              "(start_date, current, span_days) "
              "VALUES ('{0:s}', {1:d}, {2:d})".format(inpdate.strftime('%Y-%m-%d'), int(default), int(span)))
    
    get_cbid = ("SELECT cb_id from cb.cb_list "
                "WHERE current = 1")
    
    try:
        if default:
            _resetcbc()
            await concludecb.invoke(ctx)
            cb_concluded = False
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(new_cb, )
        cb_db.commit()
        cb_cursor.execute(get_cbid, )
        for (cb_id) in cb_cursor:
            current_cb = cb_id[0]
    except mysql.connector.Error as err:
        print('newcb:\n', err)
        cb_cursor.close()
        await channel.send('Could not add new CB - failed to add new entry!')
        return
    else:
        cb_cursor.close()
        print('newcb: success')
        await channel.send('Successfully added new CB entry!')
        return

# cb setcb
@cb.command(aliases=['set'])
async def setcb(ctx):
    """
    Sets the given cb_id to have current value = 1. If not provided, global current_cb will be set instead via db
    expects:
    [<cb_id: int, optional>]
    """
    global current_cb
    channel = ctx.channel
    msgv = splitctx(ctx)
    print(msgv)
    
    if len(msgv) > 0:
        cb_id = msgv[0]
        set_cb = ("UPDATE cb.cb_list "
                  "SET current = 1 "
                  "WHERE cb_id = {:d}".format(int(cb_id)))

        try:
            _resetcbc()
            cb_cursor = cb_db.cursor()
            cb_cursor.execute(set_cb, )
            cb_db.commit()
            current_cb = cb_id
        except mysql.connector.Error as err:
            print('setcb:\n', err)
            cb_cursor.close()
            await channel.send('Could not set current CB via supplied `cb_id`!')
            return
        else:
            cb_cursor.close()
            await channel.send('Successfulled set current CB!')
            return
    else:
        query = ("SELECT cb_id FROM cb.cb_list "
                 "WHERE current = 1")
        
        try:
            cb_cursor = cb_db.cursor()
            cb_cursor.execute(query, )
            for (_id) in cb_cursor:
                if str(_id) == 'None':
                    print('setcb: no active cb found in db')
                    await channel.send('Could not set current CB - no active CB found in DB!')
                    return
                current_cb = _id[0]
        except mysql.connector.Error as err:
            print('setcb:\n', err)
            cb_cursor.close()
            await channel.send('Could not set current CB via database!')
            return
        else:
            cb_cursor.close()
            print('setcb: success')
            await channel.send('Successfully set current CB via DB!')
            return

# cb updatecb
@cb.command(aliases=['ucb'])
async def updatecb(ctx):
    """
    updates a field in cb.cb_list
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    
    if len(msgv) < 3:
        print('updatecb: insufficient inputs')
        await channel.send('Could not update CB - insufficient inputs supplied!')
        return
    if msgv[1] not in ["date", "span"]:
        print('updatecb: invalid field')
        await channel.send('Could not update CB - invalid field supplied!')
        return
    cb_id = msgv[0]
    field = msgv[1]
    value = msgv[2]
    
    if field == 'date':
        field = 'start_date'
        value = datetime.datetime.strptime(value, '%Y-%m-%d')
        update_cblist = ("UPDATE cb.cb_list "
                         "SET start_date = '{0:s}' "
                         "WHERE cb_id = {1:d}".format(value.strftime('%Y-%m-%d'), int(cb_id)))
    
    if field == 'span':
        field = 'span_days'
        value = int(value)
        update_cblist = ("UPDATE cb.cb_list "
                         "SET span_days = {0:d} "
                         "WHERE cb_id = {1:d}".format(value, int(cb_id)))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(update_cblist, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print("updatecb:\n", err)
        cb_cursor.close()
        await channel.send('Could not update CB!')
        return
    else:
        cb_cursor.close()
        print('updatecb: success')
        await channel.send('Successfully updated CB!')
        return

# cb removecb
@cb.command(aliases=['rcb'])
async def removecb(ctx):
    """
    Removes a cb role given a cb_id
    """
    channel = ctx.channel
    msgv = splitctx(ctx)
    
    if len(msgv) == 0:
        print('removecb: no cb_id supplied')
        await channel.send('Could not remove CB entry - no `cb_id` supplied!')
        return
    cb_id = int(msgv[0])

    query_delete_child = ("DELETE FROM cb.cb_log "
                          "WHERE cb_id = {:d}".format(cb_id))
    
    query_delete = ("DELETE FROM cb.cb_list "
                    "WHERE cb_id = {:d}".format(cb_id))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_delete_child)
        cb_db.commit()
        cb_cursor.execute(query_delete)
        cb_db.commit()
    except mysql.connector.Error as err:
        print('removecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not remove CB entry!')
        return
    else:
        cb_cursor.close()
        print('removecb: success')
        await channels.send('Successfully removed CB entry!')
        return

# cb statscb
@cb.command()
async def statscb(ctx, cb_id=None):
    """
    Returns details needed for statscbembed.
    """
    channel = ctx.channel

    if cb_id:
        cb_id = int(cb_id)
    else:
        if not check_current_cb():
            await channel.send('No CB set!')
            return
        cb_id = int(current_cb)

    #print(cb_id)
    query_stats = ("SELECT start_date, span_days, total, active_members "
                   "FROM cb.cb_list "
                   "WHERE cb_id = {:d}".format(cb_id))
    
    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_stats, )
        data = []
        for (date, days, tot, active) in cb_cursor:
            data = [str(date), days, tot, active, str(cb_id)]
    except mysql.connector.Error as err:
        print('statcb:\n', err)
        cb_cursor.close()
        await channel.send('Could not fetch data!')
        return
    else:
        cb_cursor.close()
        print('statscb: success')
        if isempty(data):
            print('statscb: no data fetched')
            await channel.send('No data fetched!')
        await channel.send(embed=statscbembed(ctx,data))
        return

# cb listcb
@cb.command()
async def listcb(ctx):
    """
    Returns the data of the 10 latests cb data for listcbembed.
    """
    channel = ctx.channel
    
    query_list = ("SELECT cb_id, start_date, total "
                  "FROM cb.cb_list "
                  "ORDER BY cb_id DESC "
                  "LIMIT 10")
    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_list, )
        cb_idv = []
        datev = []
        totalv = []
        for (cb_id, start_date, total) in cb_cursor:
            cb_idv.append(str(cb_id))
            datev.append(str(start_date))
            totalv.append(str(total))
    except mysql.connector.Error as err:
        print('listcb:\n', err)
        cb_cursor.close()
        await channel.send('Could not fetch data!')
        return
    else:
        cb_cursor.close()
        print('listcb: success')
        data = [cb_idv, datev, totalv]
        if isempty(data):
            print('listcb: no data fetched')
            await channel.send('No data fetched!')
            return
        await channel.send(embed=listcbembed(ctx,data))
        return

# cb concludecb
@cb.command(aliases=['concl','conclude'])
async def concludecb(ctx):
    """
    aggregates data, and calls statscb
    """
    global cb_concluded
    channel = ctx.channel
    if not check_current_cb():
        print('concludecb: no cb set')
        await channel.send('Current CB not set')
        return

    cb_id = int(current_cb)
    
    query_total = ("SELECT (SUM(hit1) + SUM(hit2) + sum(hit3)) AS total, COUNT(DISTINCT m_id) AS active "
                   "FROM cb.cb_log "
                   "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    
    # update cb
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_total, )

        for (_total, _activem) in cb_cursor:
            total = _total
            activem = _activem

        update_conclude = ("UPDATE cb.cb_list "
                           "SET total = {0:d}, active_members = {1:d} "
                           "WHERE cb_id = {2:d}".format(int(total), int(activem), cb_id))
        
        cb_cursor.execute(update_conclude, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not update CB data!')
        return

    # collect player aggregate
    query_player = ("SELECT m.nick, SUM((l.hit1 + l.hit2 + l.hit3)) AS total, "
                    "SUM(l.hits) AS total_hits "
                    "FROM cb.cb_log AS l "
                    "INNER JOIN cb.members AS m "
                    "ON m.m_id = l.m_id "
                    "WHERE cb_id = {:d} "
                    "GROUP BY l.m_id".format(cb_id))
    try:
        cb_cursor.execute(query_player, )
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not aggregate data!')
        return
    else:
        tag = []
        tot = []
        toth = []
        for (_tag, _tot, _toth) in cb_cursor:
            if len(str(_tag)) > 10:
                _tag = str(_tag)[:10] + '...'
            tag.append(str(_tag))
            tot.append(str(_tot))
            toth.append(str(_toth))

    query_date = ("SELECT start_date, span_days "
                  "FROM cb.cb_list "
                  "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
         cb_cursor.execute(query_date)
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not fetch Cb data!')
        return
    else:
        for (_date, _days) in cb_cursor:
            date = _date
            days = _days
        cb_cursor.close()
        cb_concluded = True
        print('concludecb: success')
        data = [str(date), int(days), int(total), str(activem), tag, tot, toth]
        if isempty(data):
            print('concludecb: no data fetched')
            await channel.send('No data fetched!')
        await channel.send(embed=concludecbembed(ctx,data))
        return

# cb help
cb.command(alias=['help'])
async def cbhelp(ctx):
    await channel.send(embed=helpcbembed(ctx))

# EMBEDS
def concludecbembed(context, data):
    embed = discord.Embed(title="CB Conclusion report", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name=data[0]+" CB Summary", icon_url=context.message.author.avatar_url)
    embed.add_field(name="Days", value=data[1], inline=True)
    embed.add_field(name="Guild Damage", value=data[2], inline=True)
    embed.add_field(name="Active Members", value=data[3], inline=True)
    embed.add_field(name="Member", value="\n".join(data[4]), inline=True)
    embed.add_field(name="Total Damage", value="\n".join(data[5]), inline=True)
    embed.add_field(name="Total Hits", value="\n".join(data[6]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def listlogsembed(context, data):
    embed = discord.Embed(title="Log for day {:d}".format(data[0]), description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name=data[4]+" CB Log", icon_url=context.message.author.avatar_url)
    embed.add_field(name="EID", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Total Damage", value="\n".join(data[2]), inline=True)
    embed.add_field(name="Hits", value="\n".join(data[3]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def listmembersembed(context, data):
    embed = discord.Embed(title="{0:s} {1:s} Guild Roster".format(data[4],data[-1]), description="{:d} records retrieved. Prepared by yours truly.".format(len(data[0])), timestamp=datetime.datetime.utcnow())
    embed.set_author(name="Roster", icon_url=context.message.author.avatar_url)
    embed.add_field(name="M_ID", value="\n".join(data[0]), inline=True)
    #embed.add_field(name="Discord", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Nickname", value="\n".join(data[2]), inline=True)
    if data[4] == 'Full':
        embed.add_field(name="Active", value="\n".join(data[3]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def statscbembed(context, data):
    embed = discord.Embed(title="Clan Battle Report (minimal)", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Stats", icon_url=context.message.author.avatar_url)
    embed.add_field(name="CB ID", value=data[4], inline=False)
    embed.add_field(name="Start date", value=data[0], inline=True)
    embed.add_field(name="Total days", value=data[1], inline=True)
    embed.add_field(name="Total damage", value=data[2], inline=True)
    embed.add_field(name="Active members", value=data[3], inline=True)
    embed.set_footer(text="still in testing")
    return embed

def listcbembed(context, data):
    embed = discord.Embed(title="Clan Battle Log (minimal)", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Log", icon_url=context.message.author.avatar_url)
    embed.add_field(name="CB ID", value="\n".join(data[0]), inline=True)
    embed.add_field(name="Start date", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Total damage", value="\n".join(data[2]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def cbhelpembed(context):
    embed = discord.Embed(title="Clan Battle Command List", description="Here's what I can do", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Help", icon_url=context.message.author.avatar_url)
    embed.add_field(name="pcb",
                    value="I will tell you the current set CB and how far in we are along with its date and `cb_id`.")
    embed.add_field(name="startday",
                    value="I begin finalise yesterday's battle logs and begin a new day, given that I know what the current CB is.\n")
    embed.add_field(name="log `[nick]` `[hit1]` `[hit2]` `[hit3]` `[hits]`",
                    value="I will log the hit data provided for the current member with `nick` given I know the current CB and day. All fields must be provided.\n")
    embed.add_field(name="removelog [`eid`]",
                    value="I will remove the CB log with entry ID `eid`.\n")
    embed.add_field(name="listlogs `[cbid(optional)]` `[day(optional)]`",
                    value="I will fetch CB logs for the current CB if nothing is provided, otherwise I will fetch the logs of CB with an ID `cbid`. If so, `day` data must be provided.\n")
    embed.add_field(name="update log `[eid]` `[field:day|hit1|hit2|hit3|hits]` `[value]`",
                    value="I will update log the with an ID of `eid`. All fields must be provided.\n")
    embed.add_field(name="update member `[nick]` `[field:nick|active]` `[value]`",
                    value="I will update the member with an ID of `mid`. All fields must be provided.\n")
    embed.add_field(name="update cb `[cbid]` `[field:date|span]` `[value]`",
                    value="I will update the CB with an ID of `cbid`. All fields must be provided.\n")
    embed.add_field(name="reload `[role:b(lue)|y(ellow)|g(reen)]`",
                    value="I will find all members with the current role and update it to the guild members record. This is the recommended to be done before every CB.\n")
    embed.add_field(name="removemember `[mid]`",
                    value="I will remove the member with an member ID of `mid`. It is not recommended to use this as you will lose data about their CB contribution. Instead, update their `active` tag to 0.\n")
    embed.add_field(name="listmembers `[mode(optional):0|1]`",
                    value="I will fetch the member list of the guild. If no input is provided, the list will only contain `active` members. If its 0, I will fetch all `inactive` members. If its 1, I will fetch everything.\n")
    embed.add_field(name="newcb `[start_date:yyyy-mm-dd]` `[span(optional):default={:d}]` `[set_cb(optional):default=1]`".format(span_days),
                    value="I will create a new CB entry and set it as the current CB. The starting date must be provided. This will automatically `conclude` the current CB if `set_cb` is set to `1`.\n")
    embed.add_field(name="setcb `[cb_id(optional)]`",
                    value="I will set the current CB to be the one with `cb_id` if its provided. Otherwise I will fetch the current CB from the database and set that as the current CB.\n")
    embed.add_field(name="removecb `[cbid]`",
                    value="I will remove the CB with an ID of `cbid` along with all CB logs associated with it.`\n")
    embed.add_field(name="statscb `[cbid(optional)]`",
                    value="I will fetch the data for either the current CB or the one with ID `cbid` if provided. The data will be minimal due to Discord.\n")
    embed.add_field(name="listcb",
                    value="I will fetch the latst 10 CBs and their data.\n")
    embed.add_field(name="concludecb",
                    value="I will wrap up the CB and aggregate data logged.\n")
    return embed
        
# MISC FUNCTIONS
def getmembers(_guild:str):
    role, guild = getrole(_guild)
    if guild == 'None':
        return []
    query_listmembers = (
                "SELECT m_id, discord_tag, nick, active "
                "FROM cb.members "
                "WHERE guild = '{:s}'".format(guild))
    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_listmembers, )
        m_id = []
        d_tag = []
        nick = []
        active = []
        for (_m_id, _d_tag, _nick, _active) in cb_cursor:
            m_id.append(str(_m_id))
            d_tag.append(_d_tag)
            active.append(str(_active))
            if len(_nick) > 23:
                nick.append(str(_nick)[:22]+"...")
            else:
                nick.append(str(_nick))
            guild = str(_guild)
    except mysql.connector.Error as err:
        print("getmembers:\n:", err)
        cb_cursor.close()
        return []
    else:
        cb_cursor.close()
        print('getmembers: success')
        guild = guildname(guild)
        data = [m_id, d_tag, nick, active, guild]
        if isempty(data[:-1]):
            print('getmembers: empty data')
            return []
        print(data)
        return data

def _resetcbc():
    """
    Sets all cb.cb_lists.current values to 0.
    """
    set_reset = ("UPDATE cb.cb_list "
                 "SET current = 0")
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(set_reset, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print('_resetcbc:\n', err)
        cb_cursor.close()
        return False
    else:
        cb_cursor.close()
        print('_resetcbc: success')
        return True

async def _addmember(ctx, roster=[]):
    """
    Adds a member to cb.members. Expects roster to be an array of discord member objects
    """
    channel = ctx.channel
    
    if len(roster) == 0:
        print('addmember: roster is empty')
        await channel.send('Could not add members - new members list is empty!')
        return
    
    member_data = []
    for member, _guild in roster:
        guild = _guild
        if str(member.nick) == 'None':
            nick = ""
        else:
            nick = str(member.nick)
        member_data.append(
            (
            str(member.id),
            " ".join((member.name, nick))
            )
        )

    query_addm = "INSERT INTO cb.members (guild, discord_tag, nick, active) "\
                 "VALUES ('{2:s}', '{0:s}', '{1:s}', 1)"
    try:
        cb_cursor = cb_db.cursor()
        for (discord_tag, nick) in member_data:
            cb_cursor.execute((query_addm.format(discord_tag, nick, guild)))
            cb_db.commit()
    except mysql.connector.Error as err:
        print("addmember:\n:", err)
        cb_cursor.close()
        await channel.send('Could not add member - failed to insert data!')
        return
    else:
        cb_cursor.close()
        print('addmember: success')
        await channel.send('Successfulled added new members!')
        return

def _getday(cb_id):
    get_day = ("SELECT MAX(day) FROM cb.cb_log "
               "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(get_day, )
        for (_day) in cb_cursor:
            day = str(_day[0])
    except mysql.connector.Error as err:
        print('_getday:\n', err)
        cb_cursor.close()
        return False

    if day == 'None':
        day = 0
    else:
        day = int(day)
    print('_getday: success')
    return day

def _checkconcl():
    global cb_concluded
    if not check_current_cb():
        print('_checkconcl: failed to set current cb status - curent_cb not set')
        return False

    cb_id = int(current_cb)

    get_date = ("SELECT start_date, span_days FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(get_date, )
    except mysql.connector.Error as err:
        print('_checkconcl:\n', err)
        cb_cursor.close()
        return False
    else:
        for (sd, span) in cb_cursor:
            pass
        cb_concluded = (datetime.datetime.strptime(str(sd), '%Y-%m-%d') + datetime.timedelta(days=int(span))) < datetime.datetime.utcnow()
        print(cb_concluded)
        print('_checkconcl: success')
        return True

async def cb_init(ctx):
    """
    Initialises the basic requirements for operating the cb command and checks at every call
    """
    global current_cb
    channel = ctx.channel
    # check if cb_db is connected
    if not check_db_isconnected():
        print('cb_init: DB is not connected - exiting command')
        await ctx.channel.send('Database is not connected!')
        return False

    # check and set current_cb
    if not check_current_cb():
        print('cb_init: global current_cb is not set. Attempting to set via database.')
        query = ("SELECT cb_id FROM cb.cb_list "
                 "WHERE current = 1")
        
        try:
            cb_cursor = cb_db.cursor()
            cb_cursor.execute(query, )
            for (_id) in cb_cursor:
                if str(_id) == 'None':
                    print('cb_init: no active cb found in db')
                    #await channel.send('Could not set current CB - no active CB found in DB!')
                    return
                current_cb = _id[0]
        except mysql.connector.Error as err:
            print('cb_init:\n', err)
            cb_cursor.close()
            #await channel.send('Could not set current CB via database!')
            return
        else:
            _checkconcl()
            cb_cursor.close()
            print('cb_init: success')
            #await channel.send('Successfully set current CB via DB!')
            return
        
    return True
    
def getrole(guild:str):
    """
    returns the role number for the guild specified
    """
    if guild[0] == 'b':
        return '547686074302857218', 'b'
    elif guild[0] == 'y':
        return 'None', 'y', 
    elif guild[0] == 'g':
        return 'None', 'g'
    else:
        return 'None', 'None'

def splitctx(ctx):
    return ctx.message.content.lower().split(" ")[2:]

def check_cb_concluded():
    return bool(cb_concluded)

def check_current_cb():
    return bool(current_cb)

def check_db_isconnected():
    return bool(db_isconnected)

def check_author(author):
    """
    check author for lock-in commands
    """
    def inner_check(message):
        return message.author == author
    return inner_check

def isempty(inList):
    """
    checks if data returned is empty
    """
    if isinstance(inList, list): # Is a list
        return all( map(isempty, inList) )
    return False

def guildname(guild:str):
    if guild == 'g':
        return 'Green'
    elif guild == 'b':
        return 'Blue'
    elif guild == 'y':
        return 'Yellow'
    else:
        return 'None'

# DATABASE RELATED
@client.command()
async def _connectdb(context):
    global db_isconnected
    await context.channel.send('Connecting to database...')
    if not db_isconnected:
        if connect_db():
            await context.channel.send('Connection successful!')
        else:
            await context.channel.send('Connection failed.')
    else:
        await context.channel.send('Database is already connected!')

@client.command()
async def _disconnectdb(context):
    global db_isconnected
    await context.channel.send('Disconnecting from database...')
    if db_isconnected:
        if connect_db(0):
            await context.channel.send('Disconnected!')
        else:
            await context.channel.send('Failed to disconnect.')
    else:
        await context.channel.send('Database not connected!')

def connect_db(mode=1):    
    global cb_db, db_name, db_pw, db_host, db_dbname, db_isconnected
    
    if mode:
        print('connecting to database...')
        try:
            cb_db = mysql.connector.connect(
                user = db_name,
                password = db_pw,
                host = db_host,
                database = db_dbname)
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print('connection failed: access denied')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print('connection failed: database does not exist')
            else:
                print(err)
            return False
            
        else:
            print('connected')
            db_isconnected = 1
            return True
        
    else:
        print('disconnecting from database...')
        try:
            cb_db.close()
            
        except mysql.connector.Error as err:
            print(err)
            return False
        
        else:
            print('disconnected')
            db_isconnected = 0
            return True

# tests
# cb log test version
@cb.command()
async def log(ctx, *hit_v:str):
    channel = ctx.channel
    user_id = ctx.message.author.id
    name = ctx.message.author.name
    error = '<:shioread:449255102721556490>'

    # check input length
    if len(hit_v) > 3:
        print('logtest: too many inputs')
        await channel.send(error)
        return

    mode = len(hit_v)
    if hit_v.count('0') == 3:
        print('logtest: reset request detected')
        reset = True
    else:
        reset = False

    # check if current cb is set
    if not check_current_cb():
        print('logtest: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return

    # check if current cb has concluded
    if not check_current_cb():
        print('logtest: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return
    
    # grab cb_id and current day
    cb_id = int(current_cb)
    day = _getday(cb_id)

    # check if cb has been initiated
    if day == 0:
        print('logtest: day was None - start a new day!')
        await channel.send('Could not log - CB hasn\'t started!')
        return
    
    # unpack hit_v
    if not reset:
        hit_v = list(hit_v)
        totdmg = []
        meta = []
        for log_ in hit_v:
            tempsum = []
            tempmeta = []
            for hit in log_.split('+'):
                # check if input is of form wave-boss:dmg
                # check if wave-boss is valid and do sanity check on numbers
                print(hit)
                try:
                    meta_, dmg = hit.split(':')
                except:
                    print('logtest: could not split metadata:dmg in a hit')
                    await channel.send(error+' There was an error when trying to read your `metadata:damage` input.')
                    return
                try:
                    wave, boss = meta_.split('-')
                except:
                    print(error+'logtest: could not split wave-boss in metadata of a hit')
                    await channel.send(error+' There was an error when trying to read your `wave-boss` input.')
                    return
                try:
                    wave_check = int(wave)
                    boss_check = int(boss)
                    dmg_int = int(dmg)
                    if wave_check <= 0 or boss_check <= 0 or boss_check > 6 or wave_check > 25:
                        print('logtest: bad wave-boss input - failed sanity check')
                        await channel.send(error+' One or more of your wave-boss input is too wild')
                        return
                except:
                    print('logtest: invalid inputs')
                    await channel.send(error+' Did not recognise input type. Make sure you used integers.')
                    return
                
                tempsum.append(dmg_int)
                tempmeta.append(':'.join([meta_,dmg]))
                
            totdmg.append(sum(tempsum))
            meta.append(".".join(tempmeta))
    else:
        totdmg = [0,0,0]
        meta = ['0-0:0','0-0:0','0-0:0']

    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE discord_tag LIKE '%{:d}%' LIMIT 1".format(user_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(find_mid, )
        m_id = 0
        for _m_id in cb_cursor:
            m_id = int(_m_id[0]) 
    except mysql.connector.Error as err:
        print("logtest:\n:", err)
        cb_cursor.close()
        await channel.send('Something went wrong while fetching your records!')
        return
    
    if m_id == 0:
        print('logtest: no matching m_id')
        await channel.send('<:shioread:449255102721556490> I couldn\'t find your records, {:s}'.format(name))
        return

    
    # find existing records and append if nessecary
    find_log = ("SELECT "
                "entry_id, hit1, hit1meta, hit2, hit2meta, hit3, hit3meta from cb.cb_log WHERE "
                "cb_id = {0:d} AND day = {1:d} AND m_id = {2:d} "
                "LIMIT 1".format(cb_id, int(day), m_id))
    print(find_log)
    try:
        cb_cursor.execute(find_log, )
        for eid, hit1, hit1m, hit2, hit2m, hit3, hit3m in cb_cursor:
            ex_hits = [int(hit1), int(hit2), int(hit3)]
            m_hits = [str(hit1m), str(hit2m), str(hit3m)]
            eid = int(eid)  
    except mysql.connector.Error as err:
        print("logtest:\n:", err)
        cb_cursor.close()
        await channel.send('Oops, something went wrong...')
        return
    
    hits_left = ex_hits.count(0)

    if mode != 0:            
        if len(totdmg) == 3:
            hit1, hit2, hit3 = totdmg
            hit1m, hit2m, hit3m = meta
            hits = 3 - totdmg.count(0)
                
        elif (hits_left - len(hit_v)) == 0:
            split = ex_hits.index(0)
            hit1, hit2, hit3 = (ex_hits[:split] + totdmg)
            hit1m, hit2m, hit3m = (m_hits[:split] + meta)
            hits = 3 - (ex_hits[:split] + totdmg).count(0)
            
        elif (hits_left - len(totdmg)) > 0:
            for hit in totdmg:
                ex_hits[ex_hits.index(0)] = hit
                m_hits[ex_hits.index(0)] = meta.pop(0)
            hit1, hit2, hit3 = ex_hits
            hit1m, hit2m, hit3m = m_hits
            hits = 3 - ex_hits.count(0)
            
        else:
            print('log: invalid update inputs')
            await channel.send('Something went wrong - you have {0:d} hits left '\
                               'and you tried to update {1:d} hits'.format(hits_left, len(hit_v)))
            return
        
        # update the logs
        update_log = ("UPDATE cb.cb_log SET "
                      "hit1 = {0:d}, "
                      "hit2 = {1:d}, "
                      "hit3 = {2:d}, "
                      "hits = {3:d}, "
                      "hit1meta = '{5:s}', "
                      "hit2meta = '{6:s}', "
                      "hit3meta = '{7:s}' "
                      "WHERE entry_id = {4:d}".format(hit1, hit2, hit3, hits, eid, hit1m, hit2m, hit3m))

        try:
            cb_cursor.execute(update_log, )
            cb_db.commit()
        except mysql.connector.Error as err:
            print("logtest:\n:", err)
            cb_cursor.close()
            await channel.send('Oops, something went wrong while writing your log...')
            return

        await channel.send("Successfully updated your **day {0:d}** log, **{1:s}**!"\
                           " You have **{2:d} hits remaining**. Ganbarimasu!".format(day, name, 3-hits))
        print('log: success')
        return
    else:
        await channel.send("**{0:s}**, it is currently **day {1:d}** of CB and you have **{2:d} hits** remaining. "\
                           "Ganbarimasu!".format(name, day, hits_left))
        print('log: success')
        return

# cb battle
@cb.command()
async def battle(ctx, bat:str):
    channel = ctx.channel
    author = ctx.message.author
    error = '<:shioread:449255102721556490>'

    # usual checks
    # check if current cb is set
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not fetch - current CB not set!')
        return

    # check if current cb has concluded
    if not check_cb_concluded():
        print('log: current_cb is not set')
        await channel.send('Could not fetch - current CB has ended!')
        return
    
    # grab cb_id
    cb_id = int(current_cb)

    # check wave-boss request
    req = bat.split('-')
    if len(req) != 2:
        print('battle: invalid inputs')
        await channel.send(error)
        return

    wave, boss = req

    # check wave-boss request
    try:
        wave, boss = bat.split('-')
        if wave == "*":
            search = '-'+boss
            boss = int(boss)
            mode = 'boss'
        elif boss == "*":
            search = wave+'-'
            wave = int(wave)
            mode = 'wave'
        else:
            search = wave+'-'+boss
            boss = int(boss)
            wave = int(wave)
            mode = 'all'
    except:
        print('battle: check failed')
        await channel.send(error)
        return
    
    # fetch records
    fetch = ("SELECT entry_id, nick, hit1meta, hit2meta, hit3meta, day "
             "FROM cb.cb_log l JOIN cb.members m ON l.m_id = m.m_id "
             "WHERE cb_id = {0:d} AND "
             "(hit1meta LIKE '%{1:s}%' "
             "OR hit2meta LIKE '%{1:s}%' "
             "OR hit3meta LIKE '%{1:s}%') "
             "ORDER BY day ASC".format(cb_id, search))

    raw_data = []
    try:
        cursor = cb_db.cursor(buffered=True)
        cursor.execute(fetch, )
        for eid, nick, hit1m, hit2m, hit3m, day in cursor:
            nick = str(nick)
            if len(nick) > 15:
                nick = nick[:15] + '...'
            row = (int(eid), nick, (str(hit1m), str(hit2m), str(hit3m)), int(day))
            raw_data.append(row)
            
    except mysql.connector.Error as err:
            print("battle:\n:", err)
            cursor.close()
            await channel.send('Oops, something went wrong while fetching the data...')
            return

    print('here')
    print(raw_data)
    
    if len(raw_data) == 0:
        print('battle: no data fetched')
        await channel.send(error + ' No data found')
        return

    # sift records
    sift_data = []
    #((wave,boss,day),(eid,nick,dmg))
    for eid, nick, hits_all, day in raw_data:
        for hitm in hits_all: # hit_all -> [("wave-boss:dmg", "wave-boss:dmg", "wave-boss:dmg.wave-boss:dmg"),...]
            for indiv in hitm.split('.'): # indiv -> ["wave-boss:dmg", ...]
                if search in indiv:
                    wbm, dmg = indiv.split(':')
                    wave, boss = wbm.split('-')
                    sift_data.append(
                        ((int(wave), int(boss), day), (eid, nick, int(dmg)))
                         )
                    
    # split by mode
    skip = False
    sort_data = []
    if mode == 'wave':
        key = lambda x: x[0][1]
        max_ = max(sift_data, key=key)[0][1]
        #print(max_)
        
    elif mode == 'boss':
        key = lambda x: x[0][0]
        max_ = max(sift_data, key=key)[0][0]
        #print(max_)
    else:
        sort_data.append(sift_data)
        skip = True

    if not skip:
        for i in range(1,max_+1):
            temp = []
            for hit_data in sift_data:
                if mode == 'wave' and hit_data[0][1] == i:
                    temp.append(hit_data)
                elif mode == 'boss' and hit_data[0][0] == i:
                    temp.append(hit_data)
                
            sort_data.append(temp)

    # sort by dmg
    key = lambda x: x[1][2]
    for i in range(len(sort_data)):
        sort_data[i].sort(reverse=True, key=key)

    # sorted data in the form
    # [
    #   Wave/Boss1
    #   [((wave, boss, day), (eid, nick, dmg)),
    #    ((wave, boss, day), (eid, nick, dmg)),
    #    ((wave, boss, day), (eid, nick, dmg))...
    #   ],
    #   Wave/Boss2
    #   [...],
    #   ...
    # ]
    seperator = '||'+':'*60+'||'
    embed = discord.Embed(title="CB Battle Report",
                          description="Fetched records matching <{:s}>. Prepared by yours truly.".format(search),
                          timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="still in testing")
    if mode == 'all':
        embed.add_field(value=seperator + " **[ Wave {:d} Boss {:d} ]** ".format(sort_data[0][0][0][0], sort_data[0][0][0][1]) + seperator,
                        name=". ", inline=False)
        embed.add_field(name="EID",
                        value='\n'.join(
                            [str(field[1][0])+"-"+field[1][1] for field in sort_data[0]]),
                        inline=True
                        )
        embed.add_field(name="Day",
                        value="\n".join([str(field[0][2]) for field in sort_data[0]]),
                        inline=True
                        )
        embed.add_field(name="Damage",
                        value="\n".join([str(field[1][2]) for field in sort_data[0]]),
                        inline=True
                        )
    elif mode == 'boss':
        for wave in sort_data:
            if wave:
                embed.add_field(value=seperator + " **[ Wave {:d} ]** ".format(wave[0][0][0]) + seperator,
                            name=". ", inline=False)
                embed.add_field(name="EID",
                                value='\n'.join(
                                    [str(field[1][0])+"-"+field[1][1] for field in wave]),
                                inline=True
                                )
                embed.add_field(name="Day",
                                value="\n".join([str(field[0][2]) for field in wave]),
                                inline=True
                                )
                embed.add_field(name="Damage",
                                value="\n".join([str(field[1][2]) for field in wave]),
                                inline=True
                                )
    else:
        for boss in sort_data:
            #print(boss[0][0][1])
            if boss:
                embed.add_field(value=seperator + " **[ Boss {:d} ]** ".format(boss[0][0][1]) + seperator,
                                name=". ", inline=False)
                embed.add_field(name="EID",
                                value='\n'.join(
                                    [str(field[1][0])+"-"+field[1][1] for field in boss]),
                                inline=True
                                )
                embed.add_field(name="Day",
                                value="\n".join([str(field[0][2]) for field in boss]),
                                inline=True
                                )
                embed.add_field(name="Damage",
                                value="\n".join([str(field[1][2]) for field in boss]),
                                inline=True
                                )

    await channel.send(embed=embed)
    return

# cb mrep
@cb.command()
async def mrep(ctx, search="", cb_id=0):
    func = 'mrep: '
    channel = ctx.channel
    author = ctx.message.author

    # usual checks
    # check if current cb is set
    if not check_current_cb():
        print(func+'current_cb is not set')
        await channel.send('Could not fetch - current CB not set!')
        return

    # check if current cb has concluded
    if check_cb_concluded():
        print(func+'cb has concluded')
        await channel.send('Could not fetch - current CB has concluded!')
        return

    # grab cb_id
    if cb_id == 0:
        cb_id = int(current_cb)
    else:
        try:
            cb_id = int(cb_id)
        except:
            print(func+'could not read cb_id input')
            await channel.send(shiori+'check your cb_id input')
            return

    # try casting search
    fetch = "SELECT entry_id, nick, hit1meta, hit2meta, hit3meta, day FROM cb.cb_log l "\
            "JOIN cb.members m ON l.m_id = m.m_id "\
            "WHERE {0:s} AND cb_id = {1:d} ORDER BY day ASC"
    if search == "":
        search = str(author.id)
        fetch = fetch.format("discord_tag = '{:s}'".format(search), cb_id)
    else:
        # m_id?
        try:
            search = int(search)
            fetch = fetch.format('l.m_id = {:s}'.format(str(search)), cb_id)
        except:
            # resort to nick
            print(func+'could not read search_input as m_id')
            search = str(search)
            fetch = fetch.format("nick LIKE '%{:s}%'".format(search), cb_id)
    
    # fetch
    raw_data = []
    try:
        cursor = cb_db.cursor(buffered=True)
        cursor.execute(fetch, )
        for eid, nick, hit1m, hit2m, hit3m, day in cursor:
            if str(hit1m) == 'None' or str(hit2m) == 'None' or str(hit3m) == 'None':
                continue
            nick = str(nick)
            name = nick
            if len(nick) > 15:
                nick = nick[:15] + '...'
            row = (int(eid), nick, (str(hit1m), str(hit2m), str(hit3m)), int(day))
            raw_data.append(row)
    except mysql.connector.Error as err:
            print(func+err)
            cursor.close()
            await channel.send('Oops, something went wrong while fetching the data...')
            return

    if len(raw_data) == 0:
        print(func+'no data fetched')
        await channel.send(shiori + ' No data fetched')
        return

    #print(raw_data)
    # sift records
    sift_data = []
    #((wave,boss,day),(eid,nick,dmg))
    for eid, nick, hits_all, day in raw_data:
        for hitm in hits_all: # hit_all -> [("wave-boss:dmg", "wave-boss:dmg", "wave-boss:dmg.wave-boss:dmg"),...]
            for indiv in hitm.split('.'): # indiv -> ["wave-boss:dmg", ...]
                #if search in indiv:
                wbm, dmg = indiv.split(':')
                wave, boss = wbm.split('-')
                sift_data.append(
                    ((int(wave), int(boss), day), (eid, nick, int(dmg)))
                     )

    print(sift_data)
    # for data
    sort_data = []
    key = lambda x: x[0][1]
    max_ = max(sift_data, key=key)[0][1]
    
    for i in range(1,max_+1):
            temp = []
            for hit_data in sift_data:
                if hit_data[0][1] == i:
                    temp.append(hit_data)
                
            sort_data.append(temp)

    # sort by wave
    key = lambda x: x[0][0]
    for i in range(len(sort_data)):
        sort_data[i].sort(key=key)
    

    seperator = '||'+':'*60+'||'
    embed = discord.Embed(title="Member CB Report",
                          description="Fetched CB records matching for {:s} for `cb_id = {:d}`. Prepared by yours truly.".format(name, cb_id),
                          timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="still in testing")
    for boss in sort_data:
        if boss:
            embed.add_field(value=seperator + " **[ Boss {:d} ]** ".format(boss[0][0][1]) + seperator,
                                name=". ", inline=False)
            embed.add_field(name="EID",
                            value='\n'.join(
                                [str(field[1][0]) for field in boss]),
                            inline=True
                            )
            embed.add_field(name="Day < > Wave",
                            value="\n".join([str(field[0][2])+' < > '+str(field[0][0]) for field in boss]),
                            inline=True
                            )
            embed.add_field(name="Damage",
                            value="\n".join([str(field[1][2]) for field in boss]),
                            inline=True
                            )

    await channel.send(embed=embed)
    return
        
# RUN
client.run(token)
