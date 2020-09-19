# this module takes care of all shitpost commands that does require the PIL module
import discord
from discord.ext import commands
import datetime, random
import os
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
from difflib import SequenceMatcher as sm
import requests, traceback

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
                try:
                    if temp.is_animated:
                        #temp.seek(temp.n_frames//2)
                        temp.seek(0)
                        temp = temp.convert(mode="RGB")
                except Exception as e:
                    await self.logger.send(self.name, "could not get attr", e)
            
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
        
        # check for attachment
        link = ctx.message.attachments[0].url if ctx.message.attachments else None
        
        # default to attachment
        url = link if link else url

        # return if void
        if not url:
            channel.send(self.client.emotes['maki'])
            return

        async with ctx.typing():
            out = await self.muimi_embed(ctx, url)
            if out:
                await ctx.message.delete()
                await channel.send(file=discord.File(out))

        #async with ctx.typing():
        #    embed = self.muimi_embed(ctx, link)
        #    if embed:
        #        await ctx.message.delete()
        #        await channel.send(embed=embed)
        #    else:
        #        await channel.send(self.client.emotes['maki'])
        
    async def muimi_embed(self, ctx, url:str):
        # attempt to load the image
        try:
            bg = Image.open(BytesIO(requests.get(url).content))
        except:
            await self.logger.send(traceback.format_exc())
            return None
        else:
            # get bg data
            bg_size = bg.size # (w,h)
            bg_ratio = bg_size[0]/bg_size[1]
        
        # no support for animated bgs yet
        if hasattr(bg, "is_animated"):
            if bg.is_animated:
                await ctx.message.delete()
                await ctx.channel.send("No support for animated files (yet)")
                return
        
        # load fg
        muimi_fg = Image.open(os.path.join(self.client.dir, self.client.config['shen_path'], "other/muimi_this_c.png"))
        fg_size = muimi_fg.size # (w,h)
        fg_ratio = fg_size[0]/fg_size[1]

        # target size
        target_multi = 1.25
        target_dim = tuple(round(i*target_multi) for i in fg_size)

        # scaling
        #width_multi = bg_size[1]/target_dim[1]
        #final_width = round(width_multi*bg_size[0])
        final_width = round(target_dim[1]*bg_ratio)
        bg = bg.resize((final_width, target_dim[1]), resample=Image.ANTIALIAS)

        # since we're forcing the scaling to only 1 dimension, 
        # we only need to check the width of the final image

        if final_width >= fg_size[0]:
            delta = round((final_width - fg_size[0])/2*(1/3))
            paste_pos = (final_width-delta-fg_size[0], target_dim[1]-fg_size[1])
            bg.paste(muimi_fg, paste_pos, muimi_fg)
        else:
            # need to create new canvas because the scaled bg width does not match muimi width
            base = Image.new("RGBA", target_dim, (255,0,0,0))
            delta = round((target_dim[0] - fg_size[0])/2*(1/3))
            paste_pos = (target_dim[0]-delta-fg_size[0], target_dim[1]-fg_size[1])
            # see if bg is transparent
            if bg.mode in ('RGBA', 'LA') or (bg.mode == 'P' and 'transparency' in bg.info):
                base.paste(bg, (round((target_dim[0]-final_width)/2), 0), bg)
            else:
                base.paste(bg, (round((target_dim[0]-final_width)/2), 0))

            base.paste(muimi_fg, paste_pos, muimi_fg)

            bg.close()
            bg = base
        
        path = os.path.join(self.client.dir, self.client.config['post_path'], "muimi.png")
        bg.save(path)
        bg.close()
        muimi_fg.close()
        return path
    
    @commands.command()
    async def cheer(self, ctx, user:str=None):
        channel = ctx.channel
        if not self.client.command_status['cheer']:
            raise commands.DisabledCommand
        async with ctx.typing():
            user = await self.process_user(ctx, user)
            if not user:
                return
            user = {
                "user": user,
                "size": (330,330),
                "paste": [(773,0)]
            }
            shenpf, name = await self.make_shenp(channel, [user], ["cheer/cheer.png"], "post_cheer.png")
        await channel.send(file=shenpf)
            
    @commands.command(aliases=['w','long','l'])
    async def wide(self, ctx, *request):
        channel = ctx.channel
        if not self.client.command_status['wide']:
            raise commands.DisabledCommand
        elif len(request) > 2:
            await channel.send(self.client.emotes['derp'])
            return

        async with ctx.typing():
            
            multi = 5
            blob = Image.open(os.path.join(self.client.dir, self.client.config['shen_path'], "other/hatsuneblob.png"))

            for thing in request:
                if thing.isdigit():
                    multi = int(thing)
                else:
                    animated = False
                    try:
                        _thing = thing[1:-1].split(':')
                        if _thing[0] == '' and len(_thing) > 1:
                            link = f"https://cdn.discordapp.com/emojis/{_thing[-1]}.png"
                        elif _thing[0] == 'a' and len(_thing) > 1:
                            #await channel.send(self.client.emotes['derp'])
                            #return
                            link = f"https://cdn.discordapp.com/emojis/{_thing[-1]}.gif"
                        blob = Image.open(BytesIO(requests.get(link).content))
                        if hasattr(blob, "is_animated"):
                            animated = blob.is_animated
                        else:
                            animated = False
                    except:
                        await channel.send(self.client.emotes['derp'])
                        return
            
            if multi < 1 or multi > 10:
                await channel.send(self.client.emotes['derp'])
                return

            #blob = Image.open(os.path.join(self.client.dir, self.client.config['shen_path'], "other/hatsuneblob.png"))
            w, h = blob.size
            if ctx.invoked_with.startswith('w'):
                target = (w*multi, h)
            else:
                target = (w, multi*h)

            if not animated:
                path = os.path.join(self.client.dir, self.client.config['post_path'], "blob.png")
                blob = blob.resize(target, resample=Image.ANTIALIAS)
                blob.save(path)
                blob.close()
            else:
                blob.seek(0)
                duration = blob.info['duration']
                path = os.path.join(self.client.dir, self.client.config['post_path'], "blob.gif")
                _blob = [frame.resize(target, resample=Image.ANTIALIAS) for frame in ImageSequence.Iterator(blob)]
                _blob[0].save(
                    path,
                    format='GIF',
                    append_images=_blob[1:],
                    save_all=True,
                    duration=duration,
                    loop=0,
                    optimize=False,
                    disposal=2
                )
                [frame.close() for frame in _blob]
            blob.close()
            await channel.send(file=discord.File(path))

def setup(client):
    client.add_cog(shenpCog(client))