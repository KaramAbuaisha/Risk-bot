import argparse
import sqlite3
import numpy as np
import trueskill
import re
import requests
import json

from collections import defaultdict, deque
from copy import deepcopy

import discord
from discord.ext.commands import bot
from discord.ext import commands

# Discord Client
client = discord.Client()
bot_prefix = "!"
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=bot_prefix, intents=intents)

ones_channel = discord.Object(790313550270693396)
teams_channel = discord.Object(790313583484731422)
db_path = "risk.db"
db_path_old = "risk_old_clean.db"


BETA=200

main_elo = trueskill.TrueSkill(mu=1350, draw_probability=0, backend="mpmath", sigma=175, tau=6, beta=BETA)
main_elo.make_as_global()

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

def get_win_probability(elo1, sigma1, elo2, sigma2):
    deltaMu = elo1 - elo2
    sumSigma = sigma1**2 + sigma2**2
    rsss = np.sqrt(2* (BETA**2) + sumSigma)
    return cdf(deltaMu/rsss)
    
def safeName(name):
    """Changes player's names that will mess up the discord leaderboard formatting to Shitname"""
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
    players_table = "players"
    if ctx.channel.id == teams_channel.id:
        players_table += "_team"

    if len(name) == 0:
        # Tried without an input
        out = ctx.message.author.id
    else:
        # Test to see if it's a ping
        server = ctx.message.guild
        if name[0:2] == "<@":
            if name[2] == "!":
                player = ctx.guild.get_member(int(name[3:-1]))
            else:
                player = ctx.guild.get_member(int(name[2:-1]))
            if player is not None:
                out = player.id
        else:
            # Test to see if it's a username
            # player = server.get_member_named(name)
            # if player is not None:
            #     out = player.id
            # else:
            # Check the database to see if it's a username
            c.execute(f"SELECT ID FROM {players_table} WHERE name LIKE ?", [name])
            result = c.fetchone()
            if result is not None:
                out = result[0]
            else:
                # Check the database to see if it's LIKE a username
                wildcard_name = name + "%"
                c.execute(f"SELECT ID FROM {players_table} WHERE name LIKE ?", [wildcard_name])
                result = c.fetchone()
                if result is not None:
                    out = result[0]
    conn.commit()
    conn.close()
    if out is not None:
        return int(out)
    else:
        return None

def find_userid_by_name_old(ctx, name):

    db_path = db_path_old
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    out = None
    players_table = "players"
    if ctx.channel.id == teams_channel.id:
        players_table += "_team"

    if len(name) == 0:
        # Tried without an input
        out = ctx.message.author.id
    else:
        # Test to see if it's a ping
        server = ctx.message.guild
        if name[0:2] == "<@":
            if name[2] == "!":
                player = ctx.guild.get_member(int(name[3:-1]))
            else:
                player = ctx.guild.get_member(int(name[2:-1]))
            if player is not None:
                out = player.id
        else:
            # Test to see if it's a username
            # player = server.get_member_named(name)
            # if player is not None:
            #     out = player.id
            # else:
            # Check the database to see if it's a username
            c.execute(f"SELECT ID FROM {players_table} WHERE name LIKE ?", [name])
            result = c.fetchone()
            if result is not None:
                out = result[0]
            else:
                # Check the database to see if it's LIKE a username
                wildcard_name = name + "%"
                c.execute(f"SELECT ID FROM {players_table} WHERE name LIKE ?", [wildcard_name])
                result = c.fetchone()
                if result is not None:
                    out = result[0]
    conn.commit()
    conn.close()
    if out is not None:
        return int(out)
    else:
        return None


@client.event
async def on_ready():
    print("Bot has now logged on")

