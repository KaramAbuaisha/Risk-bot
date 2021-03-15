import sqlite3
import numpy as np
import itertools
import trueskill
import scipy.special
import logging
import datetime
import re
import asyncio
import requests
import json

from collections import defaultdict

from time import time as gettime
from discord.ext import tasks

import discord
from discord.ext.commands import bot
from discord.ext import commands

db_path = "risk.db"

# Boolean

#1v1

GAME = False
RUNNING = False
STARTING = False

#2v2

GAME2 = False
RUNNING2 = False
STARTING2 = False

#3v3

GAME3 = False
RUNNING3 = False
STARTING3 = False

# Dictionaries

global_dict = dict()
joined_dic = {}

# Lists and Variables

ID = 0

PLAYERS = []
PLAYERS2 = []
PLAYERS3 = []
repeat_list = []
no_score = []

# Logging

logger = logging.getLogger('discord')

# Logger.setLevel(logging.INFO)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
main_elo = trueskill.TrueSkill(mu=1500, draw_probability=0, backend="mpmath", sigma=400, tau=10, beta=200)
main_elo.make_as_global()

# Channel ID's

na_lobby_channel = discord.Object(785009271317463091)
ones_channel = discord.Object(790313550270693396)
twos_channel = discord.Object(790313583484731422)
threes_channel = discord.Object(790313624395972668)
ffa_channel = discord.Object(784960892617490452)
admin_channel = discord.Object(785006670865498153) 
na_activity_channel = discord.Object(790313358816968715) 
na_leaderboard_channel = discord.Object(785234105968099409) 
na_announcements_channel = discord.Object(791741867845877771)
na_rules_channel = discord.Object(787070402768928819)
na_test_channel = discord.Object(787071010180169749)
na_general_channel = discord.Object(784960513435631670)
bot_spam_channel = discord.Object(787071010180169749)

# Discord Client

client = discord.Client()
bot_prefix = "!"
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=bot_prefix, intents=intents)
# client.remove_command("help") #removes default help command
def erfc(x):
    """Complementary error function (via `http://bit.ly/zOLqbc`_)"""
    z = abs(x)
    t = 1. / (1. + z / 2.)
    r = t * np.math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (
        0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (
            0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (
                -0.82215223 + t * 0.17087277
            )))
        )))
    )))
    return 2. - r if x < 0 else r


def cdf(x, mu=0, sigma=1):
    """Cumulative distribution function"""
    return 0.5 * erfc(-(x - mu) / (sigma * np.math.sqrt(2)))

def win_probability(elo1, sigma1, elo2, sigma2):
    BETA=200
    deltaMu = elo1 - elo2
    sumSigma = sigma1**2 + sigma2**2
    rsss = sqrt(2* (BETA**2) + sumSigma)
    return cdf(deltaMu/rsss)
    
def safeName(name):
    """ Changes player's names that will mess up the discord leaderboard formatting to shitname """
    safe_name = ''.join(e for e in name if e.isalnum())
    if safe_name == '':
        safe_name = "Shitname"
    return safe_name


def find_user_by_name(ctx, name):
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    out = None

    if len(name) == 0:
        # Tried without an input
        out = ctx.message.author
    else:
        # Test to see if it's a ping
        server = ctx.message.guild
        if name[0:2] == "<@":
            if name[2] == "!":
                player = server.get_member(name[3:-1])
            else:
                player = server.get_member(name[2:-1])
            if player is not None:
                out = player
        else:
            # Test to see if it's a username
            player = server.get_member_named(name)
            if player is not None:
                out = player
            else:
                # Check the database to see if it's a username
                conn = sqlite3.connect(db_path, uri=True)

                c = conn.cursor()
                c.execute("SELECT ID FROM players WHERE name LIKE ?", [name])
                result = c.fetchone()
                if result is not None:
                    player = server.get_member(result[0])
                    if player is not None:
                        out = player
                else:
                    # Check the database to see if it's LIKE a username
                    wildcard_name = name + "%"
                    c.execute("SELECT ID FROM players WHERE name LIKE ?", [wildcard_name])
                    result = c.fetchone()
                    if result is not None:
                        player = server.get_member(result[0])
                        if player is not None:
                            out = player
    conn.commit()
    conn.close()
    return out


def find_userid_by_name(ctx, name):
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    out = None

    if len(name) == 0:
        # Tried without an input
        out = ctx.message.author.id
    else:
        # Test to see if it's a ping
        server = ctx.message.guild
        if name[0:2] == "<@":
            if name[2] == "!":
                player = get_member(name[3:-1])
            else:
                player = get_member(name[2:-1])
            if player is not None:
                out = player.id
        else:
            # Test to see if it's a username
            player = server.get_member_named(name)
            if player is not None:
                out = player.id
            else:
                # Check the database to see if it's a username
                c.execute("SELECT ID FROM players WHERE name LIKE ?", [name])
                result = c.fetchone()
                if result is not None:
                    out = result[0]
                else:
                    # Check the database to see if it's LIKE a username
                    wildcard_name = name + "%"
                    c.execute("SELECT ID FROM players WHERE name LIKE ?", [wildcard_name])
                    result = c.fetchone()
                    if result is not None:
                        out = result[0]
    conn.commit()
    conn.close()
    return out

@client.event
async def on_ready():
    print("Bot has now logged on")

@tasks.loop(seconds=10)
async def autokicktimer():

    global PLAYERS, joined_dic, repeat_list

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    for player_id in PLAYERS:
        if gettime() - joined_dic[player_id] > 1020:
            lobby = client.get_channel(785009271317463091)
            user = client.get_user(player_id)
            c.execute("SELECT elo FROM PLAYERS WHERE ID = ?", [player_id])
            fetch = c.fetchone()
            player_elo = fetch[0]
            PLAYERS.remove(player_id)
            repeat_list.remove(player_id)
            await lobby.send(f"**{user.name} [{player_elo}]** has been kicked from the lobby for inactivity. **({str(len(set(PLAYERS)))})**")

    conn.close()

@tasks.loop(seconds=10)
async def timer():
    global PLAYERS, joined_dic, repeat_list

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for player_id in PLAYERS:
        if gettime() - joined_dic[player_id] > 900 and player_id not in repeat_list:
            lobby = client.get_channel(785009271317463091)
            user = client.get_user(player_id)
            repeat_list.append(player_id)
            await lobby.send(f"{user.mention} Still around? (.here)")
        
    conn.close()

async def leaderboard_team(ctx):
    """ Updates the leaderboard channel """

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = ctx.guild
    leaderboard_channel = discord.utils.get(guild.channels, id=787070684106194954)
    leader_board = []
    i = 1
    msg = []  # Empty list to put all the messages in the log

    await leaderboard_channel.purge(limit=15)

    msg = "```\n"
    msg = msg + "{:<4}  {:<20}  {:<10}  {:<10}  {:<10} {:<10} {:<10}".format('RANK', 'NAME', 'WIN', 'LOSS', 'ELO', 'SIGMA',
                                                                      'WINRATE') + "" + "\n"

    for player in c.execute("SELECT name, win, loss, elo, record, id, lowest, sigma FROM players_team ORDER BY elo desc"):
        leader_board.append(player)

    for player in leader_board:
        total_games = int(player[1]) + int(player[2])
        win = int(player[1])
        if int(total_games) == 0:
            winrate = "0.0"
        else:
            winrate = float("{0:.2f}".format((int(win) / int(total_games)) * 100))

        if total_games > 0:

            if player[4] == None or player[3] > player[4]:
                c.execute("UPDATE players_team SET record = ? where ID = ?", [player[3], player[5]])

            msg = msg + "{:<4}  {:<20}  {:<10}  {:<10}  {:<10} {:<10} {:<10}".format('#' + str(i), safeName(player[0][:20]),
                                                                            player[1], player[2], int(round(player[3])), int(round(player[7])),
                                                                            str(winrate) + "%", (player[3])) + "" + "\n"
            c.execute("UPDATE players_team SET rank = ? WHERE ID = ?", [i,player[5]])
            # i = i + 1
            # if i % 10 == 0:
            #     await leaderboard_channel.send(msg + '```')
            #     msg = "```\n"
    c.execute("SELECT MAX(ELO), ID from PLAYERS_TEAM")
    player = c.fetchone()[1]
    member = guild.get_member(player)
    role = discord.utils.get(ctx.guild.roles, name="Rank 1 Team")
    await role.members[0].remove_roles(role)
    await member.add_roles(role)
    msg += "```"
    conn.commit()
    conn.close()
    await leaderboard_channel.send(msg)

async def leaderboard_solo(ctx):
    """ Updates the leaderboard channel """

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = ctx.guild
    leaderboard_channel = discord.utils.get(guild.channels, id=787070644427948142)
    leader_board = []
    i = 1
    msg = []  # Empty list to put all the messages in the log

    await leaderboard_channel.purge(limit=15)

    msg = "```\n"
    msg = msg + "{:<4}  {:<25}  {:<10} {:<10} {:<10}".format('RANK', 'NAME', 'ELO', 'SIGMA', 'TOTAL GAMES') + "" + "\n"

    for player in c.execute("SELECT name, win, loss, elo, record, id, lowest, sigma FROM players WHERE win + loss > 19 ORDER BY elo desc"):
        leader_board.append(player)

    for i, player in enumerate(leader_board):
        name = safeName(player[0][:20])
        # member = guild.get_member(player[5])

        # if member is not None:
        #     if member.nick is not None:
        #         name = member.nick
        #     else:
        #         name = member.name
        # else:
        #     name = player[0]

                
        total_games = int(player[1]) + int(player[2])
        sigma = int(round(player[7]))

        c.execute("UPDATE players SET rank = ? WHERE ID = ?", [i+1, player[5]])

        if player[4] == None or player[3] > player[4]:
            c.execute("UPDATE players SET record = ? where ID = ?", [int(round(player[3])), player[5]])

        msg += "{:<4}  {:<25}  {:<10}  {:<10}  {:<10}".format('#' + str(i+1), name,
                                                                        int(round(player[3])), int(round(player[7])), int(total_games)) + "" + "\n"
        # if i + 1 % 10 == 0:
        #     await leaderboard_channel.send(msg + '```')
        #     msg = "```\n"

    c.execute("SELECT MAX(ELO), ID from PLAYERS WHERE win + loss > 19")
    player = c.fetchone()[1]
    member = guild.get_member(player)
    role = discord.utils.get(ctx.guild.roles, name="Rank 1 Solo")
    await role.members[0].remove_roles(role)
    await member.add_roles(role)
    msg += "```"
    conn.commit()
    conn.close()
    await leaderboard_channel.send(msg)


def isName(memberName, member):
    name = member.display_name
    name = name.upper()
    pattern = re.compile('[\W_]+')
    if memberName.upper() in pattern.sub('', name).upper():
        return True
    else:
        return False


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def register(ctx, member: discord.Member=None):
    '''Registers a user into the player database.'''

    global db_path, joined_dic

    if ctx.channel.id == ones_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
            
        conn = sqlite3.connect(db_path)

        c = conn.cursor()

        B = ctx.message.author.name

        A = ctx.message.author.id

        mod_role = discord.utils.get(ctx.guild.roles, name="League Admin")

        L = ctx.author

        date = datetime.datetime.now()

        role = discord.utils.get(ctx.guild.roles, name="League")

        profile = "https://cdn1.bbcode0.com/uploads/2020/7/1/888ce487a07a840bf8f6c2bc7f842252-full.jpg"

        if member == None:
                
            await L.add_roles(role)
            await ctx.channel.send('Added player role.')

        if member:

            if mod_role in ctx.author.roles:

                c.execute("SELECT elo FROM players WHERE ID = ?", [member.id])
                row = c.fetchone()
                if row == None:
                    c.execute('INSERT INTO players VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, ?, NULL, 400)',
                            [member.id, member.name, "Empty", date, str(profile)])
                    c.execute("INSERT INTO warnings VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL)", [member.id,member.name])
                    await ctx.channel.send(f'Registered {member.name}.')
                    role = discord.utils.get(ctx.guild.roles, name="League")
                    await member.add_roles(role)
                
                else: 
                    await ctx.send("You have already registered.")

        conn.commit()

    if ctx.channel.id == twos_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
            
        conn = sqlite3.connect(db_path)

        c = conn.cursor()

        B = ctx.message.author.name

        A = ctx.message.author.id

        mod_role = discord.utils.get(ctx.guild.roles, name="League Admin")

        L = ctx.author

        date = datetime.datetime.now()

        role = discord.utils.get(ctx.guild.roles, name="League")

        profile = "https://cdn1.bbcode0.com/uploads/2020/7/1/888ce487a07a840bf8f6c2bc7f842252-full.jpg"

        if member == None:
                
            await L.add_roles(role)
            await ctx.channel.send('Added player role.')

        if member:

            if mod_role in ctx.author.roles:

                c.execute("SELECT elo FROM players_team WHERE ID = ?", [member.id])
                row = c.fetchone()
                if row == None:
                    c.execute('INSERT INTO players_team VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, ?, NULL, 400)',
                            [member.id, member.name, "Empty", date, str(profile)])
                    c.execute("INSERT INTO warnings2 VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL)", [member.id,member.name])
                    await ctx.channel.send(f'Registered {member.name}.')
                    role = discord.utils.get(ctx.guild.roles, name="League")
                    await member.add_roles(role)
                
                else: 
                    await ctx.send("You have already registered.")

        conn.commit()

    if ctx.channel.id == threes_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
            
        conn = sqlite3.connect(db_path)

        c = conn.cursor()

        B = ctx.message.author.name

        A = ctx.message.author.id

        mod_role = discord.utils.get(ctx.guild.roles, name="League Admin")

        L = ctx.author

        date = datetime.datetime.now()

        role = discord.utils.get(ctx.guild.roles, name="League")

        profile = "https://cdn1.bbcode0.com/uploads/2020/7/1/888ce487a07a840bf8f6c2bc7f842252-full.jpg"

        if member == None:
                
            await L.add_roles(role)
            await ctx.channel.send('Added player role.')

        if member:

            if mod_role in ctx.author.roles:

                c.execute("SELECT elo FROM players_team WHERE ID = ?", [member.id])
                row = c.fetchone()
                if row == None:
                    c.execute('INSERT INTO players_team VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, ?, NULL, 400)',
                            [member.id, member.name, "Empty", date, str(profile)])
                    c.execute("INSERT INTO warnings3 VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL)", [member.id,member.name])
                    await ctx.channel.send(f'Registered {member.name}.')
                    role = discord.utils.get(ctx.guild.roles, name="League")
                    await member.add_roles(role)
                
                else: 
                    await ctx.send("You have already registered.")

        conn.commit()


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def unregister(ctx):

    """Removes banjo role."""

    global joined_dic

    if ctx.channel.id == ones_channel.id or ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:
                
        t = ctx.author
        joined_dic[t] = gettime()
        banjo_role = discord.utils.get(ctx.guild.roles, name="League")
        await t.remove_roles(banjo_role)
        await ctx.send("Banjo role removed.")


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def lobby(ctx):
    '''Show's the current players in the lobby.'''

    global PLAYERS, PLAYERS2, PLAYERS3, GAME, GAME2, GAME3, db_path

    conn = sqlite3.connect(db_path, uri=True)

    c = conn.cursor()

    if ctx.message.channel.id == threes_channel.id:
        if GAME3:
            PLAYERS3 = list(set(PLAYERS3))
            NAMES = []
            for t in PLAYERS3:
                c.execute("SELECT name, elo FROM players_team WHERE ID = ?", [t])
                result = c.fetchone()
                name = result[0]
                pts = int(round(result[1]))
                NAMES.append(name + " **[" + str(pts) + "]**")

            tup = tuple(PLAYERS3)    
            if len(set(PLAYERS3)) > 1:
                sql = "select name from players_team where id IN {}".format(tup)
                sql += " ORDER BY elo desc LIMIT 2"
                c.execute((sql))

            elif len(PLAYERS) == 1:
                sql = "select name from players_team where id = ?"
                c.execute((sql), [tup[0]])
            data = c.fetchall()
            strCaptainsList = "Projected Captains: **"
            for d in data:
                strCaptainsList += "  " + str(d[0])

            if len(set(PLAYERS3)) > 0:
                lobbystr = f"Current Lobby **(Normal) (" + str(len(set(PLAYERS3))) + ")**: "
                for t in NAMES:
                    lobbystr += t + " "

                await ctx.channel.send(lobbystr)

            elif ctx.message.channel.id == threes_channel.id:
                await ctx.channel.send("There is no lobby active.")

        if len(PLAYERS3) == 0:
            await ctx.channel.send("There is no lobby active.")

    if ctx.message.channel.id == twos_channel.id:
        if GAME2:
            PLAYERS2 = list(set(PLAYERS2))
            NAMES = []
            for t in PLAYERS2:
                c.execute("SELECT name, elo FROM players_team WHERE ID = ?", [t])
                result = c.fetchone()
                name = result[0]
                pts = int(round(result[1]))
                NAMES.append(name + " **[" + str(pts) + "]**")

            tup = tuple(PLAYERS2)    
            if len(set(PLAYERS2)) > 1:
                sql = "select name from players_team where id IN {}".format(tup)
                sql += " ORDER BY elo desc LIMIT 2"
                c.execute((sql))

            elif len(PLAYERS2) == 1:
                sql = "select name from players_team where id = ?"
                c.execute((sql), [tup[0]])
            data = c.fetchall()
            strCaptainsList = "Projected Captains: **"
            for d in data:
                strCaptainsList += "  " + str(d[0])

            if len(set(PLAYERS2)) > 0:
                lobbystr = f"Current Lobby **(Normal) (" + str(len(set(PLAYERS2))) + ")**: "
                for t in NAMES:
                    lobbystr += t + " "

                await ctx.channel.send(lobbystr)

            elif ctx.message.channel.id == twos_channel.id:
                await ctx.channel.send("There is no lobby active.")

        if len(PLAYERS2) == 0:
            await ctx.channel.send("There is no lobby active.")

    if ctx.message.channel.id == ones_channel.id:
        if GAME:
            PLAYERS = list(set(PLAYERS))
            NAMES = []
            for t in PLAYERS:
                c.execute("SELECT name, elo FROM players WHERE ID = ?", [t])
                result = c.fetchone()
                name = result[0]
                pts = int(round(result[1]))
                NAMES.append(name + " **[" + str(pts) + "]**")

            tup = tuple(PLAYERS)    
            if len(set(PLAYERS)) > 1:
                sql = "select name from players where id IN {}".format(tup)
                sql += " ORDER BY elo desc LIMIT 2"
                c.execute((sql))

            elif len(PLAYERS) == 1:
                sql = "select name from players where id = ?"
                c.execute((sql), [tup[0]])
            data = c.fetchall()
            strCaptainsList = "Projected Captains: **"
            for d in data:
                strCaptainsList += "  " + str(d[0])

            if len(set(PLAYERS)) > 0:
                lobbystr = f"Current Lobby **(Normal) (" + str(len(set(PLAYERS))) + ")**: "
                for t in NAMES:
                    lobbystr += t + " "

                await ctx.channel.send(lobbystr)

            elif ctx.message.channel.id == ones_channel.id:
                await ctx.channel.send("There is no lobby active.")

        if len(PLAYERS) == 0:
            await ctx.channel.send("There is no lobby active.")

    conn.close()


