import nextcord, json, copy, requests, random
from io import BytesIO
from nextcord.ext import commands
import utils as ut
import templates as tem
from collections.abc import Mapping
from PIL import Image
from glob import glob
from asyncio import sleep

def setup(client):
    client.add_cog(hatsuneCog(client))

class hatsuneCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[Hatsune]'
        self.logger = ut.Ames_logger(self.name, self.client.Log)
        self.logger.init_client(self.client)

        self.rel_path = ut.full_path(self.client.dir, self.client.config['configs']['hatsune'])

        # load config
        with open(ut.full_path(self.rel_path, 'hatsune_config.json')) as cf:
            self.hatsu_cf = json.load(cf)

        # aliases and prefixes and res
        self.load_aliases()
        self.load_prefixes()
        self.res = self.client.hatsu_res

#############################################################################################################
# Hatsune Update 
#############################################################################################################

    def load_prefixes(self):
        with open(ut.full_path(self.rel_path, self.hatsu_cf['prefix'])) as p:
            self.prefixes = json.load(p)
    
    def load_aliases(self):
        self.aliases = self.get_full_alias()

    @commands.command()
    async def convert_db(self, ctx):
        if not self.client.check_perm(ctx.author):
            await ctx.channel.send('Restricted')
            return
        self.__convert_db()
        await self.validate_database(ctx.channel)

    # convert to new DB structure    
    def __convert_db(self):
        with open(ut.full_path(self.rel_path, 'data/chara_data_OLD.json')) as odb:
            odbf = json.load(odb)

        db = []

        for unit in odbf['units']:
            unit_new = tem.fetch('hatsu_chara')

            # basic stats
            unit_new['id']      = unit['basic']['en']['id']
            unit_new['hnid']    = unit['basic']['jp']['id']
            old_prefix          = unit['basic']['en']['prefix']
            if old_prefix == 'c':
                unit_new['prefix'] = 'cd'
            elif old_prefix == 'cr':
                unit_new['prefix'] = 'c'
            else:
                unit_new['prefix'] = old_prefix
            unit_new['sname']   = unit_new['prefix'] + unit['basic']['en']['name'] if unit_new['prefix'] != None else unit['basic']['en']['name']

            unit_new['tags'] = unit['tags']
            unit_new['type'] = 0 if 'magic' in unit_new['tags'] else 1
            if 'front' in unit['tags']:
                unit_new['pos_field']   = 0
                unit_new['pos']         = unit['pos'] - 100
            elif 'mid' in unit['tags']:
                unit_new['pos_field']   = 1
                unit_new['pos']         = unit['pos'] - 200
            else:
                unit_new['pos_field']   = 2
                unit_new['pos']         = unit['pos'] - 300

            # status
            sub             = unit['status']
            sub_new         = unit_new['status']
            sub_new['lvl']      = sub['lvl']
            sub_new['ue']       = sub['ue']
            sub_new['rank']     = sub['rk']
            unit_new['status']  = sub_new

            # base
            sub                 = unit['basic']
            sub_new             = unit_new['base']
            sub_new['active']   = True
            sub_new['img']      = unit['img']
            #sub_new['card']     = unit['']
            sub_new['hnid']     = unit_new['hnid']

            if 'ue' in unit['tags']: sub_new['ue'] = True
            
            # base - atkptn
            for atkptn in unit['atkptn']:
                if atkptn['no'] == '1':
                    sub_new['normal']['pattern']['all']   = atkptn['ptn']
                    sub_new['normal']['pattern']['loop']  = atkptn['loop']
                elif atkptn['no'] == '2':
                    sub_new['alt']['pattern']['all']   = atkptn['ptn']
                    sub_new['alt']['pattern']['loop']  = atkptn['loop']
                    sub_new['b_alt'] = True
                else:
                    print('unknown skill pattern no', atkptn, unit['sname'], unit['basic']['jp']['id'])
                    #s = copy.deepcopy(tem.hatsu_chara_skills)
                    s = {
                        'type': 'pattern',
                        'pattern_no': int(atkptn['no']),
                        'all': atkptn['ptn'],
                        'loop': atkptn['loop']
                    }
                    unit_new['special'].append(s)
                    #raise Exception('db conversion error')
            
            # base - norm skills
            sub_new['normal']['ub']['en']              = sub['en']['ub']['text']
            sub_new['normal']['ub']['name']['jp']     = sub['jp']['ub']['name']
            sub_new['normal']['ub']['jp']              = sub['jp']['ub']['text']
            sub_new['normal']['ub']['actions']         = sub['en']['ub']['action']
            sub_new['normal']['sk1']['en']             = sub['en']['sk1']['text']
            sub_new['normal']['sk1']['name']['jp']    = sub['jp']['sk1']['name']
            sub_new['normal']['sk1']['jp']             = sub['jp']['sk1']['text']
            sub_new['normal']['sk1']['actions']        = sub['en']['sk1']['action']
            sub_new['normal']['sk2']['en']             = sub['en']['sk2']['text']
            sub_new['normal']['sk2']['name']['jp']    = sub['jp']['sk2']['name']
            sub_new['normal']['sk2']['jp']             = sub['jp']['sk2']['text']
            sub_new['normal']['sk2']['actions']        = sub['en']['sk2']['action']
            sub_new['normal']['sk3']['en']             = sub['en']['sk3']['text']
            sub_new['normal']['sk3']['name']['jp']    = sub['jp']['sk3']['name']
            sub_new['normal']['sk3']['jp']             = sub['jp']['sk3']['text']
            sub_new['normal']['sk3']['actions']        = sub['en']['sk3']['action']
            if sub_new['ue']:
                sub_new['normal']['ue']['sk1']['en']             = sub['en']['sk1p']['text']
                sub_new['normal']['ue']['sk1']['name']['jp']    = sub['jp']['sk1p']['name']
                sub_new['normal']['ue']['sk1']['jp']             = sub['jp']['sk1p']['text']
                sub_new['normal']['ue']['sk1']['actions']        = sub['en']['sk1p']['action']

            # base - alt skills 
            if sub_new['b_alt'] == True:
                sub_new['alt']['ub']['en']              = sub['en']['uba']['text']
                sub_new['alt']['ub']['name']['jp']     = sub['jp']['uba']['name']
                sub_new['alt']['ub']['jp']              = sub['jp']['uba']['text']
                sub_new['alt']['ub']['actions']         = sub['en']['uba']['action']
                sub_new['alt']['sk1']['en']             = sub['en']['sk1a']['text']
                sub_new['alt']['sk1']['name']['jp']    = sub['jp']['sk1a']['name']
                sub_new['alt']['sk1']['jp']             = sub['jp']['sk1a']['text']
                sub_new['alt']['sk1']['actions']        = sub['en']['sk1a']['action']
                sub_new['alt']['sk2']['en']             = sub['en']['sk2a']['text']
                sub_new['alt']['sk2']['name']['jp']    = sub['jp']['sk2a']['name']
                sub_new['alt']['sk2']['jp']             = sub['jp']['sk2a']['text']
                sub_new['alt']['sk2']['actions']        = sub['en']['sk2a']['action']
                sub_new['alt']['sk3']['en']             = sub['en']['sk3a']['text']
                sub_new['alt']['sk3']['name']['jp']    = sub['jp']['sk3a']['name']
                sub_new['alt']['sk3']['jp']             = sub['jp']['sk3a']['text']
                sub_new['alt']['sk3']['actions']        = sub['en']['sk3a']['action']
                if sub_new['ue']:
                    sub_new['alt']['ue']['sk1']['en']             = sub['en']['sk1ap']['text']
                    sub_new['alt']['ue']['sk1']['name']['jp']    = sub['jp']['sk1ap']['name']
                    sub_new['alt']['ue']['sk1']['jp']             = sub['jp']['sk1ap']['text']
                    sub_new['alt']['ue']['sk1']['actions']        = sub['en']['sk1ap']['action']

            # base - EX and stats
            sub_new['ex']['en']             = sub['en']['ex']['text']
            sub_new['ex']['name']['jp']    = sub['jp']['ex']['name']
            sub_new['ex']['jp']             = sub['jp']['ex']['text']
            sub_new['ex']['actions']        = sub['en']['ex']['action']
            sub_new['stats'] = unit['stats']['normal']

            # base - UE stats
            sub_new['ue_data']['hnid'] = unit['ue']['id']
            sub_new['ue_data']['img'] = unit['ue']['img']
            sub_new['ue_data']['stats'] = unit['ue']['stats']
            sub_new['ue_data']['name']['en'] = unit['ue']['en']['name']
            sub_new['ue_data']['name']['jp'] = unit['ue']['jp']['name']
            sub_new['ue_data']['text']['en'] = unit['ue']['en']['text']
            sub_new['ue_data']['text']['jp'] = unit['ue']['jp']['text']

            unit_new['base'] = sub_new

            # flb
            sub                 = unit['basic']
            sub_new             = unit_new['flb']
            sub_new['active']   = True if 'flb' in unit['tags'] else False
            if sub_new['active']:
                sub_new['img']      = unit['img6']
                #sub_new['card']     = unit['']
                sub_new['hnid']     = unit_new['hnid']

                sub_new['ue'] = True
                
                # flb - atkptn
                for atkptn in unit['atkptn']:
                    if atkptn['no'] == '2':
                        sub_new['b_alt'] = True
                    else:
                        continue
                
                # flb - norm skills
                sub_new['normal']['ub']['en']              = sub['en']['ub2']['text']
                sub_new['normal']['ub']['name']['jp']     = sub['jp']['ub2']['name']
                sub_new['normal']['ub']['jp']              = sub['jp']['ub2']['text']
                sub_new['normal']['ub']['actions']         = sub['en']['ub2']['action']

                # flb - EX and stats
                sub_new['ex']['en']             = sub['en']['ex2']['text']
                sub_new['ex']['name']['jp']    = sub['jp']['ex2']['name']
                sub_new['ex']['jp']             = sub['jp']['ex2']['text']
                sub_new['ex']['actions']        = sub['en']['ex2']['action']
                sub_new['stats'] = unit['stats']['flb'] if unit['stats']['flb'] else None

                unit_new['flb'] = sub_new

            # misc
            unit_new['name']['en']          = unit['basic']['en']['name']
            unit_new['name']['jp']          = unit['basic']['jp']['name']
            unit_new['name_alt']['jp']      = unit['profile']['jp']['name_alt']
            unit_new['name_irl']['jp']      = unit['profile']['jp']['name_irl']
            unit_new['guild']               = unit['profile']['jp']['guild']
            unit_new['age']                 = unit['profile']['age']
            unit_new['bloodtype']           = unit['profile']['blood']
            unit_new['va']                  = unit['profile']['jp']['va']
            unit_new['weight']              = unit['profile']['weight']
            unit_new['height']              = unit['profile']['height']
            unit_new['bday']                = unit['profile']['bd']
            unit_new['race']                = unit['profile']['jp']['race']
            unit_new['image_irl']           = unit['profile']['img']
            unit_new['comment']['jp']       = unit['basic']['jp']['comment']

            db.append(unit_new)
            print('processed', unit['sname'])
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database']), 'w+') as ndb:
            ndb.write(json.dumps({'units':db}, indent=4))
        print('complete')

    @commands.command()
    async def update(self, ctx, *, option): #FIXME
        channel = ctx.channel
        if not self.client.check_perm(ctx.author):
            await channel.send('Restricted')
            return
        elif not option:
            await channel.send('No input')
            return
        option = option.split()
        
        if option[0] == 'index':
            await self.make_index(channel)

        elif option[0] == 'db':
            await self.update_database(ctx, option[-1] if len(option) > 1 else None)

        elif option[0] == 'exskills':
            with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as db:
                await self.update_exskills(ctx, json.load(db)['units'], True)

        elif option[0] == 'assets':
            await self.update_assets(ctx)

        elif option[0] == 'pos':
            cmd = ' '.join(option[1:])
            request = self.process_request(cmd)
            if not request:
                await channel.send(f"Failed to find {cmd}")
                return
            request = self.fetch_chara(request)
            if not request:
                await channel.send(f"Failed to find {cmd}")
                return
            elif request['fallback']:
                await channel.send(f"Failed to find {cmd}")
                return
            else:
                with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as f:
                    dbf = json.load(f)['units']
                    dbf.pop(dbf.index(request['target']))

            await self.update_pos(ctx, request['target'], dbf, True)

        elif option[0] == 'prefix':
            await self.update_prefix(ctx)

        elif option[0] == 'gacha':
            await self.update_gacha(ctx)

        elif option[0] == 'all': #FIXME
            # update prefix
            await self.update_prefix(ctx)

            # update db
            await self.update_database(ctx, option[-1] if len(option) > 1 else None)

            # update assets
            await self.update_assets(ctx)

            # update gacha
            await self.update_gacha(ctx)

            # update index
            self.make_index(channel)

            # done
            await channel.send("Full update complete")

        else:
            # .edit [cmd]
            cmd = ' '.join(option)
            request = self.process_request(cmd)
            if not request:
                await channel.send(f"Failed to find {cmd}")
                return
            request = self.fetch_chara(request)
            if not request:
                await channel.send(f"Failed to find {cmd}")
                return
            elif request['fallback']:
                await channel.send(f"Failed to find {cmd}")
                return
            
            target = await self.update_tl(ctx, request['target'])

            if target:
                with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as f:
                    dbf = json.load(f)
                dbf['units'][request['target_index']] = target
                with open(ut.full_path(self.rel_path, self.hatsu_cf['database']), 'w+') as f:
                    f.write(json.dumps(dbf, indent=4))

        await self.validate_database(channel)

    # sub update function
    async def make_index(self, channel, verbose=True):
        temp = []

        with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as db:
            dbf = json.load(db)
        
        for unit in dbf['units']:
            index = tem.fetch('hatsu_index')

            index['id']         = unit['id']
            index['hnid']       = unit['hnid']
            index['prefix']     = unit['prefix']
            index['name']['en'] = unit['name']['en']
            index['name']['jp'] = unit['name']['jp']
            index['flb']        = unit['flb']['active']
            index['ue']         = unit['base']['ue']
            index['sname']      = unit['sname']
            index['enum_alias'] = self.enum_alias(index['name']['en'], index['prefix'], unit['kizuna'])
            index['kizuna']     = unit['kizuna']

            temp.append(index)
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['index']), 'w+') as indf:
            indf.write(json.dumps({'index': temp}, indent=4))
        
        if verbose: await channel.send('Finished making index')
    
    def get_full_alias(self):
        with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases'])) as aliases:
            alias_master = json.load(aliases)
        try:
            with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases_loc'])) as aliases:
                alias_loc = json.load(aliases)
        except FileNotFoundError:
            alias_loc = {}

        alias_master.update(alias_loc)
        return alias_master

    def enum_alias(self, name_en, prefix, kizuna=[]):
        alias_names = [name_en] + kizuna
        alias_prefixes = []

        # check aliases
        for alias, name in self.aliases.items():
            if name_en == name:
                alias_names.append(alias)
        
        # check prefix
        if prefix:
            alias_prefixes = [prefix]
            for p_alias, p in self.prefixes['prefix_alias'].items():
                if prefix == p:
                    alias_prefixes.append(p_alias)
        
        # enum
        return [p+a for p in alias_prefixes for a in alias_names]

    def fetch_index_diff(self):
        with open(self.hatsu_cf['fag_index'], encoding='utf-8') as ind:
            fag_ind = json.load(ind)
        
        for chara in self.hatsu_cf['blacklist']:
            flag = fag_ind.pop(chara, None)
            if not flag:
                print("diff - failed to remove from blacklist:", chara)

        with open(ut.full_path(self.rel_path, self.hatsu_cf['index']), encoding='utf-8') as ind:
            hatsu_ind = [chara['name']['jp'] for chara in json.load(ind)['index']]
        
        for chara in hatsu_ind:
            flag = fag_ind.pop(chara, None)
            if not flag:
                print("diff - failed to remove from fag_ind:", chara)
        
        return fag_ind

    def deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, Mapping):
                d[k] = self.deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    async def fetch_fag_data(self, hnid):
        port = self.client.config['fag_port']
        if port != None:
            request = f"http://localhost:{port}/FagUtils/gateway.php?"
        else:
            request = f"http://localhost/FagUtils/gateway.php?"
        params = {
            "cmd":  "priconne.api",
            "call": "api.fetch",
            "id":   hnid
        }
        try:
            result = requests.get(request, params=params)
            raw = json.load(BytesIO(result.content))
        except Exception as e:
            await self.logger.report("failed to fetch hnid:", hnid)
            return False
        if raw['status'] != 200:
            await self.logger.send("fag returned status code" , raw['status'])
            return False
        else:
            return raw
    
    async def update_fag_data(self, data, raw):
        # soft reset
        data['flb']['active']   = False

        # conversions
        with open(ut.full_path(self.hatsu_cf['fag_conversion'])) as conv:
            conversion = json.load(conv)

        # insert fag data
        # status
        data['status']['lvl']   = raw['config']['LEVEL_MAX']
        data['status']['ue']    = raw['config']['UE_MAX']
        data['status']['rank']  = raw['config']['RANK_MAX']

        # unit profile
        profile                 = raw['data']['unit_profile']
        data['hnid']                = int(profile['id'])
        data['guild']               = profile['guild']
        data['name']['jp']          = profile['name'].replace('（', '(').replace('）', ')')
        data['name_alt']['jp']      = profile['name_alt']
        data['name_irl']['jp']      = profile['name_irl']
        data['race']                = profile['race']
        data['age']                 = profile['age']
        data['bday']                = profile['bday']
        data['weight']              = profile['weight']
        data['height']              = profile['height']
        data['bloodtype']           = profile['bloodtype']
        data['va']                  = profile['VA']
        data['comment']['jp']       = profile['comment']

        # unit pattern
        for pattern in raw['data']['unit_pattern']:
            patNo       = pattern.pop('PatternNo')
            loop, pat   = self.fag_proc_pattern(pattern)
            if patNo == '1':
                data['base']['normal']['pattern']['all']    = pat
                data['base']['normal']['pattern']['loop']   = loop
            elif patNo == '2':
                data['base']['alt']['pattern']['all']       = pat
                data['base']['alt']['pattern']['loop']      = loop
            else:
                spec_data = {
                    'type':         'pattern',
                    'pattern_no':   int(patNo),
                    'loop':         loop,
                    'all':          pat
                }
                data['special'].append(spec_data)
                await self.logger.report(
                    'Unknown attack pattern encountered for', 
                    data['name']['jp'], 
                    json.dumps(spec_data, indent=4)
                )
        
        # ue
        ue = raw['data'].get('unique_equipment', None)
        if ue:
            ue.pop('ue_id_growth')
            data['base']['ue']                      = True
            data['base']['ue_data']['hnid']         = ue.pop('ue_id')
            data['base']['ue_data']['name']['jp']   = ue.pop('ue_name')
            data['base']['ue_data']['text']['jp']   = ue.pop('ue_description')
            data['base']['ue_data']['stats']        = ue
        
        # check for special conversion
        if 'conversion_skill_data' in raw['data']:
            for key, value in raw['data']['conversion_skill_data'].items():
                # complete character conversion on FLB
            #if key.startswith('conversion_skill_data'):
                #print('here')
                OVERRIDE = 'flb'
                data[OVERRIDE]['hnid'] = int(conversion[str(data['hnid'])])
                # UB
                if key.startswith('Union Burst'):
                    k3 = 'ub'
                    if key.endswith('Alt+'):
                        k2 = 'alt'
                        data[OVERRIDE]['b_alt']    = True
                        data[OVERRIDE]['active']   = True
                    elif key.endswith('Alt'):
                        # ignore - no place to store data
                        continue
                    elif key.endswith('+'):
                        k2 = 'normal'
                        data[OVERRIDE]['active']   = True
                    else:
                        # ignore - no place to store data
                        continue

                    data[OVERRIDE][k2][k3]['name']['jp'] = value['skill_name']
                    data[OVERRIDE][k2][k3]['jp']         = value['description']
                    data[OVERRIDE][k2][k3]['actions']    = value['actions']

                # skills
                elif key.startswith('Skill 1'):
                    k1 = 'sk1'
                    if key.endswith('Alt+'):
                        data[OVERRIDE]['b_alt'] = True
                        data[OVERRIDE]['alt']['ue'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['alt']['ue'][k1]['jp']         = value['description']
                        data[OVERRIDE]['alt']['ue'][k1]['actions']    = value['actions']
                    elif key.endswith('Alt'):
                        data[OVERRIDE]['b_alt'] = True
                        data[OVERRIDE]['alt'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['alt'][k1]['jp']         = value['description']
                        data[OVERRIDE]['alt'][k1]['actions']    = value['actions']
                    elif key.endswith('+'):
                        data[OVERRIDE]['normal']['ue'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['normal']['ue'][k1]['jp']         = value['description']
                        data[OVERRIDE]['normal']['ue'][k1]['actions']    = value['actions']
                    else:
                        data[OVERRIDE]['normal'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['normal'][k1]['jp']         = value['description']
                        data[OVERRIDE]['normal'][k1]['actions']    = value['actions']
                elif key.startswith('Skill 2'):
                    k1 = 'sk2'
                    if key.endswith('Alt+'):
                        raise Exception('Unhandled skill key:', key, data['name']['jp'])
                    elif key.endswith('Alt'):
                        data[OVERRIDE]['b_alt'] = True
                        data[OVERRIDE]['alt'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['alt'][k1]['jp']         = value['description']
                        data[OVERRIDE]['alt'][k1]['actions']    = value['actions']
                    elif key.endswith('+'):
                        raise Exception('Unhandled skill key:', key, data['name']['jp'])
                    else:
                        data[OVERRIDE]['normal'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['normal'][k1]['jp']         = value['description']
                        data[OVERRIDE]['normal'][k1]['actions']    = value['actions']
                elif key.startswith('Skill 3'):
                    k1 = 'sk3'
                    if key.endswith('Alt+'):
                        raise Exception('Unhandled skill key:', key, data['name']['jp'])
                    elif key.endswith('Alt'):
                        data[OVERRIDE]['b_alt'] = True
                        data[OVERRIDE]['alt'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['alt'][k1]['jp']         = value['description']
                        data[OVERRIDE]['alt'][k1]['actions']    = value['actions']
                    elif key.endswith('+'):
                        raise Exception('Unhandled skill key:', key, data['name']['jp'])
                    else:
                        data[OVERRIDE]['normal'][k1]['name']['jp'] = value['skill_name']
                        data[OVERRIDE]['normal'][k1]['jp']         = value['description']
                        data[OVERRIDE]['normal'][k1]['actions']    = value['actions']
                
                # EX skills
                elif key.startswith('EX Skill'):
                    k1 = 'ex'
                    if key.endswith('+'):
                        #k2 = 'flb'
                        data['flb']['active']    = True
                    else:
                        # ignore - no place to store data
                        continue
                    
                    data[OVERRIDE][k1]['name']['jp'] = value['skill_name']
                    data[OVERRIDE][k1]['jp']         = value['description']
                    data[OVERRIDE][k1]['actions']    = value['actions']
                else:
                    spec_data = {
                        'type':     'skill',
                        'key':      key,
                        'data':     value
                    }
                    data['special'].append(spec_data)
                    await self.logger.report(
                        'Unknown attack skill encountered for', 
                        data['name']['jp'], 
                        json.dumps(spec_data, indent=4)
                    )

        # skill data
        data['base']['active'] = True
        for key, value in raw['data']['skill_data'].items():
            #else:
            # UB
            if key.startswith('Union Burst'):
                k3 = 'ub'
                if key.endswith('Alt+'):
                    k1 = 'flb'
                    k2 = 'alt'
                    data['flb']['b_alt']    = True
                    data['flb']['active']   = True
                elif key.endswith('Alt'):
                    k1 = 'base'
                    k2 = 'alt'
                    data['base']['b_alt']   = True
                elif key.endswith('+'):
                    k1 = 'flb'
                    k2 = 'normal'
                    data['flb']['active']   = True
                else:
                    k1 = 'base'
                    k2 = 'normal'

                data[k1][k2][k3]['name']['jp'] = value['skill_name']
                data[k1][k2][k3]['jp']         = value['description']
                data[k1][k2][k3]['actions']    = value['actions']

            # skills
            elif key.startswith('Skill 1'):
                k1 = 'sk1'
                if key.endswith('Alt+'):
                    data['base']['b_alt'] = True
                    data['base']['alt']['ue'][k1]['name']['jp'] = value['skill_name']
                    data['base']['alt']['ue'][k1]['jp']         = value['description']
                    data['base']['alt']['ue'][k1]['actions']    = value['actions']
                elif key.endswith('Alt'):
                    data['base']['b_alt'] = True
                    data['base']['alt'][k1]['name']['jp'] = value['skill_name']
                    data['base']['alt'][k1]['jp']         = value['description']
                    data['base']['alt'][k1]['actions']    = value['actions']
                elif key.endswith('+'):
                    data['base']['normal']['ue'][k1]['name']['jp'] = value['skill_name']
                    data['base']['normal']['ue'][k1]['jp']         = value['description']
                    data['base']['normal']['ue'][k1]['actions']    = value['actions']
                else:
                    data['base']['normal'][k1]['name']['jp'] = value['skill_name']
                    data['base']['normal'][k1]['jp']         = value['description']
                    data['base']['normal'][k1]['actions']    = value['actions']
            elif key.startswith('Skill 2'):
                k1 = 'sk2'
                if key.endswith('Alt+'):
                    raise Exception('Unhandled skill key:', key, data['name']['jp'])
                elif key.endswith('Alt'):
                    data['base']['b_alt'] = True
                    data['base']['alt'][k1]['name']['jp'] = value['skill_name']
                    data['base']['alt'][k1]['jp']         = value['description']
                    data['base']['alt'][k1]['actions']    = value['actions']
                elif key.endswith('+'):
                    raise Exception('Unhandled skill key:', key, data['name']['jp'])
                else:
                    data['base']['normal'][k1]['name']['jp'] = value['skill_name']
                    data['base']['normal'][k1]['jp']         = value['description']
                    data['base']['normal'][k1]['actions']    = value['actions']
            elif key.startswith('Skill 3'):
                k1 = 'sk3'
                if key.endswith('Alt+'):
                    raise Exception('Unhandled skill key:', key, data['name']['jp'])
                elif key.endswith('Alt'):
                    data['base']['b_alt'] = True
                    data['base']['alt'][k1]['name']['jp'] = value['skill_name']
                    data['base']['alt'][k1]['jp']         = value['description']
                    data['base']['alt'][k1]['actions']    = value['actions']
                elif key.endswith('+'):
                    raise Exception('Unhandled skill key:', key, data['name']['jp'])
                else:
                    data['base']['normal'][k1]['name']['jp'] = value['skill_name']
                    data['base']['normal'][k1]['jp']         = value['description']
                    data['base']['normal'][k1]['actions']    = value['actions']
            
            # EX skills
            elif key.startswith('EX Skill'):
                k1 = 'ex'
                if key.endswith('+'):
                    k2 = 'flb'
                    #data['flb']['active']    = True
                else:
                    k2 = 'base'
                
                data[k2][k1]['name']['jp'] = value['skill_name']
                data[k2][k1]['jp']         = value['description']
                data[k2][k1]['actions']    = value['actions']
            else:
                spec_data = {
                    'type':     'skill',
                    'key':      key,
                    'data':     value
                }
                data['special'].append(spec_data)
                await self.logger.report(
                    'Unknown attack skill encountered for', 
                    data['name']['jp'], 
                    json.dumps(spec_data, indent=4)
                )
            
        # stats
        if 'stats' in raw['data']:
            k1 = 'stats'
            k2 = 'base'

            data[k2][k1] = raw['data']['stats']

        if 'stats_flb' in raw['data']:
            k1 = 'stats'
            k2 = 'flb'
            data['flb']['active']   = True

            data[k2][k1] =  raw['data']['stats_flb']

        # make img links
        data = self.update_img(data)            
        
        return data

    def update_img(self, data):
        # img to get (default):
            # irl card
            # base img
            # base card
        # img to get (if applicable):
            # ue img
            # flb img
            # flb card

        data['image_irl']               = self.hatsu_cf['links']['card_irl'].format(data['hnid'])
        data['base']['img']             = self.hatsu_cf['links']['img_3s'].format(data['hnid'])
        data['base']['card']            = self.hatsu_cf['links']['card_3s'].format(data['hnid'])
        data['base']['ue_data']['img']  = self.hatsu_cf['links']['img_ue'].format(data['base']['ue_data']['hnid']) \
                                            if data['base']['ue'] else self.hatsu_cf['links']['unknown']
        data['flb']['img']              = self.hatsu_cf['links']['img_6s'].format(data['hnid'])
        data['flb']['card']             = self.hatsu_cf['links']['card_6s'].format(data['hnid'])

        return data

    def fag_proc_pattern(self, pattern):
        loop = [
            pattern.pop('loop_start'),
            pattern.pop('loop_end')
        ]
        return loop, [kv[1] for kv in sorted(pattern.items(), key=lambda x: x[0])]

    # sub update function
    async def update_database(self, ctx, option):
        channel = ctx.channel

        fag_ind_diff = self.fetch_index_diff()
        with open(self.hatsu_cf['fag_index'], encoding='utf-8') as ind:
            fag_ind_full = json.load(ind)
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as db:
            dbf = json.load(db)
            units = dbf['units']
        
        if option == 'all':
            await channel.send('Updating all database entries')
            target = fag_ind_full
        elif option == 'ue':
            await channel.send('Updating all UE characters')
            target = dict(
                [(chara['name']['jp'],str(chara['hnid'])) for chara in units 
                if chara['base']['ue_data']['name']['jp'] and not chara['base']['ue_data']['name']['en']]
            )
        elif option == 'flb':
            await channel.send('Updating all FLB characters')
            target = dict(
                [(chara['name']['jp'],str(chara['hnid'])) for chara in units 
                if chara['flb']['active'] and not chara['flb']['normal']['ub']['en']]
            )
        else:
            await channel.send('Updating new database entries')
            target = fag_ind_diff
        
        ten_pcent = len(target)//10
        counter = 1
        status_str = 'Starting Update...'
        status = await channel.send(status_str)
        #updated = []

        for chara, hnid in target.items():
            if counter < ten_pcent:
                counter += 1
            else:
                status_str += 'x'
                await status.edit(status_str)
                counter = 1
            
            if chara in fag_ind_diff:
                # chara is new
                new = True
                data = tem.fetch('hatsu_chara')
            else:
                # chara exists; pop entry from master database and update structure
                new = False
                match = [u for u in units if str(u['hnid']) == hnid]
                assert len(match) == 1, f'Expected 1 match when searching in DB but found {len(match)} for {chara}'
                data = units.pop(units.index(match[0]))

                data = self.deep_update(tem.fetch('hatsu_chara'), data)
            
            raw = await self.fetch_fag_data(hnid)
            if not raw:
                raise Exception('Failed to fetch data from fag')
            
            data = await self.update_fag_data(data, raw)
            
            # add TLs
            if new:
                data = await self.update_tl(ctx, data)
                data, units = await self.update_pos(ctx, data, units)
            elif option in ['ue', 'flb']:
                data = await self.update_tl(ctx, data)

            units.append(data)
        
        dbf['units'] = await self.update_exskills(ctx, units)

        with open(ut.full_path(self.rel_path, self.hatsu_cf['database']), 'w+') as db:
            db.write(json.dumps(dbf, indent=4))
            await status.edit(content="Finished DB update")
        
        await self.make_index(ctx.channel)

    async def update_tl(self, ctx, data):
        channel = ctx.channel
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == channel and \
                    not msg.content.startswith('--')

        active_page_str = "Available pages are `base | base-alt | flb | flb-alt | ue`. Current editing **{}** page."
        edit_str        = "Editing **{}** field:\n`{}`\nto\n`{}`"
        edit_str_fail   = "Unknown key `{}`"
        warn            = "Warning - Either `name_en` and/or `prefix` is empty; this may leave the character inaccessible!\n Type `exit` to exit."

        active = 'base'
        embeds = {
            'base':     self.update_tl_embed(data, 'base'),
            'base-alt': self.update_tl_embed(data, 'base-alt'),
            'flb':      self.update_tl_embed(data, 'flb'),
            'flb-alt':  self.update_tl_embed(data, 'flb-alt'),
            'ue':       self.update_tl_embed(data, 'ue')
        }
        active_embed = await channel.send(embed=embeds[active])
        active_page = await channel.send(active_page_str.format(active))
        exit_confirm = False

        while True:
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            if content == 'exit':
                if not data['name']['en'] or not data['prefix']:
                    if exit_confirm:
                        break
                    warn_msg = await channel.send(warn)
                    exit_confirm = True
                    continue
                else:
                    break
            
            elif content == 'cancel':
                await active_page.delete()
                await active_embed.edit(content=f"cancelled", embed=None)
                return None

            elif content in ['base', 'base-alt', 'flb', 'flb-alt', 'ue']:
                active = content
                await active_embed.edit(embed=embeds[active])

            else:
                data, success, old, new, key = self.update_tl_proc_cmd(active, data, content)
                if success:
                    embeds[active] = self.update_tl_embed(data, active)
                    await active_embed.edit(embed=embeds[active])
                    upd = '\n'.join([active_page_str, edit_str])
                    await active_page.edit(content=upd.format(active, key, old, new))
                else:
                    upd = '\n'.join([active_page_str, edit_str_fail])
                    await active_page.edit(content=upd.format(active, key))

            if exit_confirm:
                exit_confirm = False
                await warn_msg.delete()

        if 'phys' in data['tags']:
            data['type'] = 1
        else:
            data['type'] = 0
        
        if 'front' in data['tags']:
            data['pos_field'] = 0
        elif 'mid' in data['tags']:
            data['pos_field'] = 1
        else:
            data['pos_field'] = 2
        
        p = data['prefix'] if data['prefix'] else ''
        data['sname'] = p + data['name']['en']

        await active_page.delete()
        await active_embed.edit(content=f"Finished updating {data['sname']}", embed=None)
        
        return data

    def update_tl_proc_cmd(self, active, data, content):
        null = 'N/A'
        if active == 'ue':
            k1 = 'base'
            k2 = 'ue_data'
        else: 
            if active.startswith('base'):
                k1 = 'base'
            else:
                k1 = 'flb'
            if active.endswith('alt'):
                k2 = 'alt'
            else:
                k2 = 'normal'

        # possible keys
        # name prefix tags kizuna
        # ub uba ubp ubap
        # sk1 sk1a sk1p sk1ap
        # sk2 sk2a
        # sk3 sk3a
        # ue_name
        key, value = content.split(':')
        key = key.lower().strip()
        value = value.strip() if value.strip() else None

        if key == 'name':
            old                 = self.update_tl_clean_val(data[key]['en'], null)
            new                 = value.lower()
            data[key]['en']     = self.update_tl_clean_val(new, null, 2)

        elif key == 'prefix':
            old                 = self.update_tl_clean_val(data[key], null)
            new                 = value.lower()
            data[key]           = self.update_tl_clean_val(new, null, 2)

        elif key == 'uename':
            old                                     = self.update_tl_clean_val(data['base']['ue_data']['name']['en'], null)
            new                                     = value#.title()
            data['base']['ue_data']['name']['en']   = self.update_tl_clean_val(new, null, 2)

        elif key in [
                'ub', 'uba', 'ubp', 'ubap',
                'sk1', 'sk1a', 
                'sk2', 'sk2a',
                'sk3', 'sk3a'
            ]:
            if key.startswith('ub'):
                k3 = 'ub'
            elif key.endswith('a'):
                k3 = key[:-1]
            else:
                k3 = key

            old                     = self.update_tl_clean_val(data[k1][k2][k3]['en'], null)
            new                     = value#.capitalize()
            data[k1][k2][k3]['en']  = self.update_tl_clean_val(new, null, 2)
        
        elif key in ['sk1p', 'sk1ap']:
            old                             = self.update_tl_clean_val(data[k1][k2]['ue']['sk1']['en'], null)
            new                             = value#.capitalize()
            data[k1][k2]['ue']['sk1']['en'] = self.update_tl_clean_val(new, null, 2)
        
        elif key == 'tags':
            old = data[key]
            new = self.update_tl_proc_tags(data[key], value)
            data[key] = new
        
        elif key == 'kizuna':
            old = data[key]
            new = [i.strip() for i in value.lower().split(',')]
            data[key] = new
            
        else:
            return data, False, null, value, key
        
        return data, True, old, new, key

    def update_tl_clean_val(self, val, null, mode=1):
        """
        mode 1 (default): return null if bool(val) = F
        mode 2: return None if bool(val) = F
        """
        if mode == 1:
            return val if val else null
        else:
            return val if val else None
            
    def update_tl_proc_tags(self, old:list, new:str):
        replace = []
        for tag in new.split(','):
            tag = tag.strip().lower()

            if tag.startswith('+'):
                old.append(tag[1:])

            elif tag.startswith('-'):
                old.pop(old.index(tag[1:]))

            else:
                replace.append(tag)
        
        return old if not replace else replace

    # sub update function
    async def update_pos(self, ctx, target:dict, data_all:list, save_db=False):
        """
        note that `target` must not also be found in `data_all` - isolate and pop it prior to this function
        """
        channel = ctx.channel
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel and \
                    not msg.content.startswith('--')

        # grab target pos field
        target_pos_field = target['pos_field']
        if target_pos_field != None:
            field = list(filter(lambda x: x['pos_field'] == target_pos_field, data_all))
        else:
            field = []
        field.append(target)
        field.sort(key=lambda x: x['pos'] if not x['pos'] == None else -1)

        active_embed = await channel.send(embed=self.make_pos_embed(target, field))
        await channel.send('Editing character positions. Set `pos_field` via `tags:`. Set `pos` via `insert:`')

        while True:
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            if content == 'exit':
                break
            
            elif content.startswith('tags'):
                target, success, _, _, _ = self.update_tl_proc_cmd('', target, content)

                if not success:
                    continue

                if 'front' in target['tags']:
                    target['pos_field'] = 0
                elif 'mid' in target['tags']:
                    target['pos_field'] = 1
                elif 'rear' in target['tags']:
                    target['pos_field'] = 2
        
            elif content.startswith('insert') and len(field) > 1:
                new = int(content.split(':')[-1])
                current_ind = field.index(target)

                if current_ind <= new: new -= 1
                field.pop(current_ind)

                field = field[:new] + [target] + field[new:]
                for i, chara in enumerate(field):
                    #i -= 1
                    if chara != target:
                        ind = data_all.index(chara)
                        data_all[ind]['pos'] = i if data_all[ind]['pos'] != None else None
                    else:
                        target['pos'] = i

            else:
                continue

            if target['pos_field'] != None:
                field = list(filter(lambda x: x['pos_field'] == target['pos_field'], data_all))
            else:
                field = []

            field.append(target)
            field.sort(key=lambda x: x['pos'] if not x['pos'] == None else -1)

            await active_embed.edit(embed=self.make_pos_embed(target, field))
            
        if save_db:
            with open(ut.full_path(self.rel_path, self.hatsu_cf['database']), 'w+') as dbf:
                dbf.write(json.dumps({'units': data_all + [target]}, indent=4))
        
        await active_embed.edit(content=f"Finished updating POS for {target['sname']}")

        return target, data_all
    
    def make_pos_embed(self, data, field:list):
        """
        data must be also in field
        """
        embed = {
            'title': f"Update POS for {data['name']['jp']}",
            'thumb': data['base']['img'],
            'fields': [
                {
                    'name': 'tags',
                    'value': str(data['tags']) if data['tags'] else 'N/A',
                    'inline': False
                },
                {
                    'name': 'pos_field',
                    'value': str(data['pos_field']) if data['pos_field'] != None else 'unknown',
                    'inline': False
                },
                {
                    'name': 'pos',
                    'value': str(data['pos']) if data['pos'] != None else 'unknown',
                    'inline': False
                }
            ]
        }
        if len(field) > 1:
            embed_values = []
            for i, chara in enumerate(field):
                #i -= 1
                if chara['pos'] == None:
                    i = f"{i}?"

                if chara != data:
                    embed_values.append(f"{self.client.hatsu_res[chara['sname']]['full'] if self.client.hatsu_res.get(chara['sname'], None) else '❓'} {i} {self.get_full_name(chara['name']['en'], chara['prefix'], True)}")
                else:
                    embed_values.append(f"> {self.client.hatsu_res[chara['sname']]['full'] if self.client.hatsu_res.get(chara['sname'], None) else '❓'} **{i} {self.get_full_name(chara['name']['en'], chara['prefix'], True)}**")
                
            for chunk in ut.chunks(embed_values, 20):
                embed['fields'].append(
                    {
                        'name': 'lineup',
                        'value': '\n'.join(chunk),
                        'inline': True
                    }
                )
        else:
            embed['fields'].append(
                {
                    'name': 'lineup',
                    'value': 'unknown field_pos',
                    'inline': True
                }
            )
        
        return ut.embed_contructor(**embed)
                
    def update_tl_embed(self, data, mode):
        # modes:
        # base, base-alt, flb, flb-alt, ue
        # base:         name prefix tags ub     sk1     sk1+    sk2     sk3
        # flb:          name prefix tags ub+    sk1     sk1+    sk2     sk3
        # base-alt:     name prefix tags uba    sk1a    sk1a+   sk2a    sk3a
        # flb-alt:      name prefix tags uba+   sk1a    sk1a+   sk2a    sk3a
        
        # ue:           ...

        null = 'N/A'

        embed = {
            'title': f"Editing {data['sname']} {data['name']['jp']}",
            'fields': [
                {
                        'name':     'name_jp',
                        'value':    data['name']['jp'],
                        'inline':   True
                    },
                    {
                        'name':     'name_en',
                        'value':    data['name']['en'],
                        'inline':   True
                    },
                    {
                        'name':     'prefix',
                        'value':    data['prefix'],
                        'inline':   True
                    },
                    {
                        'name':     'kizuna',
                        'value':    str(data['kizuna']),
                        'inline':   True
                    },
                    {
                        'name':     'tags',
                        'value':    self.make_tags_string(data['tags']),
                        'inline':   False
                    }
            ]
        }

        if mode != 'ue':
            if mode.startswith('base'):
                k1 = 'base'
            else:
                k1 = 'flb'
            if mode.endswith('-alt'):
                k2 = 'alt'
            else:
                k2 = 'normal'
            embed['thumb'] = data['base']['img']
            embed['fields'] += [
                {
                    'name':     ut.SPACE,
                    'value':    self.update_tl_embed_key(k1, k2, 'ub', 1),
                    'inline':   False
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'ub_jp', 2),
                    'value':    data[k1][k2]['ub']['jp'],
                    'inline':   True
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'ub_en', 2),
                    'value':    data[k1][k2]['ub']['en'],
                    'inline':   True
                },
                {
                    'name':     ut.SPACE,
                    'value':    self.update_tl_embed_key(k1, k2, 'sk1', 1),
                    'inline':   False
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk1_jp', 2),
                    'value':    data[k1][k2]['sk1']['jp'],
                    'inline':   True
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk1_en', 2),
                    'value':    data[k1][k2]['sk1']['en'],
                    'inline':   True
                },
                {
                    'name':     ut.SPACE,
                    'value':    self.update_tl_embed_key(k1, k2, 'sk1+', 1),
                    'inline':   False
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk1+_jp', 2),
                    'value':    data[k1][k2]['ue']['sk1']['jp'],
                    'inline':   True
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk1+_en', 2),
                    'value':    data[k1][k2]['ue']['sk1']['en'],
                    'inline':   True
                },
                {
                    'name':     ut.SPACE,
                    'value':    self.update_tl_embed_key(k1, k2, 'sk2', 1),
                    'inline':   False
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk2_jp', 2),
                    'value':    data[k1][k2]['sk2']['jp'],
                    'inline':   True
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk2_en', 2),
                    'value':    data[k1][k2]['sk2']['en'],
                    'inline':   True
                },
                {
                    'name':     ut.SPACE,
                    'value':    self.update_tl_embed_key(k1, k2, 'sk3', 1),
                    'inline':   False
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk3_jp', 2),
                    'value':    data[k1][k2]['sk3']['jp'],
                    'inline':   True
                },
                {
                    'name':     self.update_tl_embed_key(k1, k2, 'sk3_en', 2),
                    'value':    data[k1][k2]['sk3']['en'],
                    'inline':   True
                }
            ]
        else:
            embed['thumb'] = data['base']['ue_data']['img']
            embed['fields'] += [
                {
                    'name': ut.SPACE,
                    'value': 'UE Name',
                    'inline': False
                },
                {
                    'name': 'uename_jp',
                    'value': data['base']['ue_data']['name']['jp'],
                    'inline': True
                },
                {
                    'name': 'uename_en',
                    'value': data['base']['ue_data']['name']['en'],
                    'inline': True
                },
                {
                    'name': ut.SPACE,
                    'value': 'UE Text',
                    'inline': False
                },
                {
                    'name': 'uetext_jp',
                    'value': data['base']['ue_data']['text']['jp'],
                    'inline': True
                },
                {
                    'name': 'uetext_en',
                    'value': data['base']['ue_data']['text']['en'],
                    'inline': True
                }
            ]

        temp = []
        for field in embed['fields']:
            if not field['value']:
                field['value'] = null
            temp.append(field)
        
        embed['fields'] = temp
        return ut.embed_contructor(**embed)

    def update_tl_embed_key(self, k1, k2, field, mode=1):
        """
        mode 1 (default): make section title
        mode 2: make field key
        """
        # k1 = base/flb
        # k2 = normal/alt
        # field = ub, sk1, sk1+, sk2, sk3
        if mode == 1:
            suffix = ''
            d1 = {
                'ub': 'Union Burst',
                'sk1': 'Skill 1',
                'sk1+': 'Skill 1+',
                'sk2': 'Skill 2',
                'sk3': 'Skill 3'
            }
            d2 = {
                'base':     '',
                'normal':   '',
                'flb':      '+',
                'alt':      ' Alt'
            }
            d3 = {
                'base':     '',
                'normal':   '',
                'flb':      '+',
                'alt':      ' Alt'
            }
        else:
            field, suffix = field.split('_')
            d1 = {
                'ub': 'ub',
                'sk1': 'sk1',
                'sk1+': 'sk1+',
                'sk2': 'sk2',
                'sk3': 'sk3'
            }
            d2 = {
                'base':     '',
                'normal':   '',
                'flb':      'p',
                'alt':      'a',
            }
            d3 = {
                'base':     '',
                'normal':   '',
                'flb':      'p',
                'alt':      'a'
            }
        
        return d1[field] + d2[k1] + d3[k2] + suffix
            
    def make_tags_string(self, tags, mode=1):
        """
        mode 1 (default): make string
        mode 2: tags string -> array of tags
        """
        if not tags:
            return 'N/A'
        elif mode == 1:
            return ', '.join(tags)
        elif mode == 2:
            return tags.split(', ')

    # sub update function
    async def update_exskills(self, ctx, data_all, save_db=False):
        channel = ctx.channel
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel and \
                    not msg.content.startswith('--')

        with open(ut.full_path(self.rel_path, self.hatsu_cf['exskills'])) as exf:
            exdb = json.load(exf)
        
        msg = 'New EX skill - set via `set:`, exit via `exit`:\n{}'
        active = None
        for chara in data_all:
            for key in ['base', 'flb']:
                ex = chara[key]['ex']['jp']
                if not ex:
                    continue
                elif not ex in exdb:
                    active = await channel.send(msg.format(ex))

                    while True:
                        inp = await self.client.wait_for('message', check=check)
                        content = inp.content
                        await inp.delete()

                        if content == 'exit':
                            break
                        elif content.startswith('set'):
                            text = content.split(':')[-1].capitalize()
                            exdb[ex] = text
                            await active.edit(content=msg.format(ex)+f"\nset: {text}")
                
                chara[key]['ex']['en'] = exdb[ex]
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['exskills']), 'w+') as exf:
            exf.write(json.dumps(exdb, indent=4))

        if save_db:
            with open(ut.full_path(self.rel_path, self.hatsu_cf['database']), 'w+') as dbf:
                dbf.write(json.dumps({'units': data_all}, indent=4))
        
        if active:
            await active.edit(content="Finished updating EX skills")
        else:
            await channel.send("Finished updating EX skills")

        return data_all

    # sub update function
    async def update_assets(self, ctx):
        await self.update_local_assets(ctx)
        await self.update_server_assets(ctx)
        await self.load_res()

    async def update_local_assets(self, ctx):
        index = self.make_expected_asset_index()
        local = self.make_local_asset_index()
        
        for chara in index:
            # check normal
            if not chara['sname'] in local:
                name = chara['sname']
                success = self.grab_estertion_asset(chara['img'], ut.full_path(self.rel_path, self.hatsu_cf['assets'], f"{name}.png"))
                if success:
                    await ctx.channel.send(f"Grabbed `{name}`")
                else:
                    await ctx.channel.send(f"Failed to grab `{name}`")

            # check flb
            if chara['flb'] and not (chara['sname']+'6') in local:
                name = chara['sname'] + '6'
                success = self.grab_estertion_asset(chara['img6'], ut.full_path(self.rel_path, self.hatsu_cf['assets'], f"{name}.png"))
                if success:
                    await ctx.channel.send(f"Grabbed `{name}`")
                else:
                    await ctx.channel.send(f"Failed to grab `{name}`")
        
        await ctx.channel.send("Finished updating local assets")

    def grab_estertion_asset(self, link, path):
        try:
            asset = Image.open(BytesIO(requests.get(link).content))
        except:
            return False
        else:
            asset.save(path)
            asset.close()
            return True

    def make_expected_asset_index(self):
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as db:
            dbf = json.load(db)
        
        temp = []
        for chara in dbf['units']:
            temp.append(
                {
                    'sname': chara['sname'],
                    'flb':  chara['flb']['active'],
                    'img': chara['base']['img'],
                    'img6': chara['flb']['img']
                }
            )
        
        return temp

    def make_local_asset_index(self):
        return [i.split('\\')[-1].split('.')[0] for i in glob(ut.full_path(self.rel_path, self.hatsu_cf['assets'], '*.png'))]

    async def update_server_assets(self, ctx):
        """
        This can only be done after updating local assets or weird stuff might happen
        """
        index = self.make_local_asset_index()
        guild_ids, res = self.make_server_asset_index()

        #print(index)
        #print(res)
        print(guild_ids)

        status = None
        full = []
        for asset in index:
            if not (asset in res):
                for id in guild_ids:
                    
                    if id in full:
                        continue

                    guild = await self.client.fetch_guild(id)

                    if guild.emoji_limit == len(guild.emojis):
                        #guild_ids.pop(guild_ids.index(id))
                        full.append(id)
                        await ctx.channel.send(f"{guild.name} - full")
                        status = None
                        continue

                    else:
                        if not status:
                            status = await ctx.channel.send(f"{guild.name} - {guild.emoji_limit - len(guild.emojis)} free")
                        else:
                            await status.edit(content=f"{guild.name} - {guild.emoji_limit - len(guild.emojis)} free")

                        with open(ut.full_path(self.rel_path, self.hatsu_cf['assets'], f"{asset}.png"), 'rb') as img:
                            try:
                                await guild.create_custom_emoji(name=asset, image=img.read())
                            except Exception as e:
                                await ctx.channel.send(f"Failed to add {asset}")
                            else:
                                await ctx.channel.send(f"Added {asset}")
                                break
        
        await ctx.channel.send("Finished updating server assets")

    def make_server_asset_index(self):
        server_ids = [int(i) for i in self.client.config['resource_servers']]
        res = []
        for id in server_ids:
            guild = self.client.get_guild(id)
            res += list(guild.emojis)
        return server_ids, [e.name for e in res]

    async def load_res(self):
        server_ids = self.client.config['resource_servers']
        res = {}
        for id in server_ids:
            guild = await self.client.fetch_guild(id)
            for emote in guild.emojis:
                res[emote.name] = {
                    'name': emote.name,
                    'id': emote.id,
                    'full': f"<:{emote.name}:{emote.id}>"
                }
        
        self.res = res
        self.client.hatsu_res = res # update variable

    # sub update function
    async def update_gacha(self, ctx): #FIXME
        channel = ctx.channel
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel and \
                    not msg.content.startswith('--')

        with open(ut.full_path(self.rel_path, self.hatsu_cf['gacha'])) as p:
            gacha = json.load(p)
        
        msg = "Updating gacha. Command keys: `prifes`, `double`, `lim`, `ssr`, `sr`, `r`, `exit`\n"\
            "`prifes/double` -> `prifes/double:0|1`\n"\
            "`pools` -> `pools:sname,...`\n"\
            "`lim` will always replace while the rest will always append\n"
        status = await channel.send(msg)
        while True:
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            if content == 'exit':
                break

            cmd, options = content.split(':')

            if cmd in ['prifes', 'double']:
                try:
                    options = int(options)
                except:
                    pass
                options = True if options == 1 else False
                gacha[cmd] = options
                await status.edit(content=msg+f"Set `{cmd}` to `{options}`")

            elif cmd.startswith('lim'):
                gacha['pools']['lim'] = [i.strip().lower() for i in options.split(',') if i]
                await status.edit(content=msg+f"Set limited pool to `{gacha['pools']['lim']}`")

            elif cmd in ['ssr', 'sr', 'r']:
                append = [i.strip().lower() for i in options.split(',') if i]
                gacha['pools'][cmd] += append
                await status.edit(content=msg+f"Appended {append} to {cmd} pool")
            
            else:
                await status.edit(content=msg+f"Unknown command: `{content}`")
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['gacha']), 'w+') as p:
            p.write(json.dumps(gacha, indent=4))
        
        await channel.send('Finished updating gacha')
    
    # sub update function
    async def update_prefix(self, ctx):
        channel = ctx.channel
        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel and \
                    not msg.content.startswith('--')

        with open(ut.full_path(self.rel_path, self.hatsu_cf['prefix'])) as p:
            prefixes = json.load(p)
        
        msg = "Updating prefixes. Command keys: `prefix`, `alias`, `exit`.\n"\
            "`prefix` -> `prefix:p,full,short(SINGLE)`\n"\
            "`alias` -> `alias:prefix_alias:prefix(SINGLE)`\n"\
            "Commands will always append unless entry is a duplicate\n"
        status = await channel.send(msg)
        overwrite = False
        while True:
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            if content == 'exit':
                break

            elif content.startswith('prefix'):
                pkv = content.split(':')[1]
                p, k, v = pkv.split(',')

                if p in prefixes['prefixes'] and not overwrite:
                    await status.edit(content=msg+f"prefix `{p}` already exists in prefixes: `{prefixes['prefixes'][p]}`. Enter again to overwrite")
                    overwrite = True
                    continue
                elif p in list(prefixes['prefix_alias'].values()):
                    await status.edit(content=msg+f"prefix `{p}` already exists in prefix_alias!")
                    continue
                else:
                    overwrite = False
                    k = k.title()
                    v = v.title()
                    prefixes['prefixes'][p] = {
                        'full': k,
                        'short': v if v else None
                    }
                    await status.edit(content=msg+f"prefix: set {p} -> {prefixes['prefixes'][p]}")
            
            elif content.startswith('alias'):
                pa = content.split(':')[1]
                p, a = [i.lower() for i in pa.split(',')]

                if a in prefixes['prefixes']:
                    await status.edit(content=msg+f"prefix `{a}` already exists in prefixes: `{prefixes['prefixes'][a]}`!")
                    continue
                elif a in prefixes['prefix_alias'].values() and not overwrite:
                    await status.edit(content=msg+f"prefix `{a}` already exists in prefix_alias: `{prefixes['prefix_alias'][a]}`. Enter again to overwrite")
                    overwrite = True
                    continue
                else:
                    overwrite = False
                    prefixes['prefix_aliax'][a] = p
                    await status.edit(content=msg+f"prefix: set {a} -> {p}")
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['prefix']), 'w+') as p:
            p.write(json.dumps(prefixes, indent=4))
            self.prefixes = prefixes
        
        await channel.send('Finished updating prefixes')

    async def validate_database(self, channel):
        # make sure format of database values are correct
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as db:
            dbf = json.load(db)
        
        # write backup in case something goes wrong
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database']+'.bak'), 'w+') as dbb:
            dbb.write(json.dumps(dbf, indent=4))
        
        dbf_clean = {'units':[]}
        for chara in dbf['units']:
            chara['sname'] = chara['sname'].lower()
            chara['name']['en'] = chara['name']['en'].lower()
            chara['sname'] = chara['name']['en'] if not chara['prefix'] else chara['prefix'] + chara['name']['en']
            chara = self.update_img(chara)
            dbf_clean['units'].append(chara)
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database']), 'w+') as db:
            db.write(json.dumps(dbf_clean, indent=4))

        await channel.send('Validated DB')
        
    def get_full_name(self, name:str, prefix:str, short=False):
        if prefix:
            p = self.prefixes['prefixes'].get(prefix, None)
            if not p:
                pf = '???'
            elif p == 'k':
                return name.title()
            elif short:
                pf = p['short'] if p['short'] else p['full']
            else:
                pf = p['full']

            return f"{name.title()} ({pf.title()})"
        else:
            return name.title()

    def get_name(self, data, short=False):
        if data['prefix'] == 'k':
            name_en = " & ".join(data['kizuna']).title()
        else:
            name_en = data['name']['en']

        return self.get_full_name(name_en, data['prefix'], short)

