# this module handles the listeners for pcrd twitter feeds
# this also relies on an external bot/service that ames happens to be hosted together with

import discord
from discord.ext import commands, tasks
import requests, json, os, copy, traceback
from datetime import datetime
from io import BytesIO
timer = 60

class twitterCog(commands.Cog):
    def __init__(self, client):
        global timer
        self.client = client
        self.logger = client.log
        self.name = "[twitter]"
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_twitter'])
        
        # load configs
        with open(os.path.join(self.client.dir, self.client.config['twitter_config_path'])) as tf:
            self.config = json.load(tf)
            timer = self.config['timer']
        #with open(os.path.join(self.client.dir, self.client.config["twitter_guilds_path"])) as gf:
        #    self.guilds = json.load(gf)
        
        #self.listeners = []
        self.listener.start()
        
    
    def cog_unload(self):
        self.listener.cancel()

    @tasks.loop(seconds=timer)
    async def listener(self):
        #with open(os.path.join(self.client.dir, self.client.config['twitter_config_path'])) as tf:
        #    config = json.load(tf)

        if not self.config["active"]:
            return
        for service in list(self.config["accounts"].values()):
            # check if the service is active and a nonzero number of subscriptions
            if not service['active'] or len(service['guilds']) == 0:
                continue
            
            # construct request url
            if self.client.config["port"] != "default":
                url = f"http://localhost:{self.client.config['port']}/FagUtils/gateway.php?"
            else:
                url = "http://localhost/FagUtils/gateway.php?"
            
            # get
            try:
                params = {
                    "cmd":              "twit.get.feed",
                    "include_rts":      1 if service['includeRT'] else 0,
                    "include_replies":  0,
                    "type":             "timeline",
                    "id":               service['id'],
                    "ames":             1
                }
                result = requests.get(url, params=params)
                payload = json.load(BytesIO(result.content))
            except Exception as e:
                await self.logger.send(self.name, e)
                await self.logger.send(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
                return
            
            # only proceed if status code is green
            if payload['status'] == 200:

                # load cache
                try:
                    with open(os.path.join(self.client.dir, self.client.config["twitter_cache_path"], f"{service['id']}.json")) as cf:
                        cache = json.load(cf)
                except:
                    cache = {"tweet_idv":[]}
                
                # iterate throug tweets; tweets are sorted by most recent so reverse the array
                for tweet in payload["result"]["tweets"][::-1]:

                    # only proceed if the tweet havent been already been sent
                    if not tweet["tweet_id"] in cache["tweet_idv"]:

                        # prepare embeds
                        embed, tweet = self.make_main_tweet_embed(payload["result"]["user"], tweet)                    
                        temp = [embed]

                        # process additional media
                        for media in tweet["media"]:
                            if media["type"] == "photo":
                                temp.append(self.make_ad_image_embed(payload["result"]["user"],tweet,media["url"]))
                            elif media["type"] == "video" or media["type"] == "animated_gif":
                                temp.append({"type":"text","payload":media["url"]})

                        # append to id to cache
                        cache["tweet_idv"].append(tweet["tweet_id"])
                        if len(cache["tweet_idv"]) > self.config["cache_limit"]:
                            cache["tweet_idv"].pop(0)

                        # push data to guilds that have the feature enabled
                        for guild in service['guilds'].values():
                            try:
                                if guild['active'] and not guild.get("channel", None) == None:
                                    channel = self.client.get_guild(guild['id']).get_channel(guild['channel'])
                                    if channel != None:
                                       for msg in temp:
                                            try:
                                                if msg["type"] == "embed":
                                                    await channel.send(embed=msg["payload"])
                                                elif msg["type"] == "text":
                                                    await channel.send(msg["payload"])
                                            except:
                                                continue 
                            except Exception as e:
                                await self.logger.send(self.name, service['name'], 'failed to send tweet:', e)
                                continue
                        
                # save cache
                with open(os.path.join(self.client.dir, self.client.config["twitter_cache_path"], f"{service['id']}.json"),"w+") as cf:
                    cf.write(json.dumps(cache, indent=4))

            else:
                await self.logger.send(self.name, 'return code', payload["status"])
                await self.logger.send(payload)
                await self.logger.send(f'```{service}```')

    @listener.before_loop
    async def before_listener(self):
        print(self.name, "Awaiting client...", end="")
        await self.client.wait_until_ready()
        print("started")

    def make_main_tweet_embed(self, user, tweet):
        embed = discord.Embed(
            title="Link to tweet",
            url=f"https://twitter.com/{user['screen_name']}/status/{tweet['tweet_id']}",
            description=(f"RT by [@{user['screen_name']}](https://twitter.com/{user['screen_name']})\n" if tweet['isRT'] else "") + self.construct_tweet_text(tweet),
            timestamp=datetime.strptime(tweet["date"], "%a %b %d %H:%M:%S %z %Y"),
            colour=self.colour
        )
        embed.set_thumbnail(url=user["image_url"] if not tweet["isRT"] else tweet["RTUser"]["image_url"])
        if not tweet["isRT"]:
            embed.set_author(name=f"{user['name']}(@{user['screen_name']})",url=f"https://twitter.com/{user['screen_name']}")
        else:
            embed.set_author(name=f"{tweet['RTUser']['name']}(@{tweet['RTUser']['screen_name']})",url=f"https://twitter.com/{tweet['RTUser']['screen_name']}")
        embed.set_footer(text="Tweet sent at:", icon_url=self.client.user.avatar_url)
        if len(tweet["media"]) > 0:
            if tweet["media"][0]["type"] == "photo":
                embed.set_image(url=tweet["media"].pop(0)["url"])
        return {"type":"embed","payload":embed}, tweet
    
    def construct_tweet_text(self, tweet):
        text = tweet["text"]
        for replacement in tweet["replacements"]:
            text = text.replace(replacement["marker"],
            f"[{replacement['text']}]({replacement['link']})")
        while "{br}" in text:
            text = text.replace("{br}", "\n")
        return text
        
    def make_ad_image_embed(self, user, tweet, url):
        embed=discord.Embed(
            title="[Additional Image]",
            url=f"https://twitter.com/{user['screen_name']}/status/{tweet['tweet_id']}",
            timestamp=datetime.strptime(tweet["date"], "%a %b %d %H:%M:%S %z %Y"),
            colour=self.colour
        )
        embed.set_image(url=url)
        embed.set_footer(text="Tweet sent at:", icon_url=self.client.user.avatar_url)
        return {"type":"embed","payload":embed}

    @commands.group(invoke_without_command=True,aliases=["ann"])
    async def announce(self, ctx):
        channel=ctx.channel
        author=ctx.message.author
        if ctx.invoked_subcommand is None:
            await channel.send(embed=self.make_announce_embed(author.guild))
    
    def make_announce_embed(self, guild):
        services =  []
        active =    []
        channel =   []
        for service_code, service in sorted(self.config['accounts'].items(), key=lambda x: x[0]):
            guild_info = service['guilds'].get(str(guild.id), {})
            set_channel = guild.get_channel(guild_info.get('channel', 0))

            services.append(f"{':green_square:' if guild_info.get('active', False) else ':black_large_square:'} {service_code}")
            #services.append(f"{'1' if guild_info.get('active', False) else '0'} `{service_code}`")
            active.append(service['name'])
            channel.append(f"<#{set_channel.id}>" if set_channel else 'Not set')
        
        embed=discord.Embed(
            title="Announce",
            description="The following twitter listeners are available.",
            timestamp=datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Announce | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="ID (active|id)",
            value="\n".join(services),
            inline=True
        )
        embed.add_field(
            name="Full Title",
            value="\n".join(active),
            inline=True
        )
        embed.add_field(
            name="Bound Channel",
            value="\n".join(channel),
            inline=True
        )
        return embed

    @announce.command()
    async def set(self, ctx, service, status:str):
        author=ctx.message.author
        channel=ctx.message.channel
        # checks
        if not self.client._check_author(author, "admin"):
            await channel.send("Missing [admin] permission "+self.client.emotes['ames'])
            return
        elif not service in list(self.config['accounts'].keys()):
            await channel.send(f"`{service}` is not a valid service. Please use `.announce` to see all available services or `.help announce` for more details.")
            return

        # param check - status is either a single digit or a channel
        if len(status) == 1:
            # digit?
            try:
                status = int(status)
            except:
                await channel.send(f"Unknown state {status}")
                return
            else:
                mode="status"
        # check if its a channel
        else:
            try:
                channel_id = int(status[2:-1])
                set_channel = author.guild.get_channel(channel_id)
                if set_channel == None:
                    await channel.send("Failed to find channel")
                    return
            except:
                await channel.send("Failed to read channel")
                return
            else:
                mode="channel"
        
        guild_ann = self.config['accounts'][service]['guilds'].get(str(author.guild.id), 
        {
            "id":       author.guild.id,
            "active":   True,
            "channel":  None
        })

        if mode == "channel":
            msg = await channel.send(f"Binding `{service}` -> {self.config['accounts'][service]['name']} listener to <#{channel_id}>...")
            guild_ann["channel"] = channel_id
        else:
            msg = await channel.send(f"Turning `{service}` {'on' if status == 1 else 'off'}...")
            guild_ann["active"] = True if status == 1 else False
        
        self.config['accounts'][service]['guilds'][str(author.guild.id)] = guild_ann

        with open(os.path.join(self.client.dir, self.client.config['twitter_config_path']), "w+") as gf:
            gf.write(json.dumps(self.config, indent=4))
            await msg.edit(content=msg.content+" saved")

    @announce.command(aliases=['edit'])
    async def add(self, ctx, code, *, input):
        author = ctx.message.author
        channel = ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        elif not input:
            return
        mode = ctx.invoked_with

        # process
        params = dict([kv.split('=') for kv in input.split("&")])

        # checks
        flag = code in self.config['accounts']
        if mode == 'add' and flag:
            await channel.send(f"could not add: `{code}` already exists")
            return
        elif mode == 'edit' and not flag:
            await channel.send(f"could not edit: `{code}` does not exist")
            return
        
        service = copy.deepcopy(
            self.config['accounts'].get(code, 
                {
                    "name":         "",
                    "id":           0,
                    "active":       True,
                    "includeRT":    True,
                    "guilds":       {}
                }
            )
        )
        
        msg = await channel.send(f"{'Adding' if mode == 'add' else 'Editing'} `{code}`...")

        if params.get('tag', None):
            self.config['accounts'].pop(code)
            await channel.send(f"deleting old code `{code}` and replacing with `{params['tag']}`")
            code = "_".join(params['tag'].split())

        for key in service:
            if params.get(key, "") != "":
                if key in ['active','includeRT']:
                    service[key] = True if int(params[key]) else False
                    await channel.send(f"set `{key}` to {params[key]}")
                elif key == "id":
                    service[key] = int(params[key])
                    await channel.send(f"set `{key}` to {params[key]}")
                elif key == 'name':
                    service[key] = params[key]
                    await channel.send(f"set `{key}` to {params[key]}")

        self.config['accounts'][code] = service
        with open(os.path.join(self.client.dir, self.client.config['twitter_config_path']), "w+") as gf:
            gf.write(json.dumps(self.config, indent=4))
            await msg.edit(content=msg.content+" saved")
        
    @announce.command(aliases=['m'])
    async def master(self, ctx):
        author = ctx.message.author
        channel = ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        await channel.send(embed=self.make_ann_m_embed())

    def make_ann_m_embed(self):
        services =  []
        active =    []
        channel =   []

        for service_code, service in sorted(self.config['accounts'].items(), key=lambda x: x[0]):
            services.append(service_code)
            active.append(f"{':green_square:' if service['active'] else ':black_large_square:'} {':green_square:' if service['includeRT'] else ':black_large_square:'} {len(service['guilds'])} {service['id']}")
            channel.append(service['name'])
        
        embed=discord.Embed(
            title="Master Announce (twitterconfig)",
            timestamp=datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Master Announce | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Status",
            value="Active" if self.config['active'] else "Inactive"
        )
        embed.add_field(
            name="Refresh Frequency",
            value=f"{self.config['timer']}s"
        )
        embed.add_field(
            name="Max Cache Depth",
            value=str(self.config['cache_limit'])
        )
        embed.add_field(
            name="id",
            value="\n".join(services),
            inline=True
        )
        embed.add_field(
            name="active|RT|sub|tid",
            value="\n".join(active),
            inline=True
        )
        embed.add_field(
            name="title",
            value="\n".join(channel),
            inline=True
        )
        return embed
        
def setup(client):
    client.add_cog(twitterCog(client))