@client.command(aliases=["kill"])
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def end(ctx):
    '''Ends the current lobby.'''

    global PLAYERS, PLAYERS2, PLAYERS3, GAME, GAME2, GAME3, RUNNING, RUNNING2, RUNNING3

    if ctx.channel.id == ones_channel.id:

        t = ctx.message.author.id

        if RUNNING:
            PLAYERS = []
            RUNNING = False
            GAME = False

        await ctx.channel.send("Lobby ended.")

    if ctx.channel.id == twos_channel.id:

        t = ctx.message.author.id

        if RUNNING2:
            PLAYERS2 = []
            RUNNING2 = False
            GAME2 = False

        await ctx.channel.send("Lobby ended.")

    if ctx.channel.id == threes_channel.id:

        t = ctx.message.author.id

        if RUNNING3:
            PLAYERS3 = []
            RUNNING3 = False
            GAME3 = False

        await ctx.channel.send("Lobby ended.")

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('Dev')
async def forcejoinall(ctx):
    '''Forcejoins 7 players into the lobby for testing'''

    global PLAYERS, GAME, RUNNING, db_path

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:
            
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        player1 = 102475732378193920
        player2 = 341306490071810050
        player3 = 222886535631077378
        player4 = 229094474297376770
        player5 = 565326927976726538
        player6 = 676645353327427600
        player7 = 641160452247781397

        c.execute("SELECT name FROM players WHERE ID = ?", [player1])
        c.execute("SELECT name FROM players WHERE ID = ?", [player2])
        c.execute("SELECT name FROM players WHERE ID = ?", [player3])
        c.execute("SELECT name FROM players WHERE ID = ?", [player4])
        c.execute("SELECT name FROM players WHERE ID = ?", [player5])
        c.execute("SELECT name FROM players WHERE ID = ?", [player6])
        c.execute("SELECT name FROM players WHERE ID = ?", [player7])
        user = c.fetchone()
        name = user[0]

        if GAME:
            PLAYERS = list(set(PLAYERS))
            PLAYERS.append(player1)
            PLAYERS.append(player2)
            PLAYERS.append(player3)
            PLAYERS.append(player4)
            PLAYERS.append(player5)
            PLAYERS.append(player6)
            PLAYERS.append(player7)

            await ctx.channel.send("Forced a full lobby.")

        conn.commit()
        conn.close()

@client.command()
async def search(ctx, gn):

    """Searches through Warcraft III gamelist."""
    
    result = requests.get('https://api.wc3stats.com/gamelist')

    gamelist = result.json()
    
    games = []
    for game in gamelist ['body']:
        if re.search(gn, game['name'], re.IGNORECASE):
            slots_taken = game['slotsTaken']
            slots_total = game['slotsTotal']
            emb = (discord.Embed(description='**Server:** [' + game['server'] + '] /n **Game Name:** ' + game['name'] + '/n **Slots:** (' + str(slots_taken) + '/' + str(slots_total) + ')' '/n **Host:** [' + game['host'] + ']', colour=0x3DF27))
            games.append('[' + game['server'] + '] ' + game['name'] + ' (' + str(slots_taken) + '/' + str(slots_total) + ')' ' [' + game['host'] + ']')

    if len(games) <= 0:
            await ctx.channel.send("No games found.")

    else:
        for game in games:
            await ctx.channel.send(game)

@client.command(aliases=["h"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def here(ctx):
    '''Resets the lobby timer for inactivity kick.'''

    global PLAYERS, joined_dic, repeat_list

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:

        t = ctx.message.author.id

        try:

            repeat_list.remove(t)
            joined_dic[t] = gettime()
            await ctx.send("All good.")

        except:

            joined_dic[t] = gettime()
            await ctx.send("All good.")

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def peak(ctx, name=None):
    
    '''Show's the highest ELO reached by a player.'''

    global joined_dic

    if ctx.channel.id == ones_channel.id:

        if name == None:
            x = ctx.author.id
            joined_dic[x] = gettime()
            t = ctx.message.author.id
            conn = sqlite3.connect(db_path, uri=True)
            c = conn.cursor()
            #player = find_userid_by_name(ctx, name)
            if x is None:
                await ctx.channel.send("No user found by that name.")
                return
            c.execute("SELECT name, record FROM players WHERE ID = ?", [x])
            user = c.fetchone()
            name = user[0]
            record = user[1]

            await ctx.channel.send(f"**{name}** has an elo peak of **{record}**.")

        elif name:

            x = ctx.author.id
            joined_dic[x] = gettime()
            t = ctx.message.author.id
            conn = sqlite3.connect(db_path, uri=True)
            c = conn.cursor()
            player = find_userid_by_name(ctx, name)
            if player is None:
                await ctx.channel.send("No user found by that name.")
                return
            c.execute("SELECT name, record FROM players WHERE ID = ?", [player])
            user = c.fetchone()
            name = user[0]
            record = user[1]

            await ctx.channel.send(f"**{name}** has an elo peak of **{record}**.")

    if ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:

        if name == None:
            x = ctx.author.id
            joined_dic[x] = gettime()
            t = ctx.message.author.id
            conn = sqlite3.connect(db_path, uri=True)
            c = conn.cursor()
            #player = find_userid_by_name(ctx, name)
            if x is None:
                await ctx.channel.send("No user found by that name.")
                return
            c.execute("SELECT name, record FROM players_team WHERE ID = ?", [x])
            user = c.fetchone()
            name = user[0]
            record = user[1]

            await ctx.channel.send(f"**{name}** has an elo peak of **{record}**.")

        elif name:

            x = ctx.author.id
            joined_dic[x] = gettime()
            t = ctx.message.author.id
            conn = sqlite3.connect(db_path, uri=True)
            c = conn.cursor()
            player = find_userid_by_name(ctx, name)
            if player is None:
                await ctx.channel.send("No user found by that name.")
                return
            c.execute("SELECT name, record FROM players_team WHERE ID = ?", [player])
            user = c.fetchone()
            name = user[0]
            record = user[1]

            await ctx.channel.send(f"**{name}** has an elo peak of **{record}**.")


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def kick(ctx, player):

    """Kicks a player out of the lobby."""

    global PLAYERS, GAME, db_path, joined_dic

    if ctx.channel.id == ones_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        n = ctx.author.name
        player = find_userid_by_name(ctx, player)
        if player is None:
            await ctx.channel.send("No user found by that name.")
            return
        c.execute("SELECT name FROM players WHERE ID = ?", [player])
        fetch = c.fetchone()
        user = fetch[0]

        try:
            if GAME:
                PLAYERS = list(set(PLAYERS))

                PLAYERS.remove(player)

                await ctx.channel.send("**" + str(user) + "** has been kicked from the lobby by **" + str(n) + "**.")
        except ValueError:
            await ctx.channel.send("**" + str(user) + " is not in lobby.")

        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        n = ctx.author.name
        player = find_userid_by_name(ctx, player)
        if player is None:
            await ctx.channel.send("No user found by that name.")
            return
        c.execute("SELECT name FROM players_team WHERE ID = ?", [player])
        fetch = c.fetchone()
        user = fetch[0]

        try:
            if GAME2:
                PLAYERS2 = list(set(PLAYERS2))

                PLAYERS2.remove(player)

                await ctx.channel.send("**" + str(user) + "** has been kicked from the lobby by **" + str(n) + "**.")
        except ValueError:
            await ctx.channel.send("**" + str(user) + " is not in lobby.")

        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        n = ctx.author.name
        player = find_userid_by_name(ctx, player)
        if player is None:
            await ctx.channel.send("No user found by that name.")
            return
        c.execute("SELECT name FROM players_team WHERE ID = ?", [player])
        fetch = c.fetchone()
        user = fetch[0]

        try:
            if GAME3:
                PLAYERS3 = list(set(PLAYERS3))

                PLAYERS3.remove(player)

                await ctx.channel.send("**" + str(user) + "** has been kicked from the lobby by **" + str(n) + "**.")
        except ValueError:
            await ctx.channel.send("**" + str(user) + " is not in lobby.")

        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def games(ctx):
    '''Shows current games being played.'''

    global PLAYERS, GAME, db_path, joined_dic

    if ctx.channel.id == ones_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()

        conn = sqlite3.connect(db_path, uri=True)
        t = ctx.message.author.id
        c = conn.cursor()
        
        c.execute("SELECT ID FROM games WHERE s1 IS NULL")
        games = c.fetchall()
        
        if len(games) == 0:
            await ctx.channel.send("There are no games running.")
        else:
            if len(games) == 1:
                #await ctx.channel.send("Found " + str(len(games)) + " active game!")
                pass
                
            else:
                print("Found " + str(len(games)) + " active games!")

            count = 1
            for game in games:
                c.execute("SELECT p1, p2 FROM games WHERE ID is ?", game)
                players = c.fetchone()

                c.execute("SELECT elo FROM PLAYERS where ID = ?", [players[0]])
                p1 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS where ID = ?", [players[1]])
                p2 = c.fetchone()[0]

                team1 = int(round(p1))
                team2 = int(round(p2))
                
                gameStr = "**Game " + str(game[0]) + ": **\n**Team 1: (" + str(team1) + ")** "
                count += 1
                playerCnt = 1
                for player in players:
                    c.execute("SELECT name, elo FROM players where ID = ?", [player])
                    result = c.fetchone()
                    name = result[0]
                    pts = int(round(result[1]))
                    gameStr += name + " [" + str(pts) + "]  "
                    if playerCnt == 1:
                        gameStr += "\n**Team 2: (" + str(team2) + ")** "
                    playerCnt += 1
                c.execute("SELECT currentg from players where currentg > 0")
                gn = c.fetchone()
                gID = gn[0]
                c.execute("SELECT ID, start_time FROM games WHERE ID = ?", [str(gID)])
                time = c.fetchone()
                start_time = time[1]
                done = datetime.datetime.now()
                done1 = done.strftime("%M")
                uptime = int(done1) - start_time
                await ctx.channel.send(gameStr)
                if uptime == 0:
                    await ctx.channel.send("Uptime: a few seconds.")
                if uptime ==  1:
                    await ctx.channel.send("Uptime: " + str(uptime) + " minute.")
                if uptime > 1:
                    await ctx.channel.send("Uptime: " + str(uptime) + " minutes.")
                if uptime < 0:
                    calc = int(uptime) + 60
                    await ctx.channel.send("Uptime: " + str(calc) + " minutes.")

        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()

        conn = sqlite3.connect(db_path, uri=True)
        t = ctx.message.author.id
        c = conn.cursor()
        
        c.execute("SELECT ID FROM games_team WHERE s1 IS NULL")
        games = c.fetchall()
        
        if len(games) == 0:
            await ctx.channel.send("There are no games running.")
        else:
            if len(games) == 1:

                pass
                
            else:

                print("Found " + str(len(games)) + " active games!")

            count = 1
            for game in games:
                c.execute("SELECT p1, p2, p3, p4 FROM games_team WHERE ID is ?", game)
                players = c.fetchone()

                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[0]])
                p1 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[1]])
                p2 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[2]])
                p3 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[3]])
                p4 = c.fetchone()[0]

                team1 = p1+p2
                team2 = p3+p4
                
                gameStr = "**Game " + str(game[0]) + ": **\n**Team 1: (" + str(team1) + ")** "
                count += 1
                playerCnt = 1
                for player in players:
                    c.execute("SELECT name, elo FROM players_team where ID = ?", [player])
                    result = c.fetchone()
                    name = result[0]
                    pts = int(round(result[1]))
                    gameStr += name + " [" + str(pts) + "]  "
                    if playerCnt == 2:
                        gameStr += "\n**Team 2: (" + str(team2) + ")** "
                    playerCnt += 1
                c.execute("SELECT currentg from players_team where currentg > 0")
                gn = c.fetchone()
                gID = gn[0]
                c.execute("SELECT ID, start_time FROM games_team WHERE ID = ?", [str(gID)])
                time = c.fetchone()
                start_time = time[1]
                done = datetime.datetime.now()
                done1 = done.strftime("%M")
                uptime = int(done1) - start_time
                await ctx.channel.send(gameStr)
                if uptime == 0:
                    await ctx.channel.send("Uptime: a few seconds.")
                if uptime == 1:
                    await ctx.channel.send("Uptime: " + str(uptime) + " minute.")
                if uptime > 1:
                    await ctx.channel.send("Uptime: " + str(uptime) + " minutes.")
                if uptime < 0:
                    calc = int(uptime) + 60
                    await ctx.channel.send("Uptime: " + str(calc) + " minutes.")

        conn.commit()
        conn.close()


    if ctx.channel.id == threes_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()

        conn = sqlite3.connect(db_path, uri=True)
        t = ctx.message.author.id
        c = conn.cursor()
        
        c.execute("SELECT ID FROM games_team WHERE s1 IS NULL")
        games = c.fetchall()
        
        if len(games) == 0:
            await ctx.channel.send("There are no games running.")
        else:
            if len(games) == 1:

                pass
                
            else:

                print("Found " + str(len(games)) + " active games!")

            count = 1
            for game in games:
                c.execute("SELECT p1, p2, p3, p4, p5, p6 FROM games_team WHERE ID is ?", game)
                players = c.fetchone()

                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[0]])
                p1 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[1]])
                p2 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[2]])
                p3 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[3]])
                p4 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[4]])
                p5 = c.fetchone()[0]
                c.execute("SELECT elo FROM PLAYERS_TEAM where ID = ?", [players[5]])
                p6 = c.fetchone()[0]

                team1 = p1+p2+p3
                team2 = p4+p5+p6
                
                gameStr = "**Game " + str(game[0]) + ": **\n**Team 1: (" + str(team1) + ")** "
                count += 1
                playerCnt = 0
                for player in players:
                    c.execute("SELECT name, elo FROM players_team where ID = ?", [player])
                    result = c.fetchone()
                    name = result[0]
                    pts = int(round(result[1]))
                    gameStr += name + " [" + str(pts) + "]  "
                    if playerCnt == 2:
                        gameStr += "\n**Team 2: (" + str(team2) + ")** "
                    playerCnt += 1
                c.execute("SELECT currentg from players_team where currentg > 0")
                gn = c.fetchone()
                gID = gn[0]
                c.execute("SELECT ID, start_time FROM games_team WHERE ID = ?", [str(gID)])
                time = c.fetchone()
                start_time = time[1]
                done = datetime.datetime.now()
                done1 = done.strftime("%M")
                uptime = int(done1) - start_time
                await ctx.channel.send(gameStr)
                if uptime == 0:
                    await ctx.channel.send("Uptime: a few seconds.")
                if uptime == 1:
                    await ctx.channel.send("Uptime: " + str(uptime) + " minute.")
                if uptime > 1:
                    await ctx.channel.send("Uptime: " + str(uptime) + " minutes.")
                if uptime < 0:
                    calc = int(uptime) + 60
                    await ctx.channel.send("Uptime: " + str(calc) + " minutes.")

        conn.commit()
        conn.close()