async def leaderboard_team(ctx):
    """ Updates the leaderboard channel """

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = ctx.guild
    leaderboard_channel = discord.utils.get(guild.channels, id=787070684106194954)

    await leaderboard_channel.purge(limit=15)

    msg = "```\n"
    msg += "{:<4}  {:<25}  {:<10} {:<10} {:<10}".format('RANK', 'NAME', 'ELO', 'SIGMA', 'TOTAL GAMES') + "" + "\n"

    for i, player in enumerate(c.execute("""SELECT name, win, loss, elo, peak_elo, id, sigma 
                                            FROM players_team
                                            WHERE win + loss > 0
                                            ORDER BY elo desc""").fetchall()):

        name, win, loss, elo, peak_elo, player_id, sigma  = player
        player_id = int(player_id)
        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        # name = safeName(name[:20])
        rank = i + 1
        total_games = win + loss

        c.execute("UPDATE players_team SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        if elo > peak_elo:
            c.execute("UPDATE players_team SET peak_elo = ? where ID = ?", [elo, player_id])
            conn.commit()

        msg += "{:<4}  {:<25}  {:<10}  {:<10}  {:<10}".format(f"#{rank}", name, f"{elo:.0f}", f"{sigma:.0f}", total_games) + "\n"
        
        if rank % 25 == 0:
            await leaderboard_channel.send(msg + '```')
            msg = "```\n"
    
    msg += "```"

    role = discord.utils.get(ctx.guild.roles, name="Rank 1 Team")
    if role:
        for member in role.members:
            await member.remove_roles(role)

    try:
        c.execute("SELECT MAX(ELO), ID from players_team")
        player = int(c.fetchone()[1])
        member = guild.get_member(player)
        await member.add_roles(role)
    except Exception as e:
        # print(e)
        pass

    conn.commit()
    conn.close()
    await leaderboard_channel.send(msg)

async def leaderboard_solo(ctx):
    """ Updates the leaderboard channel """

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = ctx.guild

    leaderboard_channel = discord.utils.get(guild.channels, id=787070644427948142)

    await leaderboard_channel.purge(limit=15)

    msg = "```\n"
    msg += "{:<4}  {:<25}  {:<10}  {:<10}  {:<12}  {:<13}".format('RANK', 'NAME', 'ELO', 'SIGMA', 'TOTAL GAMES', 'LAST PLAYED') + "" + "\n"

    prev_role_assignment = defaultdict(set)
    for role_name in ["Grandmaster", "Master", "Expert", "Diamond", "Platinum", "Gold", "Silver", "Bronze"]:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        for member in role.members:
            prev_role_assignment[role_name].add(member.id)
            # await member.remove_roles(role)
        
        curr_role_assignment = defaultdict(set)

    rank = 0
    games_required = 20
    num_days = 20
    for i, player in enumerate(c.execute("""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time)
                                              FROM players 
                                             WHERE win + loss > 9
                                             AND strftime('%s', 'now') - last_played_time < 86400 * 14
                                             ORDER BY elo desc""").fetchall()):

    # for i, player in enumerate(c.execute(f"""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time) as seconds_ago
    #                                             FROM players 
    #                                             WHERE id in (SELECT p
    #                                                         FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
    #                                                             left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
    #                                                             USING(p)
    #                                                             UNION ALL
    #                                                             SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
    #                                                             left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
    #                                                             USING(p)
    #                                                             WHERE tbl1.p is NULL)
    #                                                         WHERE num > {games_required-1})
    #                                             ORDER BY elo desc""").fetchall()):

        name, win, loss, elo, peak_elo, player_id, sigma, seconds_ago  = player
        player_id = int(player_id)
        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        # name = safeName(name[:20])
        rank += 1
        total_games = win + loss
        # member = guild.get_member(player[5])

        # if member is not None:
        #     if member.nick is not None:
        #         name = member.nick
        #     else:
        #         name = member.name
        # else:
        #     name = player[0]

        c.execute("UPDATE players SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        member = guild.get_member(player_id)
        if member is not None and rank >= 1 and rank <= 28:
            if rank == 1:
                role_name = "Grandmaster"
            elif rank <= 4:
                role_name = "Master"
            # elif rank <= 8:
            #     role_name = "Diamond"
            # elif rank <= 12:
            #     role_name = "Platinum"
            # elif rank <= 16:
            #     role_name = "Gold"
            # elif rank <= 20:
            #     role_name = "Silver"
            # else:
            #     role_name = "Bronze"            
            elif rank <= 8:
                role_name = "Expert"
            elif rank <= 12:
                role_name = "Diamond"
            elif rank <= 16:
                role_name = "Platinum"
            elif rank <= 20:
                role_name = "Gold"
            elif rank <= 24:
                role_name = "Silver"
            else:
                role_name = "Bronze"
            
            curr_role_assignment[role_name].add(member.id)
            if member.id not in prev_role_assignment[role_name]:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                await member.add_roles(role)
        
        if elo > peak_elo:
            c.execute("UPDATE players SET peak_elo = ? where ID = ?", [elo, player_id])
            conn.commit()

        if seconds_ago < 86400:
            tmp = "In the last 24 hrs"
        else:
            tmp = f"In the last {seconds_ago//86400 + 1} days"

        msg += "{:<4}  {:<25}  {:<10}  {:<10}  {:<12}  {:<13}".format(f"#{rank}", name, f"{elo:.0f}", f"{sigma:.0f}", total_games, tmp) + "\n"
        if rank % 15 == 0:
            await leaderboard_channel.send(msg + '```')
            msg = "```\n"

    # if not rank % 15 == 0:
    #     await leaderboard_channel.send(msg + '```')
    #     msg = "```\n"

    msg += "-"*44 + "INACTIVE" + "-"*44 + "\n"

    for i, player in enumerate(c.execute("""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time)
                                              FROM players 
                                             WHERE win + loss > 9
                                             AND strftime('%s', 'now') - last_played_time >= 86400 * 14
                                             ORDER BY elo desc""").fetchall()):

    # for i, player in enumerate(c.execute(f"""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time) as seconds_ago
    #                                             FROM players 
    #                                             WHERE NOT id in (SELECT p
    #                                                         FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
    #                                                             left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
    #                                                             USING(p)
    #                                                             UNION ALL
    #                                                             SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
    #                                                             left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
    #                                                             USING(p)
    #                                                             WHERE tbl1.p is NULL)
    #                                                         WHERE num > {games_required-1})
    #                                             ORDER BY elo desc""").fetchall()):

        name, win, loss, elo, peak_elo, player_id, sigma, seconds_ago  = player
        player_id = int(player_id)
        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        rank += 1
        total_games = win + loss

        c.execute("UPDATE players SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        tmp = f"In the last {seconds_ago//86400 + 1} days"

        msg += "{:<4}  {:<25}  {:<10}  {:<10}  {:<12}  {:<13}".format(f"#{rank}", name, f"{elo:.0f}", f"{sigma:.0f}", total_games, tmp) + "\n"
        if rank % 15 == 0:
            await leaderboard_channel.send(msg + '```')
            msg = "```\n"

    for role_name in ["Grandmaster", "Master", "Expert", "Diamond", "Platinum", "Gold", "Silver", "Bronze"]:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        for member_id in prev_role_assignment[role_name]:
            if member_id not in curr_role_assignment[role_name]:
                member = guild.get_member(member_id)
                await member.remove_roles(role)

    # c.execute("SELECT MAX(ELO), ID from players WHERE win + loss > 19")
    # player = c.fetchone()[1]
    # member = guild.get_member(player)
    # role = discord.utils.get(ctx.guild.roles, name="Rank 1 Solo")
    # await role.members[0].remove_roles(role)
    # await member.add_roles(role)
    msg += "```"
    conn.commit()
    conn.close()
    await leaderboard_channel.send(msg)

@client.command()
@commands.has_any_role('League Admin')
async def register(ctx, member: discord.Member):
    '''Registers a user into the player database.'''

        
    conn = sqlite3.connect(db_path)

    c = conn.cursor()

    if ctx.channel.id == teams_channel.id:
        c.execute("SELECT elo FROM players_team WHERE ID = ?", [member.id])
        row = c.fetchone()
        if row == None:
            c.execute("INSERT INTO players_team VALUES(?, ?, 1500, 400, 0, 0, 1500, strftime('%s', 'now'), 0, NULL)",
                    [member.id, member.name])
            await ctx.send(f"Registered {member.name}.")
        else: 
            await ctx.send("User is already registered.")
    else:
        c.execute("SELECT elo FROM players WHERE ID = ?", [member.id])
        row = c.fetchone()
        if row == None:
            c.execute("INSERT INTO players VALUES(?, ?, 1500, 400, 0, 0, 1500, strftime('%s', 'now'), 0, NULL, 0)",
                    [member.id, member.name])
            role = discord.utils.get(ctx.guild.roles, name="1v1 League")
            await member.add_roles(role)
            await ctx.send(f"Registered {member.name}.")
        else: 
            await ctx.send("User is already registered.")
        conn.commit()

# TODO:
# @client.command()
# @commands.has_any_role('League Admin')
# async def unregister(ctx):
#     """Unregister user."""
#     await ctx.send("User unregistered.")

@client.command()
@commands.has_any_role('League Admin')
async def search(ctx, gn):
    """Searches through Warcraft III gamelist."""
    
    result = requests.get('https://api.wc3stats.com/gamelist')

    gamelist = result.json()
    
    games = []
    for game in gamelist['body']:
        if re.search(gn, game['name'], re.IGNORECASE):
            slots_taken = game['slotsTaken']
            slots_total = game['slotsTotal']
            emb = (discord.Embed(description='**Server:** [' + game['server'] + '] /n **Game Name:** ' + game['name'] + '/n **Slots:** (' + str(slots_taken) + '/' + str(slots_total) + ')' '/n **Host:** [' + game['host'] + ']', colour=0x3DF27))
            games.append('[' + game['server'] + '] ' + game['name'] + ' (' + str(slots_taken) + '/' + str(slots_total) + ')' ' [' + game['host'] + ']')

    if len(games) <= 0:
            await ctx.send("No games found.")

    else:
        for game in games:
            await ctx.send(game)

@client.command()
async def peak(ctx, name=None):
    '''Show's the highest ELO reached by a player.'''

    players_table = "players"
    if ctx.channel.id == teams_channel.id:
        players_table += "_team"

    if name is None:
        player_id = ctx.author.id
    else:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name.")
            return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    c.execute(f"SELECT name, peak_elo FROM {players_table} WHERE ID = ?", [player_id])
    try:
        user = c.fetchone()
        name = user[0]
        peak_elo = user[1]
        await ctx.send(f"**{name}** had an elo peak of **{peak_elo:.1f}**.")
    except:
        await ctx.send(f"{name} is not registered.")

@client.command()
@commands.has_any_role('League Admin')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int, channel:discord.TextChannel=None):
    """Deletes messages in channel. !purge 3 deletes last 3 messages in current channel. !purge 3 #bot-spam deletes last 3 messages in #bot-spam."""

    if channel is None or channel == ctx.channel:
        await ctx.channel.purge(limit=limit+1)
    else:
        await channel.purge(limit=limit)

@client.command()
async def stats_old(ctx, name=None):
    '''Shows a players old statistics.'''

    db_path = db_path_old

    teams = False
    players_table = "players"

    if ctx.channel.id == teams_channel.id:
        teams = True
        players_table += "_team"
        
    if name is None:
        player_id = ctx.author.id
    else:
        player_id = find_userid_by_name_old(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name.")
            return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    c.execute(f"SELECT name, elo, sigma, win, loss, streak, peak_elo, rank FROM {players_table} where ID = ?", [player_id])
    player = c.fetchone()

    if player is not None:
        name, elo, sigma, win, loss, streak, peak_elo, rank = player
        total_games = win + loss
        
        grandmaster = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grandmaster.png"
        master = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/master.png"
        expert = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/adept.png"
        diamond = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/diamond.png"
        platinum = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/platinum.png"
        gold = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/gold.png"
        silver = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/silver.png"
        bronze = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/bronze.png"
        grass = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grass.png"

        if rank is None:
            url = grass
            emoji = "<:grass:821047027638992966>"
        elif rank == 1:
            url = grandmaster
            emoji = "<:grandmaster:821047027257311234>"
        elif rank <= 4:
            url = master
            emoji = "<:master:821047027412631603>"
        # elif rank <= 8:
        #     url = diamond
        #     emoji = "<:diamond:821047028237860924>"
        # elif rank <= 12:
        #     url = platinum
        #     emoji = "<:platinum:821047027584467004>"
        # elif rank <= 16:
        #     url = gold
        #     emoji = "<:gold:821047027675955200>"
        # elif rank <= 20:
        #     url = silver
        #     emoji = "<:silver:821047027374751806>"
        # else:
        #     url = bronze
        #     emoji = "<:bronze:821047027575422996>"
        elif rank <= 8:
            url = expert
            emoji = "<:expert:821047027391660094>"
        elif rank <= 12:
            url = diamond
            emoji = "<:diamond:821047028237860924>"
        elif rank <= 16:
            url = platinum
            emoji = "<:platinum:821047027584467004>"
        elif rank <= 20:
            url = gold
            emoji = "<:gold:821047027675955200>"
        elif rank <= 24:
            url = silver
            emoji = "<:silver:821047027374751806>"
        else:
            url = bronze
            emoji = "<:bronze:821047027575422996>"
        # else:
        #     url = grass
        #     emoji = "<:grass:821047027638992966>"

        # for emoji in ctx.guild.emojis:
        #     print(f"<:{emoji.name}:{emoji.id}>")

        if total_games == 0:
            await ctx.send(f"{name} played no games and has an elo of **{elo:.1f}**.")
        else:
            recent_perf = []
            if teams:
                c.execute("""SELECT p1,p2,p3,p4,p5,p6,p7,p8,id,s1,s2 
                               FROM games_team 
                              WHERE (p1 == ? OR p2 == ? or p3 == ? or p4 == ? or p5 == ? or p6 == ? or p7 == ? or p8 == ?) 
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""", [player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id])
                recent_games = c.fetchall()

                for items in recent_games:
                    if items[7] is not None:
                        team = 1 if player_id in items[0:4] else 2
                    elif items[5] is not None:
                        team = 1 if player_id in items[0:3] else 2
                    else:
                        team = 1 if player_id in items[0:2] else 2
                    s1 = items[9]
                    s2 = items[10]
                    if team == 1:
                        if s1 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")                
                    else:
                        if s2 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")
                
            else:
                c.execute("""SELECT p1,p2,id,s1,s2 
                               FROM games 
                              WHERE (p1 == ? OR p2 == ?) 
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""", [player_id,player_id])
                recent_games = c.fetchall()

                for items in recent_games:
                    if player_id == items[0]:
                        team = 1
                    else:
                        team = 2
                    s1 = items[3]
                    s2 = items[4]
                    if team == 1:
                        if s1 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")       
                    else:
                        if s2 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")

            rp = "-".join(recent_perf)[::-1]
        
            embed = discord.Embed(
                colour=0x1F1E1E
            )
            embed.set_thumbnail(url=f"{url}")
            embed.add_field(name=f"{name} {emoji}\n\u200b",
                            value=f"Rank: **{rank if rank else 'Unranked'}** | **{win}**W - **{loss}**L (**{(win / total_games) * 100:.1f}% Win Rate**)\n\nRecent Performance:\n{rp}",
                            inline=False)
            embed.add_field(name='\n\u200b', value=f'Elo: **{elo:.1f}**')
            embed.add_field(name='\n\u200b', value=f'Sigma: **{sigma:.1f}**')
            embed.add_field(name='\n\u200b', value=f'Streak: **{streak}**')
            await ctx.send(embed=embed)
    else:
        await ctx.send("No user found by that name!")

    conn.commit()
    conn.close()

@client.command()
async def stats(ctx, name=None):
    '''Shows a players statistics.'''


    teams = False
    players_table = "players"

    if ctx.channel.id == teams_channel.id:
        teams = True
        players_table += "_team"
        
    if name is None:
        player_id = ctx.author.id
    else:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name.")
            return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    c.execute(f"SELECT name, elo, sigma, win, loss, streak, peak_elo, rank FROM {players_table} where ID = ?", [player_id])
    player = c.fetchone()

    if player is not None:
        name, elo, sigma, win, loss, streak, peak_elo, rank = player
        total_games = win + loss
        
        grandmaster = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grandmaster.png"
        master = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/master.png"
        expert = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/adept.png"
        diamond = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/diamond.png"
        platinum = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/platinum.png"
        gold = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/gold.png"
        silver = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/silver.png"
        bronze = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/bronze.png"
        grass = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grass.png"

        if rank is None:
            url = grass
            emoji = "<:grass:821047027638992966>"
        elif rank == 1:
            url = grandmaster
            emoji = "<:grandmaster:821047027257311234>"
        elif rank <= 4:
            url = master
            emoji = "<:master:821047027412631603>"
        # elif rank <= 8:
        #     url = diamond
        #     emoji = "<:diamond:821047028237860924>"
        # elif rank <= 12:
        #     url = platinum
        #     emoji = "<:platinum:821047027584467004>"
        # elif rank <= 16:
        #     url = gold
        #     emoji = "<:gold:821047027675955200>"
        # elif rank <= 20:
        #     url = silver
        #     emoji = "<:silver:821047027374751806>"
        # else:
        #     url = bronze
        #     emoji = "<:bronze:821047027575422996>"
        elif rank <= 8:
            url = expert
            emoji = "<:expert:821047027391660094>"
        elif rank <= 12:
            url = diamond
            emoji = "<:diamond:821047028237860924>"
        elif rank <= 16:
            url = platinum
            emoji = "<:platinum:821047027584467004>"
        elif rank <= 20:
            url = gold
            emoji = "<:gold:821047027675955200>"
        elif rank <= 24:
            url = silver
            emoji = "<:silver:821047027374751806>"
        else:
            url = bronze
            emoji = "<:bronze:821047027575422996>"
        # else:
        #     url = grass
        #     emoji = "<:grass:821047027638992966>"

        # for emoji in ctx.guild.emojis:
        #     print(f"<:{emoji.name}:{emoji.id}>")

        if total_games == 0:
            await ctx.send(f"{name} played no games and has an elo of **{elo:.1f}**.")
        else:
            recent_perf = []
            if teams:
                c.execute("""SELECT p1,p2,p3,p4,p5,p6,p7,p8,id,s1,s2 
                               FROM games_team 
                              WHERE (p1 == ? OR p2 == ? or p3 == ? or p4 == ? or p5 == ? or p6 == ? or p7 == ? or p8 == ?) 
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""", [player_id, player_id, player_id, player_id, player_id, player_id, player_id, player_id])
                recent_games = c.fetchall()

                for items in recent_games:
                    if items[7] is not None:
                        team = 1 if player_id in items[0:4] else 2
                    elif items[5] is not None:
                        team = 1 if player_id in items[0:3] else 2
                    else:
                        team = 1 if player_id in items[0:2] else 2
                    s1 = items[9]
                    s2 = items[10]
                    if team == 1:
                        if s1 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")                
                    else:
                        if s2 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")
                
            else:
                c.execute("""SELECT p1,p2,id,s1,s2 
                               FROM games 
                              WHERE (p1 == ? OR p2 == ?) 
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""", [player_id,player_id])
                recent_games = c.fetchall()

                for items in recent_games:
                    if player_id == items[0]:
                        team = 1
                    else:
                        team = 2
                    s1 = items[3]
                    s2 = items[4]
                    if team == 1:
                        if s1 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")       
                    else:
                        if s2 == "won":
                            recent_perf.append("W")
                        else:
                            recent_perf.append("L")

            rp = "-".join(recent_perf)[::-1]
        
            embed = discord.Embed(
                colour=0x1F1E1E
            )
            embed.set_thumbnail(url=f"{url}")
            embed.add_field(name=f"{name} {emoji}\n\u200b",
                            value=f"Rank: **{rank if rank else 'Unranked'}** | **{win}**W - **{loss}**L (**{(win / total_games) * 100:.1f}% Win Rate**)\n\nRecent Performance:\n{rp}",
                            inline=False)
            embed.add_field(name='\n\u200b', value=f'Elo: **{elo:.1f}**')
            embed.add_field(name='\n\u200b', value=f'Sigma: **{sigma:.1f}**')
            embed.add_field(name='\n\u200b', value=f'Streak: **{streak}**')
            await ctx.send(embed=embed)
    else:
        await ctx.send("No user found by that name!")

    conn.commit()
    conn.close()

@client.command()
@commands.cooldown(3, 5, commands.BucketType.user)
async def compare_old(ctx, p1, p2):

    """Compares two users old statistics.""" 

    db_path = db_path_old

    if ctx.channel.id == ones_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        
        t1 = find_userid_by_name_old(ctx, p1)
        if t1 is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = float(result[1])
        sigma1 = float(result[2])
        

        t2 = find_userid_by_name_old(ctx, p2)
        if t2 is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        name2 = result[0]
        elo2 = float(result[1])
        sigma2 = float(result[2])
        
        wins = 0
        losses = 0
        
        wins_q = list()
        losses_q = list()

        c.execute("SELECT ID, s1 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC", [t1, t2])
        game = c.fetchone()
        while game is not None:
            i, result = game
            # print(i, result)
            if result == "won":
                wins += 1
                wins_q.append(i)
            elif result == "lost":
                losses += 1
                losses_q.append(i)
            else:
                # shouldn't happen, maybe error or print to terminal
                pass
            
            game = c.fetchone()
        
        c.execute("SELECT ID, s2 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC", [t2, t1])
        game = c.fetchone()
        while game is not None:
            i, result = game
            if result == "won":
                wins += 1
                wins_q.append(i)
            elif result == "lost":
                losses += 1
                losses_q.append(i)
            else:
                # shouldn't happen, maybe error or print to terminal
                pass
            
            game = c.fetchone()

        wins_q.sort()
        losses_q.sort()

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

        win_probability = get_win_probability(elo1, sigma1, elo2, sigma2)

        if wins + losses > 0:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have played a total of {wins + losses} games together.\n"
            s += f"{name1} has a win rate of {wins/(wins+losses)*100:.2f}% (**{wins}W - {losses}L**) against {name2}.\n"
            if wins + losses > 20:
                i = 0
                wins_20 = 0
                losses_20 = 0
                while wins_q and losses_q and i < 20:
                    # print(wins_q[-1], losses_q[-1])
                    if wins_q[-1] > losses_q[-1]:
                        wins_20 += 1
                        wins_q.pop()
                    else:
                        losses_20 += 1
                        losses_q.pop()
                    i += 1
                if i < 20:
                    if wins_q:
                        wins_20 += (20-i)
                    else:
                        losses_20 += (20-i)
                s += f"{name1} has a win rate of {wins_20/(wins_20+losses_20)*100:.2f}% (**{wins_20}W - {losses_20}L**) against {name2} in the last 20 games.\n"

        else:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have not played any games together.\n"

        s += f"{name1}'s expected win probability against {name2} is {win_probability*100:.2f}%."
        
        await ctx.send(s)
        conn.commit()
        conn.close()

    if ctx.channel.id == teams_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        x = ctx.author.id
        
        t1 = find_userid_by_name_old(ctx, p1)
        if t1 is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo FROM players_team where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = str(result[1])
        

        t2 = find_userid_by_name_old(ctx, p2)
        if t2 is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo FROM players_team where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
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
        
        
        await ctx.send(str_together + "\n" + str_against)
        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(3, 5, commands.BucketType.user)
async def compare(ctx, p1, p2):

    """Compares two users statistics.""" 


    if ctx.channel.id == ones_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        x = ctx.author.id
        
        t1 = find_userid_by_name(ctx, p1)
        if t1 is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = float(result[1])
        sigma1 = float(result[2])
        

        t2 = find_userid_by_name(ctx, p2)
        if t2 is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        name2 = result[0]
        elo2 = float(result[1])
        sigma2 = float(result[2])
        
        wins = 0
        losses = 0
        
        wins_q = list()
        losses_q = list()

        c.execute("SELECT ID, s1 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC", [t1, t2])
        game = c.fetchone()
        while game is not None:
            i, result = game
            # print(i, result)
            if result == "won":
                wins += 1
                wins_q.append(i)
            elif result == "lost":
                losses += 1
                losses_q.append(i)
            else:
                # shouldn't happen, maybe error or print to terminal
                pass
            
            game = c.fetchone()
        
        c.execute("SELECT ID, s2 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC", [t2, t1])
        game = c.fetchone()
        while game is not None:
            i, result = game
            if result == "won":
                wins += 1
                wins_q.append(i)
            elif result == "lost":
                losses += 1
                losses_q.append(i)
            else:
                # shouldn't happen, maybe error or print to terminal
                pass
            
            game = c.fetchone()

        wins_q.sort()
        losses_q.sort()

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

        win_probability = get_win_probability(elo1, sigma1, elo2, sigma2)

        def get_x(x):
            wins_q_tmp = deepcopy(wins_q)
            losses_q_tmp = deepcopy(losses_q)
            if wins + losses > x:
                i = 0
                wins_x = 0
                losses_x = 0
                while wins_q_tmp and losses_q_tmp and i < x:
                    # print(wins_q_tmp[-1], losses_q_tmp[-1])
                    if wins_q_tmp[-1] > losses_q_tmp[-1]:
                        wins_x += 1
                        wins_q_tmp.pop()
                    else:
                        losses_x += 1
                        losses_q_tmp.pop()
                    i += 1
                if i < x:
                    if wins_q_tmp:
                        wins_x += (x-i)
                    else:
                        losses_x += (x-i)
                return f"{name1} has a win rate of {wins_x/(wins_x+losses_x)*100:.2f}% (**{wins_x}W - {losses_x}L**) against {name2} in the last {x} games.\n"
            else:
                return ""


        if wins + losses > 0:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have played a total of {wins + losses} games together.\n"
            s += f"{name1} has a win rate of {wins/(wins+losses)*100:.2f}% (**{wins}W - {losses}L**) against {name2}.\n"
            s += get_x(20)
            # s += get_x(30)
            # s += get_x(40)
            s += get_x(50)
        else:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have not played any games together.\n"

        s += f"{name1}'s expected win probability against {name2} is {win_probability*100:.2f}%."
        
        await ctx.send(s)
        conn.commit()
        conn.close()

    if ctx.channel.id == teams_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        x = ctx.author.id
        
        t1 = find_userid_by_name(ctx, p1)
        if t1 is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo FROM players_team where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p1 + "\"!")
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = str(result[1])
        

        t2 = find_userid_by_name(ctx, p2)
        if t2 is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
            conn.commit()
            conn.close()
            return
        
        c.execute("SELECT name, elo FROM players_team where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.send("No user found by the name \"" + p2 + "\"!")
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
        
        
        await ctx.send(str_together + "\n" + str_against)
        conn.commit()
        conn.close()


@client.command()
@commands.has_any_role('League Admin')
async def set_elo(ctx, name, new_val):
    '''Adjusts a players ELO.'''

    
    new_val = int(new_val)

    if ctx.channel.id == teams_channel.id:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, elo FROM players_team WHERE ID = ?", [player_id])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players_team SET elo = ? WHERE ID = ?",
                      [new_val, player_id])

            out = f"{ctx.message.author.name} has set {name}'s Elo to **{new_val}**!"
            activity_channel = client.get_channel(790313358816968715)
            await ctx.send(out)
            await activity_channel.send(out)
            conn.commit()
            await leaderboard_team(ctx)
        conn.close()
    else:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, elo FROM players WHERE ID = ?", [player_id])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players SET elo = ? WHERE ID = ?",
                      [new_val, player_id])

            out = f"{ctx.message.author.name} has set {name}'s Elo to **{new_val}**!"
            activity_channel = client.get_channel(790313358816968715)
            await ctx.send(out)
            await activity_channel.send(out)
            conn.commit()
            await leaderboard_solo(ctx)
        conn.close()


@client.command()
@commands.has_any_role('League Admin')
async def set_sigma(ctx, name, new_val):
    '''Adjusts a players Sigma.'''


    new_val = int(new_val)

    if ctx.channel.id == ones_channel.id:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, sigma FROM players WHERE ID = ?", [player_id])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players SET sigma = ? WHERE ID = ?",
                      [new_val, player_id])


            out = f"{ctx.message.author.name} has set {name}'s Sigma to **{new_val}**!"

            activity_channel = client.get_channel(790313358816968715)
            await ctx.send(out)
            await activity_channel.send(out)
        conn.commit()
        conn.close()

    if ctx.channel.id == teams_channel.id:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name!")
            return

        # user = find_user_by_name(ctx, name)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name, sigma FROM players_team WHERE ID = ?", [player_id])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            c.execute("UPDATE players_team SET sigma = ? WHERE ID = ?",
                      [new_val, player_id])

            out = f"{ctx.message.author.name} has set {name}'s Sigma to **{new_val}**!"
            activity_channel = client.get_channel(790313358816968715)
            await ctx.send(out)
            await activity_channel.send(out)
        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def update_leaderboards(ctx):
    """ Manually updates the leaderboard."""

    if ctx.channel.id == ones_channel.id or ctx.channel.id == teams_channel.id:

        await leaderboard_solo(ctx)
        await leaderboard_team(ctx)
        t = ctx.message.author.name
        activity_channel = client.get_channel(790313358816968715)
        await ctx.send(str(t) + " has updated the leaderboard.")
        await activity_channel.send(str(t) + " has updated the leaderboard.")


