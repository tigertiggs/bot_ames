"""
Ames
reload
"""

import discord
import datetime
import _checks as ck

async def reload(ctx, guild, flags, emj):
    """
    Updates cb.members with all members in context guild with the same role specified by msgv
    """
    channel = ctx.channel
    
    if guild == "":
        print('reload: no role supplied')
        return channel.send(emj['maki']+'Could not refresh roster - no guild specified!')
    
    role_id, guild = ck.getrole(guild)
    if role_id == 'None':
        print('reload: no role found')
        await channel.send(emj['maki']+'Invalid guild input!')
        return

    print('reload: role received: ' + role_id)

    data = getmembers(guild, flags)
    if not ck.isempty(data[:-1]):
        data = data[1] # d_tag
    roster = []
    
    for member in ctx.message.guild.members:
        if not str(member.id) in data:
            for role in member.roles:
                if str(role.id) == role_id:
                    roster.append((member, guild))
        #elif ("#".join((member.name, member.discriminator)) in data):
        #    data.remove("#".join((member.name, member.discriminator)))
                
    if len(roster) == 0:
        print('reload: no members with role found')
        await channel.send(emj['maki']+'No new members with role found - Roster remains unchanged!')
        return
    else:
        print('reload: success')
        print(roster)
        await _addmember(ctx, flags, emj, roster)
        return

def getmembers(_guild:str, flags):
    role, guild = ck.getrole(_guild)
    if guild == 'None':
        return []
    query_listmembers = (
                "SELECT m_id, discord_tag, nick, active "
                "FROM cb.members "
                "WHERE guild = '{:s}'".format(guild))
    try:
        cb_cursor = flags['cb_db'].cursor(buffered=True)
        cb_cursor.execute(query_listmembers, )
        m_id = []
        d_tag = []
        nick = []
        active = []
        for (_m_id, _d_tag, _nick, _active) in cb_cursor:
            m_id.append(str(_m_id))
            d_tag.append(_d_tag)
            active.append(str(_active))
            if len(_nick) > 23:
                nick.append(str(_nick)[:22]+"...")
            else:
                nick.append(str(_nick))
            guild = str(_guild)
    except mysql.connector.Error as err:
        print("getmembers:\n:", err)
        cb_cursor.close()
        return []
    else:
        cb_cursor.close()
        print('getmembers: success')
        guild = ck.guildname(guild)
        data = [m_id, d_tag, nick, active, guild]
        if ck.isempty(data[:-1]):
            print('getmembers: empty data')
            return []
        print(data)
        return data

async def _addmember(ctx, flags, emj, roster=[]):
    """
    Adds a member to cb.members. Expects roster to be an array of discord member objects
    """
    channel = ctx.channel
    
    if len(roster) == 0:
        print('addmember: roster is empty')
        await channel.send(emj['maki']+'Could not add members - new members list is empty!')
        return
    
    member_data = []
    for member, _guild in roster:
        guild = _guild
        if str(member.nick) == 'None':
            nick = ""
        else:
            nick = str(member.nick)
        member_data.append(
            (str(member.id)," ".join((member.name, nick)))
        )

    query_addm = "INSERT INTO cb.members (guild, discord_tag, nick, active) "\
                 "VALUES ('{2:s}', '{0:s}', '{1:s}', 1)"
    try:
        cb_cursor = flags['cb_db'].cursor()
        for (discord_tag, nick) in member_data:
            cb_cursor.execute((query_addm.format(discord_tag, nick, guild)))
            flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print("addmember:\n:", err)
        cb_cursor.close()
        await channel.send(emj['maki']+'Could not add member - failed to insert data!')
        return
    else:
        cb_cursor.close()
        print('addmember: success')
        await channel.send(emj['sarenh']+'Successfulled added new members!')
        return
