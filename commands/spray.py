"""
Ames
spray
"""
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
import discord

async def spray(ctx, member, emj):
    func = 'spray: '
    channel = ctx.channel
    #member = Image.open('test.png')
    #print(member)
    sp = Image.open('spray/spray4.png')

    async with ctx.typing():
        if member:
            try:
                member = member[0]
                member = requests.get(member.avatar_url)
                member = Image.open(BytesIO(member.content))
                
            except Exception as e:
                print(func, e)
                await channel.send(emj['shiori'])
                return
                
            else:
                if member.is_animated:
                    member.seek(member.n_frames//2)
                    member = member.convert(mode="RGB")
                    
                size = (150,150)
                member.resize(size,resample=Image.ANTIALIAS)
                mask = Image.new('L', size, 0)
                draw = ImageDraw.Draw(mask) 
                draw.ellipse((0, 0) + size, fill=255)
                member = ImageOps.fit(member, mask.size, centering=(0.5, 0.5))
                member.putalpha(mask)
                member = member.rotate(-25, expand=1)

                sp.paste(member, (50,60), member)
                sp.save('spray/sp.png')

                member.close()
                send = discord.File('spray/sp.png')
                
        else:
            print(func + 'no member input detected. Defaulting.')
            send = discord.File('spray/spray4.png')

    await channel.send(file=send)
    sp.close()
    print(func + 'success')
    return













    
