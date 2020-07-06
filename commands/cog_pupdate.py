# experimental cog that mainly serves as a playground for code stuff

import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests, copy, time, glob, re
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
SPACE = '\u200B'

def setup(client):
    client.add_cog(updateCog(client))

preupdate_checklist = [
    "+ update hnoteDB source",
    "+ check for new indicies in tl_index"
]
update_meta = [
    "+ updates prefix_title, prefix_new in hatsune_config.json",
    "+ updates unit_list index",
    "+ grab new assets from estertion by comparing with fag (if applicable)",
    "+ convert and upload new assets (if applicable)",
    "+ updates gacha state"
]

def validate_request(client, request:dict, mode="en"):
    # request needs to be a dictionary of the form {"name":str,"prefix":Union(None,str)}
    # returns match:Union(dict,None), alts:Union(list,None)

    # load index
    with open(os.path.join(client.dir, client.config['unit_list_path'])) as idf:
        index = json.load(idf)

    if mode == "en":
        # exact match
        match = list(filter(lambda x: x['name_en'] == request['name'] and x['prefix'] == request['prefix'], index['index']))
    else:
        pass

    # check
    if not match:
        # do another search but with sname for backwards compat
        match = list(filter(lambda x: x['sname'] == request['name'], index['index']))
        if not match:
            # error
            return None, None
        else:
            request['name'] = match[0]['name_en']
            request['prefix'] = match[0]['prefix']
        
    alts = list(filter(lambda x: x['name_en'] == request['name'], index['index']))
    return {**match[0],"index":index['index'].index(match[0])}, [{**alt,"index":index['index'].index(alt)} for alt in alts if alt['sname'] != match[0]['sname']]

class updateCog(commands.Cog):
    def __init__(self, client):
        self.client =   client
        self.name =     '[prototype-update]',
        self.logger =   client.log
        self.db =       self.client.database
        #self.colour =   discord.Colour.from_rgb(*self.client.config['command_colour']['cog_update'])
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
            temp['pos'] =                   int(pos) if pos else -1
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
        await ctx.message.channel.send(".")

    def get_unit_status(self, raw, data):
        status = data['status']
        status['ue'] =      raw['UE_MAX']
        status['lvl'] =     raw['LEVEL_MAX']
        status['rk'] =      raw['RANK_MAX']
        data['status'] = status
        return data
    
    def get_unit_profile(self, raw, data):
        data['basic']['jp']['id'] = int(raw['id'])
        data['basic']['jp']['comment'] = re.sub(r'\\n', '', raw['comment'])

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
                    data['ue']['jp']['text'] = re.sub(r'\\n', '',item)
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

