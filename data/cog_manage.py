import nextcord
from nextcord.ext import commands
import utils as ut
import datetime as dt

NUMBERS = [
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'
]

def setup(client):
    client.add_cog(manageCog(client))

class manageCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = "[manage]"
        self.logger = ut.Ames_logger(self.name, self.client.Log)
        self.logger.init_client(self.client)

        self.role_fmt = '<@{}>'
    
    # @commands.Cog.listener()
    # async def on_raw_reaction_add(self, payload):
    #     channel = self.client.get_channel(payload.channel_id)
    #     user = channel.guild.get_user(payload.user_id)
    #     # fetch message
    #     msg = await self.client.get_channel(payload.channel_id).fetch_message(payload)

    #     if (len(msg.embeds) != 1):
    #         return

    #     msg_embed = msg.embeds[0]
    #     key = msg_embed.footer.text.split('::')

    #     if len(key) != 2:
    #         return
        
    #     key, options = key

    #     if key == 'rsa':
    #         roles = 

    # @commands.command(aliases=['rsa'])
    # async def role_self_assign(self, ctx, *, args):
    #     # syntax: .rsa a description is applicable; @role1,@role2; limit
    #     code = 'rsa::{}'
    #     # check perms
    #     author = ctx.message.author
    #     channel=ctx.message.channel
    #     if not self.client.check_perm(author):
    #         await channel.send(self.client.emotes['ames'])
    #         return

    #     args = args.split(';')
    #     if len(args) == 2:
    #         limit = 1
    #     else:
    #         limit = int(args[-1])
        
    #     roles = [i.strip()[2:-1] for i in args[1].split(',')]
    #     emotes = [f":{i}:" for i in NUMBERS[:len(roles)]]
    #     if len(roles) > 5:
    #         await channel.send('too many roles!')
    #         return
        
    #     embed = ut.embed_contructor(
    #         title='Role Self Assignment',
    #         descr=args[0] if args[0] else None,
    #         footer={'text': code.format(limit)},
    #         fields=[
    #             {
    #                 'name': 'Available Roles',
    #                 'value': '\n'.join([f"{i} {j}" for i,j in zip(emotes, [self.role_fmt.format(i) for i in roles])])
    #             }
    #         ],
    #     )

    #     msg = await channel.send(embed=embed)

    #     for emote in emotes:
    #         await msg.add_reaction(emote)

    @commands.command()
    async def time(self, ctx, *, args=''):
        channel = ctx.channel
        # takes an input (date)time, and converts it to unix time 
        
        # input syntax
        # .time yymmdd hhmm+tz (24hr time)
        # yymmdd var is (optional). If provided, the following must be satisfied:
        #   dd is mandatory
        #   mm is optional
        #   yy is optional
        #   if yymmdd is not in full form it must be provided in this order: dd > mmdd > yymmdd; it CANNOT be something like mmyydd, yydd, etc
        #   omitted information will be assumed to be current server datetime 
        
        # hhmm+tz is mandatory
        #   24hr time format 

        args = [i.strip() for i in args.strip().split() if i.strip()]

        if not args:
            await channel.send('command syntax: `.time [yy|mm|dd](optional) hhmm+tz`') #FIXME
            return
        elif len(args) > 2:
            await channel.send('too many inputs! Expecting 2 or less') #FIXME
            return 

        # intialize default dates
        now = dt.datetime.now()
        now_arr = [now.day, now.month, now.year]

        # parse date if it exists
        if len(args) == 2:
            date = args.pop(0)
            len_date = len(date)

            # check if its in the right format
            if len_date > 6 or len_date < 2 or len_date%2 != 0:
                await channel.send()
                return
            
            try:
                # update default dates with user preference 
                date = [int(i) for i in ut.chunks(date, 2)][::-1]
                #print(now_arr)
                #print(date)
                for i, date_part in enumerate(date):
                    #print(i, date_part)
                    now_arr[i] = date_part

            except Exception as e:
                print(e)
                await channel.send('Something went wrong when parsing the date') #FIXME
                return

        # parse time
        # check for timezone
        time = args[0]
        if '+' in time:
            tz_char = '+'
            utc_mult = 1
        elif '-' in time:
            tz_char = '-'
            utc_mult = -1
        else:
            await channel.send('Did not detect specified timezone') #FIXME
            return 
        
        try:
            time, tz = time.split(tz_char)

            if len(tz) == 4: # +0830
                tz_h = int(tz[:2])
                tz_m = int(tz[2:])
            elif len(tz) < 2 and len(tz) > 0: # +08 or +8
                tz_h = int(tz)
                tz_m = 0
            else:
                await channel.send('Invalid timezone specification') #FIXME
                return
            
            if len(time) != 4:
                await channel.send('Invalid time specification') #FIXME
                return

            time_h, time_m = [int(i) for i in ut.chunks(time, 2)]

        except:
            await channel.send('Something went wrong when parsing time and timezone') #FIXME
            return
        
        # create UTC correction
        req_tz = dt.timezone(dt.timedelta(seconds=utc_mult*(tz_h*60*60 + tz_m*60)))

        # finally, construct the naive time
        try:
            aware_dt = dt.datetime(now_arr[2]%1000 + 2000, now_arr[1], now_arr[0], time_h, time_m, tzinfo=req_tz)
        except:
            await channel.send('Something went wrong when constructing the final datetime, check your inputs!')
            return

        # finally finally, return the UNIX time
        await channel.send(f'parsed time: `{aware_dt}`\ndiscord timestamp: <t:{int(aware_dt.timestamp())}:R> `<t:{int(aware_dt.timestamp())}:R>`')

        return



        
            

        


    