@client.command()
@commands.has_any_role("Dev")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int, channel:discord.TextChannel=None):

    """Delete's messages in channels."""

    if channel is None:

        await ctx.channel.purge(limit=limit)

@client.command(aliases=["j"])
async def join(ctx, gametype=None):

    """Joins a player into the lobby."""

    global PLAYERS, PLAYERS2, PLAYERS3, RUNNING, RUNNING2, RUNNING3, GAME, GAME2, GAME3, db_path, TEAMS, STARTING, STARTING2, STARTING3, lobby_channel, BANNED, joined_dic

    if ctx.channel.id == twos_channel.id:

        print("here")

        x = ctx.author
        t = ctx.message.author.id
        n = ctx.message.author.name
        member = ctx.author
        date = datetime.datetime.now()
        profile = "https://cdn1.bbcode0.com/uploads/2020/7/1/888ce487a07a840bf8f6c2bc7f842252-full.jpg"
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        c.execute("SELECT elo FROM players_team WHERE ID = ?", [t])
        mon = c.fetchone()

        if mon == None:
            c.execute('INSERT INTO players_team VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, ?, NULL, 400)',
                    [t, n, "Empty", date, str(profile)])
            c.execute("INSERT INTO warnings2 VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL)", [t,n])
            await ctx.channel.send("You are now registered.")
            role = discord.utils.get(ctx.guild.roles, name="League")
            await member.add_roles(role)
            conn.commit()

        c.execute("SELECT ID, name, elo, fresh_warns FROM players_team where ID = ?", [t])
        creator = ctx.message.author.name
        results = c.fetchone()
        ids = results[0]
        pts = int(round(results[2]))
        warns = results[3]

        c = conn.cursor()

        c.execute("SELECT currentg FROM players_team WHERE ID = ?", [t])

        A = c.fetchone()[0] is None

        if gametype == None:

            if t in PLAYERS2:
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME2 and A:

                if warns > 2:
                    await ctx.send("You are currently banned.")
                    return

                else:

                    PLAYERS2.append(t)
                    c.execute("SELECT ID, name, elo FROM players_team where ID = ?", [t])
                    result = c.fetchone()
                    ids = result[0]
                    name = result[1]
                    pts = int(round(result[2]))
                    joined_dic[t] = gettime()
                    await ctx.channel.send(
                        name + " **[" + str(pts) + "]** has joined the lobby. **(" + str(len(set(PLAYERS2))) + ")**")

            elif GAME2:
                await ctx.channel.send("You're still in a game.")

            if warns > 2:
                await ctx.channel.send("You are banned.")
                return

            else:
                c.execute("SELECT currentg FROM players_team WHERE ID = ?", [t])
                B = c.fetchone()[0]
                if B is None:
                    if not RUNNING2:
                        t = ctx.message.author.id
                        t2 = ctx.author.id
                        conn = sqlite3.connect(db_path)
                        c = conn.cursor()
                        counter = 0
                        SKATER_LIST2 = []
                        RUNNING2 = True
                        GAME2 = True
                        STARTING2 = False
                        PLAYERS2.append(ids)
                        joined_dic[t] = gettime()
                        await ctx.channel.send("Created a new lobby.")
                        await ctx.channel.send(
                            f"**{creator} [{pts}]** has joined the lobby! **(" + str(len(set(PLAYERS2))) + ")**")

                        while len(PLAYERS2) < 4 and counter < 900000000:
                            if STARTING2:
                                STARTING2 = False
                                print("Not enough players.")
                            await asyncio.sleep(10)
                            counter += 1
                            if len(set(PLAYERS2)) > 3:
                                STARTING2 = True
                                counter -= 1
                                #await ctx.channel.send(f"Starting lobby **(normal)** in **30** seconds.")
                                #await asyncio.sleep(30)
                            if len(set(PLAYERS2)) == 0 and counter > 6:
                                GAME2 = False
                                STARTING2 = False
                                RUNNING2 = False
                                return None

                        GAME2 = False
                        STARTING2 = False
                        if len(PLAYERS2) > 3:

                            np.random.shuffle(PLAYERS2)

                            ELOS = []
                            values = []
                            PLAYERS_AND_ELO = []
                            for t in PLAYERS2:
                                c.execute("SELECT elo, name FROM players_team WHERE ID = ?", [str(t)])
                                elo = c.fetchone()[0]
                                ELOS.append((t, int(elo)))
                                values.append(int(elo))

                            for t in PLAYERS2:
                                c.execute("SELECT name, elo FROM players_team WHERE ID = ?", [str(t)])
                                fetch = c.fetchone()
                                players_name = fetch[0]
                                players_elo = fetch[1]
                                PLAYERS_AND_ELO.append(players_name)
                                PLAYERS_AND_ELO.append(players_elo)

                            mu = np.mean(values)
                            sigma = 300
                            mask = np.ones(len(PLAYERS2)).astype(bool)

                            counterb = 0

                            while(sum(mask) != 4) and counterb < 250000:
                                for k,x in enumerate(values):
                                    mask[k] = np.random.uniform(0.0,1.0) < 1.0/2.0*(1.0+scipy.special.erf((x-mu)/(sigma*np.sqrt(2))))
                                counterb += 1

                            if sum(mask) == 4:
                                ELOS = list(np.array(ELOS)[mask])

                                team1 = sum([int(b[1]) for b in ELOS[0:2]])
                                team2 = sum([int(b[1]) for b in ELOS[2:4]])

                                diff = abs(team1-team2)

                                for t in itertools.permutations(ELOS, 4):
                                    team1 = sum([int(b[1]) for b in t[0:2]])
                                    team2 = sum([int(b[1]) for b in t[2:4]])
                                    if abs(team1 - team2) < diff:
                                        ELOS = t
                                        diff = abs(team1-team2)
                                c.execute("SELECT MAX(ID) from games_team")
                                gameID = c.fetchone()[0]
                                if gameID is None:
                                    gameID = 1
                                else:
                                    gameID = int(gameID) + 1

                                playerID = []
                                for t in ELOS:
                                    playerID.append(str(t[0]))

                                c.execute('INSERT INTO games_team VALUES(?, ?, ?, ?, ?, NULL, NULL, NULL,NULL,NULL,NULL,NULL,NULL,NULL)', [str(gameID)] + playerID)
                                start = datetime.datetime.now()
                                time = start.strftime("%M")
                                time_data2 = start.strftime("%B"),start.strftime("%d") + ", " + start.strftime("%Y"), start.strftime("%I") + ":" + start.strftime("%M") + " " + start.strftime("%p")
                                c.execute("UPDATE GAMES_team set start_time = ? WHERE ID = ?", [int(time), str(gameID)])
                                c.execute("UPDATE GAMES_team SET gamedate = ? WHERE ID = ?", [time_data2[0] + " " + time_data2[1] + " " + time_data2[2],str(gameID)])

                                for t in playerID:
                                    c.execute("UPDATE players_team SET currentg = ? WHERE ID = ?", [str(gameID), str(t)])

                                capt = 0
                                captid = ""
                                # finalstr = "**Game #" + str(gameID) + " started**:\n**Team 1 (" + str(sum([int(b[1]) for b in ELOS[0:2]])) + "):** "
                                # for k,t in enumerate(playerID):
                                #     c.execute("SELECT name FROM players WHERE ID = ?", [str(t)])
                                #     print(playerID)
                                #     name = c.fetchone()[0]
                                #     if(capt < int(ELOS[k][1])):
                                #         capt = int(ELOS[k][1])
                                #         captid = name
                                #     finalstr += name + "   "
                                #     if k == 1:
                                #         finalstr += "\n**Team 2 (" + str(sum([int(b[1])for b in ELOS[2:4]])) + "): **"
                                #         capt = 0
                                #         captid = ""

                                notestr = ""
                                for t in playerID:
                                    notestr += "<@" + t + "> "

                                total_elos = team1 + team2
                                team1_percentage = np.floor(team1 / total_elos * 100)
                                t1pp = round(team1_percentage)
                                team2_percentage = np.floor(team2 / total_elos * 100)
                                t2pp = round(team2_percentage)
                                diffe = np.abs(team1 - team2)

                                player_1 = f"{PLAYERS_AND_ELO[0]} [{int(round(PLAYERS_AND_ELO[1]))}]"
                                player_2 = f"{PLAYERS_AND_ELO[2]} [{int(round(PLAYERS_AND_ELO[3]))}]"
                                player_3 = f"{PLAYERS_AND_ELO[4]} [{int(round(PLAYERS_AND_ELO[5]))}]"
                                player_4 = f"{PLAYERS_AND_ELO[6]} [{int(round(PLAYERS_AND_ELO[7]))}]"

                                c.execute("SELECT ID FROM PLAYERS WHERE NAME = ?", [PLAYERS_AND_ELO[0]])
                                p1 = c.fetchone()[0]
                                
                                c.execute("SELECT ID FROM PLAYERS WHERE NAME = ?", [PLAYERS_AND_ELO[2]])
                                p2 = c.fetchone()[0]

                                c.execute("SELECT ID FROM PLAYERS WHERE NAME = ?", [PLAYERS_AND_ELO[4]])
                                p3 = c.fetchone()[0]
                                
                                c.execute("SELECT ID FROM PLAYERS WHERE NAME = ?", [PLAYERS_AND_ELO[6]])
                                p4 = c.fetchone()[0]

                                game_dict = {}
                                game_dict["ids"] = [p1, p2, p3, p4]
                                game_dict["teams"] = [[p1, p2], [p3, p4]]
                                game_dict["player_to_team"] = {}
                                for i, team in enumerate(game_dict["teams"]):
                                    for player in team:
                                        game_dict["player_to_team"][player] = i
                                game_dict["player_votes"] = defaultdict(str)
                                game_dict["vote_count"] = 0
                                game_dict["won"] = [0, 0, 0]
                                game_dict["lost"] = [0, 0, 0]
                                game_dict["draw"] = [0, 0, 0]
                                global_dict[gameID] = game_dict

                                team_1_sum = PLAYERS_AND_ELO[1]+PLAYERS_AND_ELO[3]
                                team_2_sum = PLAYERS_AND_ELO[5]+PLAYERS_AND_ELO[7]

                                final = f"**Game #{gameID} started:**\n**Team 1 ({int(round(team_1_sum))}):** {player_1} {player_2}\n**Team 2 ({int(round(team_2_sum))}):** {player_3} {player_4}\nTotal ELO Difference: {diff}.\nTeam 1: {t1pp}% probability to win;Team 2: {t2pp}% probability to win."

                                # finalstr += "\nTotal ELO Difference: " + str(diff) + "."
                                # finalstr += f"\nTeam 1: {t1pp}% probability to win;Team 2: {t2pp}% probability to win."
                                guild = discord.utils.get(client.guilds, id=383292703955222542)
                                lobby_channel = discord.utils.get(guild.channels, id=790313583484731422)
                                await lobby_channel.send(f"{final}\n{notestr}")

                                conn.commit()

                                PLAYERS2 = []

                            else:
                                await ctx.channel.send("Could not balance lobby.")
                                PLAYERS2 = []
                        else:
                            await ctx.channel.send("Not Enough Players")
                            PLAYERS2 = []

                        PLAYERS2 = []
                        RUNNING2 = False

                        conn.close()


    if ctx.channel.id == threes_channel.id:

        x = ctx.author
        t = ctx.message.author.id
        n = ctx.message.author.name
        member = ctx.author
        date = datetime.datetime.now()
        profile = "https://cdn1.bbcode0.com/uploads/2020/7/1/888ce487a07a840bf8f6c2bc7f842252-full.jpg"
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        c.execute("SELECT elo FROM players_team WHERE ID = ?", [t])
        mon = c.fetchone()

        if mon == None:
            c.execute('INSERT INTO players_team VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, ?, NULL, 400)',
                    [t, n, "Empty", date, str(profile)])
            c.execute("INSERT INTO warnings VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL)", [t,n])
            await ctx.channel.send("You are now registered.")
            role = discord.utils.get(ctx.guild.roles, name="League")
            await member.add_roles(role)
            conn.commit()

        c.execute("SELECT ID, name, elo, fresh_warns FROM players_team where ID = ?", [t])
        creator = ctx.message.author.name
        results = c.fetchone()
        ids = results[0]
        pts = int(round(results[2]))
        warns = results[3]

        c = conn.cursor()

        c.execute("SELECT currentg FROM players_team WHERE ID = ?", [t])

        A = c.fetchone()[0] is None

        if gametype == None:

            if t in PLAYERS3:
                joined_dic[t] = gettime()
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME3 and A:

                if warns > 2:
                    await ctx.send("You are currently banned.")
                    return

                else:

                    PLAYERS3.append(t)
                    c.execute("SELECT ID, name, elo FROM players_team where ID = ?", [t])
                    result = c.fetchone()
                    ids = result[0]
                    name = result[1]
                    pts = int(round(result[2]))
                    joined_dic[t] = gettime()
                    await ctx.channel.send(
                        name + " **[" + str(pts) + "]** has joined the lobby. **(" + str(len(set(PLAYERS3))) + ")**")

            elif GAME3:
                await ctx.channel.send("You're still in a game.")

            if warns > 2:
                await ctx.channel.send("You are banned.")
                return

            else:
                c.execute("SELECT currentg FROM players_team WHERE ID = ?", [t])
                B = c.fetchone()[0]
                if B is None:
                    if not RUNNING3:
                        t = ctx.message.author.id
                        t2 = ctx.author.id
                        conn = sqlite3.connect(db_path)
                        c = conn.cursor()
                        counter = 0
                        SKATER_LIST = []
                        RUNNING3 = True
                        GAME3 = True
                        STARTING3 = False
                        PLAYERS3.append(ids)
                        joined_dic[t] = gettime()
                        await ctx.channel.send("Created a new lobby.")
                        await ctx.channel.send(
                            f"**{creator} [{pts}]** has joined the lobby! **(" + str(len(set(PLAYERS3))) + ")**")

                        while len(PLAYERS3) < 6 and counter < 900000000:
                            # if STARTING:
                            #     STARTING = False
                            #     print("Not enough players.")
                            await asyncio.sleep(10)
                            counter += 1
                            if len(set(PLAYERS3)) > 5:
                                STARTING3 = True
                                counter -= 1
                            if len(set(PLAYERS3)) == 0 and counter > 6:
                                GAME3 = False
                                STARTING3 = False
                                RUNNING3 = False
                                return None

                        GAME3 = False
                        STARTING3 = False
                        if len(PLAYERS3) > 5:

                            np.random.shuffle(PLAYERS3)

                            ELOS = []
                            values = []
                            PLAYERS_AND_ELO = []
                            for t in PLAYERS3:
                                c.execute("SELECT elo, name FROM players_team WHERE ID = ?", [str(t)])
                                elo = c.fetchone()[0]
                                ELOS.append((t, int(elo)))
                                values.append(int(elo))

                            for t in PLAYERS3:
                                c.execute("SELECT name, elo FROM players_team WHERE ID = ?", [str(t)])
                                fetch = c.fetchone()
                                players_name = fetch[0]
                                players_elo = fetch[1]
                                PLAYERS_AND_ELO.append(players_name)
                                PLAYERS_AND_ELO.append(players_elo)
                            mu = np.mean(values)
                            sigma = 300
                            mask = np.ones(len(PLAYERS3)).astype(bool)

                            counterb = 0

                            while(sum(mask) != 6) and counterb < 250000:
                                for k,x in enumerate(values):
                                    mask[k] = np.random.uniform(0.0,1.0) < 1.0/2.0*(1.0+scipy.special.erf((x-mu)/(sigma*np.sqrt(2))))
                                counterb += 1

                            if sum(mask) == 6:
                                ELOS = list(np.array(ELOS)[mask])

                                team1 = sum([int(b[1]) for b in ELOS[0:3]])
                                team2 = sum([int(b[1]) for b in ELOS[3:6]])

                                diff = abs(team1-team2)

                                for t in itertools.permutations(ELOS, 6):
                                    team1 = sum([int(b[1]) for b in t[0:3]])
                                    team2 = sum([int(b[1]) for b in t[3:6]])
                                    if abs(team1 - team2) < diff:
                                        ELOS = t
                                        diff = abs(team1-team2)
                                c.execute("SELECT MAX(ID) from games_team")
                                gameID = c.fetchone()[0]
                                if gameID is None:
                                    gameID = 1
                                else:
                                    gameID = int(gameID) + 1

                                playerID = []
                                for t in ELOS:
                                    playerID.append(str(t[0]))

                                c.execute('INSERT INTO games_team VALUES(?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL,NULL,NULL,NULL,NULL)', [str(gameID)] + playerID)

                                start = datetime.datetime.now()
                                time = start.strftime("%M")
                                time_data2 = start.strftime("%B"),start.strftime("%d") + ", " + start.strftime("%Y"), start.strftime("%I") + ":" + start.strftime("%M") + " " + start.strftime("%p")
                                c.execute("UPDATE games_team set start_time = ? WHERE ID = ?", [int(time), str(gameID)])
                                c.execute("UPDATE games_team SET gamedate = ? WHERE ID = ?", [time_data2[0] + " " + time_data2[1] + " " + time_data2[2],str(gameID)])

                                for t in playerID:
                                    c.execute("UPDATE players_team SET currentg = ? WHERE ID = ?", [str(gameID), str(t)])

                                capt = 0
                                captid = ""
                                finalstr = "**Game #" + str(gameID) + " started**:\n**Team 1 (" + str(sum([int(b[1]) for b in ELOS[0:3]])) + "):** "
                                for k,t in enumerate(playerID):
                                    c.execute("SELECT name FROM players_team WHERE ID = ?", [str(t)])
                                    name = c.fetchone()[0]
                                    if(capt < int(ELOS[k][1])):
                                        capt = int(ELOS[k][1])
                                        captid = name
                                    finalstr += name + "   "
                                    if k == 1:
                                        finalstr += "\n**Team 2 (" + str(sum([int(b[1])for b in ELOS[3:6]])) + "): **"
                                        capt = 0
                                        captid = ""

                                conn.commit()

                                notestr = ""
                                for t in playerID:
                                    notestr += "<@" + t + "> "

                                total_elo = team1 + team2
                                team1_percent = team1 / total_elo * 100
                                t1p = round(team1_percent)
                                team2_percent = team2 / total_elo * 100
                                t2p = round(team2_percent)
                                diff = np.abs(team1 - team2)
                                print(PLAYERS_AND_ELO)

                                player_1 = f"{PLAYERS_AND_ELO[0]} [{int(round(PLAYERS_AND_ELO[1]))}]"
                                player_2 = f"{PLAYERS_AND_ELO[2]} [{int(round(PLAYERS_AND_ELO[3]))}]"
                                player_3 = f"{PLAYERS_AND_ELO[4]} [{int(round(PLAYERS_AND_ELO[5]))}]"
                                player_4 = f"{PLAYERS_AND_ELO[6]} [{int(round(PLAYERS_AND_ELO[7]))}]"
                                player_5 = f"{PLAYERS_AND_ELO[8]} [{int(round(PLAYERS_AND_ELO[9]))}]"
                                player_6 = f"{PLAYERS_AND_ELO[10]} [{int(round(PLAYERS_AND_ELO[11]))}]"
                                                                                                                            

                                team_1_sum = PLAYERS_AND_ELO[1] + PLAYERS_AND_ELO[3] + PLAYERS_AND_ELO[5]
                                team_2_sum = PLAYERS_AND_ELO[7] + PLAYERS_AND_ELO[9] + PLAYERS_AND_ELO[11]

                                print(PLAYERS_AND_ELO[0])
                                print(PLAYERS_AND_ELO[2])
                                print(PLAYERS_AND_ELO[4])
                                print(PLAYERS_AND_ELO[6])
                                print(PLAYERS_AND_ELO[8])
                                print(PLAYERS_AND_ELO[10])

                                c.execute("SELECT ID FROM PLAYERS_TEAM WHERE NAME = ?", [PLAYERS_AND_ELO[0]])
                                p1 = c.fetchone()[0]
                                
                                c.execute("SELECT ID FROM PLAYERS_TEAM WHERE NAME = ?", [PLAYERS_AND_ELO[2]])
                                p2 = c.fetchone()[0]

                                c.execute("SELECT ID FROM PLAYERS_TEAM WHERE NAME = ?", [PLAYERS_AND_ELO[4]])
                                p3 = c.fetchone()[0]
                                
                                c.execute("SELECT ID FROM PLAYERS_TEAM WHERE NAME = ?", [PLAYERS_AND_ELO[6]])
                                p4 = c.fetchone()[0]

                                c.execute("SELECT ID FROM PLAYERS_TEAM WHERE NAME = ?", [PLAYERS_AND_ELO[8]])
                                p5 = c.fetchone()[0]
                                
                                c.execute("SELECT ID FROM PLAYERS_TEAM WHERE NAME = ?", [PLAYERS_AND_ELO[10]])
                                p6 = c.fetchone()[0]

                                game_dict = {}
                                game_dict["ids"] = [p1, p2, p3, p4, p5, p6]
                                game_dict["teams"] = [[p1, p2, p3], [p4, p5, p6]]
                                game_dict["player_to_team"] = {}
                                for i, team in enumerate(game_dict["teams"]):
                                    for player in team:
                                        game_dict["player_to_team"][player] = i
                                game_dict["player_votes"] = defaultdict(str)
                                game_dict["vote_count"] = 0
                                game_dict["won"] = [0, 0, 0]
                                game_dict["lost"] = [0, 0, 0]
                                game_dict["draw"] = [0, 0, 0]
                                global_dict[gameID] = game_dict

                                final = f"**Game #{gameID} started:**\n**Team 1 ({int(round(team_1_sum))}):** {player_1}, {player_2}, {player_3}\n**Team 2 ({int(round(team_2_sum))}):** {player_4}, {player_5}, {player_6}\nTotal ELO Difference: {diff}.\nTeam 1: {t1p}% probability to win;Team 2: {t2p}% probability to win."

                                # finalstr += "\nTotal ELO Difference: " + str(diff) + "."
                                # finalstr += f"\nTeam 1: {t1pp}% probability to win;Team 2: {t2pp}% probability to win."
                                guild = discord.utils.get(client.guilds, id=383292703955222542)
                                lobby_channel = discord.utils.get(guild.channels, id=790313624395972668)
                                await lobby_channel.send(f"{final}\n{notestr}")

                                conn.commit()
                                
                                PLAYERS3 = []

                            else:
                                await ctx.channel.send("Could not balance lobby.")
                                PLAYERS3 = []
                        else:
                            await ctx.channel.send("Not Enough Players")
                            PLAYERS3 = []

                        PLAYERS3 = []
                        RUNNING3 = False

                        conn.close()


    if ctx.channel.id == ones_channel.id:

        x = ctx.author
        t = ctx.message.author.id
        n = ctx.message.author.name
        member = ctx.author
        date = datetime.datetime.now()
        profile = "https://cdn1.bbcode0.com/uploads/2020/7/1/888ce487a07a840bf8f6c2bc7f842252-full.jpg"
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        c.execute("SELECT elo FROM players WHERE ID = ?", [t])
        mon = c.fetchone()

        if mon == None:
            c.execute('INSERT INTO players VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, ?, NULL, 400)',
                    [t, n, "Empty", date, str(profile)])
            c.execute("INSERT INTO warnings VALUES(?,?,NULL,NULL,NULL,NULL,NULL,NULL)", [t,n])
            await ctx.channel.send("You are now registered.")
            role = discord.utils.get(ctx.guild.roles, name="League")
            await member.add_roles(role)
            conn.commit()

        c.execute("SELECT ID, name, elo, fresh_warns FROM players where ID = ?", [t])
        creator = ctx.message.author.name
        results = c.fetchone()
        ids = results[0]
        pts = int(round(results[2]))
        warns = results[3]

        c = conn.cursor()

        c.execute("SELECT currentg FROM players WHERE ID = ?", [t])
        Y = c.fetchone()[0]
        if Y is not None:
            await ctx.send("You're still in a game.")
            return

        c.execute("SELECT currentg FROM players WHERE ID = ?", [t])
        A = c.fetchone()[0] is None

        if gametype == None:

            if t in PLAYERS:
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME and A:

                if warns > 2:
                    await ctx.send("You are currently banned.")
                    return

                else:

                    PLAYERS.append(t)
                    c.execute("SELECT ID, name, elo FROM players where ID = ?", [t])
                    result = c.fetchone()
                    ids = result[0]
                    name = result[1]
                    pts = int(round(result[2]))
                    joined_dic[t] = gettime()
                    await ctx.channel.send(
                        name + " **[" + str(pts) + "]** has joined the lobby. **(" + str(len(set(PLAYERS))) + ")**")

            elif GAME:
                await ctx.channel.send("You're still in a game.")

            if warns > 2:
                await ctx.channel.send("You are banned.")
                return

            else:
                c.execute("SELECT currentg FROM players WHERE ID = ?", [t])
                B = c.fetchone()[0]
                if B is None:
                    if not RUNNING:
                        t = ctx.message.author.id
                        t2 = ctx.author.id
                        conn = sqlite3.connect(db_path)
                        c = conn.cursor()
                        counter = 0
                        SKATER_LIST = []
                        RUNNING = True
                        GAME = True
                        STARTING = False
                        PLAYERS.append(ids)
                        joined_dic[t] = gettime()
                        await ctx.channel.send("Created a new lobby.")
                        await ctx.channel.send(
                            f"**{creator} [{pts}]** has joined the lobby! **(" + str(len(set(PLAYERS))) + ")**")

                        while len(PLAYERS) < 2 and counter < 900000000:
                            if STARTING:
                                STARTING = False
                                print("Not enough players.")
                            await asyncio.sleep(10)
                            counter += 1
                            if len(set(PLAYERS)) > 2:
                                STARTING = True
                                counter -= 1
                                #await ctx.channel.send(f"Starting lobby {gametype} in **30** seconds.")
                                #await asyncio.sleep(30)
                            if len(set(PLAYERS)) == 0 and counter > 6:
                                GAME = False
                                STARTING = False
                                RUNNING = False
                                return None

                        GAME = False
                        STARTING = False
                        if len(PLAYERS) > 1:

                            np.random.shuffle(PLAYERS)

                            ELOS = []
                            values = []
                            PLAYERS_AND_ELO = []
                            for t in PLAYERS:
                                c.execute("SELECT elo, name FROM players WHERE ID = ?", [str(t)])
                                elo = c.fetchone()[0]
                                ELOS.append((t, int(elo)))
                                values.append(int(elo))

                            for t in PLAYERS:
                                c.execute("SELECT name, elo FROM players WHERE ID = ?", [str(t)])
                                fetch = c.fetchone()
                                players_name = fetch[0]
                                players_elo = fetch[1]
                                PLAYERS_AND_ELO.append(players_name)
                                PLAYERS_AND_ELO.append(players_elo)

                            mu = np.mean(values)
                            sigma = 300
                            mask = np.ones(len(PLAYERS)).astype(bool)

                            counterb = 0

                            while(sum(mask) != 2) and counterb < 250000:
                                for k,x in enumerate(values):
                                    mask[k] = np.random.uniform(0.0,1.0) < 1.0/2.0*(1.0+scipy.special.erf((x-mu)/(sigma*np.sqrt(2))))
                                counterb += 1

                            if sum(mask) == 2:
                                ELOS = list(np.array(ELOS)[mask])

                                team1 = sum([int(b[1]) for b in ELOS[0:1]])
                                team2 = sum([int(b[1]) for b in ELOS[1:2]])

                                diff = abs(team1-team2)

                                for t in itertools.permutations(ELOS, 2):
                                    team1 = sum([int(b[1]) for b in t[0:1]])
                                    team2 = sum([int(b[1]) for b in t[1:2]])
                                    if abs(team1 - team2) < diff:
                                        ELOS = t
                                        diff = abs(team1-team2)
                                c.execute("SELECT MAX(ID) from games")
                                gameID = c.fetchone()[0]
                                if gameID is None:
                                    gameID = 1
                                else:
                                    gameID = int(gameID) + 1

                                playerID = []
                                for t in ELOS:
                                    playerID.append(str(t[0]))

                                c.execute('INSERT INTO games VALUES(?, ?, ?, NULL, NULL, NULL, NULL, NULL,NULL,NULL,NULL,NULL,NULL,NULL)', [str(gameID)] + playerID)
                                start = datetime.datetime.now()
                                time = start.strftime("%M")
                                time_data2 = start.strftime("%B"),start.strftime("%d") + ", " + start.strftime("%Y"), start.strftime("%I") + ":" + start.strftime("%M") + " " + start.strftime("%p")
                                c.execute("UPDATE GAMES set start_time = ? WHERE ID = ?", [int(time), str(gameID)])
                                c.execute("UPDATE GAMES SET gamedate = ? WHERE ID = ?", [time_data2[0] + " " + time_data2[1] + " " + time_data2[2],str(gameID)])

                                for t in playerID:
                                    c.execute("UPDATE players SET currentg = ? WHERE ID = ?", [str(gameID), str(t)])

                                capt = 0
                                captid = ""
                                finalstr = "**Game #" + str(gameID) + " started**:\n**Team 1 (" + str(sum([int(b[1]) for b in ELOS[0:1]])) + "):** "
                                for k,t in enumerate(playerID):
                                    c.execute("SELECT name FROM players WHERE ID = ?", [str(t)])
                                    name = c.fetchone()[0]
                                    if(capt < int(ELOS[k][1])):
                                        capt = int(ELOS[k][1])
                                        captid = name
                                    finalstr += name + "   "
                                    if k == 0:
                                        finalstr += "\n**Team 2 (" + str(sum([int(b[1])for b in ELOS[1:2]])) + "): **"
                                        capt = 0
                                        captid = ""

                                notestr = ""
                                for t in playerID:
                                    notestr += "<@" + t + "> "

                                total_elos = team1 + team2
                                team1_percentage = np.floor(team1 / total_elos * 100)
                                t1pp = round(team1_percentage)
                                team2_percentage = np.floor(team2 / total_elos * 100)
                                t2pp = round(team2_percentage)
                                diffe = np.abs(team1 - team2)

                                player_1 = f"{PLAYERS_AND_ELO[0]} [{int(round(PLAYERS_AND_ELO[1]))}]"
                                player_2 = f"{PLAYERS_AND_ELO[2]} [{int(round(PLAYERS_AND_ELO[3]))}]"

                                team_1_sum = PLAYERS_AND_ELO[1]
                                team_2_sum = PLAYERS_AND_ELO[3]

                                final = f"**Game #{gameID} started:**\n**Team 1 ({int(round(team_1_sum))}):** {player_1}\n**Team 2 ({int(round(team_2_sum))}):** {player_2}\nTotal ELO Difference: {diff}.\nTeam 1: {t1pp}% probability to win;Team 2: {t2pp}% probability to win."
                                
                                p1name = PLAYERS_AND_ELO[0]
                                p2name = PLAYERS_AND_ELO[2]

                                c.execute("SELECT ID FROM PLAYERS WHERE NAME = ?", [p1name])
                                p1 = c.fetchone()[0]
                                
                                c.execute("SELECT ID FROM PLAYERS WHERE NAME = ?", [p2name])
                                p2 = c.fetchone()[0]

                                game_dict = {}
                                game_dict["ids"] = [p1, p2]
                                game_dict["teams"] = [[p1], [p2]]
                                game_dict["player_to_team"] = {p1: 0, p2: 1}
                                game_dict["player_votes"] = defaultdict(str)
                                game_dict["vote_count"] = 0
                                game_dict["won"] = [0, 0, 0]
                                game_dict["lost"] = [0, 0, 0]
                                game_dict["draw"] = [0, 0, 0]
                                global_dict[gameID] = game_dict

                                guild = discord.utils.get(client.guilds, id=383292703955222542)
                                lobby_channel = discord.utils.get(guild.channels, id=790313550270693396)
                                await lobby_channel.send(f"{final}\n{notestr}")

                                conn.commit()

                                PLAYERS = []

                            else:
                                await ctx.channel.send("Could not balance lobby.")
                                PLAYERS = []
                        else:
                            await ctx.channel.send("Not Enough Players")
                            PLAYERS = []

                        PLAYERS = []
                        RUNNING = False

                        conn.close()

        if gametype == "4v4":

            if t in PLAYERS:
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME and A:

                if warns > 2:
                    await ctx.send("You are currently banned.")
                    return

                else:

                    PLAYERS.append(t)
                    c.execute("SELECT ID, name, elo FROM players where ID = ?", [t])
                    result = c.fetchone()
                    ids = result[0]
                    name = result[1]
                    pts = int(round(result[2]))
                    joined_dic[t] = gettime()
                    await ctx.channel.send(
                        name + " **[" + str(pts) + "]** has joined the lobby. **(" + str(len(set(PLAYERS))) + ")**")

            elif GAME:
                await ctx.channel.send("You're still in a game.")

            if warns > 2:
                await ctx.channel.send("You are banned.")
                return

            else:
                c.execute("SELECT currentg FROM players WHERE ID = ?", [t])
                B = c.fetchone()[0]
                if B is None:
                    if not RUNNING:
                        t = ctx.message.author.id
                        t2 = ctx.author.id
                        conn = sqlite3.connect(db_path)
                        c = conn.cursor()
                        counter = 0
                        SKATER_LIST = []
                        RUNNING = True
                        GAME = True
                        STARTING = False
                        PLAYERS.append(ids)
                        joined_dic[t] = gettime()
                        await ctx.channel.send("Created a new lobby.")
                        await ctx.channel.send(
                            f"**{creator} [{pts}]** has joined the lobby! **(" + str(len(set(PLAYERS))) + ")**")

                        while len(PLAYERS) < 8 and counter < 900000000:
                            if STARTING:
                                STARTING = False
                                print("Not enough players.")
                            await asyncio.sleep(10)
                            counter += 1
                            if len(set(PLAYERS)) > 7:
                                STARTING = True
                                counter -= 1
                                await ctx.channel.send("Game starting in **30** seconds...")
                                await asyncio.sleep(30)
                            if len(set(PLAYERS)) == 0 and counter > 6:
                                GAME = False
                                STARTING = False
                                RUNNING = False
                                return None

                        GAME = False
                        STARTING = False
                        if len(PLAYERS) > 7:

                            np.random.shuffle(PLAYERS)

                            ELOS = []
                            values = []
                            PLAYERS_AND_ELO = []
                            for t in PLAYERS:
                                c.execute("SELECT elo, name FROM players WHERE ID = ?", [str(t)])
                                elo = c.fetchone()[0]
                                ELOS.append((t, int(elo)))
                                values.append(int(elo))

                            for t in PLAYERS:
                                c.execute("SELECT name, elo FROM players WHERE ID = ?", [str(t)])
                                fetch = c.fetchone()
                                players_name = fetch[0]
                                players_elo = fetch[1]
                                PLAYERS_AND_ELO.append(players_name)
                                PLAYERS_AND_ELO.append(players_elo)

                            mu = np.mean(values)
                            sigma = 300
                            mask = np.ones(len(PLAYERS)).astype(bool)

                            counterb = 0

                            while(sum(mask) != 8) and counterb < 250000:
                                for k,x in enumerate(values):
                                    mask[k] = np.random.uniform(0.0,1.0) < 1.0/2.0*(1.0+scipy.special.erf((x-mu)/(sigma*np.sqrt(2))))
                                counterb += 1

                            if sum(mask) == 8:
                                ELOS = list(np.array(ELOS)[mask])

                                team1 = sum([int(b[1]) for b in ELOS[0:4]])
                                team2 = sum([int(b[1]) for b in ELOS[4:8]])

                                diff = abs(team1-team2)

                                for t in itertools.permutations(ELOS, 8):
                                    team1 = sum([int(b[1]) for b in t[0:4]])
                                    team2 = sum([int(b[1]) for b in t[4:8]])
                                    if abs(team1 - team2) < diff:
                                        ELOS = t
                                        diff = abs(team1-team2)
                                c.execute("SELECT MAX(ID) from games")
                                gameID = c.fetchone()[0]
                                if gameID is None:
                                    gameID = 1
                                else:
                                    gameID = int(gameID) + 1

                                playerID = []
                                for t in ELOS:
                                    playerID.append(str(t[0]))

                                c.execute('INSERT INTO games VALUES(?, ?, ?, NULL, NULL, NULL, NULL, NULL,NULL,NULL,NULL)', [str(gameID)] + playerID)

                                start = datetime.datetime.now()
                                time = start.strftime("%M")
                                c.execute("UPDATE GAMES set start_time = ? WHERE ID = ?", [int(time), str(gameID)])

                                for t in playerID:
                                    c.execute("UPDATE players SET currentg = ? WHERE ID = ?", [str(gameID), str(t)])

                                capt = 0
                                captid = ""
                                finalstr = "**Game #" + str(gameID) + " started**:\n**Team 1 (" + str(sum([int(b[1]) for b in ELOS[0:4]])) + "):** "
                                for k,t in enumerate(playerID):
                                    c.execute("SELECT name FROM players WHERE ID = ?", [str(t)])
                                    name = c.fetchone()[0]
                                    if(capt < int(ELOS[k][1])):
                                        capt = int(ELOS[k][1])
                                        captid = name
                                    finalstr += name + "   "
                                    if k == 3:
                                        finalstr += "\n**Team 2 (" + str(sum([int(b[1])for b in ELOS[4:8]])) + "): **"
                                        capt = 0
                                        captid = ""

                                notestr = ""
                                for t in playerID:
                                    notestr += "<@" + t + "> "

                                total_elos = team1 + team2
                                team1_percentage = np.floor(team1 / total_elos * 100)
                                t1pp = round(team1_percentage)
                                team2_percentage = np.floor(team2 / total_elos * 100)
                                t2pp = round(team2_percentage)
                                diffe = np.abs(team1 - team2)

                                player_1 = f"{PLAYERS_AND_ELO[0]} [{PLAYERS_AND_ELO[1]}]"
                                player_2 = f"{PLAYERS_AND_ELO[2]} [{PLAYERS_AND_ELO[3]}]"
                                player_3 = f"{PLAYERS_AND_ELO[4]} [{PLAYERS_AND_ELO[5]}]"
                                player_4 = f"{PLAYERS_AND_ELO[6]} [{PLAYERS_AND_ELO[7]}]"
                                player_5 = f"{PLAYERS_AND_ELO[8]} [{PLAYERS_AND_ELO[9]}]"
                                player_6 = f"{PLAYERS_AND_ELO[10]} [{PLAYERS_AND_ELO[11]}]"
                                player_7 = f"{PLAYERS_AND_ELO[12]} [{PLAYERS_AND_ELO[13]}]"
                                player_8 = f"{PLAYERS_AND_ELO[14]} [{PLAYERS_AND_ELO[15]}]"

                                team_1_sum = PLAYERS_AND_ELO[1] + PLAYERS_AND_ELO[3] + PLAYERS_AND_ELO[5] + PLAYERS_AND_ELO[7]
                                team_2_sum = PLAYERS_AND_ELO[9] + PLAYERS_AND_ELO[11] + PLAYERS_AND_ELO[13] + PLAYERS_AND_ELO[15]

                                final = f"**Game #{gameID} started:**\n**Team 1 ({team_1_sum}):** {player_1}, {player_2}, {player_3}, {player_4}\n**Team 2 ({team_2_sum}):** {player_5}, {player_6}, {player_7}, {player_8}\nTotal ELO Difference: {diff}.\nTeam 1: {t1pp}% probability to win;Team 2: {t2pp}% probability to win."

                                # finalstr += "\nTotal ELO Difference: " + str(diff) + "."
                                # finalstr += f"\nTeam 1: {t1pp}% probability to win;Team 2: {t2pp}% probability to win."
                                guild = discord.utils.get(client.guilds, id=784960512534380586)
                                lobby_channel = discord.utils.get(guild.channels, id=785009271317463091)
                                await lobby_channel.send(f"{final}\n{notestr}")

                                conn.commit()

                                PLAYERS = []

                            else:
                                await ctx.channel.send("Could not balance lobby.")
                                PLAYERS = []
                        else:
                            await ctx.channel.send("Not Enough Players")
                            PLAYERS = []

                        PLAYERS = []
                        RUNNING = False

                        conn.close()



