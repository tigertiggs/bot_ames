# this module handles the listeners for pcrd twitter feeds
# this also relies on an external bot/service that ames happens to be hosted together with

import discord
from discord.ext import commands, tasks
import requests, json, os
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
        with open(os.path.join(self.client.dir, self.client.config["twitter_guilds_path"])) as gf:
            self.guilds = json.load(gf)
        
        #self.listeners = []
        self.listener.start()
        
    
    def cog_unload(self):
        self.listener.cancel()

    @tasks.loop(seconds=timer)
    async def listener(self):
        if not self.config["active"]:
            return
        for acc_id in list(self.config["accounts"].values()):
            # construct request url
            if self.client.config["port"] != "default":
                url = f"http://localhost:{self.client.config['port']}/FagUtils/gateway.php?cmd=twit.get.feed&include_rts=1&type=timeline&id={acc_id}&ames"
            else:
                url = f"http://localhost/FagUtils/gateway.php?cmd=twit.get.feed&include_rts=1&type=timeline&id={acc_id}&ames"
            
            # get
            try:
                result = requests.get(url)
                payload = json.load(BytesIO(result.content))
            except Exception as e:
                await self.logger.send(self.name, e)
                return
            
            # only proceed if status code is green
            if payload['status'] == 200:

                # load cache
                try:
                    with open(os.path.join(self.client.dir, self.client.config["twitter_cache_path"], f"{acc_id}.json")) as cf:
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
                        for guild_id, status in list(self.guilds.items()):
                            if status.get(acc_id, None) != None:

                                if status[acc_id]["active"] and not status[acc_id].get("channel_id",None) == None:
                                    channel = self.client.get_guild(int(guild_id)).get_channel(status[acc_id]["channel_id"])
                                    
                                    if channel != None:
                                        for msg in temp:
                                            try:
                                                if msg["type"] == "embed":
                                                    await channel.send(embed=msg["payload"])
                                                elif msg["type"] == "text":
                                                    await channel.send(msg["payload"])
                                            except:
                                                continue
                # save cache
                with open(os.path.join(self.client.dir, self.client.config["twitter_cache_path"], f"{acc_id}.json"),"w+") as cf:
                    cf.write(json.dumps(cache, indent=4))

            else:
                await self.logger.send(self.name, payload["status"])

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
        guild_ann = self.guilds.get(str(guild.id), dict())
        services = list(self.config["accounts"].keys())
        acc_ids = list(self.config["accounts"].values())
        embed=discord.Embed(
            title="Announce",
            description="The following twitter listeners have been linked.",
            timestamp=datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Announce | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Available listeners",
            value="\n".join(services),
            inline=True
        )
        embed.add_field(
            name="Active",
            value="\n".join(["True" if guild_ann.get(acc_id, dict()).get("active", False) else "False" for acc_id in acc_ids]),
            inline=True
        )
        embed.add_field(
            name="Bound Channel",
            value="\n".join([str(guild.get_channel(int(guild_ann.get(acc_id, dict()).get("channel_id", None)))) if guild_ann.get(acc_id, dict()).get("channel_id", None) != None else "Not set" for acc_id in acc_ids]),
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
        
        guild_ann = self.guilds.get(str(author.guild.id), dict())
        serv_ann = guild_ann.get(self.config["accounts"][service], dict())
        if mode == "channel":
            msg = await channel.send(f"Set `{service}` announce to `{set_channel.name}`...")
            serv_ann["channel_id"] = channel_id
        else:
            msg = await channel.send(f"Set `{service}` active status to `{status}`...")
            serv_ann["active"] = True if status == 1 else False
        
        # final checks
        if serv_ann.get("channel_id", None) == None:
            serv_ann["channel_id"] = None

        if serv_ann.get("active", None) == None:
            serv_ann["active"] = True
        
        guild_ann[self.config["accounts"][service]] = serv_ann
        self.guilds[str(author.guild.id)] = guild_ann

        with open(os.path.join(self.client.dir, self.client.config["twitter_guilds_path"]), "w+") as gf:
            gf.write(json.dumps(self.guilds, indent=4))
            await msg.edit(content=msg.content+"saved")

def setup(client):
    client.add_cog(twitterCog(client))