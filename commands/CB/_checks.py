"""
Ames
checks
"""
import datetime

def _checkconcl(flags):
    if not flags['current_cb']:
        print('_checkconcl: failed to set current cb status - curent_cb not set')
        return flags

    cb_id = int(flags['current_cb'])

    get_date = ("SELECT start_date, span_days FROM cb.cb_list "
                "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(get_date, )
    except mysql.connector.Error as err:
        print('_checkconcl:\n', err)
        cb_cursor.close()
        return flags
    else:
        for (sd, span) in cb_cursor:
            pass
        flags['cb_concluded'] = (datetime.datetime.strptime(str(sd), '%Y-%m-%d') + datetime.timedelta(days=int(span))) < datetime.datetime.utcnow()
        print('_checkconcl: success')
        return flags

def _resetcbc(flags):
    """
    Sets all cb.cb_lists.current values to 0.
    """
    set_reset = ("UPDATE cb.cb_list "
                 "SET current = 0")
    try:
        cb_cursor = flags['cb_db'].cursor()
        cb_cursor.execute(set_reset, )
        flags['cb_db'].commit()
    except mysql.connector.Error as err:
        print('_resetcbc:\n', err)
        cb_cursor.close()
        return False
    else:
        cb_cursor.close()
        print('_resetcbc: success')
        return True

def _getday(cb_id, flags):
    get_day = ("SELECT MAX(day) FROM cb.cb_log "
               "WHERE cb_id = {:d} LIMIT 1".format(cb_id))
    try:
        cb_cursor = flags['cb_db'].cursor()
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

def check_author(author):
    """
    check author for lock-in commands
    """
    def inner_check(message):
        return message.author == author
    return inner_check

def isempty(inList):
    """
    checks if data returned is empty
    """
    if isinstance(inList, list): # Is a list
        return all( map(isempty, inList) )
    return False

def guildname(guild:str):
    if guild == 'g':
        return 'Green'
    elif guild == 'b':
        return 'Blue'
    elif guild == 'y':
        return 'Yellow'
    else:
        return 'None'
    
def getrole(guild:str):
    """
    returns the role number for the guild specified
    """
    guild = guild.lower()
    if guild[0] == 'b':
        return '547686074302857218', 'b'
    elif guild[0] == 'y':
        return 'None', 'y', 
    elif guild[0] == 'g':
        return 'None', 'g'
    else:
        return 'None', 'None'

    
