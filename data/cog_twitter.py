from nextcord.ext import commands, tasks
from nextcord import File
import utils as ut
import templates as tem
import json, requests, traceback, re
from datetime import datetime, timezone
from io import BytesIO
from glob import iglob

TIMER = 60

def setup(client):
    client.add_cog(twitterCog(client))

class twitterCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[Twitter]'
        self.logger = ut.Ames_logger(self.name, self.client.Log)
        self.logger.init_client(self.client)

        self.rel_path = ut.full_path(self.client.dir, self.client.config['configs']['twitter'])

        with open(ut.full_path(self.rel_path, 'twitter_config.json')) as f:
            self.twitter_cf = json.load(f)
            # override with main config port
            self.twitter_cf['port'] = self.client.config['fag_port']
        
        if not self.twitter_cf['port']:
            self.api = self.twitter_cf['api']
        else:
            self.api = self.twitter_cf['api_port'].format(self.twitter_cf['port'])
        
        self.t = re.compile(
            "^(?:https?:\/\/(?:(?:mobile|web).)?)?twitter\.com(?:(?:\/i\/web)?|(?:\/[a-zA-Z\d_]+))\/status\/(?P<tweet_id>[\d]+)(?:\?s=\d+|\/photo\/\d+)?(?:(?:&|\?|\/)[^\s]*)?$")
            #, re.DEBUG)

        self.p1 = re.compile("^(?:https?:\/\/)?(?:www\.)?(?:pixiv.net\/)?(?:member[^\s]+illust_id=)?(?P<Illust_ID>\d+)(?:[^\s]+)?$")
        self.p2 = re.compile("^(?:https?:\/\/)?(?:www\.)?(?:pixiv.net\/)?(?:.+\/)?(?:artworks\/)?(?P<Illust_ID>\d+)(?:[^\s]+)?$")

        self.listener.start()
    
    @commands.group(invoke_without_command=True, aliases=['twit', 'tw'])
    async def twitter(self, ctx, option=None):
        channel = ctx.channel
        author = ctx.author
        if ctx.invoked_subcommand is None:
            MODE_ADMIN = False
            if option:
                if option.lower().startswith('m') and self.client.check_perm(author):
                    MODE_ADMIN = True
                else:
                    return
            
            await channel.send(embed=self.tw_embed_guild(author, MODE_ADMIN))
                
    def tw_embed_guild(self, author, MODE):
        # try to load twitter guild properties
        try:
            with open(ut.full_path(self.rel_path, self.twitter_cf['guilds'], f"{author.guild.id}.json")) as f:
                gp = json.load(f)
        except FileNotFoundError:
            gp = tem.fetch('tw_guild')
        
        # load all listeners
        with open(ut.full_path(self.rel_path, self.twitter_cf['listeners'])) as f:
            lp = json.load(f)
        
        account = sorted(lp['account'].values(), key=lambda x: x['id'])

        if not MODE:
            embed = {
                'title': 'Master Twitter Listener',
                'descr': 'All registered twitter listeners listed below',
                'fields': [
                    {
                        'name': 'Timer',
                        'value': f"{TIMER}s",
                        'inline': False
                    },
                    {
                        'name': 'Cache depth',
                        'value': str(self.twitter_cf['cache_depth']),
                        'inline': False
                    }
                ]
            }
        else:
            embed = {
                'title': 'Guild Twitter Listener',
                'descr': 'All available twitter listeners listed below',
                'fields': [
                ]
            }
        
        embed['footer'] = {'text': 'Twitter Properties'}

        col1 = []
        col2 = []
        col3 = []
        for service in account:
            col2.append(service['name'])

            if MODE:
                col1.append(service['id'])
                col3.append(str(service['t_id']))
            else:
                prop = gp['services'].get(service['id'], tem.fetch('tw_guild_lis'))
                
                col1.append(f"{'🟩' if prop['active'] else '⬛'} {service['id']}")
                
                if prop['channel']:
                    ch = author.guild.get_channel(int(prop['channel']))
                    ch = f"<#{ch.id}>" if ch else 'Invalid channel'
                else:
                    ch = 'Channel not set'
                
                col3.append(ch)

        embed['fields'] += [
            {
                'name': 'Active, ID',
                'value': '\n'.join(col1) if col1 else ut.SPACE
            },
            {
                'name': 'Name',
                'value': '\n'.join(col2) if col2 else ut.SPACE
            }
        ]

        if MODE:
            embed['fields'].append({
                'name': 'Twitter ID',
                'value': '\n'.join(col3) if col3 else ut.SPACE
            })
        else:
            embed['fields'].append({
                'name': 'Bound Channel',
                'value': '\n'.join(col3) if col3 else ut.SPACE
            })
        
        return ut.embed_contructor(**embed)

    @twitter.command()
    async def set(self, ctx, lookup=None):
        author = ctx.author
        channel = ctx.channel

        if not self.client.check_perm(author):
            await channel.send('Insufficent permissions '+self.client.emotes['ames'])
            return
        elif not lookup:
            await channel.send("No input - see `.tw` for all avilable services")
            return
        
        with open(ut.full_path(self.rel_path, self.twitter_cf['listeners'])) as f:
            lf = json.load(f)

        SET_MODE = True
        IN_INDEX = lookup in lf['index']

        try:
            with open(ut.full_path(self.rel_path, self.twitter_cf['guilds'], f"{ctx.guild.id}.json")) as gpf:
                gp = json.load(gpf)
        except:
            gp = tem.fetch('tw_guild')

        if not IN_INDEX:
            await channel.send("Did not find requested service")
            return
        else:
            index = lf['index'][lookup]
            lp = lf['account'][index]
            glp = gp['services'].get(index, tem.fetch('tw_guild_lis'))
        
        msg = self.twit_set_msg(lp, glp, SET_MODE)
        msgctx = "> Command keys: `active[0 or 1]`, `channel[#channel]`, `exit`, `cancel`\n"\
            "Syntax: `key1:value1, key2:value2, ...`\n"
        
        msg += msgctx

        status = await channel.send(msg)
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel
        
        EXIT = False
        while True:            
            changes = []
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            for cmd in content.split(','):
                if not cmd: 
                    continue
                k, _, v = cmd.partition(':')

                k = k.strip().lower()
                v = v.strip().lower()
                is_none = not bool(v)

                if k == 'exit':
                    EXIT = True
                    break

                elif k == 'cancel':
                    await status.edit('Cancelled')
                    return

                elif k == 'active':
                    if v.startswith('1') or v.startswith('t'):
                        glp['active'] = True
                    elif v.startswith('0') or v.startswith('f'):
                        glp['active'] = False
                    else:
                        changes.append(f"`[{k}]`: Failed to read {v}")
                        continue

                    changes.append(f"`[{k}]`: Setting {k} to {glp['active']}")
                
                elif k == 'channel':
                    if v.startswith('<#'):
                        glp['channel'] = v[2:-1]
                    elif is_none:
                        glp['channel'] = None
                    else:
                        changes.append(f"`[{k}]`: Failed to read {v}")
                        continue

                    changes.append(f"`[{k}]`: Setting {k} to {glp['channel']}")

                else:
                    changes.append(f"Unknown key `[{k}]`")

            if changes:
                await status.edit(content=self.twit_set_msg(lp, glp, SET_MODE) + msgctx + '\n'.join(changes))
            if EXIT:
                break
        
        gp['services'][index] = glp
        with open(ut.full_path(self.rel_path, self.twitter_cf['guilds'], f"{ctx.guild.id}.json"), 'w+') as gpf:
            gp['id'] = author.guild.id
            gpf.write(json.dumps(gp, indent=4))
        
        await status.edit(content='Saved')

    def twit_set_msg(self, lp, glp, set_mode):
        if not set_mode:
            msg = f"> [Twitter] Setting `{lp['name']}`\n"\
                f"`Index ID`: {lp['id']}\n"\
                f"`Twitter ID`: {lp['t_id']}\n"\
                f"`Name`: {lp['name']}\n"\
                f"`Include RT`: {lp['rt']}\n"
        else:
            ch = f"<#{glp['channel']}>" if glp['channel'] else 'None'
            msg = f"**Active**: {glp['active']}\n"\
                f"**Channel**: {ch}\n"
        
        return msg
        
    @twitter.command(aliases=['new'])
    async def edit(self, ctx, lookup=None):
        author = ctx.author
        channel = ctx.channel

        if not self.client.check_perm(author, 'devs'):
            return

        SET_MODE = ctx.invoked_with == 'edit'
        if SET_MODE and not lookup:
            return

        try:
            with open(ut.full_path(self.rel_path, self.twitter_cf['listeners'])) as f:
                lf = json.load(f)
        except FileNotFoundError:
            lf = {'index': {}, 'account': {}}

        IN_INDEX = lookup in lf['index']

        if SET_MODE:
            if not IN_INDEX:
                await channel.send("Did not find requested service")
                return
            else:
                index = lf['index'][lookup]
                lp = lf['account'].pop(index)
        else:
            if IN_INDEX:
                await channel.end("Service already exists")
                return
            else:
                lp = tem.fetch('tw_listener')
        
        msg = self.twit_set_msg(lp, None, SET_MODE)
        msgctx = "> Command keys: `id`, `twid`, `name`, `rt`, `exit`, `cancel`\n"\
            "Syntax: `key1:value1, key2:value2, ...`\n"
        
        msg += msgctx

        status = await channel.send(msg)
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel
        
        EXIT = False
        while True:            
            changes = []
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            for cmd in content.split(','):
                if not cmd: 
                    continue
                k, _, v = cmd.partition(':')

                k = k.strip().lower()
                v = v.strip().lower()
                is_none = not bool(v)

                print(k, v, is_none)

                if k == 'exit':
                    # check
                    if not lp['id']:
                        status.append(f"Could not exit: id cannot be None")
                    elif not lp['name']:
                        status.append(f"Could not exit: name cannot be None")
                    else:
                        EXIT = True
                        break

                elif k == 'cancel':
                    await status.edit('Cancelled')
                    return
                
                elif k in ['id', 'name']:
                    lp[k] = v if not is_none else None
                    changes.append(f"`[{k}]`: Setting {k} to {lp[k]}")

                elif k == 'rt':
                    if v.startswith('1') or v.startswith('t'):
                        lp['rt'] = True
                    elif v.startswith('0') or v.startswith('f'):
                        lp['rt'] = False
                    else:
                        changes.append(f"`[{k}]`: Failed to read {v}")
                        continue

                    changes.append(f"`[{k}]`: Setting {k} to {lp['rt']}")
                
                elif k == 'twid':
                    if v.isnumeric():
                        lp['t_id'] = int(v)
                    elif is_none:
                        lp['t_id'] = None
                    else:
                        changes.append(f"`[{k}]`: Failed to read {v}")
                        continue

                    changes.append(f"`[{k}]`: Setting {k} to {lp['t_id']}")
                
                else:
                    changes.append(f"Unknown key `[{k}]`")

            if changes:
                await status.edit(content=self.twit_set_msg(lp, None, SET_MODE) + msgctx + '\n'.join(changes))
            if EXIT:
                break
        
        if SET_MODE:
            lf['account'][index] = lp
        else:
            lf['account'][lp['id']] = lp
        
        # make index
        for i in lf['account'].keys():
            lf['index'][i] = i

        with open(ut.full_path(self.rel_path, self.twitter_cf['listeners']), 'w+') as f:
            f.write(json.dumps(lf, indent=4))
        
        await status.edit(content='Saved')
    
    @twitter.command()
    async def convert(self, ctx, option=None):
        author = ctx.author
        channel = ctx.channel

        if not self.client.check_perm(author):
            return
        
        try:
            with open(ut.full_path(self.rel_path, self.twitter_cf['guilds'], f"{ctx.guild.id}.json")) as gpf:
                gp = json.load(gpf)
        except FileNotFoundError:
            gp = tem.fetch('tw_guild')

        if not option:
            await channel.send(f"Ames {'will' if gp['convert'] else 'will not'} convert twitter links in this server.")
            return

        option = option.lower()
        print(option)
        if option.startswith('0') or option.startswith('f'):
            gp['convert'] = False
        elif option.startswith('1') or option.startswith('t'):
            gp['convert'] = True
        else:
            await channel.send('Invalid input')
            return
        
        await channel.send(f"Ames {'will' if gp['convert'] else 'will not'} convert twitter links in this server.")
        with open(ut.full_path(self.rel_path, self.twitter_cf['guilds'], f"{ctx.guild.id}.json"), 'w+') as gpf:
            gpf.write(json.dumps(gp, indent=4))
        
    def make_twitter_embeds(self, userObj, tweetObj, author=None):
        main_embed, tweetObj = self.embed_twitter_main(userObj, tweetObj, author)
        embeds = [main_embed]
        links = []

        for media in tweetObj['media']:
            if media['type'] == 'photo':
                embeds.append(self.embed_twitter_image(userObj, tweetObj, media['url'], author))
            elif media['type'] in ['video', 'animated_gif']:
                links.append(media['url'])
        
        return embeds, links

    def embed_twitter_main(self, userObj, tweetObj, author=None):
        embed = {
            'title': "Link to tweet",
            'url': f"https://twitter.com/{userObj['screen_name']}/status/{tweetObj['tweet_id']}",
            'descr': (f"RT by [@{userObj['screen_name']}](https://twitter.com/{userObj['screen_name']})\n" if tweetObj['isRT'] else "") + self.construct_tweet_text(tweetObj),
            'thumb': userObj["image_url"] if not tweetObj["isRT"] else tweetObj["RTUser"]["image_url"],
            'author': 
                {'text': f"{userObj['name']}(@{userObj['screen_name']})", 'url': f"https://twitter.com/{userObj['screen_name']}"} if not tweetObj["isRT"] else
                {'text': f"{tweetObj['RTUser']['name']}(@{tweetObj['RTUser']['screen_name']})",'url': f"https://twitter.com/{tweetObj['RTUser']['screen_name']}"},
            'footer': 
                {'text': "Tweet sent at:", 'url': self.client.user.avatar.url} if not author else
                {'text': f"Sent by: {author.name}", 'url': author.avatar.url}
        }
        if tweetObj['media']:
            if tweetObj['media'][0]['type'] == 'photo':
                embed['image'] = tweetObj["media"].pop(0)["url"]
        return ut.embed_contructor(**embed), tweetObj # {'type': 'embed', 'payload': ut.embed_contructor(**embed)}, tweetObj
    
    def construct_tweet_text(self, tweet):
        text = tweet["text"]
        for replacement in tweet["replacements"]:
            text = text.replace(replacement["marker"],
            f"[{replacement['text']}]({replacement['link']})" if replacement.get('link', False) else replacement['text'])
        while "{br}" in text:
            text = text.replace("{br}", "\n")
        return text

    def embed_twitter_image(self, userObj, tweetObj, url, author=None):
        embed = {
            'title':"[Additional Image]",
            'url':f"https://twitter.com/{userObj['screen_name']}/status/{tweetObj['tweet_id']}",
            'image':url,
            'footer':{'text':"Tweet sent at:", 'url':self.client.user.avatar.url} if not author else
                {'text': f"Sent by {author.name}", 'url': author.avatar.url}
        }
        return ut.embed_contructor(**embed) #{"type":"embed","payload":ut.embed_contructor(**embed)}
    
    async def send_tw_embeds(self, embeds, links, channel, base_link, quoted_tweet_payload=None, quoted_link=None):
        parent = await channel.send(("[Quotes a Tweet]\n" if quoted_tweet_payload else "") + f"<{base_link}>", embed=embeds[0])
        for em in embeds[1:]:
            await parent.reply(embed=em)
        if links:
            await parent.reply('\n'.join(links))
        
        if quoted_tweet_payload:
            quoted_embeds, quoted_links = quoted_tweet_payload
            quoted = await parent.reply(f"[Quoted Tweet]\n<{quoted_link}>", embed=quoted_embeds[0])
            for em in quoted_embeds[1:]:
                await quoted.reply(embed=em)
            if quoted_links:
                await quoted.reply("\n".join(quoted_links))
    
    @tasks.loop(seconds=TIMER)
    async def listener(self):
        await self.func_listener()
    
    async def func_listener(self):
        # load listeners
        with open(ut.full_path(self.rel_path, self.twitter_cf['listeners'])) as f:
            lp = json.load(f)['account']
        
        # iterate through account
        for id, acc in lp.items():

            # load cache
            cln = f"{acc['t_id']}.json"
            try:
                with open(ut.full_path(self.rel_path, self.twitter_cf['caches'], cln)) as f:
                    cl = json.load(f)
            except FileNotFoundError:
                cl = {'idv': []}
            
            # fetch timeline
            try:
                params = {
                    "cmd":              "twit.get.feed",
                    "include_rts":      1 if acc['rt'] else 0,
                    "include_replies":  0,
                    "type":             "timeline",
                    "id":               acc['t_id'],
                    "ames":             1
                }
                result = requests.get(self.api, params=params)
                payload = json.load(BytesIO(result.content))
            except Exception as e:
                await self.logger.report(self.name, e)
                await self.logger.report(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
                return

            if payload['status'] == 200:

                for tweet in payload['result']['tweets'][::-1]:
                    base_link = f"https://twitter.com/{payload['result']['user']['screen_name']}/status/"

                    if not tweet['tweet_id'] in cl['idv']:
                        embeds, links = self.make_twitter_embeds(payload['result']['user'], tweet)

                        # check quoted status
                        quoted = tweet.get('quoted_status', None)
                        quoted_link = None
                        if quoted:
                            quoted_link = f"https://twitter.com/{quoted['user']['screen_name']}/status/{quoted['tweet']['tweet_id']}"
                            quoted = self.make_twitter_embeds(quoted['user'], quoted['tweet'])

                        cl['idv'].append(tweet['tweet_id'])
                        if len(cl['idv']) > self.twitter_cf['cache_depth']:
                            cl['idv'].pop(0)

                        # do timeframe check - only post tweets done in the past 24hrs
                        # example time string
                        # 'Tue May 03 16:49:30 +0000 2022'
                        tweet_date = datetime.strptime(tweet['date'], "%a %b %d %H:%M:%S %z %Y")
                        if (datetime.now(timezone.utc) - tweet_date).seconds > (24*60*60):
                            continue
 
                        for guild in iglob(ut.full_path(self.rel_path, self.twitter_cf['guilds'], '*.json')):
                            with open(guild) as f:
                                gp = json.load(f)
                            
                            glp = gp['services'].get(id, tem.fetch('tw_guild_lis'))

                            if glp['active']:
                                guild = self.client.get_guild(int(guild.split('\\')[-1].split('.')[0]))
                                channel = guild.get_channel(int(glp['channel']))
                                if channel:
                                    await self.send_tw_embeds(embeds, links, channel, base_link + str(tweet['tweet_id']), quoted, quoted_link)
                    
                with open(ut.full_path(self.rel_path, self.twitter_cf['caches'], cln), 'w+') as f:
                    f.write(json.dumps(cl,indent=4))
                
            elif not payload['status'] in [401,404] :
                await self.logger.report('return code', payload["status"], payload, f"```{acc}```")
    
    def cog_unload(self):
        self.listener.cancel()
    
    @listener.before_loop
    async def before_listener(self):
        print(self.name, "Awaiting client...", end="")
        await self.client.wait_until_ready()
        print("started")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
           
        # load gp
        try:
            with open(ut.full_path(self.rel_path,self.twitter_cf['guilds'],f"{message.guild.id}.json")) as f:
                gp = json.load(f)
        except:
            return
        
        if gp['convert']:
            # parse twit link
            match = self.t.search(message.content.strip())

            if match:
                # fetch
                try:
                    params = {
                        "cmd":      "twit.fetch.id",
                        "query":    match.groupdict()['tweet_id']
                    }
                    result = requests.get(self.api, params=params)
                    payload = json.load(BytesIO(result.content))
                except Exception as e:
                    await self.logger.report(self.name, e)
                    await self.logger.report(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
                    return
                
                if payload['status'] == 200:
                    embeds, links = self.make_twitter_embeds(payload['result']['user'], payload['result']['tweet'], message.author)
                    
                    # check quoted status
                    quoted = payload['result']['tweet'].get('quoted_status', None)
                    quoted_link = None
                    if quoted:
                        quoted_link = f"https://twitter.com/{quoted['user']['screen_name']}/status/{quoted['tweet']['tweet_id']}"
                        quoted = self.make_twitter_embeds(quoted['user'], quoted['tweet'], message.author)

                    await message.delete()
                    await self.send_tw_embeds(embeds, links, message.channel, match.group(), quoted, quoted_link)
        
        # pixiv addition
        match1 = self.p1.search(message.content.strip())
        match2 = self.p2.search(message.content.strip())
        if match1 or match2:
            if match2:
                match = match2
            else:
                match = match1

            try:
                params = {
                    "cmd": "pixiv.get.illust",
                    "query": match.groupdict()['Illust_ID']
                }
                result = requests.get(self.api, params=params)
                payload = json.load(BytesIO(result.content))

            except Exception as e:
                await self.logger.report(self.name, e)
                await self.logger.report(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
                return

            if payload['Status'] == 200:
                await message.delete()
                parent, children = self.make_pixiv_embeds(payload['Result'], message.content.strip(), message.author)

                main = await message.channel.send(f"<{message.content.strip()}>", embed=parent[0], file=parent[1])
                for child in children:
                    await main.reply(embed=child[0], file=child[1])
            
    def make_pixiv_embeds(self, payload, link, author):
        TAG = "[{}](https://www.pixiv.net/en/tags/{}/artworks)"

        parent = {
            "title": payload['Data']['title'],
            'url': link,
            'descr': self.construct_tweet_text(payload['Data']['caption']),
            'author': {'text': payload['User']['name']},
            'image': "attachment://temp.png", #self.stream_image(payload['Illust'][0]['original']),
            'footer': {
                'text': f"Pixiv | sent by {author.name}",
                'url': author.avatar.url
            },
            'fields': [
                {
                    'name': '> Tags',
                    'value': ', '.join([TAG.format(item['altname'] if item['altname'] else item['tag_name'], item['tag_name']) for item in payload['Tags']])
                }
            ]
        }

        children = []
        for i, child in enumerate(payload['Illust'][1:6]):
            children.append(
                (self.make_pixiv_child(len(payload['Illust']), i+2, child, link), self.stream_image(child['original']))
            )
        
        return (ut.embed_contructor(**parent), self.stream_image(payload['Illust'][0]['original'])), children

    def stream_image(self, url):
        HEADERS = {'referer': 'https://www.pixiv.net/'}

        #return Image.open(BytesIO(requests.get(url, headers=HEADERS).content))
        return File(BytesIO(requests.get(url, headers=HEADERS).content), filename='temp.png')

    def make_pixiv_child(self, total, i, url, link):
        embed = {
            'title': f"Image {i} of {total}",
            'url': link,
            'image': "attachment://temp.png", #self.stream_image(url)
            'footer': {'text':'Pixiv'}
        }
        return ut.embed_contructor(**embed)

    #@twitter.command()
    #async def test(self, ctx):
    #    if not self.client.check_perm(ctx.author):
    #        return
    #    await self.func_listener()