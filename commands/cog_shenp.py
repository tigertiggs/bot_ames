import discord
from discord.ext import commands
import datetime
import os
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
dir = os.path.dirname(__file__)

class shenpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[shenp]'
        self.logger = client.log
    
    async def active_check(self, channel):
        if self.client.get_config('test') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    @commands.command(
        name=".spray [user|optional]",
        aliases=['s'],
        help="For bullying"
    )
    async def spray(self, ctx, user:discord.User=None):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        
        async with ctx.typing():
            if user != None:
                try:
                    user = requests.get(user.avatar_url)
                    user = Image.open(BytesIO(user.content))
                except:
                    await channel.send(self.client.emj['shiori'])
                    return
                else:
                    if user.is_animated:
                        user.seek(user.n_frames//2)
                        user = user.convert(mode="RGB")
                    with Image.open(os.path.join(dir,'shen/assets/spray.png')) as sp:
                        size = (150,150)
                        user.resize(size,resample=Image.ANTIALIAS)
                        mask = Image.new('L', size, 0)
                        draw = ImageDraw.Draw(mask) 
                        draw.ellipse((0, 0) + size, fill=255)
                        user = ImageOps.fit(user, mask.size, centering=(0.5, 0.5))
                        user.putalpha(mask)
                        user = user.rotate(-25, expand=1)

                        sp.paste(user, (50,60), user)
                        sp.save(os.path.join(dir,'shen/post/spray.png'))

                    user.close()
                    send = discord.File(os.path.join(dir,'shen/post/spray.png'))
            else:
                send = discord.File(os.path.join(dir,'shen/assets/spray.png'))

        await channel.send(file=send)

def setup(client):
    client.add_cog(shenpCog(client))