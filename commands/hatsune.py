"""
Ames
Hatsune
"""
import datetime

import discord
from discord.ext.commands import Bot
from discord.ext import commands

import mysql.connector
from mysql.connector import errorcode

from misc import randcolour as rc
from prototype import get_team as gt

import asyncio

#BYPASS
def hatsune_check(members):
    return False
    for member in members:
        if str(member.id) == '580194070958440448' and str(member.status) == 'online':
            return True
        else:
            continue
    return False

def get_chara(flags, ue=False):
    chara_list = []
    chara_list_jp = []
    id_list = []

    # this should always return something
    if ue:
        get_chara_list = ("SELECT unit_id, unit_name_eng , unit_name "
                          "FROM princonne.chara_data_final "
                          "WHERE tag LIKE '%ue%'")
    else:
        get_chara_list = ("SELECT unit_id, unit_name_eng , unit_name "
                          "FROM princonne.chara_data_final")
    
    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get_chara_list, )
    except mysql.connector.Error as err:
        print('chara:\n', err)
    else:
        for (_uid, _name, _namejp) in cursor:
            chara_list.append(str(_name).lower())
            chara_list_jp.append(str(_namejp))
            id_list.append(str(_uid))

    cursor.close() 
    return chara_list, chara_list_jp, id_list
    

def get_id(target, chara_list, chara_list_jp, id_list):

    if target in chara_list:
        ind = chara_list.index(target)
        target_id = id_list[ind]
        
    elif target in chara_list_jp:
        ind = chara_list_jp.index(target)
        target_id = id_list[ind]

    else:
        target_id = -1
        ind = -1

    return target_id, ind

def get_skill_names(target, flags):
    func = 'get_skill_names:'
    skills = dict()

    get_uid = ("SELECT unit_id FROM hnote.unit_data "
               "WHERE unit_name = '{:s}' "
               "ORDER BY unit_id ASC LIMIT 1".format(target))
    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get_uid, )
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        return skills
    else:
        uid = False
        for out in cursor:
            uid = str(out[0])
            print(uid)

    brackets =  ['「','」']
    if not uid:
        tba = 'TBA'
        skills['ub'] = tba.join(brackets)
        skills['sk1'] = tba.join(brackets)
        skills['sk2'] = tba.join(brackets)
        skills['sk1p'] = tba.join(brackets)
        return skills
        
    prefix =    uid[:4]
    ub =        '001'
    sk1 =       '002'
    sk2 =       '003'
    sk1p =      '012'
    ex =        '501'
    exp =       '502'

    get_skills = ("SELECT skill_id, name FROM hnote.skill_data "
                  "WHERE skill_id REGEXP '{:s}...'".format(prefix))

    try:
        cursor.execute(get_skills, )
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        return skills
    else:
        for skill_id, name in cursor:
            name = str(name)
            identifier = str(skill_id)[-3:]
            #print(skill_id)
            if      identifier == ub:    skills['ub'] = name.join(brackets)
            elif    identifier == sk1:   skills['sk1'] = name.join(brackets)
            elif    identifier == sk2:   skills['sk2'] = name.join(brackets)
            elif    identifier == sk1p:  skills['sk1p'] = name.join(brackets)
            else:
                print(func, 'unknown or ignored skill_id', skill_id)
                
    cursor.close()
    if 'sk1p' not in skills.keys():
        temp = skills['sk1']
        skills['sk1p'] = temp[:-1]+'+'+temp[-1:]
    return skills

