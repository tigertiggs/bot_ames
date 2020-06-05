# this module takes care of all shitpost commands that does require the PIL module
import discord
from discord.ext import commands
import datetime, random
import os
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
from difflib import SequenceMatcher as sm
import requests

class shenpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = "[shenp]"
        self.logger = client.log
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_shenp'])

    async def ames_check(self, target, channel):
        if target == self.client.user:
            await channel.send(self.client.emotes['amesyan'])
            return True
        else:
            return False
    
    async def make_shenp(self, channel, users:tuple, paths:tuple, save_name:str, ames=False):
        # load bg
        open_files = []
        bg = Image.open(os.path.join(self.client.dir, self.client.config['shen_path'], paths[0]))

        # users -> tuple of dict
            # user['user'] -> discord.User
            # user['size'] -> (w,h)
            # user['paste'] -> tuple of tuples
            # user['rotate'] -> float

        # pharse and paste profile pics
        for user_dict in users:
            try:
                if ames:
                    if await self.ames_check(user_dict['user'], channel):
                        bg.close()
                        return False
                temp = requests.get(user_dict['user'].avatar_url)
                temp = Image.open(BytesIO(temp.content))
            except Exception as e:
                await channel.send(self.client.emotes['shiori'])
                await self.logger.send(self.name, save_name, e)
                return False, e
            else:
                if temp.is_animated:
                    temp.seek(temp.n_frames//2)
                    temp = temp.convert(mode="RGB")
            
            temp.resize(user_dict['size'],resample=Image.ANTIALIAS)
            mask = Image.new('L', user_dict['size'],0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0,0)+user_dict['size'],fill=255)
            temp = ImageOps.fit(temp,mask.size,centering=(0.5,0.5))
            temp.putalpha(mask)
            if user_dict.get('rotate', None) != None:
                temp = temp.rotate(user_dict['rotate'], expand=1)
            
            for coord in user_dict['paste']:
                bg.paste(temp, coord, temp)
            open_files.append(temp)
        
        for other_parts in paths[1:]:
            temp = Image.open(os.path.join(self.client.dir, self.client.config['shen_path'], other_parts))
            bg.paste(temp, (0,0), temp)
            open_files.append(temp)
        
        bg.save(os.path.join(self.client.dir, self.client.config['post_path'], save_name))
        [i.close() for i in open_files]

        return discord.File(os.path.join(self.client.dir, self.client.config['post_path'], save_name)), save_name

    async def process_user(self, ctx, user, always_return:bool=True, ames=False):
        channel = ctx.channel
        if user != None:
            target = await self.client.find_user(ctx.message.guild, user)
            if target == None:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return False
            #check = await self.ames_check(target, channel)
            if ames:
                if await self.ames_check(user, channel):
                    return False
            user = target
        elif user == None and always_return:
            user = ctx.message.author
        elif user == None and not always_return:
            user = None
        else:
            await channel.send(self.client.emj['ames'])
            return False
        return user

    @commands.command(aliases=['s'])
    async def spray(self, ctx, user:str=None):
        channel = ctx.channel
        if not self.client.command_status['spray'] == 1:
            raise commands.DisabledCommand

        async with ctx.typing():
            user = await self.process_user(ctx, user, False)
            if user == False: 
                return
            elif user == None:
                await channel.send(file=discord.File(os.path.join(self.client.dir,self.client.config['shen_path'],"other/spray.png")))
                return
            user = {
                "user":user,
                "size":(150,150),
                "paste":[(50,60)],
                "rotate":-25
            }
            shenpf = await self.make_shenp(channel, [user], ["other/spray.png"], "post_spray.png", True)
            print(shenpf)
            if shenpf == False:
                return

        await channel.send(file=shenpf[0])

    @commands.command()
    async def dumb(self, ctx, user:str=None):
        channel = ctx.channel
        #guild = ctx.message.guild
        author = ctx.message.author
        if not self.client.command_status['dumb'] == 1:
            raise commands.DisabledCommand
        
        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                    "user":user,
                    "size":(200,200),
                    "paste":[(165,365)]
                }
            shenpf = await self.make_shenp(channel, [user], ["other/dumb.jpg"], "post_dumb.jpg", True)
            if shenpf == False:
                return
        await channel.send(file=shenpf[0])
        
    @commands.command(aliases=['enty1', 'enty2', 'enty3'])
    async def enty(self, ctx, user:str=None):
        channel = ctx.channel
        #guild = ctx.message.guild
        if not self.client.command_status['enty'] == 1:
            raise commands.DisabledCommand

        cmd = ctx.invoked_with
        if cmd == 'enty':
            mode = random.choice([0,1,2])
        else:
            mode = ['enty1', 'enty2', 'enty3'].index(cmd)

        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                "user":user,
            }
            if mode == 0:
                user['size'] = (400,400)
                user['paste'] = [(110,240)]
                shenpf = await self.make_shenp(channel, [user], ["enty/entychase.jpg"], "post_entychase.jpg", True)
            elif mode == 1:
                user['size'] = (270,270)
                user['paste'] = [(90,125)]
                shenpf = await self.make_shenp(channel, [user], ["enty/entyraid.jpg"], "post_entyraid.jpg", True)
            else:
                user['size'] = (150,150)
                user['paste'] = [(140,10),(115,270),(120,520)]
                shenpf = await self.make_shenp(channel, [user], ["enty/entydejavu1.jpg","enty/entydejavu2.png"], "post_entydejavu.jpg", True)
        
        if shenpf == False:
            return  
        await channel.send(file=shenpf[0])           

    @commands.command(aliases=['nozobless'])
    async def bless(self, ctx, user:str=None):
        channel = ctx.channel
        #guild=ctx.channel.guild
        if not self.client.command_status['bless'] == 1:
            raise commands.DisabledCommand

        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                "user":user,
                "size":(166,166),
                "paste":[(71,191)]
            }
            shenpf, name = await self.make_shenp(channel, [user], ["nozomibless/NozoBless1.png","nozomibless/NozoBless2.png"], "post_bless.png")
        await channel.send(file=shenpf)

    @commands.command()
    async def amesbless(self, ctx, user:str=None):
        channel = ctx.channel
        #guild = ctx.message.guild
        if not self.client.command_status['amesbless'] == 1:
            raise commands.DisabedCommand
        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                "user":user,
                "size":(285,285),
                "paste":[(168,374)]
            }
            shenpf, name = await self.make_shenp(channel, [user], ["amesbless/amesbless_2.png","amesbless/amesbless_fg.png"],"post_amesbless.png")
        await channel.send(file=shenpf)
    
    @commands.command()
    async def kiran(self, ctx, user:str=None):
        channel=ctx.channel
        if not self.client.command_status['kiran'] == 1:
            raise commands.DisabledCommand
        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                "user":user,
                "size":(250,250),
                "paste":[(206,70)]
            }
            shenpf, name = await self.make_shenp(channel, [user], ["kira/uzuki.png","kira/uzuki_2.png"], "post_kiran.png")
        await channel.send(file=shenpf)
    
    @commands.command()
    async def kira(self, ctx, user:str=None):
        channel = ctx.channel
        if not self.client.command_status['kira'] == 1:
            raise commands.DisabledCommand
        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                "user":user,
                "size":(500,500),
                "paste":[(870,43)]
            }
            shenpf, name = await self.make_shenp(channel, [user], ["kira/hatsuneblind.png"], "post_kira.png")
        await channel.send(file=shenpf)
    
    @commands.command(aliases=['chen'])
    async def chenhug(self, ctx, user:str=None):
        channel = ctx.channel
        if not self.client.command_status['chenhug'] == 1:
            raise commands.DisabledCommand
        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if user == False:
                return
            user = {
                "user":user,
                "size":(300,300),
                "paste":[(478,310)]
            }
            shenpf, name = await self.make_shenp(channel, [user], ["chenhug/chen1.png","chenhug/chen2.png"],"post_chenhug.png")
        await channel.send(file=shenpf)

    @commands.command(aliases=['pol','loli','lolipol'])
    async def police(self, ctx, user:str=None):
        channel = ctx.channel
        if not self.client.command_status['police'] == 1:
            raise commands.DisabledCommand
        pass
    
    @commands.command(aliases=['loc'])
    async def location(self, ctx, user:str=None):
        channel = ctx.channel
        if not self.client.command_status['loc'] == 1:
            raise commands.DisabledCommand
        pass
    
    @commands.command()
    async def nero(self, ctx, *, txt:str):
        channel = ctx.channel
        if not self.client.command_status['nero'] == 1:
            raise commands.DisabledCommand
        pass

    @commands.command()
    async def neroe(self, ctx, emoji:str):
        channel = ctx.channel
        if not self.client.command_status['neroe'] == 1:
            raise commands.DisabledCommand
        pass
    
    @commands.command()
    async def mind(self, ctx, *, txt:str):
        channel = ctx.channel
        if not self.client.command_status['mind'] == 1:
            raise commands.DisabledCommand
        pass
    
    @commands.command()
    async def muimi(self, ctx, url:str=None):
        channel = ctx.channel
        if not self.client.command_status['muimi'] == 1:
            raise commands.DisabledCommand
        pass
    
def setup(client):
    client.add_cog(shenpCog(client))