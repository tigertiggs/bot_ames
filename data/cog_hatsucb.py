import json, asyncio, datetime, pytz, re
import nextcord
from discord import NotFound
from nextcord.ext import commands, tasks
from glob import glob
from copy import deepcopy
import utils as ut
import templates as tem

NUM = [
    ':one:',
    ":two:",
    ":three:",
    ":four:",
    ":five:"
]

def setup(client):
    client.add_cog(hatsucbCog(client))

class hatsucbCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[Hatsune-CB]'
        self.logger = ut.Ames_logger(self.name, self.client.Log)
        self.logger.init_client(self.client)

        self.rel_path = ut.full_path(self.client.dir, self.client.config['configs']['hatsune_cb'])

        with open(ut.full_path(self.rel_path, 'hatsucb_config.json')) as f:
            self.hatsucb_cf = json.load(f)
        
        #self.timeout_checker.start()
        self.new_day_checker.start()
    
    @commands.group(invoke_without_command=True)
    async def guild(self, ctx, option=None):
        channel = ctx.channel
        #author = ctx.author

        # load guild data
        guild_id = ctx.guild.id
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json")) as f:
                guild_prop = json.load(f)
        except:
            guild_prop = tem.fetch('hcb_guild')
        
        if not option is None:
            # try to process subguild_id
            if not guild_prop['clans']:
                await channel.send('No registered clans found in this server')
                return

            try:
                option = str(int(option))
            except:
                target = [v for v in guild_prop['clans'].values() if v['name'] == option]
                target = target[0] if target else None
            else: 
                target = guild_prop['clans'].get(str(option), None)

            if not target:
                await channel.send(f"Failed to find clan via {option}")
                return
            
            await channel.send(embed=self.embed_clan_prop(target, ctx.guild))

        else:
            await channel.send(embed=self.embed_guild_prop(guild_prop, ctx.guild))
    
    def embed_guild_prop(self, gp, g):
        embed = {
            'title': 'Hatsune CB Manifest',
            'descr': 'Basic CB and clan parameters below',
            'footer': {'text': 'Guild general props', 'url': self.client.user.avatar.url},
            'fields': []
        }

        # display guild boss names
        for i in range(5):
            embed['fields'].append(
                {
                    'name': f"{NUM[i]} Boss {i+1} Name",
                    'value': gp['bosses'][i] if gp['bosses'][i] else 'not set',
                    'inline': True
                }
            )
        
        # display basic clan data
        if gp['clans']:
            clans = sorted(list(gp['clans'].items()), key=lambda x: x[0])
            for _, prop in clans:
                temp = [
                    {
                        'name': f"> Clan {prop['subguild_id']}",
                        'value': f"Name: {prop['name'] if prop['name'] else 'not set'}",
                        'inline': False
                    },
                    {
                        'name': "Clan CB Manager Role",
                        'value': f"<@&{prop['role_leader']}>" if prop['role_leader'] else 'not set',
                        'inline': True
                    },
                    {
                        'name': "Clan Member Role",
                        'value': f"<@&{prop['role_member']}>" if prop['role_member'] else 'not set',
                        'inline': True
                    },
                    {
                        'name': "Registered Members",
                        'value': str(len(self.get_members(g, prop['role_member']))) if prop['role_member'] else 'N/A',
                        'inline': True
                    },
                    
                ]

                embed['fields'] += temp
        else:
            embed['fields'].append(
                {
                    'name': 'Clan data',
                    'value': 'No recorded clan data',
                    'inline': False
                }
            )
        
        return ut.embed_contructor(**embed)

    def embed_clan_prop(self, cp, g):
        embed = {
            'title': 'Hatsune CB clan settings',
            'descr': 'Clan parameters below. See: `.guild set`',
            'footer': {'text': 'Clan properties', 'url': self.client.user.avatar.url},
            'fields': [
                {
                    'name': 'Name',
                    'value': (cp['name'] if cp['name'] else 'not set'),# + \
                        #"\nThe clan's name. Used for indexing, search, and display purposes.",
                    'inline': True
                },
                {
                    'name': 'ID',
                    'value': (cp['subguild_id'] if cp['subguild_id'] else 'to be set'),# + \
                        #"\nThe clan's ID. Used for indexing, search, and display purposes.",
                    'inline': True
                },
                {
                    'name': 'Members',
                    'value': (str(len(self.get_members(g, cp['role_member']))) if cp['role_member'] else 'N/A'),
                    'inline': True
                },
                {
                    'name': 'CB Settings',
                    'value': 'General CB settings',
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Clan Leader Role',
                    'value': '> **Clan Manager Role:** ' + (f"<@&{cp['role_leader']}>" if cp['role_leader'] else 'not set') + \
                        "\nThe clan manager role. Only users with this role can edit clan parameters and use restricted CB commands.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Clan Member Role',
                    'value': '> **Clan Member Role:** ' + (f"<@&{cp['role_member']}>" if cp['role_member'] else 'not set') + \
                        "\nThe clan member role. Used to identify clan members. Clan managers must also have this role.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Notice Channel',
                    'value': '> **Notice Channel:** ' + (f"<#{cp['channel_notice']}>" if cp['channel_notice'] else 'not set') + \
                        "\nThe clan's notice channel. Ames will post and update overview CB data in this channel. "\
                            "Clan leaders/subleads will find this info helpful. Ames will not perform updates if this is not set.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Primary Channel',
                    'value': '> **Primary Channel:** ' + (f"<#{cp['channel_primary']}>" if cp['channel_primary'] else 'not set') + \
                        "\nThe clan's primary channel for invoking CB commands. This channel is unique and cannot be shared among multiple clans. "\
                            "CB commands invoked outside this channel will be ignored.",
                    'inline': False
                },
                {
                    'name': 'Queue Settings',
                    'value': 'Tailor the complexity of the CB queue to your clan\'s needs.',
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Track OT',
                    'value': '> **Track OT:** ' + ('True' if cp['settings']['b_ot'] else 'False') + \
                        "\nEnables the ability to track OT via the `.ot` command.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Track Wave',
                    'value': '> **Track Wave:** ' + ('True' if cp['settings']['b_wave'] else 'False') + \
                        "\nEnables the ability to track waves. Enabling this allows the following functions:\n"\
                            "1) Allows members to queue for specific waves via `.q [boss_num] [wave]`\n"\
                                "2) Allows members to announce boss kills for automatic wave increment via `.q [boss_num] x`",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Track Timeout',
                    'value': '> **Track Timeout:** ' + ('True' if cp['settings']['b_timeout'] else 'False') + \
                        "\nEnables the ability automatically prune member queues if they are not resolved within a set time period."\
                            " Enabling this means all queues will be timestamped and their elapsed time will be displayed.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Timeout Time',
                    'value': '> **Timeout Time:** ' + f"{str(cp['settings']['timeout'])}min" + \
                        "\nThe time in minutes window where queues are valid. Queues outside this window will be automatically pruned."\
                            " Only used if `Track Timeout` is active.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Empty queue quick message',
                    'value': '> **Empty queue quick message:** ' + ('True' if cp['settings']['b_emptyq'] else 'False') + \
                        "\nHave Ames reply a quick message instead of a embed report if the queue is empty (for the current wave). "\
                            "Disregards active OTs (if applicable).",
                    'inline': False
                }
                
            ]
        }
        return ut.embed_contructor(**embed)

    def embed_clan_prop_split(self, cp, g):
        embed1 = {
            'title': 'Hatsune clan admin settings',
            'descr': 'Admin parameters below. See: `.guild set`',
            'footer': {'text': 'Clan properties 1/2', 'url': self.client.user.avatar.url},
            'fields': [
                {
                    'name': 'Name',
                    'value': (cp['name'] if cp['name'] else 'not set'),# + \
                        #"\nThe clan's name. Used for indexing, search, and display purposes.",
                    'inline': True
                },
                {
                    'name': 'ID',
                    'value': (cp['subguild_id'] if cp['subguild_id'] else 'to be set'),# + \
                        #"\nThe clan's ID. Used for indexing, search, and display purposes.",
                    'inline': True
                },
                {
                    'name': 'Members',
                    'value': (str(len(self.get_members(g, cp['role_member']))) if cp['role_member'] else 'N/A'),
                    'inline': True
                },
                {
                    'name': 'CB Settings',
                    'value': 'General CB settings',
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Clan Leader Role',
                    'value': '> **Clan Manager Role:** ' + (f"<@&{cp['role_leader']}>" if cp['role_leader'] else 'not set') + \
                        "\nThe clan manager role. Only users with this role can edit clan parameters and use restricted CB commands.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Clan Member Role',
                    'value': '> **Clan Member Role:** ' + (f"<@&{cp['role_member']}>" if cp['role_member'] else 'not set') + \
                        "\nThe clan member role. Used to identify clan members. Clan managers must also have this role.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Notice Channel',
                    'value': '> **Notice Channel:** ' + (f"<#{cp['channel_notice']}>" if cp['channel_notice'] else 'not set') + \
                        "\nThe clan's notice channel. Ames will post and update overview CB data in this channel. "\
                            "Clan leaders/subleads will find this info helpful. Ames will not perform updates if this is not set.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Primary Channel',
                    'value': '> **Primary Channel:** ' + (f"<#{cp['channel_primary']}>" if cp['channel_primary'] else 'not set') + \
                        "\nThe clan's primary channel for invoking CB commands. This channel is unique and cannot be shared among multiple clans. "\
                            "CB commands invoked outside this channel will be ignored.",
                    'inline': False
                }
            ]
        }

        embed2 = {
            'title': 'Hatsune clan CB settings',
            'descr': 'Queue settings below. Tailor the complexity of the CB queue to your clan\'s needs. See: `.guild set`',
            'footer': {'text': 'Clan properties 2/2', 'url': self.client.user.avatar.url},
            'fields': [
                {
                    'name': ut.SPACE,
                    'value': '> **Auto-increment Hits:** ' + ('True' if cp['settings']['b_autoincr'] else 'False') + \
                        "\nAuto increment member's daily hit counter when resolving valid non-OT hits.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Track OT',
                    'value': '> **Track OT:** ' + ('True' if cp['settings']['b_ot'] else 'False') + \
                        "\nEnables the ability to track OT via the `.ot` command.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Track Wave',
                    'value': '> **Track Wave:** ' + ('True' if cp['settings']['b_wave'] else 'False') + \
                        "\nEnables the ability to track waves. Enabling this allows the following functions:\n"\
                            "1) Allows members to queue for specific waves via `.q [boss_num] [wave]`\n"\
                                "2) Allows members to announce boss kills for automatic wave increment via `.q [boss_num] x`",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Track Timeout',
                    'value': '> **Track Timeout:** ' + ('True' if cp['settings']['b_timeout'] else 'False') + \
                        "\nEnables the ability automatically prune member queues if they are not resolved within a set time period."\
                            " Enabling this means all queues will be timestamped and their elapsed time will be displayed.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Timeout Time',
                    'value': '> **Timeout Time:** ' + f"{str(cp['settings']['timeout'])}min" + \
                        "\nThe time in minutes window where queues are valid. Queues outside this window will be automatically pruned."\
                            " Only used if `Track Timeout` is active.",
                    'inline': False
                },
                {
                    'name': ut.SPACE,#'Empty queue quick message',
                    'value': '> **Empty queue quick message:** ' + ('True' if cp['settings']['b_emptyq'] else 'False') + \
                        "\nHave Ames reply a quick message instead of a embed report if the queue is empty (for the current wave). "\
                            "Disregards active OTs (if applicable).",
                    'inline': False
                }
            ]
        }
        return ut.embed_contructor(**embed1), ut.embed_contructor(**embed2)

    def get_members(self, guild, role_id):
        role_id = int(role_id)
        temp = []
        for member in guild.members:
            for role in member.roles:
                if role.id == role_id:
                    temp.append(member)
                    break
        
        return temp

    def check_roles(self, role_list, member, channel=None, gp=None):
        found = []
        if channel and gp:
            ind = gp['index'].get(str(channel.id), None)
            cp = gp['clans'].get(ind, None)
            if cp:
                cm = cp.get('role_leader', None)
                if cm:
                    role_list = [cm] + role_list
    
        for role_id in role_list:
            if role_id.isnumeric():
                role_id = int(role_id)
                for role in member.roles:
                    if role.id == role_id:
                        found.append(role)
                        break

        return found

    #@guild.command(aliases=['new'])
    async def set_old(self, ctx, option=None):
        channel = ctx.channel
        author = ctx.author

        mode = ctx.invoked_with
        # load guild data
        guild_id = ctx.guild.id
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json")) as f:
                guild_prop = json.load(f)
        except:
            guild_prop = tem.fetch('hcb_guild')

        if mode == 'new':
            if not self.client.check_perm(author):
                await channel.send('Restricted command '+self.client.emotes['ames'])
                return
            
            clan_prop = tem.fetch('hcb_clan')
        
        elif mode == 'set':
            try:
                req = str(int(option))
            except:
                req = None

            if req:
                if not self.client.check_perm(author):
                    await channel.send('Restricted command '+self.client.emotes['ames'])
                    return
                elif not req in guild_prop['clans']:
                    await channel.send('Failed to find clan')
                    return
                clan_prop = guild_prop['clans'][req]
            else:
                found = self.check_roles(guild_prop['index'].keys(), author, channel, guild_prop)
                if not found:
                    await channel.send('Restricted command '+self.client.emotes['ames'])
                    return
                clan_prop = guild_prop['clans'][guild_prop['index'][str(found[0].id)]]

        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel and \
                    not msg.content.startswith('--')

        msg = "**Setting clan properties. Keys are:** "\
            "`name`, `leader`, `member`, `channel`, `notice`, `ot`, `wave`, `timeout`, `timeout_min`, `emptyq`, `exit`, `cancel`\n"\
            "> **Input form:**\n"\
            "`name`: string\n"\
            "`leader`, `member`: discord@role\n"\
            "`channel`, `notice`: discord#channel\n"\
            "`ot`, `wave` `timeout` `emptyq`: 0|1 OR t|f\n"\
            "`timeout_min`: integer\n"\
            "**Syntax:**\n> `key1: value1, key2: value2, ...`\n"\
            "**Use `exit` to finalize, use `cancel` to abandon changes.**\nAwaiting commands...\n"
        embed = await channel.send(embed=self.embed_clan_prop(clan_prop, ctx.guild))
        status = await channel.send(msg)
        EXIT = False
        while True:
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            st = []
            for cmd in content.split(','):
                cmd = cmd.strip()
                k, _, v, = cmd.partition(':')
                k = k.strip().lower()
                v = v.strip().lower()
                is_none = not bool(v)

                print(cmd, k, v, sep='|')

                if k == 'exit':
                    if clan_prop['role_leader'] is None:
                        st.append(f'`[{cmd}]` **Failed: Cannot exit if clan manager role is not set**')
                        EXIT = False
                    else:
                        EXIT = True
                        break
                
                elif k == 'cancel':
                    await embed.delete()
                    await status.edit(content='Cancelled')
                    return
            
                elif k == 'name':
                    if v in guild_prop.get('active_names', []):
                        st.append(f"`[{cmd}]` Failed: Clan name already taken by another clan in the same server")
                        continue
                    elif [i.strip() for i in v.lower().split() if i.strip()][-1] == 'admin':
                        st.append(f"`[{cmd}]` Failed: Clan name cannot end in 'admin'")
                        continue
                    elif v.isnumeric():
                        st.append(f"`[{cmd}]` Failed: Clan name cannot be purely numeric")
                        continue
                    clan_prop['name'] = v if not is_none else None
                
                elif k in ['leader', 'member']:
                    if not v.startswith('<@&') and not v.endswith('>'):
                        st.append(f"`[{cmd}]` Failed: Invalid discord role")
                        continue
                    else: 
                        clan_prop['role_'+k] = v[3:-1] if not is_none else None
                
                elif k in ['channel', 'notice']:
                    if not v.startswith('<#') and not v.endswith('>'):
                        st.append(f"`[{cmd}]` Failed: Invalid discord channel")
                        continue
                    else: 
                        cid = v[2:-1] if not is_none else None
                        if cid in guild_prop['active_channels'] and k == 'channel':
                            st.append(f"`[{cmd}]` Failed: Channel already taken by another clan")
                            continue
                        clan_prop['channel_primary' if k == 'channel' else 'channel_notice'] = cid
                
                elif k in ['ot', 'wave', 'timeout', 'emptyq']:
                    if v.startswith('0') or v.startswith('f'):
                        v = False
                    elif v.startswith('1') or v.startswith('t'):
                        v = True
                    else:
                        st.append(f"`[{cmd}]` Failed: Invalid value")
                        continue

                    clan_prop['settings']['b_'+k] = v
                
                elif k == 'timeout_min':
                    try:
                        v = int(v)
                    except:
                        st.append(f"`[{cmd}]` Failed to read value")
                        continue
                    else:
                        if v < 5 or v > 120:
                            st.append(f"`[{cmd}]` Failed: Value too extreme (must be between 5 and 120 min)")
                            continue

                    clan_prop['settings']['timeout'] = v
                
                else:
                    st.append(f"`[{cmd}]` Failed: Unknown key")
                    continue
                
                st.append(f"`[{cmd}]` Setting {k} to {v}")

            await embed.edit(embed=self.embed_clan_prop(clan_prop, ctx.guild))
            if st:
                await status.edit(content=msg + '\n'.join(st))
            if EXIT:
                break
        
        if mode == 'new':
            # subguild_id is designed to be sequencial but this can be disrupted by deleting the clan profile
            # hence we iterate through IDs starting at 1 until we find an unused ID
            temp_id = 0
            while True:
                temp_id += 1
                if str(temp_id) in guild_prop['clans']:
                    continue
                else:
                    clan_prop['subguild_id'] = str(temp_id)
                    break
        
        guild_prop['clans'][clan_prop['subguild_id']] = clan_prop
        guild_prop = self.validate_guild_prop(guild_prop)

        with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json"), 'w+') as f:
            f.write(json.dumps(guild_prop,indent=4))

        await embed.delete()
        await status.edit(content='Saved')

    @guild.command(aliases=['new'])
    async def set(self, ctx, option=None):
        channel = ctx.channel
        author = ctx.author
        mode = ctx.invoked_with

        # load guild data
        guild_id = ctx.guild.id
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json")) as f:
                guild_prop = json.load(f)
        except:
            guild_prop = tem.fetch('hcb_guild')
        
        if mode == 'new':
            if not self.client.check_perm(author):
                await channel.send('Restricted command '+self.client.emotes['ames'])
                return
            clan_prop = tem.fetch('hcb_clan')

        elif mode == 'set':
            try:
                req = str(int(option))
            except:
                req = None

            if req:
                cp = guild_prop.get(req, None)
                if cp:
                    await channel.send('Failed to find clan')
                    return
                else:
                    found = self.check_roles([cp['role_leader']], author, channel, guild_prop)
                    if not found or not self.client.check_perm(author):
                        await channel.send('Restricted command '+self.client.emotes['ames'])
                        return
            else:
                found = self.check_roles([cp['role_leader'] for cp in guild_prop['clans'].values()], author, channel, guild_prop)
                if not found:
                    await channel.send('Restricted command '+self.client.emotes['ames'])
                    return
                else:
                    clan_prop = guild_prop['clans'][guild_prop['index'][str(found[0].id)]]
        
        MODE = 0
        EXIT = False
        edit_mode = '> Currently editing **{}**. Switch by entering `admin` or `cb`. Enter `exit` to finalize and save, or enter `cancel` to cancel.'
        edit_mode_options = ['Admin Settings', 'CB Settings']
        instr_admin = \
            'Valid keys: `name`, `admin`, `member`, `channel`, `notice`\n'\
            '> **Input forms:**\n'\
            '`name`: string\n'\
            '`admin`, `member`: discord@role\n'\
            '`channel`, `notice`: discord#channel\n'
        instr_cb = \
            'Valid keys: `autoincr`, `ot`, `wave`, `timeout`, `timeout_min`, `emptyq`\n'\
            '> **Input forms**\n'\
            '`autoincr`, `ot`, `wave`, `timeout`, `emptyq`: 0 or 1, t or f\n'\
            '`timeout_min`: integer\n'
        syntax = \
            '> **Input syntax**\n'\
            '`key1: value, key2: value`\n'\
            'i.e. `name: littlelyricals, ot: 1, emptyq: 1`'
        instr_options = [instr_admin+syntax, instr_cb+syntax]
        msg = 'Awaiting input...\n'

        active_embed = await ctx.send(embed=self.embed_clan_prop_split(clan_prop, ctx.guild)[MODE])
        active_edit_mode = await ctx.send(edit_mode.format(edit_mode_options[MODE]))
        active_instr = await ctx.send(instr_options[MODE])
        received = await ctx.send(msg)

        def check(msg):
            return msg.author == ctx.message.author and \
                msg.channel == ctx.channel and \
                    not msg.content.startswith('--')

        while True:
            inp = await self.client.wait_for('message', check=check)
            content = inp.content
            await inp.delete()

            st = []
            for cmd in content.split(','):
                cmd = cmd.strip()
                k, _, v, = cmd.partition(':')
                k = k.strip().lower()
                v = v.strip().lower()
                is_none = not bool(v)

                print(cmd, k, v, sep='|')

                if k == 'exit':
                    if clan_prop['role_leader'] is None:
                        st.append(f'`[{cmd}]` **Failed: Cannot exit if clan manager role is not set**')
                        EXIT = False
                    else:
                        EXIT = True
                        break
                
                elif k == 'cancel':
                    await active_embed.delete()
                    await active_edit_mode.delete()
                    await active_instr.delete()
                    await received.edit(content='Cancelled')
                    return
            
                elif k == 'name':
                    if v in guild_prop.get('active_names', []):
                        st.append(f"`[{cmd}]` Failed: Clan name already taken by another clan in the same server")
                        continue
                    elif [i.strip() for i in v.lower().split() if i.strip()][-1] == 'admin':
                        st.append(f"`[{cmd}]` Failed: Clan name cannot end in 'admin'")
                        continue
                    elif v.isnumeric():
                        st.append(f"`[{cmd}]` Failed: Clan name cannot be purely numeric")
                        continue
                    clan_prop['name'] = v if not is_none else None
                
                elif k in ['leader', 'member']:
                    if not v.startswith('<@&') and not v.endswith('>'):
                        st.append(f"`[{cmd}]` Failed: Invalid discord role")
                        continue
                    else: 
                        clan_prop['role_'+k] = v[3:-1] if not is_none else None
                
                elif k in ['channel', 'notice']:
                    if not v.startswith('<#') and not v.endswith('>'):
                        st.append(f"`[{cmd}]` Failed: Invalid discord channel")
                        continue
                    else: 
                        cid = v[2:-1] if not is_none else None
                        if cid in guild_prop['active_channels'] and k == 'channel':
                            st.append(f"`[{cmd}]` Failed: Channel already taken by another clan")
                            continue
                        clan_prop['channel_primary' if k == 'channel' else 'channel_notice'] = cid
                
                elif k in ['autoincr', 'ot', 'wave', 'timeout', 'emptyq']:
                    if v.startswith('0') or v.startswith('f'):
                        v = False
                    elif v.startswith('1') or v.startswith('t'):
                        v = True
                    else:
                        st.append(f"`[{cmd}]` Failed: Invalid value")
                        continue

                    clan_prop['settings']['b_'+k] = v
                
                elif k == 'timeout_min':
                    try:
                        v = int(v)
                    except:
                        st.append(f"`[{cmd}]` Failed to read value")
                        continue
                    else:
                        if v < 5 or v > 120:
                            st.append(f"`[{cmd}]` Failed: Value too extreme (must be between 5 and 120 min)")
                            continue

                    clan_prop['settings']['timeout'] = v
                
                elif k == 'admin':
                    MODE = 0
                
                elif k == 'cb':
                    MODE = 1
                
                else:
                    st.append(f"`[{cmd}]` Failed: Unknown key")
                    continue
                
                if not k in ['admin', 'cb']:
                    st.append(f"`[{cmd}]` Setting {k} to {v}")

            await active_embed.edit(embed=self.embed_clan_prop_split(clan_prop, ctx.guild)[MODE])
            await active_edit_mode.edit(edit_mode.format(edit_mode_options[MODE]))
            await active_instr.edit(instr_options[MODE])

            if st:
                await received.edit(content=msg + '\n'.join(st))
            if EXIT:
                break
            
        if mode == 'new':
        # subguild_id is designed to be sequencial but this can be disrupted by deleting the clan profile
        # hence we iterate through IDs starting at 1 until we find an unused ID
            temp_id = 0
            while True:
                temp_id += 1
                if str(temp_id) in guild_prop['clans']:
                    continue
                else:
                    clan_prop['subguild_id'] = str(temp_id)
                    break
        
        guild_prop['clans'][clan_prop['subguild_id']] = clan_prop
        guild_prop = self.validate_guild_prop(guild_prop)

        with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json"), 'w+') as f:
            f.write(json.dumps(guild_prop,indent=4))

        await active_embed.delete()
        await active_edit_mode.delete()
        await active_instr.delete()
        await received.edit(content='Saved')

    @guild.command(aliases=['del'])
    async def delete(self, ctx, option):
        channel = ctx.channel
        author = ctx.author

        if not option:
            await channel.send('No input')
            return
        
        try:
            option = int(option)
        except:
            await channel.send('Failed to read clan ID')
            return
        else:
            option = str(option)
        
        # load guild data
        guild_id = ctx.guild.id
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json")) as f:
                guild_prop = json.load(f)
        except:
            guild_prop = tem.fetch('hcb_guild')
        
        if not option in guild_id['clans']:
            await channel.send('Did not find clan')
            return
        
        found = self.check_roles(guild_prop['index'].keys(), author)
        ind = guild_prop['index'][str(found[0])] if found else None

        if option != str(ind) and not self.client.check_perm(author):
            await channel.send('You do not have permission to perform this')
            return
        else:
            guild_prop['clans'].pop(option)
    
        guild_prop = self.validate_guild_prop(guild_prop)
        with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild_id}.json"), 'w+') as f:
            f.write(json.dumps(guild_prop,indent=4))

        await channel.send('Saved')

    @guild.command()
    async def update(self, ctx):
        if not self.client.check_perm(ctx.author):
            await ctx.send('Restricted command '+self.client.emotes['ames'])
            return
        
        # update guild and clan prop
        for fp in glob(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], '*.json')):
            with open(fp) as f:
                gp = json.loads(f.read())
            all_clans = gp['clans']
            gp['clans'] = {}

            gp = ut.update(tem.fetch('hcb_guild'), gp)
            for key in all_clans.keys():
                all_clans[key] = ut.update(tem.fetch('hcb_clan'), all_clans[key])
            
            gp['clans'] = all_clans

            with open(fp, 'w+') as f:
                f.write(json.dumps(gp, indent=4))
        
        await ctx.send('Updated format')

    def validate_guild_prop(self, gp):
        """
        links channel_primary, role_leader, role_member, name to subguild_id in index
        """
        index = {}
        ac = []
        an = []
        for v in gp['clans'].values():
            if v['role_leader']:
                index[str(v['role_leader'])] = str(v['subguild_id'])
            if v['channel_primary']:
                ac.append(v['channel_primary'])
                index[str(v['channel_primary'])] = str(v['subguild_id'])
            if v['role_member']:
                index[str(v['role_member'])] = str(v['subguild_id'])
            if v['name']:
                index[v['name']] = str(v['subguild_id'])
                an.append(v['name'])
        
        gp['index'] = index
        gp['active_channels'] = ac
        gp['active_names'] = an
        return gp

    @commands.group(invoke_without_command=True, aliases=['ot', 'q'])
    async def queue(self, ctx, *, options=None):
        if ctx.invoked_subcommand is None:
            channel = ctx.channel
            author = ctx.author

            # validate
            IS_VALID, IS_LEADER, clan_prop, queue_list, guild_prop, ql_fn = self.validate_queue_request(ctx)
            if not IS_VALID:
                return

            SETTINGS = clan_prop['settings']

            # display queue if options is none
            if not options:
                if SETTINGS['b_emptyq'] and not [i for i in queue_list['queue'] if i['type'] == 'queue']:
                    await channel.send('The queue is empty - Go wild! '+self.client.emotes['amesblob'])
                    return

                n = await channel.send(embed=self.embed_q_ot(ctx.guild, guild_prop, clan_prop, queue_list, author))
                await asyncio.sleep(60)
                await n.edit(content='This embed has expired '+self.client.emotes['ames'], embed=None)
                return
            
            Q_MODE = ctx.invoked_with.startswith('q')
            options = [i.strip().lower() for i in options.split() if i.strip()]
            # process option
            # .q (@delegatee) [(l) | [boss] (wave) (ot)|(done)|(kill)|(cancel)]
            # .ot (@delegatee) [(l) | [sec] (done)]

            # check if delegate mode
            DELEGATE_MODE = False
            if options[0].startswith('<@'):
                if not IS_LEADER:
                    await channel.send("Could not proxy: Missing manager role "+self.client.emotes['ames'])
                    return

                try:
                    proxy = int(options.pop(0)[2:-1])
                except:
                    await channel.send('Could not proxy: Failed to fetch target member '+self.client.emotes['ames'])
                    return

                proxy = ctx.guild.get_member(proxy)
                if not proxy:
                    await channel.send('Could not proxy: Failed to fetch target member '+self.client.emotes['ames'])
                    return
                
                # check if proxy is part of the guild
                IS_VALID = bool(self.check_roles([clan_prop['role_member']], proxy))
                if not IS_VALID:
                    await channel.send('Could not proxy: Target member is not part of clan '+self.client.emotes['ames'])
                    return
                
                DELEGATE_MODE = True
                author = proxy

            # List mode
            if options[0].startswith('l'):
                await self.send_list(channel, author, queue_list, Q_MODE, SETTINGS, DELEGATE_MODE)
                return
            
            # hit mode
            elif options[0].startswith('h'):
                options.pop(0)
                HIT_APPEND = True
                request = 1

                if options:
                    request = options[0]
                    if request.startswith('-'):
                        HIT_APPEND = False
                        request = request[1:]
                    
                    if not request.isnumeric():
                        await channel.send('Failed to read hit number')
                        return
                    
                    request = int(request)
                    if request > 10 or request < 1:
                        await channel.send('Number of hits to register must be between 1 and 10')
                        return
                    
                # append/remove hits
                if HIT_APPEND:
                    queue_list['done'] += [str(author.id)] * request
                    await channel.send(f"Registered {request} hit(s)")
                else:
                    temp = []
                    counter = 0
                    for hitted in queue_list['done']:
                        if hitted == str(author.id) and counter != request:
                            counter += 1
                        else:
                            temp.append(hitted)

                    queue_list['done'] = temp    
                    await channel.send(f"Unregistered {counter} hit(s)")
                
                with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], ql_fn), 'w+') as f:
                    f.write(json.dumps(queue_list, indent=4))

                await self.update_notice(clan_prop, queue_list, guild_prop, ctx.guild, ql_fn, False)
                return    

            # Queue mode
            if Q_MODE:
                Q_OT = False
                Q_DONE = False
                Q_KILL = False
                Q_CANCEL = False

                # check last option(s)
                for item in options[::-1]:
                    if item.startswith('o'):
                        Q_OT = True
                        options.pop(-1)
                    elif item.startswith('d'):
                        Q_DONE = True
                        options.pop(-1)
                    elif item.startswith('x') or options[-1].startswith('k'):
                        Q_KILL = True
                        Q_DONE = True
                        options.pop(-1)
                    elif item.startswith('c'):
                        Q_CANCEL = True
                        options.pop(-1)
                    else:
                        break
                
                # fetch all active queues by author
                active = self.queue_find_entry(queue_list, author.id, 'queue')

                # check if Q_DONE all
                if Q_DONE and len(options) == 0:
                    # unqueue all
                    for entry in active:
                        queue_list['queue'].pop(queue_list['queue'].index(entry))
                        try:
                            if not entry['payload']['is_ot'] and SETTINGS['b_autoincr']:
                                queue_list['done'].append(str(author.id))
                        except Exception as e:
                            print(self.name, e, entry)
                            await channel.send("Oops - something went wrong")
                            return
                    
                    msg = f"Unqueued {(author.name+' ' if DELEGATE_MODE else '')}from all bosses"
                else:
                    # check boss
                    try:
                        boss = options.pop(0)
                        if boss.startswith('b'):
                            boss = boss[1:]
                        boss = int(boss)
                    except IndexError:
                        await channel.send('Failed to un/queue: missing boss input '+self.client.emotes['ames'])
                        return
                    except ValueError:
                        await channel.send('Failed to un/queue: failed to read boss number '+self.client.emotes['ames'])
                        return
                    
                    if boss < 0 or boss > 5:
                        await channel.send('Failed to un/queue: boss number must be between 1 and 5 '+self.client.emotes['ames'])
                        return
                    
                    # check wave
                    if SETTINGS['b_wave']:
                        try:
                            wave = options.pop(0)
                            if wave.startswith('+'):
                                wave = queue_list['cwave'][boss-1] + int(wave[1:])
                            elif wave.startswith('-'):
                                wave = queue_list['cwave'][boss-1] - int(wave[1:])
                            else:
                                wave = int(wave)
                        except IndexError:
                            wave = queue_list['cwave'][boss-1]
                            pass
                        except ValueError:
                            await channel.send('Failed to un/queue: failed to read wave number '+self.client.emotes['ames'])
                            return
                        if wave < queue_list['cwave'][boss-1] and not (Q_DONE or Q_CANCEL):
                            await channel.send(f'Failed to un/queue: requested wave lower than current wave ({queue_list["cwave"][boss-1]})'+self.client.emotes['ames'])
                            return
                    else:
                        wave = None

                    # check if the queue entry exists or not
                    request_active = [entry for entry in active 
                        if entry['payload']['boss'] == boss 
                            and entry['payload']['wave'] == wave
                    ]

                    num_req_active = len(request_active)
                    if num_req_active == 1:
                        if Q_DONE or Q_KILL or Q_CANCEL:
                            if Q_OT and not request_active[0]['payload']['is_ot']:
                                await channel.send('Failed to unqueue: could not find matching entry '+self.client.emotes['ames'])
                                return
                            else:
                                Q_OT = request_active[0]['payload']['is_ot']
                    
                    request_active = [q for q in request_active if q['payload']['is_ot'] is Q_OT]
                    request_active = request_active[0] if request_active else False

                    # process request
                    if Q_KILL or Q_DONE:
                        if Q_KILL and not SETTINGS['b_wave']:
                            await channel.send('Failed to kill: disabled feature '+self.client.emotes['ames'])
                            return
                        elif Q_KILL and not request_active:
                            await channel.send("Failed to kill: Cannot kill announce a boss-wave you're not queued in "+self.client.emotes['ames'])
                            if IS_LEADER:
                                await channel.send('If you wish to increment the wave, please use `.q sw [boss_num] [wave]` instead')
                            return
                        elif Q_DONE and not request_active:
                            await channel.send('Failed to unqueue: could not find matching entry '+self.client.emotes['ames'])
                            return
                        elif Q_KILL:
                            # check if there are others also queuing for the same boss-wave
                            temp = [entry for entry in queue_list['queue']
                                if entry['payload']['boss'] == boss 
                                and entry['payload']['wave'] == wave
                                and entry['id'] != str(author.id)
                                and entry['type'] == 'queue'
                            ]
                            if temp:
                                def check(msg):
                                    return msg.author == ctx.message.author and msg.channel == ctx.channel 

                                alert = await channel.send(
                                    f"Warning - you're trying to kill announce a boss-wave with `{len(temp)}` active queues other than yourself.\n"\
                                        "They will not be cleared even if you proceed. Proceed with kill announcement? `y/n`")

                                try:
                                    while True:
                                        inp = await self.client.wait_for('message', check=check, timeout=30.0)
                                        
                                        if inp.content.lower().startswith('y'):
                                            await inp.delete()
                                            break
                                        elif inp.content.lower().startswith('n'):
                                            await inp.delete()
                                            await alert.edit('Request cancelled')
                                            return
                                except asyncio.TimeoutError:
                                    await alert.edit(content='Timeout reached: request cancelled')
                                    return
                                
                                await alert.delete()
                            
                            # make changes
                            queue_list['cwave'][boss-1] += 1
                            queue_list['queue'].pop(queue_list['queue'].index(request_active))
                            if SETTINGS['b_autoincr']:
                                queue_list['done'].append(str(author.id))

                            # ready message
                            msg = f"Boss {boss} wave {wave} down.\n"
                            standby = [f"<@{entry['id']}>" for entry in queue_list['queue'] 
                                if entry['payload']['boss'] == boss 
                                and entry['payload']['wave'] == wave + 1
                                and entry['type'] == 'queue'
                            ]
                            if standby:
                                msg += "Standby " + ' '.join(standby)           
                        else:
                            # unqueue
                            queue_list['queue'].pop(queue_list['queue'].index(request_active))
                            if not Q_OT: 
                                queue_list['done'].append(str(author.id))

                            msg = f"Unqueued {(author.name+' ') if DELEGATE_MODE else ''}from boss {boss} " + (f"wave {wave}" if SETTINGS['b_wave'] else '')
                        
                        if not Q_OT and SETTINGS['b_autoincr']: await channel.send(f'incremented {author.name if DELEGATE_MODE else "your"} daily hit count.')
                            
                    elif Q_CANCEL:
                        if not request_active:
                            await channel.send("Failed to cancel: could not find matching entry "+self.client.emotes['ames'])
                            return
                        
                        queue_list['queue'].pop(queue_list['queue'].index(request_active))
                        msg = f"Cancelled {(author.name+' ') if DELEGATE_MODE else ''}from boss {boss} " + (f"wave {wave}" if SETTINGS['b_wave'] else '')
                    
                    else:
                        # queue
                        if request_active:
                            msg = (f"{author.name} is" if DELEGATE_MODE else "You are") + " already queueing for this boss" + ("-wave" if SETTINGS['b_wave'] else '')
                            await channel.send(msg)
                            return
                        elif num_req_active == 1:
                            msg = "Note: " + (f"{author.name}" if DELEGATE_MODE else "You") + " have queued both normally and with OT for this boss" + ("-wave" if SETTINGS['b_wave'] else '')
                            await channel.send(msg)

                        # check other concurrent queues
                        others = len([q for q in queue_list['queue']
                            if q['type'] == 'queue' and
                            q['payload']['boss'] == boss and
                            q['payload']['wave'] == wave and
                            q['id'] != str(author.id)])
                        
                        entry = tem.fetch('hcb_qentry')
                        entry['id']                 = str(author.id)
                        entry['timestamp']          = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
                        entry['type']               = 'queue'
                        entry['payload']['boss']    = boss
                        entry['payload']['wave']    = wave
                        entry['payload']['is_ot']   = Q_OT

                        queue_list['queue'].append(entry)

                        msg = f"Queued {(author.name+' ') if DELEGATE_MODE else ''}for boss {boss}" + (f" wave {wave}" if SETTINGS['b_wave'] else '')

                        if (len(active) + 1) > 3:
                            await channel.send(f"Note: {author.name if DELEGATE_MODE else 'you'} have more than 3 active non-OT queues", delete_after=15.0)
                        if others > 0:
                            await channel.send(f"Note: There are `{others}` others queueing for this boss-wave besides yourself.")
           
            # OT mode
            else:
                OT_DONE = False
                if not SETTINGS['b_ot']:
                    await channel.send('Failed to add OT: disabled feature '+self.client.emotes['ames'])
                    return
                elif options[-1].startswith('d'):
                    OT_DONE = True
                    options.pop(-1)
                
                active = self.queue_find_entry(queue_list, author.id, 'ot')

                # check if Q_DONE all
                if OT_DONE and len(options) == 0:
                    # unqueue all
                    for entry in active:
                        queue_list['queue'].pop(queue_list['queue'].index(entry))
                    
                    msg = f"Removed all OTs" + (f" from {author.name}" if DELEGATE_MODE else '')
                else:
                    # process seconds
                    try:
                        time = options.pop(0)
                        if time.endswith('s'):
                            time = time[:-1]
                        time = int(time)
                    except IndexError:
                        await channel.send('Failed to add/remove OT: missing time input '+self.client.emotes['ames'])
                        return
                    except ValueError:
                        await channel.send('Failed to add/remove OT: failed to read time '+self.client.emotes['ames'])
                        return
                    
                    if OT_DONE:
                        temp = [entry for entry in active if entry['payload']['ot'] == time]
                        if not temp:
                            await channel.send('Failed to remove OT: did not find matching entry '+self.client.emotes['ames'])
                            return

                        temp = temp[0]
                        queue_list['queue'].pop(queue_list['queue'].index(temp))
                        msg = f"Removed {time}s OT" + (f" for {author.name}" if DELEGATE_MODE else '')
                    else:
                        entry = tem.fetch('hcb_qentry')
                        entry['id']             = str(author.id)
                        entry['timestamp']      = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
                        entry['type']           = 'ot'
                        entry['payload']['ot']  = time

                        queue_list['queue'].append(entry)
                        msg = f"Added {time}s OT" + (f" for {author.name}" if DELEGATE_MODE else '')

                        if len(active) + 1 > 3:
                            await channel.send(f"Note: {author.name if DELEGATE_MODE else 'you'} have more than 3 active OT entries", delete_after=15.0)

            with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], ql_fn), 'w+') as f:
                f.write(json.dumps(queue_list, indent=4))

            await channel.send(msg)
            await self.update_notice(clan_prop, queue_list, guild_prop, ctx.guild, ql_fn, False)

    def queue_find_entry(self, ql, id, type):
        return [entry for entry in ql['queue'] if entry['id'] == str(id) and entry['type'] == type]

    def validate_queue_request(self, ctx):
        """
        is_valid: True if channel and member roles match
        is_leader: True if author has leader role
        ql_fn: queue_list filename - guild_id-subguild_id.json

        returns: is_valid, is_leader, clan_prop, queue_list, guild_prop, ql_fn
        """
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild

        return self.validate_queue_request_new(guild, channel, author)
    
    def validate_queue_request_new(self, guild, channel, author):
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild.id}.json")) as f:
                guild_prop = json.load(f)
        except:
            #guild_prop = tem.fetch('hcb_guild')
            return False, False, None, None, None, None,
        
        # check channel
        subguild_key = guild_prop['index'].get(str(channel.id), None)
        if not subguild_key:
            return False, False, None, None, None, None,
        
        # check role
        clan_prop = guild_prop['clans'][subguild_key]
        role_member = clan_prop['role_member']
        role_leader = clan_prop['role_leader']
        found = self.check_roles([role_member, role_leader], author)
        is_valid = bool(found)
        is_leader = role_leader in [str(role.id) for role in found]

        # fetch queue list
        try:
            fn = f"{guild.id}-{subguild_key}.json"
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], fn)) as f:
                queue_list = json.load(f)
        except:
            queue_list = tem.fetch('hcb_queue')
        
        return is_valid, is_leader, clan_prop, queue_list, guild_prop, fn

    async def send_list(self, channel, author, ql, q_mode, settings, is_proxy):
        if not q_mode and not settings['b_ot']:
            await channel.send('Failed to list: disabled feature '+self.client.emotes['ames'])
            return

        entries = self.queue_find_entry(ql, str(author.id), 'queue' if q_mode else 'ot')

        temp = []
        if q_mode:
            if not entries:
                await channel.send(f"{author.name if is_proxy else 'You'} do not have any active queues")
                return

            entries.sort(key=lambda x: (x['timestamp'], x['payload']['boss'], x['payload']['wave'], x['payload']['is_ot']))
            s = f"{author.name if is_proxy else 'Your'} current queues:\n"
            for entry in entries:
                msg = f"<t:{entry['timestamp']}:R> Boss {entry['payload']['boss']}"
                if settings['b_wave']:
                    msg += f" wave {entry['payload']['wave']}"
                msg += " (non-ot)" if not entry['payload']['is_ot'] else " (with-ot)"
                temp.append(msg)
            
            s += '\n'.join(temp)
        else:
            if not entries:
                await channel.send(f"{author.name if is_proxy else 'You'} do not have any active OTs")
                return

            s = f"{author.name if is_proxy else 'Your'} current OTs:\n"
            entries.sort(key=lambda x: x['payload']['ot'])
            for entry in entries:
                temp.append(str(entry['payload']['ot']))
            
            s += ', '.join(temp)
        
        await channel.send(s)

    @queue.command(aliases=['sw'])
    async def setwave(self, ctx, *, options):
        channel = ctx.channel
        IS_VALID, IS_LEADER, clan_prop, queue_list, guild_prop, ql_fn = self.validate_queue_request(ctx)

        if not IS_LEADER:
            return
        elif not options:
            await channel.send(f"No input. See `.q h(elp) {clan_prop['subguild_id']} admin` for syntax.")
            return
        elif ctx.invoked_parents[0] not in ['q', 'queue']:
            return
        elif not clan_prop['settings']['b_wave']:
            await channel.send('Failed to setwave: disabled feature '+self.client.emotes['ames'])
            return
        
        # .q sw [boss] [wave]
        options = [i.strip().lower() for i in options.split() if i.strip()]

        # check boss
        try:
            boss = options.pop(0)
            if boss.startswith('a'):
                boss = 'ALL'
            elif boss.startswith('b'):
                boss = boss[1:]
                boss = int(boss)
            else:
                boss = int(boss)
        except ValueError:
            await channel.send('Failed to setwave: failed to read boss number '+self.client.emotes['ames'])
            return      
        if boss != 'ALL':
            if boss < 0 or boss > 5:
                await channel.send('Failed to setwave: boss number must be between 1 and 5 '+self.client.emotes['ames'])
                return

        # check wave
        try:
            wave = options.pop(0)
            if wave.startswith('+'):
                if boss == 'ALL':
                    wave = []
                    for bn in queue_list['cwave']:
                        wave.append(bn + int(wave[1:]))
                else:
                    wave = queue_list['cwave'][boss-1] + int(wave[1:])
            elif wave.startswith('-'):
                if boss == 'ALL':
                    wave = []
                    for bn in queue_list['cwave']:
                        bn -= int(wave[1:])
                        wave.append(bn if not bn < 1 else 1)
                else:
                    wave = queue_list['cwave'][boss-1] - int(wave[1:])
            else:
                wave = int(wave)
                if boss == 'ALL':
                    wave = [wave, wave, wave, wave, wave]

        except IndexError:
            await channel.send('Failed to setwave: failed to read wave number '+self.client.emotes['ames'])
            return
        except ValueError:
            await channel.send('Failed to setwave: failed to read wave number '+self.client.emotes['ames'])
            return
        
        if boss == 'ALL':
            await channel.send(f"Setting all boss waves to {wave}")
            queue_list['cwave'] = wave
        else:
            await channel.send(f"Setting boss {boss} wave from {queue_list['cwave'][boss-1]} to {wave}")
            queue_list['cwave'][boss-1] = wave
        
        with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], ql_fn), 'w+') as f:
            f.write(json.dumps(queue_list, indent=4))
        
        await self.update_notice(clan_prop, queue_list, guild_prop, ctx.guild, ql_fn, False)

    @queue.command(aliases=['n'])
    async def notice(self, ctx):
        IS_VALID, IS_LEADER, clan_prop, queue_list, guild_prop, ql_fn = self.validate_queue_request(ctx)
        if not IS_LEADER:
            return
        
        await self.update_notice(clan_prop, queue_list, guild_prop, ctx.guild, ql_fn, True)
        await ctx.channel.send('Notice has been updated')

    async def update_notice(self, cp, ql, gp, guild, ql_fn, is_new):
        # fetch channel
        if not cp['channel_notice']:
            return
        channel = guild.get_channel(int(cp['channel_notice']))
        if not channel:
            return
        
        embeds = [
            self.embed_hits(guild, cp, ql),
            self.embed_q_ot(guild, gp, cp, ql)
        ]
        
        msg = None
        if not cp['notice_msg']:
            is_new = True
        else:
            try:
                msg = await channel.fetch_message(int(cp['notice_msg']))
            except NotFound:
                msg = None
        
        if is_new:
            if msg:
                await msg.delete()

            msg = await channel.send(embeds=embeds)
            cp['notice_msg'] = msg.id
        else:
            if msg:
                await msg.edit(embeds=embeds)
            else:
                msg = await channel.send(embeds=embeds)
                cp['notice_msg'] = msg.id
        
        gp['clans'][cp['subguild_id']] = cp
        with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{guild.id}.json"), 'w+') as f:
            f.write(json.dumps(gp, indent=4))
        
    def embed_q_ot(self, guild, gp, cp, ql, author=None):
        SETTINGS = cp['settings']
        embed = {
            "title": f"CB Queue Report",
            "descr": (f"Clan #{cp['subguild_id']}'s" if not cp['name'] else f"{cp['name'].title()}'s") + \
                " CB queue report. Use `.q` to pull this up. Use `.q help` if you need help. Happy clan battling!" + \
                    (f"\n **Global minimum wave is: {min(ql['cwave'])}**" if SETTINGS['b_wave'] else '') + \
                    (f"\n **Timeout is {SETTINGS['timeout']}min**" if SETTINGS['b_timeout'] else ''),
            "footer": {'text': 'CB Queue'},
            "fields": []
        }
        queues = []
        ot = []
        for entry in ql['queue']:
            entry['name'] = guild.get_member(int(entry['id'])).name
            if entry['type'] == 'queue':
                queues.append(entry)
            else:
                ot.append(entry)
        
        # sort
        # queues - timestamp boss wave name is_ot
        # queues - name ot
        queues.sort(key=lambda x: (x['payload']['boss'], x['payload']['wave'], x['timestamp'], x['name'], x['payload']['is_ot']))
        ot.sort(key=lambda x: (x['name'], x['payload']['ot']))

        # queues
        for bn in range(5):
            members = []
            wave = []
            ts = []
            for entry in [i for i in queues if i['payload']['boss'] == (bn + 1)]:
                cw = ql['cwave'][bn]
                if author:
                    if entry['id'] == str(author.id):
                        members.append(f"**{entry['name']}**")
                    else:
                        members.append(f"{entry['name']}")
                else:
                    members.append(f"{entry['name']}")

                if SETTINGS['b_wave']:
                    if entry['payload']['wave'] is None:
                        wave.append('N/A')
                    else:
                        wave.append(str(entry['payload']['wave']) + (" (Curr.)" if entry['payload']['wave'] == cw else '') + (" (Past)" if entry['payload']['wave'] < cw else ''))
                if SETTINGS['b_timeout']:
                    ts.append(f"<t:{entry['timestamp']}:R>")
            
            embed['fields'].append({
                'name': ut.SPACE,
                'value': f"{NUM[bn]} **Boss {bn+1} " + (f" - {gp['bosses'][bn]}** " if gp['bosses'][bn] else '** ') + (f"\nActive wave (現在の周目): {ql['cwave'][bn]}" if SETTINGS['b_wave'] else ''),
                'inline': False
            })
            if members:
                embed['fields'].append({
                    'name': 'Name',
                    'value': '\n'.join(members)
                })
            if wave and SETTINGS['b_wave']:
                embed['fields'].append({
                    'name': 'Wave',
                    'value': '\n'.join(wave)
                })
            if ts and SETTINGS['b_timeout']:
                embed['fields'].append({
                    'name': 'Timeout',
                    'value': '\n'.join(ts)
                })
        
        if ot and SETTINGS['b_ot']:
            d = {}
            for entry in ot:
                temp = d.get(entry['id'], {'name':None, 'ot': []})
                temp['name'] = entry['name']
                temp['ot'].append(str(entry['payload']['ot']))
                d[entry['id']] = temp
            
            members = []
            ots = []
            for id, vd in d.items():
                if author:
                    if id == str(author.id):
                        members.append(f"**{vd['name']}**")
                    else:
                        members.append(f"{vd['name']}")
                else:
                    members.append(f"{vd['name']}")
                ots.append(', '.join(vd['ot']))
            
            embed['fields'].append({
                'name': ut.SPACE,
                'value': "> **Overtimes (残り時間)**",
                'inline': False
            })
            if members:
                embed['fields'].append({
                    'name': 'Name',
                    'value': '\n'.join(members)
                })
            if ots:
                embed['fields'].append({
                    'name': 'Time(s)',
                    'value': '\n'.join(ots)
                })
        
        return ut.embed_contructor(**embed)
    
    def embed_hits(self, guild, cp, ql):
        embed = {
            "title": f"CB Roster",
            "descr": (f"Clan #{cp['subguild_id']}'s" if not cp['name'] else f"{cp['name'].title()}'s") + \
                " CB Roster.",
            "footer": {'text': 'CB Roster'},
            "fields": []
        }
        t_members = self.get_members(guild, cp['role_member'])
        hits_remaining = [[],[],[],[]] # 0 hits, 1 hit, 2 hits, 3+ hits

        for member in t_members:
            details = {}
            details['name'] = member.name
            details['hits_done'] = ql['done'].count(str(member.id))
            details['hits_unresolved'] = len([i for i in ql['queue'] if i['id'] == str(member.id) and i['type'] == 'queue'])
            details['ots'] = [i['payload']['ot'] for i in ql['queue'] if i['id'] == str(member.id) and i['type'] == 'ot']

            k = details['hits_done'] if details['hits_done'] <= 3 else 3
            hits_remaining[k].append(details)

        for i in range(4):
            hits_rem = 3-i
            bracket = hits_remaining[i]
            bracket.sort(key=lambda x: x['name'])
            members = []
            hits_ur = []
            ots     = []

            for member in bracket:
                members.append(member['name'])
                hits_ur.append(str(member['hits_unresolved']))
                ots.append(', '.join([str(i) for i in sorted(member['ots'])]) if member['ots'] else ut.SPACE)
            
            embed['fields'].append({
                'name': ut.SPACE,
                'value': f"> **{hits_rem} Hits remaining ({len(bracket)}/{len(t_members)})**\n残{hits_rem}凸 {len(t_members)}人",
                'inline': False
            })
            if members:
                embed['fields'].append({
                    'name': 'Name',
                    'value': '\n'.join(members)
                })
            if hits_ur:
                embed['fields'].append({
                    'name': 'Active Queues',
                    'value': '\n'.join(hits_ur)
                })
            if ots:
                embed['fields'].append({
                    'name': 'OTs',
                    'value': '\n'.join(ots)
                })
        
        return ut.embed_contructor(**embed)

    @queue.command(aliases=['r'])
    async def reset(self, ctx, *, options=None):
        # .q reset (boss) (wave) (hits) | (all)
        # .ot reset all
        channel = ctx.channel
        IS_VALID, IS_LEADER, clan_prop, queue_list, guild_prop, ql_fn = self.validate_queue_request(ctx)
        if not IS_LEADER:
            return
        
        Q_MODE = 'q' in ctx.invoked_parents or 'queue' in ctx.invoked_parents
        
        if Q_MODE:
            if not options:
                await channel.send(f"No input. See `.q h(elp) {clan_prop['subguild_id']} admin` for syntax.")
                return
            
            options = [i.strip() for i in options.lower().split() if i.strip()]
            if options[0].startswith('a'):
                to_remove = queue_list['queue'].copy()
                queue_list['queue'] = []
            elif options[0].startswith('h'):
                queue_list['done'] = []
                with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], ql_fn), 'w+') as f:
                    f.write(json.dumps(queue_list, indent=4))
        
                await self.update_notice(clan_prop, queue_list, guild_prop, ctx.guild, ql_fn, False)
                await channel.send('Successfully reset registered hits')
                return
            else:
                BOSS = 'ALL'
                WAVE = 'ALL'
                for option in options:
                    try:
                        if option.startswith('w'):
                            option = option[1:]
                            mode = 'w'
                        elif option.startswith('b'):
                            option = option[1:]
                            mode = 'b'
                        else:
                            await channel.send(f"invalid option: {option}")
                            return
                        
                        if option:
                            n = int(option)
                            if mode == 'w':
                                WAVE = n
                                if WAVE < 0:
                                    await channel.send("Failed to reset: invalid wave")
                                    return
                            else:
                                BOSS = n
                                if BOSS < 0 or BOSS > 5:
                                    await channel.send("Failed to reset: boss number out of range")
                                    return
                    
                    except ValueError:
                        await channel.send('Could not reset: Failed to read boss or wave number')
                        return
                    
                to_remove = []
                if BOSS == 'ALL' and WAVE == 'ALL':
                    to_remove = [i for i in queue_list['queue'] if i['type'] == 'queue']
                elif BOSS == 'ALL':
                    to_remove = [i for i in queue_list['queue'] if i['type'] == 'queue' and i['payload']['wave'] == WAVE]
                elif WAVE == 'ALL':
                    to_remove = [i for i in queue_list['queue'] if i['type'] == 'queue' and i['payload']['boss'] == BOSS]
                else:
                    to_remove = [i for i in queue_list['queue'] if i['type'] == 'queue' and i['payload']['boss'] == BOSS and i['payload']['wave'] == WAVE]

                for item in to_remove:
                    queue_list['queue'].pop(queue_list['queue'].index(item))
            
            await channel.send(f"Removed {len(to_remove)} entries from queue")

        else:
            if not options:
                await channel.send("No input")
                return
            #elif not options.startswith('a'):
            #    await channel.send("Failed to reset: invalid input")
            #    return
            else:
                to_remove = [i for i in queue_list['queue'] if i['type'] == 'ot']
                for item in to_remove:
                    queue_list['queue'].pop(queue_list['queue'].index(item))
            
            await channel.send(f"Removed {len(to_remove)} entries from OT")
        
        with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], ql_fn), 'w+') as f:
            f.write(json.dumps(queue_list, indent=4))
        
        await self.update_notice(clan_prop, queue_list, guild_prop, ctx.guild, ql_fn, False)

    @queue.command(aliases=['h'])
    async def help(self, ctx, *, option=None):
        channel = ctx.channel
        author = ctx.author
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{ctx.guild.id}.json")) as gpf:
                gp = json.load(gpf)
        except:
            await channel.send("Did not find/failed to open guild preferences. Use `.guild` to see all subguilds in this guild\n"\
                "Set them via `.guild set (subguild_id)` or create a new guild profile via `.guild new`.")
            return

        ADMIN_MODE = False
        # admin?
        if option:
            option = [i.strip() for i in option.lower().split() if i.strip()]
            if option[-1] == 'admin':
                ADMIN_MODE = True
                option.pop(-1)

        if not option:
            # try to figure out which clan author is from
            present_member_roles = [i['role_member'] for i in gp['clans'].values() if i['role_member']]
            found = self.check_roles(present_member_roles, author)
            channel_role = gp['index'].get(str(channel.id), None)
            channel_role = gp['clans'].get(channel_role, None)
            
            if not found:
                await channel.send("Could not display help: did not find the subguild you're part of "+self.client.emotes['ames'])
                return
            elif len(found) > 1:
                if channel_role:
                    if not int(channel_role['role_member']) in [i.id for i in found]:
                        await channel.send("Could not display help: you are a member of multiple subguilds - to disambiguate use `.q h(elp) [subguild_id/name]`")
                        return
                    else:
                        cp = channel_role
                else:
                    await channel.send("Could not display help: you are a member of multiple subguilds - to disambiguate use `.q h(elp) [subguild_id/name]`")
                    return
            else:
                cp = [i for i in gp['clans'].values() if i['role_member'] == str(found[0].id)][0]
        else:
            option = ' '.join(option)

            try:
                subguild_id = str(int(option))
            except:
                key = gp['index'].get(option, None)
                key = key if key else gp['clans'].get(option, None)
                if not key:
                    await channel.send('Could not display help: Failed to process subguild_key '+self.client.emotes['ames'])
                    return
                cp = gp['clans'].get(key, None)
            else:
                cp = gp['clans'].get(subguild_id, None)

            if not cp:
                await channel.send('Could not display help: Failed to process subguild_key '+self.client.emotes['ames'])
                return
        
        if ADMIN_MODE and len(self.check_roles([cp['role_leader']], author)) == 0 :
            await channel.send('You do not have perms to see admin commands '+self.client.emotes['ames'])
            return
        
        base, embeds = self.make_help_embeds(cp)
        await channel.send(base)
        if ADMIN_MODE:
            await channel.send(embeds[-1][0])
            await channel.send(embeds[-1][1])
        else:
            await channel.send(embeds[0][0])
            await channel.send(embeds[0][1])

    def make_help_embeds(self, cp):
        SETTINGS = cp['settings']
        START = '```css\n'
        END = '```'

        base = \
            f"> **Clan #{cp['subguild_id']}** ({cp['name'] if cp['name'] else 'no name set'}) CB Help\n"\
            "Access this via `.q h(elp) (subguild_key)` or `.q h(elp) (subguild_key) admin` for the admin version. "\
            "This help section is tailored to your CB settings. You may review them with `.guild [name/subguild_id]`."

        q_title = '> **Command: `queue`**'
        q_base_admin = \
            '[Command Syntax] .queue #proxy [mode]\n'\
                '\t[alias] .q\n'\
                    '\t\tPrimary queue command. Queues/unqueues from bosses. Use .q to view current queues.\n'\
                '\t#proxy [optional]\n'\
                    '\t\tMust be a mention. Perform the command in stead of mentioned user.'
        q_base_standard = \
            '[Command Syntax] .queue [mode]\n'\
                '\t[alias] .q\n'\
                    '\t\tPrimary queue command. Queues/unqueues from bosses. Use .q to view current queues.'
        
        q_mode_norm_base = \
            '\n[mode] default\n'\
                '\t[Syntax] .queue #boss #suffixes\n'\
                '\t[e.g.] .q 1 ot done'
        q_mode_norm_base_wave = \
            '\n[mode] default\n'\
                '\t[Syntax] .queue #boss #wave #suffixes\n'\
                '\t[i.e.] .q 1 12 ot done'

        q_mode_norm_boss = \
            '\t#boss [optional]\n'\
                '\t\tRequested boss number. Must be between 1 and 5.'
        q_mode_norm_wave = \
            '\t#wave [conditional]\n'\
                '\t\tMay only be used when #boss is present. Requested wave number. '\
                "Can be relative [i.e.] +1 for next wave or -1 for previous wave. Defaults to current wave if omitted."
        q_mode_norm_suffix = \
            '\t#suffixes [optional]\n'\
                '\t\t1. [d(one)] Resolve the requested queue entry. Increments your daily hit count if applicable. '\
                'If this is the only option, resolves all active queues [i.e.] .q d\n'\
                '\t\t2. [c(ancel)] Cancel the requested queue entry without incrementing your daily hit count'
        if SETTINGS['b_ot']:
            q_mode_norm_suffix += '\n\t\t3. [o(t)] Flag the entry to be using OT. Will not increment daily hit count when resolving.'
        if SETTINGS['b_wave']:
            q_mode_norm_suffix += '\n\t\t4. [k(ill)] OR [x] Unqueue and announce the boss kill. Increments boss wave.' if SETTINGS['b_ot'] else \
                '\n\t\t3. [k(ill)] OR [x] Unqueue and announce the boss kill. Increments boss wave.'
        
        q_mode_list = \
            '\n[mode] list\n'\
                '\t[Syntax] .queue list\n'\
                '\t[alias] l\n'\
                    '\t\tShow your active queues.'
        
        q_mode_hit = \
            '\n[mode] hit\n'\
                '\t[Syntax] .queue hit #num\n'\
                '\t[alias] h\n'\
                    '\t\tIncrememnt/decrement your daily hits without queueing.\n'\
                '\t#num [optional]\n'\
                    '\t\tIncrememnt/decrement your daily hits by #num. Defaults to 1 if omitted.'
        
        q_mode_setwave = \
            '\n[mode] setwave\n'\
                '\t[Syntax] .queue setwave #boss #wave\n'\
                '\t[alias] sw\n'\
                    '\t\tSets the wave for the requested boss.\n'\
                '\t#boss [required]\n'\
                    '\t\tRequested boss number. Use [all] to set all bosses.\n'\
                '\t#wave [required]\n'\
                    '\t\tRequested wave number. Can be relative [i.e.] +1 for next wave or -1 for previous wave.' 

        q_mode_reset = \
            '\n[mode] reset\n'\
                '\t[Syntax] .queue reset b#boss_num w#wave_num\n'\
                '\t[alias] r\n'\
                '\t[i.e.] .q r b1 w11\n'\
                    '\t\tReset queues according to input\n'\
                '\tb#boss_num [required]\n'\
                    '\t\tRequested boss number. If omitted, [i.e.] .q r b, all bosses will be assumed\n'\
                '\tw#wave_num [conditional]\n'\
                    '\t\tRequested wave number. Can be relative [i.e.] +1, -1 for next/previous wave respectively.'
        
        ot_title = '> **Command: `ot`**'
        ot_base_admin = \
            '[Command Syntax] .ot #proxy [mode]\n'\
                    '\t\tPrimary OT command. Manages OT durations. Use .q to view current OTs.\n'\
                '\t#proxy [optional]\n'\
                    '\t\tMust be a mention. Perform the command in stead of mentioned user.'
        ot_base_standard = \
            '[Command Syntax] .ot [mode]\n'\
                    '\t\tPrimary OT command. Manages OT durations. Use .q to view current OTs.'

        ot_mode_norm_base = \
            '\n[mode] default\n'\
                '\t[Syntax] .ot #time #suffixes\n'\
                '\t[i.e.] .ot 30 done\n'\
                    '\t\tRecords/removes OT.\n'\
                '\t#time [conditional]\n'\
                    '\t\tOT seconds you wish to record.\n'\
                '\t#suffix [conditional]\n'\
                    '\t\t1. [d(one)] Resolve the requested OT entry. If this is the only option, resolves all active OTs [i.e.] .ot d\n'\
            '\n[mode] list\n'\
                '\t[Syntax] .ot list\n'\
                '\t[alias] l\n'\
                    '\t\tShow your active OTs.'
        
        ot_mode_norm_reset = \
            '\n[mode] reset\n'\
                '\t[Syntax] .ot reset #anything\n'\
                '\t[alias] r\n'\
                    '\t\tResets all OT entries.'
        
        # construct
        standard_q = []
        admin_q = []

        # queue
        standard_q += [q_title, START, q_base_standard]
        admin_q += [q_title, START, q_base_admin]
        if SETTINGS['b_wave']:
            standard_q += [q_mode_norm_base_wave]
            admin_q += [q_mode_norm_base_wave]
        else:
            standard_q += [q_mode_norm_base]
            admin_q += [q_mode_norm_base]

        standard_q += [q_mode_norm_boss]
        admin_q += [q_mode_norm_boss]

        if SETTINGS['b_wave']:
            standard_q += [q_mode_norm_wave]
            admin_q += [q_mode_norm_wave]
        
        standard_q += [q_mode_norm_suffix, q_mode_list, q_mode_hit, END]
        admin_q += [q_mode_norm_suffix, q_mode_list, q_mode_hit, q_mode_setwave, q_mode_reset, END]

        # ot
        standard_ot = [ot_title, START, ot_base_standard, ot_mode_norm_base, END]
        admin_ot = [ot_title, START, ot_base_admin, ot_mode_norm_base, ot_mode_norm_reset, END]

        return base, [['\n'.join(standard_q),'\n'.join(standard_ot)], ['\n'.join(admin_q),'\n'.join(admin_ot)]]
        
    def make_help_embeds_old(self, cp):
        SETTINGS = cp['settings']
        base = {
            'title': f"Clan #{cp['subguild_id']} ({cp['name'] if cp['name'] else 'no name set'}) CB Help",
            'descr': "CB Help. Access this embed via `.q h(elp) (subguild_key)` or `.q h(elp) (subguild_key) admin` for the admin version.",
            'footer': {'text': 'CB Help'},
            'fields': []
        }

        standard = deepcopy(base)
        admin = deepcopy(base)
        
        admin['fields'] += [
                {
                'name': 'CB settings',
                'value': 'Parameters below dictate how this embed is constructed',
                'inline': False
            },
            {
                'name': 'Track Overtime',
                'value': 'Yes' if SETTINGS['b_ot'] else 'No'
            },
            {
                'name': 'Track Waves',
                'value': 'Yes' if SETTINGS['b_wave'] else 'No'
            },
            {
                'name': 'Auto-Timeout',
                'value': 'Yes' if SETTINGS['b_timeout'] else 'No'
            },
            {
                'name': 'Auto Timeout Interval',
                'value': f"{SETTINGS['timeout']}min"
            },
            {
                'name': 'Empty Queue Quick Msg.',
                'value': 'Yes' if SETTINGS['b_timeout'] else 'No'
            }
        ]
        
        # queue command
        # standard - .q (subcommands) (boss) (wave) (done|cancel|kill|ot)
        queue_standard = [ 
            {
                'name': "> Command: `queue`\nSyntax: "+("`.queue (subcommand) (boss) <wave> (suffix)`" if SETTINGS['b_wave'] else "`.queue (prefix) (boss) (suffix)`"),
                'value': 'Command alias: `.q`\nPrimary queue command. Queues/unqueues from bosses. Use `.q` to view all queues.',
                'inline': False
            },
            {
                'name': '(Optional Arg) `boss`',
                'value': "Requested boss number. Must be an integer between 1 and 5.",
                'inline': False
            }
        ]
        queue_admin = [ 
            {
                'name': "> Command: `queue`\nSyntax: "+("`.queue (prefix/subcommand) (boss) <wave> (suffix)`" if SETTINGS['b_wave'] else "`.queue (prefix/subcommand) (suffix)`") ,
                'value': 'Command alias: `.q`\nPrimary queue command. Queues/unqueues from bosses. Use `.q` to view all queues.',
                'inline': False
            },
            {
                'name': '(Optional Arg) `prefix`: `discord@member`',
                'value': "`discord@member`: Perform the rest of the command in place of mentioned member. Form must be a discord member mention.",
                'inline': False
            },
            {
                'name': '(Optional Arg) `boss`',
                'value': "Requested boss number. Must be an integer between 1 and 5.",
                'inline': False
            }
        ]
        if SETTINGS['b_wave']:
            queue_wave = [
                {
                    'name': '(Conditional Arg) `wave`',
                    'value': 
                        "Can only specified if `boss` is present. Requested wave number. Must be an integer larger than 0 unless describing a relative wave:  - e.g. `+1` for next wave. "\
                        "If omitted, will default to current boss's wave.",
                    'inline': False
                },
                {
                    'name': '(Optional Arg) `suffix`: `ot`, `kill`, `done`, `cancel`',
                    'value': 
                        "`o(t)`: Flag queue request as a queue using OT. Will not increment daily hit count when resolving.\n"\
                        "`k(ill)` or `x`: Unqueue and kill announce the boss. Increments boss's wave if valid.\n"\
                        "`d(one)`: Unqueue from current boss-wave. This will increment your daily hit count. When used with no other args, i.e. `.q d`, you will be unqueued from all bosses.\n"\
                        "`c(ancel)`: Unqueue your boss-wave queue withour incrementing daily hit count.",
                    'inline': False
                }
            ]
        else:
            queue_wave = [
                {
                    'name': '(Optional Arg) `suffix`: `ot`, `done`, `cancel`',
                    'value': 
                        "`o(t)`: Flag queue request as a queue using OT. Will not increment daily hit count when resolving.\n"\
                        "`d(one)`: Unqueue from current boss-wave. This will increment your daily hit count."\
                            "When used with no other args, i.e. `.q d`, you will be unqueued from all bosses.\n"\
                        "`c(ancel)`: Unqueue your boss-wave queue withour incrementing daily hit count.",
                    'inline': False
                }
            ]

        queue_wave.append(
            {
                'name': '> Subcommand: `queue.list`\nSyntax: `.queue list`',
                'value': "Subcommand alias: `.queue l`\nShow your active queues.",
                'inline': False
            }
        )
        
        queue_standard += queue_wave
        queue_admin += queue_wave

        queue_admin += [ 
            {
                'name': '> Subcommand: `queue.setwave`\nSyntax: `.queue setwave [boss] [wave]`',
                'value': 'Subcommand alias: `.queue sw`\nSets the wave for the requested boss.',
                'inline': False
            },
            {
                'name': '(Required Arg) `boss`',
                'value': "Requested boss number. Can be an integer between 1 and 5, or 'all' to set all bosses.",
                'inline': False
            },
            {
                'name': '(Required Arg) `wave`',
                'value': 
                    "Requested wave number. Must be an integer larger than 0 unless describing a relative wave:  - e.g. `+1` to increment all bosses by 1.",
                'inline': False
            },
            {
                'name': '> Subcommand: `queue.reset`\nSyntax: `.queue reset b<boss_num> w<wave_num>`',
                'value': 'Subcommand alias: `.queue r`\nClears all queue.',
                'inline': False
            },
            {
                'name': '(Conditional Arg) `b(boss_num)`',
                'value': "Requested boss number. Must be an integer between 1 and 5, e.g. `b1`. If no number is specified, i.e. `b`, all bosses will be assumed.",
                'inline': False
            },
            {
                'name': '(Required Arg) `wave`',
                'value': 
                    "Requested wave number. Must be an integer larger than 0 unless describing a relative wave:  - e.g. `+1` to increment all bosses by 1.",
                'inline': False
            },
            {
                'name': '> Subcommand: `queue.notice`\nSyntax: `.queue notice`',
                'value': 'Subcommand alias: `.queue n`\nForce update the CB summary.',
                'inline': False
            }
        ]

        standard['fields'] += queue_standard
        admin['fields'] += queue_admin

        # OT
        if SETTINGS['b_ot']:
            queue_standard = [ 
                {
                    'name': "> Command: `ot`\nSyntax: `.ot (subcommand) <time> <suffix>`",
                    'value': 'Command alias: n/a',
                    'inline': False
                },
                {
                    'name': '(Conditional Arg) `time`',
                    'value': "The requested overtime in seconds.",
                    'inline': False
                },
                {
                    'name': '(Conditional Arg) `suffix`: `done`',
                    'value': "`d(one)`: Delist your OT entry."\
                        "When the command contains only this suffix i.e. `.ot done`, all your OT entries will be delisted.",
                    'inline': False
                },
                {
                    'name': '> Subcommand: `ot.list`\nSyntax: `.ot list`',
                    'value': "Subcommand alias: `.ot l`\nShow your active OTs.",
                    'inline': False
                }
            ]
            queue_admin = [ 
                {
                    'name': "> Command: `ot`\nSyntax: `.ot (prefix/subcommand) <time> <suffix>`",
                    'value': 'Command alias: n/a',
                    'inline': False
                },
                {
                    'name': '(Optional Arg) `prefix`: `list`, `discord@member`',
                    'value': "`l(ist)`: Show your listed OTs.\n"\
                        "`discord@member`: Perform the rest of the command in place of mentioned member. Form must be a discord member mention.",
                    'inline': False
                },
                {
                    'name': '(Conditional Arg) `time`',
                    'value': "The requested overtime in seconds.",
                    'inline': False
                },
                {
                    'name': '(Conditional Arg) `suffix`: `done`',
                    'value': "`d(one)`: Delist your OT entry."\
                        "When the command contains only this suffix i.e. `.ot done`, all your OT entries will be delisted.",
                    'inline': False
                },
                {
                    'name': '> Subcommand: `ot.list`\nSyntax: `.ot list`',
                    'value': "Subcommand alias: `.ot l`\nShow your active OTs.",
                    'inline': False
                },
                {
                    'name': '> Subcommand: `ot.reset`\nSyntax: `.ot reset`',
                    'value': 'Subcommand alias: `.ot r`\nClears all OT entries.',
                    'inline': False
                }
            ]

            standard['fields'] += queue_standard
            admin['fields'] += queue_admin
        
        return [ut.embed_contructor(**standard), ut.embed_contructor(**admin)]

    @queue.command()
    async def test(self, ctx, *, option=None):
        channel = ctx.channel
        author = ctx.author

        # load guild prefs
        try:
            with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{ctx.guild.id}.json")) as gpf:
                gp = json.load(gpf)
        except:
            await channel.send("Did not find/failed to open guild preferences. Use `.guild` to see all subguilds in this guild\n"\
                "Set them via `.guild set (subguild_id)` or create a new guild profile via `.guild new`.")
            return
        
        # parse input options and check whether to set ADMIN or not
        ADMIN_MODE = False
        if option:
            option = [i.strip() for i in option.lower().split() if i.strip()]
            if option[-1] == 'admin':
                ADMIN_MODE = True
                option.pop(-1)
        
        # check which clan property to load
        # explicit clan ID given
        if option:
            cp = gp['clans'].get(option[0], None)
            if not cp:
                await channel.send(f"Failed to fetch help via subguild ID {option[0]}")
                return
        # if not provided, match channel then all indicies
        else:
            found = self.check_roles(list(gp['index'].keys()), author, channel, gp)
            if not found:
                await channel.send("Failed to load clan-specific help: Could not determine your clan affiliation!")
                return
            else:
                cp = gp['clans'][gp['index'][str(found[0].id)]]
            
        # if admin mode, check perm
        if ADMIN_MODE and not self.check_roles([cp['role_leader']], author):
            await channel.send("You do not have permission to view extra commands")
            return
        
        # fetch embeds and send
        await channel.send(embed=self.test_make_q_embed(cp, ADMIN_MODE))

    def test_make_q_embed(self, cp, admin):
        embed = {
            'title': f"CB Queue Help - {cp['name']} (Clan #{cp['subguild_id']})",
            'descr': "Queue help for CB. This page is tailored to your clan's set CB parameters. Access this via `.q help <subguild id>`. Append `admin` to the end to view the admin version.",
            'footer': {'text': 'CB Queue'},
            'fields': []
        }
        if not admin:
            fields = [
                {
                    'name': 'Command Syntax: Queue',
                    'value': 
                        '`.queue [mode]`\n'\
                        'Aliases: `q`',
                    'inline': False
                },
                {
                    'name': '> [mode] default',
                    'value': 
                        '`.queue [boss number] [wave] [suffixes]`\n'\
                        'Primary queue command. Queues/unqueues from bosses. Use `.q` to view current queues. Any number of valid `[suffix]` can be entered but makes sure they make sense.',
                    'inline': False
                },
                {
                    'name': '`[boss number]` (optional)',
                    'value': 
                        'The requested boss number. Can be omitted depending on the intent.',
                    'inline': True
                },
                {
                    'name': '`[wave]` (optional)',
                    'value': 
                        'The requested wave number. Can be omitted. If omitted, will default to current active wave. Accepts relative wave numbers, e.g. `+1`, `-1` for the next wave and previous wave respectively.',
                    'inline': True
                },
                {
                    'name': '[suffix] `done` (optional)',
                    'value': 
                        'Alias: `d`\n'\
                        'Resolve the requested hit. If `[boss number]` and `[wave]` are omitted, resolve all active queues. If auto increment is set, you will be incremented once for each valid hit.',
                    'inline': True
                },
                {
                    'name': '[suffix] `cancel` (optional)',
                    'value': 
                        'Alias: `c`\n'\
                        'Cancel the requested hit. If `[boss number]` and `[wave]` are omitted, cancel all active queues. This will not increment any hits.',
                    'inline': True
                },
                {
                    'name': '[suffix] `kill` (optional)',
                    'value': 
                        'Alias: `k`, `x`\n'\
                        'Increment the wave for the boss. `[boss number]` is required. This will increment your hit count if its valid and will ping all members queued for the next wave.',
                    'inline': True
                },
                {
                    'name': '[suffix] `ot` (optional)',
                    'value': 
                        'Flag the request as using overtime. Anytime you resolve a hit or hits, all hits with `ot` flag will not increment your hit counter. This must be done for both initial queue and queue resolve actions.',
                    'inline': True
                },
                {
                    'name': '> [mode] `list`',
                    'value': 
                        '`.queue list`\n'\
                        'Alias: `l`\n'\
                        'Display all your active queues.',
                    'inline': False
                },
                {
                    'name': '> [mode] `hit`',
                    'value': 
                        '`.queue hit [hits]`\n'\
                        'Alias: `h`\n'\
                        'Increment your daily hit counter `[hit]` __number of times__ (not your hit number), e.g. `.q h 3` means +3 to your hit counter. `[hit]` will default to 1 if omitted.',
                    'inline': False
                }
            ]


            embed['fields'] += fields
            return ut.embed_contructor(**embed)
        
    def cog_unload(self):
        self.timeout_checker.cancel()
        self.new_day_checker.cancel()
    
    @tasks.loop(seconds=60)
    async def timeout_checker(self):
        try:
            # iterate through guild parameter files
            for gpfn in glob(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], '*.json')):            
                # fetch guild
                guild_id = gpfn.split('\\')[-1].split('.')[0]
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    continue
                
                # load guild parameters
                with open(gpfn) as gpf:
                    gp = json.load(gpf)

                # iterate through clans in guild parameter file
                for cp in gp['clans'].values():
                    SETTINGS = cp['settings']

                    # skip if notice channel or channel is invalid or b_timeout is false
                    notice_channel = cp['channel_notice']
                    if not notice_channel:
                        continue
                    elif not SETTINGS['b_timeout']:
                        continue
                    notice_channel = guild.get_channel(int(notice_channel))
                    if not notice_channel:
                        continue
                    
                    # load queue
                    qlfn = f"{guild.id}-{cp['subguild_id']}.json"
                    try:
                        with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], qlfn)) as qlf:
                            ql = json.load(qlf)
                    except:
                        continue

                    # prune
                    to_remove = []
                    ct = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
                    threshold = SETTINGS['timeout'] * 60
                    for entry in ql['queue']:
                        if not entry['type'] == 'queue':
                            continue
                        elif (ct - entry['timestamp']) > threshold:
                            to_remove.append(entry)

                    for entry in to_remove:
                        ql['queue'].pop(ql['queue'].index(entry))
                    
                    # save and update channel
                    with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], qlfn), 'w+') as qlf:
                        qlf.write(json.dumps(ql, indent=4))

                    await self.update_notice(cp, ql, gp, guild, qlfn, False)
        
        except Exception as e:
            await self.logger.report("[timeout] process failed:", e)
                
    @tasks.loop(seconds=60)
    async def new_day_checker(self):
        try:
            # offset from timeout_checker by 10s just in case
            await asyncio.sleep(10)

            # 0500 - 0505 JST
            threshold_min = 5 * 60 * 60
            #threshold_min = (11 + 55/60) * 60 * 60
            threshold_max = threshold_min + 5 * 60

            ct_jp = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
            ct_jp_relative = ct_jp.hour*60*60 + ct_jp.minute*60 + ct_jp.second

            #print('current', ct_jp_relative, 'target', threshold_min)

            # iterate through queues
            for qlfn in glob(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], '*.json')):
                with open(qlfn) as qlf:
                    ql = json.load(qlf)

                if ct_jp_relative >= threshold_min and ct_jp_relative < threshold_max:
                    #print('threshold reached')
                    # reset 
                    if not ql.get('reset', False):
                        ql['done']  = []
                        ql['reset'] = True

                        # attempt to notify main channel
                        #try:
                        #    guild_id, subguild_id = qlfn.split('/')[-1].split('.')[0].split('-')
                        #    with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], guild_id+'.json')) as gcf:
                        #        gc = json.load(gcf)
                        #    
                        #    clan_config = gc['clans'][subguild_id]
                        #    requested_channel = await self.client.fetch_channel(int(gc['channel_primary']))
                        #    await requested_channel.send('')

                        await self.logger.report('[reset] successfully reset queues for', qlfn)

                    else:
                        continue
                else:
                    if not ql.get('reset', True):
                        continue
                    else:
                        ql['reset'] = False
                
                # save
                with open(qlfn, 'w+') as qlf:
                    qlf.write(json.dumps(ql, indent=4))

        except Exception as e:
            await self.logger.report("[reset] process failed:", e)
    
    @commands.command()
    async def boss(self, ctx, *, options):
        channel = ctx.channel
        IS_VALID, IS_LEADER, clan_prop, queue_list, guild_prop, ql_fn = self.validate_queue_request(ctx)

        if not IS_LEADER:
            return
        
        # process options
        options = [i.strip() for i in options.split() if i.strip()]
        
        # reset?
        if options[0].lower() == 'reset':
            guild_prop['bosses'] = [None, None, None, None, None]
            await channel.send('Reset all boss names '+self.client.emotes['sarenh'])
        else:
            # boss num
            try:
                bn = int(options.pop(0))
            except:
                await channel.send('Failed to read boss number '+self.client.emotes['ames'])
                return
            else:
                name = ' '.join(options)
                name = name if name else None
                guild_prop['bosses'][bn-1] = name
                await channel.send('Set '+self.client.emotes['sarenh'])
        
        with open(ut.full_path(self.rel_path, self.hatsucb_cf['guilds'], f"{ctx.guild.id}.json"), 'w+') as gpf:
            gpf.write(json.dumps(guild_prop, indent=4))
        
        for clan in guild_prop['clans'].values():
            ql_fn = f"{ctx.guild.id}-{clan['subguild_id']}.json"
            try:
                with open(ut.full_path(self.rel_path, self.hatsucb_cf['queues'], ql_fn)) as qlf:
                    ql = json.load(qlf)
            except:
                continue

            await self.update_notice(clan, ql, guild_prop, ctx.guild, ql_fn, False)

    @commands.group(invoke_without_command=True, aliases=['r', 'wr'])
    async def room(self, ctx, *, option=None):
        channel = ctx.channel
        author = ctx.author

        # validate
        IS_VALID, _, clan_prop, _, _, _ = self.validate_queue_request(ctx)
        if not IS_VALID:
            return
        # load room file
        fpath = ut.full_path(self.rel_path, self.hatsucb_cf['rooms'], f"{channel.guild.id}-{clan_prop['subguild_id']}.json")
        try:
            with open(fpath) as f:
                rooms = json.load(f)
        except:
            rooms = tem.fetch('hcb_rooms')
            with open(fpath, 'w+') as f:
                f.write(json.dumps(rooms, indent=4))

        if ctx.invoked_subcommand is None:
            # check author's active rooms 
            if not option:  
                creator, member = self.author_active_rooms(author.id, rooms)

                if not creator and not member:
                    await channel.send("You are currently not in any active rooms. You may create one with: \n`.r [description] ; [damage goal in millions(optional)] ; [your estimated damage in millions(optional)]`")
                else:
                    embed = {
                        'title': f"{author.name}'s active rooms.",
                        'fields': [
                            {
                                'name': 'Room Creator',
                                'value': f"[{creator[0][0]}](https://discord.com/channels/{channel.guild.id}/{channel.id}/{creator[0][1]})" if creator else "-",
                                'inline': False
                            },
                            {
                                'name': 'Room Member',
                                'value': "\n".join([f"[{description}](https://discord.com/channels/{channel.guild.id}/{channel.id}/{message_id})" for description,message_id in member]) \
                                    if member else "-"
                            }
                        ]
                    }
                    await channel.send(embed=ut.embed_contructor(**embed), delete_after=30)
            # new room creation
            else:
                # check if the author is already a room creator
                if author.id in rooms['creators']:
                    await channel.send("You are already a creator of a room! You can only create 1 room at a time. Use `.r` to see your active rooms.")
                    return
                
                option = [i.strip() for i in option.split(';') if i.strip()]
                description = option[0]
                if len(option) == 1:
                    goal = None
                    est = None
                elif len(option) == 2:
                    est = None
                    goal = option[-1].lower().replace('m','').replace('k','')
                    try:
                        goal = float(goal)
                    except:
                        await channel.send("Failed to read goal!")
                        return
                elif len(option) == 3:
                    est = option[-1].lower().replace('m','').replace('k','')
                    goal = option[-2].lower().replace('m','').replace('k','')
                    try:
                        goal = float(goal)
                        est = float(est)
                    except:
                        await channel.send("Failed to read goal or estimated damage!")
                        return
                else:
                    await channel.send("Too many inputs!")
                    return
                
                new_room = tem.fetch('hcb_roomsentry')
                new_room['description'] = description
                new_room['goal'] = goal
                new_room['creator'] = (author.id, False, est)

                message = await channel.send(
                    embed=self.make_room_embed(new_room), 
                    view=self.roomPageView(fpath, self.make_room_embed, self.roomModal, self.validate_queue_request_new, self.client.emotes['bonk'])
                )
                new_room['message_id'] = message.id

                rooms['rooms'][str(message.id)] = new_room
                rooms['creators'] = [room['creator'][0] for room in rooms['rooms'].values()]

                with open(fpath, 'w+') as f:
                    f.write(json.dumps(rooms, indent=4))

    @room.command()
    async def purge(self, ctx):
        channel = ctx.channel

        # validate
        IS_VALID, IS_LEADER, clan_prop, _, _, _ = self.validate_queue_request(ctx)
        if not IS_VALID or not IS_LEADER:
            return
        
        # load room file
        fpath = ut.full_path(self.rel_path, self.hatsucb_cf['rooms'], f"{channel.guild.id}-{clan_prop['subguild_id']}.json")
        try:
            with open(fpath) as f:
                rooms = json.load(f)
        except:
            rooms = tem.fetch('hcb_rooms')
            with open(fpath, 'w+') as f:
                f.write(json.dumps(rooms, indent=4))
        
        # delete rooms
        for room in rooms['rooms'].values():
            try:
                message = await channel.fetch_message(room['message_id'])
            except:
                continue
            else:
                await message.edit(content='This room has been purged '+self.client.emotes['bonk'], embed=None, view=None)
                
        with open(fpath, 'w+') as f:
            f.write(json.dumps(tem.fetch('hcb_rooms'), indent=4))
        
        await channel.send(self.client.emotes['bonk'])
    
    @room.command(alias=['rl'])
    async def relist(self, ctx):
        channel = ctx.channel
        author = ctx.author

        # validate
        IS_VALID, _, clan_prop, _, _, _ = self.validate_queue_request(ctx)
        if not IS_VALID:
            return
        
        # load room file
        fpath = ut.full_path(self.rel_path, self.hatsucb_cf['rooms'], f"{channel.guild.id}-{clan_prop['subguild_id']}.json")
        try:
            with open(fpath) as f:
                rooms = json.load(f)
        except:
            rooms = tem.fetch('hcb_rooms')
            with open(fpath, 'w+') as f:
                f.write(json.dumps(rooms, indent=4))
        
        if not author.id in rooms['creators']:
            await channel.send("Could not relist: You are not the creator of any rooms!")
            return
        else:
            target_room = None
            for room in rooms['rooms'].values():
                if room['creator'][0] == author.id:
                    target_room = room
                    break
            
            if not target_room:
                return
            
            print(rooms['rooms'])
            target_room = rooms['rooms'].pop(str(target_room['message_id']))

            try:
                message = await channel.fetch_message(room['message_id'])
            except:
                pass
            else:
                await message.edit(content='This room has been moved '+self.client.emotes['bonk'], embed=None, view=None)
            
            message = await channel.send(
                embed=self.make_room_embed(target_room), 
                view=self.roomPageView(fpath, self.make_room_embed, self.roomModal, self.validate_queue_request_new, self.client.emotes['bonk'])
            )
            target_room['message_id'] = message.id
            rooms['rooms'][str(message.id)] = target_room
            with open(fpath, 'w+') as f:
                f.write(json.dumps(rooms, indent=4))


    def make_room_embed(self, room):
        creator_prefix = '👑'
        member_prefix_r = '🟢'
        member_prefix_nr = '⚫'

        members = [creator_prefix + f"<@{room['creator'][0]}>"]
        all_dmg = [room['creator'][-1]]

        user = self.client.get_user(room['creator'][0])
        if user:
            avatar = user.display_avatar.url
        else:
            avatar = None

        for member, ready, estdmg in room['members']:
            members.append((member_prefix_r if ready else member_prefix_nr)+f"<@{member}>")
            all_dmg.append(estdmg)

        embed = {
            'title': 'Ready Room',
            'descr': room['description'],
            "fields": [
                {
                    'name': 'Target',
                    'value': f"{sum([i for i in all_dmg if i])} / {room['goal'] if room['goal'] else '-'}",
                    'inline': False
                },
                {
                    'name': 'Members',
                    'value': '\n'.join(members),
                    'inline': True
                },
                {
                    'name': 'Estimated Dmg.',
                    'value': '\n'.join([str(i) if i else '-' for i in all_dmg]),
                    'inline': 'True'
                }
            ]
        }
        
        if avatar:
            embed['thumb'] = avatar

        return ut.embed_contructor(**embed)
    
    def author_active_rooms(self, author_id, rooms):
        creator = []
        member = []
        for room in rooms['rooms'].values():
            if room['creator'][0] == author_id:
                creator.append((room['description'], room['message_id']))
            elif author_id in [i[0] for i in room['members']]:
                member.append((room['description'], room['message_id']))
        
        return creator, member

    class roomPageView(ut.baseViewHandler):
        def __init__(self, fpath, embed, modal, validator, bonk):
            super().__init__(None)
            self.base_id = 'ames_cbRoomPageView_'
            self.bonk = bonk
            self.room = None
            self.fpath = fpath
            self.modal_maker = modal
            self.embed_maker = embed
            self.validator = validator
            self.make_buttons()

        def make_buttons(self):
            buttons = [
                nextcord.ui.Button(
                    custom_id=self.base_id+'join',
                    label='Join',
                    style=nextcord.ButtonStyle.success
                ),
                nextcord.ui.Button(
                    custom_id=self.base_id+'leave',
                    label='Leave',
                    style=nextcord.ButtonStyle.danger
                ),
                nextcord.ui.Button(
                    custom_id=self.base_id+'toggle',
                    label='Un/Ready',
                    style=nextcord.ButtonStyle.primary
                ),
                nextcord.ui.Button(
                    custom_id=self.base_id+'edit',
                    label='Edit',
                    style=nextcord.ButtonStyle.secondary
                ),
                nextcord.ui.Button(
                    custom_id=self.base_id+'muster',
                    label='Muster',
                    style=nextcord.ButtonStyle.success,
                    row=2
                ),
                nextcord.ui.Button(
                    custom_id=self.base_id+'disband',
                    label='Disband',
                    style=nextcord.ButtonStyle.danger,
                    row=2
                )
            ]
            for button in buttons:
                super().add_item(button)

        def roomsf_io(self, room=None):
            try:
                with open(self.fpath) as f:
                    rooms = json.load(f)
            except:
                return None, None

            if not room:
                return rooms['rooms'].get(str(self.message_id), None), rooms
            else:
                rooms['rooms'][str(self.message_id)] = room
                with open(self.fpath, 'w+') as f:
                    f.write(json.dumps(rooms, indent=4))

        async def interaction_check(self, interaction:nextcord.Interaction):
            inter_id = interaction.data.get('custom_id', None)
            action = inter_id.split('_')[-1]

            # validate
            author = interaction.user
            guild = interaction.guild
            channel = interaction.channel
            message = interaction.message

            self.message_id = message.id

            IS_VALID, _, _, _, _, _ = self.validator(guild, channel, author)
            if not IS_VALID:
                return False
                
            # load the room file
            room, rooms = self.roomsf_io()
            if not room or not rooms:
                return False

            # check membership
            IS_CREATOR = author.id == room['creator'][0]
            IS_MEMBER = author.id in [i[0] for i in room['members']]

            ### actions
            # join
            # leave
            # toggle
            # muster
            # disband
            # edit

            if action == 'join' and not (IS_CREATOR or IS_MEMBER):
                await interaction.response.send_modal(self.modal_maker(room, 'join', self))

            elif action == 'leave' and not IS_CREATOR and IS_MEMBER:
                room['members'] = [i for i in room['members'] if i[0] != author.id]

            elif action == 'muster' and IS_CREATOR:
                text = f"Muster call for room **{room['description']}**\n<@{room['creator'][0]}> " + " ".join([f"<@{member}>" for member, ready, _ in room['members'] if ready])
                await interaction.response.send_message(text)
                return True

            elif action == 'disband' and IS_CREATOR:
                await message.edit(content='Room disbanded '+self.bonk, embed=None, view=None)
                rooms['rooms'].pop(str(message.id))
                rooms['creators'] = [room['creator'] for room in rooms['rooms'].values()]
                with open(self.fpath, 'w+') as f:
                    f.write(json.dumps(rooms, indent=4))
                return True
            
            elif action == 'edit':
                if IS_CREATOR:
                    await interaction.response.send_modal(self.modal_maker(room, 'edit_creator', self))

                elif IS_MEMBER:
                    await interaction.response.send_modal(self.modal_maker(room, 'edit_member', self))

                else:
                    return True
            
            elif action == 'toggle' and IS_MEMBER:
                target_index = room['members'].index([i for i in room['members'] if i[0] == author.id][0])
                room['members'][target_index][1] = not room['members'][target_index][1]

            else:
                return True
            
            self.roomsf_io(room)
            await self.update(room, message)
            return True

        async def modal_response(self, message, user_id, result_dict):
            room, _ = self.roomsf_io()

            IS_CREATOR = user_id == room['creator'][0]

            print(result_dict)

            for og_key, value in result_dict.items():
                
                key, mode = og_key.split(':')


                if key == 'description':
                    room['description'] = value
                else:
                    try:
                        if value:
                            value = float(value.lower().replace('m','').replace('k',''))
                        else:
                            value = None
                    except:
                        continue
                    else:
                        if key == 'est':
                            if IS_CREATOR:
                                room['creator'][-1] = value
                            elif mode == 'join':
                                room['members'].append([user_id, False, value])
                            else:
                                target_index = room['members'].index([i for i in room['members'] if i[0] == user_id][0])
                                room['members'][target_index][-1] = value
                        elif key == 'goal':
                            room['goal'] = value

            self.roomsf_io(room)
            await self.update(room, message)
        
        async def update(self, room, message):
            await message.edit(embed=self.embed_maker(room))
    
    class roomModal(nextcord.ui.Modal):
        def __init__(self, room, mode, view):
            self.view = view
            super().__init__(room['description'], timeout=45)
            self.base_id = 'ames_roomModal_'

            self.make_items(room, mode)

        def make_items(self, room, mode):
            edit_descr_dict = {
                'label': 'Room Description',
                'default_value': room['description'],
                'required': True,
                'style': nextcord.TextInputStyle.short,
                'placeholder': "Required",
                'max_length': 256
            }
            edit_goal_dict = {
                'label': 'Target Damage',
                'required': False,
                'style': nextcord.TextInputStyle.short,
                'placeholder': "unchanged"
            }
            edit_estdmg_dict = {
                'label': 'Your Estimated Damage',
                'required': False,
                'style': nextcord.TextInputStyle.short,
                'placeholder': "unchanged"
            }

            """
            edit_descr = nextcord.ui.TextInput(
                custom_id=self.base_id+'description',
                label='Room Description',
                default_value=room['description'],
                required=True,
                style=nextcord.TextInputStyle.short,
                placeholder="Required",
                max_length=200
                )
            edit_goal = nextcord.ui.TextInput(
                custom_id=self.base_id+'target',
                label='Target Damage',
                required=False,
                style=nextcord.TextInputStyle.short,
                placeholder="unchanged"
            )
            edit_estdmg = nextcord.ui.TextInput(
                custom_id=self.base_id+'est',
                label='Your Estimated Damage',
                required=False,
                style=nextcord.TextInputStyle.short,
                placeholder="unchanged"
            )
            """
            
            if mode == 'edit_creator':
                code = ':editCreator'
                edit_descr_dict['custom_id'] = self.base_id+'description'+code
                edit_goal_dict['custom_id'] = self.base_id+'target'+code
                edit_estdmg_dict['custom_id'] = self.base_id+'est'+code

                items = [
                    edit_descr_dict,
                    edit_goal_dict,
                    edit_estdmg_dict
                ]

            elif mode == 'edit_member':
                code = ':editMember'
                edit_estdmg_dict['custom_id'] = self.base_id+'est'+code
                items = [ 
                    edit_estdmg_dict
                ]
            
            elif mode == 'join':
                code = ':join'
                edit_estdmg_dict['custom_id'] = self.base_id+'est'+code
                items = [ 
                    edit_estdmg_dict
                ]
            
            for item in items:
                super().add_item(nextcord.ui.TextInput(**item))

        async def callback(self, interaction:nextcord.Interaction):
            results = {}
            for container in interaction.data['components']:
                action = container['components'][0]['custom_id'].split('_')[-1]
                value = container['components'][0]['value']
                results[action] = value
            
            await self.view.modal_response(interaction.message, interaction.user.id, results)
            return True

    @commands.command(aliases=['tl'])
    async def shift_time(self, ctx, *, payload):
