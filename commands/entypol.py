"""
Ames
Enty
"""

from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
import random

import discord
from discord.ext.commands import Bot
from discord.ext import commands

async def enty(ctx, mode, member, emj):
    channel = ctx.channel
    # preprocessor

    if len(member) == 0:
        url = ctx.message.author.avatar_url
    else:
        url = member[0].avatar_url

    avatar = requests.get(url)
    avatar = Image.open(BytesIO(avatar.content))

        
    if avatar.is_animated:
        avatar.seek(avatar.n_frames//2)
        avatar = avatar.convert(mode="RGB")
    
    if mode == 0:
        mode = random.choice([1,2,3])

    if mode == 1:
        await entychase(ctx, avatar, emj)
    
    elif mode == 2:
        await entyraid(ctx, avatar, emj)
    
    elif mode == 3:
        await entydejavu(ctx, avatar, emj)
    
    else:
        await channel.send(emj['shiori'])
        
    return

async def entychase(ctx, avatar, emj):
    func = 'entychase:'
    channel = ctx.channel
    #avatar = Image.open('test.png')
    bg = Image.open('enty/entychase.jpg')

    async with ctx.typing():
        # mask
        size = (400,400)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)

        # resize
        avatar.resize(size, resample=Image.ANTIALIAS)

        # fit mask
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)

        # paste and save
        bg.paste(avatar, (110,240), avatar)
        bg.save('enty/_entychase.jpg')
        bg.close()
        avatar.close()

    await channel.send(file=discord.File('enty/_entychase.jpg'))
    print(func, 'success')
    return

async def entyraid(ctx, avatar, emj):
    func = 'entyraid:'
    channel = ctx.channel
    #avatar = Image.open('test.png')
    bg = Image.open('enty/entyraid.jpg')
    async with ctx.typing():
        # mask
        size = (270,270)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)

        # resize
        avatar.resize(size, resample=Image.ANTIALIAS)

        # fit mask
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)

        # paste and save
        bg.paste(avatar, (90,125), avatar)
        bg.save('enty/_entyraid.jpg')
        bg.close()
        avatar.close()

    await channel.send(file=discord.File('enty/_entyraid.jpg'))
    print(func, 'success')
    return

async def entydejavu(ctx, avatar, emj):
    func = 'entyraid:'
    channel = ctx.channel
    #avatar = Image.open('test.png')
    bg = Image.open('enty/entydejavu1.jpg')
    bgw = Image.open('enty/entydejavu2.png')
    
    async with ctx.typing():
        # mask
        size = (150,150)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)

        # resize
        avatar.resize(size, resample=Image.ANTIALIAS)

        # fit mask
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)

        # paste and save
        loc1 = (140,10)
        loc2 = (115,270)
        loc3 = (120,520)
        bg.paste(avatar, loc1, avatar)
        bg.paste(avatar, loc2, avatar)
        bg.paste(avatar, loc3, avatar)
        bg.paste(bgw, (0,0), bgw)
        bg.save('enty/_entydejavu.jpg')
        bg.close()
        bgw.close()
        avatar.close()

    await channel.send(file=discord.File('enty/_entydejavu.jpg'))
    print(func, 'success')
    return
