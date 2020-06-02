# main for making gacha embeds and results

import os, sys
import discord
from discord.ext import commands
import random, datetime, json
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
#dir = os.path.dirname(__file__)

#from cog_hatsune import hatsuneCog

SPACE = '\u200B'

class gachaCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.logger =   client.log
        self.name =     '[gacha]'
        self.colour =   discord.Colour.from_rgb(*client.config['command_colour']['cog_gacha'])

        with open(os.path.join(client.dir, client.config['gacha_config_path'])) as gcf:
            config = json.load(gcf)
        
        # laod
        self.roll_limit =   100000
        self.pool =         self.pool(self, client, config)

        # cog
        #self.hatsune = hatsuneCog(client)
    
    class character:
        def __init__(self, client, name, rarity, limited=False):
            self.name =         name.lower()
            self.full_name =    client.get_full_name(name)
            self.rarity =       rarity
            self.limited =      limited
        
        def __eq__(self, c):
            return self.name == c
    
    class pool:
        def __init__(self, cog, client, config, grain=100000):
            self.cog =      cog
            self.client =   client
            self.grain =    grain
            self.config =   config
            self.prifes =   True if config['prifes'] == 1 else False
            
            # normal rates
            self.rate_ssr = config['ssr_rate']
            self.rate_sr =  config['sr_rate']
            if self.prifes:
                self.rate_ssr *= 2
            self.rate_r = 1 - self.rate_ssr - self.rate_sr

            # rate ups
            self.up_ssr =   config['ssr_rate_up']
            self.up_sr =    config['sr_rate_up']
            self.up_r =     config['r_rate_up']
            if self.prifes:
                self.up_ssr *= 2
            
            # finish init
            self.threshold()
            self.load_pools()
        
        def threshold(self):
            self.sr_threshold =         round(self.grain * self.rate_r)
            self.ssr_threshold =        round(self.grain * self.rate_sr + self.sr_threshold)

            self.up_r_threshold =       round(self.grain * self.up_r)
            self.up_sr_threshhold =     round(self.grain * self.up_sr + self.sr_threshold)
            self.up_ssr_threshhold =    round(self.grain * self.up_ssr + self.ssr_threshold)
        
        def load_pools(self):
            self.ssr_pool =     {'norm':[], 'lim':[]}
            self.sr_pool =      {'norm':[], 'lim':[]}
            self.r_pool =       {'norm':[], 'lim':[]}

            # read rate ups
            for name in self.config['pools']['lim']:
                if name.startswith("1"):
                    self.r_pool['lim'].append(self.cog.character(self.client, name[1:], 1, limited=True))
                elif name.startswith("2"):
                    self.sr_pool['lim'].append(self.cog.character(self.client, name[1:], 2, limited=True))
                elif name.startswith("3"):
                    self.ssr_pool['lim'].append(self.cog.character(self.client, name[1:], 3, limited=True))
            
            # ssr pool
            for name in self.config['pools']['ssr']:
                if name.lower() not in self.ssr_pool['lim']:
                    self.ssr_pool['norm'].append(self.cog.character(self.client, name, 3))
            
            # sr pool
            for name in self.config['pools']['sr']:
                if name.lower() not in self.sr_pool['lim']:
                    self.sr_pool['norm'].append(self.cog.character(self.client, name, 2))

            # r pool
            for name in self.config['pools']['r']:
                if name.lower() not in self.r_pool['lim']:
                    self.r_pool['norm'].append(self.cog.character(self.client, name, 1))
        
        def roll(self, tenth=False, test=False):
            if not test:
                seed = random.randint(0,self.grain)
            else:
                seed = random.randint(self.ssr_threshold,self.grain)

            if seed < self.sr_threshold and not tenth and not test:
                if seed < self.up_r_threshold and len(self.r_pool['lim']) != 0:
                    return random.choice(self.r_pool['lim'])
                else:
                    return random.choice(self.r_pool['norm'])

            elif seed < self.ssr_threshold and not test:
                if seed < self.up_sr_threshhold and len(self.sr_pool['lim']) != 0:
                    return random.choice(self.sr_pool['lim'])
                else:
                    return random.choice(self.sr_pool['norm'])
            
            else:
                if seed < self.up_ssr_threshhold and len(self.ssr_pool['lim']) != 0:
                    return random.choice(self.ssr_pool['lim'])
                else:
                    return random.choice(self.ssr_pool['norm'])
                      
        def spark(self, num, mode=None):
            summary = {
                        'lim':      dict(),
                        'norm':     dict(),
                        'ssr':      0,
                        'sr':       0,
                        'r':        0,   
                        }

            for i in range(1,num+1):
                ch = self.roll(i%10==0)
                if ch.rarity == 1:
                    summary['r'] += 1
                elif ch.rarity == 2:
                    summary['sr'] += 1
                elif ch.rarity == 3 and not ch.limited:
                    summary['norm'][ch.name] = [ch, summary['norm'].get(ch.name,[ch, 0])[1] + 1]
                    summary['ssr'] += 1
                else:
                    summary['lim'][ch.name] = [ch, summary['lim'].get(ch.name,[ch, 0])[1] + 1]
                    summary['ssr'] += 1

                    if mode == 'spark':
                        break
                    elif ch.name == mode:
                        break
            
            summary['rolls'] = i
            summary['frags'] = summary['ssr']*50 + summary['sr']*10 + summary['r']
            return summary

    def roll_check(self, roll:int):
        return roll > 0 and roll <= self.roll_limit

    @commands.command(
        usage='.roll [num=10]',
        help='Have Ames simulate your gacha luck on the current banner. [num] cannot be too big.'
    )
    async def roll(self, ctx, *roll):
        channel = ctx.channel
        author = ctx.message.author

        if not self.client.command_status['roll'] == 1:
            raise commands.DisabledCommand

        # check if input is valid
        if len(roll) != 0:
            try:
                roll = int(roll[0])
            except:
                await channel.send(self.client.emotes['ames'])
                return
            else:
                if not self.roll_check(roll):
                    await channel.send(self.client.emotes['ames'])
        else:
            roll = 10
        
        summary = self.pool.spark(roll)
        await channel.send(embed=self.embed_gacha_summary(author, roll, summary, 'roll'))

    def embed_gacha_summary(self, author, roll, summary, mode):
        # mode
        if mode == 'roll':
            desc = f"「ステキなナカマですね、{author.name}！」" if summary['ssr'] == 0 else f"「おめでとうございます、{author.name}！」"

        elif mode == 'spark':
            desc = f"{author.name}, you managed to pull **{list(summary['lim'].values())[0][0].full_name}** in **{summary['rolls']}** pulls." if summary['rolls'] < roll else\
                        f"{author.name}, you did not manage to pull any rate up(s) within {summary['rolls']} rolls."
        
        else:
            desc = f"{author.name}, you managed to pull **{list(summary['lim'].values())[-1][0].full_name}** in **{summary['rolls']}** pulls." if summary['rolls'] < roll else\
                        f"{author.name}, you did not manage to pull {self.pool.ssr_pool['lim'][[chara.name for chara in self.pool.ssr_pool['lim']].index(mode)].full_name} within {summary['rolls']} rolls."

        embed = discord.Embed(
            title="カレンのガチャ報道",
            description=desc,
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Recruitment | Re:Re:Write Ames",icon_url=self.client.user.avatar_url)

        embed.add_field(
            name="Total pulls",
            value=f"{summary['rolls']}" if summary['rolls'] != 300 else f"300 (Spark)",
            inline=True
        )
        embed.add_field(
            name="Total P. Tears",
            value=f"**{summary['frags']}**",
            inline=True
        )
        embed.add_field(
            name=f"{self.client.emotes['yems']} Spent",
            value=f"{summary['rolls']*150:,d} (¥{(summary['rolls']/10*2000):,.2f})",
            inline=True
        )
        embed.add_field(
            name="R Tier",
            value=f"{summary['r']} ({(summary['r']/summary['rolls']*100):.2f}%)",
            inline=True
        )
        embed.add_field(
            name="SR Tier",
            value=f"{summary['sr']} ({(summary['sr']/summary['rolls']*100):.2f}%)",
            inline=True
        )
        embed.add_field(
            name="SSR Tier",
            value=f"{summary['ssr']} ({(summary['ssr']/summary['rolls']*100):.2f}%)",
            inline=True
        )

        if len(summary['lim']) > 0:
            lim_pulls = list(summary['lim'].values())
            lim_pulls.sort(key=lambda x: x[0].full_name)
            lim_pulls = [f"> {self.client.team[ch.name]} **{ch.full_name}** x{n}" for ch, n in lim_pulls]
        else:
            lim_pulls = []

        if len(summary['norm']) > 0:
            ssr_pulls = list(summary['norm'].values())
            ssr_pulls.sort(key=lambda x: x[0].full_name)
            ssr_pulls = [f" {self.client.team[ch.name]} {ch.full_name} x{n}" for ch, n in ssr_pulls]
        else:
            ssr_pulls = []
        
        total_pulls = lim_pulls + ssr_pulls
        if len(total_pulls) == 0:
            total_pulls = [':put_litter_in_its_place:']

        for chunk in self.client.chunks(total_pulls, 10):
            embed.add_field(
                name="SSR Rolled",
                value="\n".join(chunk),
                inline=True
            )
        return embed

    @commands.command(
        usage='.spark [limit=300]',
        help='Have Ames test your luck to get the rate up in this current banner. [limit] cannot be greater than 300 for obvious reasons.'
    )
    async def spark(self, ctx, *request):
        # let limit be either (chara=lim_pool, limit=300), (chara, limit=300) or (chara, limit)
        channel = ctx.channel
        author = ctx.message.author
        if not self.client.command_status['spark'] == 1:
            raise commands.DisabledCommand
        
        # checks
        if (len(self.pool.ssr_pool['lim'])) == 0:
            await channel.send('There\'s nothing to spark! '+self.client.emotes['ames']+" (empty limited pool)")
            return
        
        limit = None
        mode = None
        for temp in request:
            # see if input is a number
            if limit == None:
                try:
                    limit = int(temp)
                except:
                    limit = None
                else:
                    if limit > 300 or limit < 0:
                        await channel.send(self.client.emotes['amesyan'])
                        return
                    continue
            # see if input is a chara
            if mode == None:
                try:
                    from cog_hatsune import hatsuneCog
                    hatsune = hatsuneCog(self.client)
                    x, mode, x = await hatsune.process_request(ctx, [temp], None, False)
                    del x
                except:
                    mode = None
                else:
                    if not mode in [chara.name for chara in self.pool.ssr_pool['lim']]:
                        await channel.send("This character cannot be sparked")
                        return
            del hatsune
                    

        limit = 300 if limit == None else limit
        mode = "spark" if mode == None else mode
        
        summary = self.pool.spark(limit, mode)
        await channel.send(embed=self.embed_gacha_summary(author, limit, summary, mode))

    @commands.command(
        usage='.gacha [num=10]',
        help='Have Ames do a 10 roll. This command is resource intensive (data warning: image <=200kB). [num] must be an integer between 1 and 10.'
    )
    async def gacha(self, ctx, num=10, *test):
        channel = ctx.channel
        author = ctx.message.author
        if not self.client.command_status['gacha'] == 1:
            raise commands.DisabledCommand
        
        if num < 1 or num > 10:
            await channel.send(self.client.emotes['amesyan'])
            return
        
        # read input
        if len(test) != 0:
            if test[0] == 'test':
                test = True
            else:
                test = False
        
        # roll
        rolls = [self.pool.roll(i==10,test) for i in range(1,num+1)]
        async with ctx.typing():
            self.make_gacha(rolls)
            result = discord.File(os.path.join(self.client.dir,self.client.config['post_path'],"gresult.jpg"), filename="gresult.jpg")
            embed = discord.Embed(
                colour =        self.colour,
                timestamp=      datetime.datetime.utcnow()
            )
            embed.set_author(name=f"{author.name} rolled:",icon_url=author.avatar_url)
            embed.set_footer(text='Gacha | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
            embed.set_image(url="attachment://gresult.jpg")
        await channel.send(embed=embed,file=result)
    
    def make_gacha(self, rolls):
        gacha =     Image.open(os.path.join(self.client.dir, self.client.config['shen_path'],'gacha/gbg2.jpg'))
        rare =      Image.open(os.path.join(self.client.dir, self.client.config['shen_path'],'gacha/r2_.png'))
        srare =     Image.open(os.path.join(self.client.dir, self.client.config['shen_path'],'gacha/sr2_.png'))
        ssrare =    Image.open(os.path.join(self.client.dir, self.client.config['shen_path'],'gacha/ssr2_.png'))
        new =       Image.open(os.path.join(self.client.dir, self.client.config['shen_path'],'gacha/new_.png'))
        #none =      Image.open(os.path.join(dir,'gacha/assets/units/png/_NONE.png'))

        rarity_bg = {'1':rare, '2':srare, '3':ssrare}

        # sizes
        row1 = 80
        row2 = 330
        spacing = 197

        #rs = Image.ANTIALIAS
        #gscalef = 0.7
        #gsizef =  (round(gacha.size[0]*gscalef), round(gacha.size[1]*gscalef))
        pxstart = 190
        cxstart = 215
        cos = 72
        #nos = -25

        for i, chara in enumerate(rolls):
            pf = Image.open(os.path.join(self.client.dir,self.client.config['png_path'],f"{chara.name}.png"))
            if i < 5:
                gacha.paste(rarity_bg[str(chara.rarity)], (pxstart + i*spacing, row1), rarity_bg[str(chara.rarity)])
                gacha.paste(pf, (cxstart + i*spacing, row1 + cos), pf)
                if chara.limited:
                    gacha.paste(new, (pxstart - 25 + i*spacing, row1 - 25), new)
            else:
                j = i - 5
                gacha.paste(rarity_bg[str(chara.rarity)], (pxstart + j*spacing, row2), rarity_bg[str(chara.rarity)])
                gacha.paste(pf, (cxstart + j*spacing, row2 + cos), pf)
                if chara.limited:
                    gacha.paste(new, (pxstart - 25 + j*spacing, row2 - 25), new)
            pf.close()
        
        #gacha = gacha.resize(gsizef, resample=rs)
        gacha.save(os.path.join(self.client.dir,self.client.config['post_path'],'gresult.jpg'))

        # shutdown
        gacha.close()
        rare.close()
        srare.close()
        ssrare.close()
        new.close()
        #none.close()  

    @commands.command()
    async def banner(self, ctx):
        channel = ctx.channel
        embed = discord.Embed(
            title="Pool statistics",
            description="Current pool condition",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Pool | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="PriFes",
            value="Active" if self.pool.prifes else "Inactive",
            inline=False
        )
        embed.add_field(
            name="SSR Rate(rateup)",
            value=f"{self.pool.rate_ssr*100}% ({self.pool.up_ssr*100}%)"
        )
        embed.add_field(
            name="SR Rate(rateup)",
            value=f"{self.pool.rate_sr*100}% ({self.pool.up_sr*100}%)"
        )
        embed.add_field(
            name="R Rate(rateup)",
            value=f"{self.pool.rate_r*100}% ({self.pool.up_r*100}%)"
        )
        pools = [
            ("SSR", self.pool.ssr_pool['lim']),
            ("SR", self.pool.sr_pool['lim']), 
            ("R", self.pool.r_pool['lim'])
        ]
        for rarity, pool in pools:
            temp = set([f"{self.client.team[chara.name]} {chara.full_name}" for chara in pool])
            embed.add_field(
                name=f"{rarity} Limited Pool",
                value="\n".join(temp) if len(temp) != 0 else "Empty",
                inline=True
            )
        await channel.send(embed=embed)

def setup(client):
    client.add_cog(gachaCog(client))