@client.command()
@commands.has_any_role("League Admin")
async def update_nickname(ctx, player: discord.Member, nickname):
    """Updates a players nickname."""

    playerID = player.id
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE players SET name = ? WHERE ID = ?", [nickname, playerID])
    c.execute("UPDATE players_team SET name = ? WHERE ID = ?", [nickname, playerID])
    
    conn.commit()
    conn.close()

    await ctx.send("Nickname updated.")

record_pattern = re.compile(".*\[.*\].*\[.*\].*\[.*\].*", flags=re.IGNORECASE)
results_pattern = re.compile("\[.*\]", flags=re.IGNORECASE)

@client.command()
@commands.has_any_role("League Admin", "TG League Admin")
async def record_team(ctx, *args):
    '''Admin command for recording team games.'''
    record_info = " ".join(args)
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record_team [@player1, @player2] [@player3, @player4] [1,2,1,2,2,2]")
        return
    
    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end) + 1
    result_end = record_info.find("]", result_start) 
    results = [int(k) for k in record_info[result_start:result_end].split(',')]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
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
        return
    
    if len(team1) != len(team2):
        await ctx.send("Unbalanced teams.")
        return
        
    activity_channel = ctx.guild.get_channel(790313358816968715)
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    games_table = "games_team"
    players_table = "players_team"
    game_type = "team game"
        

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 0
    else:
        game_id = int(game_id)

    values = "?, " + ("?, " * len(team1) + "NULL, " * (4 - len(team1)))*2 + "?, ?"
    

    for result in results:

        game_id += 1
        
        if result == 1:
            values1 = [str(game_id)] + [str(p) for p in team1] + [str(p) for p in team2] + ["won", "lost"]
            c.execute(f"INSERT INTO {games_table} VALUES({values})", values1)
            team_won = team1
            team_lost = team2
        else:
            values2 = [str(game_id)] + [str(p) for p in team1] + [str(p) for p in team2] + ["lost", "won"]
            c.execute(f"INSERT INTO {games_table} VALUES({values})", values2)
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
    conn.close()

    if len(results) == 1:
        await activity_channel.send(f"[{game_type}] Game #{game_id} has finished.")
        await ctx.send(f"[{game_type}] Game #{game_id} has finished.")
    else:
        await activity_channel.send(f"[{game_type}] Games #{game_id-len(results)+1}-{game_id} have finished.")
        await ctx.send(f"[{game_type}] Games #{game_id-len(results)+1}-{game_id} have finished.")

    await leaderboard_team(ctx)


