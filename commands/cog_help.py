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
        temp = [item for item in list(self.help_text.values()) if target in item['flags'] and ((not item['hidden'] and not "restricted" in item['flags']) or perm)]
        temp.sort(key=lambda x: x['usage'])
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
                        temp.append(f"[Aliases] {' '.join(cmd[key])}")
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
                if option in ["normal", "shitpost", "restricted", "core", "hatsune", "_update", "_gacha", "cb", "admin", "twitter"]:
                    data = self.filter_commands(option, self.client._check_author(ctx.message.author, option))
                else:
                    await self.process_options(channel, options, author)
                    return
            
            help_page_controller = self.client.page_controller(self.client, self.make_help_embed, data, 9, True)
            page = await channel.send(embed=help_page_controller.start())
            for arrow in help_page_controller.arrows:
                await page.add_reaction(arrow)
            
            def author_check(reaction, user):
                return str(user.id) == str(author.id) and str(reaction.emoji) in help_page_controller.arrows and str(reaction.message.id) == str(page.id)
            
            while True:
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=author_check)
                except asyncio.TimeoutError:
                    await page.clear_reactions()
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
            
            tag_page_controller = self.client.page_controller(self.client, self.make_tag_embed, data, 10, True)
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
        temp = [f"{value}\n```md\n# {key}```" for key, value in data]
        temp.sort(key=lambda x: x[2])
        return temp
    
    def make_tag_embed(self, data, index):
        embed = discord.Embed(
            title=f"Tag Definitions (page {index[0]} of {index[1]})",
            description="A list of tag definitions that are used in `.tag`.\n{}".format("\n".join(self.make_tag_text(data))),
            timestamp=datetime.datetime.utcnow(),
            colour=self.colour
        )
        embed.set_footer(text="Tag Definitions | Re:Re:Write Ames", icon_url=self.client.user.avatar_url)
        return embed

    def make_help_embed(self, data, index):
        embed = discord.Embed(
            title=f"Help (page {index[0]} of {index[1]})",
            description="Command documentation and usage.\nMost commands have more detailed instructions accessible by using `.help [full_command_name]`.\nCommands are displayed in `groups` that are fetched via `.help [group_name]`, defaulting to `.help normal`.\nCurrent groups are:\n{}.\n```css\n{}```".format(" ".join([f"`{i}`" for i in self.command_tags]),"\n\n".join(self.make_help_text(data))),
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

    async def process_options(self, channel, options, author):
        option = options[0]
        command = self.help_text.get(option, None)
        if command != None:
            if self.client._check_author(author):
                await channel.send(embed=self.make_extended_help(command))
            elif "admin" in command['flags'] and self.client._check_author(author, "admin"):
                await channel.send(embed=self.make_extended_help(command))
            elif not  "admin" in command['flags']:
                await channel.send(embed=self.make_extended_help(command))
            else:
                await channel.send("Command is restricted "+self.client.emotes['ames'])

def setup(client):
    client.add_cog(helpCog(client))