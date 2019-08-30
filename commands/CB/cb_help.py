"""
Ames
cb help
"""

import datetime
import discord

COMMANDS = []
SPEC_COMMANDS = []

def command(command, info, aliases=""):
    if aliases:
        return '\n'.join(['\n'+command, aliases, info+'\n'])
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

async def help(ctx):
    channel = ctx.channel
    author = ctx.message.author

    embed = discord.Embed(
        title="cb help",
        description="This is what I can do surrounding CB.",
        timestamp=datetime.datetime.utcnow()
        )
    embed.set_footer(text="still in testing")

    header = "```css\n"\
             "[Ames - Clan Battle Commands]\n{:s}\n```"

    body = ""
    body += command('.help cb', "Bring up this dialogue.")

    if _perm(author):
        headerspec = "```css\n"\
             "[Ames - Clan Battle Special Commands]\n{:s}\n```"

        bodyspec = ""
        
        bodyspec += command('.cb startday', "Conclude the current day and have Ames load all next day's records, "\
                        "advancing the day value. This affects [.cb pcb] and [.cb log] commands.")
        
        bodyspec += command('.cb removelog [entry_id/EID]', "Delete the following entry from the database.")

        bodyspec += command('.cb reload [guild]', "Refresh the roster by adding the difference between the current guild roster "\
                        "and any new members with the corresponding [guild] role.")

        bodyspec += command('.cb updatemember [m_id] [field|options: nick, active] [value]', "Update a member's field with the correspinding `m_id`.")

        bodyspec += command('.cb removemember [m_id]', "Remove this the member with the corresponding `m_id` from the roster. "\
                        "Note that this will also delete their log data.")

        bodyspec += command('.cb newcb [date|yyyy-mm-dd] [length_days|default=8] [override|default=1]', "Create a new CB entry and automatically set it as the current CB if `override` is 1.")

        bodyspec += command('.cb setcb [cb_id|default=current]', "Have Ames set the current CB with the specified [cb_id] as the global. "
                        "If not specified, she will look for an active CB in the database.")

        bodyspec += command('.cb removecb [cb_id]', "Have Ames remove all records connected to this CB. This will delete all "\
                        "associated logs in the database.")
            
        bodyspec += command('.cb updatecb [cb_id] [field|options: date, length, active] [value]', "Update the specified field for the corresponding [cb_id].")

        bodyspec += command('.cb concludecb [mode|default=1]', "Have Ames wrap up the CB and aggregate all data collected and display it, if "\
                        "`mode is 1`.")
        await channel.send(headerspec.format(bodyspec))

    body += command('.cb pcb', "Have Ames tell you the current CB and day.",)

    body += command('.cb log [*wave-boss:damage]', "Log your current day's hit. You may join hits that finish a boss with `+` "\
                    "and reset your hits with `log 0 0 0`.")

    body += command('.cb listlogs [cb_id|default=current] [day|default=current]', "Have Ames fetch the logs for the specified day of the specified CB. "\
                    "If both fields are left blank they will default to the current CB and current day."\
                    "If `cb_id` is provided, `day` must also be provided.")

    body += command('.cb battle [wave-boss]', "Have Ames fetch the records for a certain boss/wave or both. "\
                    "You may use the asterisk `*` to indicate wildcard.")

    body += command('.cb listmembers [mode|optinal]', "Have Ames fetch the current guild roster. With no inputs she will fetch all "\
                    "`active` members, `mode->0` all `inactive` members, and `mode->1` for all members.")

    body += command('.cb statscb [cb_id|default=current]', "Have Ames fetch the details for the specified CB. If nothing is specified, "\
                    "she will look for the current set CB.")

    body += command('.cb listcb', "Have Ames fetch the records of the latest 10 CBs in the database.")

    body += command('.cb mrep [nickname OR m_id/MID] [cb_id|default=current]', "Have Ames fetch the logs for the specified member during the specified CB. "\
        "If `cb_id` is not provided, she will default to the current CB.")

    await channel.send(header.format(body))
    return

# CB perm
def _perm(author):
    tiggs = '235361069202145280'
    if str(author.id) != tiggs: return False
    else: return True







        