@client.command()
@commands.has_any_role("League Admin")
async def record(ctx, *args):
    '''Admin command for recording 1v1s.'''
    record_info = " ".join(args)
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record [@player1] [@player2] [1,2,1,2,2,2] ")
        return
    
    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end) + 1
    result_end = record_info.find("]", result_start) 
    results = [int(k) for k in record_info[result_start:result_end].split(',')]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
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
        return
    if len(team2) > 1:
        await ctx.send("Team 2 has too many players (there should only be 1).")
        return

    activity_channel = ctx.guild.get_channel(790313358816968715)
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    games_table = "games"
    players_table = "players"

    player1 = team1[0]
    player2 = team2[0]
    
    c.execute("SELECT name FROM players WHERE ID = ?", [player1])
    name1 = c.fetchone()[0]

    c.execute("SELECT name FROM players WHERE ID = ?", [player2])
    name2 = c.fetchone()[0]

    await compare(ctx, name1, name2)

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 0
    else:
        game_id = int(game_id)

    for result in results:

        game_id += 1

        if result == 1:
            c.execute(f"INSERT INTO {games_table} VALUES(?, ?, ?, ?, ?, strftime('%s', 'now'))",  [str(game_id), str(player1), str(player2), "won", "lost"])
            player_won = player1
            player_lost = player2
        else:
            c.execute(f"INSERT INTO {games_table} VALUES(?, ?, ?, ?, ?, strftime('%s', 'now'))", [str(game_id), str(player1), str(player2), "lost", "won"])
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

        player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, sigma2))
        elo1 = player_won_rating.mu
        sigma1 = player_won_rating.sigma
        elo2 = player_lost_rating.mu
        sigma2 = player_lost_rating.sigma

        # TODO:
        # if (total_games1 < 20 and total_games2 < 20) or (total_games1 >= 20 and total_games2 >= 20):
        #     player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, sigma2))
        #     elo1 = player_won_rating.mu
        #     sigma1 = player_won_rating.sigma
        #     elo2 = player_lost_rating.mu
        #     sigma2 = player_lost_rating.sigma
        # elif total_games1 < 20:
        #     player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, 30))
        #     elo1 = player_won_rating.mu
        #     sigma1 = player_won_rating.sigma
        #     elo2 = player_lost_rating.mu
        # else:
        #     player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, 30), trueskill.Rating(elo2, sigma2))
        #     elo1 = player_won_rating.mu
        #     elo2 = player_lost_rating.mu
        #     sigma2 = player_lost_rating.sigma

        c.execute(f"UPDATE {players_table} SET win = win + 1 where ID = ?", [str(player_won)])
        c.execute(f"UPDATE {players_table} SET streak = streak + 1 WHERE ID = ?", [str(player_won)])
        c.execute(f"UPDATE {players_table} SET elo = ? where ID = ?", [elo1, str(player_won)])
        c.execute(f"UPDATE {players_table} SET sigma = ? where ID = ?", [sigma1, str(player_won)])

        c.execute(f"UPDATE {players_table} SET loss = loss + 1 where ID = ?", [str(player_lost)])
        c.execute(f"UPDATE {players_table} SET streak = 0 WHERE ID = ?", [str(player_lost)])
        c.execute(f"UPDATE {players_table} SET elo = ? where ID = ?", [elo2, str(player_lost)])
        c.execute(f"UPDATE {players_table} SET sigma = ? where ID = ?", [sigma2, str(player_lost)])

    c.execute(f"UPDATE {players_table} SET last_played_time = strftime('%s', 'now') where ID = ? or ID = ?", [str(player1), str(player2)])
    conn.commit()
    conn.close()

    if len(results) == 1:
        await activity_channel.send(f"[1v1] Game #{game_id} has finished.")
        await ctx.send(f"[1v1] Game #{game_id} has finished.")
    else:
        await activity_channel.send(f"[1v1] Games #{game_id-len(results)+1}-{game_id} have finished.")
        await ctx.send(f"[1v1] Games #{game_id-len(results)+1}-{game_id} have finished.")
    
    await compare(ctx, name1, name2)
    await leaderboard_solo(ctx)

