"""
Ames
prototypes
"""

import asyncio
import discord
import difflib
import datetime
from misc import randcolour as rc

import os
import glob
from PIL import Image

def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]

def webptpng():
    for webp in glob.glob("gacha/units/*.webp"):
        #print(webp[12:-5])
        im = Image.open(webp)
        im.save("gacha/units/png/{:s}.png".format(webp[12:-5]))
        im.close()

async def reload_emotes(client):
    # resource servers
    func = 'reload_emotes:'
    guilds = client.guilds
    shed1 = '613628290023948288'
    shed2 = '613628508689793055'
    LIMIT = 50

    # grab existing emotes
    """
    shed1_emotes = []
    shed2_emotes = []
    
    for guild in guilds:
        if str(guild.id) == shed1:
            for emoji in guild.emojis:
                shed1_emotes.append(emoji.name)
                    
        elif str(guild.id) == shed2:
            for emoji in guild.emojis:
                shed2_emotes.append(emoji.name)

    total_emotes = len(shed1_emotes) + len(shed2_emotes)
    """
    
    # update /png
    webptpng()

    # get all new png names
    png = []
    for file in glob.glob('gacha/units/png/*.png'):
        #print(file[16:-4])
        png.append(file[16:-4])
    total_new_png = len(png)
    png = list(chunks(png, LIMIT))

    # delete existing emotes
    print(func, 'deleting emotes')
    i = 1
    for guild in guilds:
        if str(guild.id) == shed1 or str(guild.id) == shed2:
            # delete all existing emojis
            for emoji in guild.emojis:
                print(func, 'deleting', (i,total_emotes), emoji.name, emoji.id, 'from', guild.name)
                await emoji.delete()
                i += 1

    # upload new png
    print(func, 'uploading emotes')
    loc = 'gacha/units/png/{:s}.png'
    i = 1
    for png_chunk in png:
        for guild in guilds:
            if str(guild.id) == shed1 or str(guild.id) == shed2:
                for emote in png_chunk:
                    print(func, 'uploading',(i, total_new_png), emote, 'to', guild.name)
                    #image = discord.File(loc.format(emote))
                    i += 1
                    with open(loc.format(emote), 'rb') as png:
                        #print('opened')
                        await guild.create_custom_emoji(name=emote, image=png.read())
                        #print('uploaded')

    print(func, 'success')
    return
    

def get_team(client):
    shed1 = '613628290023948288'
    shed2 = '613628508689793055'
    shed3 = '639337169508630528'
    sheds = [shed1, shed2, shed3]
    # get dict
    team = dict()
    for guild in client.guilds:
        if str(guild.id) in sheds:
            for emoji in guild.emojis:
                    team[str(emoji.name)] = str(emoji.id)
                
    team['template'] = '<:{:s}:{:s}>'
    #team['tears'] = 
    team['gems'] = '<:yems:426755775839600650>'
    return team

def getemoji(client):
    emj = []
    blacklist = ['redclan']
    for guild in client.guilds:
        #print(guild, guild.id)
        if str(guild.id) != '613628290023948288' and str(guild.id) != '613628508689793055':
            for emoji in guild.emojis:
                if not str(emoji.name) in blacklist:
                    emj.append(
                        (emoji.name,
                         emoji.url,
                         str(emoji.id),
                         emoji.animated,
                         guild.name
                         )
                        )
        emj.sort(key=lambda x: x[0])
    return emj

async def emoji(ctx, target, client, emj):
    channel = ctx.channel
    author = ctx.message.author
    func = 'emoji: '
    norm = '<:{:s}:{:s}>'
    ani = '<a:{:s}:{:s}>'
    
    if target == "":
        print(func + 'no input')
        return

    # fetch all emojis
    emojis = getemoji(client)
    name = [emoji[0] for emoji in emojis]

    # name matching
    cutoff=0.6
    match = difflib.get_close_matches(target, name, n=1, cutoff=cutoff)
    if match:
        index = name.index(match[0])
        await ctx.message.delete()
        embed = discord.Embed(colour=rc())
        embed.set_author(name="{:s} sent:".format(author.name), icon_url=author.avatar_url)
        embed.set_image(url=emojis[index][1])
        await channel.send(embed=embed)
        """
        if animated[index]:
            await channel.send(ani.format(name[index], id_[index]))
        else:
            await channel.send(norm.format(name[index], id_[index]))
        """
        print(func + 'success')
        return
    else:
        await channel.send(emj['maki'] + 'No match!')
        print(func + 'no match')
        return
    
