import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests, asyncio
from io import BytesIO
SPACE = '\u200B'

from cog_pupdate import validate_request

def setup(client):
    client.add_cog(hatsuneCog(client))

class hatsuneCog(commands.Cog):
    def __init__(self, client):
        self.client = client 
        self.name = '[prototype-hatsune]'
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_hatsune'])
        self.logger = client.log

        # load configs
        with open(os.path.join(self.client.dir, self.client.config['hatsune_config_path']),encoding='utf-8') as hcf:
            self.config = json.load(hcf)
        with open(os.path.join(self.client.dir, self.client.config['tags_index_path'])) as tif:
            self.tag_definitions = json.load(tif)
        with open(os.path.join(self.client.dir, self.client.config['alias_local_path'])) as alf:
            self.alocal = json.load(alf)
        #with open(os.path.join(self.client.dir, self.client.config['unit_list_path'])) as ulf:
        #    self.unit_list = json.load(ulf)

        self.full_alias = self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)
    
    @commands.command(aliases=['c','ue','chara', 'card', 'pic', 'stats', 'profile'])
    async def character(self, ctx, *request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client.command_status['chara']:
            raise commands.DisabledCommand
        elif not request:
            await channel.send("No input detected. Use `.c help` or `.help character` if you need help "+self.client.emotes['ames'])
            return

        # standardise
        request = [item.lower() for item in request]
        if "help" in request:
            await channel.send(embed=self.make_character_help())
            return
        elif "stats" in request:
            await channel.send(embed=self.make_stats_help())
            return

        # preprocess
        match, alts, mode, invoke = await self.preprocess(ctx, request, invoke=ctx.invoked_with, verbose=True)

        if not match:
            await channel.send(f"Failed to find `{' '.join(request)}`. Use `.c help` or `.help character` if you're stuck "+self.client.emotes['ames'])
            return
        
        #await channel.send("[Experimental Ames] This is currently a highly experimental version of `.character` and may be very unstable. Stable Ames will be up and running soon:tm:")
        if not match['flb'] and mode == "flb":
            await channel.send(f"Note: {self.client.get_full_name_kai(match['name_en'],match['prefix'])} does not have a `flb` variant")
            mode = None

        # load data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data  = json.load(dbf)

        # make alts
        all_charas = [match] + alts

        alt_data = [all_data['units'][m['index']] for m in all_charas]
        alt_emotes = [self.client.team[m['sname']] for m in all_charas]
        alt_embeds = [self.character_page_controller(self, d, invoke, flb=mode=="flb") for d in alt_data]

        alt_choice = 0
        fe, reactions = alt_embeds[alt_choice].start()
        page = await channel.send(embed=fe)
        for e in list(reactions.keys())+alt_emotes if len(alt_emotes) > 1 else list(reactions.keys()):
            await page.add_reaction(e)

        def author_check(reaction, user):
            return str(user.id) == str(author.id) and str(reaction.emoji) in list(reactions.keys())+alt_emotes and str(reaction.message.id) == str(page.id)
        
        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=70.0, check=author_check)
            except asyncio.TimeoutError:
                await page.add_reaction(alt_embeds[0].stop)
                return
            else:
                if str(reaction.emoji) in list(reactions.keys())+alt_emotes:
                    await reaction.message.remove_reaction(reaction.emoji, user)

                    if str(reaction.emoji) in alt_emotes:
                        new_choice = alt_emotes.index(str(reaction.emoji))

                        if new_choice != alt_choice:
                            alt_choice = new_choice

                            # find diff in base emotes
                            diff = list(set(reactions) - set(list(alt_embeds[alt_choice].base_emotes.keys())))

                            if diff:
                                # unreact the alts
                                for e in alt_emotes:
                                    await page.remove_reaction(e, self.client.user)

                                for e in diff:
                                    if not e in reactions:
                                        await page.add_reaction(e)
                                    else:
                                        await page.remove_reaction(e, self.client.user)
                                
                                # readd the alts
                                for e in alt_emotes:
                                    await page.add_reaction(e)
                            
                            reactions = list(alt_embeds[alt_choice].base_emotes.keys())

                    else:
                        alt_embeds[alt_choice].set(reactions[str(reaction.emoji)])
                    
                    await page.edit(embed=alt_embeds[alt_choice].reload())

    async def preprocess(self, ctx, request, **kwargs):
        verbose = kwargs.get('verbose', False)
        invoke = kwargs.get('invoke', None)

        # check invoke
        if invoke:
            if invoke in        ['ue']:
                invoke =    "ue"
            elif invoke in      ['card', 'pic']:
                invoke =    "card"
            elif invoke in      ['stats']:
                invoke =    "stats"
            elif invoke in      ['profile']:
                invoke =    "profile"
            else:
                invoke =    "chara"
        
        # check mode
        mode = request[-1]
        if mode in ['flb', 'ue']:
            if mode in ['ue']:
                if verbose: await ctx.message.channel.send("`ue` option is depreciated. Use `.ue [character]` instead.")
                mode = None
                invoke = "ue"
            elif mode == "flb":
                mode = "flb"
                request = request[:-1]
            
        else:
            mode = None
        
        # check alias
        prefix, _, name = "".join(request).partition(".")
        prefix, name = prefix.strip(), name.strip()

        if not name:
            name = prefix
            prefix = None

        name = self.full_alias.get(name, name)
        prefix = self.full_alias.get(prefix, prefix) if prefix else None

        # validate
        match, alts = validate_request(self.client, {"name":name,"prefix":prefix})

        # warn
        if match:
            if not prefix and match['prefix'] and verbose:
                await ctx.message.channel.send(f"Searching syntax `{name}` is discouraged. Consider searching via `{match['prefix']}.{match['name_en']}` syntax next time "+self.client.emotes['ames'])

        return match, alts, mode, invoke

    def get_attack_pattern(self, info):
        if "magic" in info['tags']:
            norm_atk = '<:magatk:713288155469578272>'
        else:
            norm_atk = '<:_chara:677763373739409436>'
        skills = [
            '1\u20E3',
            '2\u20E3'
        ]
        opening = info['atkptn']['ptn'][:info['atkptn']['loop'][0]-1]
        loop = info['atkptn']['ptn'][info['atkptn']['loop'][0]-1:]

        opening = "-".join([norm_atk if action == 1 else skills[action%10-1] for action in opening]) if len(opening) != 0 else "None"
        loop = "-".join([norm_atk if action == 1 else skills[action%10-1] for action in loop]) if len(loop) != 0 else "None"
        return "\n".join(
            [opening, loop]
        )

    def make_chara_embed(self, data, sections, **kwargs):
        flb = kwargs.get("flb", False)
        alt = kwargs.get("alt", False)
        # norm      ->  ub      | sk1       | sk1p        | sk2       | ex | ex2
        # alt       ->  ub      |(sk1) sk1a |(sk1p) sk1ap |(sk2) sk2a | ex | ex2
        # flb       ->      ub2 |           | sk1p        | sk2       |    | ex2
        # flb+alt   ->      ub2 |           |(sk1p) sk1ap |(sk2) sk2a |    | ex2

        # make sections
        sections[sections.index("<:_chara:677763373739409436> Chara")] = "<:_chara:677763373739409436> **[Chara]**"

        # make title
        if flb and alt:
            title = f"{data['basic']['jp']['name']} 6\⭐\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} FLB (Special Mode)"
        elif flb:
            title = f"{data['basic']['jp']['name']} 6\⭐\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} FLB"
        elif alt:
            title = f"{data['basic']['jp']['name']}\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} (Special Mode)"
        else:
            title = f"{data['basic']['jp']['name']}\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}"
        
        embed = discord.Embed(
            title=title,
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=data['img6'] if flb else data['img'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Info Page | Ames Re:Re:Write',icon_url=data['img6'] if flb else data['img'])

        # section
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )

        # basic
        embed.add_field(
            name="> **Attacker Type**",
            value="Magic Attacker" if "magic" in data['tags'] else "Physical Attacker"
        )
        if 'mid' in data['tags']:
            p = "Midguard"
        elif 'front' in data['tags']:
            p = "Vanguard"
        else:
            p = "Rearguard"
        embed.add_field(
            name="> **Position**",
            value=p,
            inline=False
        )
        embed.add_field(
            name="> **Attack Pattern**",
            value="Initial:\nLooping:",
            inline=True
        )
        embed.add_field(
            name=SPACE,
            value=self.get_attack_pattern(data),
            inline=True
        )

        # ub, ub2
        test = not flb or not (flb and alt)
        embed.add_field(
            name=   "> **Union Burst**" if test else "> **Union Burst+**",
            value=  f"「{data['basic']['jp']['ub']['name']}」" if test else 
                    f"「{data['basic']['jp']['ub2']['name']}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{data['basic']['jp']['ub']['text']}" if test else 
                    f"{data['basic']['jp']['ub2']['text']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  f"{data['basic']['en']['ub']['text']}" if test else 
                    f"{data['basic']['en']['ub2']['text']}",
            inline= True
        )

        # sk1, sk1a
        if not flb:
            test = not alt or (alt and not data['basic']['jp']['sk1a']['text'])
            embed.add_field(
                name=   "> **Skill 1**" if test else "> **Skill 1 Special**",
                value=  f"「{data['basic']['jp']['sk1']['name']}」" if test else 
                        f"「{data['basic']['jp']['sk1a']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['sk1']['text']}" if test else 
                        f"{data['basic']['jp']['sk1a']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['sk1']['text']}" if test else 
                        f"{data['basic']['en']['sk1a']['text']}",
                inline= True
            )

        # sk1p, sk1ap
        if "ue" in data['tags']:
            test = (not alt) or (alt and not data['basic']['jp']['sk1ap']['text'])
            embed.add_field(
                name=   "> **Skill 1+**" if test else "> **Skill 1 Special+**",
                value=  f"「{data['basic']['jp']['sk1p']['name']}」" if test else 
                        f"「{data['basic']['jp']['sk1ap']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['sk1p']['text']}" if test else 
                        f"{data['basic']['jp']['sk1ap']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['sk1p']['text']}" if test else 
                        f"{data['basic']['en']['sk1ap']['text']}",
                inline= True
            )

        # sk2, sk2a
        test = not alt or (alt and not data['basic']['jp']['sk2a']['text'])
        embed.add_field(
            name=   "> **Skill 2**" if test else "> **Skill 2 Special**",
            value=  f"「{data['basic']['jp']['sk2']['name']}」" if test else 
                    f"「{data['basic']['jp']['sk2a']['name']}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{data['basic']['jp']['sk2']['text']}" if test else 
                    f"{data['basic']['jp']['sk2a']['text']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  f"{data['basic']['en']['sk2']['text']}" if test else 
                    f"{data['basic']['en']['sk2a']['text']}",
            inline= True
        )

        # ex
        test = not flb
        if test:
            embed.add_field(
                name=   "> **EX Skill**",
                value=  f"「{data['basic']['jp']['ex']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['ex']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['ex']['text']}",
                inline= True
            )
        
        # ex 2
        embed.add_field(
            name=   "> **EX Skill+**",
            value=  f"「{data['basic']['jp']['ex2']['name']}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{data['basic']['jp']['ex2']['text']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  f"{data['basic']['en']['ex2']['text']}",
            inline= True
        )

        # tags
        embed.add_field(
            name="Tags",
            value=", ".join(data['tags']) if data['tags'] else "No tags yet",
            inline=False
        )

        # aliases
        falias = [key for key, value in list(self.full_alias.items()) if value.lower() == data['sname'].lower()]
        embed.add_field(
            name="> Aliases",
            value=", ".join(falias) if len(falias)!= 0 else "None",
            inline=False
        )
        return embed

    def make_ue_embed(self, data, sections, **kwargs):
        alt = kwargs.get("alt", False)
        sections[sections.index("<:_ue:677763400713109504> UnqEq")] = "<:_ue:677763400713109504> **[UnqEq]**"

        embed = discord.Embed(
            title="No Data",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour)
        embed.set_footer(text='Unique Equipment Page | Ames Re:Re:Write',icon_url=data['img'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )

        # complete the section if chara actually have ue
        if 'ue' in data['tags']:
            embed.title=        f"{data['ue']['jp']['name']}\n{data['ue']['en']['name']}"
            embed.description=  f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}\'s unique equipment.\n{data['ue']['jp']['text']}"
            embed.set_thumbnail(url=data['ue']['img'])

            # RANK
            embed.add_field(
                name="> **Rank**",
                value=f"{data['ue']['rank']}",
                inline=False
            )
            embed.add_field(
                name="> **UE Stats**",
                value=f"Base/Max (lv{data['status']['ue']})",
                inline=False
            )

            # STATS
            for field, value in list(data['ue']['stats'].items()):
                if field in list(self.config['ue_abbrev'].keys()):
                    #print(info['ue'])
                    try:
                        final_val = round(float(value) + float(data['ue']['stats'][f"{field.lower()}_growth"]) * (data['status']['ue']-1))
                    except:
                        final_val = round(float(value) + float(data['ue']['stats'].get(f"{field}_growth",0)) * (data['status']['ue']-1))
                        if data['ue']['stats'].get(f"{field}_growth",0) == 0:
                            print(f"ue - {field} growth stat is 0 or not found: {data['sname']}")

                    embed.add_field(
                        name=self.config['ue_abbrev'][field],
                        value=f"{value}/{final_val}",
                        inline=True
                    )
            

            # Skill 1
            test = not alt or (alt and not data['basic']['jp']['sk1a']['text'])
            embed.add_field(
                name=   "> **Skill 1**" if test else "> **Skill 1 Special**",
                value=  f"「{data['basic']['jp']['sk1']['name']}」" if test 
                        else f"「{data['basic']['jp']['sk1a']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['sk1']['text']}" if test
                        else f"{data['basic']['jp']['sk1a']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['sk1']['text']}" if test 
                        else f"{data['basic']['en']['sk1a']['text']}",
                inline= True
            )
            
            # Skill 1 +
            test = not alt or (alt and not data['basic']['jp']['sk1ap']['text'])
            embed.add_field(
                name=   "> **Skill 1+**" if test else "> **Skill 1 Special+**",
                value=  f"「{data['basic']['jp']['sk1p']['name']}」" if test
                        else f"「{data['basic']['jp']['sk1ap']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['sk1p']['text']}" if test
                        else f"{data['basic']['jp']['sk1ap']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['sk1p']['text']}" if test
                        else f"{data['basic']['en']['sk1ap']['text']}",
                inline= True
            )
        else:
            embed.description=  f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} does not have an unique equipment."
            embed.set_thumbnail(url='https://redive.estertion.win/icon/equipment/999999.webp')
        
        return embed        

    def make_card_embed(self, data, sections, **kwargs):
        flb = kwargs.get("flb", False)

        sections[sections.index('<:_card:677763353069879306> Card')] = '<:_card:677763353069879306> **[Card]**'

        embed = discord.Embed(
            description=f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}'s card is currently unavailable {self.client.emotes['dead']}",
            title="Card unavailble",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=data['img'] if not flb else data['img6'])
        embed.set_footer(text='Unit Card Page | Ames Re:Re:Write',icon_url=data['img'] if not flb else data['img6'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )
        #print(info['hnote_id'], type(info['hnote_id']))
        if data['basic']['jp']['id']:
            embed.title = "Unit Card"
            if not flb:
                embed.description = f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}'s card."
                link = f"https://redive.estertion.win/card/full/{data['basic']['jp']['id']}31.webp"
            else:
                embed.description = f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}'s FLB (6\⭐) card."
                link = f"https://redive.estertion.win/card/full/{data['basic']['jp']['id']}61.webp"

            embed.set_image(url=link)
        
        return embed

    def make_stats_embed(self, data, sections, **kwargs):
        flb = kwargs.get("flb", False)
        alt = kwargs.get("alt", False)
        # norm      ->  ub      | sk1       | sk1p        | sk2       | ex | ex2
        # alt       ->  ub      |(sk1) sk1a |(sk1p) sk1ap |(sk2) sk2a | ex | ex2
        # flb       ->      ub2 |           | sk1p        | sk2       |    | ex2
        # flb+alt   ->      ub2 |           |(sk1p) sk1ap |(sk2) sk2a |    | ex2

        # make sections
        sections[sections.index("<:_chara:677763373739409436> Chara")] = "<:_chara:677763373739409436> **[Chara]**"

        # make title
        if flb and alt:
            title = f"{data['basic']['jp']['name']} 6\⭐\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} FLB (Special Mode)"
        elif flb:
            title = f"{data['basic']['jp']['name']} 6\⭐\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} FLB"
        elif alt:
            title = f"{data['basic']['jp']['name']}\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} (Special Mode)"
        else:
            title = f"{data['basic']['jp']['name']}\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}"
        
        embed = discord.Embed(
            title=title,
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=data['img6'] if flb else data['img'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Info Page | Ames Re:Re:Write',icon_url=data['img6'] if flb else data['img'])

        embed.description = f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}\'s skill and misc stats. All stats assumes **LV{data['status']['lvl']}** **RANK{data['status']['rk']}** with **MAX BOND** across all character variants. `Note: This page is a WIP and displayed stats may be inaccurate`"


        # section
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )

        # stats
        for chunk in self.client.chunks(list(data['stats']['normal'].items() if not flb else data['stats']['flb'].items()), 6):
            embed.add_field(
                name=f"Stats",
                value="\n".join([f"{self.config['ue_abbrev'].get(key, key.upper())}: {arg}" for key, arg in chunk])
            )

        # ub, ub2
        test = not flb or not (flb and alt)
        embed.add_field(
            name=   "> **Union Burst**" if test else "> **Union Burst+**",
            value=  f"「{data['basic']['jp']['ub']['name']}」" if test else 
                    f"「{data['basic']['jp']['ub2']['name']}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{data['basic']['en']['ub']['text']}" if test else 
                    f"{data['basic']['en']['ub2']['text']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['ub']['action'])) if test else 
                    "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['ub2']['action'])),
            inline= True
        )

        # sk1, sk1a
        if not flb:
            test = not alt or (alt and not data['basic']['jp']['sk1a']['text'])
            embed.add_field(
                name=   "> **Skill 1**" if test else "> **Skill 1 Special**",
                value=  f"「{data['basic']['jp']['sk1']['name']}」" if test else 
                        f"「{data['basic']['jp']['sk1a']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['en']['sk1']['text']}" if test else 
                        f"{data['basic']['en']['sk1a']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk1']['action'])) if test else 
                        "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk1a']['action'])),
                inline= True
            )

        # sk1p, sk1ap
        if "ue" in data['tags']:
            test = (not alt) or (alt and not data['basic']['jp']['sk1ap']['text'])
            embed.add_field(
                name=   "> **Skill 1+**" if test else "> **Skill 1 Special+**",
                value=  f"「{data['basic']['jp']['sk1p']['name']}」" if test else 
                        f"「{data['basic']['jp']['sk1ap']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['en']['sk1p']['text']}" if test else 
                        f"{data['basic']['en']['sk1ap']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk1p']['action'])) if test else 
                        "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk1ap']['action'])),
                inline= True
            )

        # sk2, sk2a
        test = not alt or (alt and not data['basic']['jp']['sk2a']['text'])
        embed.add_field(
            name=   "> **Skill 2**" if test else "> **Skill 2 Special**",
            value=  f"「{data['basic']['jp']['sk2']['name']}」" if test else 
                    f"「{data['basic']['jp']['sk2a']['name']}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{data['basic']['en']['sk2']['text']}" if test else 
                    f"{data['basic']['en']['sk2a']['text']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk2']['action'])) if test else 
                    "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk2a']['action'])),
            inline= True
        )

        # ex
        test = not flb
        if test:
            embed.add_field(
                name=   "> **EX Skill**",
                value=  f"「{data['basic']['jp']['ex']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['en']['ex']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['ex']['action'])),
                inline= True
            )
        
        # ex 2
        embed.add_field(
            name=   "> **EX Skill+**",
            value=  f"「{data['basic']['jp']['ex2']['name']}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{data['basic']['en']['ex2']['text']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['ex2']['action'])),
            inline= True
        )
        return embed

    def make_profile_embed(self, data, sections, **kwargs):
        sections[sections.index("<:_profile:718471302460997674> Profile")] = "<:_profile:718471302460997674> **[Profile]**"
        embed = discord.Embed(
            title="Character Profile",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Profile | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Section",
            value=" - ".join(sections),
            inline=False
        )
        embed.add_field(
            name="Comment",
            value=data['basic']['jp']['comment'],
            inline=False
        )
        embed.add_field(
            name="Voice Actress",
            value=data['profile']['jp']['va'],
            inline=True
        )

        embed.set_image(url=data['profile']['img'])
        embed.add_field(
            name=SPACE,
            value="> Ingame Profile",
            inline=False
        )
        embed.add_field(
            name="Name",
            value=f"{data['profile']['jp']['name']}({data['profile']['jp']['name_alt']})"
        )
        embed.add_field(
            name="Race",
            value=data['profile']['jp']['race']
        )
        embed.add_field(
            name="Guild",
            value=data['profile']['jp']['guild']
        )
        embed.add_field(
            name=SPACE,
            value="> IRL Profile",
            inline=False
        )
        embed.add_field(
            name="Name",
            value=data['profile']['jp']['irl_name']
        )
        embed.add_field(
            name="Age",
            value=f"||{data['profile']['age']}||"
        )
        embed.add_field(
            name="Birthday (mm/dd)",
            value=data['profile']['bd']
        )
        embed.add_field(
            name="Height (cm)",
            value=data['profile']['height']
        )
        embed.add_field(
            name="Bloodtype",
            value=data['profile']['blood']
        )
        embed.add_field(
            name="Weight (kg)",
            value=data['profile']['weight']
        )
        return embed

    class character_page_controller():
        def __init__(self, cog, data, first_page, **kwargs):
            self.flb = kwargs.get("flb", False)
            self.alt = kwargs.get("alt", False)
            
            self.cog = cog
            self.current_page = first_page
            self.sections = ["<:_chara:677763373739409436> Chara", "<:_ue:677763400713109504> UnqEq", "<:_card:677763353069879306> Card", "<:_stats:678081583995158538> Stats", "<:_profile:718471302460997674> Profile"]

            self.base_emotes = {
                "<:_chara:677763373739409436>":"chara", 
                "<:_ue:677763400713109504>":"ue",
                "<:_card:677763353069879306>":"card",
                "<:_stats:678081583995158538>":"stats",
                "<:_profile:718471302460997674>":"profile"
            }

            self.flb_emote =    {"⭐":"flb"}
            self.alt_emote =    {"\U0001F500":"alt"}
            self.stop =         "\U0001f6d1"

            self.make_pages(data)
        
        def make_pages(self, data):
            self.has_flb = "flb" in data['tags']
            if self.has_flb:
                self.base_emotes.update(self.flb_emote)

            self.has_alt = data['basic']['jp']['sk1a']['text'] or data['basic']['jp']['sk2a']['text']
            if self.has_alt:
                self.base_emotes.update(self.alt_emote)
            
            # make normal pages
            self.chara_pages = [self.cog.make_chara_embed(data, self.sections.copy())]
            self.ue_pages = self.cog.make_ue_embed(data, self.sections.copy())
            self.card_pages = [self.cog.make_card_embed(data, self.sections.copy())]
            self.stats_pages = [self.cog.make_stats_embed(data, self.sections.copy())]
            self.profile_pages = self.cog.make_profile_embed(data, self.sections.copy())

            # make alt
            if self.has_alt:
                self.chara_alt = [self.cog.make_chara_embed(data, self.sections.copy(), alt=True)]
                self.stats_alt = [self.cog.make_stats_embed(data, self.sections.copy(), alt=True)]
                self.ue_alt = self.cog.make_ue_embed(data, self.sections.copy(), alt=True)
            
            # make flb
            if self.has_flb:
                self.chara_pages.append(self.cog.make_chara_embed(data, self.sections.copy(), flb=True))
                self.card_pages.append(self.cog.make_card_embed(data, self.sections.copy(), flb=True))
                self.stats_pages.append(self.cog.make_stats_embed(data, self.sections.copy(), flb=True))

                if self.has_alt:
                    self.chara_alt.append(self.cog.make_chara_embed(data, self.sections.copy(), alt=True, flb=True))
                    self.stats_alt.append(self.cog.make_stats_embed(data, self.sections.copy(), alt=True, flb=True))

        def start(self):
            if self.current_page == "chara":
                page = self.chara_pages[1 if self.has_flb and self.flb else 0]
            elif self.current_page == "ue":
                page = self.ue_pages
            elif self.current_page == "card":
                page = self.card_pages[1 if self.has_flb and self.flb else 0]
            elif self.current_pages == "stats":
                page = self.stats_pages[1 if self.has_flb and self.flb else 0]
            else:
                page = self.profile_pages
            
            return page, self.base_emotes
        
        def set(self, option):
            if option == "flb":
                self.flb = not self.flb
            elif option == "alt":
                self.alt = not self.alt
            else:
                self.current_page = option
            
        def reload(self):
            if self.current_page == "chara":
                if self.has_alt and self.alt:
                    page = self.chara_alt[1 if self.has_flb and self.flb else 0]
                else:
                    page = self.chara_pages[1 if self.has_flb and self.flb else 0]
            elif self.current_page == "ue":
                if self.has_alt and self.alt:
                    page = self.ue_alt
                else:
                    page = self.ue_pages
            elif self.current_page == "card":
                page = self.card_pages[1 if self.has_flb and self.flb else 0]
            elif self.current_page == "stats":
                if self.has_alt and self.alt:
                    page = self.stats_alt[1 if self.has_flb and self.flb else 0]
                else:
                    page = self.stats_pages[1 if self.has_flb and self.flb else 0]
            else:
                page = self.profile_pages
            
            return page
        
    def make_character_help(self):
        embed = discord.Embed(
            title="Character Help",
            description="How to use/interpret `.character` and its child commands.",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Help | Ames Re:Re:Write',icon_url=self.client.user.avatar_url)

        embed.add_field(
            name="> **Command Syntax**",
            value="```css\n.c [prefix.][character] [*options]```\nexamples: `.c s.kyaru` `.c maho flb`\n\nThe command can also be called by its aliases `.chara` `.ue` `.card` `.pic` `.profile` `.stats`. They all follow the syntax above and only changes the first page you see.\nOnly accepted `option` at the moment is `flb` which tells Ames whether if she should fetch the character's FLB variant.\n`character` and `prefix` can both be aliases. Check out `.help alias` for more details.\nExtended help can be found at `.help character`.",
            inline=False
        )
        examples = [
            "n.rei",
            "x.ilya",
            "o.ninon",
            "v.shizuru",
            "s.saren",
            "h.misogi",
            "u.aoi",
            "m.kasumi",
            "p.yui",
            "cg.rin",
            "r.rin",
            "w.rino"
        ]
        embed.add_field(
            name="> **Active Prefixes**",
            value="These prefixes are used in front of a `character` to distinguish between character variants.",
            inline=False
        )
        embed.add_field(
            name="Prefix",
            value="\n".join(list(self.config['prefix_title'].keys()))
        )
        embed.add_field(
            name="Season/Event",
            value="\n".join(list(self.config['prefix_title'].values()))
        )
        embed.add_field(
            name="Example",
            value="\n".join(examples)
        )

        embed.add_field(
            name="> **Emotes/Reactions**",
            value="The reactions at the bottom of the embed help you navigate between available pages/let you know when interactivity window has ended. The available sections can be seen on every page under the [Section] field (usually near the top). The icons have the following meaning.",
            inline=False
        )
        embed.add_field(
            name="<:_chara:677763373739409436> Chara",
            value="React to switch to the character page. This page will contain basic information along with JP text. Contains more misc information that stats page.",
            inline=False
        )
        embed.add_field(
            name="<:_ue:677763400713109504> UnqEq",
            value="React to switch to the Unique Equipment page. This page will show the characters Skill 1 and Skill 1+ along with UE bonus stats (min/max), as long as the character has UE unlocked. If you need help with stat abbreviations, use `.c stats`.",
            inline=False
        )
        embed.add_field(
            name="<:_stats:678081583995158538> Stats",
            value="React to switch to the stats page. Shows detailed character stats such as HP and DEF as well as detailed skill actions and values such as damage dealt, range and uptime. If you need help with stat abbreviations, use `.c stats`.",
            inline=False
        )
        embed.add_field(
            name="<:_card:677763353069879306> Card",
            value="React to see character card. Can switch between normal and FLB variants.",
            inline=False
        )
        embed.add_field(
            name="<:_profile:718471302460997674> Profile",
            value="React to switch to the profile page. Contains various misc character information such as age, VA and birthday.",
            inline=False
        )
        embed.add_field(
            name=":star: FLB",
            value="React to switch between the character's normal and FLB variants. This react will only be present if the character has a FLB regardless of request.",
            inline=False
        )
        embed.add_field(
            name=":twisted_rightwards_arrows: Alt",
            value="React to switch between the character's normal and special/alternate skills. Useful for characters with a prominent alternate skillset such as Muimi. This react will only be present if the character has at least 1 alternate/special skill.",
            inline=False
        )
        embed.add_field(
            name="Any character icons i.e. <:kokkoro:613990045707272192> <:skokkoro:613990215941619722> <:pkokkoro:716516467734216795> <:nkokkoro:667257632142131230>",
            value="React to switch to the specified character page. These reacts will only show up if the requested character has more than variants beside the base character. Ames may take a few seconds to reorganise the emotes on the bottom.",
            inline=False
        )
        embed.add_field(
            name=":stop_sign:",
            value="Interactivity period has ended and Ames will no longer respond to reacts. The period is currently 70 seconds. This timer resets upon a valid interaction with the embed.",
            inline=False
        )
        return embed

    def make_stats_help(self):
        embed = discord.Embed(
            title="Stats Help",
            description="How to interpret stat abbreviations present in `.stats` and `.ue`.",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Stats Help | Ames Re:Re:Write',icon_url=self.client.user.avatar_url)

        txt = [
            ("Health Points","Character is knocked out when this hits 0."),
            ("Physical Attack","Attack power of physical attackers."),
            ("Magic Attack","Attack power of magic attackers."),
            ("Physical Defense","Defense power against physical attacks."),
            ("Magic Defense","Defense power against magic attacks."),
            ("Physical Critical Chance","Chances of a critical hit on a physical attack."),
            ("Magic Criticial Chance","Chances of a critical hit on a magic attack."),
            ("HP Recovery per wave","The amount of HP recovered at the end of a wave, such as multi-wave quests."),
            ("TP Recovery per wave","The amount of TP recovered at the end of a wave, such as multi-wave quests."),
            ("Evasion","Chances of evading a received attack."),
            ("Physical Penetration","Hidden Stat."),
            ("Magic Penetration","Hidden Stat."),
            ("HP Steal","The HP gained based on dealt damage."),
            ("HP Recovery","The HP recovered at the end of a stage, such as luna tower."),
            ("TP Recovery","The TP recovered at the end of a stage, such as luna tower."),
            ("Union Burst Efficiency","The amount TP that is saved on UB."),
            ("Accuracy","The chance that the attack will miss.")
        ]

        for key, (title, text) in list(zip(list(self.config['ue_abbrev'].values()), txt)):
            embed.add_field(
                name=f"> **[{key}]** {title}",
                value=text,
                inline=False
            )
        return embed

    @commands.command(aliases=['pos'])
    async def position(self, ctx, *request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client.command_status['pos']:
            raise commands.DisabledCommand
        
        if not request:
            await channel.send("There was no input. Enter `v`, `m` or `r` for vanguard, midguard or rearguard respectively, or enter a `character` to show their linup. See `.help position` for detailed help "+self.client.emotes['ames'])
            return
        
        request = [i.lower() for i in request]

        # match
        match, _, _, _ = await self.preprocess(ctx, request)

        # load all_data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data  = json.load(dbf)

        # see if chara or pos
        if not match:
            if request[0].startswith("v") or request[0].startswith("f"):
                mode = "front"
            elif request[0].startswith("m"):
                mode = "mid"
            elif request[0].startswith("r") or request[0].startswith("b"):
                mode = "rear"
            else:
                await channel.send(f"Did not find character or position {' '.join(request)} "+self.client.emotes['ames'])
                return
        else:
            tags = all_data['units'][match['index']]['tags']
            if "mid" in tags:
                mode = "mid"
            elif "front" in tags:
                mode = "front"
            elif "rear" in tags:
                mode = "rear"
            else:
                await channel.send(f"Target character is missing a position identifier tag "+self.client.emotes['ames'])
                return
        
        lineup = list(filter(lambda x: mode in x['tags'], all_data['units']))
        lineup.sort(key=lambda x: x['pos'])

        await channel.send(embed=self.make_pos_embed(lineup, match, mode))

    def make_pos_embed(self, lineup, match, mode):
        k = {"front":"Vanguard","mid":"Midguard","rear":"Rearguard"}
        title = f"Listing **{k[mode]}** Lineup. The character at `1` is closest to the enemy. "
        if match:
            title += f"Bolding **{self.client.get_full_name_kai(match['name_en'],match['prefix'])}'s** position.'"

        embed = discord.Embed(
            title=          "Lineup",
            description=    title,
            timestamp=      datetime.datetime.utcnow(),
            colour=         self.colour
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Lineup | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)

        numbered = [
            f"{self.client.team[c['sname']]} {i+1} {self.client.get_full_name_kai(c['basic']['en']['name'],c['basic']['en']['prefix'])}" 
            if not match 
            or not match['sname'] == c['sname']
            else f"> {self.client.team[c['sname']]} **{i+1} {self.client.get_full_name_kai(c['basic']['en']['name'],c['basic']['en']['prefix'])}**" 
            for i, c in enumerate(lineup)
        ]

        for chk in list(self.client.chunks(numbered,20)):
            embed.add_field(
                name="Lineup",
                value="\n".join(chk),
                inline=True
            )
        
        return embed

    @commands.command(alises=['tags'])
    async def tag(self, ctx, *request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client.command_status['tag']:
            raise commands.DisabledCommand
        
        if not request:
            await channel.send("There was no input. Enter tag(s) to see all matching characters or enter a `character` to see their tags. See tag definitions with `.help d`. See detailed help with `.help tag` "+self.client.emotes['ames'])
            return
        
        request = [i.lower() for i in request]

        # match
        match, _, _, _ = await self.preprocess(ctx, request)

        # load all_data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data  = json.load(dbf)

        if not match:
            include, exclude = [], []
            for tag in request:
                flag = True
                if tag.startswith('-'):
                    flag = False
                    tag = tag[1:]

                if not tag in (list(self.tag_definitions['basic'].keys()) + list((self.tag_definitions['atk'].keys())) + list(self.tag_definitions['buff'].keys())):
                    await channel.send(f"Unknown tag `{tag}`")
                    return
                
                if flag:
                    include.append(tag)
                else:
                    exclude.append(tag)

            lineup = []
            for chara in all_data['units']:
                if all([tag in chara['tags'] for tag in include]) and all(not tag in chara['tags'] for tag in exclude):
                    lineup.append(chara)
            lineup.sort(key=lambda x: x['basic']['en']['name'])

            await channel.send(embed=self.make_tag_search(lineup, include, exclude))
        else:
            await channel.send(embed=self.make_tag_chara(all_data['units'][match['index']]))
    
    def make_tag_search(self, lineup, include, exclude):
        description = f"Found `{len(lineup)}` character(s) that "
        ads = []
        if include:
            ads.append("include " + ", ".join([f"`{t}`" for t in include]))
        if exclude:
            ads.append("exclude " + ", ".join([f"`{t}`" for t in exclude]))
        
        description += " and ".join(ads)

        embed = discord.Embed(
            title=          "Tag Search",
            description=    description,
            timestamp=      datetime.datetime.utcnow(),
            colour=         self.colour
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Search | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)

        numbered = [
            f"{self.client.team[c['sname']]} {self.client.get_full_name_kai(c['basic']['en']['name'],c['basic']['en']['prefix'])}" 
            for c in lineup
        ]

        for chk in list(self.client.chunks(numbered,20)):
            embed.add_field(
                name="Lineup",
                value="\n".join(chk) if chk else "No matching characters",
                inline=True
            )
        
        return embed

    def make_tag_chara(self, data):
        embed = discord.Embed(
            title=          "Tag Search",
            description=    f"Listing **{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}'s** tags.",
            timestamp=      datetime.datetime.utcnow(),
            colour=         self.colour
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Search | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        embed.set_thumbnail(url=data['img'])

        embed.add_field(
            name="Tags",
            value=", ".join([f"`{t}`" for t in data['tags']])
        )

        return embed

    # alias
    @commands.group(
        invoke_without_command=True
    )
    async def alias(self, ctx, *request):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        
        if ctx.invoked_subcommand is None:
            if len(request) == 0:
                await self.display_aliases(ctx)
            else:
                await self.search(ctx, request[0])
    
    async def display_aliases(self, ctx):
        author = ctx.message.author
        master =    []
        local =     []

        # sort the aliases by master/local
        for a, o in list(self.full_alias.items()):
            if len(o) > 3: # hide prefixes
                if not self.config['alias_master'].get(a, None) is None:
                    master.append((a, o, 'master'))
                else:
                    local.append((a, o, 'local'))
        
        # sort in alphabetical order
        master.sort(key=lambda x: x[0])
        local.sort(key=lambda x: x[0])

        aliases_page = self.client.page_controller(self.client, self.embed_display_aliases, master+local, 15, True)

        page = await ctx.channel.send(embed=aliases_page.start())
        for arrow in aliases_page.arrows:
            await page.add_reaction(arrow)

        def check(reaction, user):
            return str(user.id) == str(author.id) and\
                    reaction.emoji in ['⬅','➡'] and\
                    str(reaction.message.id) == str(page.id)
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                for arrow in aliases_page.arrows:
                    await page.remove_reaction(arrow, self.client.user)
                return
            else:
                if reaction.emoji == aliases_page.arrows[0]:
                    await reaction.message.remove_reaction(aliases_page.arrows[0], user)
                    await reaction.message.edit(embed=aliases_page.flip('l'))
                elif reaction.emoji == aliases_page.arrows[1]:
                    await reaction.message.remove_reaction(aliases_page.arrows[1], user)
                    await reaction.message.edit(embed=aliases_page.flip('r'))

    def embed_display_aliases(self, data, index):
        embed = discord.Embed(
            title=f"Alias List - Page {index[0]} of {index[1]}",
            description="Lists all saved master and local aliases.",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Alias | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Alias",
            value="\n".join([item[0] for item in data]),
            inline=True
        )
        embed.add_field(
            name="Character",
            value="\n".join([item[1] for item in data]),
            inline=True
        )
        embed.add_field(
            name="perm",
            value="\n".join([item[2] for item in data]),
            inline=True
        )
        return embed

    async def search(self, ctx, request):
        channel = ctx.channel
        author = ctx.message.author

        # check if its an alias
        if request.lower() in list(self.full_alias.keys()):
            await channel.send(
                f"Alias `{request.lower()}` -> `{self.full_alias[request.lower()]}` [{'master' if request.lower() in list(self.config['alias_master']) else 'local'}]"
            )
        elif request.lower() in list(self.full_alias.values()):
            master =    []
            local =     []

            for a, o in list(self.full_alias.items()):
                if o == request.lower():
                    if a in list(self.config['alias_master'].keys()):
                        master.append((a, 'master'))
                    else:
                        local.append((a, 'local'))
            
            master.sort(key=lambda x: x[0])
            local.sort(key=lambda x: x[0])

            search_page = self.client.page_controller(self.client, self.embed_search, master+local, 15, True)
            page =  await channel.send(embed=search_page.start())

            for arrow in search_page.arrows:
                await page.add_reaction(arrow)

            def check(reaction, user):
                return str(user.id) == str(author.id) and\
                        reaction.emoji in ['⬅','➡'] and\
                        str(reaction.message.id) == str(page.id)
            
            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    for arrow in search_page.arrows:
                        await page.remove_reaction(arrow, self.client.user)
                    return
                else:
                    if reaction.emoji == search_page.arrows[0]:
                        await reaction.message.remove_reaction(search_page.arrows[0], user)
                        await reaction.message.edit(embed=search_page.flip('l'))
                    elif reaction.emoji == search_page.arrows[1]:
                        await reaction.message.remove_reaction(search_page.arrows[1], user)
                        await reaction.message.edit(embed=search_page.flip('r'))
        else:
            await channel.send(f"No alias/character found for `{request}`")

    def embed_search(self, data, index):
        embed = discord.Embed(
            title=f"Alias Search Page {index[0]} of {index[1]}",
            description="Listing search results",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Alias | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Alias",
            value="\n".join([item[0] for item in data]),
            inline=True
        )
        embed.add_field(
            name="perm",
            value="\n".join([item[1] for item in data]),
            inline=True
        )
        return embed
        
    @alias.command()
    async def add(self, ctx, alias, *character):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        
        # checks
        alias = alias.lower()

        if alias in list(self.config['alias_master'].keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record")
            return
        elif alias in list(self.full_alias.keys()):
            await channel.send(f"`{alias}` -> `{self.full_alias[alias]}` already exists")
            return
        
        # clean input
        for token in self.config['illegal_tokens']:
            alias = alias.strip(token)
        
        # check character
        # case uniformity
        character = [i.lower() for i in character]

        # preprocess the command to find what out what the request is
        mode, _character, option = await self.process_request(ctx, character, channel)
        # request here should be a string

        # validate request
        search_sucess, _character = self.validate_entry(_character)
        if not search_sucess:
            await channel.send(f"No character entry matching `{character}`")
            return 
        character = _character
        self.alocal[alias] =    character['en']
        self.full_alias =       self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        with open(os.path.join(self.client.dir, self.client.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alocal, indent=4))
        
        await channel.send(f"Successfully added `{alias}` -> `{character['en']}`")
        
    @alias.command()
    async def edit(self, ctx, alias, *character):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        
        # checks
        alias = alias.lower()

        if alias in list(self.config['alias_master'].keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record - You may not edit a master record")
            return
        elif not alias in list(self.full_alias.keys()):
            await channel.send(f"`{alias}` does not exist")
            return
        
        # clean input
        for token in self.config['illegal_tokens']:
            alias = alias.strip(token)
        
        # check character
        # case uniformity
        character = [i.lower() for i in character]

        # preprocess the command to find what out what the request is
        mode, _character, option = await self.process_request(ctx, character, channel)
        # request here should be a string

        # validate request
        search_sucess, _character = self.validate_entry(_character)
        if not search_sucess:
            await channel.send(f"No character entry matching `{character}`")
            return 
        character = _character
        self.alocal[alias] =    character['en']
        self.full_alias =       self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        with open(os.path.join(self.client.dir, self.client.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alocal, indent=4))
        
        await channel.send(f"Successfully edited `{alias}` -> `{character['en']}`")

    @alias.command()
    async def delete(self, ctx, alias):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        
        # checks
        alias = alias.lower()

        if alias in list(self.config['alias_master'].keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record - You may not delete a master record")
            return
        elif not alias in list(self.full_alias.keys()):
            await channel.send(f"`{alias}` does not exist")
            return
        
        self.alocal.pop(alias)
        self.full_alias =       self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        with open(os.path.join(self.client.dir, self.client.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alocal, indent=4))
        
        await channel.send(f"Successfully deleted `{alias}`")