@client.command()
async def simulate(ctx, p1, p2, results_str):
    """Simulate elo after series of games - similar to record except the results are not actually saved. It also does not give the correct results for players with less than 20 games."""
    if not results_pattern.match(results_str):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !simulate player1 player2 [1,2,1,2,2,2]")
        return
    
    # results = [int(k) for k in results_str[1:-1].split(',')]
    try:
        results = eval(results_str)
    except:
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !simulate player1 player2 [1,2,1,2,2,2]")

    # print(results)

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
        return
    
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    t1 = find_userid_by_name_old(ctx, p1)
    if t1 is None:
        await ctx.send("No user found by the name \"" + p1 + "\"!")
        conn.commit()
        conn.close()
        return
    
    c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
    result = c.fetchone()
    if result is None:
        await ctx.send("No user found by the name \"" + p1 + "\"!")
        conn.commit()
        conn.close()
        return

    name1 = result[0]
    elo1 = float(result[1])
    sigma1 = float(result[2])

    player_1_rating = trueskill.Rating(elo1, sigma1)
    

    t2 = find_userid_by_name_old(ctx, p2)
    if t2 is None:
        await ctx.send("No user found by the name \"" + p2 + "\"!")
        conn.commit()
        conn.close()
        return
    
    c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
    result = c.fetchone()
    if result is None:
        await ctx.send("No user found by the name \"" + p2 + "\"!")
        conn.commit()
        conn.close()
        return

    name2 = result[0]
    elo2 = float(result[1])
    sigma2 = float(result[2])

    player_2_rating = trueskill.Rating(elo2, sigma2)

    for result in results:
        if result == 1:
            player_1_rating, player_2_rating = trueskill.rate_1vs1(player_1_rating, player_2_rating)
        else:
            player_2_rating, player_1_rating = trueskill.rate_1vs1(player_2_rating, player_1_rating)
    
    s = "Simulated Elos:\n"
    s += f"{name1}: {player_1_rating.mu:.1f} (sigma={player_1_rating.sigma:.1f})\n"
    s += f"{name2}: {player_2_rating.mu:.1f} (sigma={player_2_rating.sigma:.1f})\n"

    await ctx.send(s)

    conn.close()

