"""
Ames
log - wave-boss
"""
import discord
import datetime
import _checks as ck
import asyncio

async def log(ctx, hit_v, flags, emj, client):
    channel = ctx.channel
    user_id = ctx.message.author.id
    name = ctx.message.author.name
    error = emj['shiori']
    maki = emj['maki']

    # check input length
    if len(hit_v) > 3:
        print('logtest: too many inputs')
        await channel.send(error)
        return

    mode = len(hit_v)
    if hit_v.count('0') == 3:
        print('logtest: reset request detected')
        reset = True
    else:
        reset = False

    # check if current cb is set
    if not flags['current_cb']:
        print('logtest: current_cb is not set')
        await channel.send(maki+'Could not log - current CB not set!')
        return

    # check if current cb has concluded
    if flags['cb_concluded']:
        print('logtest: cb has concluded')
        await channel.send(maki+'Could not log - CB has ended!')
        return
    
    # grab cb_id and current day
    cb_id = int(flags['current_cb'])
    day = ck._getday(cb_id, flags)

    print(day)
    
    # check if cb has been initiated
    if day == 0:
        print('logtest: day was None - start a new day!')
        await channel.send(maki+'Could not log - CB hasn\'t started!')
        return
    
    # unpack hit_v
    if not reset:
        hit_v = list(hit_v)
        totdmg = []
        meta = []
        for log_ in hit_v:
            tempsum = []
            tempmeta = []
            for hit in log_.split('+'):
                # check if input is of form wave-boss:dmg
                # check if wave-boss is valid and do sanity check on numbers
                print(hit)
                try:
                    meta_, dmg = hit.split(':')
                except:
                    print('logtest: could not split metadata:dmg in a hit')
                    await channel.send(error+' There was an error when trying to read your `metadata:damage` input near **hit{:d}**.'.format(hit_v.index(log_)+1))
                    return
                try:
                    wave, boss = meta_.split('-')
                except:
                    print(error+'logtest: could not split wave-boss in metadata of a hit')
                    await channel.send(error+' There was an error when trying to read your `wave-boss` input near **hit{:d}**.'.format(hit_v.index(log_)+1))
                    return
                try:
                    wave_check = int(wave)
                    boss_check = int(boss)
                    dmg_int = int(dmg)
                    if wave_check <= 0 or boss_check <= 0 or boss_check > 6 or wave_check > 25:
                        print('logtest: bad wave-boss input - failed sanity check')
                        await channel.send(error+' One or more of your wave-boss input is too wild')
                        return
                except:
                    print('logtest: invalid inputs')
                    await channel.send(error+' Did not recognise/read input type near **hit{:d}**. Make sure you used integers.'.format(hit_v.index(log_)+1))
                    return
                
                tempsum.append(dmg_int)
                tempmeta.append(':'.join([meta_,dmg]))
                
            totdmg.append(sum(tempsum))
            meta.append(".".join(tempmeta))
    else:
        totdmg = [0,0,0]
        meta = ['0-0:0','0-0:0','0-0:0']

    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE discord_tag LIKE '%{:d}%' LIMIT 1".format(user_id))
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(find_mid, )
        m_id = 0
        for _m_id in cb_cursor:
            m_id = int(_m_id[0]) 
    except mysql.connector.Error as err:
        print("logtest:\n:", err)
        cb_cursor.close()
        await channel.send('Something went wrong while fetching your records!')
        return
    
    if m_id == 0:
        print('logtest: no matching m_id')
        await channel.send('<:shioread:449255102721556490> I couldn\'t find your records, {:s}'.format(name))
        return

    
    # find existing records and append if nessecary
    find_log = ("SELECT "
                "entry_id, hit1, hit1meta, hit2, hit2meta, hit3, hit3meta from cb.cb_log WHERE "
                "cb_id = {0:d} AND day = {1:d} AND m_id = {2:d} "
                "LIMIT 1".format(cb_id, int(day), m_id))
    print(find_log)
    try:
        cb_cursor.execute(find_log, )
        for eid, hit1, hit1m, hit2, hit2m, hit3, hit3m in cb_cursor:
            ex_hits = [int(hit1), int(hit2), int(hit3)]
            m_hits = [str(hit1m), str(hit2m), str(hit3m)]
            eid = int(eid)  
    except mysql.connector.Error as err:
        print("logtest:\n:", err)
        cb_cursor.close()
        await channel.send('Oops, something went wrong...')
        return
    
    hits_left = ex_hits.count(0)
    # prompt overwrite
    if hits_left == 0 and not reset:
        def check(message):
            return str(message.author.id) == str(user_id) and message.channel == channel
        
        await channel.send(emj['maki']+'You have already logged **3** hits for **day {:d}**. '\
                           "**Do you wish to overwrite, {:s}?** `yah/nah`".format(int(day), name))
        
        while True:
            try:
                msg = await client.wait_for('message', timeout=10.0, check=check)
                print(msg.content)
                if msg.content.lower().split()[0][0] == 'y':
                    print('log: overwriting logs')
                    await channel.send('overwriting current day\'s logs...')
                    break
                elif msg.content.lower().split()[0][0] == 'n':
                    await channel.send(emj['sarenh']+'Got it! Cancelling command.')
                    print('log: cancelling overwrite')
                    return
                else:
                    continue
            except asyncio.TimeoutError:
                await channel.send(emj['sarens']+'I\'ll take that as a no, {:s}. Cancelling overwite!'.format(name))
                print('log: cancelling overwrite')
                return
            except Exception as e:
                print(e)
                continue
            
        
        

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
            flags['cb_db'].commit()
        except mysql.connector.Error as err:
            print("logtest:\n:", err)
            cb_cursor.close()
            await channel.send('Oops, something went wrong while writing your log...')
            return

        if not reset:
            await channel.send("Successfully updated your **day {0:d}** log, **{1:s}**!"\
                               " You have **{2:d} hits remaining**. Ganbarimasu!".format(day, name, 3-hits))
        else:
            await channel.send("Successfully **reset** your **day {0:d}** log, **{1:s}**!"\
                               " You have **{2:d} hits remaining**. Ganbarimasu!".format(day, name, 3-hits))
            
        print('log: success')
        return
    else:
        await channel.send("**{0:s}**, it is currently **day {1:d}** of CB and you have **{2:d} hits** remaining. "\
                           "Ganbarimasu!".format(name, day, hits_left))
        print('log: success')
        return
