# cb help
cb.command(alias=['help'])
async def cbhelp(ctx):
    await channel.send(embed=helpcbembed(ctx))

# EMBEDS

def cbhelpembed(context):
    embed = discord.Embed(title="Clan Battle Command List", description="Here's what I can do", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Help", icon_url=context.message.author.avatar_url)
    embed.add_field(name="pcb",
                    value="I will tell you the current set CB and how far in we are along with its date and `cb_id`.")
    embed.add_field(name="startday",
                    value="I begin finalise yesterday's battle logs and begin a new day, given that I know what the current CB is.\n")
    embed.add_field(name="log `[nick]` `[hit1]` `[hit2]` `[hit3]` `[hits]`",
                    value="I will log the hit data provided for the current member with `nick` given I know the current CB and day. All fields must be provided.\n")
    embed.add_field(name="removelog [`eid`]",
                    value="I will remove the CB log with entry ID `eid`.\n")
    embed.add_field(name="listlogs `[cbid(optional)]` `[day(optional)]`",
                    value="I will fetch CB logs for the current CB if nothing is provided, otherwise I will fetch the logs of CB with an ID `cbid`. If so, `day` data must be provided.\n")
    embed.add_field(name="update log `[eid]` `[field:day|hit1|hit2|hit3|hits]` `[value]`",
                    value="I will update log the with an ID of `eid`. All fields must be provided.\n")
    embed.add_field(name="update member `[nick]` `[field:nick|active]` `[value]`",
                    value="I will update the member with an ID of `mid`. All fields must be provided.\n")
    embed.add_field(name="update cb `[cbid]` `[field:date|span]` `[value]`",
                    value="I will update the CB with an ID of `cbid`. All fields must be provided.\n")
    embed.add_field(name="reload `[role:b(lue)|y(ellow)|g(reen)]`",
                    value="I will find all members with the current role and update it to the guild members record. This is the recommended to be done before every CB.\n")
    embed.add_field(name="removemember `[mid]`",
                    value="I will remove the member with an member ID of `mid`. It is not recommended to use this as you will lose data about their CB contribution. Instead, update their `active` tag to 0.\n")
    embed.add_field(name="listmembers `[mode(optional):0|1]`",
                    value="I will fetch the member list of the guild. If no input is provided, the list will only contain `active` members. If its 0, I will fetch all `inactive` members. If its 1, I will fetch everything.\n")
    embed.add_field(name="newcb `[start_date:yyyy-mm-dd]` `[span(optional):default={:d}]` `[set_cb(optional):default=1]`".format(span_days),
                    value="I will create a new CB entry and set it as the current CB. The starting date must be provided. This will automatically `conclude` the current CB if `set_cb` is set to `1`.\n")
    embed.add_field(name="setcb `[cb_id(optional)]`",
                    value="I will set the current CB to be the one with `cb_id` if its provided. Otherwise I will fetch the current CB from the database and set that as the current CB.\n")
    embed.add_field(name="removecb `[cbid]`",
                    value="I will remove the CB with an ID of `cbid` along with all CB logs associated with it.`\n")
    embed.add_field(name="statscb `[cbid(optional)]`",
                    value="I will fetch the data for either the current CB or the one with ID `cbid` if provided. The data will be minimal due to Discord.\n")
    embed.add_field(name="listcb",
                    value="I will fetch the latst 10 CBs and their data.\n")
    embed.add_field(name="concludecb",
                    value="I will wrap up the CB and aggregate data logged.\n")
    return embed
        
# MISC FUNCTIONS
# tests
# cb log test version


# cb battle
@cb.command()

        
# RUN
client.run(token)