@client.command(aliases=["l"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def leave(ctx):
    '''Removes user from both lobby.'''

    global PLAYERS, PLAYERS2, PLAYERS3, db_path

    if ctx.channel.id == ones_channel.id:

        t = ctx.message.author.id

        conn = sqlite3.connect(db_path, uri=True)

        c = conn.cursor()

        if ctx.message.channel.id == ones_channel.id:
            if GAME:
                try:
                    PLAYERS = list(set(PLAYERS))
                    PLAYERS.remove(ctx.message.author.id)
                    c.execute("SELECT name, elo FROM players where ID = ?", [t])
                    result = c.fetchone()
                    name = result[0]
                    pts = int(round(result[1]))
                    await ctx.channel.send(
                        name + "** [" + str(pts) + "]** has removed their signup! **(" + str(len(set(PLAYERS))) + ")**")
                    # await ctx.channel.edit(topic="Open Lobby (" + str(len(set(PLAYERS))) + "/8)", reason=None)
                except:
                    True
            else:
                await ctx.channel.send("You're not in a lobby.")

        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:

        t = ctx.message.author.id

        conn = sqlite3.connect(db_path, uri=True)

        c = conn.cursor()

        if ctx.message.channel.id == twos_channel.id:
            if GAME2:
                try:
                    PLAYERS2 = list(set(PLAYERS2))
                    PLAYERS2.remove(ctx.message.author.id)
                    c.execute("SELECT name, elo FROM players where ID = ?", [t])
                    result = c.fetchone()
                    name = result[0]
                    pts = int(round(results[1]))
                    await ctx.channel.send(
                        name + "** [" + str(pts) + "]** has removed their signup! **(" + str(len(set(PLAYERS2))) + ")**")
                    # await ctx.channel.edit(topic="Open Lobby (" + str(len(set(PLAYERS))) + "/8)", reason=None)
                except:
                    True
            else:
                await ctx.channel.send("You're not in a lobby.")

        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id:

        t = ctx.message.author.id

        conn = sqlite3.connect(db_path, uri=True)

        c = conn.cursor()

        if ctx.message.channel.id == threes_channel.id:
            if GAME3:
                try:
                    PLAYERS3 = list(set(PLAYERS3))
                    PLAYERS3.remove(ctx.message.author.id)
                    c.execute("SELECT name, elo FROM players where ID = ?", [t])
                    result = c.fetchone()
                    name = result[0]
                    pts = int(round(result[1]))
                    await ctx.channel.send(
                        name + "** [" + str(pts) + "]** has removed their signup! **(" + str(len(set(PLAYERS3))) + ")**")
                    # await ctx.channel.edit(topic="Open Lobby (" + str(len(set(PLAYERS))) + "/8)", reason=None)
                except:
                    True
            else:
                await ctx.channel.send("You're not in a lobby.")

        conn.commit()
        conn.close()


@client.command()
@commands.cooldown(1, 1, commands.BucketType.user)
async def game(ctx, result):
    """Process game results."""

    if ctx.channel.id == threes_channel.id or ctx.channel.id == twos_channel.id:

        if result not in ["won", "lost", "draw"]:
            await ctx.send("Invalid vote.")
            return
        
        activity_channel = ctx.guild.get_channel(790313358816968715)
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        auth = ctx.message.author.id

        c.execute("SELECT name FROM players_team WHERE ID = ?", [ctx.author.id])
        name = c.fetchone()[0]
        if name in no_score:
            no_score.remove(name)

        c.execute("SELECT currentg FROM players_team where ID = ?", [str(auth)])
        currentg = c.fetchone()
        game_id = int(currentg[0])

        game_dict = global_dict[game_id]
        ids = game_dict["ids"]
        num_players = len(ids)
        players_per_team = int(len(ids)/2)
        team_index = game_dict["player_to_team"][auth]
        old_vote = game_dict["player_votes"][auth] # empty str "" means no vote

        game_type = f"{players_per_team}v{players_per_team}"

        await ctx.send(f"[{game_type}] Game #{game_id}: <@{auth}> voted {result}.")

        if old_vote != result:

            if old_vote != "":
                game_dict[old_vote][team_index] -= 1
                game_dict[old_vote][2] -= 1
            else:
                game_dict["vote_count"] += 1

            game_dict["player_votes"][auth] = result
            game_dict[result][team_index] += 1
            game_dict[result][2] += 1

            if game_dict["draw"][2] >= players_per_team + 1:
                await activity_channel.send(f"[{game_type}] Game #" + str(game_id) + " has been drawn.")
                await ctx.channel.send(f"[{game_type}] Game #" + str(game_id) + " has been drawn.")

                for t in ids:
                    c.execute("UPDATE players_team SET currentg = NULL where ID = ?", [str(t)])

                c.execute("UPDATE games_team SET s1 = ? where ID = ?", ["Draw", game_id])
                c.execute("UPDATE games_team SET s2 = ? where ID = ?", ["Draw", game_id])

                conn.commit()
                conn.close()
                del global_dict[game_id]

            elif game_dict["vote_count"] == num_players:
                if game_dict["won"][2] != players_per_team or game_dict["lost"][2] != players_per_team or not (game_dict["won"][0] == players_per_team or game_dict["won"][1] == players_per_team):
                    await ctx.send("One team must win and the other must lose - All players on each team must vote correctly. Votes have been reset.")
                    game_dict["player_votes"] = defaultdict(str)
                    game_dict["vote_count"] = 0
                    game_dict["won"] = [0, 0, 0]
                    game_dict["lost"] = [0, 0, 0]
                    game_dict["draw"] = [0, 0, 0]
                else:
                    team_won = game_dict["teams"][0]
                    team_lost = game_dict["teams"][1]

                    if game_dict["won"][0] != players_per_team:
                        team_won, team_lost = team_lost, team_won
                        c.execute("UPDATE games_team SET s1 = ? where ID = ?", ["lost",game_id])
                        c.execute("UPDATE games_team SET s2 = ? where ID = ?", ["won",game_id])
                    else:
                        c.execute("UPDATE games_team SET s1 = ? where ID = ?", ["won",game_id])
                        c.execute("UPDATE games_team SET s2 = ? where ID = ?", ["lost",game_id])
                
                    ELOS = []
                    
                    team1 = []
                    for t in team_won:
                        c.execute("SELECT elo, sigma FROM players_team where ID = ?", [str(t)])
                        row = c.fetchone()
                        elo = row[0]
                        sigma = row[1]
                        team1.append(trueskill.Rating(elo, sigma))
                    
                    team2 = []
                    for t in team_lost:
                        c.execute("SELECT elo, sigma FROM players_team where ID = ?", [str(t)])
                        row = c.fetchone()
                        elo = row[0]
                        sigma = row[1]
                        team2.append(trueskill.Rating(elo, sigma))

                    team1, team2 = trueskill.rate([team1, team2])

                    for i, t in enumerate(team_won):
                        c.execute("UPDATE players_team SET win = win + 1 where ID = ?", [str(t)])
                        c.execute("UPDATE players_team SET streak = streak + 1 WHERE ID = ?", [str(t)])
                        c.execute("UPDATE players_team SET elo = ? where ID = ?", [team1[i].mu, t])
                        c.execute("UPDATE players_team SET sigma = ? where ID = ?", [team1[i].sigma, t])
                        c.execute("UPDATE players_team SET currentg = NULL where ID = ?", [t])

                    for i, t in enumerate(team_lost):
                        c.execute("UPDATE players_team SET loss = loss + 1 where ID = ?", [str(t)])
                        c.execute("UPDATE players_team SET streak = 0 WHERE ID = ?", [str(t)])
                        c.execute("UPDATE players_team SET elo = ? where ID = ?", [team2[i].mu, t])
                        c.execute("UPDATE players_team SET sigma = ? where ID = ?", [team2[i].sigma, t])
                        c.execute("UPDATE players_team SET currentg = NULL where ID = ?", [t])

                    conn.commit()
                    conn.close()
                    del global_dict[game_id]

                    await activity_channel.send(f"[{game_type}] Game #" + str(game_id) + " has finished.")
                    await ctx.channel.send(f"[{game_type}] Game #" + str(game_id) + " has finished.")                    
                    await leaderboard_team(ctx)

    if ctx.channel.id == ones_channel.id:
        
        if result not in ["won", "lost", "draw"]:
            await ctx.send("Invalid vote.")
            return

        activity_channel = ctx.guild.get_channel(790313358816968715)
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        auth = ctx.message.author.id
        c.execute("SELECT name FROM players WHERE ID = ?", [ctx.author.id])
        name = c.fetchone()[0]
        if name in no_score:
            no_score.remove(name)
        c.execute("SELECT currentg FROM players where ID = ?", [str(auth)])
        currentg = c.fetchone()
        game_id = int(currentg[0])

        # c.execute("SELECT * FROM games where ID = ?", [str(game_id)])
        # ids = c.fetchone()[1:3]
        game_dict = global_dict[game_id]
        ids = game_dict["ids"]
        num_players = len(ids)
        players_per_team = len(ids)/2
        team_index = game_dict["player_to_team"][auth]
        old_vote = game_dict["player_votes"][auth] # empty str "" means no vote

        await ctx.send(f"[1v1] Game #{game_id}: <@{auth}> voted {result}.")

        if auth == ids[0] or auth == ids[1] and num_players == 2 and old_vote != result:
            
            if old_vote != "":
                game_dict[old_vote][team_index] -= 1
                game_dict[old_vote][2] -= 1
            else:
                game_dict["vote_count"] += 1

            game_dict["player_votes"][auth] = result
            game_dict[result][team_index] += 1
            game_dict[result][2] += 1

            if game_dict["vote_count"] == num_players:
                if game_dict["draw"][2] == num_players:
                    await activity_channel.send("[1v1] Game #" + str(game_id) + " has been drawn.")
                    await ctx.channel.send("[1v1] Game #" + str(game_id) + " has been drawn.")

                    for t in ids:
                        c.execute("UPDATE players SET currentg = NULL where ID = ?", [str(t)])

                    c.execute("UPDATE games SET s1 = ? where ID = ?", ["Draw",game_id])
                    c.execute("UPDATE games SET s2 = ? where ID = ?", ["Draw",game_id])

                    conn.commit()
                    conn.close()
                    del global_dict[game_id]

                elif game_dict["won"][2] != players_per_team or game_dict["lost"][2] != players_per_team or not (game_dict["won"][0] == players_per_team or game_dict["won"][1] == players_per_team):
                    await ctx.send("One team must win and the other must lose - All players on each team must vote correctly. Votes have been reset.")
                    game_dict["player_votes"] = defaultdict(str)
                    game_dict["vote_count"] = 0
                    game_dict["won"] = [0, 0, 0]
                    game_dict["lost"] = [0, 0, 0]
                    game_dict["draw"] = [0, 0, 0]
                else:
                    team_won = game_dict["teams"][0]
                    team_lost = game_dict["teams"][1]

                    if game_dict["won"][0] != players_per_team:
                        team_won, team_lost = team_lost, team_won
                        c.execute("UPDATE games SET s1 = ? where ID = ?", ["lost",game_id])
                        c.execute("UPDATE games SET s2 = ? where ID = ?", ["won",game_id])
                    else:
                        c.execute("UPDATE games SET s1 = ? where ID = ?", ["won",game_id])
                        c.execute("UPDATE games SET s2 = ? where ID = ?", ["lost",game_id])

                    # ELOS = []
                    for t in team_won:
                        c.execute("SELECT elo, sigma FROM players where ID = ?", [str(t)])
                        row1 = c.fetchone()
                        elo1 = row1[0]
                        sigma1 = row1[1]
                        # ELOS.append(c.fetchone())
                    
                    for t in team_lost:
                        c.execute("SELECT elo, sigma FROM players where ID = ?", [str(t)])
                        row2 = c.fetchone()
                        elo2 = row2[0]
                        sigma2 = row2[1]
                        # ELOS.append(c.fetchone())

                    skill = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1),trueskill.Rating(elo2, sigma2))

                    for t in team_won:
                        c.execute("UPDATE players SET win = win + 1 where ID = ?", [str(t)])
                        c.execute("UPDATE players SET streak = streak + 1 WHERE ID = ?", [str(t)])
                        c.execute("UPDATE players SET elo = ? where ID = ?", [skill[0].mu, t])
                        c.execute("UPDATE players SET sigma = ? where ID = ?", [skill[0].sigma, t])
                        c.execute("UPDATE players SET currentg = NULL where ID = ?", [t])

                    for t in team_lost:
                        c.execute("UPDATE players SET loss = loss + 1 where ID = ?", [str(t)])
                        c.execute("UPDATE players SET streak = 0 WHERE ID = ?", [str(t)])
                        c.execute("UPDATE players SET elo = ? where ID = ?", [skill[1].mu, t])
                        c.execute("UPDATE players SET sigma = ? where ID = ?", [skill[1].sigma, t])
                        c.execute("UPDATE players SET currentg = NULL where ID = ?", [t])

                    conn.commit()
                    conn.close()
                    del global_dict[game_id]

                    await activity_channel.send("[1v1] Game #" + str(game_id) + " has finished.")
                    await ctx.channel.send("[1v1] Game #" + str(game_id) + " has finished.")
                    await leaderboard_solo(ctx)

