import datetime

from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests

import discord
from discord.ext.commands import Bot
from discord.ext import commands

async def dumbass(ctx, member):
    channel = ctx.channel
    if len(member) == 0:
        url = ctx.message.author.avatar_url
    else:
        url = member[0].avatar_url
        
    func = 'dumbass: '
    
    async with ctx.typing():
        bg = Image.open('dumb/dumb.jpg')
        #avatar = Image.open('test.png')

        avatar = requests.get(url)
        avatar = Image.open(BytesIO(avatar.content))

        
        if avatar.is_animated:
            avatar.seek(avatar.n_frames//2)
            avatar = avatar.convert(mode="RGB")

        # mask
        size = (200,200)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + size, fill=255)

        # resize
        avatar.resize(size, resample=Image.ANTIALIAS)

        # fit mask
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)

        # paste and save
        bg.paste(avatar, (165,365), avatar)
        bg.save('dumb/dumbass.jpg')
        bg.close()
        avatar.close()

    # send
    await channel.send(file=discord.File('dumb/dumbass.jpg'))
    print(func+'Success')
