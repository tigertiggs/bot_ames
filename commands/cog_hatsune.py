import datetime
import discord
from discord.ext import commands
import asyncio, os, ast
dir = os.path.dirname(__file__)

MAX_LEVEL = 140
SPACE = '\u200B'

class hatsuneCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.logger =   client.log
        self.name =     '[Hatsune]'

        self.db =       client.database
        self.emj =      client.emj
        #self.active =   client.get_config('hatsune')

        self.help =     "\nIn case you forgot, the prefixes are:\n"\
                        "`n` for New year i.e. `nrei`\n"\
                        "`x` for Christmas i.e. `xayane`\n"\
                        "`o` for Ouedo i.e. `oninon`\n"\
                        "`v` for Valentines i.e. `vshizuru`\n"\
                        "`s` for Summer i.e. `sio`\n"\
                        "`h` for Halloween i.e. `hmiyako`\n"\
                        "`u` for Uniform i.e. `uaoi`"
        self.options =  ['flb']
        with open(os.path.join(dir,'_config/alias.txt')) as af:
            self.preprocessor = ast.literal_eval(af.read())
    
    async def active_check(self, channel):
        if self.client.get_config('hatsune') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    def chunks(self, l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n] 
    
    def error(self):
        error_msg = dict()
        error_msg['no_input'] =     'There was no input'+self.help
        error_msg['search_fail'] =  'Did not find character'+self.help
        error_msg['conn_fail'] =    'Failed to connect to database!'
        error_msg['pos_fail'] =     'Invalid input! Use `v` for vanguard, `m` for midguard or `r` for rearguard. '\
                                    'Alternatively enter a character name to find their positioning.'
        return error_msg

    async def process_input(self, request, channel):
        processed = []
        option = request[-1]
        deprec = ['ue', 'mlb']
        if option not in self.options:
            if option in deprec:
                await channel.send(f'Warning: option `{option}` has depreciated! See `.help` for more details.')
                request = request[:-1]
                if option == 'mlb':
                    option = 'flb'
                else:
                    option = None
        else:
            request = request[:-1]
        for arg in request:
            processed.append(self.preprocessor.get(arg, arg).lower())
        return "".join(processed), option
    
    def get_full_name(self, target):
        if len(target) > 1:
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
        else:
            prefix = target.lower()
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
            return prefix
    
    def fetch_list(self, conn):
        chara_list, chara_list_jp, id_list = [], [], []
        cursor = conn.cursor()
        query = ("SELECT unit_id, unit_name_eng , unit_name "
                "FROM hatsune_bot.charadata")
        cursor.execute(query)
        for (id, name, name_jp) in cursor:
            chara_list.append(str(name).lower())
            chara_list_jp.append(str(name_jp))
            id_list.append(str(id))
        cursor.close()
        return chara_list, chara_list_jp, id_list
    
    def fetch_data(self, id, conn):
        # fetch all data except skill names
        query = ("SELECT "
                "hc.unit_name, hc.unit_name_eng, " 
                "image, image_2, "
                "union_burst, ub_trans, "
                "union_burst_2, ub_2_trans, "
                "skill_1, skill_1_translation, "
                "skill_1_plus, skill_1_plus_trans, "
                "skill_2, skill_2_trans, "
                "hd.comment, comment_trans, "
                "tag, "
                "hd.unit_id, "
                "image_link, eq_name, eq_name_trans, eq_rank, "
                "eq_patk, eq_pcrit, eq_matk, eq_mcrit, "
                "eq_tp_up, eq_tp_cost, eq_hp, eq_pdef, eq_mdef, "
                "eq_dodge, eq_accuracy, eq_recovery, eq_auto_heal "
                "FROM hatsune_bot.charadata AS hc LEFT JOIN (hnote.unit_data AS hd JOIN hatsune_bot.charaUE AS hu) "
                "ON hc.unit_name = hd.unit_name AND hu.unit_id = hc.unit_id "
                "WHERE hc.unit_id = {} "
                "ORDER BY hd.unit_id ASC LIMIT 1".format(id)
                )
        cursor = conn.cursor(buffered=True)
        cursor.execute(query)
        info =  dict()
        ue =    dict()
        for (jp, en,
            im, im2, 
            ub, ubtl,
            ub2, ub2tl,
            sk1, sk1tl,
            sk1p, sk1ptl,
            sk2, sk2tl,
            cm, cmtl,
            tag,
            hnid,
            ueim, uejp, ueen, uerank, 
            patk, pcrit, matk, mcrit, 
            tpup, tpcost, hp, pdef, mdef,
            dodge, acc, rec, aheal) in cursor:
        
            info['en'] =        str(en)
            info['jp'] =        str(jp)
            info['im'] =        str(im)     if im != "-" else None
            info['im6'] =       str(im2)    if im != "-" else None
            info['ub'] =        str(ub)
            info['ubtl'] =      str(ubtl)
            info['ub2'] =       str(ub2)    if ub2 != "-" else None 
            info['ub2tl'] =     str(ub2tl)  if ub2tl != "-" else None
            info['sk1'] =       str(sk1)
            info['sk1tl'] =     str(sk1tl)
            info['sk1p'] =      str(sk1p)   if sk1p != "-" else None
            info['sk1ptl'] =    str(sk1ptl) if sk1ptl != "-" else None
            info['sk2'] =       str(sk2)
            info['sk2tl'] =     str(sk2tl)
            info['cm'] =        str(cm).replace('\\n','')
            info['cmtl'] =      str(cmtl).strip()
            info['tag'] =       [c.strip() for c in tag.split(',')]
            info['hnote_id'] =  str(hnid)   if hnid != "-" else None
            info['ue_en'] =     str(ueen)   if ueen != "-" else None
            info['ue_jp'] =     str(uejp)   if uejp != "-" else None
            info['ue_im'] =     str(ueim)   if ueim != "-" else None 
            info['ue_rank'] =   str(uerank) if uerank != "-" else None 

            ue['PATK'] =        str(patk)   if patk != "-" else None
            ue['PCRIT'] =       str(pcrit)  if pcrit != "-" else None
            ue['MATK'] =        str(matk)   if matk != "-" else None
            ue['MCRIT'] =       str(mcrit)  if mcrit != "-" else None
            ue['TP UP'] =       str(tpup)   if tpup != "-" else None
            ue['TP COST'] =     str(tpcost) if tpcost != "-" else None
            ue['HP'] =          str(hp)     if hp != "-" else None
            ue['PDEF'] =        str(pdef)   if pdef != "-" else None
            ue['MDEF'] =        str(mdef)   if mdef != "-" else None
            ue['EVA'] =         str(dodge)  if dodge != "-" else None
            ue['ACC'] =         str(acc)    if acc != "-" else None
            ue['RECV'] =        str(rec)    if rec != "-" else None
            ue['HEAL'] =        str(aheal)  if aheal != "-" else None

            info['ue'] =        ue
        
        # fetch skill names
        prefix =    info.get('hnote_id','000000')[:4]
        ub =        '001'
        sk1 =       '002'
        sk2 =       '003'
        sk1p =      '012'
        query =     ("SELECT skill_id, name FROM hnote.skill_data "
                    "WHERE skill_id REGEXP '{}...'".format(prefix))

        cursor.execute(query)
        for id, sk in cursor:
            suffix = str(id)[-3:]
            if suffix == ub:
                info['ubjp'] = str(sk)
            elif suffix == sk1:
                info['sk1jp'] = str(sk)
            elif suffix == sk2:
                info['sk2jp'] = str(sk)
            elif suffix == sk1p:
                info['sk1pjp'] = str(sk)
        
        cursor.close()
        return info

    @commands.command(
        usage = '.chara [name] [*options]', 
        aliases=['c','ue'],
        help='Have Ames fetch information on the specified character. Options include: flb'
        )
    async def character(self, ctx, *request):
        channel = ctx.channel
        author = ctx.message.author
        request = [i.lower() for i in request]
        #print(request)
        # check if command is enabled
        check = await self.active_check(channel)
        if not check:
            return

        # fetch pointer and check if its connected
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return
        
        # preprocess the args - check for aliases
        target, option = await self.process_input(request,channel)

        # fetch the character lists to check if target is in them
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        if not target in c_list and not target in c_jp_list:
            await channel.send(self.error()['search_fail'])
            await self.logger.send(self.name, 'failed to find', target)
            return 
        elif target in c_list:
            target_id = id_list[c_list.index(target)]
        else:
            target_id = id_list[c_jp_list.index(target)]
        
        # fetch all information
        print(target_id)
        info = self.fetch_data(target_id, conn)
        self.db.release(conn)

        # construct pages
        pages_title = ['Chara','UE', 'Stats']
        pages = []
        chara_p = [self.make_chara(info, None, pages_title.copy())]
        if 'flb' in info['tag']:
            chara_p.append(self.make_chara(info, 'flb', pages_title.copy()))
        else:
            chara_p.append(None)

        pages.append(chara_p)
        pages.append([self.make_ue(info, pages_title.copy())]*2)

        # check display page
        if ctx.invoked_with == 'ue':
            front = 'UE'
        else:
            front = 'Chara'

        # display
        if option == 'flb' and option in info['tag']:
            flbmode = -1
        else:
            flbmode = 0

        if front == 'Chara':
            page = await channel.send(embed=pages[0][flbmode])
        else:
            page = await channel.send(embed=pages[1][flbmode])
        
        reactions = ['⬅','➡','⭐'] if 'flb' in info['tag'] else ['⬅','➡']
        for arrow in reactions:
            await page.add_reaction(arrow)

        # def check
        def author_check(reaction, user):
            return str(user.id) == str(author.id) and\
                reaction.emoji in reactions and\
                str(reaction.message.id) == str(page.id)
        
        # wait
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=author_check)
            except asyncio.TimeoutError:
                for arrow in reactions:
                    await page.remove_reaction(arrow, self.client.user)
                break
            else:
                if reaction.emoji == '⬅':
                    pages = pages[-1:] + pages[:-1]
                    await reaction.message.remove_reaction('⬅', user)
                    await reaction.message.edit(embed=pages[0][flbmode])

                elif reaction.emoji == '➡':
                    pages = pages[1:] + pages[:1]
                    await reaction.message.remove_reaction('➡', user)
                    await reaction.message.edit(embed=pages[0][flbmode])

                elif reaction.emoji == '⭐':
                    flbmode = ~flbmode
                    await reaction.message.remove_reaction('⭐', user)
                    await reaction.message.edit(embed=pages[0][flbmode])

                else:
                    continue

    def make_chara(self, info, option, ph):
        ph[ph.index('Chara')] = '**[Chara]**'

        embed = discord.Embed(
            title=f"{info['jp']}\n{self.get_full_name(info['en'])}" if option == None else f"{info['jp']} 6⭐\n{info['en']} FLB",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=info['im'] if option == None else info['im6'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Character Info Page | SHIN Ames',icon_url=info['im6'] if option == 'flb' else info['im'])

        # page section
        embed.add_field(
            name='Section',
            value=' - '.join(ph),
            inline=False
        )

        # comment
        embed.add_field(
            name="Comment",
            value=f"{info['cm']}",
            inline=False
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
        if option != 'flb':
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

        # Skill 2
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
        return embed
    
    def make_ue(self, info, ph):
        ph[ph.index('UE')] = '**[UE]**'

        embed = discord.Embed(title="No Data",timestamp=datetime.datetime.utcnow())
        embed.set_footer(text='Unique Equipment Page | SHIN Ames',icon_url=info['im'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.add_field(
            name='Section',
            value=' - '.join(ph),
            inline=False
        )
        if 'ue' in info['tag']:
            embed.title=        f"{info['ue_jp']}\n{info['ue_en']}"
            embed.description=  f"{self.get_full_name(info['en'])}\'s unique equipment."
            embed.set_thumbnail(url=info['ue_im'])

            # RANK
            embed.add_field(
                name="> **Rank**",
                value=f"{info['ue_rank']}",
                inline=False
            )
            embed.add_field(
                name="> **UE Stats**",
                value=f"Base/Max (lv{MAX_LEVEL})",
                inline=False
            )

            # STATS
            for field, value in list(info['ue'].items()):
                if value != None:
                    embed.add_field(
                        name=field,
                        value=value,
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
            embed.description=  f"{self.get_full_name(info['en'])} does not have an unique equipment."
            embed.set_thumbnail(url='https://redive.estertion.win/icon/equipment/999999.webp')
        
        return embed

    @commands.command(
        usage='.pos [option]',
        help="Enter a [name] to have Ames fetch the relative position of the specified character. "\
            "Otherwise, use either [v(anguard)], [m(idguard)] or [r(earguard)] to list their respective positioning."
    )
    async def pos(self, ctx, *request):
        channel = ctx.channel
        request = [i.lower() for i in request]
        # check if command is enabled
        check = await self.active_check(channel)
        if not check:
            return
        
        # fetch pointer and check if its connected
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return
        
        # check if input is a chara
        # preprocess the args - check for aliases
        target = await self.process_input(request,channel)
        target = target[0]

        # fetch the character lists to check if target is in them
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        if target in c_list:
            target_id = id_list[c_list.index(target)]
        elif target in c_jp_list:
            target_id = id_list[c_jp_list.index(target)]
        else:
            target_id = None
        
        # check if 
        if target_id == None:
            pos =   {"v":           "front",
                    "vanguard":     "front",
                    "m":            "mid",
                    "midguard":     "mid",
                    "r":            "rear",
                    "rearguard":    "rear"}
            real =  {"front":       "vanguard",
                    "mid":          "midguard",
                    "rear":         "rearguard"}
            pos = pos.get(request[0], None)
            request = [real[pos]]
        
        # error check
        if target_id == None and pos == None:
            await channel.send(self.error()['pos_fail'])
            return
        
        cursor = conn.cursor()
        if target_id != None:
            # get name and tag
            query = (f"SELECT unit_name_eng, tag FROM hatsune_bot.charadata WHERE unit_id = {target_id}")
            cursor.execute(query)
            for en, tag in cursor:
                name = str(en)
                tags = str(tag).split(', ')
                if 'front' in tags:
                    pos = 'front'
                    request = ['vanguard']
                elif 'mid' in tags:
                    pos = 'mid'
                    request = ['midguard']
                else:
                    pos = 'rear'
                    request = ['rearguard']
        else: 
            name = None
            
        # collect stats
        query = (f"SELECT unit_name_eng, pos FROM hatsune_bot.charadata WHERE tag LIKE '%{pos}%' ORDER BY pos ASC")
        cursor.execute(query)
        names = []
        i = 1
        for en, pos in cursor:
            if pos == None:
                j = '??'
            else:
                j = str(i)
                i += 1

            if target_id != None and en == name:
                    names.append(f"> **{self.client.get_team()[str(en).lower()]} {j} {self.get_full_name(str(en))}**")
            else:
                names.append(f"{self.client.get_team()[str(en).lower()]} {j} {self.get_full_name(str(en))}")

        cursor.close()

        embed = discord.Embed(
            title=          "Lineup",
            description=    f"Listing **{request[0].upper()}** lineup with character closest to enemy at pos `1`." if target_id == None else 
                            f"Listing **{request[0].upper()}** lineup with character closest to enemy at pos `1`. Bolding **{self.get_full_name(name).upper()}**'s position.",
            timestamp=      datetime.datetime.utcnow()
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Field Positions | SHIN Ames',icon_url=self.client.user.avatar_url)

        for chk in list(self.chunks(names,20)):
            embed.add_field(
                name="Character",
                value="\n".join(chk),
                inline=True
            )
        
        await channel.send(embed=embed)
        self.db.release(conn)
        return

    @commands.command(
        usage='.tag [*option]',
        help='Enter tags to search all characters that qualify for those tags. Alternatively, search a character to return their tags.'
    )
    async def tag(self, ctx, *request):
        channel = ctx.channel
        request = [i.lower() for i in request]
        # check if command is enabled
        check = await self.active_check(channel)
        if not check:
            return
        
        # fetch pointer and check if its connected
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return
        
        # check if input is a chara
        # preprocess the args - check for aliases
        target, option = await self.process_input(request,channel)

        # fetch the character lists to check if target is in them
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        if target in c_list:
            target_id = id_list[c_list.index(target)]
        elif target in c_jp_list:
            target_id = id_list[c_jp_list.index(target)]
        else:
            target_id = None

        if target_id == None:
            await channel.send(embed=self.tag_search(conn, request))
        else:
            await channel.send(embed=self.tag_chara(conn, target_id, option))
        
        self.db.release(conn)
        
    def tag_chara(self, conn, target_id, option):
        query = (f"SELECT unit_name_eng, tag, image, image_2 FROM hatsune_bot.charadata WHERE unit_id = {target_id}")
        cursor = conn.cursor()
        cursor.execute(query)
        im = dict()
        for en, tag, image, image2 in cursor:
            name =          self.get_full_name(str(en))
            tags =          str(tag).split(", ")
            im['im'] =      str(image)
            im['im6'] =     str(image2)
        cursor.close()
        embed = discord.Embed(
            title=          "Tag Search",
            description=    f"Listing **{name}**'s tags.",
            timestamp=      datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=im['im6'] if option == 'flb' else im['im'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Search | SHIN Ames',icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="Tags",
            value=" ".join([f"`{tag}`" for tag in tags])
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
        cursor.close()
        embed = discord.Embed(
            title=          "Tag Search",
            description=    f"Found `{len(charas)}` characters with tags corresponding to `{' '.join(request)}`.",
            timestamp=      datetime.datetime.utcnow()
        )
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Tag Search | SHIN Ames',icon_url=self.client.user.avatar_url)
        for names in list(self.chunks(charas,20)):
            embed.add_field(
                name="Characters",
                value="\n".join([f"{self.client.get_team()[en.lower()]} {self.get_full_name(en)}" for en in names]),
                inline=True
            )
        return embed
        
    @commands.command(
        usage=".boss [num]",
        help="Have Ames fetch boss data of current CB."
    )
    async def boss(self, ctx, request:int):
        channel = ctx.channel
        author = ctx.message.author
        # check if command is enabled
        check = await self.active_check(channel)
        if not check:
            return
        request = abs(request)
        # read meta
        with open(os.path.join(dir,'data/_meta.txt')) as mf:
            current_bosses = ast.literal_eval(mf.read())['active']
        
        data = []
        for boss in current_bosses:
            try:
                with open(os.path.join(dir,f"data/{boss}.txt"), encoding='utf8') as bf:
                    data.append(ast.literal_eval(bf.read()))
            except Exception as e:
                print(e)
                data.append(None)
        
        bosses = [self.make_boss_embed(boss) if boss != None else None for boss in data]
        
        try:
            if data[request-1] == None:
                await channel.send(f'Failed to load boss {request} data')
                return
        except:
            await channel.send(self.client.emj['ames'])
            return
        else:
            page = await channel.send(embed=bosses[request-1])
        
        reactions = ['1\u20E3','2\u20E3','3\u20E3','4\u20E3','5\u20E3']
        for i, emote in enumerate(reactions):
            if bosses[i] != None:
                await page.add_reaction(emote)
        
        # def check
        def author_check(reaction, user):
            return str(user.id) == str(author.id) and\
                reaction.emoji in reactions and\
                str(reaction.message.id) == str(page.id)
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=author_check)
            except asyncio.TimeoutError:
                for emote in reactions:
                    await page.remove_reaction(emote, self.client.user)
                break
            else:
                if reaction.emoji == '1\u20E3':
                    await reaction.message.remove_reaction('1\u20E3', user)
                    await reaction.message.edit(embed=bosses[0])

                elif reaction.emoji == '2\u20E3':
                    await reaction.message.remove_reaction('2\u20E3', user)
                    await reaction.message.edit(embed=bosses[1])
                
                elif reaction.emoji == '3\u20E3':
                    await reaction.message.remove_reaction('3\u20E3', user)
                    await reaction.message.edit(embed=bosses[2])
                
                elif reaction.emoji == '4\u20E3':
                    await reaction.message.remove_reaction('4\u20E3', user)
                    await reaction.message.edit(embed=bosses[3])
                
                elif reaction.emoji == '5\u20E3':
                    await reaction.message.remove_reaction('5\u20E3', user)
                    await reaction.message.edit(embed=bosses[4])

                else:
                    continue

    def make_boss_embed(self, data):
        embed = discord.Embed(
            title=f"{data['jp']}\n{data['en']}",
            description=data["comment"] if data.get("comment","") is not "" else "No comment as of yet",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=data["im"] if data.get("im","") is not "" else "https://redive.estertion.win/icon/unit/000001.webp")
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Boss Info | SHIN Ames')

        pattern = []
        if len(data['cyc'][0]) != 0:
            pattern.append("Opening\n" + " -> ".join([f"Sk{num+1}" if num != -1 else "Atk" for num in data['cyc'][0]]))
        if len(data['cyc'][1]) != 0:
            pattern.append("Loop\n" + " -> ".join([f"Sk{num+1}" if num != -1 else "Atk" for num in data['cyc'][1]]))

        embed.add_field(
            name="Attack Pattern",
            value="\n".join(pattern),
            inline=False
        )
        embed.add_field(
            name="Targets",
            value=str(data['multi']),
            inline=False
        )
        embed.add_field(
            name="Defense (Phys/Mag)",
            value="\n".join([f"Mode {n}" for n in list(range(1,4))]),
            inline=True
        )
        embed.add_field(
            name=SPACE,
            value="\n".join([f"{phys:,d} / {mag:,d}" for phys, mag in data['def']]),
            inline=True
        )

        embed.add_field(
            name=SPACE,
            value="**Union Burst**",
            inline=False
        )
        embed.add_field(
            name='Description',
            value=data['ub'][0][0],
            inline=True
        )
        embed.add_field(
            name=SPACE,
            value=data['ub'][0][1],
            inline=True
        )

        for i, (jp, en) in enumerate(data['sk']):
            embed.add_field(
                name=SPACE,
                value=f"**Skill {i+1}**",
                inline=False
            )
            embed.add_field(
                name="Description",
                value=jp,
                inline=True
            ),
            embed.add_field(
                name=SPACE,
                value=en,
                inline=True
            )
        """
        for mode in ['1', '2', '3']:
            key = f"mode{mode}"
            embed.add_field(
                name=SPACE,
                value=f"**Mode {mode} Rec. Teams**",
                inline=False
            )
            for setup in data[key]:
                embed.add_field(
                    name=setup['type'].capitalize(),
                    value=" ".join([self.client.team[name.lower()] for name in setup['team']]),
                    inline=True
                )
                
                embed.add_field(
                    name="Type",
                    value=setup['type'].capitalize(),
                    inline=True
                )
                embed.add_field(
                    name="Auto",
                    value="Full Auto" if setup['auto'] == True else 'N/A',
                    inline=True
                )
        """
        embed.add_field(
            name=SPACE,
            value="**Recommended Teams**",
            inline=False
        )
        #P = ":regional_indicator_p:"
        #M = ":regional_indicator_m:"
        A = ":regional_indicator_a:"
        a = ":a:"
        for mode in ['1', '2', '3']:
            key = f"mode{mode}"
            teams = []
            for setup in data[key]:
                meta = []
                """
                if setup['type'] == 'physical':
                    meta.append(P)
                
                else:
                    meta.append(M)
                """
                if setup['auto'] == True:
                    meta.append(A)
                else:
                    meta.append(a)
                teams.append(
                    " ".join(
                        [
                            "".join(meta), 
                            "".join(
                                [self.client.get_team()[name.lower()] for name in setup['team']]
                                )
                        ]
                    )
                )

            embed.add_field(
                name=f"Mode {mode}",
                value="\n".join(teams),
                inline=True
            )

        return embed

    @commands.command(
        usage='.alias [alias|optional]',
        help='No description... yet'
    )
    async def alias(self, ctx, *request):
        channel = ctx.channel
        author = ctx.message.author
        active = await self.active_check(channel)
        if not active:
            return
        with open(os.path.join(dir, '_config/alias.txt')) as af:
            alias_list = list(ast.literal_eval(af.read()).items())
            alias_list.sort(key=lambda x: x[1])

        if len(request) == 0:
            embeds = []
            for chunk in self.chunks(alias_list, 20):
                embeds.append(self.make_alias_embed([item[0] for item in chunk], [item[1] for item in chunk]))
            
            page = await channel.send(embed=embeds[0])
            if len(embeds) < 2:
                return
            else:
                for arrow in ['⬅','➡']:
                    await page.add_reaction(arrow)
                
                def author_check(reaction, user):
                    return str(user.id) == str(author.id) and\
                        reaction.emoji in ['⬅','➡'] and\
                        str(reaction.message.id) == str(page.id)
                
                while True:
                    try:
                        reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=author_check)
                    except asyncio.TimeoutError:
                        for arrow in ['⬅','➡']:
                            await page.remove_reaction(arrow, self.client.user)
                        break
                    else:
                        if reaction.emoji == '⬅':
                            embeds = embeds[-1:] + embeds[:-1]
                            await reaction.message.remove_reaction('⬅', user)
                            await reaction.message.edit(embed=embeds[0])

                        elif reaction.emoji == '➡':
                            embeds = embeds[1:] + embeds[:1]
                            await reaction.message.remove_reaction('➡', user)
                            await reaction.message.edit(embed=embeds[0])

                        else:
                            continue
        else:
            pass
    
    def make_alias_embed(self, alias, pointer):
        embed = discord.Embed(
            title="Alias List",
            description="Lists all current recorded aliases.",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Alias | SHIN Ames", icon_url=self.client.user.avatar_url)
        
        embed.add_field(
            name="Alias",
            value="\n".join(alias),
            inline=True
        )
        embed.add_field(
            name="Character",
            value="\n".join([self.get_full_name(target) for target in pointer])
        )
        return embed
            

def setup(client):
    client.add_cog(hatsuneCog(client))
