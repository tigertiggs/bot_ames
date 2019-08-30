"""
Ames
listmembers
listmembersembed
"""
import discord
import datetime
import _checks as ck

async def listmembers(ctx, mode, flags, emj):
    """
    Creates data needed for listmembersembed
    """
    channel = ctx.channel
    msgv = mode
    if len(msgv) > 0:
        if msgv[0] == '0':
            mode = 0
            mode_name = 'Inactive'
        elif msgv[0] == '1':
            mode = -1
            mode_name = 'Full'
        else:
            print('listmembers: received incorrect command: ' + msgv[0])
            await channel.send('Invalid input!')
            return
    else:
        mode = 1
        mode_name = 'Active'

    if mode == -1:
        query_listmembers = (
                "SELECT m_id, discord_tag, nick, active, guild "
                "FROM cb.members ORDER BY active DESC, m_id")
    else:
        query_listmembers = (
            "SELECT m_id, discord_tag, nick, active, guild "
            "FROM cb.members "
            "WHERE active = {:d} ORDER BY active, m_id".format(mode))

    try:
        cb_cursor = flags['cb_db'].cursor(buffered=True)
        cb_cursor.execute(query_listmembers, )
        m_id = []
        d_tag = []
        nick = []
        active = []
        guild = ""
        for (_m_id, _d_tag, _nick, _active, _guild) in cb_cursor:
            m_id.append(str(_m_id))
            d_tag.append(_d_tag)
            active.append(str(_active))
            if len(_nick) > 23:
                nick.append(str(_nick)[:22]+"...")
            else:
                nick.append(str(_nick))
            guild = str(_guild)
    except mysql.connector.Error as err:
        print("listmembers:\n:", err)
        cb_cursor.close()
        await channel.send('Could not fetch data!')
        return
    else:
        cb_cursor.close()
        print('listmembers: success')
        guild = ck.guildname(guild)
        data = [m_id, d_tag, nick, active, mode_name, guild]
        if ck.isempty(data[:-2]):
            print('listmembers: empty data')
            await channel.send('No data fetched!')
            return
        print(data)
        await channel.send(embed=listmembersembed(ctx, data))
        return

def listmembersembed(context, data):
    embed = discord.Embed(title="{0:s} {1:s} Guild Roster".format(data[4],data[-1]), description="{:d} records retrieved. Prepared by yours truly.".format(len(data[0])), timestamp=datetime.datetime.utcnow())
    embed.set_author(name="Roster", icon_url=context.message.author.avatar_url)
    embed.add_field(name="M_ID", value="\n".join(data[0]), inline=True)
    #embed.add_field(name="Discord", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Nickname", value="\n".join(data[2]), inline=True)
    if data[4] == 'Full':
        embed.add_field(name="Active", value="\n".join(data[3]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

