"""
Ames
Removemember
"""

async def removemember(ctx, inp, flags, emj):
    """
    Deletes a member's record given m_id
    """
    channel = ctx.channel
    msgv = inp
    
    if len(msgv) == 0:
        print('removemember: no m_id supplied')
        await channel.send(emj['maki']+'Could not remove member record - no `m_id` supplied!')
        return
    else:
        m_id = int(msgv[0])

    query_delete_child = ("DELETE FROM cb.cb_log "
                    "WHERE m_id = {:d}".format(m_id))
    
    query_delete = ("DELETE FROM cb.members "
                    "WHERE m_id = {:d}".format(m_id))

    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(query_delete_child)
        flags['cb_db'].commit()
        cb_cursor.execute(query_delete)
        flags['cb_db'].commit()
        cb_cursor.close()
    except mysql.connector.Error as err:
        print("removemember:\n:", err)
        cb_cursor.close()
        await channel.send('Could not remove member record - failed to remove record!')
        return
    else:
        print('removemember: success')
        await channel.send('Successfully removed member record!')
        return