@client.command()
async def simulate_team(ctx, *args):
    """Simulate elo after series of games - similar to record_legacy except the results are not actually saved. It also does not give the correct results for players with less than 20 games."""
    record_info = " ".join(args)
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !simulate [@player1, @player2] [@player3, @player4] [1,2,1,2,2,2]")
        return
    
    team_won_ratings = []
    team_lost_ratings = []
    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end) + 1
    result_end = record_info.find("]", result_start) 
    results = [int(k) for k in record_info[result_start:result_end].split(',')]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
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
        return
    
    if len(team1) != len(team2):
        # print unbalanced teams
        await ctx.send("Unbalanced teams.")
        return

    if len(team1) == 1:
        await ctx.send("Teams must have at least 2 players each.")

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    games_table = "games_team"
    players_table = "players_team"

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
        s += f"<@!{t}>: {team_won_ratings[i].mu:.1f}\n"
    for i, t in enumerate(team2):
        s += f"<@!{t}>: {team_lost_ratings[i].mu:.1f}\n"

    await ctx.send(s)

    conn.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run risk bot.')
    parser.add_argument('--token', help='discord token', required=True)
    # parser.add_argument('--SC2', action='store_true', help='run SC2 bot')

    args = parser.parse_args()

    # Channel ID's

    # if args.SC2:
    #     ones_channel = discord.Object(813561724812656710)
    #     teams_channel = discord.Object(813561746388287540)
    #     db_path = "sc2.db"
    # else:
    #     ones_channel = discord.Object(790313550270693396)
    #     teams_channel = discord.Object(790313583484731422)
    #     db_path = "risk_old_clean.db"

    client.run(args.token)
