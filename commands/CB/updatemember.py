"""
Ames
updatemember
"""

async def updatemember(ctx, inp, flags, emj):
    """
    Updates a certain field in cb.members
    Expects:
    [<nick :str>,
    <field: str, nick|active>,
    value: str, nick|active>
    ]
    """
    channel = ctx.channel
    msgv = inp
    
    if len(msgv) < 3:
        print('updatemember: insufficient input')
        await channel.send(emj['maki']+'Could not update member - insufficient input supplied!')
        return
    if msgv[1] not in ["nick","active"]:
        print('updatemember: invalid field supplied')
        await channel.send(emj['maki']+'Could not update member - invalid field supplied!')
        return

    try:
        m_id = int(msgv[0])
    except:
        print('updatemember: could not read m_id as int')
        await channel.send(emj['shiori'])
        return
    field = msgv[1]
    value = msgv[2]

    update_member_nick = ("UPDATE cb.members "
                     "SET {0:s} = '{1:s}' "
                     "WHERE m_id = {2:d}".format(field, value, m_id))

    update_member_active = ("UPDATE cb.members "
                     "SET {0:s} = {1:s} "
                     "WHERE m_id = {2:d}".format(field, value, m_id))
    try:
        cb_cursor = flags['cb_db'].cursor()
        if field == 'nick':
            cb_cursor.execute(update_member_nick, )
        if field == 'active':
            cb_cursor.execute(update_member_active, )
        flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print("updatemember:\n:", err)
        cb_cursor.close()
        await channel.send(emj['maki']+'Could not update member - failed to update!')
        return
    else:
        cb_cursor.close()
        print('updatemember: success')
        await channel.send('Successfully updated member record!')
        return
