"""
Ames
cbtag new
"""
import discord
import ast
from misc import randcolour as rc

# bosses
BOSS_1 =    '616120855277076490'
BOSS_2 =    '616121000228290561'
BOSS_3 =    '616121101604618259'
BOSS_4 =    '616121290243178497'
BOSS_5 =    '616121405423091723'

bosses =    [BOSS_1,BOSS_2,BOSS_3,BOSS_4,BOSS_5]
num_emj =   ['1\u20E3','2\u20E3','3\u20E3','4\u20E3','5\u20E3']
num =       ['1','2','3','4','5']

BOSS = list(zip(bosses,num))

guild_d = dict()
guild_d['435067795919863808'] = 'green'
guild_d['435067668241055785'] = 'yellow'
guild_d['547685646001504256'] = 'red'
guild_d['434628129357824000'] = 'green'
guild_d['434628671387467788'] = 'yellow'
guild_d['547686074302857218'] = 'red'

guild_n = dict()
guild_n['green'] = '進撃のロリ'
guild_n['yellow'] = '進撃の熟女'
guild_n['red'] = '進撃の怠け'

REPEAT = '\U0001f501'
STOP = '\U0001f6d1'

async def assign(author, guild, channel, *options, _mode=""):
    func = 'assign:'
    for mode in options:
        try:
            boss_id, boss_n = BOSS[int(mode)-1]
            add_boss = guild.get_role(int(boss_id))
        except Exception as err:
            print(func, err)
            await channel.send(emj['shiori'])
        else:
            """
            for role in author.roles:
                if str(role.id) == boss_id:
                    await author.remove_roles(role)
                    await channel.send('Successfully removed role!')
                    continue
            """
            if add_boss in author.roles:
                await author.remove_roles(add_boss)
                if _mode != 'event': await channel.send('Successfully removed role!')
            else:
                await author.add_roles(add_boss)
                if _mode != 'event': await channel.send('Successfully added role!')
    return
    

async def cbtag(ctx, options, emj, client):
    author = ctx.message.author
    guild = ctx.message.guild
    channel = ctx.channel
    func = 'cbtag:'

    if len(options) == 0:
        await channel.send(embed=cbtag_embed(author,guild))
        return
    else:
        try:
            mode = options[0]
            args = options[1:]
        except Exception as err:
            print(func, 'failed to unpack options', err)
            await channel.send(emj['shiori'])
            return

        if mode in num:
            # assign role
            await assign(author, guild, channel, options)
            return
            
        elif mode == 'reset':
            # reset names
            for boss_id, boss_num in BOSS:
                role = guild.get_role(int(boss_id))
                
                if role != None:
                    boss_name = ' '.join(['boss', boss_num, '-', 'unassigned'])
                    await role.edit(name=boss_name)

        elif mode == 'edit':
            # edit name
            try:
                boss_num = int(args[0])
                boss_name = args[1]
                boss = BOSS[boss_num-1]
            except Exception as err:
                print(func, 'edit:', 'failed to unpack', err)
                await channel.send(emj['shiori'])
                return

            role = guild.get_role(int(boss[0]))
            
            if role != None:
                boss_name = ' '.join(['boss', str(boss_num), '-', boss_name])
                await role.edit(name=boss_name)
            else:
                print(func, 'edit:', 'no role found')
                await channel.send(emj['maki']+'target role does not exist!')
                return

        elif mode == 'purge':
            # remove all roles
            if len(args) == 0:
                for role in author.roles:
                    if str(role.id) in bosses:
                        await author.remove_roles(role)
            elif args[0] == 'all':
                pass
            else:
                pass

        elif mode == 'post':
            # check for author guild
            try:
                top_role = guild_d[str(author.top_role.id)]
                print(top_role)
            except Exception as err:
                print(err)
                await channel.send('I didn\'t find your guild tag')
                return
            
            # check for pre-existing message in the channels
            try:
                file = open('commands/CB/_post.txt', 'r')
                post_d = ast.literal_eval(file.read())
                file.close()
            except Exception as err:
                print(err)
                await channel.send('Failed to read post')
                return
            
            post = post_d[top_role]
            try:
                old_channel = guild.get_channel(post[0])
                message = await old_channel.fetch_message(post[1])
                await message.add_reaction(STOP)
                """
                for _emj in num_emj:
                    await message.remove_reaction(_emj, client.user)
                """
            except Exception as err:
                print(func,err)
            
            message = await channel.send(embed=cbtag_embed(author,guild,mode="post"))
            
            for react in num_emj:
                await message.add_reaction(react)
            await message.add_reaction(REPEAT)
            
            post_d[top_role] = (channel.id, message.id)
            print(str(post_d))
            file = open('commands/CB/_post.txt', 'w')
            file.write(str(post_d))
            file.close()

            return
            

    await channel.send(emj['sarenh']+'success!')
    return

def cbtag_embed(author,guild, mode=""):
    func = 'cbt embed:'
    top_role = guild_d[str(author.top_role.id)]
    
    #current = []
    names = []
    #ids =   []
    waiting = []
    
    for boss_id in bosses:
        try:
            count = 0
            boss_role = guild.get_role(int(boss_id))
            #current.append(boss_role)
            names.append(boss_role.name)
            #ids.append(str(boss_role.id))

            # get count
            # iterate through members
            for member in guild.members:

                # iterate through roles in members
                for role in member.roles:

                    # check if current boss_id matches one of the member's roles
                    if str(role.id) == str(boss_role.id):

                        # check if we are in 'post' guild-restricted mode
                        if guild_d[str(member.top_role.id)] == top_role and mode=='post':
                            count += 1
                            print(member.name)
                            break
                        elif mode == "":
                            print(member.name)
                            count += 1
                            break
            waiting.append(str(count))
                                       
        except Exception as err:
            print(func, err)

    if mode == 'post':
        embed = discord.Embed(title='Boss roles',
                              description='React to a number to toggle the boss role.\n'\
                              'React to \U0001f501 to refresh the list.\n'\
                              'If \U0001f6d1 is there it means this embed is no longer active.',
                              colour=rc())
        embed.set_author(name="{:s}'s Boss Reminders".format(guild_n[top_role]))
    else:
        embed = discord.Embed(description='Current total waits for all 3 guilds',
                              colour=rc())
        embed.set_author(name="Available boss roles", icon_url=author.avatar_url)
    
    embed.set_footer(text="still in testing")
    """
    embed.add_field(
        name="Boss number",
        value="\n".join(num)
        )
    """
    embed.add_field(
        name="Boss name",
        value="\n".join(names),
        inline=True)
    embed.add_field(
        name="Awaiting",
        value="\n".join(waiting),
        inline=True)

    return embed
