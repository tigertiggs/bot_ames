# cb log test version
@cb.command()
async def log(ctx, *hit_v:str):
    channel = ctx.channel
    user_id = ctx.message.author.id
    name = ctx.message.author.name
    error = '<:shioread:449255102721556490>'

    # check input length
    if len(hit_v) > 3:
        print('log: too many inputs')
        await channel.send(error)
        return

    # mode
    mode = len(hit_v)

    # check if current cb is set
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return

    # check if current cb has concluded
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return
    
    # grab cb_id and current day
    cb_id = int(current_cb)
    day = _getday(cb_id)

    # check if cb has been initiated
    if day == 0:
        print('log: day was None - start a new day!')
        await channel.send('Could not log - CB hasn\'t started!')
        return

    # unpack hit_v
    hit_v = list(hit_v)
    totdmg = []
    meta = []
    for log in hit_v:
        tempsum = []
        tempmeta = []
        for hit in log.split('+'):
            # check if input is of form wave-boss:dmg
            # check if wave-boss is valid and do sanity check on numbers
            try:
                meta, dmg = hit.split(':')
                wave, boss = meta.split('-')
                wave_check = int(wave)
                boss_check = int(boss)
                dmg_int = int(dmg)
                if wave_check <= 0 or boss_check <= 0 or boss_check > 6 or wave_check > 25:
                    print('log: bad wave-boss input - failed sanity check')
                    await channel.send('One or more of your wave-boss input is too wild')
                    return
            except:
                print('log: invalid inputs')
                await channel.send('Your input syntax is wrong - please check your inputs!')
                return
            
            tempsum.append(dmg_int)
            tempmeta.append(':'.join([meta,dmg]))

        totdmg.append(sum(tempsum))
        meta.append(".".join(tempmeta))

    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE discord_tag LIKE '%{:d}%' LIMIT 1".format(user_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(find_mid, )
        m_id = 0
        for _m_id in cb_cursor:
            m_id = int(_m_id[0]) 
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        await channel.send('Something went wrong while fetching your records!')
        return
    
    if m_id == 0:
        print('log: no matching m_id')
        await channel.send('<:shioread:449255102721556490> I couldn\'t find your records, {:s}'.format(name))
        return

    
    # find existing records and append if nessecary
    find_log = ("SELECT "
                "entry_id, hit1, ,hit1meta, hit2, hit2meta, hit3, hit3meta from cb.cb_log WHERE "
                "cb_id = {0:d} AND day = {1:d} AND m_id = {2:d} "
                "LIMIT 1".format(cb_id, int(day), m_id))

    try:
        cb_cursor.execute(find_log, )
        for eid, hit1, hit1m, hit2, hit2m, hit3, hit3m in cb_cursor:
            ex_hits = [int(hit1), int(hit2), int(hit3)]
            m_hits = [str(hit1m), str(hit2m), str(hit3m)]
            eid = int(eid)  
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        await channel.send('Oops, something went wrong...')
        return
    
    hits_left = ex_hits.count(0)

    if mode != 0:            
        if len(totdmg) == 3:
            hit1, hit2, hit3 = totdmg
            hit1m, hit2m, hit3m = meta
            hits = 3 - totdmg.count(0)
                
        elif (hits_left - len(hit_v)) == 0:
            split = ex_hits.index(0)
            hit1, hit2, hit3 = (ex_hits[:split] + totdmg)
            hit1m, hit2m, hit3m = (m_hits[:split] + meta)
            hits = 3 - (ex_hits[:split] + totdmg).count(0)
            
        elif (hits_left - len(totdmg)) > 0:
            for hit in totdmg:
                ex_hits[ex_hits.index(0)] = hit
                m_hits[ex_hits.index(0)] = meta.pop(0)
            hit1, hit2, hit3 = ex_hits
            hit1m, hit2m, hit3m = m_hits
            hits = 3 - ex_hits.count(0)
            
        else:
            print('log: invalid update inputs')
            await channel.send('Something went wrong - you have {0:d} hits left '\
                               'and you tried to update {1:d} hits'.format(hits_left, len(hit_v)))
            return
        
        # update the logs
        update_log = ("UPDATE cb.cb_log SET "
                      "hit1 = {0:d}, "
                      "hit2 = {1:d}, "
                      "hit3 = {2:d}, "
                      "hits = {3:d}, "
                      "hit1meta = '{5:s}', "
                      "hit2meta = '{6:s}', "
                      "hit3meta = '{7:s}' "
                      "WHERE entry_id = {4:d}".format(hit1, hit2, hit3, hits, eid, hit1m, hit2m, hit3m))

        try:
            cb_cursor.execute(update_log, )
            cb_db.commit()
        except mysql.connector.Error as err:
            print("log:\n:", err)
            cb_cursor.close()
            await channel.send('Oops, something went wrong while writing your log...')
            return

        await channel.send("Successfully updated your **day {0:d}** log, **{1:s}**!"\
                           " You have **{2:d} hits remaining**. Ganbarimasu!".format(day, name, 3-hits))
        print('log: success')
        return
    else:
        await channel.send("**{0:s}**, it is currently **day {1:d}** of CB and you have **{2:d} hits** remaining. "\
                           "Ganbarimasu!".format(name, day, hits_left))
        print('log: success')
        return

