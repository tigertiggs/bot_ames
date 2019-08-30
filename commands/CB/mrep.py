"""
Ames
mrep
"""
import datetime
import discord
import _checks as ck

# cb mrep
async def mrep(ctx, search, cb_id, flags, emj):
    func = 'mrep: '
    channel = ctx.channel
    author = ctx.message.author

    # usual checks
    # check if current cb is set
    if not flags['current_cb']:
        print(func+'current_cb is not set')
        await channel.send('Could not fetch - current CB not set!')
        return
    """
    # check if current cb has concluded
    if flags['cb_concluded']:
        print(func+'cb has concluded')
        await channel.send('Could not fetch - current CB has concluded!')
        return
    """

    # grab cb_id
    if cb_id == 0:
        cb_id = int(flags['current_cb'])
    else:
        try:
            cb_id = int(cb_id)
        except:
            print(func+'could not read cb_id input')
            await channel.send(shiori+'check your cb_id input')
            return

    # try casting search
    fetch = "SELECT entry_id, nick, hit1meta, hit2meta, hit3meta, day FROM cb.cb_log l "\
            "JOIN cb.members m ON l.m_id = m.m_id "\
            "WHERE {0:s} AND cb_id = {1:d} ORDER BY day ASC"
    if search == "":
        search = str(author.id)
        fetch = fetch.format("discord_tag = '{:s}'".format(search), cb_id)
    else:
        # m_id?
        try:
            search = int(search)
            fetch = fetch.format('l.m_id = {:s}'.format(str(search)), cb_id)
        except:
            # resort to nick
            print(func+'could not read search_input as m_id')
            search = str(search)
            fetch = fetch.format("nick LIKE '%{:s}%'".format(search), cb_id)
    
    # fetch
    raw_data = []
    try:
        cursor = flags['cb_db'].cursor(buffered=True)
        cursor.execute(fetch, )
        for eid, nick, hit1m, hit2m, hit3m, day in cursor:
            if str(hit1m) == 'None' or str(hit2m) == 'None' or str(hit3m) == 'None':
                continue
            nick = str(nick)
            name = nick
            if len(nick) > 15:
                nick = nick[:15] + '...'
            row = (int(eid), nick, (str(hit1m), str(hit2m), str(hit3m)), int(day))
            raw_data.append(row)
    except mysql.connector.Error as err:
            print(func+err)
            cursor.close()
            await channel.send('Oops, something went wrong while fetching the data...')
            return

    if len(raw_data) == 0:
        print(func+'no data fetched')
        await channel.send(shiori + ' No data fetched')
        return

    #print(raw_data)
    # sift records
    sift_data = []
    #((wave,boss,day),(eid,nick,dmg))
    for eid, nick, hits_all, day in raw_data:
        for hitm in hits_all: # hit_all -> [("wave-boss:dmg", "wave-boss:dmg", "wave-boss:dmg.wave-boss:dmg"),...]
            for indiv in hitm.split('.'): # indiv -> ["wave-boss:dmg", ...]
                #if search in indiv:
                wbm, dmg = indiv.split(':')
                wave, boss = wbm.split('-')
                sift_data.append(
                    ((int(wave), int(boss), day), (eid, nick, int(dmg)))
                     )

    print(sift_data)
    # for data
    sort_data = []
    key = lambda x: x[0][1]
    max_ = max(sift_data, key=key)[0][1]
    
    for i in range(1,max_+1):
            temp = []
            for hit_data in sift_data:
                if hit_data[0][1] == i:
                    temp.append(hit_data)
                
            sort_data.append(temp)

    # sort by wave
    key = lambda x: x[0][0]
    for i in range(len(sort_data)):
        sort_data[i].sort(key=key)
    

    seperator = '||'+':'*60+'||'
    embed = discord.Embed(title="Member CB Report",
                          description="Fetched CB records matching for {:s} for `cb_id = {:d}`. Prepared by yours truly.".format(name, cb_id),
                          timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="still in testing")
    for boss in sort_data:
        if boss:
            embed.add_field(value=seperator + " **[ Boss {:d} ]** ".format(boss[0][0][1]) + seperator,
                                name=". ", inline=False)
            embed.add_field(name="EID",
                            value='\n'.join(
                                [str(field[1][0]) for field in boss]),
                            inline=True
                            )
            embed.add_field(name="Day < > Wave",
                            value="\n".join([str(field[0][2])+' < > '+str(field[0][0]) for field in boss]),
                            inline=True
                            )
            embed.add_field(name="Damage",
                            value="\n".join([str(field[1][2]) for field in boss]),
                            inline=True
                            )

    await channel.send(embed=embed)
    return
