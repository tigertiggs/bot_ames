"""
Ames
help
"""

import datetime
import discord
import cb_help as cb

COMMANDS = [
    (".help [options]",
     "Bring up this dialogue.\n"\
     "Options include: [cb, cbtag, tag, shitpost]")
     ,
    ('.gacha [rolls|default=10]',
     "Have Ames simulate your luck in Princonne gacha.")
    ,
    ('.chara [character]',
     'Bring up UB and skill descriptions for the specified character.\n'\
     '[ue] suffix depreciated. Instead switch between pages with the arrows at '\
     'the bottom of the embed.',
     '.c')
    ,
    ('.cb [args]',
     "Please use [.help cb] for further details. [currently unavailable]")
    ,
    ('.guide [chara]',
     'Have Ames bring up a guide for the character specified. [warning: questionable authenticity at best]')
    ,
    ('.ue [chara]',
     'Show character UE stats, if they have their UE.'
     )
    ,
    ('.tag [*args]',
     'Search for character(s) that have the specified tags')
    ,
    ('.spark',
     'Do 300 rolls and have Ames bring up a gacha summary')
    ,
    ('.pos [options]',
     'Have Ames bring up the ordering of units in battle. Use [v] for Vanguards, [m] for Midguards or '\
     '[r] for Rearguards. Alternatively, you may enter in a [character] to see their position within '\
     'their field'
     )
    ,
    ('.cbtag [*args]',
     'Assign yourself a boss role during CB so you can be pinged should the boss be available.\n'\
     'Use .help cbtag for more options')
]

SHITPOST = [
    ('.find [emoji_name|optional]',
     "Search/list emojis Ames have access to currently across multiple servers.")
    ,
    ('.emoji [emoji_name]',
     "Have Ames send an emoji she has access to.",
     ".e")
    ,
    ('.big [emoji]',
     "When small emojis simply won't do.",
     '.b')
    ,
    (".mind [*text]",
     "Change my mind.")
    ,
    (".threat [user_tag|default=self]",
     "Threaten someone.")
    ,
    (".nero [*text]",
     "Have nero share your thoughts. Enter in a single line for the best effect.")
    ,
    ('.neroe [emoji]',
     "Have nero share your emoji. [Limited support for animated emojis]")
    ,
    ('.location [user_tag|default=self]',
     "Someone probably need to know this.",
     ".loc")
    ,
    ('.police [user|default=self]',
     'Someone is going to jail.',
     ".pol .lolipol")
    ,
    ('.dumbass [user_tag|optional]',
     'Call someone out for being a dumbass',
     ".dumb")
    ,
    ('.read', ':shioread:')
    ,
    ('.enty# [user_tag|optional]',
     'Officer Enterprise, it\'s him!\n# can represent 1, 2 or 3, or leave it blank.'
     )
    ,
    ('.spray [user_tag|optional]',
     "For bullying.",
     '.s')
    ,
    ('.dead',
     ':makotodead:')
    ]

CBTAG = [
    (".cbtag",
     "Have Ames show you current available tags and the number of people assigned to each boss")
    ,
    (".cbtag [*boss_num]",
     "Manually assign the boss role to yourself via the boss number")
    ,
    (".cbtag post",
     "Have Ames send an embed where guild members can react and be assigned a boss role. Further instruction "\
     "Are on the embed")
    ,
    (".cbtag purge",
     "Remove all boss roles from yourself")
    ,
    (".cbtag edit [boss_num] [name]",
     "Edit the boss's name")
    ]


def command(command, info, aliases=""):
    if aliases:
        return '\n'.join(['\n'+command, 'aliases: '+aliases, info+'\n'])
    else:
        return '\n'.join(['\n'+command, info+'\n'])

def constructor(command_list):
    # sort
    command_list.sort(key=lambda x: x[0][1])

    body = ""
    for cmd in command_list:
        if len(cmd) == 2:
            body += command(cmd[0], cmd[1])
        else:
            body += command(cmd[0], cmd[1], aliases=cmd[2])

    return body

