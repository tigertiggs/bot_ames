# experimental cog that mainly serves as a playground for code stuff

import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests, copy
from io import BytesIO

#from bs4 import BeautifulSoup

class testCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.name =     '[test-hatsune]',
        self.logger =   client.log
        self.db =       self.client.database
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_hatsune'])

        # load config
        with open(os.path.join(self.client.dir, self.client.config['hatsune_config_path'])) as hcf:
            self.config = json.load(hcf)
        # load tag definitions
        with open(os.path.join(self.client.dir, self.client.config['tags_index_path'])) as tif:
            self.tag_definitions = json.load(tif)
        # load local alias 
        with open(os.path.join(self.client.dir, self.client.config['alias_local_path'])) as alf:
            self.alocal = json.load(alf)
        # build full alias file
        self.full_alias = self.config['alias_master'].copy()
        self.full_alias.update(self.alocal)

        # db stuff
        self.db = self.client.database

        # help stuff
        self.full_help =     ("**In case you forgot, the input syntax is:**\n"
                            "> `.c [version.][character_name] [*options]`\n"
                            "> i.e. `.ue s.kyaru` `.stats maho flb`\n"
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
                            "> `r` for Ranger i.e. `r.rin`\n"
                            "> `w` for Wonderland i.e. `w.ayumi`\n"
                        "**The following icons at the bottom of the embed have the following meaning:**\n"
                            "> <:_chara:677763373739409436> react to access chara and skill info\n"
                            "> <:_ue:677763400713109504> react to access UE info and data\n"
                            "> <:_stats:678081583995158538> react to access detailed character and skill stats (WIP)\n"
                            "> <:_card:677763353069879306> react to access pretty pictures\n"
                            "> :star: react to access the character's FLB variant\n"
                            "> :twisted_rightwards_arrows: react to access character's special/alternate skills\n"
                            "> :stop_sign: Ames will no longer respond to reacts on this embed")
        
        self.help =          ("If you need help, try `.c help`")

    def error(self):
        error_msg = dict()
        error_msg['no_input'] =     'There was no input\n'+self.help
        error_msg['search_fail'] =  f"{self.client.emotes['ames']} I didn\'t find the requested character\n"+self.help
        error_msg['conn_fail'] =    'Failed to connect to database!'
        error_msg['pos_fail'] =     'Invalid input! Use `v` for vanguard, `m` for midguard or `r` for rearguard. '\
                                    'Alternatively enter a character name to find their lineup.'
        return error_msg

    def get_db_stats(self, data):
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            print("connection failed")
            return
        query = ("SELECT "
                    "hc.unit_id, hc.pos, hc.unit_name, hc.unit_name_eng, ub_trans, ub_2_trans, "
                    "skill_1_translation, skill_1_plus_trans, skill_2_trans, sk1a_trans, sk2a_trans, "
                    "comment_trans, tag, "
                    "eq_name_trans, eq_rank "
                "FROM "
                    "hatsune_bot.charadata AS hc LEFT JOIN hatsune_bot.charaUE AS hu "
                "ON "
                    "hu.unit_id = hc.unit_id "
                "ORDER BY "
                    "hc.unit_id ASC")
        cursor = conn.cursor(buffered=True)
        cursor.execute(query)
        units = data['units']
        for (uid, pos, jp, en, ubtl, ub2tl, sk1tl, sk1ptl, sk2tl, sk1atl, sk2atl, cmtl, tag, ueen, uerank) in cursor:
            search = list(filter(lambda x: x['basic']['en']['name'] == en, units))
            if search:
                temp = search[0]
                temp = units.pop(units.index(temp))
            else:
                #print(self.config['template']['basic']['en']['name'])
                temp = copy.deepcopy(self.config['template'])
            
            #print("DB",bool(search),en, temp['basic']['en']['name'])

            skills_en =                     temp['basic']['en']
            skills_en['id'] =               int(uid)
            skills_en['name'] =             en
            skills_en['ub']['text'] =       ubtl
            skills_en['ub2']['text'] =      ub2tl
            skills_en['sk1']['text'] =      sk1tl
            skills_en['sk1p']['text'] =     sk1ptl
            skills_en['sk2']['text'] =      sk2tl
            skills_en['sk1a']['text'] =     sk1atl
            skills_en['sk2a']['text'] =     sk2atl
            skills_en['comment'] =          cmtl if not cmtl else None
            temp['tags'] =                  [c.strip() for c in tag.split(',')]
            temp['pos'] =                   pos
            temp['ue']['en'] =              ueen
            temp['ue']['rank'] =            uerank
            temp['basic']['jp']['name'] =   jp
            temp['basic']['en'] =           skills_en
            units.append(temp)

        data['units'] = units
        self.db.release(conn)
        return data
            
    @commands.command()
    async def test_load_db(self, ctx):
        #channel=ctx.channel
        # load units
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            data = json.load(dbf)
        
        # preload db data
        data  = self.get_db_stats(data)
        #print([x['basic']['en']['name'] for x in data['units']])

        #return

        port = self.client.config['port']
        if port != 'default':
            request = f"http://localhost:{port}/FagUtils/gateway.php?"
        else:
            request = f"http://localhost/FagUtils/gateway.php?"
        
        for i, unit in enumerate(data['units']):
            try:
                params = {
                    "cmd":  "priconne.api",
                    "call": "api.fetch",
                    "name": unit['basic']['jp']['name']
                }
                result = requests.get(request, params=params)
                raw = json.load(BytesIO(result.content))
            except:
                traceback.print_exc
                return
            if raw['status'] != 200:
                print("failed to get", unit['basic']['jp']['name'], raw['status'])
                return

            print("fetching", raw['data']['unit_profile']['name'])
            unit = self.get_unit_status(raw['config'], unit)
            for key, val in list(raw['data'].items()):
                if key == "unit_profile":
                    unit = self.get_unit_profile(val, unit)
                elif key == "unit_pattern":
                    unit = self.get_unit_pattern(val, unit)
                elif key == "unique_equipment":
                    unit = self.get_unit_ue(val, unit)
                elif key == "skill_data":
                    unit = self.get_unit_skill(val, unit)
                elif key.startswith("stats"):
                    unit = self.get_unit_stats(val, unit, "flb" in key)
                else:
                    print("Unknown data key", key)

                hn_id = unit['basic']['jp']['id']
                ue_id = unit['ue']['id']
                unit['img'] =            'https://redive.estertion.win/icon/unit/{}31.webp'.format(hn_id)
                unit['img6'] =           'https://redive.estertion.win/icon/unit/{}61.webp'.format(hn_id) if 'flb' in unit['tags'] else None
                unit['ue']['img'] =      'https://redive.estertion.win/icon/equipment/{}.webp'.format(ue_id) if unit['ue']['id'] != None else None
            
            data['units'][i] = unit

        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']),"w+") as dbf:
            dbf.write(json.dumps(data,indent=4))

    def get_unit_status(self, raw, data):
        status = data['status']
        status['ue'] =      raw['UE_MAX']
        status['lvl'] =     raw['LEVEL_MAX']
        status['rk'] =      raw['RANK_MAX']
        data['status'] = status
        return data
    
    def get_unit_profile(self, raw, data):
        data['basic']['jp']['id'] = int(raw['id'])
        data['basic']['jp']['comment'] = raw['comment']

        jp = data['profile']['jp']
        jp['guild'] =   raw['guild']
        jp['name'] =    raw['name']
        jp['name_alt'] =raw['name_alt']
        jp['va'] =      raw['VA']
        jp['race'] =    raw['race']
        data['profile']['jp'] = jp
        
        data['profile']['blood'] =  raw['bloodtype']
        data['profile']['height'] = raw['height']
        data['profile']['bd'] =     raw['bday']
        data['profile']['weight'] = raw['weight']
        data['profile']['age'] =    raw['age']
        return data

    def get_unit_pattern(self, raw, data):
        data['atkptn']['loop'] = [raw['loop_start'], raw['loop_end']]
        ptn = list(filter(lambda x: x[0].startswith("action_"), list(raw.items())))
        ptn.sort(key=lambda x: x[0])
        data['atkptn']['ptn'] = [v for _,v in ptn]
        return data

    def get_unit_ue(self, raw, data):
        if raw:
            data['ue']['id'] = raw['ue_id']
            for key, item in list(raw.items()):
                if key == "ue_name":
                    data['ue']['jp']['name'] = item
                elif key == "ue_decription":
                    data['ue']['jp']['text'] = item
                elif not "id" in key:
                    data['ue']['stats'][key] = item
        return data

    def get_unit_skill(self, raw, data):
        jp = data['basic']['jp']
        for key, value in list(raw.items()):
            _key = None
            if key ==       "Union Burst":
                _key = "ub"
            elif key ==     "Union Burst+":
                _key = "ub2"
            elif key ==     "Skill 1":
                _key = "sk1"
            elif key ==     "Skill 1+":
                _key = "sk1p"
            elif key ==     "Skill 2":
                _key = "sk2"
            elif key ==     "EX Skill":
                _key = "ex"
            elif key ==     "EX Skill+":
                _key = "ex2"
            elif key ==     "Skill 1 Alt":
                _key = "sk1a"
            elif key ==     "Skill 2 Alt":
                _key = "sk2a"
            else:
                print("unknown skill key", key)
                continue
            jp[_key]['name'] = value['skill_name']
            jp[_key]['text'] = value["description"] if not "soon" in value["description"] else None
            data['basic']['en'][_key]['action'] = value['actions']
        data['basic']['jp'] = jp
        return data

    def get_unit_stats(self, raw, data, flb=False):
        if not flb:
            data['stats']['normal'] = raw
        else:
            data['stats']['flb'] = raw
        return data

def setup(client):
    client.add_cog(testCog(client))

if __name__ == "__main__":
    pass