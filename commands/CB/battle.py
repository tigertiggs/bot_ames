"""
Ames
battle
"""

import discord
import datetime
import _checks as ck

async def battle(ctx, bat:str, flags, emj):
    channel = ctx.channel
    author = ctx.message.author
    error = emj['shiori']

    # usual checks
    # check if current cb is set
    if not flags['current_cb']:
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return

    # check if current cb has concluded
    if flags['cb_concluded']:
        print('log: current_cb is not set')
        await channel.send('Could not log - current CB not set!')
        return
    
    # grab cb_id
    cb_id = int(flags['current_cb'])

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
             "ORDER BY day ASC".format(cb_id, search))

    raw_data = []
    try:
        cursor = flags['cb_db'].cursor(buffered=True)
        cursor.execute(fetch, )
        for eid, nick, hit1m, hit2m, hit3m, day in cursor:
            nick = str(nick)
            if len(nick) > 15:
                nick = nick[:15] + '...'
            row = (int(eid), nick, (str(hit1m), str(hit2m), str(hit3m)), int(day))
            raw_data.append(row)
            
    except mysql.connector.Error as err:
            print("battle:\n:", err)
            cursor.close()
            await channel.send('Oops, something went wrong while fetching the data...')
            return

    print(raw_data)
    
    if len(raw_data) == 0:
        print('battle: no data fetched')
        await channel.send(error + ' No data found')
        return

    # sift records
    sift_data = []
    #((wave,boss,day),(eid,nick,dmg))
    for eid, nick, hits_all, day in raw_data:
        for hitm in hits_all: # hit_all -> [("wave-boss:dmg", "wave-boss:dmg", "wave-boss:dmg.wave-boss:dmg"),...]
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
        max_ = max(sift_data, key=key)[0][1]
        #print(max_)
        
    elif mode == 'boss':
        key = lambda x: x[0][0]
        max_ = max(sift_data, key=key)[0][0]
        #print(max_)
    else:
        sort_data.append(sift_data)
        skip = True

    if not skip:
        for i in range(1,max_+1):
            temp = []
            for hit_data in sift_data:
                if mode == 'wave' and hit_data[0][1] == i:
                    temp.append(hit_data)
                elif mode == 'boss' and hit_data[0][0] == i:
                    temp.append(hit_data)
                
            sort_data.append(temp)

    # sort by dmg
    key = lambda x: x[1][2]
    for i in range(len(sort_data)):
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
    seperator = '||'+':'*60+'||'
    embed = discord.Embed(title="CB Battle Report",
                          description="Fetched records matching <{:s}>. Prepared by yours truly.".format(search),
                          timestamp=datetime.datetime.utcnow())
    embed.set_footer(text="still in testing")
    if mode == 'all':
        embed.add_field(value=seperator + " **[ Wave {:d} Boss {:d} ]** ".format(sort_data[0][0][0][0], sort_data[0][0][0][1]) + seperator,
                        name=". ", inline=False)
        embed.add_field(name="EID",
                        value='\n'.join(
                            [str(field[1][0])+"-"+field[1][1] for field in sort_data[0]]),
                        inline=True
                        )
        embed.add_field(name="Day",
                        value="\n".join([str(field[0][2]) for field in sort_data[0]]),
                        inline=True
                        )
        embed.add_field(name="Damage",
                        value="\n".join([str(field[1][2]) for field in sort_data[0]]),
                        inline=True
                        )
    elif mode == 'boss':
        for wave in sort_data:
            if wave:
                embed.add_field(value=seperator + " **[ Wave {:d} ]** ".format(wave[0][0][0]) + seperator,
                            name=". ", inline=False)
                embed.add_field(name="EID",
                                value='\n'.join(
                                    [str(field[1][0])+"-"+field[1][1] for field in wave]),
                                inline=True
                                )
                embed.add_field(name="Day",
                                value="\n".join([str(field[0][2]) for field in wave]),
                                inline=True
                                )
                embed.add_field(name="Damage",
                                value="\n".join([str(field[1][2]) for field in wave]),
                                inline=True
                                )
    else:
        for boss in sort_data:
            #print(boss[0][0][1])
            if boss:
                embed.add_field(value=seperator + " **[ Boss {:d} ]** ".format(boss[0][0][1]) + seperator,
                                name=". ", inline=False)
                embed.add_field(name="EID",
                                value='\n'.join(
                                    [str(field[1][0])+"-"+field[1][1] for field in boss]),
                                inline=True
                                )
                embed.add_field(name="Day",
                                value="\n".join([str(field[0][2]) for field in boss]),
                                inline=True
                                )
                embed.add_field(name="Damage",
                                value="\n".join([str(field[1][2]) for field in boss]),
                                inline=True
                                )

    await channel.send(embed=embed)
    return