async def ames_help(ctx, inpv, emj):
    channel = ctx.channel
    author = ctx.message.author

    if len(inpv) == 0:
        inp = ""
    else:
        inp = inpv[0]
    
    if inp == "cb":
        await cb.help(ctx)
        return

    header = "```css\n"\
             "[Ames - Commands]\n{:s}\n```"

    print(inp)
    if inp == 'shitpost':
        header = header.format(constructor(SHITPOST))
    elif inp == 'tag':
        header = tag_help(inpv[1:])
    elif inp == 'cbtag':
        header = header.format(constructor(CBTAG))
    else:
        header = header.format(constructor(COMMANDS))

    await channel.send(header)
    return

def tag_help(options):
    message = "Use `.help tag basic` for basic tags\n"\
              "Use `.help tag atk` for tags about attack characteristics\n"\
              "Use `.help tag buff` for buff/debuff tags"

    print(options)
    if len(options) == 0:
        return message
    
    if options[0] == 'basic':
        header = "```md\n"\
                 "[Ames - Basic Tags]()\n{:s}\n```"
        tags = TAGS_BASIC
        
    elif options[0] == 'atk':
        header = "```md\n"\
                 "[Ames - Attack Characteristics Tags]()\n{:s}\n```"
        tags = TAGS_ATK
        
    elif options[0] == 'buff':
        header = "```md\n"\
                      "[Ames - Buff/Debuff Tags]()\n{:s}\n```"
        tags = TAGS_BUFF

    else:
        return message

    tags.sort(key=lambda x: x[0][2])
              
    for index in range(len(tags)):
        tags[index] = "\n\t".join(tags[index])
    
    info = "\n".join(tags)

    header = header.format(info)

    return header

TAGS_BASIC = [
    ('# physical',    'Physical attacker'),
    ('# magic',       'Magic attacker'),
    ('# front',       'Vanguard position'),
    ('# mid',         'Midguard position'),
    ('# rear',        'Rearguard position'),
    ('# ue',          'Unique Equipment/Character Weapon available'),
    ('# limited',     'Character availability limited to special events'),
    ('# seasonal',    'Character availability limited to seasonal events'),
    ('# prinfes',     'Character availability limited to Princess Festivals')
    ]
TAGS_ATK = [
    ('# aoe',         'Union Burst is AOE'),
    ('# ranged',      'Skills target past the frontmost enemy'),
    ('# p_target',    'UB/skills target the strongest enemy physical attacker'),
    ('# m_target',    'UB/skills target the strongest enemy magic attacker'),
    ('# self_harm',   'UB/skills consume HP and/or inflict self debuffs'),
    ('# self_sust',   'UB/skills recover caster\'s HP'),
    ('# self_buff',   'UB/skills buff the caster'),
    ('# ailment',     'UB/skills inflict status ailment(s)'),
    ('# special',     'UB/skills have special mechanics not covered by tags')
    ]
TAGS_BUFF = [
    ('# matk_up',     'Magic attack up'),
    ('# patk_up',     'Physical attack up'),
    ('# mcrit_up',    'Magic critical chance up'),
    ('# pcrit_up',    'Physical critical chance up'),
    ('# matk_down',   'Magic attack down'),
    ('# patk_down',   'Physical attack down'),
    ('# mdef_up',     'Magic defense up'),
    ('# pdef_up',     'Physical defense up'),
    ('# mdef_down',   'Magic defense down'),
    ('# pdef_down',   'Physical defense down'),
    ('# atkspd_up',   'Attack speed up'),
    ('# atkspd_down', 'Attack speed down'),
    ('# movespd_up',  'Movement speed up'),
    ('# movespd_down','Movement speed down'),
    ('# tp_up',       'Recover TP'),
    ('# tp_down',     'Penalize TP'),
    ('# tp_steal',    'tp_down on target and tp_up on self'),
    ('# pshield',     'Physical shield (damage nullification)'),
    ('# mshield',     'Magic shield (damage nullification)'),
    ('# pbarrier',    'Physical barrier (damage to HP conversion)'),
    ('# mbarrier',    'Magic barrier (damage to HP conversion)'),
    ('# heal',        'Recover HP'),
    ('# taunt',       'Applies taunt on self')
    ]

    
    
     
















    