# may need to write a function that would update data structure in the future should I modify it
    def make_sname(self, name, prefix):
        if not prefix:
            prefix = ""
        if not name:
            return None
        return "".join([prefix,name]).lower()

    @commands.group()
    async def update_db_structure(self, ctx):
        channel=ctx.message.channel
        author=ctx.message.author
        if not self.client._check_author(author):
            return
        
        # open and load
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data  = json.load(dbf)
        
        # do stuff
        for i in range(len(all_data['units'])):
            all_data['units'][i]['basic']['jp']['comment'] = re.sub(r'\\n', '', all_data['units'][i]['basic']['jp']['comment']) if all_data['units'][i]['basic']['jp']['comment'] else None
        
        # save
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']), "w+") as dbf:
            dbf.write(json.dumps(all_data,indent=4))
        
        await channel.send("Updated db structure")

    @commands.group()
    async def update(self, ctx):
        channel = ctx.channel
        if not ctx.invoked_subcommand is None:
            return
        elif not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return 
        
        def check_m(msg):
            return self.client._check_author(msg.author) and msg.channel == channel

        # check
        if not self.client.config['debug'] == 1:
            prompt = await channel.send(self.client.emotes['ames']+" Warning - Ames is not in debug mode! Continue? y/n")
            while True:
                try:
                    message = await self.client.wait_for('message', timeout=15.0, check=check_m)
                except:
                    await channel.send("timeout - aborting update")
                    return
                else:
                    if message.content[0].lower() == 'y':
                        break
                    elif message.content[0].lower() == 'n':
                        await channel.send("cancelled")
                        return

        # preupdate checklist
        yn_reacts = ['<:akagiPillowYes:659673125532860438>','<:kagaPillowNo:659673121778827274>']
        yn_name = ['akagiPillowYes','kagaPillowNo']
        ckltxt = "\n".join(preupdate_checklist)
        updtxt = "\n".join(update_meta)

        prompt = await channel.send(
            "The update will perform the following actions:\n"
            f"```diff\n{updtxt}```\n"
            "The following items must be complete before the update can proceed; awaiting completion\n"
            f"```diff\n{ckltxt}```"
        )
        for react in yn_reacts:
            await prompt.add_reaction(react)

        def check(reaction, user):
            return str(user.id) == str(235361069202145280) and reaction.emoji.name in yn_name and str(reaction.message.id) == str(prompt.id)
        
        while True:
            reaction, user = await self.client.wait_for('reaction_add', check=check)
            if reaction.emoji.name in '<:akagiPillowYes:659673125532860438>':
                break
            elif reaction.emoji.name in '<:kagaPillowNo:659673121778827274>':
                await channel.send('aborted')
                return
        
        # step 0 - update hnote config
        await channel.send("Updating hnote config - enter command(s) or `x` to skip or end")
        while True:
            try:
                message = await self.client.wait_for('message', check=check_m)
            except Exception as e:
                await message.send("Something went wrong with hnote config update - check logs")
                await self.logger.send(self.name, e)
            else:
                command = message.content
                if command == 'x':
                    await channel.send("skipping")
                    break
                else:
                    await self.update_hatsune(ctx, command)
                    break

        # step 1 - update and append new charas
        await channel.send("> Starting update process")
        msg = await channel.send("Fetching from HNDB, creating new templates, and making index...")
        
        try:
            await self.update_hatsune(ctx)
        except Exception as e:
            await self.logger.send(self.name, e)
            await msg.edit(content=msg.content+" **failed**")
        else:
            await msg.edit(content=msg.content+" **done**")

        
        # step 2 - update assets
        msg = await channel.send("Updating local assets...")
        await self.update_res(ctx)
        await msg.edit(content=msg.content+" **done**")

        # step 3 - servers
        msg = await channel.send("Updating server assets...")
        await self.update_server(ctx)
        await msg.edit(content=msg.content+" **done**")

        # step 4 - gacha
        await channel.send("Updating gacha state - enter command(s) or `x` to skip or end")
        while True:
            try:
                message = await self.client.wait_for('message', check=check_m)
            except Exception as e:
                await message.send("Something went wrong with gacha update - check logs")
                await self.logger.send(self.name, e)
            else:
                command = message.content
                if command == 'x':
                    await channel.send("skipping")
                    break
                else:
                    await self.update_gacha(ctx, command)
                    break
        
        await channel.send("Update complete "+self.client.emotes['sarenh'])

    @update.command(aliases=['hnote','hn','hndb','hnotedb'])
    async def db(self, ctx, *options):
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
        await channel.send("Finished making index")
    
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
            sname = "".join([temp['prefix'].lower() if temp['prefix'] else '', temp['name_en'].lower() if temp['name_en'] else ''])
            temp['sname'] = sname if sname else None
            indexv.append(temp)
        
        index['index'] = indexv
        with open(os.path.join(self.client.dir, self.client.config['unit_list_path']), "w+") as idf:
            idf.write(json.dumps(index,indent=4))

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
            unit['sname'] = self.make_sname(unit['basic']['en']['name'], unit['basic']['en']['prefix'])
            all_data['units'].append(unit)
            all_data = await self.edit_pos(ctx, unit, all_data)

        # do not recommend - will take around 3min to do a complete forced update
        if forced:
            msg = await ctx.message.channel.send("Forcing update from Hnote...")
            all_data['units'] = [(await self.get_data(ctx, unit, all_data=all_data))[0] for unit in all_data['units']]
            await msg.edit(content=msg.content+" done")
            
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
                        await header_msg.edit(embed=edit.reload(chara))
                    #await cmd.edit(content="\n".join([cmd.content, f"Unknown command `{inp.content}`"]))
                confirmation = False
        await cmd.delete()
        await header_msg.edit(content=f"Updated `{chara['basic']['jp']['name']}`",embed=None)
        chara['sname'] = self.make_sname(chara['basic']['en']['name'], chara['basic']['en']['prefix'])
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
    async def edit(self, ctx, request, *options):
        channel = ctx.message.channel
        author = ctx.message.author
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        elif not request:
            return
        pos = "pos" in options
        review = "all" in options or request == "all"

        # get bulk data
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data = json.load(dbf)

        if not review:
            # check if delete mode
            delete = request.startswith('-')
            if delete:
                request = request[1:]
            
            # character should be proper - strict and no aliases allowed
            prefix, _, name = request.partition(".")

            # validate
            match, _ = validate_request(self.client, {"name":name if name else prefix, "prefix":prefix if name else None})

            if not match:
                await channel.send(f"Did not find character `{request}`")
                return
            
            # edit
            if not pos:
                if not delete:
                    await channel.send(f"Editing `{match['name_en']}({match['prefix']})` -> `{all_data['units'][match['index']]['basic']['en']['name']}({all_data['units'][match['index']]['basic']['en']['prefix']})`")
                    unit = await self.edit_chara(ctx, all_data['units'][match['index']])

                    # append
                    all_data['units'][match['index']] = unit
                else:
                    await channel.send(f"Deleting `{match['name_en']}({match['prefix']})` -> `{all_data['units'][match['index']]['basic']['en']['name']}({all_data['units'][match['index']]['basic']['en']['prefix']})`")
                    del all_data['units'][match['index']]
            # pos
            else:
                all_data = await self.edit_pos(ctx, all_data['units'][match['index']], all_data)
        else:
            # iterate through all_data
            for i in range(len(all_data['units'])):
                chara = all_data['units'][i]
                await channel.send(f"Editing `{chara['sname']}`")
                chara = await self.edit_chara(ctx, chara)
                all_data['units'][i] = chara
                all_data = await self.edit_pos(ctx, chara, all_data)
            
        # save db
        msg = await ctx.message.channel.send("Saving db...")
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']), "w+") as dbf:
            dbf.write(json.dumps(all_data, indent=4))
        await msg.edit(content=msg.content+" done")

        # make index only under certain conditions
        if delete or pos or review:
            # update local index
            msg = await ctx.message.channel.send("Making local index...")
            self.make_index()
            await msg.edit(content=msg.content+" done")
    
    async def edit_pos(self, ctx, chara, all_data):
        # assumes chara is already in all_data
        def check(msg):
            return self.client._check_author(msg.author) and msg.channel == ctx.message.channel

        # premake vg, mg and rg ranks
        def split_data(chara, units):
            vg, mg, rg = [], [], []
            for unit in units:
                if not unit == chara:
                    if "front" in unit['tags']:
                        vg.append(unit)
                    elif "mid" in unit['tags']:
                        mg.append(unit)
                    elif "rear" in unit['tags']:
                        rg.append(unit)
            return vg, mg, rg
        
        # shifters
        async def shift(cmd, chara, lineup, mode, field, val):
            start, _, end = val.partition("-")
            if mode == "front":
                l = 100
                u = 199
            elif mode == "mid":
                l = 200
                u = 299
            else:
                l = 300
                u = 399

            start = int(start) if start.isnumeric() else None
            end = int(end) if end.isnumeric() else None

            # sanity check
            if not start:
                await cmd.edit(content="\n".join([cmd.content, f"start value not specified"]))
                return lineup, chara
            else:
                if start >= u or start <= l:
                    await cmd.edit(content="\n".join([cmd.content, f"start value out of range"]))
                    return lineup, chara

                if end:
                    if end >= u or end <= l:
                        await cmd.edit(content="\n".join([cmd.content, f"end value out of range"]))
                        return lineup, chara
                else:
                    end = u
            
            # process command
            if field in ["push", "insert"]:
                await cmd.edit(content="\n".join([cmd.content, f"push {start}-{end}"]))
                for i in range(len(lineup)):
                    if lineup[i]['pos'] >= start and lineup[i]['pos'] <= end:
                        lineup[i]['pos'] += 1

            if field in ["set", "insert"]:
                await cmd.edit(content="\n".join([cmd.content, f"set target pos {start}"]))
                chara['pos'] = start

            if field == "pull":
                await cmd.edit(content="\n".join([cmd.content, f"pull {start}-{end}"]))
                for i in range(len(lineup)):
                    if lineup[i]['pos'] >= start and lineup[i]['pos'] <= end:
                        lineup[i]['pos'] -= 1

            return lineup, chara
        
        vg, mg, rg = split_data(chara, all_data['units'])

        header = await ctx.message.channel.send(embed=self.make_pos_embed(chara, vg, mg, rg))
        txt = "Editting character position.\nUse `tags:tag1,tag2,...` to edit tags or use `push|pull|set|insert` commands. Type `exit` to finish."
        cmd = await ctx.message.channel.send(txt)
        
        while True:
            message = await self.client.wait_for('message', check=check)

            if not message.content.startswith('--'):
                await message.delete()
                content = message.content
                field, _, val = content.partition(":")
                field, val = field.strip(), val.strip()

                if field == "tags":
                    chara['tags'] = [i.strip() for i in val.split(',')] if val else []
                    await cmd.edit(content="\n".join([txt,f"> set tags to {chara['tags']}"]))
                elif field == "exit":
                    break
                elif not any([lp in chara['tags'] for lp in ['front','mid','rear']]):
                    await cmd.edit(content="\n".join([txt,"Cannot process command: no lineup identifier found"]))
                    continue
                else:
                    if field in ['push','pull','insert','set']:
                        # these are pointers - not copied
                        if "front" in chara['tags']:
                            vg, chara = await shift(cmd, chara, vg, "front", field, val)
                        elif "mid" in chara['tags']:
                            mg, chara = await shift(cmd, chara, mg, "mid", field, val)
                        else:
                            rg, chara = await shift(cmd, chara, rg, "rear", field, val)
                    
                        # syntax
                        # push [start(-end)] -> shifts all pos >= start +1
                        # pull [start(-end)] -> shifts all pos >= start -1
                        # set num -> sets target chara pos to num
                        # insert num -> push num; set num;

                        #shift(cmd, chara, lineup, mode, field, val)
                    else:
                        await cmd.edit(content="\n".join([txt, f"Unknown command {content}"]))
                        continue
                
                await header.edit(embed=self.make_pos_embed(chara, vg, mg, rg))
        
        # save and whatnot
        #do something
        await cmd.delete()
        await header.edit(content=f"Updated pos for `{chara['basic']['jp']['name']}`",embed=None)
        all_data['units'] = vg+mg+rg
        all_data['units'].append(chara)
        return all_data

    def make_pos_embed(self, chara, vg, mg, rg):
        # should have: tags, pos, lineup
        
        def make_line(chara, client, active=False):
            line = "{} {} {}" if not active else "> {} **{} {}**"
            sname = chara['basic']['en']['prefix'].title() + chara['basic']['en']['name'].title() if chara['basic']['en']['prefix'] else chara['basic']['en']['name'].title()
            return line.format(client.team[sname.lower()], str(chara['pos']) if chara['pos'] != -1 else '??', sname)
        
        lineup = None
        if "front" in chara['tags']:
            lineup = vg.copy()
            mode = "Vanguard"
        elif "mid" in chara['tags']:
            lineup = mg.copy()
            mode = "Midguard"
        elif "rear" in chara['tags']:
            lineup = rg.copy()
            mode = "Rearguard"
        
        embed = discord.Embed(
            title=f"Edit Character Position - {chara['basic']['en']['name']} ({chara['basic']['jp']['name']})",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=chara['img'])

        embed.add_field(
            name="tags",
            value=chara['tags'],
            inline=False
        )
        embed.add_field(
            name="pos",
            value=chara['pos'] if chara['pos'] != -1 else "TBC",
            inline=False
        )

        if lineup:
            lineup.append(chara)
            lineup.sort(key=lambda x: x['pos'])
            for chunk in list(self.client.chunks(lineup, 20)):
                embed.add_field(
                    name=f"{mode} Lineup",
                    value="\n".join([make_line(c, self.client, c==chara) for c in chunk])
                )
        else:
            embed.add_field(
                name="Lineup",
                value=f"{chara['basic']['jp']['name']} is missing lineup identifier. Consider using edit or just adding it here."
            )
        
        return embed

    @update.command()
    async def gacha(self, ctx, command_line):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return

        await self.update_gacha(ctx, command_line)

    async def update_gacha(self, ctx, command_line):
        channel = ctx.channel

        with open(os.path.join(self.client.dir,self.client.config['unit_list_path'])) as upf:
            units = json.load(upf)

        with open(os.path.join(self.client.dir,self.client.config['gacha_config_path']), 'r') as gcf:
            gacha_config = json.load(gcf)

        for command in command_line.split(';'):
            mode, _, value = command.partition('.')

            if mode == 'prifes':
                await channel.send(f"setting prifes to {value}")
                gacha_config['prifes'] = int(value)

            elif mode == 'lim':
                await channel.send(f"replacing limited pool with {value.split(',')}")
                gacha_config['pools']['lim'] = value.split(',')

            elif mode in ['r','sr','ssr']:
                for chara in value.split(','):
                    if chara.startswith('-'):
                        chara = chara[1:]
                        flag = 'del'
                    else:
                        flag = 'add'
                    
                    if not chara.lower() in units['en']:
                        await channel.send(f"could not edit `{value}` - `{chara}` does not exist")
                        continue

                    elif flag == 'del':
                        if not chara in gacha_config['pools'][mode]:
                            await channel.send(f"could not remove `{chara}` from `{mode}` pool - character is not present in pool")
                            
                        else:
                            await channel.send(f"removing `{chara}` from `{mode}` pool")
                            gacha_config['pools'][mode].pop(gacha_config['pools'][mode].index(chara))

                    elif flag == 'add':
                        if chara in gacha_config['pools'][mode]:
                            await channel.send(f"could not add `{chara}` to `{mode}` pool - character is already present in pool")

                        else:
                            await channel.send(f"adding `{chara}` to `{mode}` pool")
                            gacha_config['pools'][mode].append(chara)
            
            elif mode.startswith('o'):
                msg = await channel.send("Force overwriting local assets with base rarity assets...")

                with open(os.path.join(self.client.dir, self.client.config['gacha_config_path'])) as gcf:
                    gcfg = json.load(gcf)

                with open(os.path.join(self.client.dir, self.client.config['unit_list_path'])) as ulf:
                    uindex = json.load(ulf)

                for rarity, pool in list(gcfg['pools'].items()):
                    if not rarity in ['lim', 'ssr']:
                        for chara in pool:
                            chara = chara.lower()
                            try:
                                hn_id = uindex['hn'][uindex['en'].index(chara)]
                                self.fetch_res_estertion(chara, hn_id, None)
                            except Exception as e:
                                await self.logger.send(self.name, e)
                                await channel.send(f"Failed to process `{chara}`")
                
                await msg.edit(content=msg.content+" **done**")

            else:
                await channel.send(f"[gacha] Unknown command {command}")
            
        with open(os.path.join(self.client.dir,self.client.config['gacha_config_path']), 'w') as gcf:
            msg = await channel.send("saving changes... ")
            gcf.write(json.dumps(gacha_config, indent=4))
            await msg.edit(content=msg.content+"done")
        
        
        if self.client.cogs_status.get('commands.cog_gacha', False) == True:
            msg = await channel.send("reloading cog_gacha... ")
            self.client.unload_extension("commands.cog_gacha")
            self.client.load_extension("commands.cog_gacha")
            await msg.edit(content=msg.content+"done")
        else:
            await channel.send("cog_gacha is not loaded - update will not reload said cog")

    @update.command()
    async def res(self, ctx):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return
        await self.update_res(ctx)

    def fetch_res_local(self):
        local_list = []
        for filename in glob.glob(os.path.join(self.client.dir, self.client.config['png_path'], '*.png')):
            local_list.append(filename.split('\\')[-1].split('.')[0])
        return local_list
    
    async def update_res(self, ctx):
        channel = ctx.channel
        await channel.send("> Beginning update")
        msg =       await channel.send("...") 

        with open(os.path.join(self.client.dir, self.client.config['unit_list_path'])) as ulf:
            index = json.load(ulf)

        local_list = self.fetch_res_local()

        hnote_id =  index['hn']
        en =        index['en']
        flb =       index['flb']
        succ, fail = 0,0
        for character in en:
            position = en.index(character)
            if not hnote_id[position] == None:
                try:
                    if not character in local_list:
                        txt = f"fetching `{character}`... "
                        await msg.edit(content=txt)
                        await self.logger.send(self.name, "fetching", character, hnote_id[position])

                        self.fetch_res_estertion(character, hnote_id[position])

                        await msg.edit(content=txt+"done")
                        succ += 1
                        
                    if not character+'6' in local_list and flb[position]:
                        txt = f"fetching `{character}` flb... "
                        await msg.edit(content=txt)
                        await self.logger.send(self.name, "fetching", character+'6', hnote_id[position])

                        self.fetch_res_estertion(character, hnote_id[position], True)

                        await msg.edit(content=txt+"done")
                        succ += 1

                except Exception as e:
                    fail += 1
                    await self.logger.send(self.name, e)
                    await msg.edit(content=txt+"failed")
                    msg = await channel.send("Continuing update")
        
        await channel.send(f"> res update finished with {succ} success and {fail} failed updates")
        await self.logger.send(self.name, 'res update', succ, fail)
    
    def fetch_res_estertion(self, name, hnote_id, flb=False):
        if flb:
            url = f"https://redive.estertion.win/icon/unit/{hnote_id}61.webp"
            save = f"{name}6.png"
        elif flb == None:
            url = f"https://redive.estertion.win/icon/unit/{hnote_id}11.webp"
            save = f"{name}.png"
        else:
            url = f"https://redive.estertion.win/icon/unit/{hnote_id}31.webp"
            save = f"{name}.png"
        
        icon = Image.open(BytesIO(requests.get(url).content))

        icon.save(os.path.join(self.client.dir,self.client.config['png_path'],save))
        icon.close()

    @update.command()
    async def server(self, ctx):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return
        await self.update_server(ctx)
        
    def fetch_server_res(self):
        guilds = []
        server_emotes = []
        for server_id in self.client.private['resource_servers']:
            guild = self.client.get_guild(server_id)
            guilds.append(guild)
            server_emotes += list(guild.emojis)
        
        return guilds, [emote.name for emote in server_emotes]
    
    async def update_server(self, ctx):
        channel = ctx.channel

        local_list = self.fetch_res_local()
        servers, server_emotes = self.fetch_server_res()

        flag = None
        for local_emote in local_list:
            if not local_emote in server_emotes:
                for server in servers:
                    flag = False
                    if server.emoji_limit == len(server.emojis):
                        await self.logger.send(self.name, "server full", server.id)
                    else:
                        await self.logger.send(self.name, 'creating', local_emote, 'in', server.name, f"{server.emoji_limit} ({len(server.emojis)})","\n")
                        
                        with open(os.path.join(self.client.dir, self.client.config['png_path'], f"{local_emote}.png"), "rb") as update_emote:
                            try:
                                await server.create_custom_emoji(name=local_emote, image=update_emote.read())
                            except Exception as e:
                                await self.logger.send(self.name, "failed to upload", e)
                                traceback.print_exc()
                            else:
                                await self.logger.send(self.name, 'success')
                                flag = True
                if flag is True:
                    await channel.send(f"Added {local_emote}")
                elif flag is False:
                    await channel.send(f"Failed to add {local_emote}")
        if flag is None:
            await channel.send("All assets already up to date")

        self.client._load_resource()

    @update.command()
    async def hatsune(self, ctx, command_line):
        channel = ctx.channel
        if not self.client._check_author(ctx.channel.author):
            await channel.send(self.client.emotes['anes'])
            return
        await self.update_hatsune(ctx, command_line)

    async def update_hatsune(self, ctx, command_line):
        channel = ctx.channel
        
        with open(os.path.join(self.client.dir,self.client.config['hatsune_config_path'])) as hcf:
            hconfig = json.load(hcf)
        
        for command in command_line.split(';'):
            mode, value = command.split('.')
            if mode == 'p':
                for kv in value.split(','):
                    if kv[0] == '-':
                        flag = 'del'
                        k = kv[1:]
                    else:
                        flag = 'add'
                        k, v = kv.split('=')

                    if k in list(hconfig['prefix_title'].keys()):
                        if flag == 'del':
                            await channel.send(f"removing prefix `{k}` -> `{hconfig['prefix_title'][k]}`")
                            hconfig['prefix_title'].pop(k)
                        elif flag == 'add':
                            await channel.send(f"changing prefix `{k}` from `{hconfig['prefix_title'][k]}` to `{v}`")
                            hconfig['prefix_title'][k] = v
                    else:
                        if flag == 'del':
                            await channel.send(f"could not remove prefix {k} as it does not exist")
                        elif flag == 'add':
                            await channel.send(f"adding prefix `{k}` -> `{v}`")
                            hconfig['prefix_title'][k] = v
            
            elif mode == 'pn':
                "pn.r=a,b,c"
                if value[0] == '-':
                    flag = 'del'
                    k = value[1:]
                else:
                    flag = 'add'
                    k, v = value.split('=')
                
                if k in list(hconfig['prefix_new'].keys()):
                    if flag == 'del':
                        await channel.send(f"Removing prefix alias {k} <- {hconfig['prefix_new'][k]}")
                        hconfig['prefix_new'].pop(k)
                    elif flag == 'add':
                        await channel.send(f"Setting prefix alias {k} from {hconfig['prefix_new'][k]} to {v.split(',')}")
                        hconfig['prefixes_new'][k] = v.split(',')
                else:
                    if flag == 'del':
                        await channel.send(f"Could not remove prefix alias {k} as it does not exist")
                    elif flag == 'add':
                        await channel.send(f"Adding prefix alias {k} <- {v.split(',')}")
                        hconfig['prefix_new'][k] = v.split(',')
            
            else:
                await channel.send(f"Unknown command {command}")
        
        with open(os.path.join(self.client.dir,self.client.config['hatsune_config_path']), 'w') as hcf:
            msg = await channel.send("Saving hatsune config file...")
            hcf.write(json.dumps(hconfig,indent=4))
            await msg.edit(content=msg.content+" **done**")
        
        if self.client.cogs_status.get('commands.cog_hatsune', False) == True:
            msg = await channel.send("reloading cog_hatsune... ")
            self.client.unload_extension("commands.cog_hatsune")
            self.client.load_extension("commands.cog_hatsune")
            await msg.edit(content=msg.content+"done")
        else:
            await channel.send("cog_hatsune is not loaded - update will not reload said cog")

    @update.command(aliases=['exskills','ex'])
    async def exskill(self, ctx):
        channel = ctx.message.channel
        author = ctx.message.channel
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
        
        def check(msg):
            return self.client._check_author(msg.author) and msg.channel == ctx.message.channel

        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path'])) as dbf:
            all_data = json.load(dbf)
        
        with open(os.path.join(self.client.dir, self.client.config['ex_skills_path'])) as exf:
            exskills = json.load(exf)
        
        untl, new = 0,0
        for i in range(len(all_data['units'])):
            chara = all_data['units'][i]

            # ex
            if not chara['basic']['jp']['ex']['text'] in exskills:
                new += 1
                exskills[chara['basic']['jp']['ex']['text']] = None

            elif exskills[chara['basic']['jp']['ex']['text']]:
                chara['basic']['en']['ex']['text'] = exskills[chara['basic']['jp']['ex']['text']]
            
            else:
                untl += 1
                chara['basic']['en']['ex']['text'] = None
            
            # ex2
            if not chara['basic']['jp']['ex2']['text'] in exskills:
                new += 1
                exskills[chara['basic']['jp']['ex2']['text']] = None

            elif exskills[chara['basic']['jp']['ex2']['text']]:
                chara['basic']['en']['ex2']['text'] = exskills[chara['basic']['jp']['ex2']['text']]
            
            else:
                untl += 1
                chara['basic']['en']['ex2']['text'] = None
            
            all_data['units'][i] = chara
        
        with open(os.path.join(self.client.dir, self.client.config['ex_skills_path']), "w+") as exf:
            exf.write(json.dumps(exskills, indent=4))
        
        await channel.send(f"Preliminary extraction and insertion done. Found `{untl}` untranslated and `{new}` new entries.")

        if untl != 0 or new != 0:
            batch = list(filter(lambda x: x[1] == None, list(exskills.items())))
            current = await channel.send("Start")
            for key, _ in batch:
                txt = f"EX Skill: {key}"
                await current.edit(content=txt)

                confirm = False
                while True:
                    msg = await self.client.wait_for("message", check=check)

                    if not msg.content.startswith('--'):
                        await msg.delete()

                        if msg == "exit":
                            break

                        if not confirm:
                            confirm = True
                            cnt = msg.content
                            await current.edit(content="\n".join([txt, f"> Set to `{cnt}`? `y/n`"]))

                        elif confirm and msg.content == "y":
                            exskills[key] = cnt
                            break
                        
                        else:
                            await current.edit(content="\n".join([txt, f"cancelled"]))
                            confirm = False
        
        with open(os.path.join(self.client.dir, self.client.config['hatsune_db_path']), "w+") as dbf:
            dbf.write(json.dumps(all_data, indent=4))
        
        with open(os.path.join(self.client.dir, self.client.config['ex_skills_path']), "w+") as exf:
            exf.write(json.dumps(exskills, indent=4))
        
        await channel.send("EX skill update complete")
                    
