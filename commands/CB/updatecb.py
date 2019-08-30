"""
Ames
updatecb
"""
import datetime

async def updatecb(ctx, inp, flags, emj):
    """
    updates a field in cb.cb_list
    """
    channel = ctx.channel
    msgv = inp
    
    if len(msgv) < 3:
        print('updatecb: insufficient inputs')
        await channel.send('Could not update CB - insufficient inputs supplied!')
        return
    if msgv[1] not in ["date", "span"]:
        print('updatecb: invalid field')
        await channel.send('Could not update CB - invalid field supplied!')
        return
    cb_id = msgv[0]
    field = msgv[1]
    value = msgv[2]
    
    if field == 'date':
        field = 'start_date'
        value = datetime.datetime.strptime(value, '%Y-%m-%d')
        update_cblist = ("UPDATE cb.cb_list "
                         "SET start_date = '{0:s}' "
                         "WHERE cb_id = {1:d}".format(value.strftime('%Y-%m-%d'), int(cb_id)))
    
    if field == 'span':
        field = 'span_days'
        value = int(value)
        update_cblist = ("UPDATE cb.cb_list "
                         "SET span_days = {0:d} "
                         "WHERE cb_id = {1:d}".format(value, int(cb_id)))

    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(update_cblist, )
        flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print("updatecb:\n", err)
        cb_cursor.close()
        await channel.send('Could not update CB!')
        return
    else:
        cb_cursor.close()
        print('updatecb: success')
        await channel.send('Successfully updated CB!')
        return
