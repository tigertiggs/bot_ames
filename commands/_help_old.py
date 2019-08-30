"""
Ames
help
"""

import datetime
import discord
import cb_help as cb

async def ames_help(ctx, inp, emj):
    channel = ctx.channel
    author = ctx.message.author
    
    if inp == "cb":
        await cb.help(ctx)
        return

    embed = discord.Embed(
        title='Ames Help',
        description='This is what I can do ' + emj['sarenh'],
        timestamp=datetime.datetime.utcnow()
        )
    embed.set_footer(text="still in testing")
    
    embed.add_field(
        name="> help",
        value="Bring up this dialogue.",
        inline=False)
    
    embed.add_field(
        name="> mind `*text`",
        value="Challenge others with that you think.",
        inline=False)
    
    embed.add_field(
        name="> threat `user|optional`",
        value="Force someone to your will, or else.",
        inline=False)

    embed.add_field(
        name="> nero `*text`",
        value="Have nero share your thoughts.",
        inline=False)

    embed.add_field(
        name="> neroe `emoji`",
        value="Have nero share your emoji.",
        inline=False)

    embed.add_field(
        name="> location `user|optional`",
        value="You/someone would probably need to know this.\nAliases: `loc`",
        inline=False)

    embed.add_field(
        name="> police `user|optional`",
        value="You/someone is going to jail.\nAliases: `pol` `lolipol`",
        inline=False)

    embed.add_field(
        name="> gacha `rolls|default=10`",
        value="Have Ames simulate your luck.",
        inline=False)

    embed.add_field(
        name="> big `emoji`",
        value="When small emojis are simply won't do.\nAliases: `b`",
        inline=False)

    embed.add_field(
        name="> chara `character`",
        value="When Hatsune is dead.\nAliases: `c`",
        inline=False)

    embed.add_field(
        name="> cb `param`",
        value="Please use `help cb` for further details.",
        inline=False)

    await channel.send(embed=embed)
    return
    
