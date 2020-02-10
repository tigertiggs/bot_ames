import datetime
import discord
from discord.ext import commands
import asyncio, os, ast, traceback, time, json, requests
from io import BytesIO
dir = os.path.dirname(__file__)

MAX_LEVEL = 140
SPACE = '\u200B'
ue_prop = [
    "hp",
    "atk",
    "matk",
    "def",
    "mdef",
    "pCrit",
    "mCrit",
    "wHpRec",
    "wTpRec",
    "dodge",
    "pPen",
    "mPen",
    "lifesteal",
    "hpRec",
    "tpRec",
    "tpSave",
    "acc"
]

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
                        "`u` for Uniform i.e. `uaoi`\n"\
                        "`m` for Magical Girl i.e. `mshiori`"
        self.options =  ['flb']
        with open(os.path.join(dir, '_config/alias_local.txt')) as alf:
            alocal = ast.literal_eval(alf.read())
        with open(os.path.join(dir,'_config/alias.txt')) as af:
            self.preprocessor = ast.literal_eval(af.read())
            self.preprocessor.update(alocal)
    
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
                    prefix =        'Uniform'
                elif prefix ==  'm':
                    prefix =        'Magical Girl'
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
            elif prefix ==  'm':
                prefix =        'Magical Girl'
            else:
                prefix =        "???"
            return prefix
    
    @commands.command()
    async def updateindex(self, ctx):
        channel = ctx.channel
        conn = self.db.db_pointer.get_connection()

        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return
        
        query = "SELECT unit_id, unit_name, unit_name_eng FROM hatsune_bot.charadata"

        id_list, name_list, nametl_list = [], [], []

        try:
            cursor = conn.cursor()
            cursor.execute(query)
            for uid, name, nametl in cursor:
                id_list.append(uid)
                name_list.append(name.lower())
                nametl_list.append(nametl.lower())
        except Exception as e:
            await channel.send('Failed to update index')
            await self.logger.send('updateindex - ', e)
            self.db.release(conn)
            return
        
        with open(os.path.join(dir, 'data/unit_list/uid.txt'), 'w+') as uf:
            uf.write(str(id_list))
        with open(os.path.join(dir, 'data/unit_list/name.txt'), 'w+') as nf:
            nf.write(str(name_list))
        with open(os.path.join(dir, 'data/unit_list/nametl.txt'), 'w+') as ntf:
            ntf.write(str(nametl_list))
        
        await channel.send('Updated master index')

    # outdated
    """
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
    """

    async def validate_entry(self, target, channel):
        with open(os.path.join(dir,'data/unit_list/name.txt')) as nf:
            jp_list = ast.literal_eval(nf.read())

        with open(os.path.join(dir,'data/unit_list/nametl.txt')) as nf:
            en_list = ast.literal_eval(nf.read())

        with open(os.path.join(dir,'data/unit_list/uid.txt')) as nf:
            id_list = ast.literal_eval(nf.read())
        
        #print(target, type(en_list))

        if not target in jp_list and not target in en_list:
            await channel.send(self.error()['search_fail'])
            await self.logger.send(self.name, 'failed to find', target)
            return False
        elif target in en_list:
            pos = en_list.index(target)
            target_id = id_list[en_list.index(target)]
        else:
            pos = jp_list.index(target)
            target_id = id_list[jp_list.index(target)]
        
        return {'id':target_id, 'en':en_list[pos], 'jp':jp_list[pos]}

    async def fetch_data_kai(self, info, conn):
        global MAX_LEVEL
        #ue = dict()
        #t0 = time.perf_counter()
        query = ("SELECT "
                    "hc.unit_name_eng, ub_trans, ub_2_trans, "
                    "skill_1_translation, skill_1_plus_trans, skill_2_trans, "
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

        for (en, ubtl, ub2tl, sk1tl, sk1ptl, sk2tl, cmtl, tag, ueen, uerank) in cursor:
            info['en'] =            en
            info['ubtl'] =          ubtl
            info['ub2tl'] =         ub2tl
            info['sk1tl'] =         sk1tl
            info['sk1ptl'] =        sk1ptl
            info['sk2tl'] =         sk2tl
            info['cmtl'] =          cmtl
            info['tag'] =           [c.strip() for c in tag.split(',')]
            info['ue_en'] =         ueen
            info['ue_rank'] =       uerank

        #print(f"Fetch TL data - {(time.perf_counter()-t0)*1000}ms")
        #t0 = time.perf_counter()

        name = info['jp']
        with open(os.path.join(dir, '_config/port.txt'), 'r') as pf:
            port = pf.read().strip()
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
        
        MAX_LEVEL =             raw['config']['UE_MAX']
        info['hnote_id'] =      raw['data']['unit_profile']['id']
        info['cm'] =            raw['data']['unit_profile']['comment'].replace('\\n', '')

        # UE
        info['ue'] =            raw['data']['unique_equipment']
        #info['ue_id'] =         ue_raw.gets('ue_id', None)
        #info['ue_jp'] =         ue_raw.gets('ue_name', None)

        # Skills
        sk_raw =                raw['data']['skill_data']
        info['ubjp'] =          sk_raw['Union Burst']['skill_name']
        info['ub'] =            sk_raw['Union Burst']['description']
        info['sk1jp'] =         sk_raw['Skill 1']['skill_name']
        info['sk1'] =           sk_raw['Skill 1']['description']
        info['sk2jp'] =         sk_raw['Skill 2']['skill_name']
        info['sk2'] =           sk_raw['Skill 2']['description']

        ub2_raw =               sk_raw.get('Union Burst+', dict())
        info['ub2jp'] =         ub2_raw.get('skill_name', None)
        info['ub2'] =           ub2_raw.get('description', None)

        sk1p_raw =              sk_raw.get("Skill 1+", dict())
        info['sk1pjp'] =        sk1p_raw.get("skill_name", None)
        info['sk1p'] =          sk1p_raw.get("description", None)

        info['im'] =            'https://redive.estertion.win/icon/unit/{}31.webp'.format(info['hnote_id'])
        info['im6'] =           'https://redive.estertion.win/icon/unit/{}61.webp'.format(info['hnote_id']) if 'flb' in info['tag'] else None
        info['ue_im'] =         'https://redive.estertion.win/icon/equipment/{}.webp'.format(info['ue']['ue_id']) if info['ue'].get('ue_id', None) != None else None

        #print(f"Fetch JSON data - {(time.perf_counter()-t0)*1000}ms")
        #print(f"target: {info['en']} {info['jp']} {info['hnote_id']}")
        return info

    """
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
                "FROM (hatsune_bot.charadata AS hc LEFT JOIN hatsune_bot.charaUE AS hu ON hu.unit_id = hc.unit_id) LEFT JOIN hnote_test.unit_data AS hd "
                "ON hc.unit_name = hd.unit_name "
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
        print(info['hnote_id'])
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

    
    def process_sk(self, ski:dict):
        pski = dict()
        for key, value in list(ski.items()):
            if key == 'pro' or key == 'con':
                if len(value) != 0:
                    if key == 'pro':
                        pski[key] = ''.join(['\n+ ' + reason for reason in value])
                    else:
                        pski[key] = ''.join(['\n- ' + reason for reason in value])
                else:
                    pski[key] = None
            elif key == 'cyc':
                pski[key] = ski[key]
            else:
                pski[key] = self.read_skill(value)
        
        return pski

    def read_skill(self, skills):
        text = []
        for skill in skills:
            typ = skill['type']

            if typ == 'atk':
                aff, pos = skill['tgt'].split('.')
                if pos == 'front':
                    pos = 'frontmost'
                    if aff == 'a':
                        aff = 'ally'
                    else:
                        aff = 'enemy'
                elif pos == 'all' or pos == 'range':
                    if aff == 'a':
                        aff = 'allies'
                    else:
                        aff = 'enemies'

                if pos == 'range':
                    skt = f"> Inflict {skill['dmg']} {'magic' if skill['attr'] == 'mag' else 'physical'} damage on all {aff} in {pos}"
                else:
                    skt = f"> Inflict {skill['dmg']} {'magic' if skill['attr'] == 'mag' else 'physical'} damage on the {pos} {aff}"
                text.append(skt)

            elif typ == 'buff':
                for indiv, strength in list(zip(skill['attr'], skill['str'])):
                    if skill['tgt'] == 'self':
                        skt = f"> Gain {strength if strength != -1 else ''} {self.get_buff(indiv)} {'up' if strength != -1 else ''} for {skill['dur'] if skill['dur'] != -1 else 'TBC'} seconds"
                    elif skill['tgt'] == 'all':
                        skt = f"> Grant {strength if strength != -1 else ''} {self.get_buff(indiv)} {'up' if strength != -1 else ''} for {skill['dur'] if skill['dur'] != -1 else 'TBC'} seconds to all allies"
                    else:
                        skt = 'Unknown Skill'
                    text.append(skt)
            
            elif typ == 'debuff':
                for indiv, strength in list(zip(skill['attr'], skill['str'])):

                    pos = skill['tgt'].split('.')
                    if len(pos) > 1:
                        aff, pos = pos
                        if pos == 'front':
                            pos = 'frontmost'
                            if aff == 'a':
                                aff = 'ally'
                            else:
                                aff = 'enemy'
                        elif pos == 'all' or pos == 'range':
                            if aff == 'a':
                                aff = 'allies'
                            else:
                                aff = 'enemies'
                    
                    if pos == 'self':
                        pass
                    elif pos == 'frontmost':
                        skt = f"> Inflict {strength if strength != -1 else ''} {self.get_buff(indiv)} {'down' if strength != -1 else ''} for {skill['dur'] if skill['dur'] != -1 else 'TBC'} seconds to the frontmost {aff}"
                    elif pos == 'all':
                        skt = f"> Inflict {strength if strength != -1 else ''} {self.get_buff(indiv)} {'down' if strength != -1 else ''} for {skill['dur'] if skill['dur'] != -1 else 'TBC'} seconds to all {aff}"
                    elif pos == 'range':
                        skt = f"> Inflict {strength if strength != -1 else ''} {self.get_buff(indiv)} {'down' if strength != -1 else ''} for {skill['dur'] if skill['dur'] != -1 else 'TBC'} seconds to all {aff} in range"
                    else:
                        skt = 'Unknown Skill'
                    text.append(skt)
                    
            elif typ == 'shield':
                if skill['tgt'] == 'self':
                    skt = 'Incomplete Skill'
                elif skill['tgt'] == 'all':
                    skt = f"> Deploy a {skill['str']} buffer {'physical' if skill['attr'] == 'phys' else 'magic'} nullification shield to all allies for {skill['dur'] if skill['dur'] != -1 else 'TBC'} seconds"
                else:
                    skt = 'Unknown Skill'
                text.append(skt)
            
            else:
                skt = 'Unknown Skill'
                text.append(skt)

        return '\n'.join(text)
            
    def get_buff(self, cd):
        return cd.upper()

    if cd == 'matk':
        return 'magic attack'
    elif cd == 'mdef':
        return 'magic def',
    elif cd == 'pdef':
        return 'physical def'
    else:
        return cd.upper()
    """

    @commands.command(
        usage = '.character [name] [*options]', 
        aliases=['c','ue', 'chara'],
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

        #t0 = time.perf_counter()
        # preprocess the args - check for aliases
        target, option = await self.process_input(request,channel)

        # fetch the character lists to check if target is in them
        """
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        if not target in c_list and not target in c_jp_list:
            await channel.send(self.error()['search_fail'])
            await self.logger.send(self.name, 'failed to find', target)
            return 
        elif target in c_list:
            target_id = id_list[c_list.index(target)]
        else:
            target_id = id_list[c_jp_list.index(target)]
        """

        chara = await self.validate_entry(target, channel)
        if chara == False:
            return
        
        #print(f"Verify input - {(time.perf_counter()-t0)*1000}ms")
        #t0 = time.perf_counter()
        
        # fetch pointer and check if its connected
        #t0 = time.perf_counter()
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return
        
        #print(f"Acquiring connection - {(time.perf_counter()-t0)*1000}ms")
    
        # fetch all information
        #print(target_id)
        #info = self.fetch_data(target_id, conn)
        try:
            info = await self.fetch_data_kai(chara, conn)
        except Exception as e:
            await self.logger.send('chara - ', e)
        if info == False:
            await channel.send('Failed to acquire data ' + self.client.emj['sarens'])
            self.db.release(conn)
            return

        #t0 = time.perf_counter()
        # construct pages
        pages_title = ['Chara','UE', 'Stats', 'Card']
        pages = []
        chara_p = [self.make_chara(info, None, pages_title.copy())]
        #stats_p = [self.make_stats(info, pages_title.copy())]
        cards_p = [self.make_card(info, pages_title.copy())]
        if 'flb' in info['tag']:
            chara_p.append(self.make_chara(info, 'flb', pages_title.copy()))
            #stats_p.append(self.make_stats(info, pages_title.copy(), 'flb'))
            cards_p.append(self.make_card(info, pages_title.copy(), 'flb'))
        else:
            chara_p.append(None)
            #stats_p.append(None)
            cards_p.append(None)

        pages.append(chara_p)
        pages.append([self.make_ue(info, pages_title.copy())]*2)
        #pages.append(stats_p)
        pages.append(cards_p)

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

        #print(f"Ready to send - {(time.perf_counter()-t0)*1000}ms")
        #t0 = time.perf_counter()

        if front == 'Chara':
            page = await channel.send(embed=pages[0][flbmode])
        else:
            page = await channel.send(embed=pages[1][flbmode])
        
        self.db.release(conn)
        
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
        if not 'soon' in info.get('sk1ptl', None):
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
    
    def ue_abbrev(self, abbr):
        #abbr = abbr.lower()
        if abbr ==      'hp':
            return              'HP'
        elif abbr ==    'atk':
            return              'PHYS ATK'
        elif abbr ==    'matk':
            return              'MAG ATK'
        elif abbr ==    'def':
            return              'PHYS DEF'
        elif abbr ==    'mdef':
            return              'MAG DEF'
        elif abbr ==    'pCrit':
            return              'PHYS CRIT'
        elif abbr ==    'mCrit':
            return              'MAG CRIT'
        elif abbr ==    'wHpRec':
            return              'HP RECV (p/wave)'
        elif abbr ==    'wTpRec':
            return              'TP RECV (p/wave)'
        elif abbr ==    'dodge':
            return              'DODGE'
        elif abbr ==    'pPen':
            return              'PHYS PENETRATION'
        elif abbr ==    'mPen':
            return              'MAG PENETRATION'
        elif abbr ==    'lifesteal':
            return              'HP STEAL'
        elif abbr ==    'hpRec':
            return              'HP RECV'
        elif abbr ==    'tpRec':
            return              'TP RECV'
        elif abbr ==    'tpSave':
            return              'UB EFFCY'
        elif abbr ==    'acc':
            return              'ACCURACY'
        else:
            return      abbr.upper()

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
            embed.title=        f"{info['ue']['ue_name']}\n{info['ue_en']}"
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
                if field in ue_prop:
                    #print(info['ue'])
                    try:
                        final_val = round(float(value) + float(info['ue'][f"{field.lower()}_growth"]) * (MAX_LEVEL-1))
                    except:
                        final_val = round(float(value) + float(info['ue'].get(f"{field}_growth",0)) * (MAX_LEVEL-1))
                        if info['ue'].get(f"{field}_growth",0) == 0:
                            print(f"ue - {field} growth stat is 0 or not found: {info['en']}")

                    embed.add_field(
                        name=self.ue_abbrev(field),
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
            embed.description=  f"{self.get_full_name(info['en'])} does not have an unique equipment."
            embed.set_thumbnail(url='https://redive.estertion.win/icon/equipment/999999.webp')
        
        return embed

    """
    def make_stats(self, info, ph, option=None):
        ph[ph.index('Stats')] = '**[Stats]**'
        try:
            with open(os.path.join(dir,f"skill/{info['en'].lower()}.txt")) as sf:
                sk_info = self.process_sk(ast.literal_eval(sf.read()))
        except Exception as e:
            print(e)
            traceback.print_exc()
            sk_info = None
        
        embed = discord.Embed(
            title="Page Unavailable",
            description=f"{self.get_full_name(info['en'])}\'s stats page is not available at the moment.",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=info['im'] if option == None else info['im6'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.set_footer(text='Stats Page | SHIN Ames',icon_url=info['im6'] if option == 'flb' else info['im'])

        embed.add_field(
            name='Section',
            value=' - '.join(ph),
            inline=False
        )

        if sk_info != None:
            embed.title = "Statistics"
            embed.description = f"{self.get_full_name(info['en'])}\'s skill and misc stats."

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
                value=  f"```glsl\n{sk_info['ub2']}```" if option == 'flb' else
                        f"```glsl\n{sk_info['ub']}```",
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
                    value=  f"{info['sk1tl']}",
                    inline= True
                )
                embed.add_field(
                    name=   "Effect",
                    value=  f"```glsl\n{sk_info['sk1']}```",
                    inline= True
                )
            
            # Skill 1+
            if not 'soon' in info.get('sk1ptl', None):
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
                    value=  f"```glsl\n{sk_info.get('sk1p','N/A')}```",
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
                value=  f"{info['sk2tl']}",
                inline= True
            )
            embed.add_field(
                name=   "Effect",
                value=  f"```glsl\n{sk_info['sk2']}```",
                inline= True
            )

        return embed   
    """

    def make_card(self, info, ph, option=None):
        ph[ph.index('Card')] = '**[Card]**'

        embed = discord.Embed(
            description=f"{self.get_full_name(info['en'])}'s card is currently unavailable {self.emj['dead']}",
            title="Card unavailble",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=info['im'] if option == None else info['im6'])
        embed.set_footer(text='Unit Card Page | SHIN Ames',icon_url=info['im'] if option == None else info['im6'])
        embed.set_author(name='ハツネのメモ帳',icon_url='https://cdn.discordapp.com/avatars/580194070958440448/c0491c103169d0aa99027b2216ee7708.jpg')
        embed.add_field(
            name='Section',
            value=' - '.join(ph),
            inline=False
        )
        #print(info['hnote_id'], type(info['hnote_id']))
        if info['hnote_id'] != 'None':
            embed.title = "Unit Card"
            if option == None:
                embed.description = f"{self.get_full_name(info['en'])}'s card."
                link = f"https://redive.estertion.win/card/full/{info['hnote_id'][:4]}31.webp"
            else:
                embed.description = f"{self.get_full_name(info['en'])}'s FLB (6:star:) card."
                link = f"https://redive.estertion.win/card/full/{info['hnote_id'][:4]}61.webp"

            embed.set_image(url=link)
        
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
        """
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        if target in c_list:
            target_id = id_list[c_list.index(target)]
        elif target in c_jp_list:
            target_id = id_list[c_jp_list.index(target)]
        else:
            target_id = None
        """
        chara = await self.validate_entry(target, channel)
        if chara == False:
            return
        target_id = chara['id']
        
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
        """
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        if target in c_list:
            target_id = id_list[c_list.index(target)]
        elif target in c_jp_list:
            target_id = id_list[c_jp_list.index(target)]
        else:
            target_id = None
        """
        chara = await self.validate_entry(target, channel)
        if chara == False:
            return
        target_id = chara['id']

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
            description=data["comment"] if data.get("comment","") != "" else "No comment as of yet",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=data["im"] if data.get("im","") != "" else "https://redive.estertion.win/icon/unit/000001.webp")
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
            if len(teams) > 0:
                embed.add_field(
                    name=f"Mode {mode}",
                    value="\n".join(teams),
                    inline=True
                )

        return embed

    @commands.group(
        invoke_without_command=True
    )
    async def alias(self, ctx):
        channel = ctx.channel
        author = ctx.message.author
        active = await self.active_check(channel)
        if not active:
            return
        
        if ctx.invoked_subcommand is None:
            with open(os.path.join(dir, '_config/alias_local.txt')) as alf:
                alocal = ast.literal_eval(alf.read())
            with open(os.path.join(dir, '_config/alias.txt')) as af:
                alias_list = ast.literal_eval(af.read())
                alias_list.update(alocal)
                alias_list = list(alias_list.items())
                alias_list.sort(key=lambda x: x[1])

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
        with open(os.path.join(dir, '_config/alias_local.txt')) as alf:
            alocal = ast.literal_eval(alf.read())

        embed.add_field(
            name="Location",
            value="\n".join(["local" if key in alocal else "master" for key in alias]),
            inline=True
        )
        return embed
    
    async def kwargcheck(self, kw, arg, channel):
        maxlen = 12
        try:
            kw = kw.lower()
            arg = arg.lower()
        except:
            return False

        if len(kw) > maxlen:
            await channel.send(f"Key exceeds maximum allowed length ({maxlen})")
            return False
        
        # fetch pointer and check if its connected
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            await channel.send(self.error()['conn_fail'])
            await self.logger.send(self.name,'DB connection failed')
            return False

        # fetch the character lists to check if target is in them
        """
        c_list, c_jp_list, id_list = self.fetch_list(conn)
        del id_list
        """
        chara = await self.validate_entry(arg, channel)
        if chara == False:
            await channel.send(f"`{arg}` is not a valid database entry")
            conn.close()
            return
        else:
            conn.close()
            return True
        

        """
        if not arg in c_list and not arg in c_jp_list:
            await channel.send(f"`{arg}` is not a valid database entry")
            conn.close()
            return False

        conn.close()
        return True
        """
        
    @alias.command()
    async def add(self, ctx, kw, arg):
        channel = ctx.channel
        with open(os.path.join(dir, '_config/alias_local.txt')) as alf:
            alocal = ast.literal_eval(alf.read())
        with open(os.path.join(dir, '_config/alias.txt')) as af:
            alias_list = ast.literal_eval(af.read())
        
        kw = kw.lower()
        arg = arg.lower()
        valid = await self.kwargcheck(kw, arg, channel)

        if not valid:
            return
        elif not kw in alocal and not kw in alias_list:
            alocal[kw] = arg
            with open(os.path.join(dir, '_config/alias_local.txt'), 'w') as alf:
                alf.write(str(alocal))
            self.preprocessor.update(alocal)
            await channel.send(f"Successfully added alias `{kw}` -> `{arg}` local")
        elif kw in alocal:
            await channel.send(f"Alias already exists in local: `{kw}` -> `{alocal[kw]}`")
        elif kw in alias_list:
            await channel.send(F"Alias already exists in tracked: `{kw}` -> `{alias_list[kw]}`\nThis cannot be edited")
        else:
            pass
    
    @alias.command(aliases=['rm'])
    async def remove(self, ctx, kw):
        channel = ctx.channel
        with open(os.path.join(dir,'_config/alias_local.txt'), 'r') as alf:
            alocal = ast.literal_eval(alf.read())
        if kw in alocal:
            arg = alocal[kw]
            del alocal[kw]
            del self.preprocessor[kw]
            with open(os.path.join(dir,'_config/alias_local.txt'), 'w') as alf:
                alf.write(str(alocal))
            await channel.send(f"Successfully removed `{kw}` -> `{arg}` local")
        else:
            await channel.send(f"No local alias with `{kw}` found.")
    
    @alias.command(aliases=['ed'])
    async def edit(self, ctx, kw, arg):
        channel = ctx.channel
        with open(os.path.join(dir,'_config/alias_local.txt'),'r') as alf:
            alocal = ast.literal_eval(alf.read())
        if kw in alocal:
            alocal[kw] = arg
            self.preprocessor[kw] = arg
            with open(os.path.join(dir,'_config/alias_local.txt'), 'w') as alf:
                alf.write(str(alocal))
            await channel.send(f"Successfully changed alias `{kw}` -> `{arg}` local")
        else:
            await channel.send(f"No local alias with `{kw}` found.")
    
    @alias.command(aliases=['ck'])
    async def check(self, ctx, kw):
        channel = ctx.channel
        if kw in self.preprocessor:
            await channel.send(f"Alias `{kw}` -> `{self.preprocessor[kw]}`")
        else:
            await channel.send(f"No alias `{kw}` found")

    @alias.command()
    async def prune(self, ctx):
        channel = ctx.channel
        with open(os.path.join(dir, '_config/alias.txt')) as af:
            alias_list = ast.literal_eval(af.read())
        with open(os.path.join(dir,'_config/alias_local.txt')) as alf:
            alocal = ast.literal_eval(alf.read())
        await channel.send('Pruning local list...')
        for key in list(alias_list.keys()):
            if key in alocal:
                await channel.send(f"Deleting master-local conflict `{key}` -> `{alocal[key]}` local")
                del alocal[key]

        await channel.send('Complete! Reloading dictionary and saving amended local...')
        self.preprocessor = alias_list
        self.preprocessor.update(alocal)
        with open(os.path.join(dir,'_config/alias_local.txt'), 'w') as alf:
            alf.write(str(alocal))

        await channel.send('Complete!')

def setup(client):
    client.add_cog(hatsuneCog(client))
