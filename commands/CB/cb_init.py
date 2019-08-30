"""
Ames
CB INIT
"""
import _checks as ck

async def cb_init(ctx, flags):
    """
    Initialises the basic requirements for operating the cb command and checks at every call
    """
    channel = ctx.channel
    # check if cb_db is connected
    if not flags['db_isconnected']:
        print('cb_init: DB is not connected - exiting command')
        await ctx.channel.send('Database is not connected!')
        return flags

    # check and set current_cb
    if not flags['current_cb']:
        print('cb_init: global current_cb is not set. Attempting to set via database.')
        query = ("SELECT cb_id FROM cb.cb_list "
                 "WHERE current = 1")
        
        try:
            cb_cursor = flags['cb_db'].cursor()
            cb_cursor.execute(query, )
            for (_id) in cb_cursor:
                if str(_id) == 'None':
                    print('cb_init: no active cb found in db')
                    #await channel.send('Could not set current CB - no active CB found in DB!')
                    return
                flags['current_cb'] = int(_id[0])
        except mysql.connector.Error as err:
            print('cb_init:\n', err)
            cb_cursor.close()
            #await channel.send('Could not set current CB via database!')
            return flags
        else:
            flags = ck._checkconcl(flags)
            cb_cursor.close()
            print('cb_init: success')
            #await channel.send('Successfully set current CB via DB!')
            return flags
        
    return flags
