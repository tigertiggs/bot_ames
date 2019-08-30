"""
Ames
change my mind shen
"""
import datetime

from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests

import discord
from discord.ext.commands import Bot
from discord.ext import commands

from misc import randcolour as rc
# change
async def changemymind(ctx, text:str, emj):
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
        await channel.send(emj['shiori'])
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

# threat
async def kalina(ctx, user:discord.Member):
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

# NEROE
async def nero_emoji(ctx, emoji:str):
    channel = ctx.channel
    author = ctx.message.author
    png = 'https://cdn.discordapp.com/emojis/{:s}.png'
    gif = 'https://cdn.discordapp.com/emojis/{:s}.gif'
    raw_emoji = emoji[1:-1].strip().split(':')
    
    if raw_emoji[0] == 'a':
        #print('neroe: no support for animated emojis yet')
        #await channel.send('<:shioread:449255102721556490>')
        #return
        animated = True
        emoji_url = gif.format(raw_emoji[-1])
    elif raw_emoji[0] == "":
        animated = False
        emoji_url = png.format(raw_emoji[-1])
    else:
        print('neroe: invalue input')
        await channel.send('<:shioread:449255102721556490>')
        return

    response = requests.get(emoji_url)

    ###########################################################
    for role in author.roles:
        if str(role.id) == '599996150040494139':
            special = True
            break
        special = False
    if special:
        nero = Image.open('nerosays/rnero.jpg')
    else:
        nero = Image.open('nerosays/nero.jpg')
    #nero = nero.convert(mode="RGBA")
    ############################################################
   
    # params
    size = 150
    image = Image.open(BytesIO(response.content))
    #image = Image.open('test.gif')
    if animated:
        print('frames: ', image.n_frames)
        if image.n_frames > 50: #~1mb
            print('neroe: frames exceeds maximum allowable!')
            await channel.send('Too many frames!')
            return
        dim = nero.size
        
        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
        frames = [frame.convert(mode="RGBA") for frame in frames]
        frames = [frame.resize((size,size),resample=Image.ANTIALIAS) for frame in frames]
        frames = [frame.rotate(10, expand=1) for frame in frames]
        
        first = frames.pop(0)
        nero.paste(first, (100,20), first)
        final = [nero]
        #final = []

        bga = Image.new('RGBA', dim, (255,0,0,0))
        
        for frame in frames:
            #bgac = nero.copy()
            bgac = bga.copy()
            bgac.paste(frame, (100,20), frame)
            final.append(bgac)

        final[0].save('nerosays/nerosayse.gif',
                      format='GIF',
                      append_images=final[1:],
                      save_all=True,
                      duration=image.info['duration'],
                      loop=0,
                      transparency=0)

        result = discord.File("nerosays/nerosayse.gif", filename="nerosayse.gif")
        
    else:
        image = image.convert(mode="RGBA")
        image = image.resize((size,size),resample=Image.ANTIALIAS)
        image = image.rotate(10, expand=1)
        nero.paste(image, (100,20), image)
        nero.save('nerosays/nerosayse.jpg')
        
        result = discord.File("nerosays/nerosayse.jpg", filename="nerosayse.jpg")

    nero.close()

    # send image
    async with ctx.typing():
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), colour=rc())
        embed.set_author(name="{:s} wanted you to know that:".format(author.name), icon_url=author.avatar_url)
        embed.set_footer(text="still in testing")
        if animated:
            embed.set_image(url="attachment://nerosayse.gif")
        else:
            embed.set_image(url="attachment://nerosayse.jpg")
    await channel.send(file=result, embed=embed)
    print('neroe: success')
    return

# NERO
async def nero_says(ctx, text, emj):
    channel = ctx.channel
    author = ctx.message.author
    text = ctx.message.content[5:]
    length = len(text)
    
    if text == "" or length > 170:
        print('nero: input text length exceeds maximum allowable')
        await channel.send(emj['shiori'])
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

    ###########################################################
    for role in author.roles:
        if str(role.id) == '599996150040494139':
            special = True
            break
        special = False
    if special:
        nero = Image.open('nerosays/rnero.jpg')
    else:
        nero = Image.open('nerosays/nero.jpg')
    ############################################################
  
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
        #embed = discord.Embed(colour=rc())
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(),colour=rc())
        embed.set_author(name="{:s} wanted you to know that:".format(author.name), icon_url=author.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://nerosays.png")
    await channel.send(file=result, embed=embed)
    print('nero: success')
    return

# location
async def knowyour(ctx, user: discord.Member):
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

# POLICE
async def jail(ctx, user: discord.Member):
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
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(),colour=rc())
        embed.set_author(name="{:s} is going to jail:".format(user.name), icon_url=user.avatar_url)
        embed.set_footer(text="still in testing")
        embed.set_image(url="attachment://pol.gif")
        
    await channel.send(file=result, embed=embed)
    #await channel.send(file=discord.File('police/pol.gif'))
    print('police: success')
    return

async def enlarge(ctx, emoji, emj):
    channel = ctx.channel
    author = ctx.message.author
    await ctx.message.delete()
    png = 'https://cdn.discordapp.com/emojis/{:s}.png'
    gif = 'https://cdn.discordapp.com/emojis/{:s}.gif'
    raw_emoji = emoji[1:-1].strip().split(':')
    #print(raw_emoji)
    if raw_emoji[0] == 'a':
        emoji_url = gif.format(raw_emoji[-1])
    elif raw_emoji[0] == "":
        emoji_url = png.format(raw_emoji[-1])
    else:
        await channel.send(emj['shiori'])
        return
    embed = discord.Embed(colour=rc())
    embed.set_author(name="{:s} sent:".format(author.name), icon_url=author.avatar_url)
    embed.set_image(url=emoji_url)
    await channel.send(embed=embed)
    return
















    
