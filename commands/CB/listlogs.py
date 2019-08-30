"""
Ames
listlogs
listlogsembed
"""
import datetime
import discord
import _checks as ck

async def listlogs(ctx, inp, flags, emj):
    """
    Lists the complete log for a cb
    Expects:
    [<cb_id: str, default = 0>, <day: str, default = 0>]
    """
    channel = ctx.channel
    msgv = inp
    if len(msgv) == 0:
        if not flags['current_cb']:
            print('listlogs: Unable to get current day or current CB!')
            await channel.send('Could not fetch current day or current CB!')
            return
        cb_id = int(flags['current_cb'])
        day = ck._getday(cb_id,flags)

    elif len(msgv) == 1:
        print('listlogs: Insufficient inputs!')
        await channel.send('Insufficient inputs!')
        return
    
    elif len(msgv) > 1:
        if msgv[0] == '0':
            if not flags['current_cb']:
                print('listlogs: Unable to get current CB!')
                await channel.send('Could not fetch current CB!')
                return
            cb_id = int(flags['current_cb'])
        else:
            cb_id = int(msgv[0])
            
        day = int(msgv[1])

    get_date = ("SELECT start_date FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    
    get_logs = ("SELECT l.entry_id, cb.members.nick, "
                "l.hits, (l.hit1 + l.hit2 + l.hit3) AS tot "
                "FROM cb.cb_log AS l "
                "INNER JOIN cb.members ON cb.members.m_id = l.m_id "
                "WHERE l.cb_id = {0:d} "
                "AND l.day = {1:d} "
                "ORDER BY l.hits DESC".format(cb_id, day))

    try:
        cb_cursor = flags['cb_db'].cursor(buffered=True)
        cb_cursor.execute(get_date)
        for _date in cb_cursor:
            date = _date[0]
        cb_cursor.execute(get_logs, )
    except mysql.connector.Error as err:
        print("listlog:\n:", err)
        cb_cursor.close()
        await channel.send('Could not fetch log data!')
        return
    else:
        c1 = []
        c2 = []
        c3 = []
        for (_e_id, _tag, _hits, _tot) in cb_cursor:
            if len(str(_tag)) > 10:
                _tag = str(_tag)[:10] + '...'
            c1.append(" - ".join((str((_e_id)), _tag)))
            c3.append(str(_hits))
            c2.append(str(_tot))
        cb_cursor.close()
        print('listlogs: success')
        data = [day, c1, c2, c3, str(date)]
        print(data)
        if ck.isempty(data):
            print('listlogs: empty data')
            await channel.send('No data fetched!')
            return
        await channel.send(embed=listlogsembed(ctx, data))
        return

def listlogsembed(context, data):
    embed = discord.Embed(title="Log for day {:d}".format(data[0]), description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name=data[4]+" CB Log", icon_url=context.message.author.avatar_url)
    embed.add_field(name="EID", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Total Damage", value="\n".join(data[2]), inline=True)
    embed.add_field(name="Hits", value="\n".join(data[3]), inline=True)
    embed.set_footer(text="still in testing")
    return embed