async def hatsune_chara(ctx, name, ue, flags, emj, client):
    channel = ctx.channel
    func = 'chara:'
    author = ctx.message.author
    
    # check hatsune
    """
    if hatsune_check(ctx.message.guild.members):
        print('chara: hatsune is online - exiting lmao')
        await channel.send(emj['kasumi']+'Hatsune is currently available. Please bother her instead.')
        return
    else:
        print('chara: hatsune offline')
    """

    if name == "":
        await channel.send(emj['maki']+'Where was no input\n'+
                           "In case you forgot, the prefixes are:\n"+
                           "`n` for New year i.e. `nrei`\n"+
                           "`x` for Christmas i.e. `xayane`\n"+
                           "`o` for Ouedo i.e. `oninon`\n"+
                           "`v` for Valentines i.e. `vshizuru`\n"+
                           "`s` for Summer i.e. `sio`")
        return
    else:
        #name = name[0]
        target = name.lower()
        #print(target)

    chara_list, chara_list_jp, id_list = get_chara(flags)

    target_id, ind = get_id(target, chara_list, chara_list_jp, id_list)
    
    if target_id == -1:
        print(func, 'did not find character')
        await channel.send(emj['maki']+'I did not find that character\n'+
                           "Make sure you used prefixes correctly:\n"+
                           "`n` for New year i.e. `nrei`\n"+
                           "`x` for Christmas i.e. `xayane`\n"+
                           "`o` for Ouedo i.e. `oninon`\n"+
                           "`v` for Valentines i.e. `vshizuru`\n"+
                           "`s` for Summer i.e. `sio`")
        return

    skills = get_skill_names(chara_list_jp[ind], flags)

    # this should always return 1 non-Null result
    get_chara_data = ("SELECT image, unit_name_eng, "
                      "ub_trans, skill_1_translation, skill_2_trans, "
                      "comment_trans, tag, skill_1_plus_trans, "
                      "unit_name, union_burst, skill_1, skill_1_plus, skill_2, comment "
                      "FROM princonne.chara_data_final "
                      "WHERE unit_id = {:d}".format(int(target_id)))
    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get_chara_data, )
    except mysql.connector.Error as err:
        print('chara:\n', err)
        cursor.close()
        await channel.send(emj['shiori'])
        return
    else:
        data = dict()
        for (_i, _name, _ub, _sk1, _sk2, _c, _t, _sk1p, unjp, ubjp, sk1jp, sk1pjp, sk2jp, cjp) in cursor:
            
            name = str(_name)
            if name[1].isupper():
                prefix = name[0]
                if      prefix == 'S':  limited = 'Summer'
                elif    prefix == 'H':  limited = 'Halloween'
                elif    prefix == 'X':  limited = 'Xmas'
                elif    prefix == 'N':  limited = 'New Year'
                elif    prefix == 'O':  limited = 'Ouedo'
                elif    prefix == 'V':  limited = 'Valentine'
                
                else:
                    print(func, 'no valid prefix matched')
                    limited = ""

                name = ' '.join([limited, name[1:]])
                
            data['uname_eng'] =     name
            data['im'] =            str(_i)
            data['ub_eng'] =        str(_ub)
            data['sk1_eng'] =       str(_sk1)
            data['sk2_eng'] =       str(_sk2)
            data['comment_eng'] =   str(_c)
            data['tags'] =          str(_t)
            data['sk1p_eng'] =      str(_sk1p)
            data['uname'] =         str(unjp)
            data['ub'] =            str(ubjp)
            data['sk1'] =           str(sk1jp)
            data['sk1p'] =          str(sk1pjp)
            data['sk2'] =           str(sk2jp)
            data['comment'] =       str(cjp)
        cursor.close()

    #print(data)
    lr = ['⬅','➡']
    print(name)
    pages = [charaembed(data, ue, skills), await hatsune_ue(ctx, [name.lower()], flags, emj, mode=True)]
    
    page = await channel.send(embed=pages[0])
    for push in lr:
        await page.add_reaction(push)

    def check(reaction, user):
        #print(str(user.id) == str(author.id),reaction.emoji in lr, str(reaction.message.id) == str(elist.id))
        return str(user.id) == str(author.id) and reaction.emoji in lr and str(reaction.message.id) == str(page.id)

    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            print('timeout')
            for arrow in lr:
                await page.remove_reaction(arrow, client.user)
            break
        else:
            if reaction.emoji == '⬅':
                pages = pages[-1:] + pages[:-1]
                await reaction.message.remove_reaction('⬅', author)
                await reaction.message.edit(embed=pages[0])

            elif reaction.emoji == '➡':
                pages = pages[1:] + pages[:1]
                await reaction.message.remove_reaction('➡', author)
                await reaction.message.edit(embed=pages[0])

            else:
                continue
        
    
    print('chara: successful!')
    return

