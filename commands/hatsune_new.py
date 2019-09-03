"""
Ames
Hatsune new
"""
# This command takes advantage of the ability to edit messages
# this allows .c to be able to combine multiple commands

import datetime
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import mysql.connector
from mysql.connector import errorcode
from misc import randcolour as rc
from prototype import get_team as gt
import asyncio

# globals
HATSUNE = '580194070958440448'

# check if hatsune is online
#BYPASS
def hatsune_check(members):
    return False
    for member in members:
        if str(member.id) == HATSUNE and str(member.status) == 'online':
            return True
        else:
            continue
    return False

# get character list for easy indexing and checking
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

# finds the target id and its index
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

# finds skill names from Hatsune's Notes
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
    #ex =        '501'
    #exp =       '502'

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

#################################################################################################
# ERRORS
hatsune_online =    'Hatsune is currently available. Please bother her instead.'
_help =             "\nIn case you forgot, the prefixes are:\n"\
                    "`n` for New year i.e. `nrei`\n"\
                    "`x` for Christmas i.e. `xayane`\n"\
                    "`o` for Ouedo i.e. `oninon`\n"\
                    "`v` for Valentines i.e. `vshizuru`\n"\
                    "`s` for Summer i.e. `sio`\n"\
                    "`u` for Uniform i.e. `uaoi`"

no_input =          'There was no input'+_help
search_fail =       'Did not find character'+_help



ALIAS = {
    'peco':     'pecorine',
    'pudding':  'miyako',
    'illya':    'ilya'
    }

LR = ['⬅','➡']

# new chara
async def hatsune_chara(ctx, name, flags, emj, client, cmode="", mode="Profile"):
    channel = ctx.channel
    author = ctx.message.author
    func = 'chara:'

    # check hatsune
    if hatsune_check(ctx.message.guild.members):
        print('chara: hatsune is online')
        await channel.send(emj['kasumi']+hatsune_online)
        return
    else:
        pass
        #print('chara: hatsune offline')

    # check input
    if name == "":
        print(func, 'no input')
        await channel.send(emj['maki']+no_input)
        return
    
    # lower case
    target = name.lower()
    print(func, 'target:', target)

    # check for alias
    try:    target = ALIAS[target]
    except: pass

    # get chara list and then chara id
    chara_list, chara_list_jp, id_list =    get_chara(flags)
    target_id, ind =                        get_id(target, chara_list, chara_list_jp, id_list)
    
    # check target_id
    if target_id == -1:
        print(func, 'did not find character')
        await channel.send(emj['maki']+search_fail)
        return

    # get skill names from hatsune's notes
    skills = get_skill_names(chara_list_jp[ind], flags)

    # by this point, we can basically be sure that this chara exists in the db
    # we can now create each indiv pages
    page_headings = ['Profile', 'UE', 'Data', 'Equipment']
    page_req = page_headings.index(mode)

    # chara data - definite
    cdata = _chara_data(target_id, flags)

    # ue data - indefinite
    uedata = _ue_data(target, flags)

    # skill data
    ddata = get_stats(target_id, flags)
    ddata['uname_eng'] = cdata['uname_eng']
    ddata['im'] = cdata['im']

    # equipment data

    # create page embeds
    c_embed = charaembed(cdata, cmode, skills, page_headings.copy(), 0)
    ue_embed = ueembed(uedata, skills, page_headings.copy(), 1)
    d_embed = skillsembed(ddata, page_headings.copy(), 2)

    embeds = [c_embed, ue_embed, d_embed]

    # send initial message
    page = await channel.send(embed=embeds[page_req])
    for arrow in LR:
        await page.add_reaction(arrow)

    # def check
    def check(reaction, user):
        return str(user.id) == str(author.id) and\
               reaction.emoji in LR and\
               str(reaction.message.id) == str(page.id)

    # wait
    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            print('timeout')
            for arrow in LR:
                await page.remove_reaction(arrow, client.user)
            break
        else:
            if reaction.emoji == '⬅':
                embeds = embeds[-1:] + embeds[:-1]
                await reaction.message.remove_reaction('⬅', author)
                await reaction.message.edit(embed=embeds[0])

            elif reaction.emoji == '➡':
                embeds = embeds[1:] + embeds[:1]
                await reaction.message.remove_reaction('➡', author)
                await reaction.message.edit(embed=embeds[0])

            else:
                continue
        
    
    print('chara: successful!')
    return

