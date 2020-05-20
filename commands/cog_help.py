# contains all of Ames' help functions
import discord
from discord.ext import commands
import datetime, time, os, sys, json, asyncio

class helpCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = "[help]"
        self.logger = client.log
        self.colour = discord.Colour.from_rgb(*client.config['command_colour']['cog_help'])

        with open(os.path.join(self.client.dir,self.client.config['help_path'])) as hf:
            self.help_config = json.load(hf)
            self.help_text = self.help_config["commands"]
            self.command_tags = self.help_config["help_tags"]
        
        with open(os.path.join(self.client.dir, self.client.config['tags_index_path'])) as tf:
            self.help_tag = json.load(tf)
    
    def filter_commands(self, target, perm=False):
        temp = [item for item in list(self.help_text.values()) if target in item['flags'] and (not item['hidden'] or perm)]
        return temp if len(temp)>0 else ["empty"]

    def make_help_text(self, data):
        txt = []
        keys = ['usage', 'aliases', 'help']
        for cmd in data:
            temp = []
            if cmd == "empty":
                return ["No eligible commands matched input flag"]
            for key in keys:
                if cmd[key] != None:
                    #print(cmd[key])
                    if key == 'aliases':
                        temp.append(f"[Aliases]: {' '.join(cmd[key])}")
                    else:
                        temp.append(cmd[key])
            #print(temp)
            txt.append("\n".join(temp))
        txt.sort(key=lambda x: x[1])

        return txt

    @commands.group(invoke_without_command=True)
    async def help(self, ctx, *options):
        channel=ctx.channel
        author=ctx.message.author
        if not self.client.command_status['help'] == 1:
            raise commands.DisabledCommand
        
        if ctx.invoked_subcommand is None:
            perm = self.client._check_author(ctx.message.author)
            if len(options) == 0:
                data = self.filter_commands("normal", perm)
            else:
                option = options[0]
                if option in ["normal", "shitpost", "restricted", "core", "hatsune", "_update", "_gacha", "cb"]:
                    data = self.filter_commands(option, perm)
                else:
                    await self.process_options(channel, options, perm)
                    return
            
            help_page_controller = self.client.page_controller(self.client, self.make_help_embed, data, 12, True)
            page = await channel.send(embed=help_page_controller.start())
            for arrow in help_page_controller.arrows:
                await page.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and str(reaction.emoji) in help_page_controller.arrows and str(reaction.message.id) == str(page.id)
            
            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
                except asyncio.TimeoutError:
                    await page.add_reaction('\U0001f6d1')
                    return
                else:
                    emote_check = str(reaction.emoji)
                    await reaction.message.remove_reaction(reaction.emoji, user)
                    if emote_check in help_page_controller.arrows:
                        if emote_check == help_page_controller.arrows[0]:
                            mode = 'l'
                        else:
                            mode = 'r'     
                        await reaction.message.edit(embed=help_page_controller.flip(mode))

    @help.command(aliases=["d"])
    async def definitions(self, ctx, *option):
        channel = ctx.channel
        author = ctx.message.author
        if not self.client.command_status["help"] == 1:
            raise commands.DisabledCommand
        elif len(option) == 0:
            txt = (
                "> `.help d basic`\n"
                "Fetch basic tag definitions\n"
                "> `.help d atk`\n"
                "Fetch attack tag definitions\n"
                "> `.help d buff`\n"
                "Fetch (de)buff tag definitions"
            )
            await channel.send(txt)
        else:
            option = option[0]
            if option in ['basic', 'atk', 'buff']:
                data = list(self.help_tag[option].items())
            else:
                await channel.send(self.client.emotes['ames'])
                return
            
            tag_page_controller = self.client.page_controller(self.client, self.make_tag_embed, data, 15, True)
            page = await channel.send(embed=tag_page_controller.start())
            for arrow in tag_page_controller.arrows:
                await page.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and str(reaction.emoji) in tag_page_controller.arrows and str(reaction.message.id) == str(page.id)
            
            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
                except asyncio.TimeoutError:
                    await page.add_reaction('\U0001f6d1')
                    return
                else:
                    emote_check = str(reaction.emoji)
                    await reaction.message.remove_reaction(reaction.emoji, user)
                    if emote_check in tag_page_controller.arrows:
                        if emote_check == tag_page_controller.arrows[0]:
                            mode = 'l'
                        else:
                            mode = 'r'     
                        await reaction.message.edit(embed=tag_page_controller.flip(mode))
            
    def make_tag_text(self, data):
        temp = [f"# {key}\n\t{value}" for key, value in data]
        temp.sort(key=lambda x: x[2])
        return temp
    
    def make_tag_embed(self, data, index):
        embed = discord.Embed(
            title=f"Tag Definitions (page {index[0]} of {index[1]})",
            description="A list of tag definitnions that are used in `.tag`.\n```md\n{}```".format("\n".join(self.make_tag_text(data))),
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Tag Definitions | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        return embed

    def make_help_embed(self, data, index):
        embed = discord.Embed(
            title=f"Help (page {index[0]} of {index[1]})",
            description="Command documentation and usage.\nMost commands have their own command page with more detailed instructions and you can access them via `.help [full_command]`.\nYou can view group commands entering `.help [group=normal]`. Current groups are: {}.\n```css\n{}```".format(" ".join([f"`{i}`" for i in self.command_tags]),"\n\n".join(self.make_help_text(data))),
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Help | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        return embed

    def make_extended_help(self, command):
        embed=discord.Embed(
            title="Extended Command Documentation",
            timestamp=datetime.datetime.utcnow(),
            color=self.colour
        )
        embed.set_footer(text="EX Help | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        embed.add_field(
            name="> **Usage**",
            value=f"`{command['usage']}`",
            inline=False
        )
        embed.add_field(
            name="Aliases",
            value="None" if command['aliases'] == None else ", ".join(command['aliases']),
            inline=True
        )
        embed.add_field(
            name="Flags",
            value="".join([f"[{flag}]" for flag in command['flags']]),
            inline=True
        )
        #embed.add_field(
        #    name="Hidden",
        #    value="Yes" if command['hidden'] else "No",
        #    inline=True
        #)
        embed.add_field(
            name="Subcommands",
            value="None" if command['subcmd'] == None else ", ".join(command['subcmd']),
            inline=True
        )
        embed.add_field(
            name="> **Help** ",
            value=command['help'],
            inline=False
        )
        embed.add_field(
            name="> **Extended Help**",
            value="Nothing 'ere" if command['help_ex'] == None else command['help_ex']
        )
        return embed

    async def process_options(self, channel, options, perm=False):
        option = options[0]
        command = self.help_text.get(option, None)
        if command != None:
            if not (command['hidden'] or "restricted" in command['flags']) or perm:
                await channel.send(embed=self.make_extended_help(command))
            else:
                await channel.send("Command is restricted "+self.client.emotes['ames'])

def setup(client):
    client.add_cog(helpCog(client))