# attempt to read the delta time
        # delta time should always be the the first thing following the command
        total_time = 90
        delta = payload.split()[0]
        delta_len = len(delta)
        if '.' in delta or ':' in delta:
            if '.' in delta:
                m, s = delta.split('.')
            else:
                m, s = delta.split(':')
            try:
                m = int(m)
                s = int(s)
                delta = m*60 + s
            except:
                ctx.channel.send('Failed to read remaining time!')
                return
        else:
            try:
                delta = int(delta)
            except:
                ctx.channel.send('Failed to read remaining time!')
                return
        
        temp = []
        # split payload into newline segments (I hope the format follows newlines)
        # recover the original payload without the delta
        payload = payload[delta_len:]

        pattern = '\d*:\d+'
        times = re.findall(pattern, payload)
        line = re.sub(pattern, '{}', payload)

        shifted = []
        for time in times:
            m, s = time.split(':')
            try:
                m = int(m)
            except:
                m = 0
            try:
                s = int(s)
            except:
                ctx.channel.send('Failed to read one of the times within instructions!')
                return
            
            remaining_time = total_time - (m*60 + s)
            shifted_time = delta - remaining_time

            if shifted_time < 0:
                shifted.append('-:--')
            else:
                m = shifted_time//60
                s = shifted_time%60
                if not s//10:
                    shifted.append(f"{m}:0{s}")
                else:
                    shifted.append(f"{m}:{s}")

        await ctx.channel.send('```'+line.format(*shifted)+'```')


