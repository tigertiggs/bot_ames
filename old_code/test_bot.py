"""
Ames bot for Princonne
Mostly developed to brush up on python3
Created by tiggs

Primary purpose is to log CB scoress

TODO:
.help
.cb conclude(cb_id)
.cb quota(cb_id) - given warning on cb_concluded
"""

import datetime

# discord dependencies
import discord
from discord.ext.commands import Bot

# database dependencies
import mysql.connector
from mysql.connector import errorcode

# global playground
temp = 0
author_lock = []
role_decor = ("<",">","@","&")

# guild roles
test_role = '600283710155128840'
blue_guild = '547686074302857218'
yellow_guild = 'dummy2'
green_guild = 'dummy3'

# database-related globals
cb_db = False
current_cb = False
span_days = 8

# global flags
db_isconnected = False
cb_concluded = False

# load token from external file
with open("token.txt") as token_file:
    token = token_file.read().strip()
    token_file.close()

# load db credencials from external file
with open("db.txt") as db_file:
    db_name = db_file.readline().strip()
    db_pw = db_file.readline().strip()
    db_host = db_file.readline().strip()
    db_dbname = db_file.readline().strip()
    db_file.close()

# bot globals
BOT_PREFIX = (".")
client = Bot(command_prefix = BOT_PREFIX)
client.remove_command('help')

# startup
@client.event
async def on_ready():
    print('on_ready: Logged in as {0.user}'.format(client))

    # connect to db
    print('on_ready: Attempting to connect to DB')
    connect_db()

# main - command filter
@client.event
async def on_message(message):
    global author_lock
    # ignore messages from bots including self
    if message.author.bot:
        #print('on_message: author is a bot - exiting')
        return
    
    # ignore commands from authors who are in a 'locked function'
    if message.author in author_lock:
        print('on_message: author is currently in author_lock - exiting')
        return
    
    # pass commands
    if message.content.startswith(BOT_PREFIX):
        print('on_message: passing command: ' + message.content)
        msg = message.content.strip("".join(BOT_PREFIX))
        await client.process_commands(message)

# commands
# quit
@client.command()
async def _kill(context):
    await context.channel.send("I'll be right back!")
    print('logging off...')
    connect_db(0)
    await client.logout()

# cb logging
# commands
#dc     .cb newcb [start date yyyy-mm-dd] [set default = 1] [span default = SPAN_DAYS]
#dc     .cb setcb [cb_id]
#dc     .cb update cb [cb_id] [field - date/span] [value]
#dc      .cb conclude [showstats default = 0]
#dc     .cb listcb
#dc     .cb statscb [id default = current]
#dc     .cb remove cb [id]

#dc     .cb reload [role]
#dc     .cb listmembers [active/inactive/both default/0/1]
#dc     .cb addmember [discord tag] [alias default = None]
#dc     .cb update member [id] [field] [value]
#dc     .cb remove member [id]

#dc      .cb log [nick] [day] [hit1] [hit2] [hit3]
#dc       .cb listlog [cb_id] [day]
#d       .cb update log [id] [field] [value]
#d       .cb remove log [id]
#       .cb concludeday [day]

