"""
Ames
cb help
"""

import datetime
import discord

async def help(ctx):
    channel = ctx.channel
    author = ctx.message.author

    embed = discord.Embed(
        title="cb help",
        description="This is what I can do surrounding CB.",
        timestamp=datetime.datetime.utcnow()
        )
    embed.set_footer(text="still in testing")

    embed.add_field(
        name="> help cb",
        value="Bring up this dialogue.",
        inline=False)

    if _perm(author):
        
        embed.add_field(
            name="> cb startday",
            value="Conclude the current day and have Ames load all next day's records, "\
            "advancing the day value. This affects `pcb` and `log` commands.",
            inline=False)
        
        embed.add_field(
            name="> cb removelog `entry_id`",
            value="Delete the following entry from the database.",
            inline=False)

        embed.add_field(
            name="> cb reload `guild`",
            value="Refresh the roster by adding the difference between the current guild roster "\
            "and any new members with the corresponding `guild` role.",
            inline=False)

        embed.add_field(
            name="> cb updatemember `m_id` `field|nick/active` `value`",
            value="Update a member's field with the correspinding `m_id`.",
            inline=False)

        embed.add_field(
            name="> cb removemember `m_id`",
            value="Remove this the member with the corresponding `m_id` from the roster. "\
            "Note that this will also delete their log data.",
            inline=False)

        embed.add_field(
            name="> cb newcb `date|yyyy-mm-dd` `length_days|default=8` `override|default=1`",
            value="Create a new CB entry and automatically set it as the current CB if `override` is 1.",
            inline=False)

        embed.add_field(
            name="> cb setcb `cb_id|optional`",
            value="Have Ames set the current CB with the specified `cb_id` as the global. "
            "If not specified, she will look for an active CB in the database.",
            inline=False)
        
        embed.add_field(
            name="> cb removecb `cb_id`",
            value="Have Ames remove all records connected to this CB. This will delete all "\
            "associated logs in the database.",
            inline=False)

        embed.add_field(
            name="> cb updatecb `cb_id` `field|date/length/active` `value`",
            value="Update the specified field for the corresponding `cb_id`.",
            inline=False)

        embed.add_field(
            name="> cb concludecb `mode|default=1",
            value="Have Ames wrap up the CB and aggregate all data collected and display it, if "\
            "`mode->1`.",
            inline=False)

    embed.add_field(
        name="> cb pcb",
        value="Have Ames tell you the current CB and day.",
        inline=False)

    embed.add_field(
        name="> cb log `*wave-boss:damage`",
        value="Log your current day's hit. You may join hits that finish a boss with `+` "\
        "and reset your hits with `log 0 0 0`.",
        inline=False)

    embed.add_field(
        name="> cb listlogs `cb_id|optional, default=0` `day|optional, default=NULL`",
        value="Have Ames fetch the logs for the specified day of the specified CB. "\
        "If both fields are left blank they will default to the current CB and current day."\
        "If `cb_id` is provided, `day` must also be provided.",
        inline=False)

    embed.add_field(
        name="> cb battle `wave-boss`",
        value="Have Ames fetch the records for a certain boss/wave or both. "\
        "You may use the asterisk `*` to indicate wildcard.",
        inline=False)

    embed.add_field(
        name="> cb listmembers `mode|optional`",
        value="Have Ames fetch the current guild roster. With no inputs she will fetch all "\
        "`active` members, `mode->0` all `inactive` members, and `mode->1` for all members.",
        inline=False)

    embed.add_field(
        name="> cb statscb `cb_id|optional`",
        value="Have Ames fetch the details for the specified CB. If nothing is specified, "\
        "she will look for the current set CB.",
        inline=False)

    embed.add_field(
        name="> cb listcb",
        value="Have Ames fetch the records of the latest 10 CBs in the database.",
        inline=False)

    embed.add_field(
        name="> cb mrep `nick/m_id` `cb_id|optional`",
        value="Have Ames fetch the logs for the specified member during the specified CB. "\
        "If `cb_id` is not provided, she will default to the current CB.",
        inline=False)

    await channel.send(embed=embed)
    return

# CB perm
def _perm(author):
    tiggs = '235361069202145280'
    if str(author.id) != tiggs: return False
    else: return True







        
