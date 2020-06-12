# bot_ames
A discord bot used for fetching character information in Princess Connect! Re:Dive by CyGames. Ames is planned to provide QoL functions for Clan Battles in the near future. Apart from PCR:D functions, Ames also provides some miscellaneous functions too.

Ames is written in Python 3.7.4 utilising the [`rewrite`](https://github.com/Rapptz/discord.py) branch of Discord's Python API and makes use of `cogs` and `extensions` to integrate commands.

Although Pull requests are welcome, please note that much of Ames' lookup function relies on an privately maintained external database and much of Ames' functionality will not be available without the said database.

## Adding Ames
You can add Ames with [this link](https://discord.com/api/oauth2/authorize?client_id=599290654878597140&permissions=1879436368&scope=bot). You will need to be a **server admininstrator** in order to add the bot. If Ames does not send anything when she joins, use `.help` to get started. Please reach out to me if something goes wrong.

## Capabilities
Ames' current features:
* Characters
  * Display both EN and JP skill descriptions
  * Show attack pattern
  * Show raw character stats (WIP)
  * Show raw skill stats (WIP)
  * Show character profile
  * Show raw UE stats
* Feed
  * Listen to [PriConne EN twitter](https://twitter.com/priconne_eng) for updates
  * Listen to [PriConne JP twitter](https://twitter.com/priconne_redive) for updates
  * Various other game feeds
* Search
  * Can search characters based on their attributes/skill effects/position to aid team composition
* Gacha
  * Simulate the current gacha banner (JP)

Ames' planned features:
* Clan Battle (JP)
  * Show boss stats and effects
  * Boss reminder system to help with coordination
* Events (JP)
  * Show future events schedule

# Pulling Ames SC
If you wish to pull/clone and run Ames for whatever reason, you will need to read the sections below. Otherwise, you're done!

## Dependencies
Ames requires a few packages to run. You can install her dependencies with:
* `pip3 install -r requirements.txt`

## Prefix
Ames' prefix is `.`,  but can be changed in `ames_new.py` under `BOT_PREFIX` should it conflict.

## Run
Before you start Ames, you will need to go into `templates/private.json` and fill get at least a token and a place where ames can send reports, and move the file into `commands/private`. You may also need to go into `re_ames.py` and edit `amesBot().__init__` and `amesBot().on_ready` to remove her dependency on the external database/loggers. This may not be needed once her external dependacies are internalized.

To start Ames, run `re_ames.py`. Use `.help` to see what she can do. 

## Disclaimer and Special Thanks
As mentioned already, `Ames` uses a privately maintained database, and additionally cross references data from an unofficial database known as [redive_master_db_diff](https://github.com/esterTion/redive_master_db_diff) and [HatsuneNote's PrincessGuide](https://github.com/superk589/PrincessGuide). Many thanks to their creators for relieving much of the time that would've needed to fetch data.

All art assets used by `Ames` are not my creation and are property of their rightful owners.

## Requests/suggestions/feedback
Find me on discord: `tigertiggs#5376`