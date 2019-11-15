"""
Ames
guide
"""
import discord
import datetime
import ast

from misc import randcolour as rc

async def guide(ctx, chara, flags, emj):
    channel = ctx.channel
    author = ctx.message.author  
    func = 'guide: '

    # get icon
    get_chara_list = ("SELECT unit_name_eng , unit_name, image "
                      "FROM hatsune_bot.charadata")

    try:
        cursor = flags['cb_db'].cursor()
        cursor.execute(get_chara_list, )
    except mysql.connector.Error as err:
        print('chara:\n', err)
        cursor.close()
        await channel.send(emj['shiori'])
        return
    else:
        chara_list = []
        chara_list_jp = []
        url = []
        for (_name, _namejp, _img) in cursor:
            chara_list.append(str(_name).lower())
            chara_list_jp.append(str(_namejp))
            url.append(str(_img))

    if chara in chara_list:
        icon = url[chara_list.index(chara)]
    elif chara in chara_list_jp:
        icon = url[chara_list_jp.index(chara)]
        chara = chara_list[chara_list_jp.index(chara)].lower()
    else:
        cursor.close()
        await channel.send(emj['kasumi']+"I didnt find that character. Please use their full name.")
        return

    # try to read guide file, if exists
    try:
        with open('guide/{:s}.txt'.format(chara.lower()),'r') as f:
            txtf = f.read()
            profile = ast.literal_eval(txtf)
    except Exception as e:
        print(func + 'failed to open file', e)
        await channel.send(emj['maki'] + 'Guide has not been written yet')
        return

    #make embed
    embed = discord.Embed(title="Name",description=profile['name'], timestamp=datetime.datetime.utcnow(), colour=rc())
    embed.set_author(name="Character Guide (questionable authenticity)", icon_url=author.avatar_url)
    embed.set_footer(text="still in testing")
    embed.set_thumbnail(url=icon)

    embed.add_field(
        name="Position",value=profile['pos'],
        inline=False
        )
    embed.add_field(
        name="Notable Roles",value=profile['role'],
        inline=True)
    embed.add_field(
        name="Rec. Setup",value="{0:d}⭐ Rank {1:d}".format(profile['rank'][0], profile['rank'][1]),
        inline=True)
    embed.add_field(
        name="UE",value=uerec(profile['ue']),
        inline=True)
    embed.add_field(
        name="Brief",value=profile['brief'],
        inline=False)
    embed.add_field(
        name="Strategy",value=profile['strat'],
        inline=False)
    embed.add_field(
        name="Tips",value=dd(profile['do'],profile['dont']),
        inline=False)
    embed.add_field(
        name="Recommended Teams",value=profile['team'],
        inline=False)

    await channel.send(embed=embed)
    print(func+'success')
    return
    
def dd(yes, no):
    yes = "\n".join(["+ " + point for point in yes])
    no = "\n".join(["- " + point for point in no])
    total = "```diff\nDO:\n{0:s}\nDON\'T:\n{1:s}```".format(yes,no)
    return total
    
def uerec(key):
    if key == 0:    return 'Not available'
    elif key == 1:  return 'Available, but mediocre'
    elif key == 2:  return 'Available, but not a necessity'
    elif key == 3:  return 'Available, and recommended'
    else:           return 'N/A'
    
















    
