"""
Ames
removecb
"""

async def removecb(ctx, inp, flags, emj):
    """
    Removes a cb role given a cb_id
    """
    channel = ctx.channel
    msgv = inp
    
    if len(msgv) == 0:
        print('removecb: no cb_id supplied')
        await channel.send('Could not remove CB entry - no `cb_id` supplied!')
        return
    cb_id = int(msgv[0])

    query_delete_child = ("DELETE FROM cb.cb_log "
                          "WHERE cb_id = {:d}".format(cb_id))
    
    query_delete = ("DELETE FROM cb.cb_list "
                    "WHERE cb_id = {:d}".format(cb_id))

    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(query_delete_child)
        flags['cb_db'].commit()
        cb_cursor.execute(query_delete)
        flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print('removecb:\n', err)
        cb_cursor.close()
        await channel.send('Could not remove CB entry!')
        return
    else:
        cb_cursor.close()
        print('removecb: success')
        await channels.send('Successfully removed CB entry!')
        return
