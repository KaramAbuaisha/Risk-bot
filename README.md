# Risk-bot

This is a bot for tracking elo for 1v1s and team-games (2v2s, 3v3s, 4v4s) on Discord. It is made for an adaptation of "Risk" on WC3 but it can be used for other games as well. 

All relevant code is under `officialriskbot.py`, other python files contain scrapped commands - most of which work but we in our discord server have no use for.

You need a client auth token to run the bot (it is found in the discord api bot page), for example if your token is `ABCD.EFG`, then you run the bot like so:
`python3 officialriskbot.py --token ABCD.EFG`
