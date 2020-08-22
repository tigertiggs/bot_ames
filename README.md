# bot_ames
A discord bot used for fetching character data in Princess Connect! Re:Dive by CyGames. Ames is planned to provide QoL functions for Clan Battles in the near future. Apart from PCR:D functions, Ames also provides some miscellaneous functions too.

Ames is written in Python 3.7.x utilising the [`rewrite` branch of Discord's Python API](https://github.com/Rapptz/discord.py) and makes use of `cogs` and `extensions` to integrate commands.

~~Please note that much of Ames' lookup function relies on a privately maintained external database and much of Ames' functionality will not be available without the said database.~~
Character data are now local and Ames should be able to access all character data without said database. However, Ames still relies on an external service for updates to the Princess Database.

## Adding Ames
You can add Ames with [this link](https://discord.com/api/oauth2/authorize?client_id=599290654878597140&permissions=1342565456&scope=bot). You will need to have the **manage server** permission on the server you wish to add Ames. If Ames does not send anything when she joins, use `.help` to get started. Please reach out to me if something goes wrong.

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

## Blue Oath JP
As an aside, Ames also provides a small set of Blue Oath (JP) related commands with a semi-standalone module `cog_blueoath.py`, with information and details provided and maintained by the EN Discord community. There are 2 main sources of information; [the spreadsheet](https://docs.google.com/spreadsheets/d/1UrEFf88vjcOFRy7tFOfcedsoobXU7ZTeezFlRFVEo2Q/edit?usp=sharing) and the [EN Wiki](https://blueoath.miraheze.org/wiki/Main_Page). You're welcome to join the [Blue Oath EN discord](https://discord.gg/hzNRN2a) community!

### Blue Oath Capabilities
Use `.bo help` to see all Blue Oath related commands.
* Ships
  * Retrieve ship skills, stats, gallery, traits, limit break information
* Daily Oil reminders

## Disclaimer and Special Thanks
As mentioned already, `Ames` uses a privately maintained database, and additionally cross references data from an unofficial database known as [redive_master_db_diff](https://github.com/esterTion/redive_master_db_diff) and [HatsuneNote's PrincessGuide](https://github.com/superk589/PrincessGuide). Many thanks to their creators for relieving much of the time that would've needed to fetch data.

All art assets used by `Ames` are not my creation and are property of their rightful owners.

## Requests/suggestions/feedback
Find me on discord: `tigertiggs#5376`