#############################################################################################################
# Hatsune Commands
#############################################################################################################

    def character_help_embed(self):
        embed = {
            'title': 'Character Help',
            'descr': 'Syntax: `.character [prefix.][name] [option]`\nAliases: `c`, `chara`, `ue`, `card`, `profile`, `stats`',
            'footer': {'text': 'Character Search', 'url': self.client.user.avatar.url},
        }
        temp = []
        temp.append( 
            {
                'name': '`[prefix.]` optional',
                'value': 'Specifies the character variant to fetch. If omitted, the base character will be fetched. See below for a list of all registered prefixes.',
                'inline': False
            }
        )
        all_prefixes = sorted(list(self.prefixes['prefixes'].items()), key=lambda x: x[-1]['full'])
        
        # experimental
        with open(ut.full_path(self.rel_path, self.hatsu_cf['index'])) as i:
            index = json.load(i)
        
        for item in all_prefixes:
            found = False
            for chara in index['index']:
                if chara['prefix'] == item[0]:
                    item[-1]['eg'] = '.'.join([item[0], chara['name']['en']])
                    found = True
                    break
            
            if not found:
                item[-1]['eg'] = 'N/A'
        
        temp += [
            {
                'name': 'Variant',
                'value': '\n'.join([i[-1]['full'] for i in all_prefixes]),
                'inline': True
            },
            {
                'name': 'Prefix',
                'value': '\n'.join([i[0] for i in all_prefixes]),
                'inline': True
            },
            {
                'name': 'Example',
                'value': '\n'.join([i[-1]['eg'] for i in all_prefixes]),
                'inline': True
            }
        ]

        temp.append(
            {
                'name': '`[name]` required',
                'value': 'Name of the character in interest. Can be an alias. See `.alias help` for more info.',
                'inline': False
            }
        )

        temp.append(
            {
                'name': '`[option]` optional',
                'value': 'Additional option specification. See below for a list of all valid options.',
                'inline': False
            }
        )
        temp += [
            {
                'name': 'Option',
                'value': '\n'.join([
                    'ue',
                    'flb'
                ]),
                'inline': True
            },
            {
                'name': 'Description',
                'value': '\n'.join([
                    "Access the unique weapon page",
                    "Access the FLB (6⭐) variant."
                ]),
                'inline': True
            }
        ]

        embed['fields'] = temp
        return ut.embed_contructor(**embed)

    def alias_help_embed(self):
        embed = {
            'title': 'Alias Help',
            'descr': 'Usage: `.alias [mode]`',
            'footer': {'text': 'Alias', 'url': self.client.user.avatar.url},
            'fields': [
                {
                    'name': '> `[mode]` default',
                    'value': 'Syntax: `.alias [name/alias]`\n'\
                        'Enter in a character `name` to check for all their aliases. Likewise, enter in an `alias` to see who it points to.',
                    'inline': False
                },
                {
                    'name': '> `[mode]` add',
                    'value': 'Syntax: `.alias add [alias], [name]`\n'\
                        'Add the following `alias` to the character `name`. `alias` must not already exist.',
                    'inline': False
                },
                {
                    'name': '> `[mode]` edit',
                    'value': 'Syntax: `.alias edit [alias], [name]`\n'\
                        'Change who `alias` points to. `alias` must already exist.',
                    'inline': False
                },
                {
                    'name': '> `[mode]` remove',
                    'value': 'Syntax: `.alias remove [alias]`\n'\
                        'Deletes the `alias`. `alias` must already exist',
                    'inline': False
                }
            ]
        }
        return ut.embed_contructor(**embed)

    def pos_help_embed(self):
        embed = {
            'title': 'Position Help',
            'descr': 'Syntax: `.pos [field/character]`\n'\
                'Enter in a `field` to see the lineup for that field. Valid fields are: `v` for vanguard, `m` for migduard, `r` for rearguard. '\
                'Enter in a `character` to see their lineup.',
            'footer': {'text': 'Pos', 'url': self.client.user.avatar.url}
        }
        return ut.embed_contructor(**embed)

    def gacha_help_embed(self):
        embed = {
            'title': 'Gacha Help',
            'footer': {'text': 'Gacha', 'url': self.client.user.avatar.url},
            'fields': [ 
                {
                    'name': '[CMD] gacha',
                    'value': 'Syntax: `.gacha [rolls]`\n'\
                        'Gacha `rolls` times. Please keep the number sensible.',
                    'inline': False
                },
                {
                    'name': '[CMD] spark',
                    'value': 'Syntax: `.spark [character]`\n'\
                        'Spark for a `character`. `character` must be in the rateup pool. Functions like `gacha` but will stop when you get your spark target. Will automatically stop at 200 unless you add the `nl` option.',
                    'inline': False
                }
            ]
        }
        return ut.embed_contructor(**embed)
    
    def tag_help_embed(self):
        pass

    async def hatsune_help(self, ctx, mode):
        # make all help embeds
        pages = {
            'chara': self.character_help_embed(),
            'alias': self.alias_help_embed(),
            'pos': self.pos_help_embed(),
            'gacha': self.gacha_help_embed(),
            'tag': None
        }

        page = self.hatsunehelpPage(ctx, pages, mode, self.hatsunehelpView(), self.client.emotes['derp'])
        await page.start()

    class hatsunehelpView(ut.baseViewHandler):
        def __init__(self, timeout=90):
            super().__init__(timeout)

        def remake_buttons(self):
            super().clear_items()
            for button in self.pageHandler.make_buttons():
                super().add_item(button)

        async def clean_up(self):
            super().stop()
            await self.pageHandler.main_message.edit(content=self.pageHandler.derp, embed=None, view=None)
        
        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            if interaction.user != self.pageHandler.ctx.author:
                return True

            inter_id = interaction.data.get('custom_id', None)
            if inter_id.startswith(self.pageHandler.base_id):
                _id = inter_id.split('_')[-1]

                if _id == 'del':
                    await self.clean_up()
                else:
                    await self.pageHandler.refresh(_id)
                
                return True

        async def on_timeout(self):
            await self.clean_up()

    class hatsunehelpPage(ut.basePageHandler):
        def __init__(self, ctx, pages, mode, view, derp):
            self.base_id    = 'hatsuhelp_'
            self.ctx        = ctx
            self.pages      = pages
            self.mode       = mode
            self.view       = view
            self.derp       = derp

            super().__init__(ctx.channel)
            self.view.pass_pageHandler(self)

        def make_buttons(self):
            button_chara = nextcord.ui.Button(
                custom_id=self.base_id+'chara',
                label='character',
                disabled=self.mode=='chara',
                style=nextcord.ButtonStyle.secondary if not self.mode=='chara' else nextcord.ButtonStyle.success
            )
            button_alias = nextcord.ui.Button(
                custom_id=self.base_id+'alias',
                label='alias',
                disabled=self.mode=='alias',
                style=nextcord.ButtonStyle.secondary if not self.mode=='alias' else nextcord.ButtonStyle.success
            )
            button_pos = nextcord.ui.Button(
                custom_id=self.base_id+'pos',
                label='position',
                disabled=self.mode=='pos',
                style=nextcord.ButtonStyle.secondary if not self.mode=='pos' else nextcord.ButtonStyle.success
            )
            button_gacha = nextcord.ui.Button(
                custom_id=self.base_id+'gacha',
                label='gacha',
                disabled=self.mode=='gacha',
                style=nextcord.ButtonStyle.secondary if not self.mode=='gacha' else nextcord.ButtonStyle.success
            )
            button_tags = nextcord.ui.Button(
                custom_id=self.base_id+'tags',
                label='tags',
                disabled=True, #self.mode=='chara',
                style=nextcord.ButtonStyle.secondary #if not self.mode=='tags' else nextcord.ButtonStyle.success
            )
            button_del = nextcord.ui.Button(
                custom_id=self.base_id+'del',
                label='\u00D7',
                style=nextcord.ButtonStyle.danger
            )
            return [
                button_chara,
                button_pos,
                button_tags,
                button_alias,
                button_gacha,
                button_del
            ]

        async def start(self):
            self.view.remake_buttons()
            await super().main_message_send(embed=self.pages[self.mode], view=self.view)

        async def refresh(self, mode):
            self.mode = mode     
            self.view.remake_buttons()
            await self.main_message.edit(embed=self.pages[self.mode], view=self.view)
        
    def process_request(self, cmd:str):
        """
        Processes command input and if successful returns:
            d = {option, prefix, name, sname}
        else:
            None
        """
        # (prefix.)character (option)
        # (prefix)character (option)
        # (prefix) character (option)

        cmd = cmd.lower()
        # firstly check if last request is an option
        cmd = cmd.split()
        if cmd[-1] in ['ue', 'flb', 'ex']:
            option = cmd[-1]
            cmd = cmd[:-1]
        else:
            option = None
        
        # check if remaining command list is len 1 or 2
        if len(cmd) == 1:
            raw_name = cmd[0]
            raw_prefix = None
        elif len(cmd) == 2:
            raw_prefix, raw_name = cmd
        else:
            return None
        
        # check if '.' is inside raw_name
        if '.' in raw_name:
            raw_prefix, raw_name = raw_name.split('.')
        
        if not raw_prefix: raw_prefix = None

        # run both name and prefix through aliases
        raw_name = self.aliases.get(raw_name, raw_name)
        raw_prefix = self.prefixes['prefix_alias'].get(raw_prefix, raw_prefix)

        return {
            'option': option, 
            'name': raw_name, 
            'prefix': raw_prefix, 
            'sname': raw_name if not raw_prefix else raw_prefix+raw_name
            }
    
    def fetch_chara(self, payload):
        if not payload:
            return None
           
        SUCCESS = False
        FALLBACK = False
        # look for chara in index
        with open(ut.full_path(self.rel_path, self.hatsu_cf['index'])) as i:
            index = json.load(i)

        # check sname
        target = list(filter(lambda x: x['sname'] == payload['sname'], index['index']))

        # check enum alias if above fails
        if len(target) == 0:
            target = list(filter(lambda x: payload['sname'] in x['enum_alias'], index['index']))
        
            # fallback on default chara
            if len(target) == 0:
                target = list(filter(lambda x: payload['name'] == x['name']['en'] and x['prefix'] == None, index['index']))
                # fail the search if nothing is found
                if len(target) == 0:
                    return None
                else:
                    FALLBACK = True
            else:
                SUCCESS = True
        else:
            SUCCESS = True
        
        target = target[0]
        
        # fetch similar characters... unless the chara is kizuna... or a collab chara (CGirls)
        if target['prefix'] != 'k':
            others = list(filter(
                lambda x: (x['name']['en'] == target['name']['en'] or target['name']['en'] in x['kizuna']) and x['prefix'] != target['prefix'] and x['prefix'] != 'd',
                index['index']
            ))
        else:
            others = []
        
        # load actual data
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as f:
            dbf = json.load(f)
        
        temp = []
        target = list(filter(lambda x: x['hnid'] == target['hnid'], dbf['units']))[0]
        for chara in others:
            temp.append(
                list(filter(lambda x: x['hnid'] == chara['hnid'], dbf['units']))[0]
            )
        
        return {'success': SUCCESS, 'fallback': FALLBACK, 'target': target, 'others': temp, 'target_index': dbf['units'].index(target) if SUCCESS or FALLBACK else None}

    class charaPage(ut.basePageHandler):
        """
        controller: dict->{
            'sname(button_id): {
                'b_flb'     : bool
                'b_alt'     : bool
                'base': {
                    'normal'    : embed,
                    'alt'       : embed | None
                },
                'flb': {
                    'norm'      : embed,
                    'alt'       : embed | None
                }
                'ue'        : {'norm': embed}
                'card'      : {'norm': embed, 'flb': embed | None
                'stats'     : {'norm': embed, 'flb': embed | None
                'profile'   : {'norm': embed}
            }, ...
        }
        buttons: dict->{
            'button_id': {
                'emote': str
                'label': str(prefix short) | None
            }
        }
        """
        def __init__(self, ctx, to_emote:str, active_chara:str, active_page:str, active_subpage:str, controller:dict, buttons:dict, view):
            self.ctx            = ctx
            self.controller     = controller
            self.buttons        = buttons
            self.view           = view
            self.to_emote       = to_emote

            self.active_chara   = active_chara
            self.active_page    = active_page
            #self.active_subpage = active_subpage
            self.b_flb          = active_subpage == 'flb'
            self.b_alt          = False

            #self.active         = None
            self.base_id        = 'ames_charaPageView_'

            super().__init__(ctx.channel)
            self.view.pass_pageHandler(self)

            #print(json.dumps(controller['hatsune']['flb']['norm'].to_dict(),indent=4))
        
        def fetch_active_embed(self):
            base = self.controller[self.active_chara]

            #print('-'*15, self.b_flb, self.b_alt, base['b_flb'], base['b_alt'], self.active_chara, self.active_page, sep='\n')

            if self.active_page in ['base', 'stats']:
                if self.active_page == 'stats':
                    k1 = 'stats-flb'
                    k2 = 'stats-base'
                else:
                    k1 = 'flb'
                    k2 = 'base'

                #print(self.b_flb and base['b_flb'])
                embed = base.get(k1 if self.b_flb and base['b_flb'] else k2, base[k2])
                #print(embed['norm'].title, base['flb']['norm'].title, sep='\n')
                #print(json.dumps(embed['norm'].to_dict(),indent=4))
                embed = embed.get(
                    'alt' if self.b_alt and base['b_alt'] else 'norm', 
                    embed['norm']
                    )
            elif self.active_page == 'card':
                embed = base[self.active_page].get(
                    'flb' if self.b_flb and base['b_flb'] else 'norm', 
                    base[self.active_page]['norm']
                    )
            else:
                embed = base[self.active_page]['norm']

            #print(json.dumps(embed.to_dict(), indent=2))
            return embed
        
        def make_default_buttons(self):
            #print(self.controller[self.active_chara]['b_flb'], self.controller[self.active_chara]['b_alt'], sep='\n')
            button_base = nextcord.ui.Button(
                custom_id=self.base_id+'base',
                label='Skills',
                emoji='<:_chara:677763373739409436>',
                disabled=self.active_page=='base',
                style=nextcord.ButtonStyle.secondary if not self.active_page=='base' else nextcord.ButtonStyle.success
            )
            button_ue = nextcord.ui.Button(
                custom_id=self.base_id+'ue',
                label='UE',
                emoji='<:_ue:677763400713109504>',
                disabled=self.active_page=='ue',
                style=nextcord.ButtonStyle.secondary if not self.active_page=='ue' else nextcord.ButtonStyle.success
            )
            button_card = nextcord.ui.Button(
                custom_id=self.base_id+'card',
                label='Art',
                emoji='<:_card:677763353069879306>',
                disabled=self.active_page=='card',
                style=nextcord.ButtonStyle.secondary if not self.active_page=='card' else nextcord.ButtonStyle.success
            )
            button_stats  = nextcord.ui.Button(
                custom_id=self.base_id+'stats',
                label='Adv.Stats',
                emoji='<:_stats:678081583995158538>',
                disabled=self.active_page=='stats',
                style=nextcord.ButtonStyle.secondary if not self.active_page=='stats' else nextcord.ButtonStyle.success
            )
            button_profile = nextcord.ui.Button(
                custom_id=self.base_id+'profile',
                label='Profile',
                emoji='<:_profile:718471302460997674>',
                disabled=self.active_page=='profile',
                style=nextcord.ButtonStyle.secondary if not self.active_page=='profile' else nextcord.ButtonStyle.success
            )
            button_alt = nextcord.ui.Button(
                custom_id=self.base_id+'alt',
                label='Alt',
                emoji='🔀',
                disabled=not self.controller[self.active_chara]['b_alt'],
                style=nextcord.ButtonStyle.secondary if not self.b_alt else nextcord.ButtonStyle.success
            )
            if button_alt.disabled:
                button_alt.style = nextcord.ButtonStyle.danger
            button_flb = nextcord.ui.Button(
                custom_id=self.base_id+'flb',
                label='FLB',
                emoji='⭐',
                disabled=not self.controller[self.active_chara]['b_flb'],
                style=nextcord.ButtonStyle.secondary if not self.b_flb else nextcord.ButtonStyle.success
            )
            if button_flb.disabled:
                button_flb.style = nextcord.ButtonStyle.danger
            button_del = nextcord.ui.Button(
                custom_id=self.base_id+'del',
                label='\u00D7',
                style=nextcord.ButtonStyle.danger
            )
            return [
                button_base,
                button_ue,
                button_card,
                button_stats,
                button_profile,
                button_alt,
                button_flb,
                button_del
            ]

        def make_alt_chara_buttons(self):
            temp = []
            for id, pref in self.buttons.items():
                temp.append(
                    nextcord.ui.Button(
                        custom_id=self.base_id+id,
                        label=pref['label'],
                        emoji=pref['emote'],
                        disabled=self.active_chara == id,
                        style=nextcord.ButtonStyle.success if self.active_chara == id else nextcord.ButtonStyle.primary
                    )
                )
            return temp

        def make_buttons(self):
            return self.make_alt_chara_buttons() + self.make_default_buttons()

        async def start(self):
            self.view.remake_buttons()
            await super().main_message_send(embed=self.fetch_active_embed(), view=self.view)

        async def refresh(self, **kwargs):
            sname = kwargs.get('sname', None)
            page = kwargs.get('page', None)
            mode = kwargs.get('mode', None)

            if sname:
                self.active_chara = sname
            elif page:
                self.active_page = page
            elif mode == 'flb':
                self.b_flb = not self.b_flb
            elif mode == 'alt':
                self.b_alt = not self.b_alt
            
            self.view.remake_buttons()
            await self.main_message.edit(embed=self.fetch_active_embed(), view=self.view)

    class charaPageView(ut.baseViewHandler):
        def __init__(self, timeout):
            super().__init__(timeout)
        
        def remake_buttons(self):
            super().clear_items()
            for button in self.pageHandler.make_buttons():
                super().add_item(button)
            
        async def clean_up(self, reason):
            super().stop()
            s = "This embed has been deleted " if reason == 'del' else "This embed has timed out "
            s += self.pageHandler.to_emote
            await self.pageHandler.main_message.edit(content=s, embed=None, view=None)

        async def interaction_check(self, interaction:nextcord.Interaction):
            if interaction.user != self.pageHandler.ctx.author:
                return True

            inter_id = interaction.data.get('custom_id', None)
            #if inter_id.startswith(self.pageHandler.base_id):
            _id = inter_id.split('_')[-1]
            if _id == 'del':
                await self.clean_up('del')

            elif _id in self.pageHandler.buttons:
                await self.pageHandler.refresh(sname=_id)

            elif _id in ['alt', 'flb']:
                await self.pageHandler.refresh(mode=_id)
                
            else:
                await self.pageHandler.refresh(page=_id)

            return True
        
        async def on_timeout(self):
            await self.clean_up('timeout')

    @commands.command(aliases=[
        'c', 'chara', 
        'ue', 
        'card', 
        'profile', 
        'stats']
        )
    async def character(self, ctx, *, options):
        channel = ctx.channel
        #author = ctx.author

        if not options:
            await channel.send('No input')
            return
        elif options.split()[0].lower() == 'help':
            await self.hatsune_help(ctx, 'chara')
            return
        
        # find landing page
        if ctx.invoked_with in ['c', 'chara']:
            landing = 'base'
        else:
            landing = ctx.invoked_with
        
        # process
        request = self.process_request(options)
        charas = self.fetch_chara(request)
        if request is None or charas is None:
            await channel.send(f"Failed to find `{options}`")
            return
        
        # quit if not success
        if not charas['success'] and not charas['fallback']:
            await channel.send(f"Failed to find {request['sname']}")
            return

        # render chara embeds
        controller = {}
        buttons = {}
        for chara in [charas['target']] + charas['others']:
            controller[chara['sname']] = self.make_chara_embeds(chara, request['option'] == 'ex')

            #print(json.dumps(controller['hatsune']['flb']['norm'].to_dict(), indent=4))
            #raise Exception('break')

            if chara['prefix']:
                label = self.prefixes['prefixes'][chara['prefix']]['short']
                if not label:
                    label = self.prefixes['prefixes'][chara['prefix']]['full']
            else:
                label = 'Base'

            buttons[chara['sname']] = {
                'label': label + (f" ({chara['prefix']})" if chara['prefix'] else ''),
                'emote': self.res[chara['sname']]['full']
            }
        
        # init handler class
        if not request['option']:
            subpage = 'norm'
        elif request['option'] == 'ex':
            subpage = 'norm'
        else:
            subpage = request['option']

        character = self.charaPage(
            ctx, self.client.emotes['derp'], charas['target']['sname'], landing, subpage, controller, buttons, 
            self.charaPageView(90)
        )

        # STARTO
        await character.start()

        # warnings
        if charas['fallback']:
            await channel.send(f"**Warning:** Failed to find **{self.get_full_name(request['name'], request['prefix'])}** but was able to default to base character "+self.client.emotes['derp'])

    def make_chara_embeds(self, data:dict, ex:bool):
        temp = {
            'b_flb' : data['flb']['active'],
            'b_alt' : data['base']['b_alt'],
            'base': {
                'norm'  : None,
                'alt'   : None,
            },
            'flb': {
                'norm'  : None,
                'alt'   : None
            },
            'ue'        : {'norm': None},
            'card'      : {'norm': None, 'flb': None},
            'stats-base': {'norm': None, 'alt': None},
            'stats-flb' : {'norm': None, 'alt': None},
            'profile'   : {'norm': None}
        }

        base_embed = {
            'author': {'text': "ハツネのメモ帳", "icon": self.hatsu_cf['HATSUNE']}
        }

        base    = self.make_chara_base_embeds(copy.deepcopy(base_embed), data, ex)
        ue      = self.make_chara_ue_embed(copy.deepcopy(base_embed), data)
        card    = self.make_chara_card_embed(copy.deepcopy(base_embed), data)
        profile = self.make_chara_profile_embed(copy.deepcopy(base_embed), data)
        stats   = self.make_chara_base_embeds(copy.deepcopy(base_embed), data, ex, 'stats')
        
        # base
        temp['base']['norm']        = ut.embed_contructor(**base['base'])       if base['base'] else None
        temp['base']['alt']         = ut.embed_contructor(**base['base-alt'])   if base['base-alt'] else None
        temp['flb']['norm']         = ut.embed_contructor(**base['flb'])        if base['flb'] else None
        temp['flb']['alt']          = ut.embed_contructor(**base['flb-alt'])    if base['flb-alt'] else None
        # ue
        temp['ue']['norm']          = ut.embed_contructor(**ue)                 if ue else None
        # card
        temp['card']['norm']        = ut.embed_contructor(**card['base'])       if card['base'] else None
        temp['card']['flb']         = ut.embed_contructor(**card['flb'])        if card['flb'] else None
        # stats
        temp['stats-base']['norm']  = ut.embed_contructor(**stats['base'])      if stats['base'] else None 
        temp['stats-base']['alt']   = ut.embed_contructor(**stats['base-alt'])  if stats['base-alt'] else None 
        temp['stats-flb']['norm']   = ut.embed_contructor(**stats['flb'])       if stats['flb'] else None 
        temp['stats-flb']['alt']    = ut.embed_contructor(**stats['flb-alt'])   if stats['flb-alt'] else None 
        # profile
        temp['profile']['norm']     = ut.embed_contructor(**profile)            if profile else None 

        return temp
    
    def make_chara_base_embeds(self, base_embed:dict, data:dict, ex:bool, mode='chara'):
        # key : base        [base]
        # key : base-ue     [base-ue base]
        # key : base-alt    [base-alt base]      
        # key : base-alt-ue [base-alt-ue base-alt base-ue base]
        # key : flb         [flb base-ue base]
        # key : flb-ue      [flb-ue flb base-ue base]
        # key : flb-alt     [flb-alt flb base-alt-ue base-alt base-ue base]
        # key : flb-alt-ue  [flb-alt-ue flb-alt flb-ue flb base-alt-ue base-alt base-ue base]
        flow = {
            'base':         ['base'],
            'base-ue':      ['base-ue', 'base'],
            'base-alt':     ['base-alt', 'base'],
            'base-alt-ue':  ['base-alt-ue', 'base-alt', 'base-ue', 'base'],
            'flb':          ['flb', 'base-ue', 'base'],
            'flb-alt':      ['flb-alt', 'flb', 'base-alt-ue', 'base-alt', 'base-ue', 'base']
        }
        embed_flow = {
            'base':         ['ub-base',     'sk1-base',         'sk1-base-ue',      'sk2-base',     'sk3-base',     'ex-base'],
            'base-alt':     ['ub-base-alt', 'sk1-base-alt',     'sk1-base-alt-ue',  'sk2-base-alt', 'sk3-base-alt', 'ex-base'],
            'flb':          ['ub-flb',                          'sk1-flb',          'sk2-flb',      'sk3-flb',      'ex-flb'],
            'flb-alt':      ['ub-flb-alt',                      'sk1-flb-alt',      'sk2-flb-alt',  'sk3-flb-alt',  'ex-flb']
        }
        all_skills  = {}
        # make all possible skills
        for b_alt, b_flb in [(a, f) for a in (True, False) for f in (True, False)]:
            if not b_alt and not b_flb:
                k1 = 'base'
                k2 = 'normal'
            elif b_alt and not b_flb:
                k1 = 'base'
                k2 = 'alt'
            elif not b_alt and b_flb:
                k1 = 'flb'
                k2 = 'normal'
            else:
                k1 = 'flb'
                k2 = 'alt'
            
            # check
            if b_flb and not data[k1]['active']:
                continue
            elif b_alt and not data[k1]['b_alt']:
                continue

            # base/flb skills (normal/ue/alt/alt-ue)
            for key, value in data[k1][k2].items():
                if key == 'pattern':
                    continue
                elif key != 'ue':
                    skey = '-'.join([i for i in [key, k1, k2 if k2 == 'alt' else ''] if i])
                    all_skills[skey] = self.make_skill(key, value, b_flb, b_alt, False, mode)
                else:
                    for k, v in value.items():
                        skey = '-'.join([i for i in [k, k1, k2 if k2 == 'alt' else '', 'ue'] if i])
                        all_skills[skey] = self.make_skill(k, v, b_flb, b_alt, data[k1]['ue'], mode)
            
            # ex skills
            skey = f"ex-{k1}"
            all_skills[skey] = self.make_skill('ex', data[k1]['ex'], b_flb, b_alt, data[k1]['ue'], mode)


        #print(json.dumps(all_skills, indent=2))
        #raise Exception('breakpoint')
        # CONSTRUCT EMBEDS FROM ALL_SKILLS
        embeds = {}
        for embed_key, embed_layout in embed_flow.items():
            skills = []

            for skill in embed_layout:
                skill_name, _, skill_key = skill.partition('-')

                # check if request is valid
                if embed_key.startswith('flb') and not data['flb']['active']:
                    break
                elif embed_key.endswith('alt') and not data['base']['b_alt']:
                    break

                # collect skills following fallback
                strict = True
                for skill_flow in flow[skill_key]:
                    if skill_name == 'ex' and not ex:
                        break
                    s = all_skills.get(f"{skill_name}-{skill_flow}", None)

                    # strict sk1+ and sk1a+ rules for base embed
                    if 'base' in skill_flow and 'ue' in skill_flow and not s and strict:
                        break
                    else:
                        strict = False

                    if s:
                        skills.append(s)
                        break
            
            # construct embed is skill accumulator is nonempty
            if skills:
                temp = copy.deepcopy(base_embed)
                temp['thumb'] = data['base']['img']
                if embed_key.startswith('flb'):
                    flbs_en = "FLB"
                    flbs_jp = '6⭐'
                    flb_key = 'flb'
                    temp['thumb'] = data['flb']['img']
                else:
                    flbs_en = ''
                    flbs_jp = ''
                    flb_key = ''
                
                if 'alt' in embed_key:
                    alts_en = "SPECIAL"
                    alts_jp = "Alt"
                    alt_key = 'alt'
                else:
                    alts_en = ""
                    alts_jp = ""
                    alt_key = ''

                name_en = self.get_name(data)
                name_en = " ".join([i for i in [name_en, flbs_en, alts_en] if i])
                name_jp = " ".join([i for i in [data['name']['jp'], flbs_jp, alts_jp] if i])
                
                temp['title']    = f"{name_jp}\n{name_en}"

                # BASE/FLB OR STATS-BASE/STATS-FLB
                if mode == 'chara':
                    temp['footer']   = {'text': 'Character Info', 'url': temp['thumb']}

                    atk, pos, ptn1, ptn2, ptn3, tags, aliases, footnote = self.make_profile_common_fields(data, bool(alt_key), b_flb)

                    temp['fields'] = [atk, pos, ptn1, ptn2]
                    if ptn3:
                        temp['fields'].append(ptn3)
                    for skill_group in skills:
                        temp['fields'] += skill_group
                    temp['fields'] += [tags, aliases]

                    if footnote:
                        temp['fields'].append(footnote)

                elif mode == 'stats':
                    temp['footer'] = {'text': 'Character Stats', 'url': temp['thumb']}

                    temp['descr'] = f"{self.get_name(data)}'s stats and skill actions. "\
                        f"Data presented here assumes character is at **LV{data['status']['lvl']} RANK{data['status']['rank']}** "\
                        "and **MAX BOND** across all character variants. Presented stats **DO** include stats from UE."
                    
                    temp['fields'] = []
                    
                    raw_stats = [f"{self.hatsu_cf['ue_abbrev'][k].upper()}: {v}" for k,v in data[flb_key if flb_key else 'base']['stats'].items()]
                    for chunk in ut.chunks(raw_stats, 6):
                        temp['fields'].append(
                            {
                                'name': 'Stats',
                                'value': '\n'.join(chunk),
                                'inline': True
                            }
                        )
                    
                    for skill_group in skills:
                        temp['fields'] += skill_group

            else:
                temp = None
            
            embeds[embed_key] = temp
        
        #print(json.dumps(embeds['flb'], indent=4))
        #raise Exception('breakpoint')
        return embeds
                
    def make_skill(self, key, value, b_flb, b_alt, b_ue, mode='chara'):
        if not value['jp']:
            return None

        title_dict = {
            'ub': '> <:_ub:953873051462795266> Union Burst',
            'sk1': '> 1\u20E3 Skill 1',
            'sk2': '> 2\u20E3 Skill 2',
            'sk3': '> 3\u20E3 Skill 3',
            'ex':  '> <:_stats:678081583995158538> EX Skill'
        }
        title = title_dict[key]
        if b_alt:
            title += ' Special'
        if b_ue and key == 'sk1':
            title += '+'
        if b_flb and key == 'ub':
            title += '+'
        
        if mode == 'chara':
            temp = [
                {
                    'name': title,
                    'value': f"「{value['name']['jp']}」",
                    'inline': False
                },
                {
                    'name': 'Description',
                    'value': value['jp']
                },
                {
                    'name': ut.SPACE,
                    'value': value['en'] if value['en'] else '...'
                }
            ]
        else:
            actions = '\n'.join(['-'+i for i in value['actions']])
            temp = [
                {
                    'name': title,
                    'value': f"「{value['name']['jp']}」",
                    'inline': False
                },
                {
                    'name': 'Description',
                    'value': value['en']
                },
                {
                    'name': ut.SPACE,
                    'value': f"```glsl\n{actions}```" if value['actions'] else '...'
                }
            ]

        return temp

    def make_profile_common_fields(self, data, b_alt, b_flb):
        # attacker type
        # position
        # attack pattern (could contain SPEC data)
        # tags
        # aliases
        field = {
            'name': ut.SPACE,
            'value': ut.SPACE,
            'inline': True
        }
        pos_field = [
            'Vanguard',
            'Midguard',
            'Rearguard'
        ]  

        # attacker type
        attacker = copy.deepcopy(field)
        attacker['name'] = '> Attacker Type'
        attacker['value'] = 'Magic Attacker' if data['type'] == 0 else 'Physical Attacker'

        # position
        pos = copy.deepcopy(field)
        pos['name'] = "> Position"
        pos['value'] = pos_field[data['pos_field']]
        pos['inline'] = False

        # attack pattern
        attack_pattern_1 = copy.deepcopy(field)
        attack_pattern_2 = copy.deepcopy(field)

        attack_pattern_1['name'] = '> Attack Pattern'
        attack_pattern_1['value'] = 'Initial:\nLooping:'
        #attack_pattern_1['inline'] = False
        attack_pattern_2['value'] = self.make_atkptn(data, b_flb, b_alt)
        #attack_pattern_2['inline'] = False

        attack_pattern_3 = None
        for spec in data.get('special',[]):
            if spec['type'] == 'pattern':
                attack_pattern_3 = copy.deepcopy(field)
                attack_pattern_3['name'] = 'Special'
                loop = self.atkptn_str2icn(spec['all'][spec['loop'][0]-1:],data['type'])
                init = self.atkptn_str2icn(spec['all'][:spec['loop'][0]-1],data['type'])
                attack_pattern_3['value'] = f"{init if init else 'None'}\n{'-'.join(loop)}"

        # tags
        tags = copy.deepcopy(field)
        tags['name'] = '> Tags'
        tags['value'] = ', '.join(data['tags'])
        tags['inline'] = False

        # aliases
        aliases = copy.deepcopy(field)
        aliases['name'] = 'Aliases'
        fetch_aliases = self.get_aliases(data['sname'])
        aliases['value'] = ', '.join(fetch_aliases) if fetch_aliases else 'None'

        # special message
        if data['base']['b_alt']:
            footnote = copy.deepcopy(field)
            footnote['name'] = "Ames' footnote "+self.client.emotes['derp']
            footnote['value'] = f"**{self.get_name(data)} has an alternate skillset** that can be toggled via the 🔀 button below"
            footnote['inline'] = False
        else:
            footnote = None
        
        return attacker, pos, attack_pattern_1, attack_pattern_2, attack_pattern_3, tags, aliases, footnote

    def make_atkptn(self, data, b_flb, b_alt):
        atkptn_flow_flb = ['flb-normal', 'base-normal']
        atkptn_flow_alt = ['flb-alt', 'base-alt', 'base-normal']
        if b_flb and b_alt:
            i = 0
            active = atkptn_flow_alt
        elif not b_flb and b_alt:
            i = 1
            active = atkptn_flow_alt
        elif b_flb and not b_alt:
            i = 0
            active = atkptn_flow_flb
        else:
            i = 1
            active = atkptn_flow_flb
        
        for tk in active[i:]:
            k1, k2 = tk.split('-')
            ptn = data[k1][k2]['pattern']
            if not ptn['all']:
                continue
            else:
                break
        
        if not ptn['loop']:
            loop = []
            init = ptn['all']
        else:
            loop = ptn['all'][ptn['loop'][0]-1:]
            init = ptn['all'][:ptn['loop'][0]-1]
        
        loop = self.atkptn_str2icn(loop, data['type'])
        init = self.atkptn_str2icn(init, data['type'])

        loop = '-'.join(loop) if loop else 'None'
        init = '-'.join(init) if init else 'None'
        return f"{init}\n{loop}"

    def atkptn_str2icn(self, l, mode):
        PHYS_NORMAL = '<:_chara:677763373739409436>'
        MAG_NORMAL = '<:magatk:713288155469578272>'
        numbers = [
            '1\u20E3',
            '2\u20E3',
            '3\u20E3'
        ]
        temp = []
        for i in l:
            i = str(i)
            if len(i) == 1:
                temp.append(MAG_NORMAL if mode == 0 else PHYS_NORMAL)
            else:
                temp.append(numbers[int(i[-1])-1])
        
        return temp

    def get_aliases(self, sname):
        temp = []
        for alias, name in self.aliases.items():
            if name == sname:
                temp.append(alias)
        
        return temp
        
    def make_chara_ue_embed(self, base_embed, data):
        base_embed['footer']   = {'text': 'Unique Equipment', 'url': data['base']['img']}

        if not data['base']['ue']:
            base_embed['title'] = 'No Data'
            base_embed['descr'] = f"{self.get_name(data)} does not have an unique equipment yet:tm:."
            base_embed['thumb'] = self.hatsu_cf['links']['unknown']
        else:
            ue = data['base']['ue_data']
            base_embed['title'] = f"{ue['name']['jp']}\n{ue['name']['en']}"
            base_embed['descr'] = f"{self.get_name(data)}'s unique equipment.\n{ue['text']['jp']}"
            base_embed['thumb'] = ue['img']
            base_embed['fields'] = []

            base_embed['fields'].append(
                {
                    'name': "UE stats",
                    'value': f"Base (Max Lv{data['status']['ue']})"
                }
            )

            # stats
            for field, value in list(ue['stats'].items()):
                if field in self.hatsu_cf['ue_abbrev']:
                    final_val = round(float(value) + float(ue['stats'].get(f"{field.lower()}_growth",0)) * (data['status']['ue']-1))

                    base_embed['fields'].append(
                        {
                            'name': self.hatsu_cf['ue_abbrev'][field],
                            'value': f"{value} ({final_val})",
                            'inline': True
                        }
                    )
            
            # sk1, sk1+, sk1a, sk1a+
            sk1 = self.make_skill('sk1', data['base']['normal']['sk1'], False, False, False)
            sk1p = self.make_skill('sk1', data['base']['normal']['ue']['sk1'], False, False, True)
            #base_embed['fields'] += [*sk1, *sk1p]
            base_embed['fields'] += sk1
            if sk1p: base_embed['fields'] += sk1p

            if data['base']['b_alt']:
                sk1a = self.make_skill('sk1', data['base']['alt']['sk1'], False, True, False)
                sk1ap = self.make_skill('sk1', data['base']['alt']['ue']['sk1'], False, True, True)
                #base_embed['fields'] += [*sk1a, *sk1ap]
                base_embed['fields'] += sk1a
                if sk1ap: base_embed['fields'] += sk1ap

                #for i in [sk1a, sk1ap]:
                #    if i:
                #        base_embed['fields'] += i
            
        return base_embed

    def make_chara_card_embed(self, base_embed, data):
        base_embed['title'] = 'Unit Card'
        base_embed['footer'] = {'text': 'Unit card', 'url': data['base']['img']}

        # base
        base = copy.deepcopy(base_embed)
        base['descr'] = f"{self.get_name(data)}'s card."
        base['thumb'] = data['base']['img']
        base['image'] = data['base']['card']

        if data['flb']['active']:
            flb = copy.deepcopy(base_embed)
            flb['descr'] = f"{self.get_name(data)}'s FLB (6⭐) card."
            flb['thumb'] = data['flb']['img']
            flb['image'] = data['flb']['card']
        else:
            flb = None
        
        return {'base': base, 'flb': flb}

    def make_chara_profile_embed(self, base_embed, data):
        base_embed['title'] = "Character profile"
        base_embed['footer'] = {'text': 'Profile', 'url': data['base']['img']}
        base_embed['image'] = data['image_irl']
        base_embed['fields'] = [
            {
                'name': 'Unit introduction',
                'value': data['comment']['jp'],
                'inline': False
            },
            {
                'name': 'Voice Actor/Actress',
                'value': data['va'],
                'inline': False
            },
            {
                'name': ut.SPACE,
                'value': '> **Ingame Profile**',
                'inline': False
            },
            {
                'name': 'Name',
                'value': f"{data['name']['jp']}({data['name_alt']['jp']})"
            },
            {
                'name': 'Race',
                'value': data['race']
            },
            {
                'name': 'Guild',
                'value': data['guild']
            },
            {
                'name': ut.SPACE,
                'value': '> **IRL Profile**',
                'inline': False
            },
            {
                'name': 'Name',
                'value': data['name_irl']['jp']
            },
            {
                'name': 'Age',
                'value': str(data['age'])
            },
            {
                'name': 'Birthday (mm/dd)',
                'value': data['bday']
            },
            {
                'name': 'Height',
                'value': f"{data['height']}cm"
            },
            {
                'name': 'Bloodtype',
                'value': data['bloodtype']
            },
            {
                'name': 'Weight',
                'value': f"{data['weight']}kg"
            }
        ]
        
        return base_embed

    @commands.command(aliases=['pos'])
    async def position(self, ctx, option):
        author = ctx.author
        channel = ctx.channel
        if not option:
            await channel.send('no input')
            return
        
        # try to determine a target
        option = option.lower()

        if option == 'help':
            await self.hatsune_help(ctx, 'pos')
            return

        request = self.process_request(option)
        request = self.fetch_chara(request)
        if request:
            if not request['success'] and not request['fallback']:
                if option.startswith('v'):
                    field = 0
                elif option.startswith('m'):
                    field = 1
                elif option.startswith('r'):
                    field = 2
                else:
                    await channel.send('failed to process request')
                    return
                request = None
            else:
                request = request['target']
                field = request['pos_field']
        else:
            if option.startswith('v'):
                field = 0
            elif option.startswith('m'):
                field = 1
            elif option.startswith('r'):
                field = 2
            else:
                await channel.send('failed to process request')
                return
            request = None

        # fetch lineup
        with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as f:
            lineup = list(filter(lambda x: x['pos_field'] == field, json.load(f)['units']))
        
        temp = []
        lineup.sort(key=lambda x: x['pos'])
        offset = 0
        for i, chara in enumerate(lineup):
            i -= offset
            if not isinstance(chara['pos'], int):
                j = '??'
                offset += 1
            else:
                j = i

            if request:
                if chara['sname'] == request['sname']:
                    temp.append(f"> **{self.res[chara['sname']]['full']} {j} {self.get_name(chara, True)}**")
                    continue

            temp.append(f"{self.res[chara['sname']]['full']} {j} {self.get_name(chara, True)}")
        
        fields = [
            '**Vanguard**',
            '**Midguard**',
            '**Rearguard**'
        ]
        embed = {
            'author': {'text': "ハツネのメモ帳", "icon": self.hatsu_cf['HATSUNE']},
            'title': 'Lineup',
            'descr': f"Listing {fields[field]} lineup. The forwardmost character is at `0`."\
                + (f" Bolding **{self.get_name(request)}'s** position." if request else ""),
            'fields': [],
            'footer': {'text': 'Lineup'}
        }
        for chunk in ut.chunks(temp, 20):
            embed['fields'].append(
                {
                    'name': 'Lineup',
                    'value': '\n'.join(chunk),
                    'inline': True
                }
            )
        
        msg = await channel.send(embed=ut.embed_contructor(**embed))
        await sleep(60)
        await msg.edit(content="This embed has expired "+self.client.emotes['derp'], embed=None)

    @commands.command(aliases=['tag'])
    async def tags(self, ctx, *, tags):
        channel = ctx.channel
        if not tags:
            await channel.send('no input')
            return

        if tags.split()[0].lower() == 'help':
            #await self.hatsune_help(ctx, 'tags')
            return
        
        # try to determine a target
        tags = tags.lower()
        request = self.process_request(tags)
        request = self.fetch_chara(request)
        msg = None
        if request:
            if request['success'] and not request['fallback']:
                msg = await channel.send(embed=self.chara_tags_embed(request['target']))

        if not msg:
            temp = []
            tags = tags.split() if not ',' in tags else tags.split(',')
            tags = [i.strip() for i in tags if i.strip()]
            include = [i for i in tags if not i.startswith('-')]
            exclude = [i[1:] for i in tags if i.startswith('-') and len(i) > 1]

            with open(ut.full_path(self.rel_path, self.hatsu_cf['database'])) as f:
                units = json.load(f)['units']
            
            for chara in units:
                success = True
                for t in include:
                    if not t in chara['tags']:
                        success = False
                        break
                if not success:
                    continue

                for t in exclude:
                    if t in chara['tags']:
                        success = False
                        break
                if not success:
                    continue

                temp.append(chara)
            
            msg = await channel.send(embed=self.tags_search(include, exclude, temp))
        
        await sleep(60)
        await msg.edit(content="This embed has expired "+self.client.emotes['derp'], embed=None)

    def chara_tags_embed(self, chara):
        embed = {
            'author': {'text': "ハツネのメモ帳", "icon": self.hatsu_cf['HATSUNE']},
            'title': "Character search via tags",
            'descr': f"Listing **{self.get_name(chara)}'s** tags",
            'footer': {'text': 'Tags search'},
            'fields': [
                {
                    'name': 'Tags',
                    'value': ', '.join([f"`{t}`" for t in chara['tags']])
                }
            ],
            'thumb': chara['base']['img']
        }

        return ut.embed_contructor(**embed)

    def tags_search(self, incl, excl, charas):
        incl_str = ', '.join([f"`{t}`" for t in incl])
        excl_str = ', '.join([f"`{t}`" for t in excl])

        embed = {
            'author': {'text': "ハツネのメモ帳", "icon": self.hatsu_cf['HATSUNE']},
            'title': "Character search via tags",
            'descr': f"Found **{len(charas)}** character(s)"\
                 + (f" with tag(s) {incl_str}" if incl_str else "")\
                 + (' and' if incl_str and excl_str else '')\
                 + (f" without tag(s) {excl_str}" if excl_str else ""), 
            'footer': {'text': 'Tags search'}
        }

        charas.sort(key=lambda x: x['name']['en'])
        charas = [f"{self.res[c['sname']]['full']} {self.get_name(c, True)}" for c in charas]
        if charas:
            temp = []
            for chunk in ut.chunks(charas, 20):
                temp.append({
                    'name': 'Lineup',
                    'value': '\n'.join(chunk)
                })
            embed['fields'] = temp
        
        return ut.embed_contructor(**embed)

    @commands.group(invoke_without_command=True)
    async def alias(self, ctx, *, option:str):
        if ctx.invoked_subcommand is None:
            channel = ctx.channel
            if not option:
                await channel.send('no input')
                return
            elif option.split()[0].lower() == 'help':
                await self.hatsune_help(ctx, 'alias')
                return
            
            
            # check if request is an alias
            if option in self.aliases:
                with open(ut.full_path(self.rel_path, self.hatsu_cf['index'])) as i:
                    index = json.load(i)['index']
                chara = list(filter(lambda x: x['sname'] == self.aliases[option], index))[0]

                await channel.send(f"Alias `{option}` \u21D2 `{self.get_full_name(chara['name']['en'], chara['prefix'])}`")
                return

            request = self.process_request(option)
            request = self.fetch_chara(request)
            if request:
                if request['success'] and not request['fallback']:
                    chara_aliases = sorted(self.get_aliases(request['target']['sname']))
                    alias_str = ", ".join([f"`{i}`" for i in chara_aliases])
                    await channel.send(f"Search name `{option}` \u21D2 `{self.get_name(request['target'])}`\n"\
                        + (f"This character has **{len(chara_aliases)}** alias(es): {alias_str}" if alias_str else \
                            "This character doesn't have aliases yet")    
                    )
                    return
            
            await channel.send(f"Found no alias/character with name `{option}`")

    @alias.command()                
    async def add(self, ctx, *, options):
        channel = ctx.channel
        try:
            alias, chara = options.split(',')
            alias = alias.strip()
            chara = chara.strip()
        except:
            await channel.send("Failed to process inputs")
            return

        exists, falias, _, index, _, local = self.validate_alias_request(alias)

        if exists:
            await channel.send(f"Alias `{alias}` already exists: `{alias}` \u21D2 `{self.get_full_name(index['name']['en'], index['prefix'])}`")
            return
        
        request = self.process_request(chara)
        request = self.fetch_chara(request)
        if request:
            if request['success'] and not request['fallback']:
                local[alias] = request['target']['sname']
                await channel.send(f"Added alias `{alias}` \u21D2 `{self.get_full_name(request['target']['name']['en'], request['target']['prefix'])}`")
                with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases_loc']), 'w+') as i:
                    i.write(json.dumps(local, indent=4))
                return

        await channel.send(f"Did not find `{chara}` in database to alias")

    @alias.command() 
    async def edit(self, ctx, *, options):
        channel = ctx.channel
        try:
            alias, chara = options.split(',')
            alias = alias.strip()
            chara = chara.strip()
        except:
            await channel.send("Failed to process inputs")
            return

        exists, falias, exists_master, index, _, local = self.validate_alias_request(alias)

        if not exists:
            await channel.send(f"Could not edit: alias name `{alias}` does not exist")
            return
        elif exists_master:
            await channel.send(f"Could not edit: alias name `{alias}` is a master alias and cannot be editted")
            return
        
        request = self.process_request(chara)
        request = self.fetch_chara(request)

        if request:
            if request['success'] and not request['fallback']:
                local[alias] = request['target']['sname']
                await channel.send(f"Changed alias to `{alias}` \u21D2 `{self.get_full_name(request['target']['name']['en'], request['target']['prefix'])}`")
                with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases_loc']), 'w+') as i:
                    i.write(json.dumps(local, indent=4))
                return

        await channel.send(f"Did not find `{chara}` in database to alias")

    @alias.command() 
    async def remove(self, ctx, alias):
        channel = ctx.channel
        if not alias:
            await channel.send('No input')
            return

        exists, falias, exists_master, index, _, local = self.validate_alias_request(alias)

        if not exists:
            await channel.send(f"Could not remove: alias name `{alias}` does not exist")
            return
        elif exists_master:
            await channel.send(f"Could not remove: alias name `{alias}` is a master alias and cannot be removed")
            return
        
        local.pop(alias)
        with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases_loc']), 'w+') as i:
            i.write(json.dumps(local, indent=4))
        await channel.send(f"Removed alias `{alias}`")

    def validate_alias_request(self, alias:str):
        """
        returns:
        \nEXISTS(bool) EXIST_ALIAS(sname)|None MASTER_ALIAS(bool) CHARA_INDEX|None MASTER_ALIAS_LIST LOCAL_ALIAS_LIST
        """
        EXISTS = False
        ALIAS = None
        MASTER = False
        INDEX = None

        with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases'])) as aliases:
            alias_master = json.load(aliases)
        try:
            with open(ut.full_path(self.rel_path, self.hatsu_cf['aliases_loc'])) as aliases:
                alias_loc = json.load(aliases)
        except FileNotFoundError:
            alias_loc = {}
        
        if not (alias in alias_master or alias in alias_loc):
            pass
        elif alias in alias_master:
            EXISTS = True
            ALIAS = alias_master[alias]
            MASTER = True
        elif alias in alias_loc:
            EXISTS = True
            ALIAS = alias_loc[alias]
        
        if EXISTS:
            with open(ut.full_path(self.rel_path, self.hatsu_cf['index'])) as i:
                INDEX = list(filter(lambda x: x['sname'] == ALIAS, json.load(i)['index']))[0]
        
        return EXISTS, ALIAS, MASTER, INDEX, alias_master, alias_loc

    # optional ventures:
    # tag definition
    # stat delta

    @commands.command(aliases=['spark'])
    async def gacha(self, ctx, *, options='10'):
        channel = ctx.channel

        if options.split()[0].lower() == 'help':
            await self.hatsune_help(ctx, 'gacha')
            return
        
        with open(ut.full_path(self.rel_path, self.hatsu_cf['gacha'])) as f:
            gacha_config = json.load(f)
        with open(ut.full_path(self.rel_path, self.hatsu_cf['index'])) as f:
            index = json.load(f)['index']

        if not gacha_config['pools']['lim']:
            await channel.send('Limited pool is empty!')
            return

        # try to process request
        options = options.split()
        
        TEST = True if options[-1].startswith('t') else False

        if ctx.invoked_with == 'spark':
            MODE        = 'SPARK'
            MAX_ROLLS   = 200
            #INIT_ROLLS  = None

            # attempt to process request
            request = self.process_request(options[0])
            TARGET = list(filter(lambda x: x['sname'] == request['sname'], index))
            if len(TARGET) == 0:
                await channel.send("Failed to process spark target")
                return
            TARGET = TARGET[0]

            IN_LIM = TARGET['sname'] in gacha_config['pools']['lim']
            IN_PRIFES = TARGET['sname'] in gacha_config['pools']['prifes']
            
            if gacha_config['prifes'] and (not IN_LIM and not IN_PRIFES):
                await channel.send(f"Invalid spark target")
                return
            elif not gacha_config['prifes'] and not IN_LIM:
                await channel.send(f"Invalid spark target")
                return

        else:
            MODE        = 'GACHA'
            #MAX_ROLLS   = None
            TARGET      = None

            # attempt to read number
            try:
                MAX_ROLLS = int(options[0])
            except:
                return
            else:
                if MAX_ROLLS <= 0 or MAX_ROLLS > 10000:
                    await channel.send(self.client.emotes['ames'])
                    MAX_ROLLS = 10
            
        page = self.gachaPage(ctx, MODE, MAX_ROLLS, TARGET, TEST, gacha_config, index, 
            self.get_full_name, 
            ut.full_path(self.rel_path, self.hatsu_cf['assets'],'{}.png'),
            ut.full_path(self.rel_path,'data', 'gacha','{}'),
            self.res,
            self.gachaView(60), self.client.user.avatar.url, self.client.emotes['ames'])
        
        await page.start()
    
    class gachaPage(ut.basePageHandler):
        def __init__(self, ctx, MODE, MAX_ROLLS, TARGET, TEST, config, index, get_name, A_PATH, G_PATH, res, viewHandler, AMES, AMES_EMOTE):
            # init parameters
            self.ctx = ctx
            self.base_id    = 'amesHatsuGacha_'
            self.ames       = AMES
            self.ames_emote = AMES_EMOTE
            self.channel    = ctx.channel
            self.author     = ctx.author
            #self.config     = config
            self.index      = index
            self.get_name   = get_name
            self.img_path   = A_PATH
            self.bg_path    = G_PATH
            self.res        = res
            self.view       = viewHandler
            
            # gacha parameters
            self.mode           = False #MODE == 'GACHA'
            self.MAX_ROLLS      = MAX_ROLLS
            self.current_rolls  = 0
            self.TARGET         = TARGET
            self.TEST           = TEST
            self.PRIFES         = config['prifes']
            self.DOUBLE         = True if config['prifes'] else config['double']

            self.rate_ssr       = config['ssr_rate'] * 2 if self.PRIFES or self.DOUBLE else config['ssr_rate']
            self.rate_sr        = config['sr_rate']
            self.rate_r         = 1 - self.rate_ssr - self.rate_sr
            self.up_ssr         = (config['ssr_rate_up'] * 2 if self.PRIFES or self.DOUBLE else config['ssr_rate_up']) / self.rate_ssr
            self.up_sr          = config['sr_rate_up'] / self.rate_sr
            self.up_r           = config['r_rate_up'] / self.rate_r

            self.pool_lim       = config['pools']['lim']# + config['pool']['prifes'] if self.PRIFES else config['pool']['lim']
            self.pool_prifes    = config['pools']['prifes']
            self.pool_ssr       = config['pools']['ssr']
            self.pool_sr        = config['pools']['sr']
            self.pool_r         = config['pools']['r']

            self.threshold_r    = self.rate_r
            self.threshold_sr   = self.threshold_r + self.rate_sr

            # gacha persist
            self.roll_results   = []
            self.lim_results    = []
            self.order          = []

            self.roll(MAX_ROLLS, TARGET)

            super().__init__(ctx.channel)
            self.view.pass_pageHandler(self)
            self.view.remake_buttons()
        
        def roll(self, max_rolls, target):
            order = []
            results = []
            lims = []
            if max_rolls is None:
                max_rolls = 10
            
            for i in range(max_rolls):
                self.current_rolls += 1
                lim_roll = random.random()
                if self.TEST:
                    tier_roll = random.uniform(self.threshold_sr, 1.0)
                else:
                    tier_roll = random.random()
                
                if tier_roll >= self.threshold_sr:
                    if lim_roll >= self.up_ssr:
                        rolled_chara = (3, random.choice(self.pool_ssr), False)
                        results.append(rolled_chara)
                    elif not self.PRIFES:
                        rolled_chara = (3, random.choice(self.pool_lim), True)
                        lims.append(rolled_chara)
                    else:
                        # lim and prifes
                        if random.random() >= 0.333333:
                            rolled_chara = (3, random.choice(self.pool_prifes), True)
                            lims.append(rolled_chara)
                        else:
                            rolled_chara = (3, random.choice(self.pool_lim), True)
                            lims.append(rolled_chara)

                elif tier_roll >= self.threshold_r or (i+1)%10==0:
                    rolled_chara = (2, random.choice(self.pool_sr), False)
                    results.append(rolled_chara)

                else:
                    rolled_chara = (1, random.choice(self.pool_r), False)
                    results.append(rolled_chara)
                
                order.append(rolled_chara)

                if target:
                    if target['sname'] == rolled_chara[1]:
                        break
            
            self.roll_results += results
            self.lim_results += lims
            self.order = order[-10:]

            #self.make_gacha_img()
            #self.embed_gacha = self.make_gacha_embed()
            self.embed_report = self.make_summary()

        def make_gacha_img(self):
            gacha =     Image.open(self.bg_path.format('gbg2.jpg'))
            rare =      Image.open(self.bg_path.format('r2_.png'))
            srare =     Image.open(self.bg_path.format('sr2_.png'))
            ssrare =    Image.open(self.bg_path.format('ssr2_.png'))
            new =       Image.open(self.bg_path.format('new_.png'))

            rarity_bg = [rare, srare, ssrare]

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

            for i, (rarity, chara, lim) in enumerate(self.order):
                rarity -= 1
                pf = Image.open(self.img_path.format(chara))
                if i < 5:
                    gacha.paste(rarity_bg[rarity], (pxstart + i*spacing, row1), rarity_bg[rarity])
                    gacha.paste(pf, (cxstart + i*spacing, row1 + cos), pf)
                    if lim:
                        gacha.paste(new, (pxstart - 25 + i*spacing, row1 - 25), new)
                else:
                    j = i - 5
                    gacha.paste(rarity_bg[rarity], (pxstart + j*spacing, row2), rarity_bg[rarity])
                    gacha.paste(pf, (cxstart + j*spacing, row2 + cos), pf)
                    if lim:
                        gacha.paste(new, (pxstart - 25 + j*spacing, row2 - 25), new)
                pf.close()
            
            #gacha = gacha.resize(gsizef, resample=rs)
            gacha.save(self.bg_path.format('gresult.jpg'))

            # shutdown
            gacha.close()
            rare.close()
            srare.close()
            ssrare.close()
            new.close()

            #return gacha         

        def make_gacha_embed(self):
            img = nextcord.File(self.bg_path.format("gresult.jpg"), filename="gresult.jpg")
            embed = {
                'author': {'text': f"{self.author.name} rolled:", 'icon': self.author.avatar.url},
                'footer': {'text': 'Gacha', 'url': self.ames},
                'image': 'attachment://gresult.jpg'
            }
            return {'embed': ut.embed_contructor(**embed), 'file': img, 'view': self.view}

        def make_buttons(self):
            button_1 = nextcord.ui.Button(
                custom_id=self.base_id+'one',
                label='Roll x1'
            )
            button_10 = nextcord.ui.Button(
                custom_id=self.base_id+'ten',
                label='Roll x10'
            )
            summary = nextcord.ui.Button(
                custom_id=self.base_id+'toggle',
                label='Report Page' if self.mode else 'Gacha Page'
            )
            button_del = nextcord.ui.Button(
                custom_id=self.base_id+'del',
                label='\u00D7',
                style=nextcord.ButtonStyle.danger
            )
            return [button_1, button_10, button_del]

        def make_summary(self):
            frags = [1, 10, 50]
            num_r = len([i for i in self.roll_results if i[0] == 1])
            num_sr = len([i for i in self.roll_results if i[0] == 2])
            ssr = self.lim_results + [i for i in self.roll_results if i[0] == 3]
            num_ssr = len(ssr)

            self.make_gacha_img()
            img = nextcord.File(self.bg_path.format("gresult.jpg"), filename="gresult.jpg")
            #img = nextcord.File(fp=BytesIO(self.make_gacha_img().tobytes()), filename="gresult.jpg")
            embed = {
                'image':  'attachment://gresult.jpg',
                'title': "カレンのガチャ報道",
                'descr': "Gacha summary report",
                'footer': {'text': 'Gacha report', 'icon': self.ames},
                'fields': [
                    {
                        'name': 'Total Pulls',
                        'value': str(self.current_rolls),
                        'inline': True
                    },
                    {
                        'name': 'Tot. P. Tears',
                        'value': sum([frags[i-1] for i, _, _, in self.lim_results + self.roll_results]),
                        'inline': True
                    },
                    {
                        'name': 'Crystals spent',
                        'value': f"{self.current_rolls*150} (¥{(self.current_rolls/10*2000):,.2f})",
                        'inline': True
                    },
                    {
                        'name': 'SSR Pulls',
                        'value': f"{num_ssr} ({(num_ssr/self.current_rolls*100):.2f}%)",
                        'inline': True
                    },
                    {
                        'name': 'SR Pulls',
                        'value': f"{num_sr} ({(num_sr/self.current_rolls*100):.2f}%)",
                        'inline': True
                    },
                    {
                        'name': 'R Pulls',
                        'value': f"{num_r} ({(num_r/self.current_rolls*100):.2f}%)",
                        'inline': True
                    }
                ]
            }

            if ssr:
                counter = {}
                for rarity, sname, lim in ssr:
                    c = counter.get(sname, {
                            'lim': None,
                            'no': 0
                        }
                    )

                    c['lim'] = lim
                    c['no'] += 1
                    counter[sname] = c

                temp = []
                base_str = "{} {} x{}"
                lim_str = "> **{} {} x{}**"
                for k, v in counter.items():
                    ind = [i for i in self.index if i['sname'] == k][0]
                    if v['lim']:
                        s = lim_str
                    else:
                        s = base_str
                    
                    s = s.format(
                        self.res[k]['full'],
                        self.get_name(ind['name']['en'], ind['prefix'], True),
                        v['no']
                    )
                    temp.append(
                        {'line': s, 'name': ind['name']['en'], 'lim':v['lim']}
                    )
                
                temp.sort(key=lambda x: (not x['lim'], x['name']))

            else:
                temp = [{'line': ':put_litter_in_its_place:'}]

            for chunk in ut.chunks(temp, 20):
                embed['fields'].append(
                    {
                        'name': 'SSR Rolled',
                        'value': '\n'.join([i['line'] for i in chunk]),
                        'inline': True
                    }
                )
            
            return {'embed': ut.embed_contructor(**embed), 'view': self.view, 'file': img}

        async def update(self, rolls, mode):
            if mode == 'roll':
                self.roll(rolls, self.TARGET)
                #async with self.ctx.typing():
                    #await self.main_message.delete()
                    #await super().main_message_send(**self.fetch_active())
                await self.main_message.edit(attachments=[], **self.fetch_active())
            elif mode == 'toggle':
                self.mode = not self.mode
                self.view.remake_buttons()
                await self.main_message.edit(**self.fetch_active())

        def fetch_active(self):
            if self.mode:
                return self.embed_gacha
            else:
                return self.embed_report

        async def start(self):
            await super().main_message_send(**self.fetch_active())

    class gachaView(ut.baseViewHandler):
        def __init__(self, timeout):
            super().__init__(timeout)
        
        def remake_buttons(self):
            super().clear_items()
            for button in self.pageHandler.make_buttons():
                super().add_item(button)
            
        async def clean_up(self, reason):
            super().stop()
            s = "This embed has been deleted " if reason == 'del' else "This embed has timed out "
            s += self.pageHandler.ames_emote
            await self.pageHandler.main_message.edit(content=s, embed=None, view=None, attachments=[])

        async def interaction_check(self, interaction:nextcord.Interaction):
            if interaction.user != self.pageHandler.author:
                return True

            inter_id = interaction.data.get('custom_id', None)
            #if inter_id.startswith(self.pageHandler.base_id):
            _id = inter_id.split('_')[-1]
            if _id == 'del':
                await self.clean_up('del')

            elif _id == 'toggle':
                await self.pageHandler.update(None, 'toggle')

            elif _id == 'one':
                await self.pageHandler.update(1, 'roll')
                
            else:
                await self.pageHandler.update(10, 'roll')

            return True
        
        async def on_timeout(self):
            await self.clean_up('timeout')