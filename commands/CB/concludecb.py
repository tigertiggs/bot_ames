"""
Ames
concludecb
"""
import _checks as ck
import discord
import datetime

async def concludecb(ctx, flags, emj):
    """
    aggregates data, and calls statscb
    """
    channel = ctx.channel
    if not flags['current_cb']:
        print('concludecb: no cb set')
        await channel.send('Current CB not set')
        return flags

    cb_id = int(flags['current_cb'])
    
    query_total = ("SELECT (SUM(hit1) + SUM(hit2) + sum(hit3)) AS total, COUNT(DISTINCT m_id) AS active "
                   "FROM cb.cb_log "
                   "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    
    # update cb
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(query_total, )

        for (_total, _activem) in cb_cursor:
            total = _total
            activem = _activem

        update_conclude = ("UPDATE cb.cb_list "
                           "SET total = {0:d}, active_members = {1:d} "
                           "WHERE cb_id = {2:d}".format(int(total), int(activem), cb_id))
        
        cb_cursor.execute(update_conclude, )
        flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not update CB data!')
        return flags

    # collect player aggregate
    query_player = ("SELECT m.nick, SUM((l.hit1 + l.hit2 + l.hit3)) AS total, "
                    "SUM(l.hits) AS total_hits "
                    "FROM cb.cb_log AS l "
                    "INNER JOIN cb.members AS m "
                    "ON m.m_id = l.m_id "
                    "WHERE cb_id = {:d} "
                    "GROUP BY l.m_id".format(cb_id))
    try:
        cb_cursor.execute(query_player, )
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not aggregate data!')
        return flags
    else:
        tag = []
        tot = []
        toth = []
        for (_tag, _tot, _toth) in cb_cursor:
            if len(str(_tag)) > 10:
                _tag = str(_tag)[:10] + '...'
            tag.append(str(_tag))
            tot.append(str(_tot))
            toth.append(str(_toth))

    query_date = ("SELECT start_date, span_days "
                  "FROM cb.cb_list "
                  "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
         cb_cursor.execute(query_date)
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not fetch Cb data!')
        return flags
    else:
        for (_date, _days) in cb_cursor:
            date = _date
            days = _days
        cb_cursor.close()
        flags['cb_concluded'] = True
        print('concludecb: success')
        data = [str(date), int(days), int(total), str(activem), tag, tot, toth]
        if ck.isempty(data):
            print('concludecb: no data fetched')
            await channel.send('No data fetched!')
        await channel.send(embed=concludecbembed(ctx,data))
        return flags

def concludecbembed(context, data):
    embed = discord.Embed(title="CB Conclusion report", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name=data[0]+" CB Summary", icon_url=context.message.author.avatar_url)
    embed.add_field(name="Days", value=data[1], inline=True)
    embed.add_field(name="Guild Damage", value=data[2], inline=True)
    embed.add_field(name="Active Members", value=data[3], inline=True)
    embed.add_field(name="Member", value="\n".join(data[4]), inline=True)
    embed.add_field(name="Total Damage", value="\n".join(data[5]), inline=True)
    embed.add_field(name="Total Hits", value="\n".join(data[6]), inline=True)
    embed.set_footer(text="still in testing")
    return embed