#############################################################################################
# subfunctions

def get_stats(target_id, flags):
    #WIP
    func = '_stats:'
    data = dict()
    data['max_rank'] = 14
    data['active'] = False

    # grab eq Rank stats
    stats = ("SELECT rank_up from princonne.chara_data_final "
             "WHERE unit_id = {:s}".format(target_id))

    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(stats, )
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        return data
    else:
        for rank in cursor:
            rank = str(rank[0])
            if rank == "Yes":
                data['rank'] = str(data['max_rank'])
            elif rank == 'Maybe':
                data['rank'] = "-".join([str(data['max_rank'] - 1), str(data['max_rank'])])
            elif rank == 'No':
                data['rank'] = str(data['max_rank']-1)
            else:
                data['rank'] = '??'

    return data

#
def skillsembed(data, page_h, ind):
    page_h[ind] = '**[{:s}]**'.format(page_h[ind])
    #star = '⭐'
    uncap = '??'

    embed = discord.Embed(
        title="{:s}'s Data".format(data['uname_eng']),
        description="WIP",
        timestamp=datetime.datetime.utcnow(),
        colour=rc())

    embed.add_field(
        name="Sections",
        value='> '+' - '.join(page_h),
        inline=False)

    embed.set_author(name="Hatsune's Copied Notes")
    embed.set_footer(text='Data page')
    embed.set_thumbnail(url=data['im'])

    embed.add_field(
        name="Rec. Setup",
        value=" ⭐ Rank ".join([uncap, data['rank']]),
        inline=True)

    embed.add_field(
        name="Union Burst",
        value="stats here"+\
        "\n 6star stats here",
        inline=False)

    embed.add_field(
        name="Skill 1",
        value="stats here"+\
        "\n UE stats here",
        inline=False)

    embed.add_field(
        name="Skill 2",
        value="stats here",
        inline=False)

    return embed

    
    
# grab ue data
def _ue_data(target, flags):
    func = '_ue:'
    data = dict()
    chara_list, chara_list_jp, id_list =    get_chara(flags, ue=True)
    target_id, ind =                        get_id(target, chara_list, chara_list_jp, id_list)
    
    if target_id == -1:
        print(func, 'did not find character')
        data['active'] = False
        return data

    get_ue_data = ("SELECT * FROM princonne.chara_unique_equipment "
                   "WHERE unit_id = {:s}".format(target_id))

    try:
        cursor = flags['cb_db'].cursor(buffered=True)
        cursor.execute(get_ue_data, )
        
    except mysql.connector.Error as err:
        print(func, err)
        cursor.close()
        data['active'] = False
        return data
    
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
        data['active'] = False
        return data
    else:
        for (skill1_eng, skill1p_eng, skill1, skill1_p) in cursor:
            
            data['sk_1'] =      str(skill1)
            data['sk_1_eng'] =  str(skill1_eng)
            data['sk_1p'] =     str(skill1_p)
            data['sk_1p_eng'] = str(skill1p_eng)

    data['active'] = True
    return data

