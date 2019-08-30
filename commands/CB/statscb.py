"""
Ames
statscb
"""
import _checks as ck
import discord
import datetime

async def statscb(ctx, inp, flags, emj):
    """
    Returns details needed for statscbembed.
    """
    channel = ctx.channel

    if len(inp) > 0:
        cb_id = int(inp[0])
    else:
        if not flags['current_cb']:
            await channel.send('No CB set!')
            return
        cb_id = int(flags['current_cb'])

    #print(cb_id)
    query_stats = ("SELECT start_date, span_days, total, active_members "
                   "FROM cb.cb_list "
                   "WHERE cb_id = {:d}".format(cb_id))
    
    try:
        cb_cursor = flags['cb_db'].cursor(buffered=True)
        cb_cursor.execute(query_stats, )
        data = []
        for (date, days, tot, active) in cb_cursor:
            data = [str(date), days, tot, active, str(cb_id)]
    except mysql.connector.Error as err:
        print('statcb:\n', err)
        cb_cursor.close()
        await channel.send('Could not fetch data!')
        return
    else:
        cb_cursor.close()
        print('statscb: success')
        if ck.isempty(data):
            print('statscb: no data fetched')
            await channel.send('No data fetched!')
        await channel.send(embed=statscbembed(ctx,data))
        return

def statscbembed(context, data):
    embed = discord.Embed(title="Clan Battle Report (minimal)", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Stats", icon_url=context.message.author.avatar_url)
    embed.add_field(name="CB ID", value=data[4], inline=False)
    embed.add_field(name="Start date", value=data[0], inline=True)
    embed.add_field(name="Total days", value=data[1], inline=True)
    embed.add_field(name="Total damage", value=data[2], inline=True)
    embed.add_field(name="Active members", value=data[3], inline=True)
    embed.set_footer(text="still in testing")
    return embed
