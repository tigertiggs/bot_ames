"""
Ames
listcb
"""

import discord
import datetime
import _checks as ck

async def listcb(ctx, flags, emj):
    """
    Returns the data of the 10 latests cb data for listcbembed.
    """
    channel = ctx.channel
    
    query_list = ("SELECT cb_id, start_date, total "
                  "FROM cb.cb_list "
                  "ORDER BY cb_id DESC "
                  "LIMIT 10")
    try:
        cb_cursor = flags['cb_db'].cursor(buffered=True)
        cb_cursor.execute(query_list, )
        cb_idv = []
        datev = []
        totalv = []
        for (cb_id, start_date, total) in cb_cursor:
            cb_idv.append(str(cb_id))
            datev.append(str(start_date))
            totalv.append(str(total))
    except mysql.connector.Error as err:
        print('listcb:\n', err)
        cb_cursor.close()
        await channel.send('Could not fetch data!')
        return
    else:
        cb_cursor.close()
        print('listcb: success')
        data = [cb_idv, datev, totalv]
        if ck.isempty(data):
            print('listcb: no data fetched')
            await channel.send('No data fetched!')
            return
        await channel.send(embed=listcbembed(ctx,data))
        return

def listcbembed(context, data):
    embed = discord.Embed(title="Clan Battle Log (minimal)", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Log", icon_url=context.message.author.avatar_url)
    embed.add_field(name="CB ID", value="\n".join(data[0]), inline=True)
    embed.add_field(name="Start date", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Total damage", value="\n".join(data[2]), inline=True)
    embed.set_footer(text="still in testing")
    return embed
