import argparse
import sqlite3
import numpy as np
import trueskill
import re
import requests
import asyncio

# import json

from collections import defaultdict
from copy import deepcopy

import discord
# from discord.ext.commands import bot
from discord.ext import commands

# Discord Client
client = discord.Client()
bot_prefix = "!"
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=bot_prefix, intents=intents)

def activity_channel():
    return client.get_channel(907464892058075156)

db_path = "risk_teams.db"

BETA=200

main_elo = trueskill.TrueSkill(mu=1500, draw_probability=0, backend="mpmath", sigma=200, tau=6, beta=BETA)
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

def find_userid_by_name(ctx, name):
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    out = None
    players_table = "players"

    if len(name) == 0:
        # Tried without an input
        return None
    else:
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

async def leaderboard():
    """ Updates the leaderboard channel """

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = client.get_guild(383292703955222542)
    leaderboard_channel = discord.utils.get(guild.channels, id=907464938308661298)

    # await leaderboard_channel.purge(limit=15)
    msg_ids = [912772433763770379]
    msg_num = 0

    msg = "```\n"
    msg += "{:<4}  {:<25}  {:<10} {:<10} {:<10}".format('RANK', 'NAME', 'ELO', 'SIGMA', 'TOTAL GAMES') + "" + "\n"

    for i, player in enumerate(c.execute("""SELECT name, win, loss, elo, peak_elo, id, sigma 
                                            FROM players
                                            -- WHERE win + loss > 0
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

        c.execute("UPDATE players SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        if elo > peak_elo:
            c.execute("UPDATE players SET peak_elo = ? where ID = ?", [elo, player_id])
            conn.commit()

        msg += "{:<4}  {:<25}  {:<10}  {:<10}  {:<10}".format(f"#{rank}", name, f"{elo:.0f}", f"{sigma:.0f}", total_games) + "\n"
        
        if rank % 15 == 0:
            # await leaderboard_channel.send(msg + '```')
            if msg_num >= len(msg_ids):
                await leaderboard_channel.send(msg + '```')
            else:
                msg_id = msg_ids[msg_num]
                msg_obj = await leaderboard_channel.fetch_message(msg_id)
                await msg_obj.edit(content=msg + '```')
            msg_num += 1
            msg = "```\n"
    
    if msg != "```\n":
        # await leaderboard_channel.send(msg + '```')
        if msg_num >= len(msg_ids):
            await leaderboard_channel.send(msg + '```')
        else:
            msg_id = msg_ids[msg_num]
            msg_obj = await leaderboard_channel.fetch_message(msg_id)
            await msg_obj.edit(content=msg + '```')


    conn.commit()
    conn.close()


@client.command()
@commands.has_any_role('League Admin')
async def register(ctx, team_name):
    '''Registers a team into the player database.'''

    conn = sqlite3.connect(db_path)

    c = conn.cursor()
    
    c.execute("SELECT name FROM players WHERE name = ?", [team_name])
    row = c.fetchone()
    if row == None:
        c.execute(f"SELECT MAX(ID) from players")
        team_id = c.fetchone()[0]
        if team_id is None:
            team_id = 1
        else:
            team_id = int(team_id) + 1


        c.execute("INSERT INTO players VALUES(?, ?, 1500, 400, 0, 0, 1500, strftime('%s', 'now'), 0, NULL, 0)",
                [team_id, team_name])
        await ctx.send(f"Registered {team_name}.")
    else: 
        await ctx.send("Team is already registered.")
    conn.commit()

@client.command()
async def peak(ctx, name):
    '''Show's the highest ELO reached by a player.'''

    players_table = "players"

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
async def stats(ctx, name=None):
    '''Shows a players statistics.'''


    teams = False
    players_table = "players"

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

        if total_games == 0:
            await ctx.send(f"{name} played no games and has an elo of **{elo:.1f}**.")
        else:
            recent_perf = []
            if teams:
                c.execute("""SELECT p1,p2 
                               FROM games
                              WHERE (p1 == ? OR p2 == ?)
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""", [player_id, player_id])
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
async def compare(ctx, p1, p2):

    """Compares two users statistics.""" 

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    
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


@client.command()
@commands.has_any_role('League Admin')
async def set_elo(ctx, name, new_val):
    '''Adjusts a players ELO.'''
    
    new_val = int(new_val)

    player_id = find_userid_by_name(ctx, name)
    if player_id is None:
        await ctx.send("No user found by that name!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, elo FROM players WHERE ID = ?", [player_id])
    player = c.fetchone()

    if player is not None:
        name = player[0]
        c.execute("UPDATE players SET elo = ? WHERE ID = ?",
                    [new_val, player_id])

        out = f"{ctx.message.author.name} has set {name}'s Elo to **{new_val}**!"
        await ctx.send(out)
        await activity_channel().send(out)
        conn.commit()
        await leaderboard()
    conn.close()


@client.command()
@commands.has_any_role('League Admin')
async def set_sigma(ctx, name, new_val):
    '''Adjusts a players Sigma.'''


    new_val = int(new_val)

    player_id = find_userid_by_name(ctx, name)
    if player_id is None:
        await ctx.send("No user found by that name!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, sigma FROM players WHERE ID = ?", [player_id])
    player = c.fetchone()

    if player is not None:
        name = player[0]
        c.execute("UPDATE players SET sigma = ? WHERE ID = ?",
                    [new_val, player_id])


        out = f"{ctx.message.author.name} has set {name}'s Sigma to **{new_val}**!"

        await ctx.send(out)
        await activity_channel().send(out)
    conn.commit()
    conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def update_leaderboard(ctx):
    """ Manually updates the leaderboard."""

    await leaderboard()
    t = ctx.message.author.name
    await ctx.send(str(t) + " has updated the leaderboard.")
    await activity_channel().send(str(t) + " has updated the leaderboard.")


@client.command()
@commands.has_any_role("League Admin")
async def update_nickname(ctx, player: discord.Member, nickname):
    """Updates a team's nickname."""

    playerID = player.id
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE players SET name = ? WHERE ID = ?", [nickname, playerID])
    
    conn.commit()
    conn.close()

    await ctx.send("Nickname updated.")

record_pattern = re.compile(".*\[.*\].*\[.*\].*\[.*\].*", flags=re.IGNORECASE)
results_pattern = re.compile("\[.*\]", flags=re.IGNORECASE)

@client.command()
@commands.has_any_role("League Admin")
async def record(ctx, p1, p2, results_str):
    '''Admin command for recording 1v1s.'''
    if not results_pattern.match(results_str):
        print("regex matching failed")
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record team1 team2 [1,2,1,2,2,2]")
        return
    
    # results = [int(k) for k in results_str[1:-1].split(',')]
    try:
        results = eval(results_str)
    except:
        await ctx.send("Invalid command. Command should look like this (capitalization included): \n !record team1 team2 [1,2,1,2,2,2]")
    
    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send("Results should only contains 1s and 2s representing wins for each respective team.")
        return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    player1 = find_userid_by_name(ctx, p1)
    if player1 is None:
        await ctx.send("No user found by the name \"" + p1 + "\"!")
        conn.commit()
        conn.close()
        return
    
    # c.execute("SELECT name, elo, sigma FROM players where ID = ?", [player1])
    # result = c.fetchone()
    # if result is None:
    #     await ctx.send("No user found by the name \"" + p1 + "\"!")
    #     conn.commit()
    #     conn.close()
    #     return
    
    # name1 = result[0]
    # elo1 = float(result[1])
    # sigma1 = float(result[2])

    # player_1_rating = trueskill.Rating(elo1, sigma1)

    player2 = find_userid_by_name(ctx, p2)
    if player2 is None:
        await ctx.send("No user found by the name \"" + p2 + "\"!")
        conn.commit()
        conn.close()
        return
    
    # c.execute("SELECT name, elo, sigma FROM players where ID = ?", [player2])
    # result = c.fetchone()
    # if result is None:
    #     await ctx.send("No user found by the name \"" + p2 + "\"!")
    #     conn.commit()
    #     conn.close()
    #     return

    # name2 = result[0]
    # elo2 = float(result[1])
    # sigma2 = float(result[2])

    # player_2_rating = trueskill.Rating(elo2, sigma2)


    games_table = "games"
    players_table = "players"
    
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
        

        c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(player_won)])
        row = c.fetchone()
        elo1 = row[0]
        sigma1 = row[1]

        c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(player_lost)])
        row = c.fetchone()
        elo2 = row[0]
        sigma2 = row[1]

        player_won_rating, player_lost_rating = trueskill.rate_1vs1(trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, sigma2))
        elo1 = player_won_rating.mu
        sigma1 = player_won_rating.sigma
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

    c.execute(f"UPDATE {players_table} SET last_played_time = strftime('%s', 'now') where ID = ? or ID = ?", [str(player1), str(player2)])
    conn.commit()
    conn.close()

    if len(results) == 1:
        await activity_channel().send(f"[1v1] Game #{game_id} has finished.")
        await ctx.send(f"[1v1] Game #{game_id} has finished.")
    else:
        await activity_channel().send(f"[1v1] Games #{game_id-len(results)+1}-{game_id} have finished.")
        await ctx.send(f"[1v1] Games #{game_id-len(results)+1}-{game_id} have finished.")
    
    await compare(ctx, name1, name2)
    await leaderboard()

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

    player_1_rating = trueskill.Rating(elo1, sigma1)
    

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

async def my_background_task():
    await client.wait_until_ready()
    print("task started")
    while True:
        await leaderboard()
        print("The leaderboards have automatically updated.")
        await activity_channel().send("The leaderboards have automatically updated.")
        await asyncio.sleep(86400) # task runs every day
    print("bot down")

@client.event
async def on_ready():
    print("Bot has now logged on")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run risk bot.')
    parser.add_argument('--token', help='discord token', required=True)

    args = parser.parse_args()

    client.loop.create_task(my_background_task())
    client.run(args.token)
    