def charaembed(data, ue, skills):
    remark, comment = data['comment_eng'].replace('\t',"").replace('\n','').split('*')[:2]
    
    embed = discord.Embed(title="{1:s}\n{0:s}".format(data['uname_eng'],data['uname']),
                          description=remark,
                          timestamp=datetime.datetime.utcnow(),
                          colour=rc())
    
    #embed.set_image(url='https://redive.estertion.win/card/profile/101231.webp')
    
    embed.set_author(name="Character Profile")
    embed.set_footer(text="still in testing")

    embed.add_field(name='Comment\n'+data['comment'],value=comment,inline=False)
    
    if data['im'] != 'None':
        embed.set_thumbnail(url=data['im'])

    if data['uname_eng'] != 'Onion':
        embed.add_field(name="\n".join(["Union Burst "+skills['ub'],data['ub']]), value=data['ub_eng'])
    else:
        embed.add_field(name="\n".join(["Onion Burst "+skills['ub'],data['ub']]), value=data['ub_eng'])
    
    if ue == "":
        embed.add_field(name="\n".join(["Skill 1 "+skills['sk1'],data['sk1']]), value=data['sk1_eng'])
    else:
        embed.add_field(name="\n".join(["Skill 1 + "+skills['sk1p'],data['sk1p']]), value=data['sk1p_eng'])
        
    embed.add_field(name="\n".join(["Skill 2 "+skills['sk2'],data['sk2']]),value=data['sk2_eng'])
    
    if len(data['tags']) == 0: 
        embed.add_field(name='Tags', value="No tags yet", inline=False)
    else:
        embed.add_field(name='Tags', value=data['tags'], inline=False)
    return embed

async def hatsune_ue(ctx, chara, flags, emj, mode=False):
    channel = ctx.channel
    func = "ue:"
    
    # check hatsune
    """
    if hatsune_check(ctx.message.guild.members):
        print('chara: hatsune is online - exiting lmao')
        await channel.send(emj['kasumi']+'Hatsune is currently available. Please bother her instead.')
        return
    else:
        print('chara: hatsune offline')
    """

    if len(chara)==0:
        await channel.send(emj['maki']+"There was no input.\n"\
                           "In case you forgot, the prefixes are:\n"+
                           "`n` for New year i.e. `nrei`\n"+
                           "`x` for Christmas i.e. `xayane`\n"+
                           "`o` for Ouedo i.e. `oninon`\n"+
                           "`v` for Valentines i.e. `vshizuru`\n"+
                           "`s` for Summer i.e. `sio`")
        return
    else:
        chara = chara[0]
        target = chara.lower()

    chara_list, chara_list_jp, id_list = get_chara(flags, ue=True)

    target_id, ind = get_id(target, chara_list, chara_list_jp, id_list)
    
    if target_id == -1:
        print(func, 'did not find character')
        await channel.send(emj['maki']+"I did not find that character. "\
                           "Either check your spelling, or the character doesn\'t have UE yet.\n"+
                           "Make sure you used prefixes correctly:\n"+
                           "`n` for New year i.e. `nrei`\n"+
                           "`x` for Christmas i.e. `xayane`\n"+
                           "`o` for Ouedo i.e. `oninon`\n"+
                           "`v` for Valentines i.e. `vshizuru`\n"+
                           "`s` for Summer i.e. `sio`")
        return

    skills = get_skill_names(chara_list_jp[ind], flags)

    # this should always return 1 row
    get_ue_data = ("SELECT * FROM princonne.chara_unique_equipment "
                   "WHERE unit_id = {:s}".format(target_id))

    try:
        cursor = flags['cb_db'].cursor(buffered=True)
        cursor.execute(get_ue_data, )
        
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        await channel.send(emj['shiori'])
        return
    
    else:
        data = dict()
        for (uid, uname, uname_eng, eqname, eqname_trans, eqrk,
             patk, pcrit, matk, mcrit, tp, tpc, hp, pdef, mdef, eva, acc, recv, ahp,
             im) in cursor:

            # unpack
            #data['uid'] =           uid
            data['uname'] =         str(uname)
            data['uname_eng'] =     str(uname_eng)
            data['eqname'] =        str(eqname)
            data['eqname_eng'] =    str(eqname_trans)
            data['rank'] =          str(eqrk)
            data['im'] =            str(im)

            # unpack stats
            raw =       [str(patk), str(pcrit), str(matk), str(mcrit), str(tp), str(tpc),
                         str(hp), str(pdef), str(mdef), str(eva), str(acc), str(recv), str(ahp)]
            stats =     ['patk', 'pcrit', 'matk', 'mcrit', 'tp up', 'tp cost', 'hp', 'pdef',
                         'mdef', 'dodge', 'acc', 'recovery', 'regen']
            
            zipstats = zip(stats, raw)
            filtered = []
            
            for stat in zipstats:
                if stat[-1] != '-':
                    filtered.append(stat)

            data['stats'] = filtered
            
    # get skills
    get_chara_data = ("SELECT skill_1_translation, skill_1_plus_trans, "
                      "skill_1, skill_1_plus "
                      "FROM princonne.chara_data_final "
                      "WHERE unit_id = {:s}".format(target_id))
    try:
        cursor.execute(get_chara_data, )
        
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        await channel.send(emj['shiori'])
        return
    else:
        for (skill1_eng, skill1p_eng, skill1, skill1_p) in cursor:
            
            data['sk_1'] =      str(skill1)
            data['sk_1_eng'] =  str(skill1_eng)
            data['sk_1p'] =     str(skill1_p)
            data['sk_1p_eng'] = str(skill1p_eng)
    if mode:
        return ue_embed(data, skills)
    else:
        await channel.send(embed=ue_embed(data, skills))
    print(func, 'success')
    cursor.close()
    return

