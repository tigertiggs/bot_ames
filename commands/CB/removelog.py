"""
Ames
removelog
"""

async def removelog(ctx, e_id, flags, emj):
    channel = ctx.channel
    try:
        e_id = int(e_id)
    except:
        print('removelog: could not read e_id as int')
        await channel.send(emj['shiori'])
        return
        
    remove_log = ("DELETE FROM cb.cb_log "
                  "WHERE entry_id = {:d}".format(e_id))
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(remove_log, )
    except mysql.connector.Error as err:
        print('removelog:\n', err)
        cb_cursor.close()
        await channel.send(emj['maki']+'Could not remove log!')
        return
    else:
        cb_cursor.close()
        print('removelog: success')
        await channel.send('Successfully removed log!')
        return
