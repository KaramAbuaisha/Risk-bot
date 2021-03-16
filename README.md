# Risk-bot

This is a bot for tracking elo for 1v1s and team-games (2v2s, 3v3s, 4v4s) on Discord. It is made for an adaptation of "Risk" on WC3 but it can be used for other games as well. 

All relevant code is under `officialriskbot.py`, other python files contain scrapped commands - most of which work but we in our discord server have no use for.

Currently the repository is missing the database schema required - this will be added in the future (FYI it uses SQLite)

In order to get this bot working on discord you also need to add the client auth token at the bottom of `officialriskbot.py`. For example
`client.run("Nzg1MDA4MzE2ODgzNDAyNzc0.X8xl9w.woujElelGS5EGInzerRzZOIPSmc")  # client auth token (found in discord api bot page)`
