import discord, asyncio, random

DURATION =      60*30
COOLDOWN =      60*15
PLAYING =       0
STREAMING =     1
LISTENING =     2
WATCHING =      3
ACTIVITIES = [
    discord.Activity(name='with Hatsune',               type=discord.ActivityType(PLAYING)),
    discord.Activity(name='Panda\'s complaints',        type=discord.ActivityType(LISTENING)),
    discord.Activity(name='with Aria\'s luck',          type=discord.ActivityType(PLAYING)),
    discord.Activity(name='with gacha rates',           type=discord.ActivityType(PLAYING)),
    discord.Activity(name='the collapse of the USSR',   type=discord.ActivityType(WATCHING)),
    discord.Activity(name='PrincessConnect Re:dive',    type=discord.ActivityType(STREAMING))
    ]

async def playing(client):
    while True:
        await client.change_presence(activity=random.choice(ACTIVITIES))
        await asyncio.sleep(random.randrange(DURATION-60*5,DURATION+60*20))
        await client.change_presence(activity=None)
        await asyncio.sleep(random.randrange(COOLDOWN-60*5,COOLDOWN+60*15))

EXPRESSIONS = [
    'ames.png',
    'ames_yan.png'
    ]

async def expression(client):
    while True:
        dp = open(random.choice(EXPRESSIONS), 'rb')
        await client.user.edit(avatar=dp.read())
        await asyncio.sleep(random.randrange(240*60, 300*60))