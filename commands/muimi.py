"""
Ames
muimi
"""
import requests
from io import BytesIO
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
import discord

async def muimi(ctx, msg, emj):
    channel = ctx.channel
    func = 'muimi:'

    # attachment takes priority
    # check msg for link
    if len(msg) != 0:
        print('link found', msg[0])
        link = msg[0]

    # check msg for attachment
    if ctx.message.attachments != []:
        print('att found', ctx.message.attachments[0].filename)
        link = ctx.message.attachments[0].url
    
    if muimi_embed(ctx, link) is not None:
        await channel.send(file=muimi_embed(ctx, link))
    else:
        await channel.send(emj['maki'])
    
    # delete the message prompt
    await ctx.message.delete()
    return

def muimi_embed(ctx, url):
    OUT = 'muimi/muimi.png'
    response = requests.get(url)
    func = 'muimi_embed:'
    
    # attempt to open image
    try:
        bg = Image.open(BytesIO(response.content))
    except Exception as err:
        print(func, err)
        return None

    try:
        if bg.is_animated:
            print(func, 'bg is animated - no support yet')
            return None
    except Exception as err:
        # may not support .is_animated
        print(func, err)
        pass

    # image augmentation
    muimi_fg = Image.open('muimi/muimi_this_c.png')
    fg_size = muimi_fg.size
    fg_ratio = fg_size[0]/fg_size[1]

    # size -> (width, height)
     
    bg_size = bg.size
    bg_ratio = bg_size[0]/bg_size[1]   

    """
    okay, so there are a lot of conditions to check right now.
    """

    # check size
    LIMIT = 125
    if bg_size[0] < LIMIT or bg_size[1] < LIMIT:
        print(func, 'limit reached')
        return None
    
    # check aspect ratio
    print(bg_size, bg_ratio)
    if bg_ratio < 0.2 or bg_ratio > 3:
        print(func, 'AR beyond tolerance')
        return None

    print('fg bg', fg_size, bg_size)
    # if bg is smaller than muimi than just resize muimi
    #if (bg_size[0] < fg_size[0] and bg_size[1] < fg_size[1]) or (bg_size[0] > fg_size[0] and bg_size[1] > fg_size[1]):
    # rescale to 150% of input bg
    scale = 1.5
    max_axis = max(bg_size)
    axis = bg_size.index(max_axis)

    target = int(1.5*max_axis)
    if axis == 0:
        target_size = (target, int(target/fg_ratio))
    else:
        target_size = (int(target*fg_ratio), target)

    muimi_fg = muimi_fg.resize(target_size, resample=Image.ANTIALIAS)

    #pos_x = ((target_size[0] - bg_size[0]) // 2)
    pos_x = 0
    pos_y = ((target_size[1] - bg_size[1]) // 2)

    fg = muimi_fg.copy()
    
    try:
        muimi_fg.paste(bg, (pos_x, pos_y), bg)
    except Exception as err:
        print(func, err)
        muimi_fg.paste(bg, (pos_x, pos_y))
        
    muimi_fg.paste(fg, (0,0), fg)
    muimi_fg.save(OUT)
    return discord.File(OUT, filename=OUT)
    

        
        
        
        
"""
# resize muimi
h_scale_factor = 0.9
bg_h_scale = bg_size[1]*h_scale_factor

return None
"""
    