# cb battle
@cb.command()
async def battle(ctx, bat:str):
    channel = ctx.channel
    author = ctx.message.author
    error = '<:shioread:449255102721556490>'

    # usual checks
    # check if current cb is set
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return

    # check if current cb has concluded
    if not check_current_cb():
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return
    
    # grab cb_id
    cb_id = int(current_cb)

    # check wave-boss request
    req = bat.split('-')
    if len(req) != 2:
        print('battle: invalid inputs')
        await channel.send(error)
        return

    wave, boss = req

    # check wave-boss request
    try:
        wave, boss = bat.split('-')
        if wave == "*":
            search = '-'+boss
            boss = int(boss)
            mode = 'boss'
        elif boss == "*":
            search = wave+'-'
            wave = int(wave)
            mode = 'wave'
        else:
            search = wave+'-'+boss
            boss = int(boss)
            wave = int(wave)
            mode = 'all'
    except:
        print('battle: check failed')
        await channel.send(error)
        return
    
    # fetch records
    fetch = ("SELECT entry_id, nick, hit1meta, hit2meta, hit3meta, day "
             "FROM cb.cb_log l JOIN cb.members m ON l.m_id = m.m_id "
             "WHERE cb_id = {0:d} AND "
             "(hit1meta LIKE '%{1:s}%' "
             "OR hit2meta LIKE '%{1:s}%' "
             "OR hit3meta LIKE '%{1:s}%') "
             "SORT day ASC".format(cb_id, search))

    raw_data = []
    try:
        cursor = cb_db.cursor(buffered=True)
        cursor.execute(fetch, )
        for eid, nick, hit1m, hit2, hit3m, day in cursor:
            row = (int(eid), str(nick), (str(hit1m), str(hit2m), str(hit3m)), int(day))
            raw_data.append(row)
            
    except mysql.connector.Error as err:
            print("battle:\n:", err)
            cb_cursor.close()
            await channel.send('Oops, something went wrong while fetching the data...')
            return

    print(raw_data)

    # sift records
    sift_data = []
    #((wave,boss,day),(eid,nick,dmg))
    for eid, nick, hits_all, day in raw_data:
        for hitm in hit_all: # hit_all -> [("wave-boss:dmg", "wave-boss:dmg", "wave-boss:dmg.wave-boss:dmg"),...]
            for indiv in hitm.split('.'): # indiv -> ["wave-boss:dmg", ...]
                if search in indiv:
                    wbm, dmg = indiv.split(':')
                    wave, boss = wbm.split('-')
                    sift_data.append(
                        ((int(wave), int(boss), day), (eid, nick, int(dmg)))
                         )
                    
    # split by mode
    skip = False
    sort_data = []
    if mode == 'wave':
        key = lambda x: x[0][1]
        max_ = max(sift_data, key=key)
        
    elif mode == 'boss':
        key = lambda x: x[0][0]
        max_ = max(sift_data, key=key)
    else:
        sort_data.append(sift_data)
        skip = True

    if not skip:
        for i in range(1,max_):
            temp = []
            for hit_data in sift_data:
                if mode == 'wave' and hit_data[0][1] == i:
                    temp.append(hit_data)
                elif mode == 'boss' and hit_data[0][0] == i:
                    temp.append(hit_data)
            sort_data.append(temp)

    # sort by dmg
    key = lambda x: x[1][2]
    for i in len(sort_data):
        sort_data[i].sort(reverse=True, key=key)

    # sorted data in the form
    # [
    #   Wave/Boss1
    #   [((wave, boss, day), (eid, nick, dmg)),
    #    ((wave, boss, day), (eid, nick, dmg)),
    #    ((wave, boss, day), (eid, nick, dmg))...
    #   ],
    #   Wave/Boss2
    #   [...],
    #   ...
    # ]
    seperator = '-'*20
    embed = discord.Embed(title="CB Battle Report",
                          description="Fetched records matching {:s}. Prepared by yours truly.".format(search),
                          timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="still in testing")
    if mode == 'all':
        embed.add_field(name="Wave {:d} Boss {:d}".format(sort_data[0][0][0][0], sort_data[0][0][0][1]),
                        value=seperator, inline=False)
        embed.add_field(name="EID",
                        value='\n'.join(
                            [field[1][0]+"-"+field[1][1] for field in sort_data[0]]),
                        inline=True
                        )
        embed.add_field(name="Day",
                        value="\n".join([field[0][1] for field in sort_data[0]]),
                        inline=True
                        )
        embed.add_field(name="Damage",
                        value="\n".join([field[1][2] for field in sort_data[0]]),
                        inline=True
                        )
    elif mode == 'boss':
        for wave in sort_data:
            embed.add_field(name="Wave {:d}".format(wave[0][0][0]),
                        value=seperator, inline=False)
            embed.add_field(name="EID",
                            value='\n'.join(
                                [field[1][0]+"-"+field[1][1] for field in wave]),
                            inline=True
                            )
            embed.add_field(name="Day",
                            value="\n".join([field[0][1] for field in wave]),
                            inline=True
                            )
            embed.add_field(name="Damage",
                            value="\n".join([field[1][2] for field in wave]),
                            inline=True
                            )
    else:
        print(sort_data)
        for boss in sort_data:
            embed.add_field(name="Boss {:d}".format(wave[0][0][1]),
                        value=seperator, inline=False)
            embed.add_field(name="EID",
                            value='\n'.join(
                                [field[1][0]+"-"+field[1][1] for field in boss]),
                            inline=True
                            )
            embed.add_field(name="Day",
                            value="\n".join([field[0][1] for field in boss]),
                            inline=True
                            )
            embed.add_field(name="Damage",
                            value="\n".join([field[1][2] for field in boss]),
                            inline=True
                            )

    await channel.send(embed=embed)
    return
        
        
    
    
                    
                
            






