@client.command()
async def cb(context):
    global db_isconnected
    
    # check if cb_db is connected
    if not db_isconnected:
        print('.cb: DB is not connected - exiting command')
        await context.channel.send('Database is not connected!')
        return

    # check and set current_cb
    if not check_current_cb():
        print('.cb: global current_cb is not set. Attempting to set via database.')
        setcb()
        _checkconcl()
    
    # lower message case to remove case dependece and split words on space
    msgv = context.message.content.lower().split(" ")[1:]
    print(".cb: received command:\n"+str(msgv))

    # set first word to be cmd and subcommands
    cmd = msgv[0]
    msgv = msgv[1:]

    # help
    if cmd == 'help':
        await context.channel.send(embed=cbhelpembed(context))

    # pcb
    if cmd == 'pcb':
        await context.channel.send(pcb())
    
    # newcb
    if cmd == 'newcb':
        await context.channel.send('Adding new CB entry...')
        await context.channel.send(newcb(msgv))

    # setcb
    if cmd == 'setcb':
        await context.channel.send('Setting current CB...')
        await context.channel.send(setcb(msgv))

    # update
    if cmd == 'update':
        if msgv[0] == 'cb':
            await context.channel.send('Updating CB entry...')
            await context.channel.send(updatecb(msgv[1:]))

        if msgv[0] == 'member':
            await context.channel.send('Updating member record...')
            await context.channel.send(updatemember(msgv[1:]))

        if msgv[0] == 'log':
            await context.channel.send('Updating CB Log entry...')
            await context.channel.send(updatelog(msgv[1:]))

    # conclude
    if cmd == 'conclude':
        await context.channel.send('Wrapping up current CB! Otsukaresama!')
        data = concludecb()
        if isListEmpty(data):
            await context.channel.send('No data retrieved!')
        else:
            await context.channel.send(embed=concludecbembed(context, data))
            

    # statscb
    if cmd == 'statscb':
        if len(msgv):
            data = statscb(msgv[0])
        else:
            data = statscb()
            
        if isListEmpty(data):
            await context.channel.send('No data retrieved!')
        else:
            await context.channel.send(embed=statscbembed(context, data))

    # listcb
    if cmd == 'listcb':
        data = listcb()
        if isListEmpty(data):
            await context.channel.send('No data retrieved!')
        else:
            await context.channel.send(embed=listcbembed(context, data))

    # remove
    if cmd == 'remove':
        if msgv[0] == 'cb':
            await context.channel.send('Deleting CB entry...')
            await context.channel.send(removecb(msgv[1:]))

        if msgv[0] == 'member':
            await context.channel.send('Deleting player records...')
            await context.channel.send(removemember(msgv[1:]))

    # reload
    if cmd == 'reload':
        await context.channel.send('Updating CB roster...')
        await context.channel.send(reload(context, msgv))

    # listmembers
    if cmd == 'listmembers':
        data = listmembers(msgv)
        if isListEmpty(data):
            await context.channel.send('No data retrieved!')
        else:
            await context.channel.send(embed=listmembersembed(context, data))

    # log
    if cmd == 'log':
        await context.channel.send('Logging day entry...')
        await context.channel.send(log(msgv))

    # listlogs
    if cmd == 'listlogs':
        data = listlogs(msgv)
        if isListEmpty(data[1:-1]):
            await context.channel.send('No data retrieved!')
        else:
            await context.channel.send(embed=listlogsembed(context, data))

    # endday
    """
    if cmd == 'endday':
        await context.channel.send('Otsukaresama! Concluding today\'s battles!')
        if _endday(msgv):
            await context.channel.send('Success!')
        else:
            await context.channel.send('Unsuccessful')
    """

    # startday
    if cmd == 'startday':
        await context.channel.send('Beginning a new day! Minna ganbarimashou!')
        await context.channel.send(startday())

    
        
