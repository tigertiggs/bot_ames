"""
Ames
newCB
"""
import _checks as ck
import concludecb as cl

async def newcb(ctx, inp, flags, emj):
    # .cb newcb [start date yyyy-mm-dd] [span default = SPAN_DAYS] [set default = 1]
    """
    Inserts a cb entry into cb.cb_lists.
    Expects:
    [<start_date: str, format yyyy-mm-dd>,
    <current: int, optional, default = 1>,
    <span_days: int, optional, default = span_days>]
    """
    channel = ctx.channel
    msgv = inp
    
    #print(msgv)
    if len(msgv) == 0:
        print('newcb: insufficient inputs')
        await channel.send('Could not add new CB - insufficient inputs supplied!')
        return flags
    
    inpdate = datetime.datetime.strptime(msgv[0], '%Y-%m-%d')
    #print(inpdate.strftime('%Y-%m-%d'))
    default = 1
    span = flags['span_days']
    
    if len(msgv) > 1:
        span = msgv[1]
        if len(msgv) > 2:
            default = msgv[2]
    
    new_cb = ("INSERT INTO cb.cb_list "
              "(start_date, current, span_days) "
              "VALUES ('{0:s}', {1:d}, {2:d})".format(inpdate.strftime('%Y-%m-%d'), int(default), int(span)))
    
    get_cbid = ("SELECT cb_id from cb.cb_list "
                "WHERE current = 1")
    
    try:
        if default:
            ck._resetcbc()
            flags = await cl.concludecb(ctx, flags, emj)
            flags['cb_concluded'] = False
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(new_cb, )
        flags['cb_db'].commit()
        cb_cursor.execute(get_cbid, )
        for (cb_id) in cb_cursor:
            flags['current_cb'] = cb_id[0]
    except mysql.connector.Error as err:
        print('newcb:\n', err)
        cb_cursor.close()
        await channel.send('Could not add new CB - failed to add new entry!')
        return flags
    else:
        cb_cursor.close()
        print('newcb: success')
        await channel.send('Successfully added new CB entry!')
        return flags
