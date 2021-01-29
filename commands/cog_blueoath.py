# supposedly self-contained blueoath module

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO

from bs4 import BeautifulSoup
import os, sys, json, traceback, datetime, requests, asyncio, re, pytz, glob
import discord
from discord.ext import commands, tasks

SPACE = '\u200B'
dir_path = os.path.dirname(os.path.realpath(__file__))

class blueoathCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = "[blueoath]"
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_blueoath'])
        self.logger = client.log
        self.sheet = None
        self.index_url = "https://blueoath.miraheze.org/w/api.php"

        # load config
        with open(os.path.join(self.client.dir, self.client.config['blueoath_path'], "config.json")) as cf:
            self.config = json.load(cf)
        
        #OVERRIDE
        with open(os.path.join(dir_path, self.config['override'])) as ovf:
            override = json.load(ovf)
            for key, val in list(override.items()):
                self.config[key] = val
        
        self.ship_template = self.config['ship_data_template']
        
        # load alias
        with open(os.path.join(dir_path, self.config['alias_path'])) as af:
            self.alias_master = json.load(af)
        with open(os.path.join(dir_path, self.config['alias_local_path'])) as alf:
            self.alias_local = json.load(alf)
        
        self.alias = {**self.alias_local,**self.alias_master}
        
        with open(os.path.join(dir_path, self.config['tag_index_path'])) as tagf:
            self.tags = json.load(tagf)

        # load help
        with open(os.path.join(dir_path,self.config['help_path'])) as hf:
            self.help_config = json.load(hf)
            self.help_text = self.help_config["commands"]
            self.command_tags = self.help_config["help_tags"]

        # load assets
        #self._load_resource()

        #self._reload_sheet()
        self.check_oil.start()

        # persist
        self.active_embeds = dict()

    def _load_resource(self):
        # THIS IS USED IN OIL PRECHECK
        # since this will only work when client is ready
        self.ship_pfp = dict()
        self.res_servers = self.client.private['bo_resource_servers']
        for server in self.res_servers:
            for emj in self.client.get_guild(server).emojis:
                self.ship_pfp[emj.name] = f"<:{emj.name}:{emj.id}>"

    @commands.group(
        invoke_without_command=True,
        case_insensitive=True)
    async def bo(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.send("This command group contains all `Blue Oath` related commands. See `.bo help` for more details "+self.client.emotes['ames'])
            return
    
    @bo.command()
    async def update(self, ctx, *, option):
        channel = ctx.channel
        if not self.config['command_status']['update']:
            raise commands.DisabledCommand
        elif not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return
        elif not option:
            return
        
        session = requests.Session()

        inp = option.split("--")
        option = inp.pop(0).lower().strip()
        kw = inp

        if option == "index":
            await self._update_index(session, channel)
            return
        elif option == "all":
            await self._update_index(session, channel)
            with open(os.path.join(dir_path, self.config['index_path'])) as inf:
                chara_list = json.load(inf)["en"]
        elif option == "ships":
            with open(os.path.join(dir_path, self.config['index_path'])) as inf:
                chara_list = json.load(inf)["en"]
        else:
            with open(os.path.join(dir_path, self.config['index_path'])) as inf:
                index = json.load(inf)
            
            # sift alias
            _character = self.process_request(option)
            search_success, _character = self.validate_entry(_character)
            if search_success:
                option = _character['sname']

            # check
            if not option in index['search_name']:
                await channel.send(f"Did not find Senki `{option}`")
                return
            else:
                chara_list = [index['en'][index['search_name'].index(option)]]
        
        await self._update_chara(session, chara_list, channel, kw)
        session.close()
        await channel.send("finished")
            
    def clean_name(self, name:str):
        temp = []
        for token in name:
            if not token in [".", "\n"]:
                temp.append(token)

        temp = "".join(temp)
        clean = temp.translate(str.maketrans("üö", "uo"))
        return temp, clean

    def get_str(self, string:str):
        for x in ["<p>", "</p>", "<td>", "</td>","<br/>"]:
            while x in string:
                if x != "<br/>":
                    string = string.replace(x,"")
                else:
                    string = string.replace("<br/>", "\n")
        return string

    def get_img_link(self, link):
        md = link.split('/')[5:8]
        #print(md)
        fixed = f"https://static.miraheze.org/blueoathwiki/{'/'.join(md)}"
        #return fixed
        return fixed

    async def _update_index(self, s, channel):
        msg = await channel.send("Updating index...")
        params = {
                "action":           "parse",
                "page":             "Senki",
                "prop":             "text",
                "formatversion":    "2",
                "format":           "json"
            }

        r = s.get(url=self.index_url, params=params)
        if r.status_code != 200:
            await self.logger.send(self.name, "failed to fetch", r.status_code)
            await channel.send(f"Response Status Code: {r.status_code}")
            return

        data = r.json()
        if data.get("error", None) != None:
            await self.logger.send(self.name, data['error'])
            await channel.send("Something went wrong... "+self.client.emotes['sarens'])
            return
        
        html = data['parse']['text']
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all("table")

        img, en, disp, jp, clss, rarity = [],[],[],[],[],[]
        #main_index = tables[0]
        main_ = tables
        for main_index in main_:
            for i, row in enumerate(main_index.find_all("tr")[1:]):
                fields = row.find_all("td")
                #link = f"static.miraheze.org/blueoathwiki/{'/'.join(fields[0].img['src'].split('/')[3:6])}"
                #img.append(link)
                #img.append(fields[0].img['src'])
                img.append(self.get_img_link(fields[0].img['src']) if fields[0].img else None)
                jp.append(fields[1].text.replace("\n",""))
                disp.append(fields[2].text.replace("\n",""))
                en.append(self.clean_name(disp[-1])[-1])
                clss.append(fields[3].text.replace("\n",""))
                rarity.append(fields[4].text.replace("\n","") if fields[4].text else None)
        
        index = {
            "display_name": disp,
            "search_name": [n.lower() for n in en],
            "en": en,
            "jp": jp,
            "class": clss,
            "rarity": rarity,
            "portrait_square": img
        }

        with open(os.path.join(dir_path, self.config['index_path']), "w+") as inf:
            inf.write(json.dumps(index, indent=4))
        
        await msg.edit(content=msg.content+" **done**")
        
    async def _update_chara(self, s, charav, channel, inp):
        msg = await channel.send("Starting chara update")

        # read index and data before iteration
        if "sheet" in inp:
            with open(os.path.join(dir_path, self.config['sheet_data_path'])) as sdf:
                skills_jp = json.load(sdf)
        with open(os.path.join(dir_path, self.config['index_path'])) as inf:
            index = json.load(inf)
        with open(os.path.join(dir_path, self.config['tag_data_path'])) as tagf:
            ship_tags = json.load(tagf)
        
        j, k = 0, 0
        await msg.edit(content=f"Fetching...")
        for i, chara in enumerate(charav):
            if (i+1)%10==0: await msg.edit(content=msg.content+".")

            # load data
            #if not os.path.exists(os.path.join(dir_path, f"blueoath/data/{''.join(chara.split(' '))}.json")):
            temp = self.ship_template.copy()
            #else:
            #    with open(os.path.join(dir_path, f"blueoath/data/{''.join(chara.split(' '))}.json")) as sdf:
            #        temp = json.load(sdf)

            # supplement with sheet data first before overwriting
            if "sheet" in inp:
                if chara.lower() in skills_jp['index']['name']:
                    sheet_data = skills_jp['data'][skills_jp['index']['name'].index(chara.lower())]
                    
                    if sheet_data['skills']:    temp['skills'] =        [{"name":skill['name'], "text":skill['text']} for skill in sheet_data['skills']]
                    if sheet_data['nation']:    temp['faction_jp'] =    sheet_data['nation']
                    if sheet_data['trait']:     temp['traits'] =        [{"name":x, "text":None} for x in sheet_data['trait']]
                    if sheet_data['nation_en']: temp['faction'] =       sheet_data['nation_en']
                    if sheet_data['prefix']:    temp['prefix'] =        sheet_data['prefix']
                    temp['on_sheet'] =      True
                else:
                    temp['on_sheet'] =      False

            # write basic data from master index            
            sid = index['en'].index(chara)
            temp['rarity'] = index['rarity'][sid]
            temp['img_sq'] = index['portrait_square'][sid]
            temp['hull_code'] = index['class'][sid]
            temp['en'] = index['en'][sid]
            temp['jp'] = index['jp'][sid]
            temp['dname'] = index['display_name'][sid]
            temp['ship_class'] = self.config['ship_class'][temp['hull_code']]
            temp['wiki'] = {"url": f"https://blueoath.miraheze.org/wiki/{'_'.join(chara.split(' '))}", "active":False}
            temp['tags'] = ship_tags.get("".join(temp['en'].split()), [])
            # write preliminary
            with open(os.path.join(dir_path, f"blueoath/data/{''.join(chara.split(' '))}.json"), "w+") as sdf:
                sdf.write(json.dumps(temp, indent=4))

            skip = False
            while True:
                params = {
                    "action":           "parse",
                    "page":             chara,
                    "prop":             "text",
                    "formatversion":    "2",
                    "format":           "json"
                }
                r = s.get(url=self.index_url, params=params)

                if r.status_code != 200:
                    await self.logger.send(self.name, f"failed to fetch, `{r.status_code}`")
                    await channel.send(f"failed to fetch, `{r.status_code}`")
                    #continue
                    skip = True
                    break

                data = r.json()
                if data.get("error", None) != None:
                    if data['error']['code'] == 'missingtitle':
                        j += 1
                        #await msg.edit(content=msg.content+"page does not exist")
                    else:
                        k +=1
                        await self.logger.send(self.name, data['error'])
                        await channel.send(f"Failed to fetch `{chara}`"+self.client.emotes['sarens'])
                    #continue
                    skip = True
                    break

                html = data['parse']['text']
                soup = BeautifulSoup(html, 'html.parser')

                # check if redirect
                redirect = soup.find_all(class_="redirectText")
                if redirect:
                    chara = redirect[0].li.a['title']
                    continue
                else:
                    break
            
            if skip: continue
            tables = soup.find_all("table")
            
            if len(tables) == 4: #FIXME
                temp = self.read_stats_table(tables[0], temp)
                temp = self.read_skills_table(tables[1], temp)
                temp = self.read_traits_table(tables[2], temp)
                temp = self.read_lb_table(tables[3], temp)
            temp = self.read_gallery(soup.find_all("div", class_="tabs tabs-tabbox"), temp)
            temp['wiki']['active'] = True

            with open(os.path.join(dir_path, f"blueoath/data/{''.join(temp['en'].lower().split(' '))}.json"), "w+") as sdf:
                sdf.write(json.dumps(temp, indent=4))
        
        await channel.send(f"Update finished with `{i+1-j-k}` successful and `{k}({j})` failed(page missing)")
            
    def read_stats_table(self, table, data):
        table_body = table.tbody.find_all("tr")
        temp_stats = {}

        # GENERAL STATS
        general_contents = table_body[:8]
        # name, class, faction
        #data['name'] =          general_contents[0].th.string
        temp =                  general_contents[1].find_all("td")
        data['ship_class'] =    temp[0].string
        data['faction'] =       temp[1].string
        
        # portrait halfbody
        data['img_rec'] =       self.get_img_link(temp[2].div.a.img['src'])

        # stats - hp/armour/trpdef
        stats = {}
        temp =                  general_contents[4].find_all("td")
        stats['hp'] =           f"{temp[1].string if temp[1].string != '✕' else '??'}({temp[2].string if temp[2].string != '✕' else '??'})"
        stats['armour'] =       f"{temp[4].string if temp[4].string != '✕' else '??'}({temp[5].string if temp[5].string!= '✕' else '??'})"
        stats['trpdef'] =       f"{temp[7].string if temp[7].string != '✕' else '??'}({temp[8].string if temp[8].string != '✕' else '??'})"
        
        # stats aa/spd/fp
        temp = general_contents[5].find_all("td")
        stats['aa'] =           f"{temp[1].string if temp[1].string != '✕' else '??'}({temp[2].string if temp[2].string != '✕' else '??'})"
        stats['spd'] =          f"{temp[4].string if temp[4].string != '✕' else '??'}"
        stats['fp'] =           f"{temp[6].string if temp[6].string != '✕' else '??'}({temp[7].string if temp[7].string != '✕' else '??'})"

        temp_stats['general'] = stats

        # SPECICAL
        special_contents = table_body[6:-3]
        while True:
            if len(special_contents) == 0:
                break
            # try to get special category
            category = special_contents.pop(0).th.string
            stats = {}

            if "Aviation" in category:
                ava_spec =          special_contents[:3]
                special_contents =  special_contents[3:]

                # stats(cv) asp/ap/range
                temp = ava_spec[0].find_all("td")
                stats["asp"] =      f"{temp[1].string if temp[1].string != '✕' else '??'}({temp[2].string if temp[2].string != '✕' else '??'})"
                stats["ap"] =       f"{temp[4].string if temp[4].string != '✕' else '??'}({temp[5].string if temp[5].string!= '✕' else '??'})"
                stats["rng"] =      temp[7].string

                # stats(cv) db/ap
                temp = ava_spec[1].find_all("td")
                stats["db"] =       temp[1].string
                stats["ft"] =       temp[3].string

                # stats(cv) tb/rld
                temp = ava_spec[2].find_all("td")
                stats["tb"] =       temp[1].string
                stats["rld"] =      temp[3].string

                temp_stats['aviation'] = stats

            elif "Shelling" in category:
                shell_spec = special_contents.pop(0)

                # stats(sh) scd/rld/range
                temp = shell_spec.find_all("td")
                stats["scd"] =      f"{temp[1].string if temp[1].string != '✕' else '??'}({temp[2].string if temp[2].string != '✕' else '??'})"
                stats["rld"] =      temp[4].string
                stats["rng"] =    temp[6].string

                temp_stats['shelling'] = stats
            
            elif "Torpedo" in category:
                torp_spec = special_contents.pop(0)

                # stats(tp) trp/stk/range
                temp = torp_spec.find_all("td")
                stats["trp"] =      f"{temp[1].string if temp[1].string != '✕' else '???'}({temp[2].string if temp[2].string != '✕' else '???'})"
                stats["stk"] =      temp[4].string
                stats["rng"] =    temp[6].string

                temp_stats['torpedo'] = stats

        data['stats'] = temp_stats

        # MISC
        misc_contents = table_body[-3:]
        # gacha/comment/va
        data["acquisition"] =   misc_contents[0].th.string.split(":")[-1].strip() if misc_contents[0].th.string != None else "N/A"
        data["comment"] =       misc_contents[1].td.string
        data["VA"] =            misc_contents[2].td.string

        return data

    def fix_skill_str(self, string):
        string = re.sub(r'\\n+',' ',string)
        return [x.strip() for x in re.sub(r'\A\d\.\s*|(\.\d\.\s*)+|\s\d\.', '+++', string).split('+++') if x]

    def read_skills_table(self, table, data):
        table_body = table.tbody.find_all("tr")

        # Class Skill
        category = table_body.pop(0)
        temp = [
            {
                "name": "Class Skill", 
                "text": self.get_str(str(category.td.p))
            }
        ]

        # SKILLS
        for category in table_body:
            skill = {}
            contents = category.find_all("td")
            try:
                skill['name'] = self.get_str("{} ({})".format(*str(contents[0]).split("<br/>")[-2:]))
            except:
                skill['name'] = self.get_str("\n".join(str(contents[0]).split("<br/>")[-2:]))
            skill['name'] = re.sub(r'<.*>', '', skill['name'])
            skill['text'] = self.fix_skill_str(contents[1].text)
            temp.append(skill)

        data['skills'] = temp
        return data
        
    def read_traits_table(self, table, data):
        table_body = table.tbody.find_all("tr")
        acc = []
        for trait in table_body:
            temp = {}
            contents = trait.find_all("td")
            temp['name'] =  contents[0].string
            temp['text'] =  contents[1].text
            acc.append(temp)
        data['traits'] = acc
        return data

    def read_lb_table(self, table, data):
        table_body = table.tbody.find_all("tr")    
        temp = []
        for lb in table_body:
            temp.append(self.get_str(str(lb.td)) if str(lb.td) != "<td></td>" else "No effect")
        data['lb'] = temp
        return data

    def read_gallery(self, tabbox, data):
        if not tabbox:
            data['gallery'] = []
            return data
        div_contents = tabbox[-1].div.find_all("div")
        temp = []
        for dv in div_contents:
            try:
                temp.append(self.get_img_link(dv.a.img['src']))
            except:
                continue
        data['gallery'] = temp
        return data

    # sheet stuff    
    def _connect(self):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(os.path.join(self.client.dir, 'commands/_private/credentials.json'), SCOPES)
                creds = flow.run_local_server(port=58325)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('sheets', 'v4', credentials=creds)

    @bo.command(aliases=['reload_sheets', 'rs'])
    async def reload_sheet(self, ctx, modules, **kwargs):
        channel = ctx.channel
        author = ctx.message.author
    
        # check
        if not self.config['command_status']['reload_sheet']:
            raise commands.DisabledCommand
        elif not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        elif not modules in list(self.config['data'].keys()):
            await channel.send("Invalid section keyword "+self.client.emotes['ames'])
            return

        # call
        service = self._connect()
        sheet = service.spreadsheets()
        results = sheet.values().get(spreadsheetId=self.config['sheet_id'], range=f"{self.config['data'][modules]['sheet_name']}!{self.config['data'][modules]['range']}").execute()
        values = results.get('values', [])

        if not values:
            await channel.send("Returned empty! "+self.client.emotes['ames'])
            await self.logger.send(self.name, "Empty value returned")
            return
        elif modules in ["skills_jp", "skills_cn"]:
            msg = await channel.send(f"Reloading `{modules}`...")
            try:
                await self.reload_skills(values, modules, channel)
            except Exception as e:
                await self.logger.send(self.name, e)
                await msg.edit(content=msg.content+" failed")
                return
            else:
                await msg.edit(content=msg.content+" success")
                  
    async def reload_skills(self, values, mode, channel):
        txt = "Fetching data..."
        msg = await channel.send(txt)
        s = requests.Session()
        idv, namev, snamev, datav, skillsv = [], [], [], [], []
        temp = {}
        end = False
        for i, row in enumerate(values):
            #if (i+1)%40==0: await msg.edit(content=msg.content+".")
            # empty row separator
            skill = {}
            if not row:
                if not end:
                    temp['skills'] = skillsv if skillsv else None
                    datav.append(temp)
                    temp = {}
                    skillsv = []
                    end = True
                    continue
                else:
                    try:
                        if values[i+1][0].isnumeric() or values[i+2][0].isnumeric():
                            continue
                    except:
                        pass
                    else:
                        break
            # if first value is an id - new ship
            elif row[0].isnumeric():
                end = False
                temp['id'] =    row[0]
                #print(row)

                # possibility of cell not containing all data
                length = len(row) #[id, faction, img, ship name, class, rarity, skill1, trait] = max 8 min 5

                # possibility that cell only contains english and not in expected format
                try:
                    temp['nation_en'], temp['nation'] = row[1].split('\n')
                except:
                    temp['nation_en'], temp['nation'] = row[1], None

                #temp['img'] =   row[2]
                #temp['prefix'], _, name = row[3].partition(" ")
                parts = row[3].partition(" ")
                if parts[0].isupper():
                    temp['prefix'] = parts[0]
                    name = parts[-1]
                else:
                    temp['prefix'] = None
                    name = parts[0]

                temp['name'], temp['sname'] = self.clean_name(name)
                #print(temp['name'], temp['sname'])
                #await msg.edit(content=txt+f" `{temp['name']}`")
                #temp['img'] = self.get_image(temp['sname'].replace(" ",""), s)

                temp['class'] = row[4]
                temp['rarity'] =row[5]
                if length > 6:
                    if row[6]:
                        skill['name'], _, skill['text'] = row[6].partition("\n")
                        skill['text'] = self.fix_skill_str(skill['text'])
                        skillsv.append(skill)
                
                if length > 7:
                    temp['trait'] = row[7].split("\n")
                else:
                    temp['trait'] = []

                idv.append(temp['id'])
                namev.append(temp['sname'].lower())
                #snamev.append(temp['sname'])
            # else its a skill continuation
            else:
                skill['name'], _, skill['text'] = row[6].partition("\n")
                skill['text'] = self.fix_skill_str(skill['text'])
                skillsv.append(skill)
        
        # write
        temp['skills'] = skillsv if skillsv else None
        datav.append(temp)
        with open(os.path.join(dir_path, self.config['sheet_data_path']), "w+") as jf:
            skill_json = {
                "index": {
                    "id": idv,
                    "name": namev
                },
                "data": datav
            }
            jf.write(json.dumps(skill_json, indent=4))
        
        await msg.edit(content="Reload complete")

    def process_request(self, character):
        return self.alias.get(character, character).lower()

    def validate_entry(self, character):
        with open(os.path.join(dir_path, self.config['index_path'])) as idf:
            index = json.load(idf)
        try:
            ind = index['search_name'].index(character)
        except:
            return False, None
        else:
            return True, {"en":index['en'][ind], "jp": index['jp'][ind], "sname": character, "dname": index["display_name"][ind], "img": index['portrait_square'][ind]}

    @bo.group(invoke_without_command=True, case_insensitive=True, pass_context=True)
    async def alias(self, ctx, *request):
        channel = ctx.message.channel
        if not self.config['command_status']['alias']:
            raise commands.DisabledCommand
        
        request = " ".join(request)
        if ctx.invoked_subcommand is None:
            if not request:
                await self.display_aliases(ctx)
            else:
                await self.search(ctx, request)
    
    async def display_aliases(self, ctx):
        author = ctx.message.author
        master =    []
        local =     []

        # sort the aliases by master/local
        for a, o in list(self.alias.items()):
            if not self.alias_master.get(a, None) is None:
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
        embed.set_footer(text="BO Alias | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
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
        if request.lower() in list(self.alias.keys()):
            await channel.send(
                f"Alias `{request.lower()}` -> `{self.alias[request.lower()]}` [{'master' if request.lower() in list(self.alias_master) else 'local'}]"
            )
        elif request.lower() in list(self.alias.values()):
            master =    []
            local =     []

            for a, o in list(self.alias.items()):
                if o == request.lower():
                    if a in list(self.alias_master.keys()):
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
            embed.set_footer(text="BO Alias | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
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
    async def add(self, ctx, *request):
        channel = ctx.channel
        
        if not self.config['command_status']['alias']:
            raise commands.DisabledCommand
        
        # checks
        try:
            alias, character = " ".join(request).split("->")
            alias, character = alias.lower().strip(), character.lower().strip()
        except Exception as e:
            await self.logger.send(self.name, "alias add", e)
            await channel.send("Invalid input format")
            return

        if alias in list(self.alias_master.keys()):
            await channel.send(f"`{alias}` -> `{self.alias_master[alias]}` is already an entry in the master alias record")
            return
        elif alias in list(self.alias.keys()):
            await channel.send(f"`{alias}` -> `{self.alias[alias]}` already exists")
            return
        
        # clean input
        for token in self.config['illegal_tokens']:
            alias = alias.strip(token)
        
        # check character
        # case uniformity
        #character = [i.lower() for i in character]

        # preprocess the command to find what out what the request is
        _character = self.process_request(character)
        # request here should be a string

        # validate request
        search_sucess, _character = self.validate_entry(_character)
        if not search_sucess:
            await channel.send(f"No character entry matching `{character}`")
            return 
        character = _character
        self.alias_local[alias] =       character['sname']
        self.alias =                    self.alias_master.copy()
        self.alias.update(self.alias_local)

        with open(os.path.join(dir_path, self.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alias_local, indent=4))
        
        await channel.send(f"Successfully added `{alias}` -> `{character['dname']}`")

    @alias.command()
    async def edit(self, ctx, *request):
        channel = ctx.channel
        
        if not self.config['command_status']['alias']:
            raise commands.DisabledCommand
        
        # checks
        try:
            alias, character = " ".join(request).split("->")
            alias, character = alias.lower().strip(), character.lower().strip()
        except Exception as e:
            await self.logger.send(self.name, "alias add", e)
            await channel.send("Invalid input format")
            return

        if alias in list(self.alias_master.keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record - You may not edit a master record")
            return
        elif not alias in list(self.alias.keys()):
            await channel.send(f"`{alias}` does not exist")
            return
        
        # clean input
        for token in self.config['illegal_tokens']:
            alias = alias.strip(token)
        
        # check character
        # case uniformity
        #character = [i.lower() for i in character]

        # preprocess the command to find what out what the request is
        _character = self.process_request(character)
        # request here should be a string

        # validate request
        search_sucess, _character = self.validate_entry(_character)
        if not search_sucess:
            await channel.send(f"No character entry matching `{character}`")
            return 
        character = _character
        self.alias_local[alias] =       character['sname']
        self.alias =                    self.alias_master.copy()
        self.alias.update(self.alias_local)

        with open(os.path.join(dir_path, self.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alias_local, indent=4))
        
        await channel.send(f"Successfully edited `{alias}` -> `{character['en']}`")

    @alias.command()
    async def delete(self, ctx, *alias):
        channel = ctx.channel
        
        if not self.client.command_status['alias'] == 1:
            raise commands.DisabledCommand
        elif not alias:
            return
        
        # checks
        alias = " ".join(alias).lower()

        if alias in list(self.alias_master.keys()):
            await channel.send(f"`{alias}` is already an entry in the master alias record - You may not delete a master record")
            return
        elif not alias in list(self.alias.keys()):
            await channel.send(f"`{alias}` does not exist")
            return
        
        self.alias_local.pop(alias)
        self.alias =       self.alias_master.copy()
        self.alias.update(self.alias_local)

        with open(os.path.join(dir_path, self.config["alias_local_path"]), 'w+') as alf:
            alf.write(json.dumps(self.alias_local, indent=4))
        
        await channel.send(f"Successfully deleted `{alias}`")

    @bo.command(aliases=['s','c','stats','st','gallery','pic', 'g', 'card', 'cd'])
    async def ship(self, ctx, *request):
        channel = ctx.channel
        author = ctx.message.author
        if not self.config['command_status']['ship']:
            raise commands.DisabledCommand
        elif not request:
            return
        
        # clean request
        request = " ".join(request).lower()

        # find mode
        call = ctx.invoked_with
        if call in ['s', 'c', "ship"]:
            mode = 'ship'
        elif call in ['stats', 'st']:
            mode = 'stats'
        elif call in ['gallery', 'pic', 'g']:
            mode = 'gallery'
        
        # validate request
        _character = self.process_request(request)
        search_success, _character = self.validate_entry(_character)

        if not search_success:
            await channel.send(f"Failed to find character `{request}`.\nIf its a nickname consider adding it as an alias via `.bo alias add [alias] -> [actual ship name]`")
            return
        else:
            # grab data
            if not os.path.exists(os.path.join(dir_path, self.config['ship_path'], "".join(_character['en'].split(" "))+".json")):
                await channel.send(f"No local data available for vessel {_character['dname']}")
                return
            else:
                with open(os.path.join(dir_path, self.config['ship_path'], "".join(_character['en'].split(" "))+".json")) as raw:
                    data = json.load(raw)
        
        emotes = ["\U0001f6a2", "\U0001f4f0", "\U0001f5bc", '⬅','➡']

        ship_controller = self.ship_page_controller(data, mode, self)
        
        page = await channel.send(embed=ship_controller.first_page())
        self.active_embeds[str(page.id)] = author.id # add to to persist
        for react in emotes:
            await page.add_reaction(react)
        
        def author_check(reaction, user):
            return str(user.id) == str(author.id) and str(reaction.emoji) in emotes+['⏱️'] and str(reaction.message.id) == str(page.id)
        
        persist=False
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=90.0, check=author_check)
            except:
                if not persist:
                    await page.edit(content=f"Embed for `{_character['dname']}` has expired "+self.client.emotes['ames'], embed=None)
                await page.clear_reactions()
                self.active_embeds.pop(str(page.id), None) # remove persistence
                return
            else:
                emote_check = str(reaction)
                if emote_check in emotes:
                    await reaction.message.remove_reaction(reaction.emoji, user)
                    if emote_check == "\U0001f6a2":
                        await reaction.message.edit(embed=ship_controller.toggle("ship"))
                    elif emote_check == "\U0001f4f0":
                        await reaction.message.edit(embed=ship_controller.toggle("stats"))
                    elif emote_check == "\U0001f5bc":
                        await reaction.message.edit(embed=ship_controller.toggle("gallery"))
                    elif emote_check == '⬅':
                        await reaction.message.edit(embed=ship_controller.turn_page('l'))
                    elif emote_check == '➡':
                        await reaction.message.edit(embed=ship_controller.turn_page('r'))
                elif emote_check == '⏱️': # stopwatch
                    persist = True
    
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
            await message.remove_reaction('⏹️', user) # stop_button
            return
        elif not message.author is guild.me:
            return
        elif not message.embeds:
            return
        elif not message.embeds[0].author.name == "Asahi's Report":
            return
        else:
            await message.clear_reactions()
            await message.edit(content="This embed has been deleted "+self.client.emotes['ames'], embed=None)
            self.active_embeds.pop(str(message.id),None)
            
    def make_ship_embed(self, data, sections):
        sections[sections.index(":ship: Ship")] = ":ship: **[Ship]**"

        title = f"{data['dname']}\n{data['jp']}" if data['prefix'] == None else f"{data['prefix']} {data['dname']}\n{data['jp']}"

        embed = discord.Embed(
            title=title,
            description=data['comment'] if data['comment'] != None else "No description... yet",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        if data['wiki']['active']:
            embed.url = data['wiki']['url']
        embed.set_author(name="Asahi's Report")
        embed.set_footer(text="BO Ship | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        if data['img_sq']:
            embed.set_thumbnail(url=data['img_sq'])

        embed.add_field(
            name="> **Section**",
            value=" - ".join(sections),
            inline=False
        )

        embed.add_field(
            name="> **Class**",
            value=f"{data['ship_class']} ({data['hull_code']})",
            inline=False
        )
        embed.add_field(
            name="> **Affiliation**",
            value=f"{data['faction']} ({data['faction_jp'] if data['faction_jp'] else 'N/A'})"
        )
        embed.add_field(
            name="> **Acquisition**",
            value=f"{data['acquisition'] if data['acquisition'] else 'TBC'}"
        )
        embed.add_field(
            name="> **Rarity**",
            value=data['rarity'] if data['rarity'] else "No data"
        )

        if data['skills']:
            if data['skills'][0]['name'] == "Class Skill":
                embed.add_field(
                    name="> **Class Skill**",
                    value=data['skills'].pop(0)['text'],
                    inline=False
                )

            for i, skill in enumerate(data['skills']):
                embed.add_field(
                    name=f"> **Skill {i+1}**",
                    value="\n".join(skill['name'].split("\n")),
                    inline=False
                )
                embed.add_field(
                    name="Description",
                    value="-"+"\n-".join(skill['text']),
                    inline=False
                )
        else:
            embed.add_field(
                name="> **Skill Data**",
                value="Data Not Available",
                inline=False
            )
        
        embed.add_field(
            name="> **Voice Actress**",
            value=f"{data['VA'] if data['VA'] != None else 'TBC'}",
            inline=False
        )
        falias = [key for key, value in list(self.alias.items()) if value.lower() == data['en'].lower()]
        embed.add_field(
            name="> **Aliases**",
            value=", ".join(falias) if falias else "None",
            inline=False
        )

        embed.add_field(
            name="> **Tags**",
            value=", ".join(data['tags']) if data.get("tags",None) else "None"
        )

        return embed

    def make_stats_embed(self, data, sections):
        sections[sections.index(":newspaper: Stats")] = ":newspaper: **[Stats]**"

        title = f"{data['dname']}\n{data['jp']}" if data['prefix'] == None else f"{data['prefix']} {data['dname']}\n{data['jp']}"

        embed = discord.Embed(
            title=title,
            description=f"{data['dname']}\'s detailed statistics. `this page is a WIP`.",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        if data['wiki']['active']:
            embed.url = data['wiki']['url']
        embed.set_author(name="Asahi's Report")
        embed.set_footer(text="BO Stats | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        if data['img_sq']: 
            embed.set_thumbnail(url=data['img_sq'])

        embed.add_field(
            name="> **Section**",
            value=" - ".join(sections),
            inline=False
        )

        if not data['stats']:
            embed.add_field(
                name="> **Stats**",
                value="No Data Available",
                inline=False
            )
        else:
            for category, stats in list(data['stats'].items()):
                if category == "general":
                    embed.add_field(
                        name=SPACE,
                        value="> **General Stats**",
                        inline=False
                    )
                elif category == "aviation":
                    embed.add_field(
                        name=SPACE,
                        value="> **Aviation Stats**",
                        inline=False
                    )
                elif category == "shelling":
                    embed.add_field(
                        name=SPACE,
                        value="> **Shelling Stats**",
                        inline=False
                    )
                elif category == "torpedo":
                    embed.add_field(
                        name=SPACE,
                        value="> **Torpedo Stats**",
                        inline=False
                    )
                #for key, val in list(stats.items()):
                #    embed.add_field(
                #        name=self.config["stats_abbrev"][key],
                #        value=val
                #    )
                embed.add_field(
                    name="Stats(max)",
                    value="\n".join([self.config["stats_abbrev"][x] for x in list(stats.keys())])
                )
                embed.add_field(
                    name=SPACE,
                    value="\n".join(list(stats.values()))
                )
            
        embed.add_field(
            name=SPACE,
            value="> **Trait Data**",
            inline=False
        )
        if not data['traits']:
            embed.add_field(
                name="Trait Data",
                value="Not Available",
                inline=False
            )
        else:
            for i, trait in enumerate(data['traits']):
                embed.add_field(
                    name=f"Trait {i+1} - {trait['name']}",
                    value=trait['text'] if trait['text'] != None else "No data available",
                    inline=False
                )

        embed.add_field(
            name=SPACE,
            value="> **Limit Break Data**",
            inline=False
        )

        if not data['lb']:
            embed.add_field(
                name="LB Data",
                value="Not Available"
            )
        else:
            for i, lb in enumerate(data['lb']):
                embed.add_field(
                    name=f"{i+1}\⭐",
                    value=lb,
                    inline=False
                )

        return embed

    def make_gallery_embed(self, data, sections):
        #print(data['img_sq'])
        #print(data['gallery'])
        
        def make_indiv_gallery(data, sections):
            sections[sections.index(":frame_photo: Gallery")] = ":frame_photo: **[Gallery]**"

            title = f"{data['dname']}\n{data['jp']}" if data['prefix'] == None else f"{data['prefix']} {data['dname']}\n{data['jp']}"

            embed = discord.Embed(
                title=title,
                colour=self.colour,
                timestamp=datetime.datetime.utcnow()
            )
            if data['wiki']['active']:
                embed.url = data['wiki']['url']
            embed.set_author(name="Asahi's Report")
            embed.set_footer(text="BO Gallery | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
            if data['img_sq']: 
                embed.set_thumbnail(url=data['img_sq'])

            embed.add_field(
                name="> **Section**",
                value=" - ".join(sections),
                inline=False
            )
            return embed
        if not data['gallery']:
            embed = make_indiv_gallery(data,sections.copy())
            embed.add_field(
                name="No pictures",
                value=f"{data['dname']}\'s gallery is currently empty"
            )
            return [embed]
        else:
            temp = []
            total = len(data['gallery'])
            for i, link in enumerate(data['gallery']):
                embed = make_indiv_gallery(data,sections.copy())
                embed.add_field(
                    name=SPACE,
                    value=f"Image {i+1} of {total}",
                    inline=False
                )
                embed.set_image(url=link)
                temp.append(embed)
            
            return temp

    class ship_page_controller():
        def __init__(self, data, mode, cog):
            self.cog = cog
            self.mode = mode
            self.data = data
            self.sections = [":ship: Ship", ":newspaper: Stats", ":frame_photo: Gallery"]

            self.ship_embeds = []
            self.stats_embeds = []
            self.gallery_embeds = []

            self.current_page = None

            self._make_pages()
        
        def _make_pages(self):
            self.ship_embeds.append(self.cog.make_ship_embed(self.data, self.sections.copy()))
            self.stats_embeds.append(self.cog.make_stats_embed(self.data, self.sections.copy()))
            self.gallery_embeds = self.cog.make_gallery_embed(self.data, self.sections.copy())
        
        def first_page(self, mode=None):
            if mode == None:
                mode = self.mode

            if mode == 'ship':
                self.current_page = mode
                return self.ship_embeds[0]
            elif mode == 'stats':
                self.current_page = mode
                return self.stats_embeds[0]
            elif mode == 'gallery':
                self.current_page = mode
                return self.gallery_embeds[0]
        
        def toggle(self, mode):
            return self.first_page(mode)
        
        def turn_page(self, mode):
            if self.current_page == 'ship':
                if mode == 'l':
                    self.ship_embeds = [self.ship_embeds[-1]] + self.ship_embeds[:-1]
                else:
                    self.ship_embeds = self.ship_embeds[1:] + [self.ship_embeds[0]]
                return self.ship_embeds[0]

            elif self.current_page == 'stats':
                if mode == 'l':
                    self.stats_embeds = [self.stats_embeds[-1]] + self.stats_embeds[:-1]
                else:
                    self.stats_embeds = self.stats_embeds[1:] + [self.stats_embeds[0]]
                return self.stats_embeds[0]

            elif self.current_page == 'gallery':
                if mode == 'l':
                    self.gallery_embeds = [self.gallery_embeds[-1]] + self.gallery_embeds[:-1]
                else:
                    self.gallery_embeds = self.gallery_embeds[1:] + [self.gallery_embeds[0]]
                return self.gallery_embeds[0]

    def filter_commands(self, target, perm=False):
        temp = [item for item in list(self.help_text.values()) if target in item['flags'] and ((not item['hidden'] and not "restricted" in item['flags']) or perm)]
        temp.sort(key=lambda x: x['usage'])
        return temp if len(temp)>0 else ["empty"]

    def make_help_text(self, data):
        txt = []
        keys = ['usage', 'aliases', 'help']
        for cmd in data:
            temp = []
            if cmd == "empty":
                return ["No eligible commands matched input flag"]
            for key in keys:
                if cmd[key] != None:
                    #print(cmd[key])
                    if key == 'aliases':
                        temp.append(f"[Aliases]: {' '.join(cmd[key])}")
                    else:
                        temp.append(cmd[key])
            #print(temp)
            txt.append("\n".join(temp))
        txt.sort(key=lambda x: x[1])

        return txt

    async def process_options(self, channel, options, author):
        option = options[0]
        command = self.help_text.get(option, None)
        if command != None:
            if self.client._check_author(author):
                await channel.send(embed=self.make_extended_help(command))
            elif "admin" in command['flags'] and self.client._check_author(author, "admin"):
                await channel.send(embed=self.make_extended_help(command))
            elif not  "admin" in command['flags']:
                await channel.send(embed=self.make_extended_help(command))
            else:
                await channel.send("Command is restricted "+self.client.emotes['ames'])

    @bo.group(invoke_without_command=True)
    async def help(self, ctx, *options):
        channel=ctx.channel
        author=ctx.message.author
        if not self.config['command_status']['help']:
            raise commands.DisabledCommand
        
        if ctx.invoked_subcommand is None:
            perm = self.client._check_author(ctx.message.author)
            if len(options) == 0:
                data = self.filter_commands("normal", perm)
            else:
                option = options[0]
                if option in ["normal", "shitpost", "restricted", "core", "admin", "_update"]:
                    data = self.filter_commands(option, self.client._check_author(ctx.message.author, option))
                else:
                    await self.process_options(channel, options, author)
                    return
            
            help_page_controller = self.client.page_controller(self.client, self.make_help_embed, data, 12, True)
            page = await channel.send(embed=help_page_controller.start())
            for arrow in help_page_controller.arrows:
                await page.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and str(reaction.emoji) in help_page_controller.arrows and str(reaction.message.id) == str(page.id)
            
            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
                except asyncio.TimeoutError:
                    await page.clear_reactions()
                    return
                else:
                    emote_check = str(reaction.emoji)
                    await reaction.message.remove_reaction(reaction.emoji, user)
                    if emote_check in help_page_controller.arrows:
                        if emote_check == help_page_controller.arrows[0]:
                            mode = 'l'
                        else:
                            mode = 'r'     
                        await reaction.message.edit(embed=help_page_controller.flip(mode))
    
    def make_help_embed(self, data, index):
        embed = discord.Embed(
            title=f"Help (page {index[0]} of {index[1]})",
            description="Command documentation and usage.\nMost commands have more detailed instructions accessible via `.bo help [full_command_name]`(no aliases accepted).\nCommands are displayed in `groups` that are fetched via `.bo help [group_name]` defaulting to `.bo help normal`. Current groups are:\n{}.\n```css\n{}```".format(" ".join([f"`{i}`" for i in self.command_tags]),"\n\n".join(self.make_help_text(data))),
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="BO Help | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        return embed
    
    def make_extended_help(self, command):
        embed=discord.Embed(
            title="Extended Command Documentation",
            timestamp=datetime.datetime.utcnow(),
            color=self.colour
        )
        embed.set_footer(text="BO EX Help | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="> **Usage**",
            value=f"`{command['usage']}`",
            inline=False
        )
        embed.add_field(
            name="Aliases",
            value="None" if command['aliases'] == None else ", ".join(command['aliases']),
            inline=True
        )
        embed.add_field(
            name="Flags",
            value="".join([f"[{flag}]" for flag in command['flags']]),
            inline=True
        )
        #embed.add_field(
        #    name="Hidden",
        #    value="Yes" if command['hidden'] else "No",
        #    inline=True
        #)
        embed.add_field(
            name="Subcommands",
            value="None" if command['subcmd'] == None else ", ".join(command['subcmd']),
            inline=True
        )
        embed.add_field(
            name="> **Help** ",
            value=command['help'],
            inline=False
        )
        embed.add_field(
            name="> **Extended Help**",
            value="Nothing 'ere" if command['help_ex'] == None else command['help_ex']
        )
        return embed

    @help.command(aliases=['d'])
    async def definitions(self,ctx,*option):
        channel=ctx.message.channel
        author=ctx.message.author
        if not option:
            await channel.send(f"Tags are split into {len(list(self.tags.keys()))} "\
                "sections. The syntax is `.bo help d [section]`.\nUse one of the following sections to navigation between groups of tags: "\
                f"{' '.join([f'`{section}`' for section in self.tags.keys()])}")
            return
        option = option[0]
        if not option in list(self.tags.keys()):
            await channel.send(f"Invalid tag option {option}")

        data = list(self.tags[option].items())
        data.sort(key=lambda x: x[0])
        tag_page_controller = self.client.page_controller(self.client, self.bo_make_tag_embed, data, 10, True)

        page = await channel.send(embed=tag_page_controller.start())
        for arrow in tag_page_controller.arrows:
            await page.add_reaction(arrow)
        
        def author_check(reaction, user):
            return str(user.id) == str(author.id) and str(reaction.emoji) in tag_page_controller.arrows and str(reaction.message.id) == str(page.id)
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
            except asyncio.TimeoutError:
                await page.add_reaction('\U0001f6d1')
                return
            else:
                emote_check = str(reaction.emoji)
                await reaction.message.remove_reaction(reaction.emoji, user)
                if emote_check in tag_page_controller.arrows:
                    if emote_check == tag_page_controller.arrows[0]:
                        mode = 'l'
                    else:
                        mode = 'r'     
                    await reaction.message.edit(embed=tag_page_controller.flip(mode))
    
    def make_tag_text(self, data):
        #temp = [f"# {key}\n\t{value}" for key, value in data]
        temp = [f"{value}\n```md\n# {key}```" for key, value in data]
        temp.sort(key=lambda x: x[2])
        return temp
    
    def bo_make_tag_embed(self, data, index):
        embed = discord.Embed(
            title=f"Tag Definitions (page {index[0]} of {index[1]})",
            description="A list of tag definitnions that are used in `.bo tag`.\n{}".format("\n".join(self.make_tag_text(data))),
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Tag Definitions | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        return embed

    @bo.command(aliases=['ss'])
    async def ship_status(self, ctx):
        channel = ctx.channel
        author = ctx.message.author
        if not self.config['command_status']['ship_status']:
            raise commands.DisabledCommand

        with open(os.path.join(dir_path, self.config['index_path'])) as idf:
            index = json.load(idf)

        data = []
        for ship, dname in zip(index['en'],index['display_name']):
            with open(os.path.join(dir_path, self.config['ship_path'], f"{''.join(ship.split(' '))}.json")) as sh:
                ship = json.load(sh)
            data.append(
                (
                    dname,
                    f"[{dname}]({ship['wiki']['url']})" if ship['wiki']['active'] else dname,
                    ship['wiki']['active'],
                    ship['on_sheet'],
                    "".join(ship['en'].split(" ")).lower()
                )
            )

        data.sort(key=lambda x: x[0])

        ship_status_controller = self.client.page_controller(self.client, self.make_ship_status_embed, data, 45, True)
        page = await channel.send(embed=ship_status_controller.start())
        for arrow in ship_status_controller.arrows:
            await page.add_reaction(arrow)
        
        def author_check(reaction, user):
            return str(user.id) == str(author.id) and str(reaction.emoji) in ship_status_controller.arrows and str(reaction.message.id) == str(page.id)
        
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
            except asyncio.TimeoutError:
                await page.add_reaction('\U0001f6d1')
                return
            else:
                emote_check = str(reaction.emoji)
                await reaction.message.remove_reaction(reaction.emoji, user)
                if emote_check in ship_status_controller.arrows:
                    if emote_check == ship_status_controller.arrows[0]:
                        mode = 'l'
                    else:
                        mode = 'r'     
                    await reaction.message.edit(embed=ship_status_controller.flip(mode))

    def make_ship_status_embed(self, data, index):
        embed = discord.Embed(
            title=f"Data Availability (Page {index[0]} of {index[1]})",
            description=f":green_circle: Available \n:black_circle: Not available",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Asahi's Report")
        embed.set_footer(text="Data | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        """
        embed.add_field(
            name="Senki",
            value="\n".join([f"{self.ship_pfp.get(x[-1],':grey_question:')} {x[1]}" for x in data])
        )
        embed.add_field(
            name="Wiki",
            value="\n".join([":green_circle:" if x[2] else ":black_circle:" for x in data])
        )
        embed.add_field(
            name="Spreadsheet",
            value="\n".join([":green_circle:" if x[3] else ":black_circle:" for x in data])
        )
        """
        embed.add_field(
            name=SPACE,
            value="Wiki/Sheet Availability",
            inline=False
        )
        for chunk in self.client.chunks(data, 5):
            embed.add_field(
                name=SPACE,
                value="\n".join([f"{':green_circle:' if x[2] else ':black_circle:'}{':green_circle:' if x[3] else ':black_circle:'} {self.ship_pfp.get(x[-1],':grey_question:')} {x[1]}" for x in chunk])
            )
        return embed

    @bo.group(invoke_without_command=True,
    case_insensitive=True)
    async def oil(self, ctx):
        author=ctx.message.author
        channel=ctx.message.channel
        if not self.config['command_status']['oil']:
            raise commands.DisabledCommand
        elif ctx.invoked_subcommand is None:
            guild = ctx.message.guild
            path = os.path.join(dir_path, self.config['oil_rem_path'], f"{guild.id}.json")
            if not os.path.exists(path):
                await channel.send("The daily oil reminder function have not been set on this server. See `.bo help oil` for more details.")
            else:
                with open(os.path.join(path)) as orf:
                    settings = json.load(orf)
                
                # try to read settings
                # should be of the form {"active":bool, "channel":Union(int,None), "role":Union(int,None)}
                
                # get channel
                _channel = None
                if settings['channel']:
                    _channel = guild.get_channel(settings['channel'])
                
                # get role
                role = None
                if settings['role']:
                    role = guild.get_role(settings['role'])
                
                report = [
                    f"**Status:** {'`Active`' if settings['active'] else '`Inactive`'}",
                    "**Role:** "+(f"`@{role.name}` `id={role.id}`" if role else "`No set role`"),
                    f"**Bound Channel:** `{_channel.name if _channel else 'No set channel'}`"
                ]
                await channel.send(f"The oil reminder settings are:\n> "+"\n> ".join(report))
    
    @oil.command()
    async def set(self, ctx, *options):
        author=ctx.message.author
        channel=ctx.message.channel
        guild=ctx.message.guild
        if not self.config['command_status']['oil']:
            raise commands.DisabledCommand
        elif not self.client._check_author(author,"admin"):
            await channel.send("You do not have the permission to do that "+self.client.emotes['ames'])
            return
        elif not options:
            return
        elif len(options) > 3:
            await channel.send("Too many inputs! "+self.client.emotes['ames'])
            return
        
        # set
        path = os.path.join(dir_path, self.config['oil_rem_path'], f"{guild.id}.json")
        if not os.path.exists(path):
            settings = {"active":False,"channel":None,"role":None}
        else:
            with open(os.path.join(path)) as orf:
                settings = json.load(orf)

        for option in [i.lower() for i in options]:
            txt = f"Invalid option `{option}`"
            if len(option) == 1 and option.isnumeric():
                if option == "1":
                    settings['active'] = True
                elif option == "0":
                    settings['active'] = False
                txt = f"Set active to `{option}`"

            else:
                r = re.match(r'<([^\d]{1,2})(\d*)>',option)
                if r:
                    if r.group(1) == "#": # channel
                        fchannel = guild.get_channel(int(r.group(2)))
                        if fchannel:
                            settings['channel'] = fchannel.id
                            txt = f"Set channel to `#{fchannel.name}`"

                    elif r.group(1) == "@&": # role
                        frole = guild.get_role(int(r.group(2)))
                        if frole:
                            settings['role'] = frole.id
                            txt = f"Set role to `@{frole.name}`"

            await channel.send(txt)
        
        with open(path, "w+") as orf:
            orf.write(json.dumps(settings,indent=4))
    
    @oil.command()
    async def reset(self, ctx, *options):
        author=ctx.message.author
        channel=ctx.message.channel
        guild=ctx.message.guild
        if not self.config['command_status']['oil']:
            raise commands.DisabledCommand
        elif not self.client._check_author(author,"admin"):
            await channel.send("You do not have the permission to do that "+self.client.emotes['ames'])
            return
        
        path = os.path.join(dir_path, self.config['oil_rem_path'], f"{guild.id}.json")
        if not os.path.exists(path):
            await channel.send("This guild does not have an oil reminder setting!")
            return
        else:
            with open(os.path.join(path)) as orf:
                settings = json.load(orf)

        if not options:
            with open(path, "w+") as orf:
                orf.write(json.dumps({"active":False,"channel":None,"role":None},indent=4))
            await channel.send("Reset all settings")
            return
        elif len(options) > 2:
            await channel.send("Too many inputs!")
            return

        for option in options:
            if option == "channel":
                settings['channel'] = None
                await channel.send("Reset channel")
            elif option == "role":
                settings['role'] = None
                await channel.send("Reset role")
            else:
                await channel.send(f"Invalid option `{option}`")
        
        with open(path, "w+") as orf:
            orf.write(json.dumps(settings,indent=4))

    @tasks.loop(seconds=60)
    async def check_oil(self):
        if not self.config['oil_rem']:
            return
        try:
            # prep time zone
            jp_tz = pytz.timezone('Asia/Tokyo')
            jp_now = datetime.datetime.now(jp_tz)

            # get current day
            t_fmt = "%d-%m-%Y"
            current_day = jp_now.strftime(t_fmt)

            # get reminder times relative to today by joining today's date and scheduled time
            rem_fmt = " ".join([t_fmt, self.config['oil_reminder_times']['format']])
            rem_afternoon = datetime.datetime.strptime(" ".join([current_day, self.config['oil_reminder_times']['times']['afternoon']]), rem_fmt)
            rem_night =     datetime.datetime.strptime(" ".join([current_day, self.config['oil_reminder_times']['times']['night']]), rem_fmt)

            # get current reminder task
            path = os.path.join(dir_path, self.config['oil_rem_task'])
            if os.path.exists(path):
                with open(path) as rf:
                    current_task = json.load(rf)
            else:
                current_task = {"current": "afternoon"}
            
            # see if its time to do a reminder
            if current_task['current'] == "afternoon":
                d_time = rem_afternoon - jp_now
            else:
                d_time = rem_night - jp_now
            
            #print(d_time.total_seconds())

            if d_time.total_seconds() > self.config['oil_reminder_times']['duration']: # if delta time is positive (event yet to happen) and beyond 6hrs from end time
                if d_time.total_seconds() > 2*self.config['oil_reminder_times']['duration'] and current_task['current'] == "night": # fix
                    current_task['current'] = "afternoon"
                self.save_task(current_task)
                return
            elif d_time.total_seconds() < 0: # if delta time is negative (past end time)
                #if current_task['current'] == "afternoon":
                    #current_task['current'] = "night"
                self.save_task(current_task)
                return
            
            # do reminder
            for path in glob.glob(os.path.join(dir_path, self.config['oil_rem_path'], "*.json")):
                try:
                    guild_id = path.split("\\")[-1].split(".")[0] # grab filename .../.../guild_id.json
                    if guild_id.isnumeric():
                        with open(path) as f:
                            guildf = json.load(f) # should be of the form {"active":bool, "channel":Union(int,None), "role":Union(int,None)}
                        if guildf['active'] and guildf['channel']:
                            guild = self.client.get_guild(int(guild_id))
                            if guild:
                                role = None
                                channel = guild.get_channel(int(guildf['channel']))

                                if guildf['role']:
                                    role = guild.get_role(int(guildf['role']))
                                if channel:
                                    check_txt = "afternoon" if current_task['current'] == "afternoon" else "evening"
                                    if role:
                                        await channel.send(f"<@&{role.id}> Time to collect your {check_txt} oil, Commander "+self.client.emotes['ames'])
                                    else:
                                        await channel.send(f"Time to collect your {check_txt} oil, Commander "+self.client.emotes['ames'])
                except Exception as e:
                    await self.logger.send(self.name, "oil task", e)
                    continue
            
            current_task['current'] = "night" if current_task['current'] == "afternoon" else "afternoon"
            self.save_task(current_task)
                    
        except Exception as e:
            #traceback.print_exc()
            self.logger.send(self.name, "oil task", e)

    def save_task(self, task):
        with open(os.path.join(dir_path, self.config['oil_rem_task']), "w+") as tf:
            tf.write(json.dumps(task, indent=4))

    @check_oil.before_loop
    async def before_check_oil(self):
        print(self.name, "Awaiting client...", end="")
        await self.client.wait_until_ready()
        self._load_resource()
        print("started")
    
    @bo.group(invoke_without_command=True)
    async def wiki(self, ctx, *option):
        channel = ctx.channel
        if ctx.invoked_subcommand is None:
            options = {
                "base":     "https://blueoath.miraheze.org/wiki/Base",
                "senki":    "https://blueoath.miraheze.org/wiki/Senki",
                "guilds":   "https://blueoath.miraheze.org/wiki/Guilds",
                "wall":     "https://blueoath.miraheze.org/wiki/Wishing_Wall"
            }
            if not option:
                await channel.send(f"Here's the requested link:\nhttps://blueoath.miraheze.org/wiki/Main_Page")
            else:
                await channel.send(f"Here's the requested link:\n{options.get(option[0], 'https://blueoath.miraheze.org/wiki/Main_Page')}")

    @wiki.command()
    async def settings(self, ctx):
        await ctx.channel.send(file=discord.File(os.path.join(dir_path,self.config['assets_path'],"settings.png")))

    def cog_unload(self):
        self.check_oil.cancel()

    @bo.command()
    async def make_res(self, ctx, *options):
        channel=ctx.message.channel
        author=ctx.message.author
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return
        
        local = self.get_res_local()
        with open(os.path.join(dir_path, self.config['index_path'])) as idf:
            index = json.load(idf)
            names = [("".join(name.split(" ")),img) for name, img in zip(index['search_name'], index['portrait_square'])]

        if "update" in options:
            await channel.send("Updating missing/new assets")
            diff = [name for name in names if not name[0] in local]
        else:
            await channel.send("Forcing asset update")
            diff = names
        
        msg = await channel.send("fetching...")
        error = 0
        for i, (name, img) in enumerate(diff):
            try:
                icon = Image.open(BytesIO(requests.get(img).content))
                icon.save(os.path.join(dir_path,self.config['assets_path'],"png", f"{name}.png"))
                icon.close()
            except Exception as e:
                await self.logger.send(self.name, "[make_res]", e)
                error += 1
                continue

            if (i+1)%10==0: await msg.edit(content=msg.content+".")
        
        await msg.edit(content=msg.content+f" done ({error} failed)")
    
    def get_res_local(self):
        local_list = []
        for filename in glob.glob(os.path.join(dir_path, self.config['assets_path'], "png", '*.png')):
            local_list.append(filename.split('\\')[-1].split('.')[0])
        return local_list
    
    @bo.command()
    async def update_res(self, ctx):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return
        await self.update_server(ctx)

    def fetch_server_res(self):
        guilds = []
        server_emotes = []
        for server_id in self.client.private['bo_resource_servers']:
            guild = self.client.get_guild(server_id)
            guilds.append(guild)
            server_emotes += list(guild.emojis)
        
        return guilds, [emote.name for emote in server_emotes]
    
    async def update_server(self, ctx):
        channel = ctx.channel

        local_list = self.get_res_local()
        servers, server_emotes = self.fetch_server_res()

        flag = None
        for local_emote in local_list:
            if not local_emote in server_emotes:
                for server in servers:
                    flag = False
                    if server.emoji_limit == len(server.emojis):
                        await self.logger.send(self.name, "server full", server.id)
                        continue
                    else:
                        await self.logger.send(self.name, 'creating', local_emote, 'in', server.name, f"{server.emoji_limit} ({len(server.emojis)})","\n")
                        with open(os.path.join(dir_path, self.config['assets_path'], "png", f"{local_emote}.png"), "rb") as update_emote:
                            try:
                                await server.create_custom_emoji(name=local_emote, image=update_emote.read())
                            except Exception as e:
                                await self.logger.send(self.name, "failed to upload", e)
                                traceback.print_exc()
                            else:
                                await self.logger.send(self.name, 'success')
                                flag = True
                                break
    
                if flag is True:
                    await channel.send(f"Added {local_emote}")
                elif flag is False:
                    await channel.send(f"Failed to add {local_emote}")
        if flag is None:
            await channel.send("All assets already up to date")

        self._load_resource()

    @bo.command()
    async def update_tag(self, ctx, *options):
        channel=ctx.message.channel
        author=ctx.message.author
        if not self.client._check_author(author):
            await channel.send(self.client.emotes['ames'])
            return

        if not options:
            with open(os.path.join(dir_path, self.config['index_path'])) as idf:
                index = json.load(idf)
            charas = ["".join(ship.split()) for ship in index['en']]
        elif "new" in options:
            with open(os.path.join(dir_path, self.config['index_path'])) as idf:
                index = json.load(idf)
            charas = []
            for ship in index['en']:
                shipname = ''.join(ship.split())
                filename = f"{shipname}.json"
                with open(os.path.join(dir_path, self.config['ship_path'], filename)) as shipf:
                    data = json.load(shipf)
                if not data.get("tags", []):
                    charas.append(shipname)
        else:
            _character = self.process_request(" ".join(options))
            search_success, _character = self.validate_entry(_character)

            if not search_success:
                await channel.send(f"Failed to edit `{' '.join(options)}`")
                return
            else:
                charas = ["".join(_character['en'].split())]

        if not charas:
            await channel.send("target update list is empty")
            return

        with open(os.path.join(dir_path, self.config['tag_data_path'])) as tagf:
            ship_tags = json.load(tagf)
        
        #msg = channel.send("Starting edit")
        def author_check(message):
            return str(message.author.id) == str(author.id) and message.channel==channel
        for ship in charas:
            text = f"Editing tags for `{ship}`. Type tags or `exit` to finish."
            with open(os.path.join(dir_path, self.config['ship_path'],f"{ship}.json")) as shipf:
                temp = json.load(shipf)
            msg = await channel.send(embed=self.make_utag_embed(temp))
            cmd = await channel.send(text)
            while True:
                message = await self.client.wait_for("message", check=author_check)

                if not message.content.startswith("--"):
                    await message.delete()
                    if message.content.startswith("exit"):
                        if not temp.get("tags",None):
                            temp['tags'] = []
                            ship_tags[ship] = []
                        with open(os.path.join(dir_path, self.config['ship_path'], f"{ship}.json"), "w+") as shipf:
                            shipf.write(json.dumps(temp))
                        with open(os.path.join(dir_path, self.config['tag_data_path']), "w+") as tagf:
                            tagf.write(json.dumps(ship_tags, indent=4))
                        
                        await msg.edit(content=f"Finished editing `{ship}`", embed=None)
                        if message.content == "exit!":
                            await cmd.delete()
                            return
                        break
                    # process tag update:
                    value = message.content
                    append = []
                    remove = []
                    for tag in [i.strip() for i in value.split(',')]:
                        if tag.startswith("+"):
                            append.append(tag[1:])
                        elif tag.startswith("-"):
                            remove.append(tag[1:])
                    if not append and not remove:
                        temp['tags'] = [i.strip() for i in value.split(',')]
                        await cmd.edit(content="\n".join([text,f"> Setting `tags` to `{temp['tags']}`"]))
                    else:
                        for tag in remove:
                            try:
                                temp['tags'].pop(temp['tags'].index(tag))
                            except:
                                continue
                        temp['tags'] += append
                        await cmd.edit(content="\n".join([text,f"> Modifying `tags` - added `{append}` and removed `{remove}`"]))
                
                with open(os.path.join(dir_path, self.config['ship_path'], f"{ship}.json"), "w+") as shipf:
                    shipf.write(json.dumps(temp))
                with open(os.path.join(dir_path, self.config['tag_data_path']), "w+") as tagf:
                    ship_tags[ship] = temp['tags']
                    tagf.write(json.dumps(ship_tags, indent=4))
                await msg.edit(embed=self.make_utag_embed(temp))
            
            await cmd.delete()

    def make_utag_embed(self, data):
        title = f"{data['dname']}\n{data['jp']}" if data['prefix'] == None else f"{data['prefix']} {data['dname']}\n{data['jp']}"

        embed = discord.Embed(
            title=title,
            description=data['comment'] if data['comment'] != None else "No description... yet",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        if data['wiki']['active']:
            embed.url = data['wiki']['url']
        embed.set_author(name="Asahi's Report")
        embed.set_footer(text="BO Ship | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        if data['img_sq']:
            embed.set_thumbnail(url=data['img_sq'])

        embed.add_field(
            name="> **Class**",
            value=f"{data['ship_class']} ({data['hull_code']})",
            inline=False
        )
        embed.add_field(
            name="> **Affiliation**",
            value=f"{data['faction']} ({data['faction_jp'] if data['faction_jp'] else 'N/A'})"
        )
        embed.add_field(
            name="> **Acquisition**",
            value=f"{data['acquisition'] if data['acquisition'] else 'TBC'}"
        )
        embed.add_field(
            name="> **Rarity**",
            value=data['rarity'] if data['rarity'] else "No data"
        )

        if data['skills']:
            if data['skills'][0]['name'] == "Class Skill":
                embed.add_field(
                    name="> **Class Skill**",
                    value=data['skills'].pop(0)['text'],
                    inline=False
                )

            for i, skill in enumerate(data['skills']):
                embed.add_field(
                    name=f"> **Skill {i+1}**",
                    value="\n".join(skill['name'].split("\n")),
                    inline=False
                )
                embed.add_field(
                    name="Description",
                    value="-"+"\n-".join(skill['text']),
                    inline=False
                )
        else:
            embed.add_field(
                name="> **Skill Data**",
                value="Data Not Available",
                inline=False
            )

        if not data['traits']:
            embed.add_field(
                name="Trait Data",
                value="Not Available",
                inline=False
            )
        else:
            for i, trait in enumerate(data['traits']):
                embed.add_field(
                    name=f"Trait {i+1} - {trait['name']}",
                    value=trait['text'] if trait['text'] != None else "No data available",
                    inline=False
                )
        embed.add_field(
            name="> **Tags**",
            value=", ".join(data['tags']) if data.get("tags",None) else "None"
        )
        return embed

    #@bo.group(aliases=['tags'],invoke_without_subcommand=True)
    @bo.command(aliases=['tags'])
    async def tag(self, ctx, *tags):
        channel = ctx.message.channel
        if not ctx.invoked_subcommand is None:
            return
        elif not tags:
            await channel.send("No input detected - use `.bo help tag` or `.bo help definitions` if you're stuck")
            return
        elif tags[0] in ['d','def','help']:
            await self.d(ctx, *tags[1:])
            return

        _character = self.process_request(" ".join(tags))
        search_success, _character = self.validate_entry(_character)

        with open(os.path.join(dir_path, self.config['tag_data_path'])) as tagf:
            ship_tags = json.load(tagf)

        if not search_success:
            # do tag search
            include, exclude = [],[]
            for tag in tags:
                # do a tag validation
                if tag.startswith('-'):
                    exclude.append(tag[1:])
                else:
                    include.append(tag)
            
            all_tags = []
            for tag in self.tags.values():
                all_tags += list(tag.keys())

            for tag in include+exclude:
                if not tag in all_tags:
                    await channel.send(f"Unknown tag `{tag}`")
                    return

            lineup = []
            #with open(os.path.join(dir_path, self.config['index_path'])) as idf:
            #    index = json.load(idf)
            #for ship in index['en']:
            #    with open(os.path.join(dir_path, self.config['ship_path'], f"{''.join(ship.split())}.json")) as shipf:
            #        data = json.load(shipf)
            for s, t in ship_tags.items():
                if all([tag in t for tag in include]) and all(not tag in t for tag in exclude):
                    with open(os.path.join(dir_path, self.config['ship_path'], f"{s}.json")) as shipf:
                        data = json.load(shipf)
                        lineup.append(data)
            lineup.sort(key=lambda x: x['dname'])
            await channel.send(embed=self.make_search_embed(lineup, include, exclude))
        else:
            #with open(os.path.join(dir_path, self.config['ship_path'], f"{''.join(_character['en'].split())}.json")) as shipf:
            #    data = json.load(shipf)
            await channel.send(embed=self.make_tag_embed(_character,ship_tags.get(''.join(_character['en'].split()), [])))
    
    def make_tag_embed(self, chara, data):
        embed = discord.Embed(
            title="Senki Tags",
            description=f"Fetching `{chara['dname']}`'s tags.",
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Asahi's Report")
        embed.set_footer(text="BO Tag | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        if chara['img']:
            embed.set_thumbnail(url=chara['img'])
        data.sort()
        embed.add_field(
            name="Tags",
            value=", ".join([f"`{tag}`" for tag in data]) if data else "None"
        )
        return embed
    
    def make_search_embed(self, lineup, include, exclude):
        description = f"Found `{len(lineup)}` character(s) that "
        ads = []
        if include:
            ads.append("include " + ", ".join([f"`{t}`" for t in include]))
        if exclude:
            ads.append("exclude " + ", ".join([f"`{t}`" for t in exclude]))
        
        description += " and ".join(ads)
        
        embed = discord.Embed(
            title="Senki Tag Search",
            description=description,
            colour=self.colour,
            timestamp=datetime.datetime.utcnow()
        )

        for chunk in self.client.chunks(lineup, 15):
            embed.add_field(
                name="Results",
                value="\n".join([f"{self.ship_pfp.get(''.join(ship['en'].split()).lower(),':grey_question:')} {ship['dname']}" for ship in chunk])
            )
        embed.set_author(name="Asahi's Report")
        embed.set_footer(text="BO Tag | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        return embed

    #@tag.command(aliases=['def','help'])
    async def d(self, ctx, *request):
        channel = ctx.message.channel
        author = ctx.message.author
        if not request:
            await channel.send("No input - enter tags to fetch their definitions")
            return

        # standardize and pick unique items
        request = [i.lower() for i in request]
        request = list(set(request))

        # validate
        all_tags = dict()
        for item in self.tags:
            all_tags = {**all_tags, **self.tags[item]} 

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
        embed.set_author(name='Asahi\'s Report')
        embed.set_footer(text='BO Tag Definitions | Re:Re:Write Ames',icon_url=self.client.user.avatar_url)
        for tag, definition in tags:
            embed.add_field(
                name=f"> `{tag}`",
                value=definition,
                inline=False
            )
        return embed
    
def setup(client):
    client.add_cog(blueoathCog(client))