def pcb():
    """
    Have Ames say the current CB. This should never throw an error.
    """
    if not check_current_cb():
        print('pcb: current_cb not set')
        return "No CB set!"
    
    cb_id = int(current_cb)
    day = _getday(cb_id)
    query_cb = ("SELECT start_date, span_days "
                "FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_cb, )
    except mysql.connector.Error as err:
        print('pcb:\n', err)
        cb_cursor.close()
        return "Error upon requesting CB data, check console!"
    else:
        for (_sd, _span) in cb_cursor:
            sd = str(_sd)
            span = int(_span)
        cb_cursor.close()
        if cb_concluded:
            status = 'has concluded. Otsukaresama!'
        else:
            status = 'is ongoing. Ganbare!'
        print('pcb: success')
        return "We are currently on **Day {0:s} of {4:d}**  of the CB that started on {1:s} with `cb_id = {2:d}`. The CB {3:s}".format(str(day), sd, cb_id, status, span) 

def startday():
    """
    Inserts 0s into cb.cb_log. Replaced _endday
    """
    if not check_current_cb():
        print('startday: current_cb is not set!')
        return 'Could not start day: current CB not set!'
    if cb_concluded:
        print('startday: cb_concluded flag set')
        return 'Could not start new day: CB has ended!'
    cb_id = int(current_cb)
    
    # get the current day
    day = _getday(cb_id)
    
    # get m_id
    get_mid = ("SELECT m_id FROM cb.members WHERE active = 1")
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(get_mid, )
    except mysql.connector.Error as err:
        print('startday:\n', err)
        cb_cursor.close()
        return 'Could not start new day!'
    
    mid = []
    for (_mid) in cb_cursor:
        mid.append(int(_mid[0]))
    if len(mid) == 0:
        print('startday: no active members')
        return 'No active members - Nothing to insert!'

    # insert
    insert_log = "INSERT INTO cb.cb_log (cb_id, day, hit1, hit2, hit3, hits, m_id) "\
                 "VALUES ({0:d}, {1:d}, {2:d}, {3:d}, {4:d}, {5:d}, {6:d})"

    #print(mid, day, cb_id)
    try:
        for m_id in mid:
            cb_cursor.execute((insert_log.format(cb_id, day+1, 0, 0, 0, 0, int(m_id))))
            cb_db.commit()
    except mysql.connector.Error as err:
        print('startday:\n', err)
        cb_cursor.close()
        return 'Failed to start today\'s log'
    else:
        cb_cursor.close()
        print('startday: success')
        return 'Successfully started new day!'

def log(msgv):
    """
    Logs a day's hit for a certain member
    expects:
    [<nick: str>], <hit1: str>, <hit2: str>, <hit3 :str>, <hits: str>]
    """
    if not check_current_cb():
        print('log: current_cb is not set')
        return 'Could not log - current CB not set!'
    if len(msgv) < 5:
        print('log: insufficient input')
        return 'Could not log - insufficient inputs!'
    
    cb_id = int(current_cb)
    nick = msgv[0]
    (hit1, hit2, hit3, hits) = msgv[1:5]

    #print(cb_id, nick, hit1, hit2, hit3)

    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE nick LIKE '%{:s}%' LIMIT 1".format(nick))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(find_mid)
        for _m_id in cb_cursor:
            m_id = int(_m_id[0])
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        return 'Could not log - failed to fetch member data!'

    # find_day
    day = _getday(cb_id)

    if day == 0:
        print('log: day was None - start a new day!')
        return 'Could not log - no records to update - start a new day!'

    #print(m_id)
    log_hit = ("UPDATE cb.cb_log SET "
               "hit1= {3:d}, "
               "hit2 = {4:d}, "
               "hit3 = {5:d}, "
               "hits = {6:d} "
               "WHERE cb_id = {1:d} "
               "AND day = {2:d} "
               "AND m_id = {0:d}".format(m_id, cb_id, day, int(hit1), int(hit2), int(hit3), int(hits))
               )

    try:
        cb_cursor.execute(log_hit, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print("log:\n:", err)
        cb_cursor.close()
        return 'Could not log - failed to update details!'
    else:
        cb_cursor.close()
        print('log: success')
        return 'Data successfully logged!'

def updatelog(msgv):
    """
    Updates a field on a log
    Expects:
    [<e_id:str>, <field :str>, <value: str>]
    options:
        day
        hit1
        hit2
        hit3
        hits
    """
    if len(msgv) < 3:
        print('updatelog: insufficient inputs')
        return 'Could not update - insufficient inputs!'

    if msgv[1] not in ["day","hit1","hit2","hit3","hits"]:
        print('updatelog: invalid field param')
        return 'Could not update - invalid field parameter supplied!'
    
    e_id = int(msgv[0])
    field = str(msgv[1])
    value = int(msgv[2])
    if field[0] == "d":
        field = "day"

    update_log = ("UPDATE cb.cb_log "
                  "SET {0:s} = {1:d} "
                  "WHERE entry_id = {2:d}".format(field, value, e_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(update_log, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print('updatelog:\n', err)
        cb_cursor.close()
        return 'Could not update log!'
    else:
        cb_cursor.close()
        print('updatelog: success')
        return 'Log successfully updated!'

def removelog(msgv):
    """
    removes a log entry
    """
    if len(msgv) == 0:
        print('removelog: no entry_id supplied')
        return 'Could not remove log - no `entry_id` supplied!'

    e_id = int(msgv[0])
    remove_log = ("DELETE FROM cb.cb_log "
                  "WHERE entry_id = {:d}".format(e_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(remove_log, )
    except mysql.connector.Error as err:
        print('removelog:\n', err)
        cb_cursor.close()
        return 'Could not remove log!'
    else:
        cb_cursor.close()
        print('removelog: success')
        return 'Successfully removed log!'

def listlogs(msgv):
    """
    Lists the complete log for a cb
    Expects:
    [<cb_id: str, default = 0>, <day: str, default = 0>]
    """
    if len(msgv) == 0:
        if not check_current_cb():
            print('listlogs: Unable to get current day or current CB!')
            return []
        cb_id = int(current_cb)
        day = _getday(cb_id)

    elif len(msgv) == 1:
        print('listlogs: Insufficient inputs!')
        return []
    
    elif len(msgv) > 1:
        if msgv[0] == '0':
            if not check_current_cb():
                print('listlogs: Unable to get current CB!')
                return []
            cb_id = int(current_cb)
        else:
            cb_id = int(msgv[0])
            
        day = int(msgv[1])

    get_date = ("SELECT start_date FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    
    get_logs = ("SELECT l.entry_id, cb.members.discord_tag, "
                "l.hits, (l.hit1 + l.hit2 + l.hit3) AS tot "
                "FROM cb.cb_log AS l "
                "INNER JOIN cb.members ON cb.members.m_id = l.m_id "
                "WHERE l.cb_id = {0:d} "
                "AND l.day = {1:d} "
                "ORDER BY l.hits DESC".format(cb_id, day))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(get_date)
        for _date in cb_cursor:
            date = _date[0]
        cb_cursor.execute(get_logs, )
    except mysql.connector.Error as err:
        print("listlog:\n:", err)
        cb_cursor.close()
        return []
    else:
        c1 = []
        c2 = []
        c3 = []
        for (_e_id, _tag, _hits, _tot) in cb_cursor:
            c1.append("\t".join((str((_e_id)), str(_tag)[:-5])))
            c3.append(str(_hits))
            c2.append(str(_tot))
        cb_cursor.close()
        print('listlogs: success')
        return [day, c1, c2, c3, str(date)]

"""
def _endday(msgv):

    'concludes the current day. Depreciated'

    if len(msgv) == 0:
        print('endday: insufficient inputs')
        return False
    if not check_current_cb():
        print('endday: current CB is not set')
        return False

    cb_id = int(current_cb)
    day = int(msgv[0])

    # find all members who are active and did not hit
    find_slackers = ("SELECT m.m_id "
                     "FROM cb.members m "
                     "LEFT JOIN cb.cb_log l "
                     "ON l.m_id = m.m_id "
                     "AND m.active <> 0 "
                     "AND l.day = {0:d} "
                     "AND l.cb_id = {1:d} "
                     "WHERE hits IS NULL".format(day, cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(find_slackers, )
    except mysql.connector.Error as err:
        print('endday:\n', err)
        cb_cursor.close()
        return False

    # checking returned results, check if 0, 1 or multiple results
    m_id = []
    for (_m_id) in cb_cursor:
        m_id.append(_m_id[0])

    if len(m_id) == 0:
        print('endday: no m_id found')
        cb_cursor.close()
        return True
    #if len(m_id) == 1:
    #    m_id[0] = m_id[0][0]
    print(m_id)
    # insert data for slackers
    insert_slackers = "INSERT INTO cb.cb_log "\
                      "SET m_id = {0:d}, "\
                      "hit1 = 0, hit2 = 0, hit3 = 0, hits = 0, "\
                      "day = {1:d}, cb_id = {2:d}"
    try:
        for mid in m_id:
            cb_cursor.execute((insert_slackers.format(int(mid), day, cb_id)))
            cb_db.commit()
    except mysql.connector.Error as err:
        print('endday:\n', err)
        cb_cursor.close()
        return False
    else:
        cb_cursor.close()
        return True
"""

def _checkconcl():
    global cb_concluded
    if not check_current_cb():
        print('_checkconcl: failed to set current cb status - curent_cb not set')
        return False

    cb_id = int(current_cb)

    get_date = ("SELECT start_date, span_days FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(get_date, )
    except mysql.connector.Error as err:
        print('_checkconcl:\n', err)
        cb_cursor.close()
        return False
    else:
        for (sd, span) in cb_cursor:
            pass
        cb_concluded = (datetime.datetime.strptime(str(sd), '%Y-%m-%d') + datetime.timedelta(days=int(span))) < datetime.datetime.utcnow()
        print('_checkconcl: success')
        return True

def _getday(cb_id):
    get_day = ("SELECT MAX(day) FROM cb.cb_log "
               "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(get_day, )
        for (_day) in cb_cursor:
            day = str(_day[0])
    except mysql.connector.Error as err:
        print('_getday:\n', err)
        cb_cursor.close()
        return False

    if day == 'None':
        day = 0
    else:
        day = int(day)
    print('_getday: success')
    return day

def reload(context, msgv):
    """
    Updates cb.members with all members in context guild with the same role specified by msgv
    """
    global test_role, blue_guild, yellow_guild, green_guild
    global role_decor
    if len(msgv) == 0:
        print('reload: no role supplied')
        return 'Could not refresh roster - no role supplied!'

    print(msgv)
    
    if msgv[0][0] == 'b':
        role_id = blue_guild
    elif msgv[0][0] == 'y':
        role_id = yellow_guild
    elif msgv[0][0] == 'g':
        role_id = green_guild
    else:
        role_id = msgv[0].strip("".join(role_decor))

    print('reload: role received: ' + role_id)

    data = listmembers(['1'])[1] # d_tag
    #print(data)
    roster = []
    for member in context.message.guild.members:
        if not ("#".join((member.name, member.discriminator)) in data):
            for role in member.roles:
                if str(role.id) == role_id:
                    roster.append(member)
        #elif ("#".join((member.name, member.discriminator)) in data):
        #    data.remove("#".join((member.name, member.discriminator)))
                
    if len(roster) == 0:
        print('reload: no members with role found')
        return 'No new members with role found - Roster remains unchanged!'
    else:
        print('reload: success')
        return addmember(roster)

def addmember(roster=[]):
    """
    Adds a member to cb.members. Expects roster to be an array of discord member objects
    """
    if len(roster) == 0:
        print('addmember: roster is empty')
        return 'Could not add members - new members list is empty!'
    
    member_data = []
    for member in roster:
        if str(member.nick) == 'None':
            nick = ""
        else:
            nick = str(member.nick)
        member_data.append(
            (
            "#".join((member.name,member.discriminator)),
            " ".join((member.name, nick))
            )
        )

    query_addm = "INSERT INTO cb.members (discord_tag, nick, active) "\
                 "VALUES ('{0:s}', '{1:s}', 1)"
    try:
        cb_cursor = cb_db.cursor()
        for (discord_tag, nick) in member_data:
            cb_cursor.execute((query_addm.format(discord_tag, nick)))
            cb_db.commit()
    except mysql.connector.Error as err:
        print("addmember:\n:", err)
        cb_cursor.close()
        return 'Could not add member - failed to insert data!'
    else:
        cb_cursor.close()
        print('addmember: success')
        return 'Successfulled added new members!'

def updatemember(msgv):
    """
    Updates a certain field in cb.members
    Expects:
    [<nick :str>,
    <field: str, nick|active>,
    value: str, nick|active>
    ]
    """
    if len(msgv) < 3:
        print('updatemember: insufficient input')
        return 'Could not update member - insufficient input supplied!'
    if msgv[1] not in ["nick","active"]:
        print('updatemember: invalid field supplied')
        return 'Could not update member - invalid field supplied!'

    nick = msgv[0]
    
    # find m_id
    find_mid = ("SELECT m_id FROM cb.members "
                "WHERE nick LIKE '%{:s}%' LIMIT 1".format(nick))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(find_mid)
        for _m_id in cb_cursor:
            m_id = int(_m_id[0])
    except mysql.connector.Error as err:
        print("updatemember:\n:", err)
        cb_cursor.close()
        return 'Could not update member - failed to find member data!'
    
    field = msgv[1]
    value = msgv[2]

    update_member_nick = ("UPDATE cb.members "
                     "SET {0:s} = '{1:s}' "
                     "WHERE m_id = {2:d}".format(field, value, m_id))

    update_member_active = ("UPDATE cb.members "
                     "SET {0:s} = {1:s} "
                     "WHERE m_id = {2:d}".format(field, value, m_id))
    try:
        cb_cursor = cb_db.cursor()
        if field == 'nick':
            cb_cursor.execute(update_member_nick, )
        if field == 'active':
            cb_cursor.execute(update_member_active, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print("updatemember:\n:", err)
        cb_cursor.close()
        return 'Could not update member - failed to update!'
    else:
        cb_cursor.close()
        print('updatemember: success')
        return 'Successfully updated member record!'

def removemember(msgv):
    """
    Deletes a member's record given m_id
    """
    if len(msgv) == 0:
        print('removemember: no m_id supplied')
        return 'Could not remove member record - no `m_id` supplied!'
    else:
        m_id = int(msgv[0])

    query_delete_child = ("DELETE FROM cb.cb_log "
                    "WHERE m_id = {:d}".format(m_id))
    
    query_delete = ("DELETE FROM cb.members "
                    "WHERE m_id = {:d}".format(m_id))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_delete_child)
        cb_db.commit()
        cb_cursor.execute(query_delete)
        cb_db.commit()
        cb_cursor.close()
    except mysql.connector.Error as err:
        print("removemember:\n:", err)
        cb_cursor.close()
        return 'Could not remove member record - failed to remove record!'
    else:
        print('removemember: success')
        return 'Successfully removed member record!'

def listmembers(msgv=[]):
    """
    Creates data needed for listmembersembed
    """
    if len(msgv) > 0:
        if msgv[0] == '0':
            mode = 0
            mode_name = 'Inactive'
        if msgv[0] == '1':
            mode = -1
            mode_name = 'Full'
        else:
            print('listmembers: received incorrect command: ' + msgv[0])
            return []
    else:
        mode = 1
        mode_name = 'Active'

    if mode == -1:
        query_listmembers = (
                "SELECT m_id, discord_tag, nick, active "
                "FROM cb.members")
    else:
        query_listmembers = (
            "SELECT m_id, discord_tag, nick, active "
            "FROM cb.members "
            "WHERE active = {:d}".format(mode))

    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_listmembers, )
        m_id = []
        d_tag = []
        nick = []
        active = []
        for (_m_id, _d_tag, _nick, _active) in cb_cursor:
            m_id.append(str(_m_id))
            d_tag.append(_d_tag)
            active.append(str(_active))
            if len(_nick) > 23:
                nick.append(str(_nick)[:22]+"...")
            else:
                nick.append(str(_nick))
    except mysql.connector.Error as err:
        print("listmembers:\n:", err)
        cb_cursor.close()
        return []
    else:
        cb_cursor.close()
        print('listmembers: success')
        return [m_id, d_tag, nick, active, mode_name]

def newcb(msgv):
    # .cb newcb [start date yyyy-mm-dd] [span default = SPAN_DAYS] [set default = 1]
    """
    Inserts a cb entry into cb.cb_lists.
    Expects:
    [<start_date: str, format yyyy-mm-dd>,
    <current: int, optional, default = 1>,
    <span_days: int, optional, default = span_days>]
    """
    global current_cb, cb_concluded
    #print(msgv)
    if len(msgv) == 0:
        print('newcb: insufficient inputs')
        return 'Could not add new CB - insufficient inputs supplied!'
    
    inpdate = datetime.datetime.strptime(msgv[0], '%Y-%m-%d')
    #print(inpdate.strftime('%Y-%m-%d'))
    default = 1
    span = span_days
    
    if len(msgv) > 1:
        span = msgv[1]
        if len(msgv) > 2:
            default = msgv[2]
    
    new_cb = ("INSERT INTO cb.cb_list "
              "(start_date, current, span_days) "
              "VALUES ('{0:s}', {1:d}, {2:d})".format(inpdate.strftime('%Y-%m-%d'), int(default), int(span)))
    
    get_cbid = ("SELECT cb_id from cb.cb_list "
                "WHERE current = 1")
    
    try:
        if default:
            _resetcbc()
            concludecb()
            cb_concluded = False
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(new_cb, )
        cb_db.commit()
        cb_cursor.execute(get_cbid, )
        for (cb_id) in cb_cursor:
            current_cb = cb_id[0]
    except mysql.connector.Error as err:
        print('newcb:\n', err)
        cb_cursor.close()
        return 'Could not add new CB - failed to add new entry!'
    else:
        cb_cursor.close()
        print('newcb: success')
        return 'Successfully added new CB entry!'

def setcb(msgv=[]):
    """
    Sets the given cb_id to have current value = 1. If not provided, global current_cb will be set instead via db
    expects:
    [<cb_id: int, optional>]
    """
    global current_cb
    if len(msgv) > 0:
        cb_id = msgv[0]
        set_cb = ("UPDATE cb.cb_list "
                  "SET current = 1 "
                  "WHERE cb_id = {:d}".format(int(cb_id)))

        try:
            _resetcbc()
            cb_cursor = cb_db.cursor()
            cb_cursor.execute(set_cb, )
            cb_db.commit()
            current_cb = cb_id
        except mysql.connector.Error as err:
            print('setcb:\n', err)
            cb_cursor.close()
            return 'Could not set current CB via supplied `cb_id`!'
        else:
            cb_cursor.close()
            return 'Successfulled set current CB!'
    else:
        query = ("SELECT cb_id FROM cb.cb_list "
                 "WHERE current = 1")
        
        try:
            cb_cursor = cb_db.cursor()
            cb_cursor.execute(query, )
            for (_id) in cb_cursor:
                if str(_id) == 'None':
                    print('setcb: no active cb found in db')
                    return 'Could not set current CB - no active CB found in DB!'
                current_cb = _id[0]
        except mysql.connector.Error as err:
            print('setcb:\n', err)
            cb_cursor.close()
            return 'Could not set current CB via database!'
        else:
            cb_cursor.close()
            print('setcb: success')
            return 'Successfully set current CB via DB!'

def updatecb(msgv):
    """
    updates a field in cb.cb_list
    """
    if len(msgv) < 3:
        print('updatecb: insufficient inputs')
        return 'Could not update CB - insufficient inputs supplied!'
    if msgv[1] not in ["date", "span"]:
        print('updatecb: invalid field')
        return 'Could not update CB - invalid field supplied!'
    cb_id = msgv[0]
    field = msgv[1]
    value = msgv[2]
    
    if field == 'date':
        field = 'start_date'
        value = datetime.datetime.strptime(value, '%Y-%m-%d')
        update_cblist = ("UPDATE cb.cb_list "
                         "SET start_date = '{0:s}' "
                         "WHERE cb_id = {1:d}".format(value.strftime('%Y-%m-%d'), int(cb_id)))
    
    if field == 'span':
        field = 'span_days'
        value = int(value)
        update_cblist = ("UPDATE cb.cb_list "
                         "SET span_days = {0:d} "
                         "WHERE cb_id = {1:d}".format(value, int(cb_id)))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(update_cblist, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print("updatecb:\n", err)
        cb_cursor.close()
        return 'Could not update CB!'
    else:
        cb_cursor.close()
        print('updatecb: success')
        return 'Successfully updated CB!'

def removecb(msgv):
    """
    Removes a cb role given a cb_id
    """
    if len(msgv) == 0:
        print('removecb: no cb_id supplied')
        return 'Could not remove CB entry - no `cb_id` supplied!'
    cb_id = int(msgv[0])

    query_delete_child = ("DELETE FROM cb.cb_log "
                          "WHERE cb_id = {:d}".format(cb_id))
    
    query_delete = ("DELETE FROM cb.cb_list "
                    "WHERE cb_id = {:d}".format(cb_id))

    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_delete_child)
        cb_db.commit()
        cb_cursor.execute(query_delete)
        cb_db.commit()
    except mysql.connector.Error as err:
        print('removecb:\n', err)
        cb_cursor.close()
        return 'Could not remove CB entry!'
    else:
        cb_cursor.close()
        print('removecb: success')
        return 'Successfully removed CB entry!'

def statscb(cb_id=None):
    """
    Returns details needed for statscbembed.
    """
    if cb_id:
        cb_id = int(cb_id)
    else:
        if not check_current_cb():
            return []
        cb_id = int(current_cb)

    #print(cb_id)
    query_stats = ("SELECT start_date, span_days, total, active_members "
                   "FROM cb.cb_list "
                   "WHERE cb_id = {:d}".format(cb_id))
    
    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_stats, )
        data = []
        for (date, days, tot, active) in cb_cursor:
            data = [str(date), days, tot, active, str(cb_id)]
    except mysql.connector.Error as err:
        print('statcb:\n', err)
        cb_cursor.close()
        return []
    else:
        cb_cursor.close()
        print('statscb: success')
        return data

def listcb():
    """
    Returns the data of the 10 latests cb data for listcbembed.
    """
    query_list = ("SELECT cb_id, start_date, total "
                  "FROM cb.cb_list "
                  "ORDER BY cb_id DESC "
                  "LIMIT 10")
    try:
        cb_cursor = cb_db.cursor(buffered=True)
        cb_cursor.execute(query_list, )
        cb_idv = []
        datev = []
        totalv = []
        for (cb_id, start_date, total) in cb_cursor:
            cb_idv.append(str(cb_id))
            datev.append(str(start_date))
            totalv.append(str(total))
    except mysql.connector.Error as err:
        print(err)
        cb_cursor.close()
        return []
    else:
        cb_cursor.close()
        print('listcb: success')
        return [cb_idv, datev, totalv]

def _resetcbc():
    """
    Sets all cb.cb_lists.current values to 0.
    """
    set_reset = ("UPDATE cb.cb_list "
                 "SET current = 0")
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(set_reset, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print('_resetcbc:\n', err)
        cb_cursor.close()
        return False
    else:
        cb_cursor.close()
        print('_resetcbc: success')
        return True

def concludecb():
    """
    aggregates data, and calls statscb
    """
    global cb_concluded
    if not check_current_cb():
        print('concludecb: no cb set')
        return []

    cb_id = int(current_cb)
    
    query_total = ("SELECT (SUM(hit1) + SUM(hit2) + sum(hit3)) AS total, COUNT(DISTINCT m_id) AS active "
                   "FROM cb.cb_log "
                   "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    
    # update cb
    try:
        cb_cursor = cb_db.cursor()
        cb_cursor.execute(query_total, )

        for (_total, _activem) in cb_cursor:
            total = _total
            activem = _activem

        update_conclude = ("UPDATE cb.cb_list "
                           "SET total = {0:d}, active_members = {1:d} "
                           "WHERE cb_id = {2:d}".format(int(total), int(activem), cb_id))
        
        cb_cursor.execute(update_conclude, )
        cb_db.commit()
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
        return []

    # collect player aggregate
    query_player = ("SELECT m.discord_tag, SUM((l.hit1 + l.hit2 + l.hit3)) AS total, "
                    "SUM(l.hits) AS total_hits "
                    "FROM cb.cb_log AS l "
                    "INNER JOIN cb.members AS m "
                    "ON m.m_id = l.m_id "
                    "WHERE cb_id = {:d} "
                    "GROUP BY l.m_id".format(cb_id))
    try:
        cb_cursor.execute(query_player, )
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
    else:
        tag = []
        tot = []
        toth = []
        for (_tag, _tot, _toth) in cb_cursor:
            tag.append(str(_tag)[:-5])
            tot.append(str(_tot))
            toth.append(str(_toth))

    query_date = ("SELECT start_date, span_days "
                  "FROM cb.cb_list "
                  "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
         cb_cursor.execute(query_date)
    except mysql.connector.Error as err:
        print('concludecb:\n', err)
        cb_cursor.close()
    else:
        for (_date, _days) in cb_cursor:
            date = _date
            days = _days
        cb_cursor.close()
        cb_concluded = True
        print('concludecb: success')
        return [str(date), int(days), int(total), str(activem), tag, tot, toth]

def concludecbembed(context, data):
    embed = discord.Embed(title="CB Conclusion report", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name=data[0]+" CB Summary", icon_url=context.message.author.avatar_url)
    embed.add_field(name="Days", value=data[1], inline=True)
    embed.add_field(name="Guild Score", value=data[2], inline=True)
    embed.add_field(name="Active Members", value="\n".join(data[3]), inline=True)
    embed.add_field(name="Member", value="\n".join(data[4]), inline=True)
    embed.add_field(name="Total Score", value="\n".join(data[5]), inline=True)
    embed.add_field(name="Total Hits", value="\n".join(data[6]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def listlogsembed(context, data):
    embed = discord.Embed(title="Log for day {:d}".format(data[0]), description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name=data[4]+" CB Log", icon_url=context.message.author.avatar_url)
    embed.add_field(name="EID", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Total Score", value="\n".join(data[2]), inline=True)
    embed.add_field(name="Hits", value="\n".join(data[3]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def listmembersembed(context, data):
    embed = discord.Embed(title="{:s} Guild Roster".format(data[4]), description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="Roster", icon_url=context.message.author.avatar_url)
    embed.add_field(name="M_ID", value="\n".join(data[0]), inline=True)
    #embed.add_field(name="Discord", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Nickname", value="\n".join(data[2]), inline=True)
    #embed.add_field(name="Active", value="\n".join(data[3]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

def statscbembed(context, data):
    embed = discord.Embed(title="Clan Battle Report (minimal)", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Stats", icon_url=context.message.author.avatar_url)
    embed.add_field(name="CB ID", value=data[4], inline=False)
    embed.add_field(name="Start date", value=data[0], inline=True)
    embed.add_field(name="Total days", value=data[1], inline=True)
    embed.add_field(name="Total score", value=data[2], inline=True)
    embed.add_field(name="Active members", value=data[3], inline=True)
    embed.set_footer(text="still in testing")
    return embed

def listcbembed(context, data):
    embed = discord.Embed(title="Clan Battle Log (minimal)", description="Prepared by yours truly.", timestamp=datetime.datetime.utcnow())
    embed.set_author(name="CB Log", icon_url=context.message.author.avatar_url)
    embed.add_field(name="CB ID", value="\n".join(data[0]), inline=True)
    embed.add_field(name="Start date", value="\n".join(data[1]), inline=True)
    embed.add_field(name="Total score", value="\n".join(data[2]), inline=True)
    embed.set_footer(text="still in testing")
    return embed

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

# database related
@client.command()
async def _connectdb(context):
    global db_isconnected
    await context.channel.send('Connecting to database...')
    if not db_isconnected:
        if connect_db():
            await context.channel.send('Connection successful!')
        else:
            await context.channel.send('Connection failed.')
    else:
        await context.channel.send('Database is already connected!')

@client.command()
async def _disconnectdb(context):
    global db_isconnected
    await context.channel.send('Disconnecting from database...')
    if db_isconnected:
        if connect_db(0):
            await context.channel.send('Disconnected!')
        else:
            await context.channel.send('Failed to disconnect.')
    else:
        await context.channel.send('Database not connected!')
        
def connect_db(mode=1):    
    global cb_db, db_name, db_pw, db_host, db_dbname, db_isconnected
    
    if mode:
        print('connecting to database...')
        try:
            cb_db = mysql.connector.connect(
                user = db_name,
                password = db_pw,
                host = db_host,
                database = db_dbname)
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print('connection failed: access denied')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print('connection failed: database does not exist')
            else:
                print(err)
            return False
            
        else:
            print('connected')
            db_isconnected = 1
            return True
        
    else:
        print('disconnecting from database...')
        try:
            cb_db.close()
            
        except mysql.connector.Error as err:
            print(err)
            return False
        
        else:
            print('disconnected')
            db_isconnected = 0
            return True

# MISC FUNCTION
def check_current_cb():
    return bool(current_cb)

def check(author):
    def inner_check(message):
        return message.author == author
    return inner_check

def isListEmpty(inList):
    if isinstance(inList, list): # Is a list
        return all( map(isListEmpty, inList) )
    return False

# RUN
client.run(token)