def ueembed(data, skills, page_h, ind):
    page_h[ind] = '**[{:s}]**'.format(page_h[ind])
    if data['active']:
        embed = discord.Embed(title=data['eqname'],
                              description=data['eqname_eng'],
                              timestamp=datetime.datetime.utcnow(),
                              colour=rc())
        
        embed.set_thumbnail(url=data['im'])

        embed.add_field(
            name="Sections",
            value='> '+' - '.join(page_h),
            inline=False)
        
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
        
    else:
        embed = discord.Embed(title='No Data',
                              description='This character does not have an UE yet',
                              timestamp=datetime.datetime.utcnow(),
                              colour=rc())

        embed.add_field(
            name="Sections",
            value='> '+' - '.join(page_h),
            inline=False)
        
        embed.set_thumbnail(url='https://redive.estertion.win/icon/equipment/130551.webp')

    #print(page_h)

    embed.set_author(name="Hatsune's Copied Notes")
    embed.set_footer(text='UE page')
    return embed

# grab chara data
def _chara_data(target_id, flags):
    func = '_c:'
    get_chara_data = ("SELECT image, unit_name_eng, "
                      "ub_trans, skill_1_translation, skill_2_trans, "
                      "comment_trans, tag, skill_1_plus_trans, "
                      "unit_name, union_burst, skill_1, skill_1_plus, skill_2, comment, "
                      "image_2, union_burst_2, ub_2_trans "
                      "FROM princonne.chara_data_final "
                      "WHERE unit_id = {:d}".format(int(target_id)))
    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get_chara_data, )
    except mysql.connector.Error as err:
        print('chara:\n', err)
        cursor.close()
        #await channel.send(emj['shiori'])
        return False
    else:
        data = dict()
        for (_i, _name, _ub, _sk1, _sk2, _c, _t, _sk1p, unjp, ubjp, sk1jp, sk1pjp, sk2jp, cjp, _i2, ub2jp, _ub2) in cursor:
            
            name = str(_name)
            if name[1].isupper():
                prefix = name[0]
                if      prefix == 'S':  limited = 'Summer'
                elif    prefix == 'H':  limited = 'Halloween'
                elif    prefix == 'X':  limited = 'Xmas'
                elif    prefix == 'N':  limited = 'New Year'
                elif    prefix == 'O':  limited = 'Ouedo'
                elif    prefix == 'V':  limited = 'Valentine'
                elif    prefix == 'U':  limited = 'Uniform'
                
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
            data['im2'] =           str(_i2)
            data['ub2'] =           str(ub2jp)
            data['ub2_eng'] =       str(_ub2)
        cursor.close()

    return data

def charaembed(data, ue, skills, page_h, ind):
    remark, *comment = data['comment_eng'].replace('\t',"").replace('\n','').split('*')[:2]
    
    if remark == "":
        remark = "Soon"
    if comment == []:
        comment = "Soon"
    else:
        comment = comment[0]
    #print(remark,comment)

    if ue == "mlb":
        title = "{1:s} 6⭐\n{0:s} MLB".format(data['uname_eng'],data['uname'])
    else:
        title = "{1:s}\n{0:s}".format(data['uname_eng'],data['uname'])
        
    embed = discord.Embed(title=title,
                          description=remark,
                          timestamp=datetime.datetime.utcnow(),
                          colour=rc())
    
    #embed.set_image(url='https://redive.estertion.win/card/profile/101231.webp')
    embed.set_author(name="Hatsune's Copied Notes")
    embed.set_footer(text="{:s} page".format(page_h[ind]))

    page_h[ind] = '**[{:s}]**'.format(page_h[ind])
    embed.add_field(
        name="Sections",
        value='> '+' - '.join(page_h),
        inline=False)

    embed.add_field(name='Comment\n'+data['comment'],value=comment,inline=False)

    
    if data['im'] != 'None':
        if ue == "mlb":
            embed.set_thumbnail(url=data['im2'])
        else:
            embed.set_thumbnail(url=data['im'])
    

    if data['uname_eng'] != 'Onion':
        if ue == "mlb":
            embed.add_field(name="\n".join(["Union Burst +",data['ub2']]), value=data['ub2_eng'])
        else:
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