def ue_embed(data, skills):
    embed = discord.Embed(title=data['eqname'],
                          description=data['eqname_eng'],
                          timestamp=datetime.datetime.utcnow(),
                          colour=rc())
    
    embed.set_thumbnail(url=data['im'])
    embed.set_author(name="{:s}'s Unique Equipment".format(data['uname_eng']))
    embed.set_footer(text="still in testing")
    embed.add_field(
        name='Rank',
        value=data['rank'],
        inline=False)
    
    embed.add_field(
        name='Stat Gain',
        value='Base/Max (lv140)\n'+'-'*40,
        inline=False)

    for stat in data['stats']:
        embed.add_field(
            name=stat[0].upper(),
            value=stat[1],
            inline=True)

    embed.add_field(
        name='\n'.join(['Skill 1 '+skills['sk1'], data['sk_1']]),
        value=data['sk_1_eng'],
        inline=True)

    embed.add_field(
        name='\n'.join(['Skill 1+ '+skills['sk1p'],data['sk_1p']]),
        value=data['sk_1p_eng'],
        inline=True)

    return embed

async def hatsune_tag(ctx, tags, flags, emj, client):
    channel = ctx.channel
    func = 'tag:'
    
    if len(tags) == 0:
        print(func, 'no inputs')
        await channel.send(emj['kasumi']+\
                           'No inputs found. Use .help tags for tags you can use')
        return

    otags = " ".join([tag.strip() for tag in " ".join(tags).replace(",", " ").split()])
    
    tags = ["'%"+tag.strip()+"%'" for tag in " ".join(tags).replace(",", " ").split()]
    tags = " AND tag LIKE ".join(tags)
    
    get_charas = ("SELECT unit_name, unit_name_eng "
                  "FROM princonne.chara_data_final "
                  "WHERE tag LIKE "+tags+
                  " ORDER BY unit_name_eng")

    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get_charas, )
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        await channel.send(emj['shiori'])
        return
    else:
        names = []
        jpnames = []
        #emojis = []
        team = gt(client)
        for name_jp, name in cursor:
            name = str(name)
            try:
                emoji = team['template'].format(name.lower(), team[name.lower()])
            except Exception as err:
                print(func, err)
                emoji = ""
            
            if name[1].isupper():
                prefix = name[0]
                if      prefix == 'S':  limited = 'Summer'
                elif    prefix == 'H':  limited = 'Halloween'
                elif    prefix == 'X':  limited = 'Xmas'
                elif    prefix == 'N':  limited = 'New Year'
                elif    prefix == 'O':  limited = 'Ouedo'
                elif    prefix == 'V':  limited = 'Valentine'
                
                else:
                    print(func, 'no valid prefix matched')
                    limited = ""

                name = ' '.join([limited, name[1:]])
                
            names.append(emoji + " " + name)
            jpnames.append(str(name_jp))

    cursor.close()

    if len(names) == 0 or len(jpnames) == 0:
        print(func, 'no chara found')
        await channel.send(emj['kasumi']+'No characters with lookup tags found. Use `.help tag` if you\'re unsure about existing tags.')
        return

    print(len(names))
    await channel.send(embed=tag_embed(names,jpnames,otags))

def tag_embed(names, jpnames, tags):
    #print(names)
    #print(jpnames)
    #print(tags)
    embed = discord.Embed(title="Search Results",
                          description="{:d} results returned for tags matching `{:s}`".format(
                              len(names),tags),
                          timestamp=datetime.datetime.utcnow(),
                          colour=rc())
    
    #embed.set_image(url='https://redive.estertion.win/card/profile/101231.webp')
    
    embed.set_author(name="Tag Search")
    embed.set_footer(text="still in testing")
    """
    embed.add_field(
        name="Name",
        value="\n".join(jpnames),
        inline=True)
    """
    names = list(chunks(names, 20))
    for name_chunk in names:                    
        embed.add_field(
            name="Characters",
            value="\n".join(name_chunk),
            inline=True)

    return embed
        
def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]                       