async def listemoji(ctx, target, client, emj):
    channel = ctx.channel
    author = ctx.message.author

    emojis = getemoji(client)
    name = [emoji[0] for emoji in emojis]

    if target != '':
        cutoff=0.6
        match = difflib.get_close_matches(target, name, n=10, cutoff=cutoff)
        if match:
            try:
                match.remove('beetle')
            except:
                pass
            embed = discord.Embed(colour=rc())
            embed.set_author(name="Found emojis", icon_url=author.avatar_url)
            embed.set_footer(text="still in testing")
            
            guilds = []
            animated = []
            for emoji in match:
                index = name.index(emoji)
                guilds.append(emojis[index][4])
                if emojis[index][3]:
                    inp = "True"
                else:
                    inp = "False"
                animated.append(inp)

            embed.add_field(name="Name", value="\n".join(match), inline=True)
            embed.add_field(name="Animated", value="\n".join(animated), inline=True)
            embed.add_field(name="Guild", value="\n".join(guilds), inline=True)

            await channel.send(embed=embed)
        else:
            await channel.send(emj['maki'] + 'No match!')
        return
    else:
        length = len(emojis)
        #await channel.send('emojis available: ' +str(length))
        #await channel.send(emj['maki'] + 'No support for emoji list yet! Search for an emoji instead!')

        # split array
        lr = ['⬅','➡']
        pages = []
        i = 0
        temp = []
        for _ in range(length):
            #print(i)
            temp.append(emojis.pop(0))
            i += 1
            
            if i == 60:
                pages.append(temp)
                temp = []
                i = 0
                
            elif len(emojis) == 0:
                pages.append(temp)
                break

        max_page = len(pages)
        
        elist = await channel.send(embed=emoji_list(pages[0], length, (1,max_page)))
        for push in lr:
            await elist.add_reaction(push)

        #print(elist.reactions)

        # listen for reaction
        def check(reaction, user):
            print(str(user.id) == str(author.id),reaction.emoji in lr, str(reaction.message.id) == str(elist.id))
            
            return str(user.id) == str(author.id) and reaction.emoji in lr and str(reaction.message.id) == str(elist.id)

        temp = pages.copy()
        while True:
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                print('timeout')
                for arrow in lr:
                    await elist.remove_reaction(arrow, client.user)
                break
            else:
                if reaction.emoji == '⬅':
                    temp = temp[-1:] + temp[:-1]
                    await reaction.message.remove_reaction('⬅', author)
                    await reaction.message.edit(embed=emoji_list(temp[0], length, (pages.index(temp[0])+1,max_page)))

                elif reaction.emoji == '➡':
                    temp = temp[1:] + temp[:1]
                    await reaction.message.remove_reaction('➡', author)
                    await reaction.message.edit(embed=emoji_list(temp[0], length, (pages.index(temp[0])+1,max_page)))

                else:
                    continue        

        return
        
def emoji_list(emojis, length, page):
    embed = discord.Embed(
        title="Emoji List - page {:d} of {:d}".format(*page),
        description="Total emotes available: {:d}".format(length),
        timestamp=datetime.datetime.utcnow(),
        colour=rc())
    #embed.set_author(name="Emoji List")
    embed.set_footer(text="still in testing")

    norm = '<:{:s}:{:s}> {:s}'
    ani = '<a:{:s}:{:s}> {:s}'

    emotes = []
    #names = []
    #guilds = []
    i = 0
    temp = []
    for name, url, id, animated, guild in emojis:
        if animated:
            temp.append(ani.format(name,id, name))
        else:
            temp.append(norm.format(name,id, name))
        i += 1
        if i == 20:
            emotes.append(temp)
            temp = []
            i = 0
    
    if i != 0:
        emotes.append(temp)

        #names.append(name)
        #guilds.append(guild)

    for emote in emotes:
        embed.add_field(
            name="Emote - Name",
            value="\n".join(emote),
            inline=True)
    """
    embed.add_field(
        name="Identifier",
        value="\n".join(names),
        inline=True)
    """

    """
    embed.add_field(
        name="Guild",
        value="\n".join(guilds)
        )
    """

    return embed



































            
        