@client.command()
async def stats(ctx):
    '''Shows a players statistics.'''

    global db_path, joined_dic

    
    # if ctx.channel.id == ones_channel.id:
    #     players_table = "players"
    # elif ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:
    #     players_table = "players_team"
    # else:
    #     return

    teams = False
    players_table = "players"

    if ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:
        teams = True
        players_table += "_team"
        
    x = ctx.author.id
    joined_dic[x] = gettime()
        
    name = str(ctx.message.content)[7:]
    t = find_userid_by_name(ctx, name)
    if t is None:
        await ctx.channel.send("No user found by that name!")
        return

    conn = sqlite3.connect(db_path, uri=True)

    c = conn.cursor()
    c.execute(f"SELECT name, elo, sigma, win, loss, streak, record, rank FROM {players_table} where ID = ?", [t])
    player = c.fetchone()

    if player is not None:
        name, elo, sigma, win, loss, streak, peak_elo, rank = player
        total_games = win + loss
        if streak > 0:
            streak = f"{streak}"
        if total_games == 0:
            await ctx.channel.send(f"{name} played no games and has an elo of **{elo:.1f}**.")
        else:
            await ctx.channel.send(f"**{name}** has played **{total_games}** games with a win rate of **{(win / total_games) * 100:.1f}%** (**{win}**W - **{loss}**L). ELO: **{elo:.1f}**. Sigma: **{sigma:.1f}**. Streak: **{streak}**. Rank: **{rank if rank else 'Need 20 games minimum'}**.")
        
        grandmaster = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grandmaster.png"
        master = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/master.png"
        adept = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/adept.png"
        diamond = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/diamond.png"
        platinum = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/platinum.png"
        gold = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/gold.png"
        silver = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/silver.png"
        bronze = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/bronze.png"
        grass = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grass.png"

        if rank == 1:
            url = grandmaster
            emoji = "<:grandmaster:821047027257311234>"

        if 2 <= rank and rank <= 4:
            url = master
            emoji = "<:master:821047027412631603>"
        
        if 5 <= rank and rank <= 8:
            url = adept
            emoji = "<:adept:821047027391660094>"

        if 9 <= rank and rank <= 12:
            url = diamond
            emoji = "<:diamond:821047028237860924>"

        if 13 <= rank and rank <= 16:
            url = platinum
            emoji = "<:platinum:821047027584467004>"

        if 17 <= rank and rank <= 20:
            url = gold
            emoji = "<:gold:821047027675955200>"
        
        if 21 <= rank and rank <= 24:
            url = silver
            emoji = "<:silver:821047027374751806>"
        
        if 25 <= rank and rank <= 28:
            url = bronze
            emoji = "<:bronze:821047027575422996>"
        
        if rank > 30:
            url = grass
            emoji = "<:grass:821047027638992966>"

        for emoji in ctx.guild.emojis:
            print(f"<:{emoji.name}:{emoji.id}>")
    else:
        await ctx.channel.send("No user found by that name!")

    conn.commit()
    conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def warns(ctx, player=None):

    '''Show's warnings on a player'''

    global joined_dic

    test_channel = discord.Object(785006530310438912)

    if ctx.channel.id == ones_channel.id or test_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()

        t = ctx.author.id
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT fresh_warns, name FROM players WHERE ID = ?", [t])
        fetch = c.fetchone()
        warns = fetch[0]
        name = fetch[1]

        c.execute("SELECT reason1, reason2, reason3, time_of_warn1, time_of_warn2, time_of_warn3 FROM warnings WHERE ID = ?", [t])
        fetch5 = c.fetchone()
        reasonone = fetch5[0]
        reasontwo = fetch5[1]
        reasonthree = fetch5[2]
        timeone = fetch5[3]
        timetwo = fetch5[4]
        timethree = fetch5[5]


        if player == None:

            if warns == 0:
                await ctx.send(f"{name} has {warns} warnings.")

            if warns > 0:

                if reasontwo == None:
                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\nNext unwarn in ")
                    return

                if reasonthree == None:
                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\n[2] {reasontwo} on {timetwo}\nNext unwarn in ")            
                    return

                else:

                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\n[2] {reasontwo} on {timetwo}\n[3] {reasonthree} on {timethree}\nNext unwarn in ")
                    return

        elif player:

            player = find_userid_by_name(ctx, player)

            if player is None:
                await ctx.channel.send(f"'{player}' not found.")
                return

            c.execute("SELECT name, fresh_warns FROM players WHERE ID = ?", [player])
            fetch2 = c.fetchone()
            player_warns = fetch2[1]
            player_name = fetch2[0]

            c.execute("SELECT reason1, reason2, reason3, time_of_warn1, time_of_warn2, time_of_warn3 FROM warnings WHERE ID = ?", [player])
            fetch3 = c.fetchone()
            reason1 = fetch3[0]
            reason2 = fetch3[1]
            reason3 = fetch3[2]
            time1 = fetch3[3]
            time2 = fetch3[4]
            time3 = fetch3[5]

            if player_warns == 0:
                await ctx.send(f"{player_name} has {warns} warnings.")
                return
            
            if player_warns > 0:

                # If you have all 3 warns:

                if reason1 is not None and reason2 is not None and reason3 is not None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[2] {reason2} on {time2}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have warns 1 and 2 only:

                if reason1 is not None and reason2 is not None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[2] {reason2} on {time2}\nNext unwarn in ")

                # If you have warns 1 and 3 only:

                if reason1 is not None and reason3 is not None and reason2 == None:

                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have warns 3 and 2 only:

                if reason3 is not None and reason2 is not None and reason1 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[2] {reason2} on {time2}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you only the 3rd warn:

                if reason1 == None and reason2 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have only the 2nd warn:

                if reason1 == None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[2] {reason2} on {time2}\nNext unwarn in ")

                # If you have only the 1st warn:

                if reason2 == None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\nNext unwarn in ")

                return
                    
        conn.close()

    if ctx.channel.id == twos_channel.id or test_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()

        t = ctx.author.id
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT fresh_warns, name FROM players_team WHERE ID = ?", [t])
        fetch = c.fetchone()
        warns = fetch[0]
        name = fetch[1]

        c.execute("SELECT reason1, reason2, reason3, time_of_warn1, time_of_warn2, time_of_warn3 FROM warnings2 WHERE ID = ?", [t])
        fetch5 = c.fetchone()
        reasonone = fetch5[0]
        reasontwo = fetch5[1]
        reasonthree = fetch5[2]
        timeone = fetch5[3]
        timetwo = fetch5[4]
        timethree = fetch5[5]


        if player == None:

            if warns == 0:
                await ctx.send(f"{name} has {warns} warnings.")

            if warns > 0:

                if reasontwo == None:
                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\nNext unwarn in ")
                    return

                if reasonthree == None:
                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\n[2] {reasontwo} on {timetwo}\nNext unwarn in ")            
                    return

                else:

                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\n[2] {reasontwo} on {timetwo}\n[3] {reasonthree} on {timethree}\nNext unwarn in ")
                    return

        elif player:

            player = find_userid_by_name(ctx, player)

            if player is None:
                await ctx.channel.send(f"'{player}' not found.")
                return

            c.execute("SELECT name, fresh_warns FROM players_team WHERE ID = ?", [player])
            fetch2 = c.fetchone()
            player_warns = fetch2[1]
            player_name = fetch2[0]

            c.execute("SELECT reason1, reason2, reason3, time_of_warn1, time_of_warn2, time_of_warn3 FROM warnings2 WHERE ID = ?", [player])
            fetch3 = c.fetchone()
            reason1 = fetch3[0]
            reason2 = fetch3[1]
            reason3 = fetch3[2]
            time1 = fetch3[3]
            time2 = fetch3[4]
            time3 = fetch3[5]

            if player_warns == 0:
                await ctx.send(f"{player_name} has {warns} warnings.")
                return
            
            if player_warns > 0:

                # If you have all 3 warns:

                if reason1 is not None and reason2 is not None and reason3 is not None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[2] {reason2} on {time2}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have warns 1 and 2 only:

                if reason1 is not None and reason2 is not None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[2] {reason2} on {time2}\nNext unwarn in ")

                # If you have warns 1 and 3 only:

                if reason1 is not None and reason3 is not None and reason2 == None:

                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have warns 3 and 2 only:

                if reason3 is not None and reason2 is not None and reason1 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[2] {reason2} on {time2}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you only the 3rd warn:

                if reason1 == None and reason2 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have only the 2nd warn:

                if reason1 == None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[2] {reason2} on {time2}\nNext unwarn in ")

                # If you have only the 1st warn:

                if reason2 == None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\nNext unwarn in ")

                return
                    
        conn.close()

    if ctx.channel.id == threes_channel.id or test_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()

        t = ctx.author.id
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT fresh_warns, name FROM players_team WHERE ID = ?", [t])
        fetch = c.fetchone()
        warns = fetch[0]
        name = fetch[1]

        c.execute("SELECT reason1, reason2, reason3, time_of_warn1, time_of_warn2, time_of_warn3 FROM warnings3 WHERE ID = ?", [t])
        fetch5 = c.fetchone()
        reasonone = fetch5[0]
        reasontwo = fetch5[1]
        reasonthree = fetch5[2]
        timeone = fetch5[3]
        timetwo = fetch5[4]
        timethree = fetch5[5]


        if player == None:

            if warns == 0:
                await ctx.send(f"{name} has {warns} warnings.")

            if warns > 0:

                if reasontwo == None:
                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\nNext unwarn in ")
                    return

                if reasonthree == None:
                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\n[2] {reasontwo} on {timetwo}\nNext unwarn in ")            
                    return

                else:

                    await ctx.send(f"{name} has {warns} warnings:\n[1] {reasonone} on {timeone}\n[2] {reasontwo} on {timetwo}\n[3] {reasonthree} on {timethree}\nNext unwarn in ")
                    return

        elif player:

            player = find_userid_by_name(ctx, player)

            if player is None:
                await ctx.channel.send(f"'{player}' not found.")
                return

            c.execute("SELECT name, fresh_warns FROM players_team WHERE ID = ?", [player])
            fetch2 = c.fetchone()
            player_warns = fetch2[1]
            player_name = fetch2[0]

            c.execute("SELECT reason1, reason2, reason3, time_of_warn1, time_of_warn2, time_of_warn3 FROM warnings3 WHERE ID = ?", [player])
            fetch3 = c.fetchone()
            reason1 = fetch3[0]
            reason2 = fetch3[1]
            reason3 = fetch3[2]
            time1 = fetch3[3]
            time2 = fetch3[4]
            time3 = fetch3[5]

            if player_warns == 0:
                await ctx.send(f"{player_name} has {warns} warnings.")
                return
            
            if player_warns > 0:

                # If you have all 3 warns:

                if reason1 is not None and reason2 is not None and reason3 is not None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[2] {reason2} on {time2}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have warns 1 and 2 only:

                if reason1 is not None and reason2 is not None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[2] {reason2} on {time2}\nNext unwarn in ")

                # If you have warns 1 and 3 only:

                if reason1 is not None and reason3 is not None and reason2 == None:

                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have warns 3 and 2 only:

                if reason3 is not None and reason2 is not None and reason1 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[2] {reason2} on {time2}\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you only the 3rd warn:

                if reason1 == None and reason2 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[3] {reason3} on {time3}\nNext unwarn in ")

                # If you have only the 2nd warn:

                if reason1 == None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[2] {reason2} on {time2}\nNext unwarn in ")

                # If you have only the 1st warn:

                if reason2 == None and reason3 == None:
                    await ctx.send(f"{player_name} has {player_warns} warnings:\n[1] {reason1} on {time1}\nNext unwarn in ")

                return
                    
        conn.close()

