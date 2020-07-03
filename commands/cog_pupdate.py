# experimental cog that mainly serves as a playground for code stuff

import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests, copy, time
from io import BytesIO
SPACE = '\u200B'

def setup(client):
    client.add_cog(updateCog(client))

#def fetch_chara_data(data, )

class updateCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.name =     '[test-update]',
        self.logger =   client.log
        self.db =       self.client.database
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_hatsune'])

        # load config
        with open(os.path.join(self.client.dir, self.client.config['hatsune_config_path']), encoding='utf-8') as hcf:
            self.config = json.load(hcf)
        # load tag definitions
        with open(os.path.join(self.client.dir, self.client.config['tags_index_path'])) as tif:
            self.tag_definitions = json.load(tif)

        # db stuff
        self.db = self.client.database

    def get_db_stats(self, data):
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            print("connection failed")
            return
        query = ("SELECT "
                    "hc.unit_id, hc.pos, hc.unit_name, hc.unit_name_eng, ub_trans, ub_2_trans, "
                    "skill_1_translation, skill_1_plus_trans, skill_2_trans, sk1a_trans, sk2a_trans, sk1ap_trans, "
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
        #units = data['units']
        units = []
        for (uid, pos, jp, en, ubtl, ub2tl, sk1tl, sk1ptl, sk2tl, sk1atl, sk2atl, sk1aptl, cmtl, tag, ueen, uerank) in cursor:
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
            if en[1].isupper():
                skills_en['name'] =         en[1:].lower()
                skills_en['prefix'] =       en[0].lower()
            else:
                skills_en['name'] =         en.lower()
            skills_en['ub']['text'] =       ubtl
            skills_en['ub2']['text'] =      ub2tl
            skills_en['sk1']['text'] =      sk1tl
            skills_en['sk1p']['text'] =     sk1ptl
            skills_en['sk2']['text'] =      sk2tl
            skills_en['sk1a']['text'] =     sk1atl
            skills_en['sk2a']['text'] =     sk2atl
            skills_en['sk1ap']['text'] =    sk1aptl
            skills_en['comment'] =          cmtl if not cmtl else None
            temp['tags'] =                  [c.strip() for c in tag.split(',')]
            temp['pos'] =                   pos
            temp['ue']['en']['name'] =      ueen
            temp['ue']['rank'] =            uerank if uerank != "-" else None
            temp['basic']['jp']['name'] =   jp.replace("（","(").replace("）",")")
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
            
            url = f"https://redive.estertion.win/card/actual_profile/{hn_id}32.webp"
            if requests.get(url).status_code == 404:
                url = f"https://redive.estertion.win/card/actual_profile/{hn_id}31.webp"
            unit['profile']['img'] = url

            data['units'][i] = unit

        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']),"w+") as dbf:
            dbf.write(json.dumps(data,indent=4))
        self.make_index()

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
        #data['basic']['jp']['name'] = raw['name']
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
                elif key == "ue_description":
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
            elif key ==     "Skill 1 Alt+":
                _key = "sk1ap"
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

# new update control flow to reflect local data storage
# 1. update fagtest with new db
# 2. fetch the index list in fagtest and run a comparison with local unit list
# 3. iterate through the differences and:
#   a. create a new template
#   b. prefill with JP details from fag
#   c. call new data entry feature and input data fields with arrows and whatnot
#   d. save the data

    @commands.group()
    async def update(self, ctx):
        pass

    @update.command(aliases=['hnote','hn','hndb','hnotedb'])
    async def hatsune(self, ctx, *options):
        channel=ctx.channel
        author=ctx.message.author
        # add command status check
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return

        forced = False
        for option in options:
            if option == "f":
                forced = True
        
        await self.update_hatsune(ctx, force=forced)
    
    @update.command()
    async def index(self, ctx):
        channel=ctx.channel
        author=ctx.message.author
        # add command status check
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        self.make_index()
    
    def make_index(self):
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            data = json.load(dbf)
        index = dict()
        indexv = []
        for chara in data['units']:
            temp = copy.deepcopy(self.config['template_index'])
            temp['id'] = chara['basic']['en']['id']
            temp['hnid'] = chara['basic']['jp']['id']
            temp['name_en'] = chara['basic']['en']['name']
            temp['prefix'] = chara['basic']['en']['prefix']
            temp['name_jp'] = chara['basic']['jp']['name']
            temp['flb'] = 'flb' in chara['tags']
            indexv.append(temp)
        
        index['index'] = indexv
        with open(os.path.join(self.client.dir, self.client.config['unit_list_path']), "w+") as idf:
            idf.write(json.dumps(index,indent=4))

    def validate_request(self, request:dict, mode="en"):
        # request needs to be a dictionary of the form {"name":str,"prefix":Union(None,str)}
        # returns match:Union(dict,None), alts:Union(list,None)

        # load index
        with open(os.path.join(self.client.dir, self.client.config['unit_list_path'])) as idf:
            index = json.load(idf)

        if mode == "en":
            # exact match
            match = list(filter(lambda x: x['name_en'] == request['name'] and x['prefix'] == request['prefix'], index['index']))
        else:
            pass

        # check
        if not match:
            # error
            return None, None
        else:
            alts = list(filter(lambda x: x['name_en'] == request['name'], index['index']))
            return {**match[0],"index":index['index'].index(match[0])}, [{**alt,"index":index['index'].index(alt)} for alt in alts]

    def fetch_index_diff(self):
        # open fag index
        with open(os.path.join(self.client.dir, self.client.config['fag_index_path']), encoding='utf-8') as fag:
            fag_index = json.load(fag)

        for invalid in self.config['blacklist']:
            try:
                fag_index.pop(invalid)
            except KeyError:
                continue
        
        # load index
        with open(os.path.join(self.client.dir, self.client.config['unit_list_path']), encoding='utf-8') as idf:
            index = json.load(idf)
        # get jp list
        local_jp = [chara['name_jp'] for chara in index['index']]

        diff = []
        for chara, hnid in list(fag_index.items()):
            if not chara in local_jp:
                diff.append((chara,hnid))
        
        return diff
    
    async def update_hatsune(self, ctx, **kwargs):
        # fetch difference
        diff = self.fetch_index_diff()

        # check options
        forced = kwargs.get("force", False)

        # check if theres anything to update
        if not diff and not forced:
            await ctx.message.channel.send("Local index already up to date. Consider using ``")
            return
        
        # get bulk data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data = json.load(dbf)
        
        # iterate through diff and update new data
        #print(diff)
        for chara in diff:
            unit, _ = await self.get_data(ctx, chara, new=True)

            if not unit:
                await ctx.message.channel.send(f"Failed to fetch basic data for `{chara[0]} ({chara[1]})`")
                continue
            unit = await self.edit_chara(ctx, unit)
            all_data['units'].append(unit)

        if forced:
            await ctx.message.channel.send("Forcing update from Hnote")
            all_data['units'] = [(await self.get_data(ctx, unit, all_data=all_data))[0] for unit in all_data['units']]
        
        # save db
        try:
            msg = await ctx.message.channel.send("Saving db...")
            with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']), "w+") as dbf:
                dbf.write(json.dumps(all_data, indent=4))
            await msg.edit(content=msg.content+" done")
        except Exception as e:
            await self.logger.send(self.name, "failed to save", e)
            await msg.edit(content=msg.content+" failed")
            return
        else:
            # update local index
            msg = await ctx.message.channel.send("Making local index...")
            self.make_index()
            await msg.edit(content=msg.content+" done")

    async def get_data(self, ctx, chara, **kwargs):
        new = kwargs.get("new", False)
        prefix = kwargs.get("prefix", None)
        all_data = kwargs.get("data", None)

        if new:
            unit = copy.deepcopy(self.config['template'])
            unit['basic']['jp']['name'] = chara[0]
            unit['basic']['jp']['id'] = chara[1]
        else:
            unit = all_data['units'][chara["index"]]

        port = self.client.config['port']
        if port != 'default':
            request = f"http://localhost:{port}/FagUtils/gateway.php?"
        else:
            request = f"http://localhost/FagUtils/gateway.php?"
        params = {
            "cmd":  "priconne.api",
            "call": "api.fetch",
            "id": unit['basic']['jp']['id']
        }
        try:
            result = requests.get(request, params=params)
            raw = json.load(BytesIO(result.content))
        except Exception as e:
            await self.logger.send(self.name, e)
            return False, all_data
        if raw['status'] != 200:
            await self.logger.send(self.name, raw['status'])
            return False, all_data

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
                await ctx.message.channel.send("Unknown data key "+key)
                await self.logger.send(self.name, "Unknown data key", key)

        hn_id = unit['basic']['jp']['id']
        ue_id = unit['ue']['id']
        unit['img'] =            'https://redive.estertion.win/icon/unit/{}31.webp'.format(hn_id)
        unit['img6'] =           'https://redive.estertion.win/icon/unit/{}61.webp'.format(hn_id) if unit['basic']['jp']['ub2']['text'] else None
        unit['ue']['img'] =      'https://redive.estertion.win/icon/equipment/{}.webp'.format(ue_id) if unit['ue']['id'] != None else None
        url = f"https://redive.estertion.win/card/actual_profile/{hn_id}32.webp"
        if requests.get(url).status_code == 404:
            url = f"https://redive.estertion.win/card/actual_profile/{hn_id}31.webp"
        unit['profile']['img'] = url

        return unit, all_data
        
    async def edit_chara(self, ctx, chara):
        def check(msg):
            return self.client._check_author(msg.author) and msg.channel == ctx.message.channel
        
        edit = self.edit_controller(chara, self)
        text = "Currently editting `{}` page.\nType a `field:value` command to edit, type `norm|alt|ue|flb` to switch pages, or type `exit` to finish..."
        
        header_msg = await ctx.message.channel.send(embed=edit.start())
        for emote in edit.emote:
            await header_msg.add_reaction(emote)
        cmd = await ctx.message.channel.send(text.format(edit.mode))
        
        confirmation = False
        while True:
            inp = await self.client.wait_for('message', check=check)
            cnt = inp.content

            if not cnt.startswith('--'):
                await inp.delete()
                if cnt == "exit":
                    if (not chara['basic']['en']['name'] or not chara['basic']['en']['prefix']) and not confirmation:
                        await ctx.message.channel.send("Warning - `name_en` and/or `prefix` field is empty! Saving now may have leave the character inaccessible!\nType `exit` again to confirm")
                        confirmation = True
                        continue
                    break
                elif cnt in ['alt', 'norm', 'flb', 'ue']:
                    await header_msg.edit(embed=edit.switch(cnt))
                    await cmd.edit(content=text.format(edit.mode))
                else:
                    # process commands
                    chara, success = await self.process_command(cmd, cnt, chara, edit.mode, text.format(edit.mode))
                    if success:
                        print("reloading")
                        await header_msg.edit(embed=edit.reload(chara))
                    #await cmd.edit(content="\n".join([cmd.content, f"Unknown command `{inp.content}`"]))
                confirmation = False
        await cmd.delete()
        await header_msg.edit(content=f"Updated `{chara['basic']['jp']['name']}`",embed=None)
        return chara

    async def process_command(self, cmd, content, data, mode, text):
        # accepted keys
        persist =   ['name', 'prefix', 'tags']
        norm =      ['ub', 'sk1', 'sk1p', 'sk2', 'ex', 'ex2']
        alt =       ['sk1a', 'sk1ap', 'sk2a']
        ue =        ['sk1', 'sk1p', 'uename', 'uetext']
        flb =       ['ub', 'ub2']

        field, _, value = content.partition(':')
        value = value.strip()
        field = field.strip()

        if field in persist:
            if field == 'tags':
                data['tags'] = [i.strip() for i in value.split(',')]
                await cmd.edit(content="\n".join([text,f"> Setting `tags` to `{data['tags']}`"]))
            else:
                data['basic']['en'][field] = value if value else None
                await cmd.edit(content="\n".join([text,f"> Setting `{field}` to `{data['basic']['en'][field]}`"]))
        
        elif mode == "norm" and field in norm:
            data['basic']['en'][field]['text'] = value if value else None
            await cmd.edit(content="\n".join([text,f"> Setting `{field}` to `{data['basic']['en'][field]['text']}`"]))
        
        elif mode == "alt" and field in alt:
            data['basic']['en'][field]['text'] = value if value else None
            await cmd.edit(content="\n".join([text,f"> Setting `{field}` to `{data['basic']['en'][field]['text']}`"]))
        
        elif mode == "ue" and field in ue:
            if field in ['sk1', 'sk1p']:
                data['basic']['en'][field]['text'] = value if value else None
                await cmd.edit(content="\n".join([text,f"> Setting `{field}` to `{data['basic']['en'][field]['text']}`"]))
            else:
                data['ue']['en'][field.replace("ue","")] = value if value else None
                await cmd.edit(content="\n".join([text,f"> Setting `{field.replace('ue','')}` to `{data['ue']['en'][field.replace('ue','')]}`"]))
        
        elif mode == "flb" and field in flb:
            data['basic']['en'][field]['text'] = value if value else None
            await cmd.edit(content="\n".join([text,f"> Setting `{field}` to `{data['basic']['en'][field]['text']}`"]))
        
        else:
            await cmd.edit(content="\n".join([text,f"> Unknown command `{content}`"]))
            return data, False
        
        return data, True
        
    class edit_controller():
        def __init__(self, data, cog):
            self.emote = ["<:_chara:677763373739409436>", '<:_ue:677763400713109504>', "⭐", "\U0001F500"]
            self.data = data
            self.cog = cog
            self.current_page = None
            self.mode = None
            self._make()
        
        def _make(self):
            self.norm = self.cog.make_chara_embed(self.data)
            self.flb = self.cog.make_chara_embed(self.data, flb=True)
            self.alt = self.cog.make_chara_embed(self.data, alt=True)
            self.ue = self.cog.make_chara_embed(self.data, ue=True)
        
        def start(self):
            self.current_page = self.norm
            self.mode = "norm"
            return self.current_page
        
        def switch(self, mode):
            if mode == 'norm':
                self.current_page = self.norm
            elif mode == "flb":
                self.current_page = self.flb
            elif mode == "alt":
                self.current_page = self.alt
            elif mode == 'ue':
                self.current_page = self.ue
            self.mode = mode
            return self.current_page
        
        def reload(self, data):
            self.data = data
            self._make()
            if self.mode == "norm":
                self.current_page = self.norm
            elif self.mode == "alt":
                self.current_page = self.alt
            elif self.mode == "flb":
                self.current_page = self.flb
            elif self.mode == "ue":
                self.current_page = self.ue
            return self.current_page
        
    def make_chara_embed(self, chara, **kwargs):
        flb = kwargs.get("flb", False)
        alt = kwargs.get("alt", False)
        ue = kwargs.get("ue", False)
        null = "N/A"
        embed = discord.Embed(
            title=f"Edit Character - {chara['basic']['en']['name']} ({chara['basic']['jp']['name']})",
            timestamp=datetime.datetime.utcnow()
        )
        # thumbnail
        if flb:
            embed.set_thumbnail(url=chara['img6'] if chara['img6'] else "https://redive.estertion.win/icon/unit/000001.webp")
        elif ue:
            embed.set_thumbnail(url=chara['ue']['img'] if chara['ue']['img'] else "https://redive.estertion.win/icon/equipment/999999.webp")
        else:
            embed.set_thumbnail(url=chara['img'])
        
        # 4 modes -> norm, alt, ue, flb
        # BASIC: this should be in every mode -> name, prefix, tags,        (4)
        # norm ->   ub,     sk1, sk1p               sk2,    ex, ex2,        (18)
        # alt ->                        sk1a, sk1ap,    sk2a                (9)
        # ue ->             sk1, sk1p,                              ue_name (12)
        # flb ->    ub, ub2                                                 (6)
        def get_text(data):
            return data if data else null

        # basic
        embed.add_field(
            name="name_jp",
            value=chara['basic']['jp']['name']
        )
        embed.add_field(
            name="name_en",
            value=get_text(chara['basic']['en']['name'])
        )
        embed.add_field(
            name="prefix_en",
            value=get_text(chara['basic']['en']['prefix'])
        )
        embed.add_field(
            name="tags",
            value=get_text(chara['tags']),
            inline=False
        )
        # ub, ub2
        if not alt and not ue:
            embed.add_field(
                name=SPACE,
                value="**Union Burst**",
                inline=False
            )
            embed.add_field(
                name="ub_jp",
                value=chara['basic']['jp']['ub']['text']
            )
            embed.add_field(
                name="ub_en",
                value=get_text(chara['basic']['en']['ub']['text'])
            )
            if flb:
                embed.add_field(
                    name=SPACE,
                    value="**Union Burst+**",
                    inline=False
                )
                embed.add_field(
                    name="ub2_jp",
                    value=get_text(chara['basic']['jp']['ub2']['text'])
                )
                embed.add_field(
                    name="ub2_en",
                    value=get_text(chara['basic']['en']['ub2']['text'])
                )

        # sk1, sk1p
        if not alt and not flb:
            embed.add_field(
                name=SPACE,
                value="**Skill 1**",
                inline=False
            )
            embed.add_field(
                name="sk1_jp",
                value=chara['basic']['jp']['sk1']['text']
            )
            embed.add_field(
                name="sk1_en",
                value=get_text(chara['basic']['en']['sk1']['text'])
            )
            embed.add_field(
                name=SPACE,
                value="**Skill 1+**",
                inline=False
            )
            embed.add_field(
                name="sk1p_jp",
                value=get_text(chara['basic']['jp']['sk1p']['text'])
            )
            embed.add_field(
                name="sk1p_en",
                value=get_text(chara['basic']['en']['sk1p']['text'])
            )

        # sk1a, sk1ap, sk2a
        if alt:
            embed.add_field(
                name=SPACE,
                value="**Skill 1 Special**",
                inline=False
            )
            embed.add_field(
                name="sk1a_jp",
                value=get_text(chara['basic']['jp']['sk1a']['text'])
            )
            embed.add_field(
                name="sk1a_en",
                value=get_text(chara['basic']['en']['sk1a']['text'])
            )
            embed.add_field(
                name=SPACE,
                value="**Skill 1 Special+**",
                inline=False
            )
            embed.add_field(
                name="sk1ap_jp",
                value=get_text(chara['basic']['jp']['sk1ap']['text'])
            )
            embed.add_field(
                name="sk1ap_en",
                value=get_text(chara['basic']['en']['sk1ap']['text'])
            )
            embed.add_field(
                name=SPACE,
                value="**Skill 2 Special**",
                inline=False
            )
            embed.add_field(
                name="sk2a_jp",
                value=get_text(chara['basic']['jp']['sk2a']['text'])
            )
            embed.add_field(
                name="sk2a_en",
                value=get_text(chara['basic']['en']['sk2a']['text'])
            )

        # ue_name
        if ue:
            embed.add_field(
                name=SPACE,
                value="**UE Name**",
                inline=False
            )
            embed.add_field(
                name="uename_jp",
                value=get_text(chara['ue']['jp']['name'])
            )
            embed.add_field(
                name="uename_en",
                value=get_text(chara['ue']['en']['name'])
            )
            embed.add_field(
                name=SPACE,
                value="**UE Text**",
                inline=False
            )
            embed.add_field(
                name="uetext_jp",
                value=get_text(chara['ue']['jp']['text'])
            )
            embed.add_field(
                name="uetext_en",
                value=get_text(chara['ue']['en']['text'])
            )

        # sk2, ex, ex2
        if not alt and not ue and not flb:
            embed.add_field(
                name=SPACE,
                value="**Skill 2**",
                inline=False
            )
            embed.add_field(
                name="sk2_jp",
                value=chara['basic']['jp']['sk2']['text']
            )
            embed.add_field(
                name="sk2_en",
                value=get_text(chara['basic']['en']['sk2']['text'])
            )
            embed.add_field(
                name=SPACE,
                value="**EX Skill**",
                inline=False
            )
            embed.add_field(
                name="ex_jp",
                value=chara['basic']['jp']['ex']['text']
            )
            embed.add_field(
                name="ex_en",
                value=get_text(chara['basic']['en']['ex']['text'])
            )
            embed.add_field(
                name=SPACE,
                value="**EX+ Skill**",
                inline=False
            )
            embed.add_field(
                name="ex2_jp",
                value=get_text(chara['basic']['jp']['ex2']['text'])
            )
            embed.add_field(
                name="ex2_en",
                value=get_text(chara['basic']['en']['ex2']['text'])
            )
            
        return embed

    @commands.command()
    async def edit(self, ctx, request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        elif not request:
            return

        # check if delete mode
        delete = request.startswith('-')
        if delete:
            request = request[1:]
        
        # character should be proper - strict and no aliases allowed
        prefix, _, name = request.partition(".")

        # validate
        match, _ = self.validate_request({"name":name if name else prefix, "prefix":prefix if name else None})

        if not match:
            await channel.send(f"Did not find character `{request}`")
            return

        # get bulk data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data = json.load(dbf)
        
        # edit
        if not delete:
            await channel.send(f"Editing `{match['name_en']}({match['prefix']})` -> `{all_data['units'][match['index']]['basic']['en']['name']}({all_data['units'][match['index']]['basic']['en']['prefix']})`")
            unit = await self.edit_chara(ctx, all_data['units'][match['index']])

            # append
            all_data['units'][match['index']] = unit
        else:
            await channel.send(f"Deleting `{match['name_en']}({match['prefix']})` -> `{all_data['units'][match['index']]['basic']['en']['name']}({all_data['units'][match['index']]['basic']['en']['prefix']})`")
            del all_data['units'][match['index']]

        # save db
        msg = await ctx.message.channel.send("Saving db...")
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']), "w+") as dbf:
            dbf.write(json.dumps(all_data, indent=4))
        await msg.edit(content=msg.content+" done")

        if delete:
            # update local index
            msg = await ctx.message.channel.send("Making local index...")
            self.make_index()
            await msg.edit(content=msg.content+" done")
        
if __name__ == "__main__":
    pass