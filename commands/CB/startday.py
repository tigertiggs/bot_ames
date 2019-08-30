"""
Ames
startday
"""
import _checks as ck

async def startday(ctx, flags, emj):
    """
    Inserts 0s into cb.cb_log. Replaced _endday
    """
    channel = ctx.channel
    
    if not flags['current_cb']:
        print('startday: current_cb is not set!')
        await channel.send(emj['maki']+'Could not start day: current CB not set!')
        return
    if flags['cb_concluded']:
        print('startday: cb_concluded flag set')
        await channel.send(emj['maki']+'Could not start new day: CB has ended!')
        return
    
    cb_id = int(flags['current_cb'])
    
    # get the current day
    day = ck._getday(cb_id, flags)
    
    # get m_id
    get_mid = ("SELECT m_id FROM cb.members WHERE active = 1")
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(get_mid, )
    except mysql.connector.Error as err:
        print('startday:\n', err)
        cb_cursor.close()
        await channel.send(emj['maki']+'Could not start new day!')
        return
    
    mid = []
    for (_mid) in cb_cursor:
        mid.append(int(_mid[0]))
    if len(mid) == 0:
        print('startday: no active members')
        await channel.send(emj['maki']+'No active members - Nothing to insert!')
        return

    # insert
    insert_log = "INSERT INTO cb.cb_log "\
                 "(cb_id, day, hit1, hit2, hit3, hits, m_id, hit1meta, hit2meta, hit3meta) "\
                 "VALUES ({0:d}, {1:d}, {2:d}, {3:d}, {4:d}, {5:d}, {6:d}, '{7:s}', '{8:s}', '{9:s}')"

    #print(mid, day, cb_id)
    try:
        for m_id in mid:
            cb_cursor.execute((insert_log.format(cb_id, day+1, 0, 0, 0, 0, int(m_id), '0-0:0', '0-0:0', '0-0:0')))
            flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print('startday:\n', err)
        cb_cursor.close()
        await channel.send(emj['maki']+'Failed to start today\'s log')
        return
    else:
        cb_cursor.close()
        print('startday: success')
        await channel.send(emj['sarenh']+'Successfully started new day!')
        return


    
