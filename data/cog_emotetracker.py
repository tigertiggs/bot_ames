import nextcord
from nextcord.ext import commands
import utils as ut
import templates
import json, datetime, re, argparse, shlex
#from zoneinfo import ZoneInfo

def setup(client):
    client.add_cog(emotetrackerCog(client))

class emotetrackerCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[emote-tracker]'
        self.logger = ut.Ames_logger(self.name, self.client.Log)
        self.logger.init_client(self.client)

        self.stat_path = ut.full_path(self.client.dir, self.client.config['configs']['emotetracker'])
        self.config_path = ut.full_path(self.client.dir, self.client.config['configs']['guilds'])

        self.emojipattern = r"<a?:(?P<name>[a-zA-Z0-9]+):(?P<id>\d+)>" #re.compile("<a?:(?P<name>[a-zA-Z0-9]+):(?P<id>\d+)>")
        self.datetime_format = "%Y-%m-%d %H:%M %z"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if the server is tracking emotes
        try:
            guild_config_path = ut.full_path(self.config_path, f"{message.author.guild.id}.json")
            with open(guild_config_path) as pf:
                gp = json.load(pf)
                if not gp.get('emotetracker', False):
                    return
        except:
            return
        
        # Check if there is an emote/sticker in the message
        emotes = []
        for emote in re.finditer(self.emojipattern, message.content):
            emotes.append(
                 {
                      'name': emote.group('name'), 
                      'id': int(emote.group('id')),
                      'type': 0,
                      'user': message.author.id,
                      'date': message.created_at.strftime(self.datetime_format) #UTC
                }
            )
        for sticker in message.stickers:
             emotes.append(
                {
                       'name': sticker.name, 
                       'id': sticker.id,
                       'type': 1,
                       'user': message.author.id,
                       'date': message.created_at.strftime(self.datetime_format) #UTC
                }
            )
        
        if not emotes:
             return
        
        # log the emote
        stat_path = ut.full_path(self.stat_path, f"{message.guild.id}.json")
        try:
            with open(stat_path) as f:
                jf = json.loads(f.read())

        except Exception as e:
            print(e)
            jf = {'history':[]}
        
        jf['history'] += emotes
        with open(stat_path, 'w+') as f:
            f.write(json.dumps(jf))

    def load_gp(self, guild_id):
        try:
            guild_config_path = ut.full_path(self.config_path, f"{guild_id}.json")
            with open(guild_config_path) as pf:
                    gp = json.load(pf)
        except:
            gp = templates.guild
        
        return gp

    def write_gp(self, guild_id, gp):
        guild_config_path = ut.full_path(self.config_path, f"{guild_id}.json")
        with open(guild_config_path, 'w+') as pf:
            pf.write(json.dumps(gp))

    @commands.group(invoke_without_command=True, aliases=['etrack'])
    async def emotetrack(self, ctx, *, options=''):
        channel = ctx.channel
        author = ctx.author

        # Load guild preferences
        gp = self.load_gp(author.guild.id)
        
        etrack_status = gp.get('emotetracker', False)
        if not etrack_status:
            etrack_status = gp.get('emotetracker', False)
            await channel.send(f"Ames {'is' if etrack_status else 'is not'} tracking emote usage on this server.")
            return
        
        # Options
        # .emotetrack [flags]
        #   If flags is blank, will display serverwide statistics.
        # flags:
        #   -m <member|id>          Filter with member. If blank will assume author. If this flag is omitted will use serverwide statistics.
        #   -e <emoteName|id>       Filter with emote. If blank result will only contain emotes. -s is ignored if this is present.
        #   -s <stickerName|id>     Filter with sticker. If blank result will only contain stickers. 
        #   -l                      Local server emotes only. -x is ignored if this is present.
        #   -x                      External emotes only.
        #   -t <days=30>            Filter within the previous <days> days. Default is 30 days. 
        #   -h <top=10>             Only show the top <top> results. Default is 10 results. Cannot be more than 20.

        # Set default options
        #SERVERWIDE              = True
        TARGET_MEMBER           = None
        #FILTER_EMOTE_ONLY       = False
        FILTER_EMOTE_ID         = None
        #FILTER_STICKER_ONLY     = False
        #FILTER_STICKER_ID       = None
        #FILTER_LOCAL_ONLY       = False
        #FILTER_EXTERNAL_ONLY    = False
        #FILTER_TIME_DAYS        = 30
        #LIMIT                   = 10
        parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
        parser.add_argument('-m', dest='member', nargs='?', const=author.id, default=False)
        parser.add_argument('-e', dest='emote', nargs='?', const=True, default=False)
        parser.add_argument('-s', dest='sticker', nargs='?', const=True, default=False)
        parser.add_argument('-l', dest='local', action='store_true', default=False)
        parser.add_argument('-x', dest='external', action='store_true', default=False)
        parser.add_argument('-t', dest='time', type=int, default=30)
        parser.add_argument('-h', dest='head', type=int, default=10)
        
        try:
            options = parser.parse_args(shlex.split(options.strip()))
            print(options)
        except argparse.ArgumentError or SystemExit:
            await channel.send('Failed to read options')
            return

        # Load the stats and prep for filtering
        try:
            with open(ut.full_path(self.stat_path, f'{channel.guild.id}.json')) as f:
                statsf = json.load(f)
                if len(statsf['history']) == 0:
                    await channel.send('There is no emote data at the moment: data file is empty.')
                    return
                
                stats = statsf['history']

        except:
            await channel.send('There is no emote data at the moment: data file is missing.')
            return
        
        # Member filter
        if options.member:
            # Attempt to find the user
            TARGET_MEMBER = await self.client.find_user(channel.guild, options.member)
            if TARGET_MEMBER == None:
                await channel.send(f'Failed to find user `{options.member}`')
                return
            
            stats = [i for i in stats if i['user'] == TARGET_MEMBER.id]
        
        # Emote filter
        if options.emote:
            # Determine which filter
            if isinstance(options.emote, bool):
                stats = [i for i in stats if i['type'] == 0]

            # Attempt to grab the emote ID
            elif options.emote.startswith('<'):
                try:
                    FILTER_EMOTE_ID = int(options.emote[options.emote.rindex(':')+1:-1])
                except:
                    await channel.send('Failed to process emote filter')
                    return
                stats = [i for i in stats if (i['id'] == FILTER_EMOTE_ID and i['type'] == 0)]
            
            elif options.emote.isnumeric():
                try:
                    FILTER_EMOTE_ID = int(options.emote)
                except:
                    await channel.send('Failed to process emote filter')
                    return
                stats = [i for i in stats if (i['id'] == FILTER_EMOTE_ID and i['type'] == 0)]
            
            else:
                emote = nextcord.utils.find(lambda emote: emote.name == options.emote, channel.guild.emojis)
                if not emote:
                    await channel.send('Invalid emote filter parameter')
                    return
                else:
                    FILTER_EMOTE_ID = emote.id
                    stats = [i for i in stats if (i['id'] == FILTER_EMOTE_ID and i['type'] == 0)]

        # Stickers filter
        if options.sticker and not options.emote:
            # Determine which filter
            if isinstance(options.sticker, bool):
                stats = [i for i in stats if i['type'] == 1]

            # Attempt to grab the emote ID            
            elif options.sticker.isnumeric():
                try:
                    FILTER_EMOTE_ID = int(options.sticker)
                except:
                    await channel.send('Failed to process emote filter')
                    return
                stats = [i for i in stats if (i['id'] == FILTER_EMOTE_ID and i['type'] == 1)]
            
            else:
                emote = nextcord.utils.find(lambda sticker: sticker.name == options.sticker, channel.guild.stickers)
                if not emote:
                    await channel.send('Invalid emote filter parameter')
                    return
                else:
                    FILTER_EMOTE_ID = emote.id
                    stats = [i for i in stats if (i['id'] == FILTER_EMOTE_ID and i['type'] == 1)]
        
        # Local filter
        if options.local:
            local_emotes = [i.id for i in (channel.guild.emojis + channel.guild.stickers)]
            stats = [i for i in stats if i['id'] in local_emotes]
        
        # External filter
        if options.external and not options.local:
            local_emotes = [i.id for i in (channel.guild.emojis + channel.guild.stickers)]
            stats = [i for i in stats if not (i['id'] in local_emotes)]
        
        # Time filter
        if options.time:
            if options.time < 1 or options.time > 364:
                await channel.send('Invalid time period')
                return
            
            # Get target time to filter from
            target_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=options.time)
            #target_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=options.time) # python3.12
            stats = [i for i in stats if target_time <= datetime.datetime.strptime(i['date'], self.datetime_format)]

        # Truncate
        if options.head:
            if options.head < 1 or options.head > 20:
                await channel.send('Invalid head limit')
                return
        
        # Aggregate data
        stats = self.aggregate_stats(stats, channel.guild, options.head)

        if len(stats) == 0:
            await channel.send('0 records match the applied filters.')
            return
        else:
            await channel.send(embed=ut.embed_contructor(
                **self.make_emotestat_embed(
                    stats, channel.guild, 
                    TARGET_MEMBER, 
                    options.time, 
                    any([
                        options.local, 
                        options.external, 
                        options.member != False, 
                        options.emote != False, 
                        options.sticker != False
                        ]
                    )
            )))
            
    def aggregate_stats(self, stats, guild, limit):
        agg = {}
        for item in stats:
            if item['id'] in agg:
                agg[item['id']]['count'] += 1

            else:
                if item['type'] == 0:
                    emote = nextcord.utils.find(lambda x: x.id == item['id'], guild.emojis)
                else:
                    emote = nextcord.utils.find(lambda x: x.id == item['id'], guild.stickers)
                
                if not emote:
                    emote = item['name']
                    local = 0
                elif item['type'] == 0:
                    local = 1
                    if emote.animated:
                        emote = f'<a:{emote.name}:{emote.id}>'
                    else:
                        emote = f'<:{emote.name}:{emote.id}>'
                else:
                    local = 1
                    emote = f'{emote.name}(sticker)'

                agg[item['id']] = {
                    'id': item['id'],
                    'name': item['name'],
                    'type': item['type'],
                    'local': local,
                    'disp': emote,
                    'count': 1
                }

        return sorted(agg.values(), key=lambda x: x['count'], reverse=True)[:limit]
        
    def make_emotestat_embed(self, stats, guild, TARGET_MEMBER, FILTER_TIME_DAYS, FILTER_FLAG):
        embed = {
            'title': ("Server" if not TARGET_MEMBER else TARGET_MEMBER.name+"'s") + " Emote Statistics",
            'descr': f"Showing statistics for the past {FILTER_TIME_DAYS} days. " + ("Data has been further filtered." if FILTER_FLAG else ""),
            'footer': {'text': 'Emote Tracker'},
            'thumb': TARGET_MEMBER.avatar.url if TARGET_MEMBER else guild.icon.url,
            'fields': [
                {
                    'name': 'Emote',
                    'value': '\n'.join([i['disp'] for i in stats]),
                    'inline': True
                },
                {
                    'name': 'Count',
                    'value': '\n'.join([str(i['count']) for i in stats]),
                    'inline': True
                },
                {
                    'name': 'Source',
                    'value': '\n'.join([('Local' if i['local'] == 1 else 'External') for i in stats]),
                    'inline': True
                }
            ]
        }

        return embed

    @emotetrack.command()
    async def help(self, ctx):
        channel = ctx.channel
        await channel.send(\
            "**Syntax**\n```.etrack [options]```If used without options, will show serverwide statistics.\n\n**Options**\n"\
            "> `-m <username|id>`\nFilters the stats for a specific user. If used without an arg will assume user.\n"\
            "> `-e <emotename|id>`\nFilters the stats for a specific emoji. If used without an arg will filter all emojis.\n"\
            "> `-s <stickername|id>`\nFilters the stats for a specific sticker. If used without an arg will filter all stickers. Ignored if `-e` is present.\n"\
            "> `-l`\nFilters the stats for only emotes on the current server.\n"\
            "> `-x`\nFilters the stats for only emotes not on the current server. Ignored if `-l` is present.\n"\
            "> `-t <days=30>`\nFilters the stats to the last `<days>` days. Must be between 1 and 364.\n"\
            "> `-h <limit=10>`\nTruncates the stats to contain a maximum of `<limit>` emotes. Must be between 1 and 20."
        )
    
    @emotetrack.command()
    async def status(self, ctx, option=None):
        channel = ctx.channel
        author = ctx.author

        # Load guild preferences
        gp = self.load_gp(author.guild.id)

        if not option:
            etrack_status = gp.get('emotetracker', False)
            await channel.send(f"Ames {'is' if etrack_status else 'is not'} tracking emote usage on this server.")
            return
        elif option == '1':
            gp['emotetracker'] = True
            await channel.send('Ames is now tracking emote usage on this server')
        elif option == '0':
            gp['emotetracker'] = False
            await channel.send('Ames is no longer tracking emote usage on this server')
        else:
            await channel.send(f'Invalid option: {option}, expected 1 or 0 '+self.client.emotes['ames'])
            return
        
        self.write_gp(author.guild.id, gp)
        await channel.send('Server preferences saved')

        
    
