import discord
from discord.ext import commands
import datetime, time, os, sys, requests, random, ast
dir = os.path.dirname(__file__)

class proxyCommand:
    def __init__(self, usage:str, help:str, **kwargs):
        self.usage = usage
        self.help = help
        self.aliases = kwargs.get('aliases', [])
        self.hidden = kwargs.get('hidden', False)

default = [
    'hatsuneCog',
    'gachaCog',
    'statusCog'
]
default_additional = [
    proxyCommand(
        '.help shitpost',
        'Ames doesn\'t like it, but she has no choice. Bring up shitpost commands.',
    ),
    proxyCommand(
        '.help cb',
        'Bring up CB-related help. This command is currently guild restricted and WIP, but may expand to include other guilds with due time.'
    ),
    proxyCommand(
        '.help tag',
        'Bring up tag-related help.'
    ),
    proxyCommand(
        '.help alias',
        'Bring up alias-related help.'
    )
]

shitpost = [
    'shenCog',
    'shenpCog'
]

cb = [
    'cbCog'
]
cb_additional = [
    proxyCommand(
        '.cbtag [*boss_num]',
        'Toggle the following boss numbers from yourself.'
    ),
    proxyCommand(
        '.cbtag post',
        'Have Ames send a report for the boss wait list for your guild. Further instructions on embed.'
    ),
    proxyCommand(
        '.cbtag purge',
        'Remove all boss tags from yourself.'
    ),
    proxyCommand(
        '.cbtag edit [boss_n] [descr]',
        'Edit the specified boss\'s tag name',
        hidden=True
    ),
    proxyCommand(
        '.cbtag reset',
        'Reset all boss names',
        hidden=True
    )
]

