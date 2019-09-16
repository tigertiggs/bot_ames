"""
ames
jail
"""
import discord
import asyncio
gulag_id = '620624824540069899'

yes = ['д', 'y', 'd']
no = ['n', 'н']

red = '547685646001504256'
yellow = '435067668241055785'
green = '435067795919863808'
admin = '622997371294318613'

test = '580517346016362518'

perms = [admin]

async def jail(ctx, prisoner, emj, client):
    func = 'jail:'
    author = ctx.message.author
    channel = ctx.channel
    guild = ctx.message.guild
    gulag = guild.get_role(int(gulag_id))
    
    # check perms
    perm = discord.utils.find(
        lambda m: str(m.id) in perms, author.roles)
    if perm == None:
        await channel.send(emj['ames'])
        return

    """
    # check if the person is in jail
    locked = discord.utils.find(
        lambda m: str(m.id) == gulag_id, author.roles)
    if locked != None:
        await channel.send(emj['ames'])
        return
    """

    # verify user
    try:
        #chv = ['<', '@', '!', '>']
        #<@!235361069202145280>
        print(prisoner.split('!'))
        user_id = prisoner.replace('<', '').replace('>','').replace('!','').replace('@','')      
        user = guild.get_member(int(user_id))
    except Exception as err:
        print(func, err)
        user = discord.utils.find(
            lambda m: prisoner.lower() in m.name.lower(), guild.members)

    if user == None:
        await channel.send(
            emj['ames']+'I did not find the suspect.')
        return

    # check if target is an admin
    if discord.utils.find(
        lambda m: str(m.id) in perms, user.roles) != None:
        await channel.send(emj['ames'] + 'You may not jail your comrades')
        return

    jailed = discord.utils.find(
        lambda m: str(m.id) == gulag_id, user.roles)

    if jailed == None:
        """
        # check if the user is already in jail
        for role in user.roles:
            if str(role.id) == gulag_id:
                await channel.send('**{:s}** is already in the gulags!'.format(user.name))
                return
        """
        
        confirm = await channel.send(
            emj['ames']+'Are you sure you want to throw **{:s}** in the gulags?\n> да/нет'\
            .format(user.name))
        
        def check(message):
            return str(message.author.id) == str(author.id) and message.channel == channel
        
        while True:
            try:
                msg = await client.wait_for('message', timeout=15.0, check=check)
                print(msg.content)
                cmd = msg.content.lower()[0]

                if cmd in yes:
                    await user.add_roles(gulag)
                    await channel.send('**{:s}** has been thrown into the gulags for treason against the motherland.'\
                                       .format(user.name))
                    return
                
                elif cmd in no:
                    await channel.send('Retracting the order')
                    return

                else:
                    continue

            except asyncio.TimeoutError as e:
                await channel.send('Retracting the order due to timeout')
                return

    else:
        """
        if jailed == None:
            await channel.send('**{:s}** is currently not in the gulags!'.format(user.name))
            return
        """

        await user.remove_roles(gulag)
        await channel.send('**{:s}** has been released from the gulags'.format(user.name))
        return
