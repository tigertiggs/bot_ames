# cog for fetching data off custom DB

import datetime
import discord
from discord.ext import commands
import asyncio, os, traceback, time, json, requests
from io import BytesIO
dir = os.path.dirname(__file__)
SPACE = '\u200B'

class hatsuneCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = self.client.log
        self.name = "[hatsune]"
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_hatsune'])

        # load configs
        with open(os.path.join(self.client.dir, self.client.config['hatsune_config_path'])) as hcf:
            self.config = json.load(hcf)
        with open(os.path.join(self.client.dir, self.client.config['tags_index_path'])) as tif:
            self.tag_definitions = json.load(tif)
        with open(os.path.join(self.client.dir, self.client.config['alias_local_path'])) as alf:
            self.alocal = json.load(alf)
        #with open(os.path.join(self.client.dir, self.client.config['unit_list_path'])) as ulf:
        #    self.unit_list = json.load(ulf)

        self.full_alias = self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        # db stuff
        self.db = self.client.database

        # help stuff
        self.full_help =     ("**In case you forgot, the input syntax is:**\n"
                            "> `.c(haracter) [version|optional].[character_name] [*option|optional]`\n"
                            "> i.e. `.c s.kyaru` `.c maho flb`\n"
                        "**The seasonal prefixes are:**\n"
                            "> `n` for New year i.e. `n.rei`\n"
                            "> `x` for Christmas i.e. `x.ayane`\n"
                            "> `o` for Ouedo i.e. `o.ninon`\n"
                            "> `v` for Valentines i.e. `v.shizuru`\n"
                            "> `s` for Summer i.e. `s.io`\n"
                            "> `h` for Halloween i.e. `h.miyako`\n"
                            "> `u` for Uniform i.e. `u.aoi`\n"
                            "> `m` for Magical Girl i.e. `m.shiori`\n"
                            "> `p` for Princess i.e. `p.peco`\n"
                            "> `cg` for DereMasu i.e. `cg.uzuki`\n"
                            "> `r` for ranger i.e. `r.rin`\n"
                        "**The following icons at the bottom of the embed have the following meaning:**\n"
                            "> <:_chara:677763373739409436> react to access chara and skill info\n"
                            "> <:_ue:677763400713109504> react to access UE info and data\n"
                            "> <:_stats:678081583995158538> react to access detailed character and skill stats (WIP)\n"
                            "> <:_card:677763353069879306> react to access pretty pictures\n"
                            "> :star: react to access the character's FLB variant\n"
                            "> :twisted_rightwards_arrows: react to access character's special/alternate skills\n"
                            "> :stop_sign: Ames will no longer respond to reacts on this embed")
        
        self.help =          ("If you need help, try `.c(haracter) help`")

    def error(self):
        error_msg = dict()
        error_msg['no_input'] =     'There was no input\n'+self.help
        error_msg['search_fail'] =  f"{self.client.emotes['ames']} I didn\'t find the requested character\n"+self.help
        error_msg['conn_fail'] =    'Failed to connect to database!'
        error_msg['pos_fail'] =     'Invalid input! Use `v` for vanguard, `m` for midguard or `r` for rearguard. '\
                                    'Alternatively enter a character name to find their lineup.'
        return error_msg

     # to avoid connecting to pandaDB keep a local copy of the index
    def get_attack_pattern(self, info):
        if "magic" in info['tag']:
            norm_atk = '<:magatk:713288155469578272>'
        else:
            norm_atk = '<:_chara:677763373739409436>'
        skills = [
            '1\u20E3',
            '2\u20E3'
        ]
        opening = info['attack_pattern']['action'][:info['attack_pattern']['loop'][0]-1]
        loop = info['attack_pattern']['action'][info['attack_pattern']['loop'][0]-1:]

        opening = "-".join([norm_atk if action == 1 else skills[action%10-1] for action in opening]) if len(opening) != 0 else "None"
        loop = "-".join([norm_atk if action == 1 else skills[action%10-1] for action in loop]) if len(loop) != 0 else "None"
        return "\n".join(
            [opening, loop]
        )
        
    def validate_entry(self, target):
        with open(os.path.join(self.client.dir, self.client.config['unit_list_path'])) as ulf:
            self.unit_list = json.load(ulf)

        if not (target in self.unit_list['jp'] or target in self.unit_list['en']):
            return False, None
        elif target in self.unit_list['en']:
            pos = self.unit_list['en'].index(target)
        else:
            pos = self.unit_list['jp'].index(target)
        
        return True, {
                        'id': self.unit_list['id'][pos], 
                        'en': self.unit_list['en'][pos], 
                        'jp': self.unit_list['jp'][pos]
                    }
        
    async def process_request(self, ctx, request, channel, verbose=True):
        # the goal for prerprocessing is to
        #   1. find which mode the user wants (.c, .ue., .card, .stats)
        #   2. find what option, if any are input: (flb)
        #   3. find if the primary request is an alias
        # this result is used validated with the local unit_list
        # finally the japanese name is used to fetch the raw data off laragon and the TL data off pandaDB

        # we expect the request be of the form:
        # (prefix.chara/alias, option)

        # old form:
        # (prefixchara/alias, option)
        processed = []

        # check mode
        invk = ctx.invoked_with
        if invk == 'ue':
            mode = 'ue'
        elif invk == 'card' or invk == 'pic':
            mode = 'card'
        elif invk == 'stats':
            mode = 'stats'
        else:
            mode = 'chara'
        
        # check option
        option = request[-1]
        if not option in self.config['options']:
            if option in ['ue'] and verbose:
                await channel.send(self.client.emotes['ames']+" Option `ue` is no longer in use; use `.ue` instead")
                mode = 'ue'
                option = None
            else:
                option = None
        else:
            # remove the option from the request
            request = request[:-1]
        
        # process prefix and run through master and local aliases
        for item in self.process_prefix(request):
            processed.append(self.full_alias.get(item, item).lower())

        return mode, "".join(processed), option

    def process_prefix(self, request):
        # we expect request to be of the form:
        # (prefix.name, )
        # (prefixname, )

        processed = []
        for item in request:
            temp = item.split('.')

            if len(temp) == 2:
                prefix = temp[0]
                if prefix in list(self.config['prefix_title'].keys()):
                    processed.append("".join(temp[:2]))
                else:
                    for key, value in list(self.config['prefix_new'].items()):
                        if prefix in value:
                            processed.append("".join([key, temp[1]]))
            else:
                processed.append(item)
        
        return processed # vector

        # fetch raw and TL data
    
    async def fetch_data_kai(self, info, conn):
        #global MAX_LEVEL
        #ue = dict()
        #t0 = time.perf_counter()
        query = ("SELECT "
                    "hc.unit_name_eng, ub_trans, ub_2_trans, "
                    "skill_1_translation, skill_1_plus_trans, skill_2_trans, sk1a_trans, sk2a_trans, "
                    "comment_trans, tag, "
                    "eq_name_trans, eq_rank "
                "FROM "
                    "hatsune_bot.charadata AS hc LEFT JOIN hatsune_bot.charaUE AS hu "
                "ON "
                    "hu.unit_id = hc.unit_id "
                "WHERE "
                    "hc.unit_id = {} "
                "LIMIT 1")
        cursor = conn.cursor(buffered=True)
        cursor.execute(query.format(info['id']))

        for (en, ubtl, ub2tl, sk1tl, sk1ptl, sk2tl, sk1atl, sk2atl, cmtl, tag, ueen, uerank) in cursor:
            info['en'] =            en
            info['ubtl'] =          ubtl
            info['ub2tl'] =         ub2tl
            info['sk1tl'] =         sk1tl
            info['sk1ptl'] =        sk1ptl
            info['sk2tl'] =         sk2tl
            info['sk1atl'] =        sk1atl
            info['sk2atl'] =        sk2atl
            info['cmtl'] =          cmtl
            info['tag'] =           [c.strip() for c in tag.split(',')]
            info['ue_en'] =         ueen
            info['ue_rank'] =       uerank

        #print(f"Fetch TL data - {(time.perf_counter()-t0)*1000}ms")
        #t0 = time.perf_counter()

        name = info['jp']
        port = self.client.config['port']
        if port != 'default':
            request = f"http://localhost:{port}/FagUtils/gateway.php?cmd=priconne.api&call=api.fetch&name={name}"
        else:
            request = f"http://localhost/FagUtils/gateway.php?cmd=priconne.api&call=api.fetch&name={name}"
        
        try:
            result = requests.get(request)
            raw = json.load(BytesIO(result.content))
        except Exception as e:
            await self.logger.send('failed to fetch data: ', e)
            return False

        info['max_ue'] =        raw['config']['UE_MAX']
        info['hnote_id'] =      raw['data']['unit_profile']['id']
        info['cm'] =            raw['data']['unit_profile']['comment'].replace('\\n', '')
        info['stats'] =         raw['data']['stats']
        info['max_lvl'] =       raw['config']['LEVEL_MAX']
        info['max_rk'] =        raw['config']['RANK_MAX']
        
        #info['attack_pattern'] =raw['data']['unit_profile']['attack_pattern']
        atk_pattern =           raw['data']['unit_pattern']
        loop =                  [atk_pattern['loop_start'],atk_pattern['loop_end']]
        action =                [[key, value] for key, value in list(atk_pattern.items()) if key.startswith("action_")]
        action.sort(key=lambda x: x[0])
        action =                [value for key, value in action]
        info['attack_pattern'] ={"loop":loop,"action":action}

        # UE
        info['ue'] =            raw['data']['unique_equipment']
        #info['ue_id'] =         ue_raw.gets('ue_id', None)
        #info['ue_jp'] =         ue_raw.gets('ue_name', None)

        # Skills
        sk_raw =                raw['data']['skill_data']
        info['ubjp'] =          sk_raw['Union Burst']['skill_name']
        info['ub'] =            sk_raw['Union Burst']['description']
        info['ubaction'] =      sk_raw['Union Burst']['actions']

        info['sk1jp'] =         sk_raw['Skill 1']['skill_name']
        info['sk1'] =           sk_raw['Skill 1']['description']
        info['sk1action'] =     sk_raw['Skill 1']['actions']

        info['sk2jp'] =         sk_raw['Skill 2']['skill_name']
        info['sk2'] =           sk_raw['Skill 2']['description']
        info['sk2action'] =     sk_raw['Skill 2']['actions']

        ub2_raw =               sk_raw.get('Union Burst+', dict())
        info['ub2jp'] =         ub2_raw.get('skill_name', None)
        info['ub2'] =           ub2_raw.get('description', None)
        info['ub2action'] =     ub2_raw.get('actions', [None])

        sk1p_raw =              sk_raw.get("Skill 1+", dict())
        info['sk1pjp'] =        sk1p_raw.get("skill_name", None)
        info['sk1p'] =          sk1p_raw.get("description", None)
        info['sk1paction'] =    sk1p_raw.get('actions', [None])

        sk1a_raw =              sk_raw.get('Skill 1 Alt', dict())
        info['sk1ajp'] =        sk1a_raw.get('skill_name', None)
        info['sk1a'] =          sk1a_raw.get('description', None)
        info['sk1aaction'] =    sk1a_raw.get('actions', [None])

        sk2a_raw =              sk_raw.get('Skill 2 Alt', dict())
        info['sk2ajp'] =        sk2a_raw.get('skill_name', None)
        info['sk2a'] =          sk2a_raw.get('description', None)
        info['sk2aaction'] =    sk2a_raw.get('actions', [None])

        info['im'] =            'https://redive.estertion.win/icon/unit/{}31.webp'.format(info['hnote_id'])
        info['im6'] =           'https://redive.estertion.win/icon/unit/{}61.webp'.format(info['hnote_id']) if 'flb' in info['tag'] else None
        info['ue_im'] =         'https://redive.estertion.win/icon/equipment/{}.webp'.format(info['ue']['ue_id']) if info['ue'].get('ue_id', None) != None else None

        #print(f"Fetch JSON data - {(time.perf_counter()-t0)*1000}ms")
        await self.logger.send(f"target: {info['en']} {info['jp']} {info['hnote_id']}")
        return info

    @commands.command(
        usage="character [name] [*option|optional]",
        aliases=['c','ue','chara', 'card', 'pic', 'stats'],
        help="Have Ames fetch data on the specified character"
    )
    async def character(self, ctx, *request):
        channel = ctx.channel
        author = ctx.message.author

        # checks
        if not self.client.command_status['chara'] == 1:
            raise commands.DisabledCommand
        elif len(request) == 0:
            await channel.send(self.error()['no_input'])
            return
        
        # uniform case
        request = [i.lower() for i in request]

        if request[0] == 'help':
            await channel.send(self.full_help)
            return
        
        # preprocess the command to find what out what the request is
        mode, request, option = await self.process_request(ctx, request, channel)
        # request here should be a string

        # validate request
        search_sucess, request = self.validate_entry(request)
        if not search_sucess:
            await channel.send(self.error()['search_fail'])
            return 

        # establish a db connection
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name, "DB connection failed")
            return

        # fetch the raw data and then TL data
        try:
            info = await self.fetch_data_kai(request, conn)
        except Exception as e:
            await self.logger.send(self.name, e)
            await channel.send("Failed to acquire data")
            self.db.release(conn)
            return
        if info == False:
            await channel.send('Failed to acquire data ' + self.client.emotes['sarens'])
            self.db.release(conn)
            return
        
        # construct embeds
        embed_controller = self.chara_page_controller(info, mode, option, self)

        reactions = ['<:_chara:677763373739409436>', '<:_ue:677763400713109504>', '<:_card:677763353069879306>', '<:_stats:678081583995158538>'] 
        if 'flb' in info['tag']:
            reactions.append('⭐')
        if info['sk1a'] != None or info['sk2a'] != None:
            reactions.append('\U0001F500')

        # make the first message
        page = await channel.send(embed=embed_controller.first_page())
        for react in reactions:
            await page.add_reaction(react)
        

        def author_check(reaction, user):
            return str(user.id) == str(author.id) and str(reaction.emoji) in reactions and str(reaction.message.id) == str(page.id)
        
        # release the connection 
        self.db.release(conn)

        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
            except asyncio.TimeoutError:
                await page.add_reaction('\U0001f6d1')
                return
            else:
                emote_check = str(reaction.emoji)
                await reaction.message.remove_reaction(reaction.emoji, user)
                if emote_check in reactions:
                    if emote_check == '<:_chara:677763373739409436>':
                        toggle = 'chara'
                    elif emote_check == '<:_stats:678081583995158538>':
                        toggle = 'stats'
                    elif emote_check == '<:_ue:677763400713109504>':
                        toggle = 'ue'
                    elif emote_check == '<:_card:677763353069879306>':
                        toggle = 'card'
                    elif emote_check == '⭐':
                        toggle = 'flb'
                    elif emote_check == '\U0001F500':
                        toggle = 'alt'
                    await reaction.message.edit(embed=embed_controller.toggle(toggle))
    
    # page controller
    # controls what the buttons do on the bottom of an embed
    # should only return the correct embed
    class chara_page_controller():
        def __init__(self, info, mode, option, cog):
            self.cog = cog
            self.pages_title = ["<:_chara:677763373739409436> Chara", "<:_ue:677763400713109504> UnqEq", "<:_card:677763353069879306> Card", "<:_stats:678081583995158538> Stats"]
            self.page_icons = []

            self.chara_pages =  []
            self.ue_pages =     []
            self.card_pages =   []
            self.stats_pages =  []
            self.alt_mode =     False
            self.flb_mode =     False
            self.current_page = None

            self.info = info
            self.mode = mode
            self.option = option

            self._make_embeds()
        
        def _make_embeds(self):
            # standard
            self.chara_pages.append(self.cog.make_embed_chara(self.info, self.pages_title.copy()))
            self.ue_pages.append(self.cog.make_embed_ue(self.info, self.pages_title.copy()))
            self.card_pages.append(self.cog.make_embed_card(self.info, self.pages_title.copy()))
            self.stats_pages.append(self.cog.make_embed_stats(self.info, self.pages_title.copy()))

            # flb
            if 'flb' in self.info['tag']:
                self.chara_pages.append(self.cog.make_embed_chara(self.info, self.pages_title.copy(), 'flb'))
                self.stats_pages.append(self.cog.make_embed_stats(self.info, self.pages_title.copy(), 'flb'))
                self.card_pages.append(self.cog.make_embed_card(self.info, self.pages_title.copy(), 'flb'))
            
            # alt
            if 'alt' in self.info['tag']:
                self.chara_alt = self.cog.make_embed_chara(self.info, self.pages_title.copy(), 'alt')
                self.stats_alt = self.cog.make_embed_stats(self.info, self.pages_title.copy(), 'alt')
        
        def first_page(self):
            if self.mode == 'ue':
                self.current_page = 'ue'
                return self.ue_pages[0]

            elif self.mode == 'card':
                self.current_page = 'card'
                if self.option == 'flb' and self.option in self.info['tag']:
                    self.flb_mode = True
                    return self.card_pages[1]
                return self.card_pages[0]

            elif self.mode == 'stats':
                self.current_page = 'stats'
                if self.option == 'flb' and self.option in self.info['tag']:
                    self.flb_mode = True
                    return self.stats_pages[1]
                return self.stats_pages[0]

            else:
                self.current_page = 'chara'
                if self.option == 'flb' and self.option in self.info['tag']:
                    self.flb_mode = True
                    return self.chara_pages[1]
                return self.chara_pages[0]
        
        def toggle(self, mode):
            if mode == 'ue':
                self.current_page = 'ue'
                if self.flb_mode:
                    return self.ue_pages[1]
                return self.ue_pages[0]

            elif mode == 'card':
                self.current_page = 'card'
                if self.flb_mode:
                    return self.card_pages[1]
                return self.card_pages[0]

            elif mode == 'stats':
                self.current_page = 'stats'
                if self.alt_mode:
                    return self.stats_alt
                if self.flb_mode:
                    return self.stats_pages[1]
                return self.stats_pages[0]

            elif mode == 'alt':
                self.alt_mode = not self.alt_mode
                return self.toggle(self.current_page)
            
            elif mode == 'flb':
                self.flb_mode = not self.flb_mode
                return self.toggle(self.current_page)
        
            else:
                self.current_page = 'chara'
                if self.alt_mode:
                    return self.chara_alt
                if self.flb_mode:
                    return self.chara_pages[1]
                return self.chara_pages[0]

    # make chara
    def make_embed_chara(self, info, section_title, option=None):
        section_title[section_title.index("<:_chara:677763373739409436> Chara")] = "<:_chara:677763373739409436> **[Chara]**"
        
        if option == 'flb':
            title = f"{info['jp']} 6⭐\n{info['en']} FLB"
        elif option == 'alt':
            title = f"{info['jp']}\n{self.client.get_full_name(info['en'])} (Special Mode)"
        else:
            title = f"{info['jp']}\n{self.client.get_full_name(info['en'])}"

        embed = discord.Embed(
            title=title,
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=info['im6'] if option == 'flb' else info['im'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Info Page | Ames Re:Re:Write',icon_url=info['im6'] if option == 'flb' else info['im'])

        # page section
        embed.add_field(
            name='Section',
            value=' - '.join(section_title),
            inline=False
        )

        # comment
        embed.add_field(
            name="Comment",
            value=f"{info['cm']}",
            inline=False
        )

        embed.add_field(
            name="> **Attack Pattern**",
            value="Initial:\nLooping:",
            inline=True
        )
        embed.add_field(
            name=SPACE,
            value=self.get_attack_pattern(info),
            inline=True
        )

        # UB
        embed.add_field(
            name=   "> **Union Burst+**" if option == 'flb' else "> **Union Burst**",
            value=  f"「{info.get('ub2jp','soon:tm:')}」" if option == 'flb' else 
                    f"「{info.get('ubjp','soon:tm:')}」",
            inline= False
        )
        embed.add_field(
            name=   "Description",
            value=  f"{info['ub2']}" if option == 'flb' else 
                    f"{info['ub']}",
            inline= True
        )
        embed.add_field(
            name=   SPACE,
            value=  f"{info['ub2tl']}" if option == 'flb' else 
                    f"{info['ubtl']}",
            inline= True
        )

        # Skill 1
        #print(info['sk1atl'], type(info['sk1atl']))
        if option == 'alt' and info['sk1a'] != None:
            embed.add_field(
                name=   "> **Skill 1 Special**",
                value=  f"「{info.get('sk1ajp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk1a']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info['sk1atl']}",
                inline= True
            )
        elif option != 'flb':
            embed.add_field(
                name=   "> **Skill 1**",
                value=  f"「{info.get('sk1jp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk1']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info['sk1tl']}",
                inline= True
            )
        
        # Skill 1 +
        if 'ue' in info['tag']:
            embed.add_field(
                name=   "> **Skill 1+**",
                value=  f"「{info.get('sk1pjp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info.get('sk1p','なし')}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info.get('sk1ptl','This character does not have an UE')}",
                inline= True
            )

        # Skill 2
        if option == 'alt' and info['sk2a'] != None:
            embed.add_field(
                name=   "> **Skill 2 Special**",
                value=  f"「{info.get('sk2ajp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk2a']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info['sk2atl']}",
                inline= True
            )
        elif option != 'alt' or info['sk2a'] == None:
            embed.add_field(
                name=   "> **Skill 2**",
                value=  f"「{info.get('sk2jp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk2']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info['sk2tl']}",
                inline= True
            )

        # Tags
        embed.add_field(
            name="> Tags",
            value=', '.join(info['tag']),
            inline=False
        )

        # Aliases
        falias = [key for key, value in list(self.full_alias.items()) if value.lower() == info['en'].lower()]
        embed.add_field(
            name="> Aliases",
            value=", ".join(falias) if len(falias)!= 0 else "None",
            inline=False
        )
        return embed

    # make ue
    def make_embed_ue(self, info, section_title):
        section_title[section_title.index("<:_ue:677763400713109504> UnqEq")] = "<:_ue:677763400713109504> **[UnqEq]**"

        embed = discord.Embed(
            title="No Data",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour)
        embed.set_footer(text='Unique Equipment Page | Ames Re:Re:Write',icon_url=info['im'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.add_field(
            name='Section',
            value=' - '.join(section_title),
            inline=False
        )

        # complete the section if chara actually have ue
        if 'ue' in info['tag']:
            embed.title=        f"{info['ue']['ue_name']}\n{info['ue_en']}"
            embed.description=  f"{self.client.get_full_name(info['en'])}\'s unique equipment."
            embed.set_thumbnail(url=info['ue_im'])

            # RANK
            embed.add_field(
                name="> **Rank**",
                value=f"{info['ue_rank']}",
                inline=False
            )
            embed.add_field(
                name="> **UE Stats**",
                value=f"Base/Max (lv{info['max_ue']})",
                inline=False
            )

            # STATS
            for field, value in list(info['ue'].items()):
                if field in list(self.config['ue_abbrev'].keys()):
                    #print(info['ue'])
                    try:
                        final_val = round(float(value) + float(info['ue'][f"{field.lower()}_growth"]) * (info['max_ue']-1))
                    except:
                        final_val = round(float(value) + float(info['ue'].get(f"{field}_growth",0)) * (info['max_ue']-1))
                        if info['ue'].get(f"{field}_growth",0) == 0:
                            print(f"ue - {field} growth stat is 0 or not found: {info['en']}")

                    embed.add_field(
                        name=self.config['ue_abbrev'][field],
                        value=f"{value}/{final_val}",
                        inline=True
                    )
            

            # Skill 1
            embed.add_field(
                name=   "> **Skill 1**",
                value=  f"「{info.get('sk1jp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk1']}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info['sk1tl']}",
                inline= True
            )
            
            # Skill 1 +
            embed.add_field(
                name=   "> **Skill 1+**",
                value=  f"「{info.get('sk1pjp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info.get('sk1p','なし')}",
                inline= True
            )
            embed.add_field(
                name=   SPACE,
                value=  f"{info.get('sk1ptl','This character does not have an UE')}",
                inline= True
            )
        else:
            embed.description=  f"{self.client.get_full_name(info['en'])} does not have an unique equipment."
            embed.set_thumbnail(url='https://redive.estertion.win/icon/equipment/999999.webp')
        
        return embed        

    # make stats
    def make_embed_stats(self, info, section_title, option=None):
        section_title[section_title.index("<:_stats:678081583995158538> Stats")] = "<:_stats:678081583995158538> **[Stats]**"

        embed = discord.Embed(
            title="Page Unavailable",
            description=f"{self.client.get_full_name(info['en'])}\'s stats page is not available at the moment.",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=info['im6'] if option == 'flb' else info['im'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Stats Page | Ames Re:Re:Write',icon_url=info['im6'] if option == 'flb' else info['im'])

        embed.add_field(
            name='Section',
            value=' - '.join(section_title),
            inline=False
        )

        #if info != None:
        embed.title = "Statistics"
        embed.description = f"{self.client.get_full_name(info['en'])}\'s skill and misc stats. All stats assumes **LV{info['max_lvl']}** **RANK{info['max_rk']}** with **MAX BOND** across all character variants. `Disclaimer: This page is a WIP and displayed stats may be inaccurate`"

        for chunk in self.client.chunks(list(info['stats'].items()), 6):
            embed.add_field(
                name=f"Stats",
                value="\n".join([f"{self.config['ue_abbrev'].get(key, key.upper())}: {arg}" for key, arg in chunk])
            )

        """
        pattern = []
        if len(sk_info['cyc'][0]) != 0:
            pattern.append("Opening\n" + " -> ".join([f"Sk{num+1}" if num != -1 else "Atk" for num in sk_info['cyc'][0]]))
        if len(sk_info['cyc'][1]) != 0:
            pattern.append("Loop\n" + " -> ".join([f"Sk{num+1}" if num != -1 else "Atk" for num in sk_info['cyc'][1]]))

        embed.add_field(
            name="Attack Pattern",
            value="\n".join(pattern),
            inline=False
        )

        embed.add_field(
            name="Strengths and Weaknesses",
            value=f"```diff{sk_info['pro'] if sk_info['pro'] != None else ''} {sk_info['con'] if sk_info != None else ''}```",
            inline=False
        )
        """

        embed.add_field(
            name="> **Attack Pattern**",
            value="Initial:\nLooping:",
            inline=True
        )
        embed.add_field(
            name=SPACE,
            value=self.get_attack_pattern(info),
            inline=True
        )

        # UB
        embed.add_field(
            name=   "> **Union Burst+**" if option == 'flb' else "> **Union Burst**",
            value=  f"「{info.get('ub2jp','soon:tm:')}」" if option == 'flb' else 
                    f"「{info.get('ubjp','soon:tm:')}」",
            inline= False
        )
        embed.add_field(
            name=   'Description',
            value=  f"{info['ub2tl']}" if option == 'flb' else 
                    f"{info['ubtl']}",
            inline= True
        )
        embed.add_field(
            name=   'Effect',
            value=  "```glsl\n-{}```".format('\n-'.join(info['ub2action'])) if option == 'flb' else
                    "```glsl\n-{}```".format('\n-'.join(info['ubaction'])),
            inline= True
        )

        # Skill 1
        if option != 'flb':
            if option == 'alt' and info['sk1ajp'] != None:
                embed.add_field(
                    name=   "> **Skill 1 Special**",
                    value=  f"「{info.get('sk1ajp','soon:tm:')}」",
                    inline= False
                )
                embed.add_field(
                    name=   "Description",
                    value=  f"{info['sk1atl']}",
                    inline= True
                )
                embed.add_field(
                    name=   "Effect",
                    value=  "```glsl\n-{}```".format('\n-'.join(info['sk1aaction'])),
                    inline= True
                )
            else:
                embed.add_field(
                name=   f"> **Skill 1**",
                value=  f"「{info.get('sk1jp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk1tl']}",
                inline= True
            )
            embed.add_field(
                name=   "Effect",
                value=  "```glsl\n-{}```".format('\n-'.join(info['sk1action'])),
                inline= True
            )
        
        # Skill 1+
        if 'ue' in info['tag']:
            embed.add_field(
                name=   "> **Skill 1+**",
                value=  f"「{info.get('sk1pjp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info.get('sk1ptl','This character does not have an UE')}",
                inline= True
            )
            embed.add_field(
                name=   "Effect",
                value=  "```glsl\n-{}```".format('\n-'.join(info.get('sk1paction','N/A'))),
                inline= True
            )

        # Skill 2
        if option == 'alt' and info['sk2ajp'] != None:
            embed.add_field(
                name=   "> **Skill 2 Special**",
                value=  f"「{info.get('sk2ajp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk2atl']}",
                inline= True
            )
            embed.add_field(
                name=   "Effect",
                value=  "```glsl\n-{}```".format('\n-'.join(info['sk2aaction'])),
                inline= True
            )
        else:
            embed.add_field(
                name=   "> **Skill 2**",
                value=  f"「{info.get('sk2jp','soon:tm:')}」",
                inline= False
            )
            embed.add_field(
                name=   "Description",
                value=  f"{info['sk2tl']}",
                inline= True
            )
            embed.add_field(
                name=   "Effect",
                value=  "```glsl\n-{}```".format('\n-'.join(info['sk2action'])),
                inline= True
            )

        return embed   

    # make card
    def make_embed_card(self, info, section_title, option=None):
        section_title[section_title.index('<:_card:677763353069879306> Card')] = '<:_card:677763353069879306> **[Card]**'

        embed = discord.Embed(
            description=f"{self.client.get_full_name(info['en'])}'s card is currently unavailable {self.client.emotes['dead']}",
            title="Card unavailble",
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_thumbnail(url=info['im'] if option == None else info['im6'])
        embed.set_footer(text='Unit Card Page | Ames Re:Re:Write',icon_url=info['im'] if option == None else info['im6'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.add_field(
            name='Section',
            value=' - '.join(section_title),
            inline=False
        )
        #print(info['hnote_id'], type(info['hnote_id']))
        if info['hnote_id'] != 'None':
            embed.title = "Unit Card"
            if option == None:
                embed.description = f"{self.client.get_full_name(info['en'])}'s card."
                link = f"https://redive.estertion.win/card/full/{info['hnote_id'][:4]}31.webp"
            else:
                embed.description = f"{self.client.get_full_name(info['en'])}'s FLB (6:star:) card."
                link = f"https://redive.estertion.win/card/full/{info['hnote_id'][:4]}61.webp"

            embed.set_image(url=link)
        
        return embed

    # position finder
    @commands.command(
        usage='.pos [option]',
        help="Enter a [name] to have Ames fetch the relative position of the specified character. "\
            "Otherwise, use either [v(anguard)], [m(idguard)] or [r(earguard)] to list their respective lineup.",
        aliases=['pos']
    )
    async def position(self, ctx, *request):
        channel = ctx.channel
        if not self.client.command_status['pos'] == 1:
            raise commands.DisabledCommand 

        # checks 
        if len(request) == 0:
            await channel.send(self.error()['pos_fail'])
            return
        
        # case uniformity
        request = [i.lower() for i in request]

        # DB
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return

        # check if input is a character
        mode, request, option = await self.process_request(ctx, request, channel, False)
        del mode, option

        search_success, _request = self.validate_entry(request)

        if not search_success:
            try:
                first_letter = request[0].lower()

                if first_letter in ['v', 'f']:
                    request = 'front'
                elif first_letter in ['m']:
                    request = 'mid'
                elif first_letter in ['r']:
                    request = 'rear'
                else:
                    request = None
            except:
                request = None
        else:
            request = _request
        
        if not search_success and request == None:
            await channel.send(self.error()['pos_fail'])
            return
        
        # fetch lineup
        cursor = conn.cursor()
        if search_success:
            # get name and tag
            query = (f"SELECT unit_name_eng, tag FROM hatsune_bot.charadata WHERE unit_id = {request['id']}")
            cursor.execute(query)
            for en, tag in cursor:
                name = str(en)
                tags = str(tag).split(', ')
                if 'front' in tags:
                    request = 'front'
                elif 'mid' in tags:
                    request = 'mid'
                else:
                    request = 'rear'
        else:
            name = None

        lineup = []
        query = (f"SELECT unit_name_eng, pos FROM hatsune_bot.charadata WHERE tag LIKE '%{request}%' ORDER BY pos ASC")
        cursor.execute(query)

        for i, (en, pos) in enumerate(cursor):
            if pos == None:
                index = '??'
            else:
                index = i+1
            
            if en == name:
                lineup.append(f"> **{self.client.team.get(en.lower(), 'X')} {index} {self.client.get_full_name(en)}**")
            else:
                lineup.append(f"{self.client.team.get(en.lower(), 'X')} {index} {self.client.get_full_name(en)}")
        
        cursor.close()

        ranks = {'front':'vanguard', 'mid':'midguard', 'rear':'rearguard'}
        embed = discord.Embed(
            title=          "Lineup",
            description=    f"Listing **{ranks[request].upper()}** lineup with character closest to enemy at pos `1`." if not search_success else 
                            f"Listing **{ranks[request].upper()}** lineup with character closest to enemy at pos `1`. Bolding **{self.client.get_full_name(name).upper()}**'s position.",
            timestamp=      datetime.datetime.utcnow(),
            colour=         self.colour
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Field Positions | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)

        for chk in list(self.client.chunks(lineup,20)):
            embed.add_field(
                name="Character",
                value="\n".join(chk),
                inline=True
            )
        
        await channel.send(embed=embed)
        self.db.release(conn)
        return

    # tag searcher/fetcher
    @commands.command(
        usage='.tag [*option]',
        help='Enter tags to search all characters that qualify. Alternatively, search a character to return their tags.'
    )
    async def tag(self, ctx, *request):
        channel = ctx.channel

        if not self.client.command_status['tag'] == 1:
            raise commands.DisabledCommand
        
        # checks 
        if len(request) == 0:
            await channel.send("There was no input. Use `.help tag` if you're stuck.")
            return 
        
        # case uniformity
        request = [i.lower() for i in request]

        # DB
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return

        mode, _request, option = await self.process_request(ctx, request, channel, False)
        search_success, _request = self.validate_entry(_request)
        if search_success:
            await channel.send(embed=await self.tag_chara(conn, _request, option))
        else:
            for tag in request:
                if not tag in (list(self.tag_definitions['basic'].keys()) + list((self.tag_definitions['atk'].keys())) + list(self.tag_definitions['buff'].keys())):
                    await channel.send(f"Unknown tag `{tag}`")
                    self.db.release(conn)
                    return
            await channel.send(embed=self.tag_search(conn, request))
        
        self.db.release(conn)
 
    async def tag_chara(self, conn, request, option):
        info = await self.fetch_data_kai(request, conn)
        embed = discord.Embed(
            title=          "Tag Search",
            description=    f"Listing **{self.client.get_full_name(info['en'])}**'s tags.",
            timestamp=      datetime.datetime.utcnow(),
            colour=         self.colour
        )
        embed.set_thumbnail(url=info['im6'] if option == 'flb' else info['im'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Search | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Tags",
            value=" ".join([f"`{tag}`" for tag in info['tag']])
        )
        return embed

    def tag_search(self, conn, request):
        join = " and tag like ".join([f"'%{tag}%'" for tag in request])
        query = ("SELECT unit_name_eng FROM hatsune_bot.charadata WHERE tag like "+join+" ORDER BY unit_name_eng")
        cursor = conn.cursor(buffered=True)
        cursor.execute(query)
        charas = []
        for en in cursor:
            charas.append(str(en[0]))

        charas = list(zip(charas, [self.client.get_full_name(en) for en in charas]))
        charas.sort(key=lambda x: x[1])

        cursor.close()
        embed = discord.Embed(
            title=          "Tag Search",
            description=    f"Found `{len(charas)}` characters with tags corresponding to `{' '.join(request)}`.",
            timestamp=      datetime.datetime.utcnow(),
            colour=         self.colour
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Search | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        for names in list(self.client.chunks(charas,20)):
            embed.add_field(
                name="Characters",
                value="\n".join([f"{self.client.team.get(en.lower(),':question:')} {full_en}" for en, full_en in names]),
                inline=True
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

def setup(client):
    client.add_cog(hatsuneCog(client))