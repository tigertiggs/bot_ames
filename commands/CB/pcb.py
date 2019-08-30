"""
Ames
PCB
"""
import _checks as ck

async def pcb(ctx, flags, emj):
    """
    Have Ames say the current CB. This should never throw an error.
    """
    channel = ctx.channel
    author = ctx.message.author
    nick = author.nick
    
    if not flags['current_cb']:
        print('pcb: current_cb not set')
        await channel.send(emj['maki']+"No CB set!")
        return 
    
    cb_id = flags['current_cb']
    day = ck._getday(cb_id, flags)
    query_cb = ("SELECT start_date, span_days "
                "FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(query_cb, )
    except mysql.connector.Error as err:
        print('pcb:\n', err)
        cb_cursor.close()
        await channel.send(emj['maki']+"Error upon requesting CB data, check console!")
        return
    else:
        for (_sd, _span) in cb_cursor:
            sd = str(_sd)
            span = int(_span)
        cb_cursor.close()
        if flags['cb_concluded']:
            status = 'has concluded. Otsukaresama!'
        else:
            status = 'is ongoing. Ganbare!'
            
        print('pcb: success')
        await channel.send("We are currently on **Day {0:s} of {4:d}** of the CB that started on {1:s} with `cb_id = {2:d}`. The CB {3:s}"\
               .format(str(day), sd, cb_id, status, span))
        return
