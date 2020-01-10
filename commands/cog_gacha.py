import os, sys
import discord
from discord.ext import commands
import random, datetime
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
dir = os.path.dirname(__file__)

SPACE = '\u200B'
PRIFES = False

def get_full_name(target):
    if target[1].isupper():
        prefix = target[0].lower()
        if prefix ==    'n': 
            prefix =        'New Year'
        elif prefix ==  'x':
            prefix =        'Xmas'
        elif prefix ==  'o':
            prefix =        'Ouedo'
        elif prefix ==  'v':
            prefix =        'Valentine'
        elif prefix ==  's':
            prefix =        'Summer'
        elif prefix ==  'h':
            prefix =       'Halloween'
        elif prefix ==  'u':
            prefix = '      Uniform'
        else:
            prefix =        "???"
        return " ".join([prefix, target[1:]])
    else:
        return target

class chara:
    def __init__(self, name, rarity, limited=False):
        self.full_name =    get_full_name(name)
        self.name =         name.lower()
        self.rarity =       rarity
        self.limited =      limited
    
    def __eq__(self, c):
        return self.name == c

class pool:
    def __init__(self, grain=1000000):
        self.grain =    grain

        # normal rates
        self.rate_ssr = 0.025
        if PRIFES:
            self.rate_ssr = self.rate_ssr * 2
        self.rate_sr =  0.18
        self.rate_r =   1 - self.rate_ssr - self.rate_sr

        # rate ups
        self.up_ssr =   0.008
        if PRIFES:
            self.up_ssr = self.up_ssr * 2
        self.up_sr =    0
        self.up_r =     0

        self.load_pools()
        self.threshold()
    
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
        with open(os.path.join(dir,'gacha/_lim.txt')) as gf:
            for name in gf.read().splitlines():
                if name[0] == 1:
                    self.r_pool['lim'].append(chara(name[1:], 1, limited=True))
                elif name[0] == 2:
                    self.sr_pool['lim'].append(chara(name[1:], 2, limited=True))
                else:
                    self.ssr_pool['lim'].append(chara(name[1:], 3, limited=True))
        
        # ssr pool
        with open(os.path.join(dir,'gacha/ssr.txt')) as gf:
            for name in gf.read().splitlines():
                if name.lower() not in self.ssr_pool['lim']:
                    self.ssr_pool['norm'].append(chara(name, 3))
        
        # sr pool
        with open(os.path.join(dir,'gacha/sr.txt')) as gf:
            for name in gf.read().splitlines():
                if name.lower() not in self.sr_pool['lim']:
                    self.sr_pool['norm'].append(chara(name, 2))

        # r pool
        with open(os.path.join(dir,'gacha/r.txt')) as gf:
            for name in gf.read().splitlines():
                if name.lower() not in self.r_pool['lim']:
                    self.r_pool['norm'].append(chara(name, 1))
    
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
        
        summary['rolls'] = i
        summary['frags'] = summary['ssr']*50 + summary['sr']*10 + summary['r']
        return summary

