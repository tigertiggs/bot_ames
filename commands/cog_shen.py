# this module takes care of all shitpost commands that does not require the PIL module
from sys import path_importer_cache
import discord
from discord.ext import commands
import datetime, asyncio, os, json, requests, copy
from difflib import SequenceMatcher as sm
from PIL import Image
import random
from imgur_python import Imgur
from io import BytesIO

class shenCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = "[shen]"
        self.logger = client.log
        self.colour = discord.Colour.from_rgb(*self.client.config['command_colour']['cog_shen'])
        with open(os.path.join(self.client.config['shen_path'],"other","_config.json"), "r") as c:
            self.config = json.load(c)
        
        if not self.client.private['imgur']['token']:
            self.imgur = Imgur({"client_id":self.client.private['imgur']['id'], "client_secret": self.client.private['imgur']['secret']})
            self.client.private['imgur']['token'] = self.imgur.authorize()
            print(self.name, "access token expired or missing for imgur")
            return
        else:
            self.imgur = Imgur({"client_id":self.client.private['imgur']['id'], "client_secret": self.client.private['imgur']['secret'], "access_token": self.client.private['imgur']['token']})
 
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        channel = message.channel
        if not self.client.command_status['emote'] == 1:
            raise commands.DisabledCommand
            
        if message.content.startswith(self.client.prefix):
            msg_pp = message.content.strip("".join(self.client.prefix))
            if msg_pp in list(self.client.emotes.keys()):
                await message.delete()
                await message.channel.send(self.client.emotes[msg_pp])
                return

            msg_pp, _, request = msg_pp.partition(" ")
            if not msg_pp in list(self.config.keys()):
                return
            active = self.config[msg_pp]
            if "red" in active["tags"] and message.guild.id != 419624511189811201:
                return
            elif not active['active']:
                return
            elif not active['images']:
                return 
            
            try:
                if request:
                    request = int(request)
                else:
                    request = random.choice(list(range(len(active['images']))))
            except:
                request = active['default']
            finally:
                if request >= len(active['images']) or request < 0:
                    request = random.choice(list(range(len(active['images']))))
            
            await channel.send(active['images'][request])

    @commands.group(invoke_without_command=True, case_insensitive=True, pass_context=True)
    async def shen(self, ctx, *, cmd):
        author = ctx.message.author
        channel = ctx.message.channel
        if ctx.invoked_subcommand is None and cmd in self.config and self.client._check_author(author):
            pass
    
    @shen.command() # appends
    async def add(self, ctx, *, cmd):
        author = ctx.message.author
        channel = ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        cmd = dict([c.split("=") for c in cmd.split("&")])
        #name=key&link=a,b,c
        if not "name" in cmd:
            await channel.send("missing name")
            return
        elif not cmd['name'] in self.config:
            await channel.send(f"`{cmd['name']}` is an invalid name")
            return
        
        links = cmd.get("link","").split(",") + [i.url for i in ctx.message.attachments]
        if not any(links):
            await channel.send("Emtpy requests or all requests are invalid")
            return

        for link in links:
            if not link:
                continue
            msg = await channel.send(f"appending `{link}`...")
            try:
                
                im = Image.open(BytesIO(requests.get(link).content))
                path = os.path.join(self.client.dir, self.client.config['shen_path'], "other", "temp."+im.format.lower())
                im.save(path)

                response = self.imgur.image_upload(
                    path,
                    None,
                    None,
                    None,
                    1
                )
                if response['status'] != 200:
                    await msg.edit(content=msg.content+str(response['status']))
                    continue
                else:
                    self.config[cmd['name']]['images'].append(response['response']['data']['link'])
            except Exception as e:
                await msg.edit(content=msg.content+str(e))
                continue

        with open(os.path.join(self.client.config['shen_path'],"other","_config.json"), "w+") as c:
            c.write(json.dumps(self.config,indent=4))
        await channel.send("saved")
        
    @shen.command()# creates new category
    async def new(self, ctx, *, cmd):
        author = ctx.message.author
        channel=ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        #name=str&seq=0&default=0&tags=a,b,c
        cmd = dict([c.split("=") for c in cmd.split("&")])
        if not 'name' in cmd:
            await channel.send("missing name")
            return
        elif cmd['name'] in self.config:
            await channel.send(f"`{cmd['name']}` already exists")
            return
        seq = False
        default = 0
        tags = []
        temp = copy.deepcopy(self.config['template'])
        
        for k,v in cmd.items():
            if k == 'seq':
                temp['sequencial'] = True if v == "1" else seq
            elif k == 'tags':
                temp['tags'] = v.split(",") if all(v.split(",")) else tags
            elif k == 'default':
                temp['default'] = int(v) if v.isnumeric() else default
        
        self.config[cmd['name']] = temp
        with open(os.path.join(self.client.config['shen_path'],"other","_config.json"), "w+") as c:
            c.write(json.dumps(self.config,indent=4))
        await channel.send("saved")
    
    @shen.command()
    async def edit(self, ctx, *, cmd):
        author = ctx.message.author
        channel=ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        cmd = dict([c.split("=") for c in cmd.split("&")])
        #name=key&seq=0&tags=a,+b,-c&default=0
        if not "name" in cmd:
            await channel.send("missing name")
            return
        elif not cmd['name'] in self.config:
            await channel.send(f"`{cmd['name']}` is an invalid name")
            return
        active = self.config[cmd['name']]
        for k,v in cmd.items():
            if k == 'seq':
                active['sequencial'] = True if v == "1" else False
            elif k == 'tags':
                arr = []
                for tag in v.split(","):
                    if tag.startswith("+"):
                        tag = tag[1:]
                        active['tags'].append(tag)
                    elif tag.startswith("-"):
                        tag = tag[1:]
                        try:
                            active['tags'].pop(active['tags'].index(tag = tag[1:]))
                        except:
                            continue
                    else:
                        arr.append(tag)
                if arr:
                    active['tags'] = arr
            elif k == 'default':
                active['default'] = int(v) if v.isnumeric() else 0
            elif k == "active":
                active['active'] = True if v == "1" else False

        with open(os.path.join(self.client.config['shen_path'],"other","_config.json"), "w+") as c:
            c.write(json.dumps(self.config,indent=4))
        await channel.send("saved")
    
    @shen.command()
    async def delete(self,ctx,*,cmd):
        author = ctx.message.author
        channel=ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        cmd = dict([c.split("=") for c in cmd.split("&")])
        #name=str&index=1,2,3,4...
        if not "name" in cmd:
            await channel.send("missing name")
            return
        elif not cmd['name'] in self.config:
            await channel.send(f"`{cmd['name']}` is an invalid name")
            return
        active = self.config[cmd['name']]
        try:
            index = sorted([int(i) for i in cmd['index'].split(",")], reverse=True)
        except:
            await channel.send("failed to read indicies")
            return
        for i in index:
            try:
                active['images'].pop(i)
            except:
                await channel.send(f"failed to unlist {i}")
                continue

        with open(os.path.join(self.client.config['shen_path'],"other","_config.json"), "w+") as c:
            c.write(json.dumps(self.config,indent=4))
        await channel.send("saved")

    @commands.command(
        usage='.big [arg:discord_emote_animated_okay]',
        aliases=['b', 'e', 'emote'],
        help='Enlarge the emote.'
    )
    async def big(self, ctx, emote:str="",num:int=1):
        channel = ctx.channel
        if not self.client.command_status['big'] == 1:
            raise commands.DisabledCommand
        elif not emote:
            return
        # try extracting id
        emote1 = emote[1:-1].split(':')
        if emote1[0] == '' and len(emote1) > 1:
            link = f"https://cdn.discordapp.com/emojis/{emote1[-1]}.png"
        elif emote1[0] == 'a' and len(emote1) > 1:
            link = f"https://cdn.discordapp.com/emojis/{emote1[-1]}.gif"
        else:
            targets = list(filter(lambda x: not x.guild_id in (self.client.private['resource_servers'] + self.client.private['bo_resource_servers']) and sm(None, emote.lower(), x.name.lower(), None).ratio() >= 0.25 and emote.lower() in x.name.lower(), self.client.emojis))
            if len(targets) > 0:
                targets.sort(key=lambda x: x.name)
                try:
                    emote = targets[num-1]
                except:
                    emote = targets[0]
                if not emote.animated:
                    link = f"https://cdn.discordapp.com/emojis/{emote.id}.png"
                else:
                    link = f"https://cdn.discordapp.com/emojis/{emote.id}.gif"
            else:
                await channel.send('https://cdn.discordapp.com/emojis/617546206662623252.png')
                return
        author = ctx.message.author
        embed = discord.Embed(colour=self.colour)
        embed.set_author(name=f"{author.name} sent:",icon_url=author.avatar_url)
        #print(link)
        embed.set_image(url=link)
        await ctx.message.delete()
        await channel.send(embed=embed)

    @commands.command(
        usage=".find [emote|optional]",
        aliases=['f'],
        help='List all emotes available to Ames or search for an emote.'
    )
    async def find(self, ctx, option:str=None):
        channel = ctx.channel
        author = ctx.message.author
        if not self.client.command_status['efinder'] == 1:
            raise commands.DisabledCommand
        # filter out restricted emojis
        emotes = list(filter(lambda x: not x.guild_id in (self.client.private["resource_servers"] + self.client.private['bo_resource_servers']), self.client.emojis))
        emotes.sort(key=lambda x: x.name)

        if option == None:
            emotes_per_column = 20
            find_controller = self.client.page_controller(self.client, self.make_find_embed, emotes, 3*emotes_per_column, True)

            finder = await channel.send(embed=find_controller.start())
            for arrow in find_controller.arrows:
                await finder.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and\
                    reaction.emoji in find_controller.arrows and\
                    str(reaction.message.id) == str(finder.id)

            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=90.0, check=author_check)
                except asyncio.TimeoutError:
                    for arrow in find_controller.arrows:
                        await finder.remove_reaction(arrow, self.client.user)
                    break
                else:
                    if reaction.emoji == find_controller.arrows[0]:
                        await reaction.message.edit(embed=find_controller.flip('l'))
                    elif reaction.emoji == find_controller.arrows[1]:
                        await reaction.message.edit(embed=find_controller.flip('r'))
                    else:
                        continue
                    await reaction.message.remove_reaction(reaction.emoji, user)
        else:
            cutoff = 0.25
            max = 20
            approx = list(filter(lambda x: sm(None, option.lower(), x.name.lower(), None).ratio() >= cutoff and option in x.name.lower(), emotes))[:max]
            embed = discord.Embed(description=f'Listing the top {max} results correspoinding to `{option}`',
                                    timestamp=datetime.datetime.utcnow(),colour=self.colour)
            embed.set_footer(text='Find Page | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
            embed.set_author(name="Emotefinder")
            if len(approx) > 0:
                #approx.sort(key=lambda x: x.name)
                embed.add_field(
                    name='Emote',
                    value="\n".join([f"<:{emote.name}:{emote.id}> [{str(i+1) if len(str(i+1)) == 2 else str(i+1)+' '}]" if not emote.animated else f"<a:{emote.name}:{emote.id}> [{str(i+1) if len(str(i+1)) == 2 else str(i+1)+' '}]" for i, emote in enumerate(approx)]),
                    inline=True
                )
                embed.add_field(
                    name="Name",
                    value="\n".join([emote.name for emote in approx]),
                    inline=True
                )
                embed.add_field(
                    name="Guild",
                    value="\n".join([self.client.get_guild(emote.guild_id).name for emote in approx]),
                    inline=True
                )
            else:
                embed.add_field(
                    name="Hmmm",
                    value="Nothing found",
                )
            await channel.send(embed=embed)
            
    def make_find_embed(self, emotes, page):
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), colour=self.colour)
        embed.set_footer(text='Find Page | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        embed.set_author(name=f"Emotedex - Page {page[0]} of {page[1]}")

        for column in self.client.chunks(emotes, 20):
            embed.add_field(
                name='Emotes',
                value="\n".join([f"<:{emote.name}:{emote.id}> {emote.name}" if not emote.animated else f"<a:{emote.name}:{emote.id}> {emote.name}" for emote in column]),
                inline=True
            )
        
        return embed

#    @commands.command()
#    async def bruh(self, ctx):
#        channel=ctx.channel
#        if not self.client.command_status['bruh'] == 1:
#            raise commands.DisabledCommand
#        
#        await channel.send(file=discord.File(os.path.join(self.client.dir,self.client.config['shen_path'],"other/bruh.png")))

#    @commands.command()
#    async def broke(self, ctx, *num:int):
#        channel=ctx.channel
#        if ctx.message.guild.id != 419624511189811201:
#            return
#        else:
#            available = list(range(1,len([i for i in self.config['red']['images'] if i.startswith('broke')])+1))
#            if not num:
#                request = 3
#            else:
#                request = num[-1]
#            
#            if not request or not request in available:
#                await channel.send(self.config['red']['images'][random.choice([i for i in self.config['red']['images'] if i.startswith('broke')])])
#            else:
#                await channel.send(self.config['red']['images'][[i for i in self.config['red']['images'] if i.split(".")[0] == f"broke{num}"][0]])

#    @commands.command()
#    async def roko(self, ctx, *num:int):
#        channel=ctx.channel
#        fnames = list(self.config['roko']['images'].keys())
#        available = list(range(len(fnames)))
#        if not num or not num[0] in available:
#            request = random.choice(fnames)
#        else:
#            request = f"roko{available[num[0]]}.png"
#
#        await channel.send(self.config['roko']['images'][request])

def setup(client):
    client.add_cog(shenCog(client))