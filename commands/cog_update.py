# this module will focus on the automation of updates for hnote db

import discord
from discord.ext import commands
import datetime, glob, os, asyncio, traceback, json
from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
dir = os.path.dirname(__file__)

preupdate_checklist = [
    "+ update hnoteDB source",
    "+ check for new indicies in tl_index",
    "+ update pandaDB basic/placeholer charainfo and tags",
]
update_meta = [
    "+ updates prefix_title, prefix_new in hatsune_config.json",
    "+ updates unit_list index",
    "+ grab new assets from estertion by comparing with fag (if applicable)",
    "+ convert and upload new assets (if applicable)",
    "+ updates gacha state"
]

class updateCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = client.log
        self.name = "[updater]"
        self.db = self.client.database

    @commands.group(
        usage=".update",
        help="update resource servers and data",
        hidden=True,
        invoke_without_subcommand=True,
        case_insensitive=True
    )
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

        # step 1 - update index
        await channel.send("> Starting update process")
        msg = await channel.send("Updating index...")
        try:
            flag = await self.fetch_index()
        except Exception as e:
            await self.logger.send(self.name, e)
            await msg.edit(content=msg.content+" **failed**")
        else:
            if flag:
                await msg.edit(content=msg.content+" **done**")
            else:
                await msg.edit(content=msg.content+" **failed**")
        
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

    @update.command()
    async def index(self, ctx):
        channel = ctx.channel
        if not self.client._check_author(ctx.message.author):
            await channel.send(self.client.emotes['ames'])
            return

        success = await self.fetch_index()
        if not success:
            await channel.send('Failed to update list')
        else:
            await channel.send(self.client.emotes['sarenh'])

    async def fetch_index(self, mode='update'):
        conn = self.db.db_pointer.get_connection()
        if not conn.is_connected():
            return False
        
        query = "SELECT unit_id, unit_name, unit_name_eng, tag FROM hatsune_bot.charadata"
        id_list, hn_list, flb_list, en_list, jp_list = [], [], [], [], []

        try:
            cursor = conn.cursor()
            cursor.execute(query)
            with open(self.client.config['fag_index_path'], encoding='utf-8') as f:
                fag = json.load(f)
            for uid, name, nametl, rtag in cursor:
                id_list.append(uid)
                jp_list.append(name)
                en_list.append(nametl.lower())
                hn_list.append(fag.get(name.replace('（','(').replace('）',')'), None))
                flb_list.append('flb' in [i.strip() for i in rtag.split(",")])
        except Exception as e:
            await self.logger.send(self.name, e)
            self.db.release(conn)
            return False
        else:
            new_ulist = {
                "id": id_list,
                "hn": hn_list,
                "flb":flb_list,
                "en": en_list,
                "jp": jp_list
            }
        
        if mode=='fetch':
            return new_ulist
        elif mode == 'update':
            try:
                with open(os.path.join(self.client.dir, self.client.config['unit_list_path']), 'w') as ulf:
                    ulf.write(json.dumps(new_ulist, indent=4))
            except Exception as e:
                await self.logger.send(self.name, e)
                return False
            else:
                return True
    
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
                                self.logger.send(self.name, 'success')
                                flag = True
                if flag is True:
                    await channel.send(f"Added {local_emote}")
                elif flag is False:
                    await channel.send(f"Failed to add {local_emote}")
        if flag is None:
            await channel.send("All assets already up to date")

        self.client._load_resource()

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
            mode, value = command.split('.')

            if mode == 'prifes':
                await channel.send(f"setting prifes to {value}")
                gacha_config['prifes'] = int(value)

            elif mode == 'lim':
                await channel.send(f"replacing limited pool with {value.split(',')}")
                gacha_config['pools']['lim'] = value.split(',')

            elif mode == 'r' or mode == 'sr' or mode == 'ssr':
                for chara in value.split(','):
                    if chara.startswith('-'):
                        chara = chara[1:]
                        flag = 'del'
                    else:
                        flag = 'add'
                    
                    if not chara in units['en']:
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


def setup(client):
    client.add_cog(updateCog(client))
