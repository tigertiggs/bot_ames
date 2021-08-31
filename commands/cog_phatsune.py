import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests, asyncio
from discord.ext.commands.core import after_invoke
from io import BytesIO
SPACE = '\u200B'

from cog_pupdate import validate_request, updateCog

#pupdate = None
#async def update_index(ctx):
#    pupdate.make_index()

def setup(client):
    client.add_cog(hatsuneCog(client))

class hatsuneCog(commands.Cog):
    def __init__(self, client):
        #global pupdate
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

        # persist
        self.active_embeds = dict()

        # co-dependence on pupdate
        #pupdate = updateCog(self.client)
        self.pupdate = updateCog(self.client)
    
    @commands.command(aliases=['c','ue', 'cw', 'chara', 'card', 'pic', 'cd', 'g', 'stats', 'st', 'profile', 'pf'])
    async def character(self, ctx, *request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client.command_status['chara']:
            raise commands.DisabledCommand
        elif not request:
            await channel.send("No input detected "+self.client.emotes['ames']+"\n-Use `.c help` or `.help character` if you need help.")
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
        match, alts, mode, invoke = await self.preprocess(ctx, request, invoke=ctx.invoked_with, verbose=False)

        if not match:
            await channel.send(f"Failed to find `{' '.join(request)}` "+self.client.emotes['ames']+"\n-Use `.c help` or `.help character` if you're stuck\n-Add the input as an alias to a character with `.alias add`. See `.help alias` for more")
            return
        
        #await channel.send("[Experimental Ames] This is currently a highly experimental version of `.character` and may be very unstable. Stable Ames will be up and running soon:tm:")
        if not match['flb'] and mode.get('flb', False):
            await channel.send(f"**[Note]: {self.client.get_full_name_kai(match['name_en'],match['prefix'])}** does not have a `flb` variant.")
            mode['flb'] = False

        await self.logger.send(self.name, match['sname'], match['name_jp'], match['hnid'])

        # load data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data  = json.load(dbf)

        # make alts
        all_charas = [match] + alts

        alt_data = [all_data['units'][m['index']] for m in all_charas]
        alt_emotes = [self.client.team.get(m['sname'],"❔") for m in all_charas]
        alt_embeds = [self.character_page_controller(self, d, invoke, **mode) for d in alt_data]

        alt_choice = 0
        fe, reactions = alt_embeds[alt_choice].start()
        page = await channel.send(embed=fe)

        self.active_embeds[str(page.id)] = author.id # add to persistence      

        for e in alt_emotes+list(reactions.keys()) if len(alt_emotes) > 1 else list(reactions.keys()):
            await page.add_reaction(e)

        def author_check(reaction, user):
            return str(user.id) == str(author.id) and str(reaction.emoji) in list(reactions.keys())+alt_emotes+['⏱️'] and str(reaction.message.id) == str(page.id)
        
        persist = False

        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=90.0, check=author_check)
            except asyncio.TimeoutError:
                #await page.add_reaction(alt_embeds[0].stop)
                if not persist:
                    await page.edit(embed=None, content=f"Embed for `{self.client.get_full_name_kai(match['name_en'], match['prefix'])}` has expired "+self.client.emotes['ames'])
                await page.clear_reactions()
                # remove persistence
                self.active_embeds.pop(str(page.id), None)
                return
            else:
                if str(reaction) in list(reactions.keys())+alt_emotes:
                    await reaction.message.remove_reaction(reaction.emoji, user)

                    if str(reaction) in alt_emotes:
                        new_choice = alt_emotes.index(str(reaction.emoji))

                        if new_choice != alt_choice:
                            alt_choice = new_choice

                            # find diff in base emotes
                            diff = list(set(reactions).symmetric_difference(set(list(alt_embeds[alt_choice].base_emotes.keys()))))
                            if diff:
                                # unreact the alts
                                #for e in alt_emotes:
                                #    await page.remove_reaction(e, self.client.user)

                                for e in diff:
                                    if not e in reactions:
                                        await page.add_reaction(e)
                                    else:
                                        await page.remove_reaction(e, self.client.user)
                                
                                # readd the alts
                                #for e in alt_emotes:
                                #    await page.add_reaction(e)
                            
                            reactions = alt_embeds[alt_choice].base_emotes

                    else:
                        alt_embeds[alt_choice].set(reactions[str(reaction.emoji)])
                    
                    await page.edit(embed=alt_embeds[alt_choice].reload())

                elif str(reaction) == '⏱️': # :stopwatch:
                    persist=True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.client.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        if user.bot:
            return
        elif not str(payload.emoji) == '⏹️': # :stop_button:
            return
        message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if self.active_embeds.get(str(message.id), None) and not self.active_embeds.get(str(message.id), None) == user.id:
            await message.remove_reaction('⏹️', user)
            return
        elif message.author.id == 757869389851787374:
            await message.delete()
            return
        elif not message.author is guild.me:
            return
        elif not message.embeds:
            return
        elif not message.embeds[0].author.name == "ハツネのメモ帳":
            return
        else:
            await message.clear_reactions()
            await message.edit(content="This embed has been deleted "+self.client.emotes['ames'], embed=None)
            self.active_embeds.pop(str(message.id), None)
        
    async def preprocess(self, ctx, request, **kwargs):
        verbose = kwargs.get('verbose', False)
        invoke = kwargs.get('invoke', None)

        # check invoke
        if invoke:
            if invoke in        ['ue', 'cw']:
                invoke =    "ue"
            elif invoke in      ['card', 'pic', 'g', 'cd']:
                invoke =    "card"
            elif invoke in      ['stats', 'st']:
                invoke =    "stats"
            elif invoke in      ['profile', 'pf']:
                invoke =    "profile"
            else:
                invoke =    "chara"
        else: # somehow bool(invoke) -> False
            invoke = 'chara'
        
        # check mode
        #mode = request[-1]
        #if mode in ['flb', 'ue']:
        #    if mode in ['ue']:
        #        if verbose: await ctx.message.channel.send("`ue` option is depreciated. Use `.ue [character]` instead.")
        #        mode = None
        #        invoke = "ue"
        #    elif mode == "flb":
        #        mode = "flb"
        #        request = request[:-1]
        #else:
        #    mode = None

        mode = {}
        pop = []
        for thing in request:
            if thing == "ue":
                if verbose: await ctx.message.channel.send("`ue` option is depreciated. Use `.ue [character]` instead.")
                invoke = "ue"
                pop.append(request.index(thing))
            elif thing == "flb":
                mode['flb'] = True
                pop.append(request.index(thing))
            elif thing == "ex":
                mode['ex'] = True
                pop.append(request.index(thing))

        for i in sorted(pop, reverse=True):
            del request[i]

        # check alias
        #prefix, _, name = "".join(request).partition(".")
        #prefix, name = prefix.strip(), name.strip()

        #if not name: # no . present
        #    name = prefix
        #    prefix = None
        
        processed = []
        prefix = None
        for r in request:
            pf, _, name = r.partition(".")
            pf, name = pf.strip(), name.strip()

            for word in [pf, name]:
                if not word:
                    continue

                word = self.full_alias.get(word, word)
                word = self.config['prefix_alias'].get(word, word)

                # check if using new prefixes
                for k, v in list(self.config['prefix_new'].items()):
                    #print(name, v)
                    if word in v:
                        prefix = k
                        word = None
            
                # check if name is actually a prefix
                if word in list(self.config['prefix_title'].keys()):
                    prefix = word
                    word = None

                #print(_prefix, name)
            
                # append
                if word:
                    processed.append(word)

        name = "".join(processed)
        #print(prefix, name)

        # kizuna preprocessor
        if prefix == 'k':
            prefix = None
            name = self.config['kizuna_search'].get(name, None)
            if name == None:
                await ctx.message.channel.send("Did not find kizuna (multi-unit) version of requested character!")
                return None, None, None, None

        if prefix and not prefix in list(self.config['prefix_title'].keys()):
            await ctx.message.channel.send(f"Unknown prefix `{prefix}`")
            return None, None, None, None

        #name = self.full_alias.get(name, name)
        prefix = self.full_alias.get(prefix, prefix) if prefix else None

        # validate
        match, alts, ipflag = validate_request(self.client, {"name":name,"prefix":prefix}, 'en', self.config)

        # warn
        if match:
            if not prefix and match['prefix'] and verbose:
                await ctx.message.channel.send(f"Searching syntax `{name}` is discouraged. Consider searching via `{match['prefix']}.{match['name_en']}` syntax next time "+self.client.emotes['ames'])
        if ipflag['flag'] == True:
            await ctx.message.channel.send(f"**[Note]: {self.client.get_full_name_kai(ipflag['name'], prefix=ipflag['prefix'])}** either does not exist or is not recorded in the database at the moment. Please try again later or bug the developer.")

        return match, alts, mode, invoke

    def get_attack_pattern(self, info, alt_mode, special=None):
        if "magic" in info['tags']:
            norm_atk = '<:magatk:713288155469578272>'
        else:
            norm_atk = '<:_chara:677763373739409436>'
        skills = [
            '1\u20E3',
            '2\u20E3',
            '3\u20E3'
        ]

        if special == '115801':
            i = 0
        elif special == '115802':
            i = 1
        elif special == '115803':
            i = 2
        else:
            i = 0 if not alt_mode else -1
        opening = info['atkptn'][i]['ptn'][:info['atkptn'][i]['loop'][0]-1]
        loop = info['atkptn'][i]['ptn'][info['atkptn'][i]['loop'][0]-1:]

        opening = "-".join([norm_atk if action == 1 else skills[action%10-1] for action in opening]) if len(opening) != 0 else "None"
        loop = "-".join([norm_atk if action == 1 else skills[action%10-1] for action in loop]) if len(loop) != 0 else "None"
        return "\n".join(
            [opening, loop]
        )

    def make_chara_embed(self, data, sections, **kwargs):
        flb = kwargs.get("flb", False)
        alt = kwargs.get("alt", False)
        ex = kwargs.get("ex", False)
        # norm      ->  ub       | sk1       | sk1p        | sk2       |  sk3       | ex | ex2
        # alt       ->  uba      |(sk1) sk1a |(sk1p) sk1ap |(sk2) sk2a | (sk3) sk3a | ex | ex2
        # flb       ->      ub2  |           | sk1p        | sk2       |  sk3       | ex2
        # flb+alt   ->      uba2 |           |(sk1p) sk1ap |(sk2) sk2a | (sk3) sk3a | ex2

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
        #if data['sname'] == "nkyaru":
        #    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/513948468281212928/700260655931981854/FncyaHa2.gif")
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Info Page | Ames Re:Re:Write',icon_url=data['img6'] if flb else data['img'])

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
            name="> **Special Attack Pattern**" if alt and len(data['atkptn']) > 1 else "**Attack Pattern**",
            value="Initial:\nLooping:",
            inline=True
        )
        if data['basic']['jp']['id'] == 1158:
            if not alt:
                embed.add_field(
                    name=SPACE,
                    value=self.get_attack_pattern(data, alt, '115803'),
                    inline=True
                )
            else:
                embed.add_field(
                    name=SPACE+"\n"+SPACE,
                    value=self.get_attack_pattern(data, alt, '115802'),
                    inline=True
                )
            embed.add_field(
                name=SPACE+"\n"+"Spec" if alt else "Spec",
                value=self.get_attack_pattern(data, alt, '115801'),
                inline=True
            )
        else:
            embed.add_field(
                name=SPACE,
                value=self.get_attack_pattern(data, alt),
                inline=True
            )

        # ub, ub2
        if not flb:
            test = alt and data['basic']['jp']['uba']['name']
            embed.add_field(
                name=   "> **Union Burst Special**" if test else "> **Union Burst**",
                value=  f"「{data['basic']['jp']['uba']['name']}」" if test else 
                        f"「{data['basic']['jp']['ub']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['uba']['text']}" if test else 
                        f"{data['basic']['jp']['ub']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['uba']['text']}" if test else 
                        f"{data['basic']['en']['ub']['text']}",
                inline= True
            )
        else:
            test = alt and data['basic']['jp']['uba2']['name']
            embed.add_field(
                name=   "> **Union Burst Special**" if test else "> **Union Burst+**",
                value=  f"「{data['basic']['jp']['uba2']['name']}」" if test else 
                        f"「{data['basic']['jp']['ub2']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['jp']['uba2']['text']}" if test else 
                        f"{data['basic']['jp']['ub2']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{data['basic']['en']['uba2']['text']}" if test else 
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

        # sk3, sk3a (may or may not exist)
        if data['basic']['jp']['sk3a']['text'] or data['basic']['jp']['sk3']['text']:
            if alt and data['basic']['jp']['sk3a']['text']:
                embed.add_field(
                    name=   "> **Skill 3 Special**",
                    value=  f"「{data['basic']['jp']['sk3a']['name']}」",
                    inline= False
                )
                embed.add_field(
                    name=   "Description",
                    value=  f"{data['basic']['jp']['sk3a']['text']}",
                    inline= True
                )
                embed.add_field(
                    name=   SPACE,
                    value=  f"{data['basic']['en']['sk3a']['text']}",
                    inline= True
                )
            elif not alt and data['basic']['jp']['sk3']['text']:
                embed.add_field(
                    name=   "> **Skill 3**",
                    value=  f"「{data['basic']['jp']['sk3']['name']}」",
                    inline= False
                )
                embed.add_field(
                    name=   "Description",
                    value=  f"{data['basic']['jp']['sk3']['text']}",
                    inline= True
                )
                embed.add_field(
                    name=   SPACE,
                    value=  f"{data['basic']['en']['sk3']['text']}",
                    inline= True
                )

        # ex
        if ex:
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
        # section
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )
        embed = self.add_extra_comment(embed,data)
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
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )
        embed = self.add_extra_comment(embed,data)
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
        
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )
        return embed

    def make_stats_embed(self, data, sections, **kwargs):
        flb = kwargs.get("flb", False)
        alt = kwargs.get("alt", False)
        ex = kwargs.get("ex", False)
        # norm      ->  ub      | sk1       | sk1p        | sk2       | ex | ex2
        # alt       ->  ub      |(sk1) sk1a |(sk1p) sk1ap |(sk2) sk2a | ex | ex2
        # flb       ->      ub2 |           | sk1p        | sk2       |    | ex2
        # flb+alt   ->      ub2 |           |(sk1p) sk1ap |(sk2) sk2a |    | ex2

        # make sections
        sections[sections.index("<:_stats:678081583995158538> Stats")] = "<:_stats:678081583995158538> **[Stats]**"

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

        # stats
        for chunk in self.client.chunks(list(data['stats']['normal'].items() if not flb else data['stats']['flb'].items()), 6):
            embed.add_field(
                name=f"Stats",
                value="\n".join([f"{self.config['ue_abbrev'].get(key, key.upper())}: {arg}" for key, arg in chunk])
            )

        # ub, ub2
        if not flb:
            test = alt and data['basic']['jp']['uba']['name']
            embed.add_field(
                name=   "> **Union Burst Special**" if test else "> **Union Burst**",
                value=  f"「{data['basic']['jp']['uba']['name']}」" if test else 
                        f"「{data['basic']['jp']['ub']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['en']['uba']['text']}" if test else 
                        f"{data['basic']['en']['ub']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['uba']['action'])) if test else 
                        "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['ub']['action'])),
                inline= True
            )
        else:
            test = alt and data['basic']['jp']['uba2']['name']
            embed.add_field(
                name=   "> **Union Burst Special+**" if test else "> **Union Burst+**",
                value=  f"「{data['basic']['jp']['uba2']['name']}」" if test else 
                        f"「{data['basic']['jp']['ub2']['name']}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{data['basic']['en']['uba2']['text']}" if test else 
                        f"{data['basic']['en']['ub2']['text']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['uba2']['action'])) if test else 
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

        # sk3, sk3a (may or may not exist)
        if data['basic']['jp']['sk3a']['text'] or data['basic']['jp']['sk3']['text']:
            if alt and data['basic']['jp']['sk3a']['text']:
                embed.add_field(
                    name=   "> **Skill 3 Special**",
                    value=  f"「{data['basic']['jp']['sk3a']['name']}」",
                    inline= False
                )
                embed.add_field(
                    name=   "Description",
                    value=  f"{data['basic']['en']['sk3a']['text']}",
                    inline= True
                )
                embed.add_field(
                    name=   SPACE,
                    value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk3a']['action'])),
                    inline= True
                )
            elif not alt and data['basic']['jp']['sk3']['text']:
                embed.add_field(
                    name=   "> **Skill 3**",
                    value=  f"「{data['basic']['jp']['sk3']['name']}」",
                    inline= False
                )
                embed.add_field(
                    name=   "Description",
                    value=  f"{data['basic']['en']['sk3']['text']}",
                    inline= True
                )
                embed.add_field(
                    name=   SPACE,
                    value=  "```glsl\n-{}```".format('\n-'.join(data['basic']['en']['sk3']['action'])),
                    inline= True
                )

        # ex
        if ex:
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
        # section
        embed.add_field(
            name='Section',
            value=' - '.join(sections),
            inline=False
        )
        embed = self.add_extra_comment(embed,data)
        return embed

    def make_profile_embed(self, data, sections, **kwargs):
        sections[sections.index("<:_profile:718471302460997674> Profile")] = "<:_profile:718471302460997674> **[Profile]**"
        embed = discord.Embed(
            title="Character Profile",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Profile | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
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
            value=data['profile']['jp']['name_irl']
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
        embed.add_field(
            name="Section",
            value=" - ".join(sections),
            inline=False
        )
        return embed

    def add_extra_comment(self, embed, data):
        if data['basic']['jp']['sk1a']['text'] or data['basic']['jp']['sk2a']['text']:
            embed.add_field(
                name="Ames' footnote "+self.client.emotes['derp'],
                value=f"**{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} has a alternate skillset** that can be toggled via :twisted_rightwards_arrows: below. Read more about how the buttons on the bottom work by visiting `.c help`.",
                inline=False
            )
        return embed

        #alts = ['labyrista', 'muimi', 'luna']
        #if not data['sname'] in alts:
        #    return embed
        #else:
        #    embed.add_field(
        #        name=SPACE,
        #        value=f"psst - **{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} has a alternate skillset** that can be toggled via :twisted_rightwards_arrows: below",
        #        inline=False
        #    )
        #    return embed

    class character_page_controller():
        def __init__(self, cog, data, first_page, **kwargs):
            self.flb = kwargs.get("flb", False)
            self.alt = kwargs.get("alt", False)
            self.ex = kwargs.get("ex", False)
            
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
            self.chara_pages = [self.cog.make_chara_embed(data, self.sections.copy(), ex=self.ex)]
            self.ue_pages = self.cog.make_ue_embed(data, self.sections.copy())
            self.card_pages = [self.cog.make_card_embed(data, self.sections.copy())]
            self.stats_pages = [self.cog.make_stats_embed(data, self.sections.copy(), ex=self.ex)]
            self.profile_pages = self.cog.make_profile_embed(data, self.sections.copy())

            # make alt
            if self.has_alt:
                self.chara_alt = [self.cog.make_chara_embed(data, self.sections.copy(), alt=True, ex=self.ex)]
                self.stats_alt = [self.cog.make_stats_embed(data, self.sections.copy(), alt=True, ex=self.ex)]
                self.ue_alt = self.cog.make_ue_embed(data, self.sections.copy(), alt=True)
            
            # make flb
            if self.has_flb:
                self.chara_pages.append(self.cog.make_chara_embed(data, self.sections.copy(), flb=True, ex=self.ex))
                self.card_pages.append(self.cog.make_card_embed(data, self.sections.copy(), flb=True))
                self.stats_pages.append(self.cog.make_stats_embed(data, self.sections.copy(), flb=True, ex=self.ex))

                if self.has_alt:
                    self.chara_alt.append(self.cog.make_chara_embed(data, self.sections.copy(), alt=True, flb=True, ex=self.ex))
                    self.stats_alt.append(self.cog.make_stats_embed(data, self.sections.copy(), alt=True, flb=True, ex=self.ex))

        def start(self):
            if self.current_page == "chara":
                page = self.chara_pages[1 if self.has_flb and self.flb else 0]
            elif self.current_page == "ue":
                page = self.ue_pages
            elif self.current_page == "card":
                page = self.card_pages[1 if self.has_flb and self.flb else 0]
            elif self.current_page == "stats":
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
            description="How to use/interpret `.character` and its subcommands.",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Help | Ames Re:Re:Write',icon_url=self.client.user.avatar_url)

        embed.add_field(
            name="> **Command Syntax**",
            value="```css\n.c [prefix.][character] [*options]```\nExamples:\n`.c s.kyaru` `.card maho flb` `.stats labyrista ex` `.c shizuru flb ex` `.card rei flb` `.profile nanaka`\n\nThe command can also be called by its aliases `.chara` `.ue` `.card` `.pic` `.profile` `.stats`. They all follow the syntax above and only changes the lainding page.\n\nAccepted `[options]` are `flb` and `ex` which fetches the character's FLB variant and EX/EX+ skills respectively.\n\nExtended help can be found at `.help character`.",
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
            "d.rin",
            "r.rin",
            "w.rino",
            "a.akari",
            "c.kokkoro",
            "cr.rima",
            "f.chieru",
            "tt.inori",
            "ww.aot",
            "k.shiori/k.hatsune"
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
            value="The reactions at the bottom of the embed help you navigate between available pages and can be seen on every page under the [Section] field at the very bottom. The icons have the following meaning.",
            inline=False
        )
        embed.add_field(
            name="> <:_chara:677763373739409436> Character",
            value="React to switch to the character page. This page will contain basic information along with JP text. Contains more misc. information than stats page.",
            inline=False
        )
        embed.add_field(
            name="> <:_ue:677763400713109504> Unqiue Equipment/Character Weapon",
            value="React to switch to the Unique Equipment page. This page will show the character's Skill 1 and Skill 1+ along with UE bonus stats (min/max), as long as the character has UE unlocked. If you need help with stat abbreviations, use `.c stats`.",
            inline=False
        )
        embed.add_field(
            name="> <:_stats:678081583995158538> Statistics",
            value="React to switch to the stats page. Shows detailed character stats such as HP and DEF as well as detailed skill actions and values such as damage dealt, range and uptime. If you need help with stat abbreviations, use `.c stats`.",
            inline=False
        )
        embed.add_field(
            name="> <:_card:677763353069879306> Card",
            value="React to see character card. Can switch between normal and FLB variants.",
            inline=False
        )
        embed.add_field(
            name="> <:_profile:718471302460997674> Profile",
            value="React to switch to the profile page. Contains various misc character information such as age, VA, birthday, etc.",
            inline=False
        )
        embed.add_field(
            name="> :star: FLB (Full Limit Break)",
            value="React to switch between the character's normal and FLB variants (6\⭐ variant). This react will only be present if the character has a FLB regardless of request.",
            inline=False
        )
        embed.add_field(
            name="> :twisted_rightwards_arrows: Alternate/Special Skills",
            value="React to switch between the character's normal and special/alternate skills. Useful for characters with a prominent alternate skillset such as Muimi and Labyrista. This react will only be present if the character has at least 1 alternate/special skill.",
            inline=False
        )
        embed.add_field(
            name="> <:kokkoro:613990045707272192> <:skokkoro:613990215941619722> <:pkokkoro:716516467734216795> <:nkokkoro:667257632142131230> Any character icons",
            value="React to switch to the specified character page. These reacts will only show up if the requested character has more than 1 variant. Helpful if you've forgotten the prefix.",
            inline=False
        )
        #embed.add_field(
        #    name=":stop_sign:",
        #    value="Interactivity period has ended and Ames will no longer respond to reacts. The period is currently 70 seconds. This timer resets upon a valid interaction with the embed.",
        #    inline=False
        #)
        embed.add_field(
            name="> :stopwatch: Force embed persist",
            value="MANUALLY react this on the embed to stop the embed from being deleted on timeout (70s inactivity). Find this emote quickly by searching `:stop`.",
            inline=False
        )
        embed.add_field(
            name="> :stop_button: Delete embed",
            value="MANUALLY react this on the embed to instantly delete it. This can only be done to embeds with the title `ハツネのメモ帳`. Find this emote quickly by searching `:stop`.",
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
            f"{self.client.team.get(c['sname'],':grey_question:')} {i+1 if c['pos'] else '??'} {self.client.get_full_name_kai(c['basic']['en']['name'],c['basic']['en']['prefix'],True)}" 
            if not match 
            or not match['sname'] == c['sname']
            else f"> {self.client.team.get(c['sname'],':grey_question:')} **{i+1 if c['pos'] else '??'} {self.client.get_full_name_kai(c['basic']['en']['name'],c['basic']['en']['prefix'],True)}**" 
            for i, c in enumerate(lineup)
        ]

        for chk in list(self.client.chunks(numbered,20)):
            embed.add_field(
                name="Lineup",
                value="\n".join(chk),
                inline=True
            )
        #for chk in [numbered[:len(numbered)//2], numbered[len(numbered)//2:]]:
        #    embed.add_field(
        #        name="Lineup",
        #        value="\n".join(chk),
        #        inline=True
        #    )
        
        return embed

    @commands.group(aliases=['tags'],invoke_without_command=True)
    async def tag(self, ctx, *request):
        if not ctx.invoked_subcommand is None:
            return
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

        all_tags = (list(self.tag_definitions['basic'].keys()) + list((self.tag_definitions['atk'].keys())) + list(self.tag_definitions['buff'].keys()))
        if not match:
            include, exclude = [], []
            for tag in request:
                flag = True
                if tag.startswith('-'):
                    flag = False
                    tag = tag[1:]

                if tag == 'prifes':
                    tag = 'prinfes'

                if not tag in all_tags:
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
            f"{self.client.team.get(c['sname'],':grey_question:')} {self.client.get_full_name_kai(c['basic']['en']['name'],c['basic']['en']['prefix'],True)}" 
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

    @tag.command(aliases=['def', 'help'])
    async def d(self, ctx, *request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client.command_status['tag']:
            raise commands.DisabledCommand
        elif not request:
            await channel.send("No input - enter tags to fetch their definitions")
            return
        
        # standardize and pick unique items
        request = [i.lower() for i in request]
        request = list(set(request))

        # validate
        #all_tags = (list(self.tag_definitions['basic'].keys()) + list((self.tag_definitions['atk'].keys())) + list(self.tag_definitions['buff'].keys()))
        all_tags = dict()
        for item in self.tag_definitions:
            all_tags = {**all_tags, **self.tag_definitions[item]} #kms

        valid = []
        for tag in request:
            definition = all_tags.get(tag, None)
            if not definition:
                await channel.send(f"Unknown tag `{tag}`")
                return
            else:
                valid.append((tag, definition))
        
        def_page_controller = self.client.page_controller(self.client, self.make_definitions, valid, 6, True)
        page = await channel.send(embed=def_page_controller.start())
        for arrow in def_page_controller.arrows:
            await page.add_reaction(arrow)
        
        def author_check(reaction, user):
            return str(reaction) in def_page_controller.arrows and user.id == author.id and reaction.message.id == page.id
        
        while True:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=90, check=author_check)
            except asyncio.TimeoutError:
                await page.clear_reactions()
                return
            else:
                emote_check = str(reaction)
                await page.remove_reaction(emote_check, user)
                if emote_check == def_page_controller.arrows[0]:
                    mode = 'l'
                else:
                    mode = 'r'
                
                await page.edit(embed=def_page_controller.flip(mode))
                   
    def make_definitions(self, tags, index):
        embed = discord.Embed(
            title=f"Tag Definitions (page {index[0]} of {index[1]})",
            description="Listing tag definitions",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Definitions | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        for tag, definition in tags:
            embed.add_field(
                name=f"> `{tag}`",
                value=definition,
                inline=False
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

    #@alias.after_invoke
    #async def update_index(self, ctx):
    #    self.pupdate.make_index()

    async def display_aliases(self, ctx):
        author = ctx.message.author
        master =    []
        local =     []

        # sort the aliases by master/local
        for a, o in list(self.full_alias.items()):
            #if len(o) > 1: # hide prefixes
            match, _, _, _ = await self.preprocess(ctx, [o], verbose=False)
            if match: o = f"{self.client.team.get(match['sname'],':grey_question:')} {self.client.get_full_name_kai(match['name_en'], match['prefix'])}"

            if not self.config['alias_master'].get(a, None) is None:
                master.append((a, o, 'master'))
            else:
                local.append((a, o, 'local'))
        
        # sort in alphabetical order
        master += local
        master.sort(key=lambda x: x[0])
        #local.sort(key=lambda x: x[0])
    
        aliases_page = self.client.page_controller(self.client, self.embed_display_aliases, master, 15, True)

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
                #for arrow in aliases_page.arrows:
                await page.clear_reactions()
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
            full = self.full_alias[request.lower()]
            match, _, _, _ = await self.preprocess(ctx, [request], verbose=False)
            if not match:
                await channel.send(
                    f"Alias `{request.lower()}` -> `{self.full_alias[request.lower()]}` [{'master' if request.lower() in list(self.config['alias_master']) else 'local'}]"
                )
            else:
                await channel.send(
                    f"Alias `{request.lower()}` -> `{self.client.get_full_name_kai(match['name_en'], match['prefix'])}` [{'master' if request.lower() in list(self.config['alias_master']) else 'local'}]"
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
            
            master += local
            master.sort(key=lambda x: x[0])
            #local.sort(key=lambda x: x[0])

            search_page = self.client.page_controller(self.client, self.embed_search, master, 15, True)
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
                    #for arrow in search_page.arrows:
                    await page.clear_reactions()
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
        elif not character:
            await channel.send("Missing character input")
            return
        elif len(alias) < 2:
            await channel.send("Alias input must be more than 2 characters")
            return
        
        # checks
        alias = alias.lower()

        if alias in list(self.config['alias_master'].keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record and will conflict")
            return
        elif alias in list(self.full_alias.keys()):
            full, _, _, _ = await self.preprocess(ctx, [self.full_alias[alias]], verbose=False)
            if not full:
                await channel.send(f"`{alias}` -> `{self.full_alias[alias]}` already exists")
            else:
                await channel.send(f"`{alias}` -> `{self.client.get_full_name_kai(full['name_en'],full['prefix'])}` already exists")
            return
        
        # clean input
        for token in self.config['illegal_tokens']:
            alias = alias.strip(token)
        
        # check character
        # case uniformity
        character = [i.lower() for i in character]

        # preprocess the command to find what out what the request is
        match, _, _, _ = await self.preprocess(ctx, character, verbose=False)

        if not match:
            await channel.send(f"No character entry matching `{character}`")
            return 
        #character = _character

        self.alocal[alias] =    match['sname']
        self.full_alias =       self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        with open(os.path.join(self.client.dir, self.client.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alocal, indent=4))
        
        await channel.send(f"Successfully added `{alias}` -> `{self.client.get_full_name_kai(match['name_en'], match['prefix'])}`")
        self.pupdate.make_index()
        
    @alias.command()
    async def edit(self, ctx, alias, *character):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        
        # checks
        alias = alias.lower()

        if alias in list(self.config['alias_master'].keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record and cannot be modified.")
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
        match, _, _, _ = await self.preprocess(ctx, character, verbose=False)

        if not match:
            await channel.send(f"No character entry matching `{character}`")
            return 

        self.alocal[alias] =    match['sname']
        self.full_alias =       self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        with open(os.path.join(self.client.dir, self.client.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alocal, indent=4))
        
        await channel.send(f"Successfully edited `{alias}` -> `{self.client.get_full_name_kai(match['name_en'], match['prefix'])}`")
        self.pupdate.make_index()

    @alias.command(aliases=['rm'])
    async def delete(self, ctx, alias):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        
        # checks
        alias = alias.lower()

        if alias in list(self.config['alias_master'].keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record and cannot be modified")
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
        self.pupdate.make_index()

    @commands.command(aliases=['delta'])
    async def compare(self, ctx, rank_range, *request):
        channel = ctx.channel
        if not self.client.command_status['compare']:
            raise commands.DisabledCommand
        elif not request:
            await channel.send("No character specified")
            return

        # character validation
        match, _, mode, _ = await self.preprocess(ctx, [i.lower() for i in request], invoke=ctx.invoked_with, verbose=False)

        if not match:
            await channel.send(f"Failed to find `{' '.join(request)}`")
            return
        if mode == 'flb' and not match['flb']:
            await channel.send(f"`{self.client.get_full_name_kai(match['name_en'], match['prefix'])}` does not have a FLB variant")
            return
        
        # validate rank
        rank_i, _, rank_f = rank_range.partition("-")
        with open(os.path.join(self.client.dir, self.client.config["unit_list_path"])) as idf:
            constants = json.load(idf)['constants']
            if not rank_f:
                rank_f = constants['rk']
        try:
            rank_i, rank_f = int(rank_i), int(rank_f)
        except:
            await channel.send(self.client.emotes['ames'])
            return

        if not 0 < rank_i <= constants['rk'] or not 0 < rank_f <= constants['rk']:
            await channel.send("Rank input out of range")
            return
        
        # fetch
        params_f = {
            "cmd": "priconne.api",
            "call": "api.fetch",
            "id": match['hnid'],
            "rarity": 6 if mode=='flb' else 5,
            "rank": rank_f
        }
        params_i = {
            "cmd": "priconne.api",
            "call": "api.fetch",
            "id": match['hnid'],
            "rarity": 6 if mode=='flb' else 5,
            "rank": rank_i
        }
        port = self.client.config['port']
        if port != 'default':
            request = f"http://localhost:{port}/FagUtils/gateway.php?"
        else:
            request = f"http://localhost/FagUtils/gateway.php?"
        try:
            result_i = requests.get(request, params=params_i)
            result_f = requests.get(request, params=params_f)
            ri = json.load(BytesIO(result_i.content))
            rf = json.load(BytesIO(result_f.content))
        except Exception as e:
            await self.logger.send(self.name, e)
            return
    
        if ri['status'] != 200 or rf['status'] != 200:
            await self.logger.send(self.name, ri['status'], rf['status'])
            await channel.send(f"Failed to fetch {ri['status']}, {rf['status']}")
            return
        
        if mode == "flb":
            stats_i = ri['data']['stats_flb']
            stats_f = rf['data']['stats_flb']
        else:
            stats_i = ri['data']['stats']
            stats_f = rf['data']['stats']

        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            data  = json.load(dbf)['units'][match['index']]

        await channel.send(embed=self.make_compare_embed(data, (rank_i,rank_f), stats_i, stats_f, mode=='flb'))
        
    def make_compare_embed(self, data, rankr, ri, rf, flb):
        if flb:
            title = f"{data['basic']['jp']['name']} 6\⭐\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])} FLB"
        else:
            title = f"{data['basic']['jp']['name']}\n{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}"
        
        embed = discord.Embed(
            title=title,
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=data['img6'] if flb else data['img'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Delta | Ames Re:Re:Write',icon_url=data['img6'] if flb else data['img'])

        embed.description = f"{self.client.get_full_name_kai(data['basic']['en']['name'],data['basic']['en']['prefix'])}\'s stat difference from rank **{rankr[0]} to {rankr[1]}**. Baseline stats assume **LV{data['status']['lvl']}**, **max rarity** (5\⭐ unless FLB mode) with **MAX BOND** across all character variants. `Note: This page is a WIP and displayed stats may be inaccurate`"

        # stats
        #for chunk in self.client.chunks(list(rf.items()), 6):
        #    embed.add_field(
        #        name=f"Stats",
        #        value="\n".join([f"{self.config['ue_abbrev'].get(key, key.upper())}: {arg} ({'+'+str(arg-ri[key]) if arg-ri[key] >= 0 else str(arg-ri[key])})" for key, arg in chunk])
        #    )
        #for chunk in self.client.chunks(list(rf.items()), 6):
        
        #embed.add_field(
        #    name=f"Stats",
        #    value="\n".join([f"{self.config['ue_abbrev'].get(key, key.upper())}: {arg} ({'+'+str(arg-ri[key]) if arg-ri[key] >= 0 else str(arg-ri[key])})" for key, arg in rf.items()])
        #)

        embed.add_field(
            name=f"Field",
            value="\n".join([f"{self.config['ue_abbrev'].get(key, key.upper())}:" for key, arg in rf.items()])
        )
        embed.add_field(
            name=f"Value",
            value="\n".join([f"{arg} ({'+'+str(arg-ri[key]) if arg-ri[key] >= 0 else str(arg-ri[key])})" for key, arg in rf.items()])
        )

        return embed