@client.command()
@commands.cooldown(1, 2, commands.BucketType.user)
async def compare(ctx, p1, p2):

    """Compares two users statistics.""" 

    global db_path, joined_dic

    if ctx.channel.id == ones_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        x = ctx.author.id
        joined_dic[x] = gettime()
        
        t1 = find_userid_by_name(ctx, p1)
        if t1 is None:
            await ctx.channel.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.channel.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = float(result[1])
        sigma1 = float(result[2])
        

        t2 = find_userid_by_name(ctx, p2)
        if t2 is None:
            await ctx.channel.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.channel.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        name2 = result[0]
        elo2 = float(result[1])
        sigma2 = float(result[2])
        
        wins = 0
        losses = 0
        
        c.execute("SELECT s1 FROM games WHERE (p1 == ? AND p2 == ? AND p3 IS NULL) AND s1 != s2", [t1, t2])
        game = c.fetchone()
        while game is not None:
            result = game[0]
            if result == "won":
                wins += 1
            elif result == "lost":
                losses += 1
            else:
                # shouldn't happen, maybe error or print to terminal
                pass
            
            game = c.fetchone()
        
        c.execute("SELECT s2 FROM games WHERE (p1 == ? AND p2 == ? AND p3 IS NULL) AND s1 != s2", [t2, t1])
        game = c.fetchone()
        while game is not None:
            result = game[0]
            if result == "won":
                wins += 1
            elif result == "lost":
                losses += 1
            else:
                # shouldn't happen, maybe error or print to terminal
                pass
            
            game = c.fetchone()

        def erfc(x):
            """Complementary error function (via `http://bit.ly/zOLqbc`_)"""
            z = abs(x)
            t = 1. / (1. + z / 2.)
            r = t * np.math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (
                0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (
                    0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (
                        -0.82215223 + t * 0.17087277
                    )))
                )))
            )))
            return 2. - r if x < 0 else r


        def cdf(x, mu=0, sigma=1):
            """Cumulative distribution function"""
            return 0.5 * erfc(-(x - mu) / (sigma * np.math.sqrt(2)))

        # win_probability
        BETA=200
        deltaMu = elo1 - elo2
        sumSigma = sigma1**2 + sigma2**2
        rsss = np.sqrt(2* (BETA**2) + sumSigma)
        win_probability = cdf(deltaMu/rsss)

        if wins + losses > 0:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have played a total of {wins + losses} games together.\n"
            s += f"{name1} has a win rate of {wins/(wins+losses)*100:.2f}% (**{wins}W - {losses}L**) against {name2}.\n"
        else:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have not played any games together.\n"

        s += f"{name1}'s expected win probability against {name2} is {win_probability*100:.2f}%."
        
        await ctx.channel.send(s)
        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id or ctx.channel.id == twos_channel:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        x = ctx.author.id
        joined_dic[x] = gettime()
        
        t1 = find_userid_by_name(ctx, p1)
        if t1 is None:
            await ctx.channel.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo FROM players_team where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.channel.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = str(result[1])
        

        t2 = find_userid_by_name(ctx, p2)
        if t2 is None:
            await ctx.channel.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo FROM players_team where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.channel.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        name2 = result[0]
        elo2 = str(result[1])
        
        wins_together = 0
        loss_together = 0
        wins_against  = 0
        loss_against  = 0
        
        c.execute("SELECT s1, s2, ID FROM games_team where (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND s1 != s2", [t1, t1, t1, t1, t2, t2, t2, t2])
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]
            if s1 > s2:
                wins_together += 1
            elif s1 < s2:
                loss_together += 1  
            
            game = c.fetchone()
        
        c.execute("SELECT s1, s2, ID FROM games_team where (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND s1 != s2", [t1, t1, t1, t1, t2, t2, t2, t2])
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]
            
            if s1 < s2:
                wins_together += 1
            elif s1 > s2:
                loss_together += 1
            
            game = c.fetchone()

        c.execute("SELECT s1, s2 FROM games_team where (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND s1 != s2", [t1, t1, t1, t1, t2, t2, t2, t2])
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]
            
            if s1 > s2:
                wins_against += 1
            elif s1 < s2:
                loss_against += 1
            
            game = c.fetchone()
        
        c.execute("SELECT s1, s2 FROM games_team where (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND s1 != s2", [t1, t1, t1, t1, t2, t2, t2, t2])
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]
            
            if s1 < s2:
                wins_against += 1
            elif s1 > s2:
                loss_against += 1
            
            game = c.fetchone()

        total_together = wins_together + loss_together
        if total_together > 0:
            winrate_together = float("{0:.2f}".format((wins_together / total_together) * 100))
            str_together = name1 + " **[" + elo1 + "]** and " + name2 + " **[" + elo2 + "]** have played " + str(total_together) + " games together with a win rate of " + str(winrate_together) + "% (**" + str(wins_together) + "W - " + str(loss_together) + "L**)."
        else:
            str_together = name1 + " **[" + elo1 + "]** and " + name2 + " **[" + elo2 + "]** have not played together."
        
        total_against = wins_against + loss_against
        if total_against > 0:
            winrate_against = float("{0:.2f}".format((wins_against / total_against) * 100))
            str_against = name1 + " **[" + elo1 + "]** has played against " + name2 + " **[" + elo2 + "]** a total of " + str(total_against) + " times with a win rate of " + str(winrate_against) + "% (**" + str(wins_against) + "W - " + str(loss_against) + "L**) ."
        else:
            str_against = name1 + " **[" + elo1 + "]** and " + name2 + " **[" + elo2 + "]** have not played against each other."
        
        
        await ctx.channel.send(str_together + "\n" + str_against)
        conn.commit()
        conn.close()


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin', 'PwR Team')
async def set_elo(ctx, name, adjustment):
    '''Adjusts a players ELO.'''

    global db_path
    
    adjustment = int(adjustment)

    if ctx.channel.id == ones_channel.id:
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, elo FROM players WHERE ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players SET elo = ? WHERE ID = ?",
                      [adjustment, t])

            out = ctx.message.author.name + "has set " + name + "'s Sigma to **" + str(adjustment) + "**!"
            activity_channel = client.get_channel(790313358816968715)
            await ctx.channel.send(out)
            await activity_channel.send(out)
        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, elo FROM players_team WHERE ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players_team SET elo = ? WHERE ID = ?",
                      [adjustment, t])

            out = ctx.message.author.name + "has set " + name + "'s Sigma to **" + str(adjustment) + "**!"
            activity_channel = client.get_channel(790313358816968715)
            await ctx.channel.send(out)
            await activity_channel.send(out)
        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin', 'PwR Team')
