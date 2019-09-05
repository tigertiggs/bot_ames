"""
Ames
Misc
"""
import random
import discord
import datetime
import ast

async def kill(ctx, flags, emj):
    func = '_kill: '
    channel = ctx.channel
    # only allow author to kill
    if str(ctx.message.author.id) == '235361069202145280':
        await channel.send(emj['sarenh']+"I'll be right back!")
        print(func+'logging off...')
        flags = connect_db(flags,db,0)
        await client.logout()
    else:
        print(func+'user has no authorisation')
        await channel.send(emj['mako'])
        return

def randcolour():
    rc = (random.randint(0,255),
          random.randint(0,255),
          random.randint(0,255))
    
    return discord.Colour.from_rgb(*rc)

def _log(message, log):
    flog = open(log, mode="a+")
    time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    author = message.author.name
    channel = message.channel.name
    guild = message.channel.guild.name
    

    flog.write(" ".join(
        [time, guild, channel, author, message.content, "\n"]))

    flog.close()

def _errlog(message,err, log):
    flog = open(log, mode="a+")
    time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    author = message.author.name
    channel = message.channel.name
    guild = message.channel.guild.name

    flog.write(" ".join(
        [time, guild, channel, author, err, "\n"]))

    flog.close()
        
def alias_check(message, modes=[]):
    with open('commands/_alias.txt', 'r') as file:
        aliasraw = file.read()
        alias = ast.literal_eval(aliasraw)
        
    # check mode
    kw = message
    if kw[-1] in modes:
        kw = kw[:-1]
        mode = kw[-1]
    else:
        mode = ""

    # iterate through
    found = []
    for word in kw:
        try:
            found.append(alias[word])
        except:
            pass
    
    if found == []:
        return (None, mode)
    else:
        found = "".join(found)
        return (found, mode)
