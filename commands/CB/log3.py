"""
Ames
log - simple
"""

import discord
import datetime
import _checks as ck
import asyncio

# log hit1 hit2 hit3 day|optional
# async def log(*hitv:str, **day)

async def log(ctx, hit_v, flags, emj, client):
    channel = ctx.channel
    user_id = ctx.message.author.id
    name = ctx.message.author.name
    func = 'log:'

    # check flags
    if not flags['current_cb']:
        print(func, 'current_cb is not set')
        await channel.send(emj['maki']+'Could not log - current CB not set!')
        return
    
    if flags['cb_concluded']:
        print(func, 'cb has concluded')
        await channel.send(emf['maki']+'Could not log - CB has ended!')
        return

    # input processing
    mode = len(hit_v)
    cb_id = int(flags['current_cb'])
    
    if mode > 4:
        print(func, 'too many inputs')
        await channel.send(emj['maki'] + 'Too many inputs')
        return
    
    elif mode == 4:
        print(func, 'day override mode')
        day = int(hit_v.pop())
        day_check = ck._getday(cb_id, flags)
        mode -= 1
        
        if day <= 0:
            print(func, 'invalid day override')
            await channel.send(emj['maki'] + 'invalid day input')
            return
        elif day > day_check:
            print(func, 'day value greater than current day')
            await channel.send(emj['shiori'] + 'cannot enter in future days')
            return
    else:
        day = ck._getday(cb_id, flags)

        if not day:
            print(func, 'CB day has not started')
            await channel.send(emj['maki']+'Could not log - CB hasn\'t started!')
            return

    if hit_v.count('0') == 3:
        print(func, 'reset detected')
        totdmg = [0,0,0]
    else:
        totdmg = []
        for hit in hit_v:
            temp = 0
            for indiv in hit.split('+'):
                try:
                    temp += int(indiv)
                except Exception as e:
                    print(func, e)
                    await channel.send(emj['maki'] + 'error while reading hit near {:s}'\
                                       .format(hit))
                    return
                
            totdmg.append(temp)
    











        