async def set_sigma(ctx, name, adjustment):
    '''Adjusts a players Sigma.'''

    global db_path

    adjustment = int(adjustment)

    if ctx.channel.id == ones_channel.id:
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, sigma FROM players WHERE ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players SET sigma = ? WHERE ID = ?",
                      [adjustment, t])


            out = ctx.message.author.name + "has set " + name + "'s Sigma to **" + str(adjustment) + "**!"

            activity_channel = client.get_channel(790313358816968715)
            await ctx.channel.send(out)
            await activity_channel.send(out)
        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, sigma FROM players_team WHERE ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players_team SET sigma = ? WHERE ID = ?",
                      [adjustment, t])

            out = ctx.message.author.name + "has set " + name + "'s Sigma to **" + str(adjustment) + "**!"
            activity_channel = client.get_channel(790313358816968715)
            await ctx.channel.send(out)
            await activity_channel.send(out)
        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin', 'PwR Team')
async def update_leaderboards(ctx):
    """ Manually updates the leaderboard."""

    if ctx.channel.id == ones_channel.id or ctx.channel.id == twos_channel.id or ctx.channel.id == threes_channel.id:

        await leaderboard_solo(ctx)
        await leaderboard_team(ctx)
        t = ctx.message.author.name
        activity_channel = client.get_channel(790313358816968715)
        await ctx.channel.send(str(t) + " has updated the leaderboard.")
        await activity_channel.send(str(t) + " has updated the leaderboard.")


