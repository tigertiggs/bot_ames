# bot_ames
A discord bot used for fetching character information in Princess Connect! Re:Dive by CyGames. Ames is planned to provide QoL functions for Clan Battles in the near future. Apart from PCR:D functions, Ames also provides some miscellaneous functions too.

Ames is written in Python 3.7.4 utilising the [`rewrite`](https://github.com/Rapptz/discord.py) branch of Discord's Python API and makes use of `cogs` and `extensions` to integrate commands.

Although Pull requests are welcome, please note that much of Ames' lookup function relies on a privately maintained database.

## Dependencies
Ames requires a few packages to run. You can install her dependencies with
* `pip3 install -r requirements.txt`

## Run
To start Ames, run `re_ames.py`. Use `.help` to see what she can do.

## Prefix
Ames' prefix is `.`,  but can be changed in `ames_new.py` under `BOT_PREFIX` should it conflict. 

## Disclaimer
As mentioned already, `Ames` uses a privately maintained database, and additionally cross references data from an unofficial database known as [Hatsune Note's PrincessGuide Database](https://github.com/superk589/PrincessGuide). Many thanks to them for relieving much of the time that would've needed to fetch data.

All art assets used by `Ames` are not my creation and are property of their rightful owners.

## Author
Find me on discord: `tigertiggs#5376`