"""
Ames
setcb
"""
import _checks as ck

async def setcb(ctx, inp, flags, emj):
    """
    Sets the given cb_id to have current value = 1. If not provided, global current_cb will be set instead via db
    expects:
    [<cb_id: int, optional>]
    """
    channel = ctx.channel
    msgv = inp
    print(msgv)
    
    if len(msgv) > 0:
        cb_id = msgv[0]
        set_cb = ("UPDATE cb.cb_list "
                  "SET current = 1 "
                  "WHERE cb_id = {:d}".format(int(cb_id)))

        try:
            ck._resetcbc()
            cb_cursor = flags['cb_db'].cursor()
            cb_cursor.execute(set_cb, )
            flags['cb_db'].commit()
            flags['current_cb'] = cb_id
        except mysql.connector.Error as err:
            print('setcb:\n', err)
            cb_cursor.close()
            await channel.send('Could not set current CB via supplied `cb_id`!')
            return flags
        else:
            cb_cursor.close()
            await channel.send('Successfulled set current CB!')
            return flags
    else:
        query = ("SELECT cb_id FROM cb.cb_list "
                 "WHERE current = 1")
        
        try:
            cb_cursor = flags['cb_db'].cursor()
            cb_cursor.execute(query, )
            for (_id) in cb_cursor:
                if str(_id) == 'None':
                    print('setcb: no active cb found in db')
                    await channel.send('Could not set current CB - no active CB found in DB!')
                    return flags
                flags['current_cb'] = _id[0]
        except mysql.connector.Error as err:
            print('setcb:\n', err)
            cb_cursor.close()
            await channel.send('Could not set current CB via database!')
            return flags
        else:
            cb_cursor.close()
            print('setcb: success')
            await channel.send('Successfully set current CB via DB!')
            return flags