@client.command()
@commands.has_any_role('League Admin')
async def warn(ctx, name, *, reason, aliases=["w", "aw", "warns", "addwarn", "addwarns"]):
    '''Warns a player.'''


    if ctx.channel.id == ones_channel.id:
            
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.send("No user found by that name!")
            return

        user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, warnings, fresh_warns, id FROM players where ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            warns = player[1] + player[2]
            stale_warns = player[1]
            fresh_warns = player[2]
            ids = player[3]

            if reason is not None:
                if warns is None:
                    warns = 0

                time = datetime.datetime.now()

                time_data = time.strftime("%B"),time.strftime("%d") + ", " + time.strftime("%Y"), time.strftime("%I") + ":" + time.strftime("%M") + " " + time.strftime("%p")

                if warns == 0:

                    new_warns = warns
                    c.execute("UPDATE players SET fresh_warns = ? where ID = ?", [1, t])
                    c.execute("UPDATE warnings SET reason1 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings SET time_of_warn1 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warning"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if warns == 1:
                    
                    new_warns = warns
                    c.execute("UPDATE players SET fresh_warns = fresh_warns + 1 where ID = ?", [t])
                    c.execute("UPDATE warnings SET reason2 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings SET time_of_warn2 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warnings"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if warns == 2:
                    
                    new_warns = warns
                    c.execute("UPDATE players SET fresh_warns = fresh_warns + 1 where ID = ?", [t])
                    c.execute("UPDATE warnings SET reason3 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings SET time_of_warn3 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warnings"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if user is not None:
                    pass

                reason = "{}".format(reason)

                if warns >= 3:
                    out += " and remain **banned**"

                elif warns >= 3:
                    out += " and are now **banned**"


                await ctx.send(out + ".")
                activity_channel = client.get_channel(790313358816968715)
                await activity_channel.send(activity_out + ".")

            else:
                await ctx.send("Warn amount must be positive.")
        else:
            await ctx.send("No user found by that name!")

        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:
            
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.send("No user found by that name!")
            return

        user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, warnings, fresh_warns, id FROM players_team where ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            warns = player[1] + player[2]
            stale_warns = player[1]
            fresh_warns = player[2]
            ids = player[3]

            if reason is not None:
                if warns is None:
                    warns = 0

                time = datetime.datetime.now()

                time_data = time.strftime("%B"),time.strftime("%d") + ", " + time.strftime("%Y"), time.strftime("%I") + ":" + time.strftime("%M") + " " + time.strftime("%p")

                if warns == 0:

                    new_warns = warns
                    c.execute("UPDATE players_team SET fresh_warns = ? where ID = ?", [1, t])
                    c.execute("UPDATE warnings2 SET reason1 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings2 SET time_of_warn1 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warning"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if warns == 1:
                    
                    new_warns = warns
                    c.execute("UPDATE players_team SET fresh_warns = fresh_warns + 1 where ID = ?", [t])
                    c.execute("UPDATE warnings2 SET reason2 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings2 SET time_of_warn2 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warnings"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if warns == 2:
                    
                    new_warns = warns
                    c.execute("UPDATE players_team SET fresh_warns = fresh_warns + 1 where ID = ?", [t])
                    c.execute("UPDATE warnings2 SET reason3 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings2 SET time_of_warn3 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warnings"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if user is not None:
                    pass

                reason = "{}".format(reason)

                if warns >= 3:
                    out += " and remain **banned**"

                elif warns >= 3:
                    out += " and are now **banned**"


                await ctx.send(out + ".")
                activity_channel = client.get_channel(790313358816968715)
                await activity_channel.send(activity_out + ".")

            else:
                await ctx.send("Warn amount must be positive.")
        else:
            await ctx.send("No user found by that name!")

        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id:
            
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.send("No user found by that name!")
            return

        user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, warnings, fresh_warns, id FROM players_team where ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            warns = player[1] + player[2]
            stale_warns = player[1]
            fresh_warns = player[2]
            ids = player[3]

            if reason is not None:
                if warns is None:
                    warns = 0

                time = datetime.datetime.now()

                time_data = time.strftime("%B"),time.strftime("%d") + ", " + time.strftime("%Y"), time.strftime("%I") + ":" + time.strftime("%M") + " " + time.strftime("%p")

                if warns == 0:

                    new_warns = warns
                    c.execute("UPDATE players_team SET fresh_warns = ? where ID = ?", [1, t])
                    c.execute("UPDATE warnings3 SET reason1 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings3 SET time_of_warn1 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warning"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if warns == 1:
                    
                    new_warns = warns
                    c.execute("UPDATE players_team SET fresh_warns = fresh_warns + 1 where ID = ?", [t])
                    c.execute("UPDATE warnings3 SET reason2 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings3 SET time_of_warn2 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warnings"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if warns == 2:
                    
                    new_warns = warns
                    c.execute("UPDATE players_team SET fresh_warns = fresh_warns + 1 where ID = ?", [t])
                    c.execute("UPDATE warnings3 SET reason3 = ? WHERE ID = ?", [reason + " by " + ctx.author.name, t])
                    c.execute("UPDATE warnings3 SET time_of_warn3 = ? WHERE ID = ?", [time_data[0] + " " + time_data[1] + " " + time_data[2], t])
                    new_warns = new_warns + 1
                    out = f"<@{t}> a warning has been issued by **{ctx.author.name}** for {reason}. You now have **{new_warns}** warnings"
                    activity_out = f"**{ctx.message.author.name}** has issued **1** warnings to **{name}** for {reason}. \nThey now have **{new_warns}** warnings"
                    new_warns = 0

                if user is not None:
                    pass

                reason = "{}".format(reason)

                if warns >= 3:
                    out += " and remain **banned**"

                elif warns >= 3:
                    out += " and are now **banned**"


                await ctx.send(out + ".")
                activity_channel = client.get_channel(790313358816968715)
                await activity_channel.send(activity_out + ".")

            else:
                await ctx.send("Warn amount must be positive.")
        else:
            await ctx.send("No user found by that name!")

        conn.commit()
        conn.close()
        
@client.command(aliases=["rw", "removewarn"])
@commands.has_any_role('League Admin')
async def unwarn(ctx, name, warnings=None):
    '''Unwarns a player.'''

    if ctx.channel.id == ones_channel.id:

        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.send("No user found by that name!")
            return

        user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, warnings, fresh_warns, ID FROM players where ID = ?", [t])
        player = c.fetchone()

        c.execute("SELECT reason1,reason2,reason3 FROM warnings WHERE ID = ?", [t])
        row = c.fetchone()
        reason1 = row[0]
        reason2 = row[1]
        reason3 = row[2]

        if player is not None:
            name = player[0]
            warns = player[2]
            stale_warns = player[1]
            fresh_warns = player[2]
            ids = player[3]

            if int(warnings) > 0:
                if warns is None:
                    warns = 0

                if warns == 1:

                    if int(warnings) == 1:
                            
                        c.execute("UPDATE warnings SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:
                            
                        c.execute("UPDATE warnings SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 3:

                        c.execute("UPDATE warnings SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"



                if warns == 2:

                    if int(warnings) == 1:

                        c.execute("UPDATE warnings SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:
                            
                        c.execute("UPDATE warnings SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 3:
                            
                        c.execute("UPDATE warnings SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"

                if warns == 3:

                    if int(warnings) == 1:

                        c.execute("UPDATE warnings SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:

                        c.execute("UPDATE warnings SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"
                        
                    if int(warnings) == 3:

                        c.execute("UPDATE warnings SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"

                if user is not None:
                    pass

                if warns >= 3:
                    out += " and remain **banned**"
                elif warns >= 3:
                    out += " and are now **unbanned**"

                activity_channel = client.get_channel(790313358816968715)
                await ctx.send(out + ".")
                if ctx.message.channel.id != admin_channel.id:
                    await activity_channel.send(activity_out + ".")
            else:
                await ctx.send("Warn amount must be positive.")
        else:
            await ctx.send("No user found by that name!")

        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:

        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.send("No user found by that name!")
            return

        user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, warnings, fresh_warns, ID FROM players_team where ID = ?", [t])
        player = c.fetchone()

        c.execute("SELECT reason1,reason2,reason3 FROM warnings2 WHERE ID = ?", [t])
        row = c.fetchone()
        reason1 = row[0]
        reason2 = row[1]
        reason3 = row[2]

        if player is not None:
            name = player[0]
            warns = player[2]
            stale_warns = player[1]
            fresh_warns = player[2]
            ids = player[3]

            if int(warnings) > 0:
                if warns is None:
                    warns = 0

                if warns == 1:

                    if int(warnings) == 1:
                            
                        c.execute("UPDATE warnings2 SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:
                            
                        c.execute("UPDATE warnings2 SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 3:

                        c.execute("UPDATE warnings2 SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"



                if warns == 2:

                    if int(warnings) == 1:

                        c.execute("UPDATE warnings2 SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:
                            
                        c.execute("UPDATE warnings2 SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 3:
                            
                        c.execute("UPDATE warnings2 SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"

                if warns == 3:

                    if int(warnings) == 1:

                        c.execute("UPDATE warnings2 SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:

                        c.execute("UPDATE warnings2 SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"
                        
                    if int(warnings) == 3:

                        c.execute("UPDATE warnings2 SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings2 SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"

                if user is not None:
                    pass

                if warns >= 3:
                    out += " and remain **banned**"
                elif warns >= 3:
                    out += " and are now **unbanned**"

                activity_channel = client.get_channel(790313358816968715)
                await ctx.send(out + ".")
                if ctx.message.channel.id != admin_channel.id:
                    await activity_channel.send(activity_out + ".")
            else:
                await ctx.send("Warn amount must be positive.")
        else:
            await ctx.send("No user found by that name!")

        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id:

        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.send("No user found by that name!")
            return

        user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, warnings, fresh_warns, ID FROM players_team where ID = ?", [t])
        player = c.fetchone()

        c.execute("SELECT reason1,reason2,reason3 FROM warnings3 WHERE ID = ?", [t])
        row = c.fetchone()
        reason1 = row[0]
        reason2 = row[1]
        reason3 = row[2]

        if player is not None:
            name = player[0]
            warns = player[2]
            stale_warns = player[1]
            fresh_warns = player[2]
            ids = player[3]

            if int(warnings) > 0:
                if warns is None:
                    warns = 0

                if warns == 1:

                    if int(warnings) == 1:
                            
                        c.execute("UPDATE warnings3 SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:
                            
                        c.execute("UPDATE warnings3 SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 3:

                        c.execute("UPDATE warnings3 SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"



                if warns == 2:

                    if int(warnings) == 1:

                        c.execute("UPDATE warnings3 SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:
                            
                        c.execute("UPDATE warnings3 SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 3:
                            
                        c.execute("UPDATE warnings3 SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"

                if warns == 3:

                    if int(warnings) == 1:

                        c.execute("UPDATE warnings3 SET reason1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn1 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason1}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason1}.\nThey now have **{warns}** warnings"

                    if int(warnings) == 2:

                        c.execute("UPDATE warnings3 SET reason2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn2 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason2}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason2}.\nThey now have **{warns}** warnings"
                        
                    if int(warnings) == 3:

                        c.execute("UPDATE warnings3 SET reason3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE warnings3 SET time_of_warn3 = NULL WHERE ID = ?", [t])
                        c.execute("UPDATE players_team SET fresh_warns = fresh_warns - 1 where ID = ?", [t])
                        warns = warns - 1
                        out = f"<@{t}> a warning has been removed by **{ctx.message.author.name}** for {reason3}. You now have {warns} warnings"
                        activity_out = f"**{ctx.message.author.name}** has removed a warning from {name} for {reason3}.\nThey now have **{warns}** warnings"

                if user is not None:
                    pass

                if warns >= 3:
                    out += " and remain **banned**"
                elif warns >= 3:
                    out += " and are now **unbanned**"

                activity_channel = client.get_channel(790313358816968715)
                await ctx.send(out + ".")
                if ctx.message.channel.id != admin_channel.id:
                    await activity_channel.send(activity_out + ".")
            else:
                await ctx.send("Warn amount must be positive.")
        else:
            await ctx.send("No user found by that name!")

        conn.commit()
        conn.close()

@client.command()
@commands.has_any_role("League Admin")
async def update_nickname(ctx, player: discord.Member, nickname):

    """Updates a players nickname."""

    if ctx.channel.id == ones_channel.id:

        playerID = player.id
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE players SET name = ? WHERE ID = ?", [nickname, playerID])
        await ctx.send("Nickname updated.")
        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:

        playerID = player.id
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE players_team SET name = ? WHERE ID = ?", [nickname, playerID])
        await ctx.send("Nickname updated.")
        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id:

        playerID = player.id
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE players_team SET name = ? WHERE ID = ?", [nickname, playerID])
        await ctx.send("Nickname updated.")
        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def noscore(ctx):

    global no_score

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for game_id in c.execute("SELECT MAX(ID) FROM GAMES"):
        game_ID = (game_id[0])
        
    await ctx.send("**Game #" + str(game_ID) + "**: " + ', '.join(no_score))


record_pattern = re.compile(".*\[.*\].*\[.*\].*\[.*\].*", flags=re.IGNORECASE)

@client.command()
@commands.has_any_role("League Admin")
async def record_legacy(ctx, *args):
    record_info = " ".join(args)
    # !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2] 
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2]")
        # print fail, give !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2] as working example
        return
    
    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end)
    result_end = record_info.find("]", result_start) + 1
    results = [int(k) for k in eval(record_info[result_start:result_end])]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
        # print fail, results is a list showing the order of wins for each team (for example, [1,2,1] means team 1 won, then team 2 won then team 1 won again)
        return

    ids = []
    i = 0
    team1 = []
    while i < len(team1_str):
        c = team1_str[i]
        if c == "<":
            player_id = ""
            i += 3 # <@!361548991755976704>
            c = team1_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = team1_str[i]
            team1.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(team1) == 0:
        # print fail, team 1 empty
        await ctx.send("Team 1 empty.")
        return

    i = 0
    team2 = []
    while i < len(team2_str):
        c = team2_str[i]
        if c == "<":
            player_id = ""
            i += 3
            c = team2_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = team2_str[i]
            team2.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(team2) == 0:
        await ctx.send("Team 2 empty.")
        # print fail, team 2 empty
        return
    
    if len(team1) != len(team2):
        # print unbalanced teams
        await ctx.send("Unbalanced teams.")
        return
        
    activity_channel = ctx.guild.get_channel(790313358816968715)
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    auth = ctx.message.author.id

    games_table = "games"
    players_table = "players"

    if len(team1) > 1:
        games_table += "_team"
        players_table += "_team"

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 1
    else:
        game_id = int(game_id) + 1

    start = datetime.datetime.now()
    time = start.strftime("%M")
    time_data2 = start.strftime("%B"),start.strftime("%d") + ", " + start.strftime("%Y"), start.strftime("%I") + ":" + start.strftime("%M") + " " + start.strftime("%p")

    values = "?, " + "?, " * len(ids) + "NULL, " * (8 - len(ids)) + "?, ?, ?, NULL, ?"
    values1 = [str(p) for p in team1] + [str(p) for p in team2] + ["won", "lost"] + [int(time)] + [time_data2[0] + " " + time_data2[1] + " " + time_data2[2]]
    values2 = [str(p) for p in team1] + [str(p) for p in team2] + ["lost", "won"] + [int(time)] + [time_data2[0] + " " + time_data2[1] + " " + time_data2[2]]

    game_type = f"{len(team1)}v{len(team1)}"

    for result in results:
        
        if result == 1:
            c.execute(f"INSERT INTO {games_table} VALUES({values})", [str(game_id)] + values1)
            team_won = team1
            team_lost = team2
        else:
            c.execute(f"INSERT INTO {games_table} VALUES({values})", [str(game_id)] + values2)
            team_won = team2
            team_lost = team1

        team_won_ratings = []
        for t in team_won:
            c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(t)])
            row = c.fetchone()
            elo = row[0]
            sigma = row[1]
            team_won_ratings.append(trueskill.Rating(elo, sigma))
        
        team_lost_ratings = []
        for t in team_lost:
            c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(t)])
            row = c.fetchone()
            elo = row[0]
            sigma = row[1]
            team_lost_ratings.append(trueskill.Rating(elo, sigma))

        team_won_ratings, team_lost_ratings = trueskill.rate([team_won_ratings, team_lost_ratings])

        for i, t in enumerate(team_won):
            c.execute(f"UPDATE {players_table} SET win = win + 1 where ID = ?", [str(t)])
            c.execute(f"UPDATE {players_table} SET streak = streak + 1 WHERE ID = ?", [str(t)])
            c.execute(f"UPDATE {players_table} SET elo = ? where ID = ?", [team_won_ratings[i].mu, t])
            c.execute(f"UPDATE {players_table} SET sigma = ? where ID = ?", [team_won_ratings[i].sigma, t])

        for i, t in enumerate(team_lost):
            c.execute(f"UPDATE {players_table} SET loss = loss + 1 where ID = ?", [str(t)])
            c.execute(f"UPDATE {players_table} SET streak = 0 WHERE ID = ?", [str(t)])
            c.execute(f"UPDATE {players_table} SET elo = ? where ID = ?", [team_lost_ratings[i].mu, t])
            c.execute(f"UPDATE {players_table} SET sigma = ? where ID = ?", [team_lost_ratings[i].sigma, t])

        conn.commit()
        #conn.close()
        #del global_dict[game_id]

        await activity_channel.send(f"[{game_type}] Game #" + str(game_id) + " has finished.")
        await ctx.channel.send(f"[{game_type}] Game #" + str(game_id) + " has finished.")
        game_id += 1

    if len(team1) > 1:
        await leaderboard_team(ctx)
    else:
        await leaderboard_solo(ctx)
    
    conn.close()

@client.command()
@commands.has_any_role("League Admin")
async def record(ctx, *args):
    record_info = " ".join(args)
    # !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2] 
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2]")
        # print fail, give !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2] as working example
        return
    
    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end)
    result_end = record_info.find("]", result_start) + 1
    results = [int(k) for k in eval(record_info[result_start:result_end])]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
        # print fail, results is a list showing the order of wins for each team (for example, [1,2,1] means team 1 won, then team 2 won then team 1 won again)
        return

    ids = []
    i = 0
    team1 = []
    while i < len(team1_str):
        c = team1_str[i]
        if c == "<":
            player_id = ""
            i += 3 # <@!361548991755976704>
            c = team1_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = team1_str[i]
            team1.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(team1) == 0:
        # print fail, team 1 empty
        await ctx.send("Team 1 empty.")
        return
    if len(team1) > 1:
        await ctx.send("Team 1 has too many players (there should only be 1).")
        return

    i = 0
    team2 = []
    while i < len(team2_str):
        c = team2_str[i]
        if c == "<":
            player_id = ""
            i += 3
            c = team2_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = team2_str[i]
            team2.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(team2) == 0:
        await ctx.send("Team 2 empty.")
        # print fail, team 2 empty
        return
    if len(team1) > 1:
        await ctx.send("Team 2 has too many players (there should only be 1).")
        return

    activity_channel = ctx.guild.get_channel(790313358816968715)
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    auth = ctx.message.author.id

    games_table = "games"
    players_table = "players"

    player1 = team1[0]
    player2 = team2[0]

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 1
    else:
        game_id = int(game_id) + 1

    start = datetime.datetime.now()
    time = start.strftime("%M")
    time_data2 = start.strftime("%B"),start.strftime("%d") + ", " + start.strftime("%Y"), start.strftime("%I") + ":" + start.strftime("%M") + " " + start.strftime("%p")

    values = "?, " + "?, " * len(ids) + "NULL, " * (8 - len(ids)) + "?, ?, ?, NULL, ?"
    values1 = [str(p) for p in team1] + [str(p) for p in team2] + ["won", "lost"] + [int(time)] + [time_data2[0] + " " + time_data2[1] + " " + time_data2[2]]
    values2 = [str(p) for p in team1] + [str(p) for p in team2] + ["lost", "won"] + [int(time)] + [time_data2[0] + " " + time_data2[1] + " " + time_data2[2]]

    game_type = f"{len(team1)}v{len(team1)}"

    for result in results:
        
        if result == 1:
            c.execute(f"INSERT INTO {games_table} VALUES({values})", [str(game_id)] + values1)
            player_won = player1
            player_lost = player2
        else:
            c.execute(f"INSERT INTO {games_table} VALUES({values})", [str(game_id)] + values2)
            player_won = player2
            player_lost = player1
        

        c.execute(f"SELECT elo, sigma, win, loss FROM {players_table} where ID = ?", [str(player_won)])
        row = c.fetchone()
        elo1 = row[0]
        sigma1 = row[1]
        total_games1 = row[2] + row[3]

        c.execute(f"SELECT elo, sigma, win, loss FROM {players_table} where ID = ?", [str(player_lost)])
        row = c.fetchone()
        elo2 = row[0]
        sigma2 = row[1]
        total_games2 = row[2] + row[3]


        if (total_games1 < 20 and total_games2 < 20) or (total_games1 >= 20 and total_games2 >= 20):
            player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, sigma2))
            elo1 = player_won_rating.mu
            sigma1 = player_won_rating.sigma
            elo2 = player_lost_rating.mu
            sigma2 = player_lost_rating.sigma
        elif total_games1 < 20:
            player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, 30))
            elo1 = player_won_rating.mu
            sigma1 = player_won_rating.sigma
            elo2 = player_lost_rating.mu
        else:
            player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, 30), trueskill.Rating(elo2, sigma2))
            elo1 = player_won_rating.mu
            elo2 = player_lost_rating.mu
            sigma2 = player_lost_rating.sigma


        c.execute(f"UPDATE {players_table} SET win = win + 1 where ID = ?", [str(player_won)])
        c.execute(f"UPDATE {players_table} SET streak = streak + 1 WHERE ID = ?", [str(player_won)])
        c.execute(f"UPDATE {players_table} SET elo = ? where ID = ?", [elo1, str(player_won)])
        c.execute(f"UPDATE {players_table} SET sigma = ? where ID = ?", [sigma1, str(player_won)])

        c.execute(f"UPDATE {players_table} SET loss = loss + 1 where ID = ?", [str(player_lost)])
        c.execute(f"UPDATE {players_table} SET streak = 0 WHERE ID = ?", [str(player_lost)])
        c.execute(f"UPDATE {players_table} SET elo = ? where ID = ?", [elo2, str(player_lost)])
        c.execute(f"UPDATE {players_table} SET sigma = ? where ID = ?", [sigma2, str(player_lost)])

        conn.commit()
        #conn.close()
        #del global_dict[game_id]

        await activity_channel.send(f"[{game_type}] Game #" + str(game_id) + " has finished.")
        await ctx.channel.send(f"[{game_type}] Game #" + str(game_id) + " has finished.")
        game_id += 1

    await leaderboard_solo(ctx)
    
    conn.close()

@client.command()
async def simulate(ctx, *args):
    record_info = " ".join(args)
    # !simulate Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2] 
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2]")
        # print fail, give !record Team1 - [@player1, @player2], Team2 - [@player3, @player4], Results - [1,2,1,2,2,2] as working example
        return
    
    team_won_ratings = []
    team_lost_ratings = []
    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end)
    result_end = record_info.find("]", result_start) + 1
    results = [int(k) for k in eval(record_info[result_start:result_end])]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
        # print fail, results is a list showing the order of wins for each team (for example, [1,2,1] means team 1 won, then team 2 won then team 1 won again)
        return

    ids = []
    i = 0
    team1 = []
    while i < len(team1_str):
        c = team1_str[i]
        if c == "<":
            player_id = ""
            i += 3 # <@!361548991755976704>
            c = team1_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = team1_str[i]
            team1.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(team1) == 0:
        # print fail, team 1 empty
        await ctx.send("Team 1 empty.")
        return

    i = 0
    team2 = []
    while i < len(team2_str):
        c = team2_str[i]
        if c == "<":
            player_id = ""
            i += 3
            c = team2_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = team2_str[i]
            team2.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(team2) == 0:
        await ctx.send("Team 2 empty.")
        # print fail, team 2 empty
        return
    
    if len(team1) != len(team2):
        # print unbalanced teams
        await ctx.send("Unbalanced teams.")
        return
        
    activity_channel = ctx.guild.get_channel(790313358816968715)
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    auth = ctx.message.author.id

    games_table = "games"
    players_table = "players"

    if len(team1) > 1:
        games_table += "_team"
        players_table += "_team"

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 1
    else:
        game_id = int(game_id) + 1

    start = datetime.datetime.now()
    time = start.strftime("%M")
    time_data2 = start.strftime("%B"),start.strftime("%d") + ", " + start.strftime("%Y"), start.strftime("%I") + ":" + start.strftime("%M") + " " + start.strftime("%p")

    values = "?, " + "?, " * len(ids) + "NULL, " * (8 - len(ids)) + "?, ?, ?, NULL, ?"
    values1 = [str(p) for p in team1] + [str(p) for p in team2] + ["won", "lost"] + [int(time)] + [time_data2[0] + " " + time_data2[1] + " " + time_data2[2]]
    values2 = [str(p) for p in team1] + [str(p) for p in team2] + ["lost", "won"] + [int(time)] + [time_data2[0] + " " + time_data2[1] + " " + time_data2[2]]

    game_type = f"{len(team1)}v{len(team1)}"

    team_won_ratings = []
    for t in team1:
        c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(t)])
        row = c.fetchone()
        elo = row[0]
        sigma = row[1]
        team_won_ratings.append(trueskill.Rating(elo, sigma))
    
    team_lost_ratings = []
    for t in team2:
        c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(t)])
        row = c.fetchone()
        elo = row[0]
        sigma = row[1]
        team_lost_ratings.append(trueskill.Rating(elo, sigma))

    last_result = 1
    for result in results:
        
        if result != last_result:
            last_result = result
            team_won_ratings, team_lost_ratings = team_lost_ratings, team_won_ratings

        team_won_ratings, team_lost_ratings = trueskill.rate([team_won_ratings, team_lost_ratings])

    if last_result != 1:
        team_won_ratings, team_lost_ratings = team_lost_ratings, team_won_ratings
    
    s = "Simulated Elos:\n"
    for i, t in enumerate(team1):
        s += f"<@!{t}>: {team_won_ratings[i].mu:.2f}\n"
    for i, t in enumerate(team2):
        s += f"<@!{t}>: {team_lost_ratings[i].mu:.2f}\n"

    await ctx.send(s)

    conn.close()

# client.run("XXXxX")