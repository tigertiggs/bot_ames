import discord
from discord.ext import commands
import datetime, random
import os
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
from difflib import SequenceMatcher as sm
import requests
dir = os.path.dirname(__file__)

class shenpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[shenp]'
        self.logger = client.log

    async def ames_check(self, target, channel):
        if target == self.client.user:
            await channel.send(self.client.emj['amesyan'])
            return True
        else:
            return False
    
    async def find_user(self, guild, user:str):
        members = guild.members

        # check if user is a discord id
        try:
            user = user.replace('>', '').replace('<','').replace('@','').replace('!','')
            #print(user)
            user = guild.get_member(int(user))
        except Exception as e:
            await self.logger.send(self.name, 'dumb id mismatch', e)
            pass
        else:
            return user
        
        # do string match
        # search name
        cutoff = 0.3
        user = user.lower()
        fname = list(filter(lambda x: sm(None, user, x.name.lower(), None).ratio() >= cutoff and user in x.name.lower(), members))
        fnick = list(filter(lambda x: sm(None, user, x.nick.lower() if x.nick != None else '', None).ratio() >= cutoff and user in x.nick.lower(), members))
        #print(user, fname, fnick)
        if len(fname) != 0 and len(fnick) != 0:
            #print(fname[0].name, fnick[0].nick)
            a = sm(None, user, fname[0].name, None).ratio()
            b = sm(None, user, fnick[0].nick, None).ratio()
            if a == b:
                return fnick[0]
            elif a > b:
                return fname[0]
            else:
                return fnick[0]
        elif len(fname) != 0:
            #print(fname[0].name)
            return fname[0]
        elif len(fnick) != 0:
            #print(fnick[0].nick)
            return fnick[0]
        else:
            return None

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
                check = await self.ames_check(user, channel)
                if check:
                    return
                try:
                    user = requests.get(user.avatar_url)
                    user = Image.open(BytesIO(user.content))
                except Exception as e:
                    await channel.send(self.client.emj['shiori'])
                    await self.logger.send(self.name, 'failed to fetch image', e)
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

    @commands.command(
        usage=".dumb [user|optional]",
        help="Call someone out for being a dumbass. Defaults to self!"
    )
    async def dumb(self, ctx, user:str=None):
        channel = ctx.channel
        guild = ctx.message.guild
        author = ctx.message.author
        check = await self.active_check(channel)
        if not check:
            return
        
        # get user
        if user != None:
            target = await self.find_user(guild, user)
            if target == None:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
            check = await self.ames_check(target, channel)
            if check:
                return
            url = target.avatar_url
        elif user == None:
            url = author.avatar_url
        else:
            await channel.send(self.client.emj['ames'])
            return
        
        # make things
        async with ctx.typing():
            bg = Image.open(os.path.join(dir,'shen/assets/dumb.jpg'))

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
            bg.save(os.path.join(dir,'shen/post/dumbass.jpg'))
            bg.close()
            avatar.close()

        # send
        await channel.send(file=discord.File(os.path.join(dir,'shen/post/dumbass.jpg')))

    @commands.command(
        usage=".enty [user|optional]",
        aliases=['enty1','enty2','enty3'],
        help="Call someone out for being an Ark Royal. Defaults to self!"
    )
    async def enty(self, ctx, user:str=None):
        channel = ctx.channel
        guild = ctx.message.guild
        check = await self.active_check(channel)
        if not check:
            return
        
        if user != None:
            target = await self.find_user(guild, user)
            if target == None:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
            check = await self.ames_check(target, channel)
            if check:
                return
            url = target.avatar_url
        elif user == None:
            url = ctx.message.author.avatar_url
        else:
            await channel.send(self.client.emj['ames'])
            return
        
        avatar = requests.get(url)
        avatar = Image.open(BytesIO(avatar.content))
        if avatar.is_animated:
            avatar.seek(avatar.n_frames//2)
            avatar = avatar.convert(mode="RGB")

        cmd = ctx.invoked_with
        mode = 0
        if cmd == 'enty':
            mode = random.choice([1,2,3])
        async with ctx.typing():
            if cmd == 'enty1' or mode == 1:
                await channel.send(file=self.entychase(avatar))
            elif cmd == 'enty2' or mode == 2:
                await channel.send(file=self.entyraid(avatar))
            elif cmd == 'enty3' or mode == 3:
                await channel.send(file=self.entydejavu(avatar))
        
    def entychase(self, avatar):
        bg = Image.open(os.path.join(dir,'shen/assets/entychase.jpg'))
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
        bg.save(os.path.join(dir,'shen/post/entychase.jpg'))
        bg.close()
        avatar.close()
        return discord.File(os.path.join(dir,'shen/post/entychase.jpg'))
    
    def entyraid(self, avatar):
        bg = Image.open(os.path.join(dir,'shen/assets/entyraid.jpg'))
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
        bg.save(os.path.join(dir,'shen/post/entyraid.jpg'))
        bg.close()
        avatar.close()
        return discord.File(os.path.join(dir,'shen/post/entyraid.jpg'))

    def entydejavu(self, avatar):
        bg = Image.open(os.path.join(dir,'shen/assets/entydejavu1.jpg'))
        bgw = Image.open(os.path.join(dir,'shen/assets/entydejavu2.png'))
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
        bg.save(os.path.join(dir,'shen/post/entydejavu.jpg'))
        bg.close()
        bgw.close()
        avatar.close()

        return discord.File(os.path.join(dir,'shen/post/entydejavu.jpg'))
            
    @commands.command(
        usage='.location [user|optional]',
        aliases=['loc'],
        help="No description... yet."
    )
    async def location(self, ctx, user:str=None):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        
        if user != None:
            target = await self.find_user(ctx.message.guild, user)
            if target == None:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
            name = target.display_name
        elif user == None:
            name = ctx.message.author.display_name
        else:
            await channel.send(self.client.emj['ames'])
            return
        
        await ctx.message.delete()
        async with ctx.typing():
            font = ImageFont.truetype("arial.ttf", 22)
            loc = Image.open(os.path.join(dir,'shen/assets/location.png'))
            draw = ImageDraw.Draw(loc)
            draw.text((35, 45),name+" wants to",(0,0,0),font=font)
            loc.save(os.path.join(dir,'shen/post/loc.png'))
        await channel.send(file=discord.File(os.path.join(dir,'shen/post/loc.png')))

    @commands.command(
        usage='.police [user|optional]',
        aliases=['pol','loli','lolipol'],
        help='Call someone out for being a lolicon. Defaults to self!'
    )
    async def police(self, ctx, user:str=None):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        
        if user != None:
            target = await self.find_user(ctx.message.guild, user)
            if target == None:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
            check = await self.ames_check(target, channel)
            if check:
                return
            user = target
        elif user == None:
            user = ctx.message.author
        else:
            await channel.send(self.client.emj['ames'])
            return
        
        async with ctx.typing():
            # get images
            url = user.avatar_url
            response = requests.get(url)
            avatar = Image.open(BytesIO(response.content))
            police_base = Image.open(os.path.join(dir,'shen/assets/police.gif'))
            
            # check if avatar is animated
            if avatar.is_animated:
                animated = True
            else:
                animated = False

                
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
                n_frames = len(aframes)
            
            else:
                avatar = avatar.resize(size,Image.ANTIALIAS)
                avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
                avatar.putalpha(mask)
            
            counter = 0
            frames = []
            for frame in ImageSequence.Iterator(police_base):
                frame = frame.copy()
                
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

            frames[0].save(os.path.join(dir,'shen/assets/pol.gif'),
                        format='GIF',
                        append_images=frames[1:],
                        save_all=True,
                        duration=80,
                        loop=0)
            
            result = discord.File(os.path.join(dir,'shen/assets/pol.gif'), filename="pol.gif")
            embed = discord.Embed(timestamp=datetime.datetime.utcnow())
            embed.set_author(name="{:s} is going to jail:".format(user.name), icon_url=user.avatar_url)
            embed.set_footer(text="Police | SHIN Ames", icon_url=self.client.user.avatar_url)
            embed.set_image(url="attachment://pol.gif")
        
        await channel.send(file=result, embed=embed)

    @commands.command(
        usage='.nero [text]',
        help="Have Nero say something."
    )
    async def nero(self, ctx, *, txt:str):
        channel = ctx.channel
        author = ctx.message.author
        check = await self.active_check(channel)
        if not check:
            return
        
        #text = ctx.message.content[5:]
        text = txt
        length = len(text)
        
        if text == "" or length > 170:
            await self.logger.send('nero: input text length exceeds maximum allowable')
            await channel.send(self.client.emj['shiori'])
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
            nero = Image.open(os.path.join(dir,'shen/assets/rnero.jpg'))
        else:
            nero = Image.open(os.path.join(dir,'shen/assets/nero.jpg'))
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
        nero.save(os.path.join(dir,'shen/post/nerosays.png'))
        nero.close()

        async with ctx.typing():
            result = discord.File(os.path.join(dir,'shen/post/nerosays.png'), filename="nerosays.png")
            #embed = discord.Embed(colour=rc())
            embed = discord.Embed(timestamp=datetime.datetime.utcnow())
            embed.set_author(name="{:s} wanted you to know that:".format(author.name), icon_url=author.avatar_url)
            embed.set_footer(text="Nero says | SHIN Ames", icon_url=self.client.user.avatar_url)
            embed.set_image(url="attachment://nerosays.png")
        await channel.send(file=result, embed=embed)

    @commands.command(
        usage='.neroe [emote]',
        help="Have Nero share an emote."
    )
    async def neroe(self, ctx, emoji:str):
        channel = ctx.channel
        author = ctx.message.author
        check = await self.active_check(channel)
        if not check:
            return

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
            await channel.send(self.client.emj['shiori'])
            return

        response = requests.get(emoji_url)

        ###########################################################
        for role in author.roles:
            if str(role.id) == '599996150040494139':
                special = True
                break
            special = False
        if special:
            nero = Image.open(os.path.join(dir,'shen/assets/rnero.jpg'))
        else:
            nero = Image.open(os.path.join(dir,'shen/assets/nero.jpg'))
        #nero = nero.convert(mode="RGBA")
        ############################################################
    
        # params
        size = 150
        image = Image.open(BytesIO(response.content))
        #image = Image.open('test.gif')
        if animated:
            #print('frames: ', image.n_frames)
            if image.n_frames > 50: #~1mb
                #print('neroe: frames exceeds maximum allowable!')
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

            final[0].save(os.path.join(dir,'shen/post/nerosayse.gif'),
                        format='GIF',
                        append_images=final[1:],
                        save_all=True,
                        duration=image.info['duration'],
                        loop=0,
                        transparency=0)

            result = discord.File(os.path.join(dir,'shen/post/nerosayse.gif'), filename="nerosayse.gif")
            
        else:
            image = image.convert(mode="RGBA")
            image = image.resize((size,size),resample=Image.ANTIALIAS)
            image = image.rotate(10, expand=1)
            nero.paste(image, (100,20), image)
            nero.save(os.path.join(dir,'shen/post/nerosayse.jpg'))
            
            result = discord.File(os.path.join(dir,'shen/post/nerosayse.jpg'), filename="nerosayse.jpg")

        nero.close()

        # send image
        async with ctx.typing():
            embed = discord.Embed(timestamp=datetime.datetime.utcnow())
            embed.set_author(name="{:s} wanted you to know that:".format(author.name), icon_url=author.avatar_url)
            embed.set_footer(text="Nero says emote | SHIN Ames", icon_url=self.client.user.avatar_url)
            if animated:
                embed.set_image(url="attachment://nerosayse.gif")
            else:
                embed.set_image(url="attachment://nerosayse.jpg")
        await channel.send(file=result, embed=embed)

    @commands.command(
        usage='.threat [user]',
        help='Coax someone with a P5 Compact.'
    )
    async def threat(self, ctx, user:str=None):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return 

        threater = ctx.message.author
        async with ctx.typing():
            if user == None:
                threatened = threater
            else:
                threatened = await self.find_user(ctx.message.guild, user)
                if threatened == None:
                    await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                    return
                check = await self.ames_check(threatened, channel)
                if check:
                    return

            t1 = requests.get(threater.avatar_url)
            t2 = requests.get(threatened.avatar_url)

            threat = Image.open(os.path.join(dir,'shen/assets/threaten.png'))
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

            threat.save(os.path.join(dir,'shen/post/threat.png'))

        await channel.send(file=discord.File(os.path.join(dir,'shen/post/threat.png')))

    @commands.command(
        usage='.mind [text]',
        help='No description... yet.'
    )
    async def mind(self, ctx, *, text):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return
        
        author = ctx.message.author.avatar_url
        length = len(text)
        change = Image.open(os.path.join(dir,'shen/assets/change.jpg'))

        response = requests.get(author)
        author = Image.open(BytesIO(response.content))
        if author.is_animated:
            author.seek(author.n_frames//2)
            author = author.convert(mode="RGB")

        # find good font and size set depending on text length
        #print(length)
        if length <= 30:
            limit = 22
            fontsize = 22
        elif length <= 60:
            limit = 22
            fontsize = 17
        else:
            await channel.send(self.client.emj['shiori'])
            await self.logger.send('mind: input text length exceeds maximum allowable')
            return

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
            change.save(os.path.join(dir,'shen/post/changemymind.png'))
            change.close()
            
        await channel.send(file=discord.File(os.path.join(dir,'shen/post/changemymind.png')))

    @commands.command(
        usage=".muimi [image_url] / [attachment]",
        help="No description... yet."
    )
    async def muimi(self, ctx, url:str=None):
        channel = ctx.channel
        check = await self.active_check(channel)
        if not check:
            return

        # attachment takes priority
        # check msg for link
        if url != None:
            link = url

        # check msg for attachment
        if ctx.message.attachments != []:
            #print('att found', ctx.message.attachments[0].filename)
            link = ctx.message.attachments[0].url
        
        async with ctx.typing():
            if not self.muimi_embed(ctx, link) is None:
                await ctx.message.delete()
                await channel.send(file=self.muimi_embed(ctx, link))
            else:
                await channel.send(self.client.emj['maki'])

    def muimi_embed(self, ctx, url):
        OUT = os.path.join(dir,'shen/post/muimi.png')
        response = requests.get(url)        
        # attempt to open image
        try:
            bg = Image.open(BytesIO(response.content))
        except Exception as err:
            print(err)
            return None
        try:
            if bg.is_animated:
                #print(func, 'bg is animated - no support yet')
                return None
        except Exception as err:
            # may not support .is_animated
            pass

        # image augmentation
        muimi_fg = Image.open(os.path.join(dir,'shen/assets/muimi_this_c.png'))
        fg_size = muimi_fg.size
        #fg_ratio = fg_size[0]/fg_size[1]

        # muimi size
        # fg_size -> (1280, 894)
        # fg_ratio -> 1.43177

        # size -> (width, height)
        bg_size = bg.size
        bg_ratio = bg_size[0]/bg_size[1]   

        # okay, so there are a lot of conditions to check right now.

        # check size - cannot be smaller than this for upscalling reasons
        LIMIT = 300
        if bg_size[0] < LIMIT or bg_size[1] < LIMIT:
            print('limit reached')
            return None
        # check aspect ratio
        elif bg_ratio < 0.2 or bg_ratio > 3:
            print('AR beyond tolerance')
            return None

        # to mitigate an image getting bigger and bigger with following recursions, each image will be scaled to muimi size
        # always scale height to muimi height
        target_size = (int(fg_size[1]*bg_ratio), fg_size[1])
        bg = bg.resize(target_size, resample=Image.ANTIALIAS)

        # target pos - line up with x=400 as close as possible
        left_clearance =    400
        right_clearance =   fg_size[0] - left_clearance
        bg_half_width =     int(bg_size[0]/2)

        # case 1 - bg half width clearance smaller than muimi left clearance
        if bg_half_width <= left_clearance:
            pos_x = 0
            pos_y = left_clearance - bg_half_width
            fg = muimi_fg.copy()
        
            try:
                muimi_fg.paste(bg, (pos_x, pos_y), bg)
            except Exception as err:
                muimi_fg.paste(bg, (pos_x, pos_y))
            finally:
                muimi_fg.paste(fg, (0,0), fg)

            muimi_fg.save(OUT)
            fg.close()
        # case 2 - bg half width clearance larger than muimi left clearance but smaller than muimi right clearance
        elif bg_half_width <= right_clearance:
            base = Image.new('RGBA', ( bg_half_width + right_clearance, fg_size[1]), (255,0,0,0))
            try:
                base.paste(bg, (0,0), bg)
            except Exception as err:
                base.paste(bg, (0,0))
            finally:
                base.paste(muimi_fg, (bg_half_width - left_clearance,0), muimi_fg)

            base.save(OUT)
            base.close()
        # case 3 - bg half clearance larger than muimi
        elif bg_half_width > right_clearance:
            bg.paste(muimi_fg, (bg_half_width - left_clearance,0), muimi_fg)
            bg.save(OUT)
        # somthing wrong happened
        else:
            muimi_fg.close()
            bg.close()
            return None

        muimi_fg.close()
        bg.close()
        return discord.File(OUT, filename=OUT)


def setup(client):
    client.add_cog(shenpCog(client))