alias = [
    proxyCommand(
        '.alias',
        'List all local and master aliases.'
    ),
    proxyCommand(
        '.alias add [keyword] [character]',
        'Add the following alias to the character. Keyword is case-insensitive and character must match a valid name in the database. The keyword must not already exist. The keyword cannot be in the master alias list.'
    ),
    proxyCommand(
        '.alias remove [keyword]',
        'Remove the local alias.',
        aliases=['rm']
    ),
    proxyCommand(
        '.alias check [keyword]',
        'Search for the alias.',
        aliases=['ck']
    ),
    proxyCommand(
        '.alias edit [keyword] [character]',
        'Edit the character alias. Basically functions the same way as .alias add. Master aliases cannot be edited.',
        aliases=['ed']
    )
]
class helpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = client.log
        self.name = '[Help]'
        #self.active = client.config.get('help',True)
    
    async def active_check(self, channel):
        if self.client.get_config('help') is False:
            await channel.send(self.client.error()['inactive'])
            await self.logger.send(self.name, 'command disabled')
            return False
        else:
            return True
    
    def make_hhelp(self):
        text1 = "**How to interpret the documentation [README]**\n"
        embed = ("In the documentation you will encounter any combination of the notations explained below. This small help segment only appear with `.help`\n"
                "```css\n"
                    "[Square brackets used in documentation] only serve as a visual guide (only noticable on discord desktop) and is not part of the input\n\n"
                    ".example_0 something\nenter [.example_0 something] to use this command\n\n"
                    ".example_1 [argument]\nThis command will not function unless an [argument] is specified\n\n"
                    ".example_2 [*arguments]\nThis command accepts multiple [arguments] separated by a space\n\n"
                    ".example_3 [argument = default value]\nThis command accepts an [argument] but will assume a default value if left blank\n\n"
                    ".example_4 [argument|optional]\n This command's input argument is optional and will work if left blank\n\n"
                    ".example_5\n[Aliases]: tiggsisdumb\nthis command can be called with .tiggsisdumb\n\n"
                    ".example_6 [argument:type]\nThis command accept an argument of a particular type; for example: text, URL, :discord_emote:, @user_ping, etc.\n\n"
                "```")
        return text1+embed

    def make_help_embed(self, functions, name, **kwargs):
        functions.sort(key=lambda x: x[1])

        tag = kwargs.get('tag', False)
        if not tag:
            help_embed = '```css\n{}```'.format("\n\n".join(functions))
        else:
            help_embed = '```md\n{}```'.format("\n".join(functions))

        embed = discord.Embed(
            title="Ames Help",
            description=f"{name}\n{help_embed}",
            timestamp=datetime.datetime.utcnow()
            )
        embed.set_footer(text="Help | SHIN Ames", icon_url=self.client.user.avatar_url)
        return f"{name}\n{help_embed}"

    async def construct_functions(self, cogs:list, cog_additional:list=[], **kwargs):
        functions = []
        tag = kwargs.get('tag', False)
        if not tag:
            for cogName in cogs:
                cog = self.client.get_cog(cogName)
                if cog != None:
                    for cmd in cog.get_commands():
                        cog_additional.append(cmd)
                else:
                    await self.logger.send(self.name, 'failed to load commands from', cogName)
            
            for cmd in cog_additional:
                if not cmd.hidden and not cmd.usage is None:
                    if len(cmd.aliases) != 0:
                        txt = f'{cmd.usage}\n[Aliases]: {" ".join(cmd.aliases)}\n{cmd.help}'
                    else:
                        txt = f"{cmd.usage}\n{cmd.help}"
                    functions.append(txt)
        else:
            for (tagName, descr) in cogs:
                txt = f"{tagName}\n\t{descr}"
                functions.append(txt)

        return functions

    @commands.group(
        invoke_without_command=True,
        case_sensitive=False
    )
    async def help(self, ctx):
        active = await self.active_check(ctx.channel)
        if not active:
            return
        
        if ctx.invoked_subcommand is None:
            functions = await self.construct_functions(default.copy(), default_additional.copy())
            await ctx.channel.send(self.make_hhelp())
            await ctx.channel.send(self.make_help_embed(functions, "Active Commands"))

    @help.command()
    async def shitpost(self, ctx):
        functions = await self.construct_functions(shitpost.copy(), [])
        await ctx.channel.send(self.make_help_embed(functions,"Shitpost"))

    @help.command()
    async def cb(self, ctx):
        functions = await self.construct_functions(cb.copy(), cb_additional.copy())
        await ctx.channel.send(self.make_help_embed(functions,"Clan Battle"))
    
    @help.command()
    async def alias(self, ctx):
        functions = await self.construct_functions([], alias.copy())
        await ctx.channel.send(self.make_help_embed(functions,"Alias"))

    @help.group(
        invoke_without_command=True,
        case_sensitive=False
    )
    async def tag(self, ctx):
        if ctx.invoked_subcommand is None:
            functions = await self.construct_functions([], tag_additional.copy())
            await ctx.channel.send(self.make_help_embed(functions, "Tag Help"))
    
    @tag.command()
    async def basic(self, ctx):
        functions = await self.construct_functions(TAGS_BASIC.copy(), [], tag=True)
        print(functions)
        await ctx.channel.send(self.make_help_embed(functions, "Basic Tags", tag=True))
    
    @tag.command()
    async def atk(self, ctx):
        functions = await self.construct_functions(TAGS_ATK.copy(), [], tag=True)
        await ctx.channel.send(self.make_help_embed(functions, "Attack Tags", tag=True))
    
    @tag.command()
    async def buff(self, ctx):
        functions = await self.construct_functions(TAGS_BUFF.copy(), [], tag=True)
        await ctx.channel.send(self.make_help_embed(functions, "Buff/Debuff Tags", tag=True))
    
tag_additional = [
    proxyCommand(
        '.help tag basic',
        'Bring up basic tag definitions.'
    ),
    proxyCommand(
        '.help tag atk',
        'Bring up attack tag definitions.'
    ),
    proxyCommand(
        '.help tag buff',
        'Bring up buff/debuff tag characteristics.'
    )
]
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

def setup(client):
    client.add_cog(helpCog(client))