import copy

###################### guild settings structure ######################
guild = {
    'id':               None,
    'role_admin':       None,
    "welcome": {
            "channel":  None,
            "active":   False
    },
    "pins": {
            "active":   False,
            "no_pin":   []
    }
}

###################### hatsune ######################
hatsu_chara_skills_base = {
    'name': {
        'en':           None,
        'jp':           None
    },
    'en':           None,
    'jp':           None,
    'actions':      []
}

hatsu_chara_stats = {
    "hp":       0,
    "atk":      0,
    "matk":     0,
    "def":      0,
    "mdef":     0,
    "pCrit":    0,
    "mCrit":    0,
    "wHpRec":   0,
    "wTpRec":   0,
    "dodge":    0,
    "pPen":     0,
    "mPen":     0,
    "lifesteal":0,
    "hpRec":    0,
    "tpRec":    0,
    "tpSave":   0,
    "acc":      0
}

hatsu_ue = {
    'hnid':         None,
    'img':          None,
    'stats':        {},
    'name': {
        'en':           None,
        'jp':           None
    },
    "text": {
        'en':           None,
        'jp':           None
    }
}

hatsu_chara_skills = {
    "pattern": {
        'all':          [],
        'loop':         []
    },
    "ub":           copy.deepcopy(hatsu_chara_skills_base),
    "sk1":          copy.deepcopy(hatsu_chara_skills_base),
    "sk2":          copy.deepcopy(hatsu_chara_skills_base),
    "sk3":          copy.deepcopy(hatsu_chara_skills_base),
    "ue": {
        "sk1":          copy.deepcopy(hatsu_chara_skills_base),
        "sk2":          copy.deepcopy(hatsu_chara_skills_base),
        "sk3":          copy.deepcopy(hatsu_chara_skills_base)
    }
}

hatsu_chara = {
    'active':       False,
    'hnid':         None,
    'fallback':     [],
    'img':          None,
    'card':         None,
    'b_alt':        False,
    'ue':           False,
    'normal':       copy.deepcopy(hatsu_chara_skills),
    'alt':          copy.deepcopy(hatsu_chara_skills),
    "ex":           copy.deepcopy(hatsu_chara_skills_base),
    "stats":        copy.deepcopy(hatsu_chara_stats),
    "ue_data":      copy.deepcopy(hatsu_ue)
}

hatsu_chara_flb = copy.deepcopy(hatsu_chara)
hatsu_chara_flb['fallback'] = ['ue']

hatsu_chara_base = {
    'id':           None,
    'hnid':         None,
    'sname':        None,
    'prefix':       None,
    'tags':         [],
    'type':         None,   # 0 = magic
    'pos_field':    None,
    'pos':          None,
    'kizuna':       [],
    'special':      [],
    'status': {
        'lvl':          None,
        'ue':           None,
        'rank':         None
    },

    'base':         copy.deepcopy(hatsu_chara),
    'flb':          copy.deepcopy(hatsu_chara_flb),

    'name': {
        'en':           None,
        'jp':           None
    },
    "name_alt": {
        "en":           None,
        "jp":           None
    },
    'name_irl': {
        'en':           None,
        'jp':           None
    },
    'image_irl':    None,
    'age':          None,
    'height':       None,
    'va':           None,
    'bloodtype':    None,
    'bday':         None,
    'weight':       None,
    "race":         None,
    'guild':        None,
    'comment': {
        'en':           None,
        'jp':           None
    }
}

hatsu_index = {
    'id':           None,
    'hnid':         None,
    'prefix':       None,
    'sname':        None,
    'name': {
        'en':           None,
        'jp':           None
    },
    "flb":          False,
    'ue':           False,
    'enum_alias':   []
}

###################### CB ######################
hatsucb_guild = {
    "index"             : {},
    "active_channels"   : [],
    "active_names"      : [],
    "bosses"            : [
        None, None, None, None, None
    ],
    "clans"             : {}
}

hatsucb_clan =  {
    "name"              : None,
    "subguild_id"       : None,
    "role_leader"       : None,
    "role_member"       : None,
    "channel_primary"   : None,
    "channel_notice"    : None,
    "notice_msg"        : None,
    "settings": {
        "b_autoincr": True,
        "b_ot"      : False,
        "b_wave"    : False,
        "b_timeout" : False,
        "timeout"   : 30,
        "b_emptyq"  : True
    }
}

hatsucb_q = {
    "reset" : False,
    "done"  : [],
    "cwave" : [1, 1, 1, 1, 1],
    "queue" : []
}

hatsucb_qentry = {
    "id"        : None,
    "timestamp" : None,
    "type"      : None,
    "payload": {
        "boss"      : None, 
        "wave"      : None,
        'is_ot'     : False, 
        "ot"        : None
    }
}

hatsucb_room = {
    'creators'  : [],
    'rooms'     : {}
}

hatsucb_roomentry = {
    "description"   : None,
    "message_id"    : None,
    "target"        : None,
    "creator"       : None,
    "members"       : []
}

###################### twitter ######################
twit_listener = {
    'id'    : None,
    "t_id"  : None,
    "name"  : None,
    'rt'    : False
}

twit_cache = {
    'idv': []
}

twit_guild = {
    'id'        : None,
    'convert'   :  False,
    "services"  : {}
}

twit_guild_listener = {
    'active'    : False,
    'channel'   : None
}


def fetch(template_name):
    """
    guild
    hatsu_chara
    hatsu_index
    hcb_guild
    hcb_clan
    hcb_queue
    hcb_qentry
    tw_listener
    tw_cache
    tw_guild
    tw_guild_lis
    """
    if      template_name == 'guild':
        return copy.deepcopy(guild)

    elif    template_name == 'hatsu_chara':
        return copy.deepcopy(hatsu_chara_base)
    elif    template_name == 'hatsu_index':
        return copy.deepcopy(hatsu_index)

    elif    template_name == 'hcb_guild':
        return copy.deepcopy(hatsucb_guild)
    elif    template_name == 'hcb_clan':
        return copy.deepcopy(hatsucb_clan)
    elif    template_name == 'hcb_queue':
        return copy.deepcopy(hatsucb_q)
    elif    template_name == 'hcb_qentry':
        return copy.deepcopy(hatsucb_qentry)
    elif    template_name == 'hcb_rooms':
        return copy.deepcopy(hatsucb_room)
    elif    template_name == 'hcb_roomsentry':
        return copy.deepcopy(hatsucb_roomentry)

    elif    template_name == 'tw_listener':
        return copy.deepcopy(twit_listener)
    elif    template_name == 'tw_cache':
        return copy.deepcopy(twit_cache)
    elif    template_name == 'tw_guild':
        return copy.deepcopy(twit_guild)
    elif    template_name == 'tw_guild_lis':
        return copy.deepcopy(twit_guild_listener)
    
    else:
        return None