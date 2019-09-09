"""
Ames
muimi
"""
import requests
import BytesIO
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
import discord

async def muimi(ctx, msg, emj):
    channel = ctx.channel
    func = 'muimi:'

    # delete the message prompt
    await ctx.message.delete()
    
    # check msg for link
    if len(msg) != 0:
        link = msg[0]

    # check msg for attachment
    if ctx.message.attachments != []:
        link = ctx.message.attachments[0].url
        
    if muimi_embed(ctx, link) is not None:
        await channel.send(embed=muimi_embed(ctx, link))
    else:
        await channel.send(emg['maki'])
    return

def muimi_embed(ctx, url):
    response = requests.get(url)
    func = 'muimi_embed:'
    
    # attempt to open image
    try:
        bg = Image.open(BytesIO(response.content))
    except Exception as err:
        print(func, err)
        return None

    if bg.is_animated:
        print(func, 'bg is animated - no support yet')
        return None

    # image augmentation
    muimi_fg = Image.open('muimi/muimi.png')
    fg_size = muimi.size
    fg_ratio = fg_size[0]/fg_size[1]    
    bg_size = bg.size

    # check aspect ratio
    print(fg_ratio)
    if fg_ratio < 0.2:
        print(func, 'AR beyond tolerance')
        return None
    
    # resize muimi
    h_scale_factor = 0.8
    bg_h_scale = bg_size[1]*h_scale_factor
    
    