class gachaCog(commands.Cog):
    def __init__(self, client):
        self.name = '[gacha]'
        self.logger = client.log
        self.client = client
        #self.active = client.get_config('gacha')
        self.roll_limit = 100000
        self.pool = pool()

    def chunks(self, l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n] 
    
    async def active_check(self, channel):
        if self.client.get_config('gacha') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    def roll_check(self, roll):
        return roll < 0 or roll > self.roll_limit
    
    @commands.command(
        usage='.roll [num=10]',
        help='Have Ames simulate your gacha luck on the current banner.'
    )
    async def roll(self, ctx, *roll):
        channel = ctx.channel
        author = ctx.message.author
        check = await self.active_check(channel)
        if not check:
            return
        
        if len(roll) != 0:
            try:
                roll = int(roll[0])
            except:
                await channel.send('Please enter in a valid input')
                return
            else:
                if self.roll_check(roll):
                    await channel.send(self.client.emj['ames'])
                    return 
        else:
            roll = 10
        
        summary = self.pool.spark(roll)

        embed = discord.Embed(
            title="Spark Summary" if roll == 300 else "Roll Summary",
            description=f"Feeling lucky, {author.name}?",
            timestamp=datetime.datetime.utcnow()
        )
        #embed.set_author(icon_url=author.avatar_url)
        embed.set_footer(text="Roll | SHIN Ames",icon_url=self.client.user.avatar_url)

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
            name=f"{self.client.emj['yems']} Spent",
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
            lim_pulls.sort(key=lambda x: x[0].name)
            lim_pulls = [f"> {self.client.get_team()[ch.name]} **{ch.full_name}** x{n}" for ch, n in lim_pulls]
        else:
            lim_pulls = []

        if len(summary['norm']) > 0:
            ssr_pulls = list(summary['norm'].values())
            ssr_pulls.sort(key=lambda x: x[0].name)
            ssr_pulls = [f" {self.client.get_team()[ch.name]} {ch.full_name} x{n}" for ch, n in ssr_pulls]
        else:
            ssr_pulls = []
        
        total_pulls = lim_pulls + ssr_pulls
        if len(total_pulls) == 0:
            total_pulls = [':put_litter_in_its_place:']

        for chunk in self.chunks(total_pulls, 10):
            embed.add_field(
                name="SSR Rolled",
                value="\n".join(chunk),
                inline=True
            )
        await channel.send(embed=embed)

    @commands.command(
        usage='.spark [limit=300]',
        help='Have Ames test your luck to get the rate up in this current banner. [limit] cannot be greater than 300 for obvious reasons.'
    )
    async def spark(self, ctx, *limit):
        channel = ctx.channel
        author = ctx.message.author
        check = await self.active_check(channel)
        if not check:
            return
        
        if (len(self.pool.ssr_pool['lim'])) == 0:
            await channel.send('There\'s nothing to spark! '+self.client.emj['ames'])
            return
        
        if len(limit) == 0:
            limit = 300
        else:
            try:
                limit = int(limit[0])
            except:
                await channel.send(self.client.emj['ames'])
                return 
            else:
                if limit < 1 or limit > 300:
                    await channel.send(self.client.emj['ames'])
                    return
        
        summary = self.pool.spark(limit, 'spark')

        embed = discord.Embed(
            title="Spark Summary" if summary['rolls'] == 300 else "Roll Summary",
            description=f"{author.name}, you managed to pull **{list(summary['lim'].values())[0][0].full_name}** in **{summary['rolls']}** pulls." if summary['rolls'] < limit else
                        f"{author.name}, you did not manage to pull any rate up(s) within {summary['rolls']} rolls.",
            timestamp=datetime.datetime.utcnow()
        )
        #embed.set_author(icon_url=author.avatar_url)
        embed.set_footer(text="Spark | SHIN Ames",icon_url=self.client.user.avatar_url)

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
            name=f"{self.client.emj['yems']} Spent",
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
            lim_pulls.sort(key=lambda x: x[0].name)
            lim_pulls = [f"> {self.client.get_team()[ch.name]} **{ch.full_name}** x{n}" for ch, n in lim_pulls]
        else:
            lim_pulls = []

        if len(summary['norm']) > 0:
            ssr_pulls = list(summary['norm'].values())
            ssr_pulls.sort(key=lambda x: x[0].name)
            ssr_pulls = [f" {self.client.get_team()[ch.name]} {ch.full_name} x{n}" for ch, n in ssr_pulls]
        else:
            ssr_pulls = []
        
        total_pulls = lim_pulls + ssr_pulls
        if len(total_pulls) == 0:
            total_pulls = [':put_litter_in_its_place:']

        for chunk in self.chunks(total_pulls, 10):
            embed.add_field(
                name="SSR Rolled",
                value="\n".join(chunk),
                inline=True
            )
        await channel.send(embed=embed)

    @commands.command(
        usage='.gacha [num=10]',
        help='Have Ames do a 10 roll. This command is resource intensive.'
    )
    async def gacha(self, ctx, num=10, *test):
        #print(num,test)
        channel = ctx.channel
        author = ctx.message.author
        check = await self.active_check(channel)
        if not check:
            return

        if num < 1 or num > 10:
            await channel.send(self.client.emj['amesyan'])
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
            result = discord.File(os.path.join(dir,"gacha/gresult.jpg"), filename="gresult.jpg")
            embed = discord.Embed(
                timestamp=      datetime.datetime.utcnow()
            )
            embed.set_author(name=f"{author.name} rolled:",icon_url=author.avatar_url)
            embed.set_footer(text='Gacha | SHIN Ames',icon_url=self.client.user.avatar_url)
            embed.set_image(url="attachment://gresult.jpg")
        await channel.send(embed=embed,file=result)

    def make_gacha(self, rolls):
        gacha =     Image.open(os.path.join(dir,'gacha/assets/gbg2.jpg'))
        rare =      Image.open(os.path.join(dir,'gacha/assets/r2_.png'))
        srare =     Image.open(os.path.join(dir,'gacha/assets/sr2_.png'))
        ssrare =    Image.open(os.path.join(dir,'gacha/assets/ssr2_.png'))
        new =       Image.open(os.path.join(dir,'gacha/assets/new_.png'))
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
            pf = Image.open(os.path.join(dir,f"gacha/assets/units/png/{chara.name}.png"))
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
        gacha.save(os.path.join(dir,'gacha/gresult.jpg'))

        # shutdown
        gacha.close()
        rare.close()
        srare.close()
        ssrare.close()
        new.close()
        #none.close()   

def setup(client):
    client.add_cog(gachaCog(client))