async def hatsune_pos(ctx, guard, flags, emj, client):
    channel = ctx.channel
    func = 'pos:'

    if len(guard) == 0:
        print(func, 'no input')
        await channel.send(emj['shiori']+'No input detected.\n'\
                           'Use v for vanguard, m for midguard and r for rearguard'
                           )
        return
    
    # check if guard is a character
    guard = guard[0].lower()
    
    chara_list, chara_list_jp, id_list = get_chara(flags)
    target_id, ind = get_id(guard, chara_list, chara_list_jp, id_list)

    if target_id == -1:
        # pos
        mode = 'pos'
        
        if      guard[0] == 'v':    p = 'front'
        elif    guard[0] == 'm':    p = 'mid'
        elif    guard[0] == 'r':    p = 'rear'
        else:
            print(func, 'invalid input')
            await channel.send(emj['shiori']+'No input detected.\n'\
                           'Use v for vanguard, m for midguard and r for rearguard'
                           )
            return
    else:
        # chara - find position
        mode = 'chara'
        get_pos = ("SELECT tag FROM princonne.chara_data_final WHERE unit_id = {:s}".format(str(target_id)))

        try:
            cursor = flags['cb_db'].cursor()
            cursor.execute(get_pos, )
        except mysql.connector.Error as err:
            print(func, err)
            cursor.close()
            await channel.send(emj['shiori'])
            return
        else:
            for tag in cursor:
                tags = str(tag[0]).split(", ")

            cursor.close()
                
            if 'front' in tags:     p = 'front'
            elif 'mid' in tags:     p = 'mid'
            else:                   p = 'rear'

    get = ("SELECT unit_name_eng, pos "
            "FROM princonne.chara_data_final "
            "WHERE tag LIKE '%{:s}%' ORDER BY pos".format(p))
    
    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get, )
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        await channel.send(emj['shiori'])
        return
    else:
        names = []
        """
        numbers = [":{:s}:".format(number) for number in
                   ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
                   ]
        """
        team = gt(client)
        i = 1
        for name, pos in cursor:
            #find number
            name = str(name)
            pos = str(pos)
            #print(pos)
            if pos == 'None':
                pos = '??'
                i -= 1
            else:
                pos = i
            #print(name)
            """
            num_word = []
            for value in str(i):
                num_word.append(numbers[int(value)])
            num_word = " ".join(num_word)
            """

            #find emoji
            try:
                emoji = team['template'].format(name.lower(), team[name.lower()])
            except Exception as err:
                print(func, err)
                emoji = ""

            if name[1].isupper():
                prefix = name[0]
                if      prefix == 'S':  limited = 'Summer'
                elif    prefix == 'H':  limited = 'Halloween'
                elif    prefix == 'X':  limited = 'Xmas'
                elif    prefix == 'N':  limited = 'New Year'
                elif    prefix == 'O':  limited = 'Ouedo'
                elif    prefix == 'V':  limited = 'Valentine'
                
                else:
                    print(func, 'no valid prefix matched')
                    limited = ""

                _name = ' '.join([limited, name[1:]])
            else:
                _name = name

            if mode == 'chara':
                print(name.lower(), chara_list[ind].lower())
                if name.lower() == chara_list[ind].lower():
                    target = _name
                    _name = "**{:s}**".format(_name)
                    names.append(" ".join(["> "+emoji, "**{:s}**".format(str(pos)), _name]))
                else:
                    names.append(" ".join([emoji, str(pos), _name]))
            else:
                names.append(" ".join([emoji, str(pos), _name]))
            i += 1
            
    #print(names)
    if mode == 'chara':
        await channel.send(embed=pos_embed(names, mode, p, target))
    else:
        await channel.send(embed=pos_embed(names, mode, p))

    cursor.close()
    return

def pos_embed(names, mode, p, target=""):
    if      p == 'front':   p = 'vanguard'
    elif    p == 'mid':     p = 'midguard'
    else:                   p = 'rearguard'

    body = "Listing **{:s}** lineup. ".format(p.upper())
    if mode == 'chara':
        body += "Bolding **{:s}'s** position".format(target)
    
    embed = discord.Embed(title="Lineup",
                          description=body,
                          timestamp=datetime.datetime.utcnow(),
                          colour=rc())
    
    embed.set_author(name="Tag Search")
    embed.set_footer(text="still in testing")

    names = list(chunks(names, 20))

    for names_chunk in names:
        embed.add_field(
            name="Character",
            value="\n".join(names_chunk),
            inline=True)

    return embed
    
        






























