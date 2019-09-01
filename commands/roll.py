"""
Ames
Gacha
"""
import time
import datetime

from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
import random

import discord
from discord.ext.commands import Bot
from discord.ext import commands

from misc import randcolour as rc
from prototype import get_team as gt

async def roll(ctx, emj, t=10, mode=''):
    channel = ctx.channel
    author = ctx.message.author
    if t > 10:
        print('gacha: roll > 10')
        await channel.send(emj['sarens']+'You\'re being a bit too ambitious')
        return
    elif t < 1:
        print('gacha: invalid roll input')
        await channel.send('<:shioread:449255102721556490>')
        return
    raw_result = gacha_result(t, mode)
    async with ctx.typing():
        create_gacha_result(raw_result)
        result = discord.File("gacha/gresult.jpg", filename="gresult.jpg")
        st = time.time()
        embed = discord.Embed(colour=rc())
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_author(name="{:s} rolled:".format(author.name), icon_url=author.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://gresult.jpg")
    await channel.send(file=result, embed=embed)       
    #await channel.send(file=result)
    print('gacha: success - send time (w embed): {:f}s'.format(time.time() - st))
    
    return

def create_gacha_result(result):
    #print('cgr: start init')
    # open images
    st = time.time()
    gacha = Image.open('gacha/gbg2.jpg')
    rare = Image.open('gacha/r2_.png')
    srare = Image.open('gacha/sr2_.png')
    ssrare = Image.open('gacha/ssr2_.png')
    new = Image.open('gacha/new_.png')
    none = Image.open('gacha/units/_NONE.webp')
    
    # sizes
    row1 = 80
    row2 = 330
    spacing = 197
    #psize = (197,270)
    #csize = (141,141)
    #nsize = (80,80)
    rs = Image.ANTIALIAS
    gscalef = 0.7
    gsizef =  (round(gacha.size[0]*gscalef),
               round(gacha.size[1]*gscalef))
    pxstart = 190
    cxstart = 215
    cos = 72
    nos = -25

    # resize
    #rare = rare.resize(psize, resample=rs)
    #srare = srare.resize(psize, resample=rs)
    #ssrare = ssrare.resize(psize, resample=rs)
    #new = new.resize(nsize, resample=rs)

    #print('cgr: end init')
    #print('cgr: start reading avatars')
    # get avatars
    final = []
    for chara, rarity in result:
        try:
            avatar = Image.open('gacha/units/{:s}.webp'.format(chara))
        except:
            avatar = none
        #avatar = avatar.resize(csize, resample=rs)
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
    gacha.save('gacha/gresult.jpg')

    # shutdown
    gacha.close()
    rare.close()
    srare.close()
    ssrare.close()
    new.close()
    #none.close()
    print('cgr: success - {:f}s'.format(time.time() - st))
    return

def gacha_result(t=10, mode=''):
    r_pool, sr_pool, ssr_pool = read_pool()
    ssr_rate = 0.05
    sr_rate = 0.18
    r_rate = 1 - ssr_rate - sr_rate

    # LIMITED/SEASONAL ADDITION - PLEASE MANUALLY FILL
    # DOES NOT APPLY TO RATEUPS FOR NORMAL POOL CHARAS!
    ssr_up = ['neneka', 'christina', 'muimi']
    ssr_up_rate_indiv = 0.005
    
    rolls = []
    grain = 100000

    if mode == '':
        for i in range(t):
            roll = random.randint(0,grain)
            if (i+1)%10 != 0:
                if roll < (r_rate * grain):
                    chara = random.choice(r_pool)
                    rolls.append((chara,1))
                elif roll < ((r_rate + sr_rate) * grain):
                    chara = random.choice(sr_pool)
                    rolls.append((chara,2))
                else:
                    chara = random.choice(ssr_pool)
                    rolls.append(tier(3, ssr_pool, ssr_rate, ssr_up, ssr_up_rate_indiv))
            else:
                if roll < ((r_rate + sr_rate) * grain):
                    chara = random.choice(sr_pool)
                    rolls.append((chara,2))
                else:
                    rolls.append(tier(3, ssr_pool, ssr_rate, ssr_up, ssr_up_rate_indiv))
    elif mode == 'test':
        for i in range(t):
            roll = random.randint(0,grain)
            rolls.append(tier(3, ssr_pool, ssr_rate, ssr_up, ssr_up_rate_indiv))
        
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
    return r_pool, sr_pool, ssr_pool

async def spark(ctx, emj, client):
    channel = ctx.channel
    author = ctx.message.author
    func = 'spark:'
    
    rolls = gacha_result(t=300)
    r_tier = 0
    sr_tier = 0
    ssr_tier = []

    spec = []
    for chara, rarity in rolls:
        if abs(rarity) == 1:
            r_tier += 1
        elif abs(rarity) == 2:
            sr_tier += 1
        elif abs(rarity) == 3 and rarity > 0:
            ssr_tier.append(chara)
        elif abs(rarity) == 3 and rarity < 0:
            ssr_tier.append("_"+chara)
            spec.append("_"+chara)
        else:
            #ssr_tier.append(chara)
            pass


    unique_set = list(set(ssr_tier))
    #unique_set = list(unique_set)
    unique_set.sort()
    teams = gt(client)
    
    count = [(chara, ssr_tier.count(chara)) for chara in unique_set]

    await channel.send(embed=spark_embed(author, count, r_tier, sr_tier, len(ssr_tier), teams, spec))
    return

def spark_embed(author, count, r, sr, ssr, teams, spec):
    embed = discord.Embed(
        title="Spark Summary",
        description="Prepare for salt, {:s}".format(author.name),
        timestamp=datetime.datetime.utcnow(),
        colour=rc())
    
    embed.set_footer(text="still in testing")

    r_pc = ' ({:.2f}\%)'.format(r/300*100)
    sr_pc = ' ({:.2f}\%)'.format(sr/300*100)
    ssr_pc = ' ({:.2f}\%)'.format(ssr/300*100)

    tears = r + sr*10 + ssr*50
    
    embed.add_field(
        name="R Tier",
        value=str(r)+r_pc,
        inline=True
        )
    embed.add_field(
        name="SR Tier",
        value=str(sr)+sr_pc,
        inline=True
        )
    embed.add_field(
        name="SSR Tier",
        value=str(ssr)+ssr_pc,
        inline=True)
    embed.add_field(
        name="Total P.Tears",
        value='**{:s}**'.format(str(tears)),
        inline=True
        )

    ssrlist = []
    for chara, order in count:
        if chara in spec:
            chara = chara[1:]
            temp = chara.join(['**', '**'])
            ssrlist.append('> ' +\
                " ".join([teams['template'].format(chara,teams[chara]),
                       temp,
                       'x'+str(order)]))
        else:
            ssrlist.append(
                " ".join([teams['template'].format(chara,teams[chara]),
                          chara,
                          'x'+str(order)]))
    
    embed.add_field(
        name="SSR Rolled",
        value="\n".join(ssrlist),
        inline=False
        )
    return embed
