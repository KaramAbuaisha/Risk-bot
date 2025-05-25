import argparse
import sqlite3
import numpy as np
import trueskill
import random
import re
import requests
import asyncio
import math

from collections import defaultdict, deque
from copy import deepcopy

import discord

from discord.ext import commands

# Discord Client
bot_prefix = "!"
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=bot_prefix, intents=intents)

ones_channel = discord.Object(790313550270693396)
teams_channel = discord.Object(790313583484731422)
ffa_channel = discord.Object(1153103553888518235)
db_path = "risk.db"
old_dbs = [
    "risk_old_clean.db",
    "risk_old2.db",
    "risk_old3.db",
    "risk_old4.db",
    "risk_old5.db",
]

BETA = 200
main_elo = trueskill.TrueSkill(mu=1500, draw_probability=0, sigma=400, tau=4, beta=BETA)
main_elo.make_as_global()

# fmt: off
def erfc(x):
    """Complementary error function (via http://bit.ly/zOLqbc)"""
    z = abs(x)
    t = 1. / (1. + z / 2.)
    r = t * math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (
        0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (
            0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (
                -0.82215223 + t * 0.17087277
            )))
        )))
    )))
    return 2. - r if x < 0 else r
# fmt: on


def generate_sequence(player1_wins, player2_wins):
    total_games = player1_wins + player2_wins
    sequence = []
    count = 0
    player1_winrate = player1_wins / total_games
    while total_games > len(sequence):
        # Calculate the current ratio of player1_wins
        loss_ratio = count / (len(sequence) + 1)
        win_ratio = (count + 1) / (len(sequence) + 1)
        win_delta = win_ratio - player1_winrate
        loss_delta = player1_winrate - loss_ratio

        if win_delta == loss_delta:
            if random.choice([0, 1]):
                sequence.append(1)
                count += 1
            else:
                sequence.append(2)
        elif win_delta < loss_delta:
            sequence.append(1)
            count += 1
        else:
            sequence.append(2)

    return sequence


def cdf(x, mu=0, sigma=1):
    """Cumulative distribution function"""
    return 0.5 * erfc(-(x - mu) / (sigma * math.sqrt(2)))


def get_win_probability(elo1, sigma1, elo2, sigma2):
    deltaMu = elo1 - elo2
    sumSigma = sigma1 ** 2 + sigma2 ** 2
    rsss = np.sqrt(2 * (BETA ** 2) + sumSigma)
    return cdf(deltaMu / rsss)


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
        # server = ctx.message.guild
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
                c.execute(
                    f"SELECT ID FROM {players_table} WHERE name LIKE ?", [wildcard_name]
                )
                result = c.fetchone()
                if result is not None:
                    out = result[0]
    conn.commit()
    conn.close()
    if out is not None:
        return int(out)
    else:
        return None


async def leaderboard_team():
    """Updates the leaderboard channel"""

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = client.get_guild(383292703955222542)
    leaderboard_channel = discord.utils.get(guild.channels, id=787070684106194954)
    # await leaderboard_channel.purge(limit=15)
    msg_ids = [1030994412135776266, 1174189975437320194]
    msg_num = 0

    msg = "```\n"
    msg += (
        "{:<4}  {:<25}  {:<10} {:<10} {:<10}".format(
            "RANK", "NAME", "ELO", "SIGMA", "TOTAL GAMES"
        )
        + ""
        + "\n"
    )

    for i, player in enumerate(
        c.execute(
            """SELECT name, win, loss, elo, peak_elo, id, sigma 
                                            FROM players_team
                                            WHERE win + loss > 0
                                            ORDER BY elo desc"""
        ).fetchall()
    ):

        name, win, loss, elo, peak_elo, player_id, sigma = player
        player_id = int(player_id)
        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        rank = i + 1
        total_games = win + loss

        c.execute("UPDATE players_team SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        if elo > peak_elo:
            c.execute(
                "UPDATE players_team SET peak_elo = ? where ID = ?", [elo, player_id]
            )
            conn.commit()

        msg += (
            "{:<4}  {:<25}  {:<10}  {:<10}  {:<10}".format(
                f"#{rank}", name, f"{elo:.0f}", f"{sigma:.0f}", total_games
            )
            + "\n"
        )

        if rank % 15 == 0:
            if msg_num >= len(msg_ids):
                await leaderboard_channel.send(msg + "```")
            else:
                msg_id = msg_ids[msg_num]
                msg_obj = await leaderboard_channel.fetch_message(msg_id)
                await msg_obj.edit(content=msg + "```")
            msg_num += 1
            msg = "```\n"

    if msg != "```\n":
        if msg_num >= len(msg_ids):
            await leaderboard_channel.send(msg + "```")
        else:
            msg_id = msg_ids[msg_num]
            msg_obj = await leaderboard_channel.fetch_message(msg_id)
            await msg_obj.edit(content=msg + "```")

    role = discord.utils.get(guild.roles, name="Rank 1 Team")
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


async def leaderboard_solo(decay=False):
    """Updates the leaderboard channel"""

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = client.get_guild(383292703955222542)

    leaderboard_channel = discord.utils.get(guild.channels, id=787070644427948142)
    channel_1v1 = discord.utils.get(
        guild.channels, id=790313550270693396
    )  # 1v1s channel

    if decay:
        await channel_1v1.send("Elo Decay")

    # await leaderboard_channel.purge(limit=15)
    msg_ids = [1082353771486646322, 1082353773428609224, 1207164995087896597]
    msg_num = 0

    msg = "```\n"
    msg += (
        "{:<4}  {:<25}  {:<10}  {:<10}  {:<12}  {:<17}  {:<13}".format(
            "RANK",
            "NAME",
            "ELO",
            "SIGMA",
            "TOTAL GAMES",
            "% GAMES VS TOP 5",
            "RECENT GAMES",
        )
        + ""
        + "\n"
    )

    prev_role_assignment = defaultdict(set)
    for role_name in [
        "Grandmaster",
        "Master",
        "Expert",
        "Diamond",
        "Platinum",
        "Gold",
        "Silver",
        "Bronze",
    ]:
        role = discord.utils.get(guild.roles, name=role_name)
        for member in role.members:
            prev_role_assignment[role_name].add(member.id)
            # await member.remove_roles(role)

        curr_role_assignment = defaultdict(set)

    rank = 0
    games_required = 25
    num_days = 30
    # for i, player in enumerate(c.execute("""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time)
    #                                           FROM players
    #                                          WHERE win + loss > 9
    #                                          AND strftime('%s', 'now') - last_played_time < 86400 * 14
    #                                          ORDER BY elo desc""").fetchall()):

    for player in c.execute(
        f"""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time) as seconds_ago, num
                                                FROM players 
                                                JOIN (SELECT p, num
                                                            FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                USING(p)
                                                                UNION ALL
                                                                SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                USING(p)
                                                                WHERE tbl1.p is NULL)
                                                            WHERE num >= {games_required}) tbl
                                                ON players.id = tbl.p
                                                ORDER BY elo desc"""
    ).fetchall():

        (
            name,
            win,
            loss,
            elo,
            peak_elo,
            player_id,
            sigma,
            seconds_ago,
            num_games,
        ) = player

        win, loss = 0, 0
        c.execute(
            """SELECT p1,p2,id,s1,s2 
                        FROM games 
                        WHERE (p1 == ? OR p2 == ?) 
                        AND (s1 is not NULL or s2 is not NULL)""",
            [player_id, player_id],
        )
        all_games = c.fetchall()

        for items in all_games:
            if (player_id == items[0]) ^ (items[3] == "won"):
                loss += 1
            else:
                win += 1

        player_id = int(player_id)

        games_vs_top_5 = c.execute(
            f"""
        select count(*) from games
        where (p1={player_id} and p2 in (SELECT id
                                                FROM players 
                                                JOIN (SELECT p, num
                                                            FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                USING(p)
                                                                UNION ALL
                                                                SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                USING(p)
                                                                WHERE tbl1.p is NULL)
                                                            WHERE num >= {games_required}) tbl
                                                ON players.id = tbl.p
                                                ORDER BY elo desc
                                                LIMIT 5))
        or (p2={player_id} and p1 in (SELECT id
                                                FROM players 
                                                JOIN (SELECT p, num
                                                            FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                USING(p)
                                                                UNION ALL
                                                                SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                USING(p)
                                                                WHERE tbl1.p is NULL)
                                                            WHERE num >= {games_required}) tbl
                                                ON players.id = tbl.p
                                                ORDER BY elo desc
                                                LIMIT 5))"""
        ).fetchone()[0]

        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        rank += 1
        total_games = win + loss

        c.execute("UPDATE players SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        member = guild.get_member(player_id)
        if member is not None:
            if rank == 1:
                role_name = "Grandmaster"
            elif rank <= 4:
                role_name = "Master"
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
                role = discord.utils.get(guild.roles, name=role_name)
                await member.add_roles(role)

        if elo > peak_elo:
            c.execute("UPDATE players SET peak_elo = ? where ID = ?", [elo, player_id])
            conn.commit()

        msg += (
            "{:<4}  {:<25}  {:<10}  {:<10}  {:<12}  {:<17}  {:<13}".format(
                f"#{rank}",
                name,
                f"{elo:.0f}",
                f"{sigma:.0f}",
                total_games,
                round(100 * games_vs_top_5 / total_games, 2),
                num_games,
            )
            + "\n"
        )
        if rank % 15 == 0:
            # await leaderboard_channel.send(msg + '```')
            if msg_num >= len(msg_ids):
                await leaderboard_channel.send(msg + "```")
            else:
                msg_id = msg_ids[msg_num]
                msg_obj = await leaderboard_channel.fetch_message(msg_id)
                await msg_obj.edit(content=msg + "```")
            msg_num += 1
            msg = "```\n"

    # if not rank % 15 == 0:
    #     await leaderboard_channel.send(msg + '```')
    #     msg = "```\n"

    msg += "-" * 44 + "INACTIVE" + "-" * 44 + "\n"

    for player in c.execute(
        f"""SELECT name, win, loss, elo, peak_elo, id, sigma, (strftime('%s', 'now') - last_played_time) as seconds_ago, COALESCE(num, 0) as num
                                FROM players 
                                left JOIN (SELECT p, num
                                            FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                USING(p)
                                                UNION ALL
                                                SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                USING(p)
                                                WHERE tbl1.p is NULL)) tbl
                                ON players.id = tbl.p
                                WHERE (num is null or num < {games_required}) and win + loss >= {games_required}
                                ORDER BY elo desc"""
    ).fetchall():

        (
            name,
            win,
            loss,
            elo,
            peak_elo,
            player_id,
            sigma,
            seconds_ago,
            num_games,
        ) = player

        win, loss = 0, 0
        c.execute(
            """SELECT p1,p2,id,s1,s2 
                        FROM games 
                        WHERE (p1 == ? OR p2 == ?) 
                        AND (s1 is not NULL or s2 is not NULL)""",
            [player_id, player_id],
        )
        all_games = c.fetchall()

        for items in all_games:
            if (player_id == items[0]) ^ (items[3] == "won"):
                loss += 1
            else:
                win += 1

        player_id = int(player_id)

        games_vs_top_5 = c.execute(
            f"""
        select count(*) from games
        where (p1={player_id} and p2 in (SELECT id
                                                FROM players 
                                                JOIN (SELECT p, num
                                                            FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                USING(p)
                                                                UNION ALL
                                                                SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                USING(p)
                                                                WHERE tbl1.p is NULL)
                                                            WHERE num >= {games_required}) tbl
                                                ON players.id = tbl.p
                                                ORDER BY elo desc
                                                LIMIT 5))
        or (p2={player_id} and p1 in (SELECT id
                                                FROM players 
                                                JOIN (SELECT p, num
                                                            FROM (SELECT p, num1 + COALESCE(num2, 0) as num FROM (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                left JOIN (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                USING(p)
                                                                UNION ALL
                                                                SELECT p, num2 as num FROM (SELECT p2 as p, count(*) as num2 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p2)) as tbl2
                                                                left JOIN (SELECT p1 as p, count(*) as num1 FROM games WHERE strftime('%s', 'now') - time < 86400 * {num_days} GROUP BY(p1)) as tbl1
                                                                USING(p)
                                                                WHERE tbl1.p is NULL)
                                                            WHERE num >= {games_required}) tbl
                                                ON players.id = tbl.p
                                                ORDER BY elo desc
                                                LIMIT 5))"""
        ).fetchone()[0]

        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        if decay:
            if elo > 1500:
                new_elo = elo - (elo - 1500) * 0.05
                new_sigma = sigma + (elo - new_elo) * 0.2
                c.execute(
                    "UPDATE players SET elo = ? WHERE ID = ?", [new_elo, player_id]
                )
                c.execute(
                    "UPDATE players SET sigma = ? WHERE ID = ?", [new_sigma, player_id]
                )
                await channel_1v1.send(
                    f"{name} - elo: {elo:.2f} -> {new_elo:.2f}, sigma: {sigma:.2f} -> {new_sigma:.2f}"
                )
                elo = new_elo
                sigma = new_sigma

        rank += 1
        total_games = win + loss

        c.execute("UPDATE players SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        member = guild.get_member(player_id)
        if member is not None:
            if rank == 1:
                role_name = "Grandmaster"
            elif rank <= 4:
                role_name = "Master"
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
                role = discord.utils.get(guild.roles, name=role_name)
                await member.add_roles(role)

        msg += (
            "{:<4}  {:<25}  {:<10}  {:<10}  {:<12}  {:<17}  {:<13}".format(
                f"#{rank}",
                name,
                f"{elo:.0f}",
                f"{sigma:.0f}",
                total_games,
                round(100 * games_vs_top_5 / total_games, 2),
                num_games,
            )
            + "\n"
        )

        if rank % 15 == 0:
            # await leaderboard_channel.send(msg + '```')
            if msg_num >= len(msg_ids):
                await leaderboard_channel.send(msg + "```")
            else:
                msg_id = msg_ids[msg_num]
                msg_obj = await leaderboard_channel.fetch_message(msg_id)
                await msg_obj.edit(content=msg + "```")
            msg_num += 1
            msg = "```\n"

    for role_name in [
        "Grandmaster",
        "Master",
        "Expert",
        "Diamond",
        "Platinum",
        "Gold",
        "Silver",
        "Bronze",
    ]:
        role = discord.utils.get(guild.roles, name=role_name)
        for member_id in prev_role_assignment[role_name]:
            if member_id not in curr_role_assignment[role_name]:
                member = guild.get_member(member_id)
                await member.remove_roles(role)

    # c.execute("SELECT MAX(ELO), ID from players WHERE win + loss > 19")
    # player = c.fetchone()[1]
    # member = guild.get_member(player)
    # role = discord.utils.get(guild.roles, name="Rank 1 Solo")
    # await role.members[0].remove_roles(role)
    # await member.add_roles(role)

    if msg != "```\n":
        # await leaderboard_channel.send(msg + '```')
        if msg_num >= len(msg_ids):
            await leaderboard_channel.send(msg + "```")
        else:
            msg_id = msg_ids[msg_num]
            msg_obj = await leaderboard_channel.fetch_message(msg_id)
            await msg_obj.edit(content=msg + "```")
        msg_num += 1

    while msg_num < len(msg_ids):
        msg_id = msg_ids[msg_num]
        msg_obj = await leaderboard_channel.fetch_message(msg_id)
        await msg_obj.edit(content="----")
        msg_num += 1
        await asyncio.sleep(1)

    conn.commit()
    conn.close()


async def leaderboard_ffa():
    """Updates the leaderboard channel"""

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    guild = client.get_guild(383292703955222542)
    leaderboard_channel = discord.utils.get(guild.channels, id=1153102418205233202)
    # await leaderboard_channel.purge(limit=15)
    msg_ids = [1182004017665167421, 1182004019242225805, 1182004021012205629]
    msg_num = 0

    msg = "```\n"
    msg += (
        "{:<4}  {:<25}  {:<10} {:<10} {:<10}".format(
            "RANK", "NAME", "ELO", "SIGMA", "TOTAL GAMES"
        )
        + ""
        + "\n"
    )

    for i, player in enumerate(
        c.execute(
            """SELECT name, win, loss, elo, peak_elo, id, sigma 
                                            FROM players_ffa
                                            -- WHERE win + loss > 0
                                            ORDER BY elo desc"""
        ).fetchall()
    ):

        name, win, loss, elo, peak_elo, player_id, sigma = player
        player_id = int(player_id)
        win = int(win)
        loss = int(loss)
        elo = float(elo)
        sigma = float(sigma)
        peak_elo = float(peak_elo)

        rank = i + 1
        total_games = win + loss

        c.execute("UPDATE players_ffa SET rank = ? WHERE ID = ?", [rank, player_id])
        conn.commit()

        if elo > peak_elo:
            c.execute(
                "UPDATE players_ffa SET peak_elo = ? where ID = ?", [elo, player_id]
            )
            conn.commit()

        msg += (
            "{:<4}  {:<25}  {:<10}  {:<10}  {:<10}".format(
                f"#{rank}", name, f"{elo:.0f}", f"{sigma:.0f}", total_games
            )
            + "\n"
        )

        if rank % 15 == 0:
            if msg_num >= len(msg_ids):
                await leaderboard_channel.send(msg + "```")
            else:
                msg_id = msg_ids[msg_num]
                msg_obj = await leaderboard_channel.fetch_message(msg_id)
                await msg_obj.edit(content=msg + "```")
            msg_num += 1
            msg = "```\n"

    if msg != "```\n":
        if msg_num >= len(msg_ids):
            await leaderboard_channel.send(msg + "```")
        else:
            msg_id = msg_ids[msg_num]
            msg_obj = await leaderboard_channel.fetch_message(msg_id)
            await msg_obj.edit(content=msg + "```")

    # role = discord.utils.get(guild.roles, name="Rank 1 FFA")
    # if role:
    #     for member in role.members:
    #         await member.remove_roles(role)

    # try:
    #     c.execute("SELECT MAX(ELO), ID from players_ffa")
    #     player = int(c.fetchone()[1])
    #     member = guild.get_member(player)
    #     await member.add_roles(role)
    # except Exception as e:
    #     # print(e)
    #     pass

    conn.commit()
    conn.close()


@client.command()
@commands.has_any_role("League Admin", "Risker")
async def register(ctx, member: discord.Member):
    """Registers a user into the player database."""

    conn = sqlite3.connect(db_path)

    c = conn.cursor()

    if ctx.channel.id == teams_channel.id:
        c.execute("SELECT elo FROM players_team WHERE ID = ?", [member.id])
        row = c.fetchone()
        if row == None:
            c.execute(
                "INSERT INTO players_team VALUES(?, ?, 1500, 400, 0, 0, 1500, strftime('%s', 'now'), 0, NULL)",
                [member.id, member.name],
            )
            await ctx.send(f"Registered {member.name}.")
            conn.commit()
        else:
            await ctx.send("User is already registered.")
    elif ctx.channel.id == ffa_channel.id:
        c.execute("SELECT elo FROM players_ffa WHERE ID = ?", [member.id])
        row = c.fetchone()
        if row == None:
            c.execute(
                "INSERT INTO players_ffa VALUES(?, ?, 1500, 100, 0, 0, 1500, strftime('%s', 'now'), 0, NULL)",
                [member.id, member.name],
            )
            await ctx.send(f"Registered {member.name}.")
            conn.commit()
        else:
            await ctx.send("User is already registered.")
    else:
        c.execute("SELECT elo FROM players WHERE ID = ?", [member.id])
        row = c.fetchone()
        if row == None:
            c.execute(
                "INSERT INTO players VALUES(?, ?, 1500, 400, 0, 0, 1500, strftime('%s', 'now'), 0, NULL, 0)",
                [member.id, member.name],
            )
            role = discord.utils.get(ctx.guild.roles, name="1v1 League")
            await member.add_roles(role)
            await ctx.send(f"Registered {member.name}.")
            conn.commit()
        else:
            await ctx.send("User is already registered.")


@client.command()
async def peak(ctx, name=None):
    """Show's the highest ELO reached by a player."""

    players_table = "players"
    if ctx.channel.id == teams_channel.id:
        players_table += "_team"
    elif ctx.channel.id == ffa_channel.id:
        players_table += "_ffa"

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
@commands.has_any_role("Moderator")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int, channel: discord.TextChannel = None):
    """Deletes messages in channel. !purge 3 deletes last 3 messages in current channel. !purge 3 #bot-spam deletes last 3 messages in #bot-spam."""

    if channel is None or channel == ctx.channel:
        await ctx.channel.purge(limit=limit + 1)
    else:
        await channel.purge(limit=limit)


@client.command()
async def stats(ctx, name=None):
    """Shows a players statistics."""

    players_table = "players"

    if ctx.channel.id == teams_channel.id:
        players_table += "_team"
    elif ctx.channel.id == ffa_channel.id:
        players_table += "_ffa"

    if name is None:
        player_id = ctx.author.id
    else:
        player_id = find_userid_by_name(ctx, name)
        if player_id is None:
            await ctx.send("No user found by that name.")
            return

    print(player_id)
    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    c.execute(
        f"SELECT name, elo, sigma, win, loss, streak, peak_elo, rank FROM {players_table} where ID = ?",
        [player_id],
    )
    player = c.fetchone()

    if player is not None:
        name, elo, sigma, win, loss, streak, peak_elo, rank = player

        if players_table == "players":
            win, loss = 0, 0
            c.execute(
                """SELECT p1,p2,id,s1,s2 
                            FROM games 
                            WHERE (p1 == ? OR p2 == ?) 
                            AND (s1 is not NULL or s2 is not NULL)""",
                [player_id, player_id],
            )
            all_games = c.fetchall()

            for items in all_games:
                if (player_id == items[0]) ^ (items[3] == "won"):
                    loss += 1
                else:
                    win += 1
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
            if players_table == "players_team":
                c.execute(
                    """SELECT p1,p2,p3,p4,p5,p6,p7,p8,id,s1,s2 
                               FROM games_team 
                              WHERE (p1 == ? OR p2 == ? or p3 == ? or p4 == ? or p5 == ? or p6 == ? or p7 == ? or p8 == ?) 
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""",
                    [
                        player_id,
                        player_id,
                        player_id,
                        player_id,
                        player_id,
                        player_id,
                        player_id,
                        player_id,
                    ],
                )
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

            elif players_table == "players":
                c.execute(
                    """SELECT p1,p2,id,s1,s2 
                               FROM games 
                              WHERE (p1 == ? OR p2 == ?) 
                                AND (s1 is not NULL or s2 is not NULL) 
                              ORDER BY ID DESC LIMIT 10""",
                    [player_id, player_id],
                )
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

            embed = discord.Embed(colour=0x1F1E1E)
            embed.set_thumbnail(url=f"{url}")
            embed.add_field(
                name=f"{name} {emoji}\n\u200b",
                value=f"Rank: **{rank if rank else 'Unranked'}** | **{win}**W - **{loss}**L (**{(win / total_games) * 100:.1f}% Win Rate**)\n\nRecent Performance:\n{rp}",
                inline=False,
            )
            embed.add_field(name="\n\u200b", value=f"Elo: **{elo:.1f}**")
            embed.add_field(name="\n\u200b", value=f"Sigma: **{sigma:.1f}**")
            embed.add_field(name="\n\u200b", value=f"Streak: **{streak}**")
            await ctx.send(embed=embed)
    else:
        await ctx.send("No user found by that name!")

    conn.commit()
    conn.close()

@client.command()
async def stats_past(ctx, name=None):
    """Shows a players past season statistics."""

    teams = False
    players_table = "players"

    if ctx.channel.id == teams_channel.id:
        teams = True
        players_table += "_team"

    for i, db_path in enumerate(old_dbs):
        conn = sqlite3.connect(db_path, uri=True)

        if name is None:
            player_id = ctx.author.id
        else:
            player_id = find_userid_by_name(ctx, name)
            if player_id is None:
                continue

        c = conn.cursor()
        c.execute(
            f"SELECT name, elo, sigma, win, loss, streak, peak_elo, rank FROM {players_table} where ID = ?",
            [player_id],
        )
        player = c.fetchone()

        if player is not None:
            name, elo, sigma, win, loss, streak, peak_elo, rank = player
            total_games = win + loss

            if total_games > 0:
                await ctx.send(
                    f"Season {i+1}:\n Name: {name} | Elo: **{elo:.1f}** | Sigma: **{sigma:.1f}** | Rank: **{rank if rank else 'Unranked'}** | **{win}**W - **{loss}**L (**{(win / total_games) * 100:.1f}% Win Rate**)"
                )

        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(3, 5, commands.BucketType.user)
async def compare(ctx, p1, p2):

    """Compares two users statistics."""

    if ctx.channel.id == ones_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        t1 = find_userid_by_name(ctx, p1)
        if t1 is None:
            await ctx.send('No user found by the name "' + p1 + '"!')
            conn.commit()
            conn.close()
            return

        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.send('No user found by the name "' + p1 + '"!')
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = float(result[1])
        sigma1 = float(result[2])

        t2 = find_userid_by_name(ctx, p2)
        if t2 is None:
            await ctx.send('No user found by the name "' + p2 + '"!')
            conn.commit()
            conn.close()
            return

        c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.send('No user found by the name "' + p2 + '"!')
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

        c.execute(
            "SELECT ID, s1 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC",
            [t1, t2],
        )
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
                print(f"Unknown result: {result} for game {i}")

            game = c.fetchone()

        c.execute(
            "SELECT ID, s2 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC",
            [t2, t1],
        )
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
                print(f"Unknown result: {result} for game {i}")

            game = c.fetchone()

        wins_q.sort()
        losses_q.sort()

        win_probability = get_win_probability(elo1, sigma1, elo2, sigma2)

        def get_winrate_in_last_x_games(x):
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
                        wins_x += x - i
                    else:
                        losses_x += x - i
                return f"{name1} has a win rate of {wins_x/(wins_x+losses_x)*100:.2f}% (**{wins_x}W - {losses_x}L**) against {name2} in the last {x} games.\n"
            else:
                return ""

        if wins + losses > 0:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have played a total of {wins + losses} games together.\n"
            s += f"{name1} has a win rate of {wins/(wins+losses)*100:.2f}% (**{wins}W - {losses}L**) against {name2}.\n"
            s += get_winrate_in_last_x_games(20)
            # s += get_winrate_in_last_x_games(30)
            # s += get_winrate_in_last_x_games(40)
            s += get_winrate_in_last_x_games(50)
        else:
            s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have not played any games together.\n"

        s += f"{name1}'s expected win probability against {name2} is {win_probability*100:.2f}%."

        await ctx.send(s)
        conn.commit()
        conn.close()

    if ctx.channel.id == teams_channel.id:

        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()

        t1 = find_userid_by_name(ctx, p1)
        if t1 is None:
            await ctx.send('No user found by the name "' + p1 + '"!')
            conn.commit()
            conn.close()
            return

        c.execute("SELECT name, elo FROM players_team where ID = ?", [t1])
        result = c.fetchone()
        if result is None:
            await ctx.send('No user found by the name "' + p1 + '"!')
            conn.commit()
            conn.close()
            return
        name1 = result[0]
        elo1 = str(result[1])

        t2 = find_userid_by_name(ctx, p2)
        if t2 is None:
            await ctx.send('No user found by the name "' + p2 + '"!')
            conn.commit()
            conn.close()
            return

        c.execute("SELECT name, elo FROM players_team where ID = ?", [t2])
        result = c.fetchone()
        if result is None:
            await ctx.send('No user found by the name "' + p2 + '"!')
            conn.commit()
            conn.close()
            return
        name2 = result[0]
        elo2 = str(result[1])

        wins_together = 0
        loss_together = 0
        wins_against = 0
        loss_against = 0

        c.execute(
            "SELECT s1, s2, ID FROM games_team where (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND s1 != s2",
            [t1, t1, t1, t1, t2, t2, t2, t2],
        )
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]
            if s1 > s2:
                wins_together += 1
            elif s1 < s2:
                loss_together += 1

            game = c.fetchone()

        c.execute(
            "SELECT s1, s2, ID FROM games_team where (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND s1 != s2",
            [t1, t1, t1, t1, t2, t2, t2, t2],
        )
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]

            if s1 < s2:
                wins_together += 1
            elif s1 > s2:
                loss_together += 1

            game = c.fetchone()

        c.execute(
            "SELECT s1, s2 FROM games_team where (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND s1 != s2",
            [t1, t1, t1, t1, t2, t2, t2, t2],
        )
        game = c.fetchone()
        while game is not None:
            s1 = game[0]
            s2 = game[1]

            if s1 > s2:
                wins_against += 1
            elif s1 < s2:
                loss_against += 1

            game = c.fetchone()

        c.execute(
            "SELECT s1, s2 FROM games_team where (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND s1 != s2",
            [t1, t1, t1, t1, t2, t2, t2, t2],
        )
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
            winrate_together = float(
                "{0:.2f}".format((wins_together / total_together) * 100)
            )
            str_together = (
                f"{name1} **[{elo1}]** and {name2} **[{elo2}]** have played "
                f"{total_together} games together with a win rate of "
                f"{winrate_together}% (**{wins_together}W - {loss_together}L**)."
            )
        else:
            str_together = (
                f"{name1} **[{elo1}]** and {name2} **[{elo2}]** have not played together."
            )

        total_against = wins_against + loss_against
        if total_against > 0:
            winrate_against = float(
                "{0:.2f}".format((wins_against / total_against) * 100)
            )
            str_against = (
                f"{name1} **[{elo1}]** has played against {name2} **[{elo2}]** "
                f"a total of {total_against} times with a win rate of "
                f"{winrate_against}% (**{wins_against}W - {loss_against}L**) ."
            )
        else:
            str_against = (
                f"{name1} **[{elo1}]** and {name2} **[{elo2}]** have not played against each other."
            )

        await ctx.send(str_together + "\n" + str_against)
        conn.commit()
        conn.close()


@client.command()
@commands.cooldown(3, 5, commands.BucketType.user)
async def compare_past(ctx, p1, p2):
    """Compares two users previous season statistics."""

    for season_number, db_path in enumerate(old_dbs):

        if ctx.channel.id == ones_channel.id:

            conn = sqlite3.connect(db_path, uri=True)
            c = conn.cursor()

            t1 = find_userid_by_name(ctx, p1)
            if t1 is None:
                continue

            c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
            result = c.fetchone()
            if result is None:
                continue
            name1 = result[0]
            elo1 = float(result[1])
            sigma1 = float(result[2])

            t2 = find_userid_by_name(ctx, p2)
            if t2 is None:
                continue

            c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
            result = c.fetchone()
            if result is None:
                continue
            name2 = result[0]
            elo2 = float(result[1])
            sigma2 = float(result[2])

            wins = 0
            losses = 0

            wins_q = list()
            losses_q = list()

            c.execute(
                "SELECT ID, s1 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC",
                [t1, t2],
            )
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

            c.execute(
                "SELECT ID, s2 FROM games WHERE (p1 == ? AND p2 == ?) AND s1 != s2 ORDER BY ID ASC",
                [t2, t1],
            )
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
                            wins_20 += 20 - i
                        else:
                            losses_20 += 20 - i
                    s += f"{name1} has a win rate of {wins_20/(wins_20+losses_20)*100:.2f}% (**{wins_20}W - {losses_20}L**) against {name2} in the last 20 games.\n"

            else:
                s = f"{name1} (Elo: {int(round(elo1))}, Sigma: {int(round(sigma1))}) and {name2} (Elo: {int(round(elo2))}, Sigma: {int(round(sigma2))}) have not played any games together.\n"

            s += f"{name1}'s expected win probability against {name2} is {win_probability*100:.2f}%."

            await ctx.send(f"Season {season_number+1}:")
            await ctx.send(s)
            conn.commit()
            conn.close()

        if ctx.channel.id == teams_channel.id:

            conn = sqlite3.connect(db_path, uri=True)
            c = conn.cursor()

            x = ctx.author.id

            t1 = find_userid_by_name(ctx, p1)
            if t1 is None:
                await ctx.send('No user found by the name "' + p1 + '"!')
                conn.commit()
                conn.close()
                return

            c.execute("SELECT name, elo FROM players_team where ID = ?", [t1])
            result = c.fetchone()
            if result is None:
                await ctx.send('No user found by the name "' + p1 + '"!')
                conn.commit()
                conn.close()
                return
            name1 = result[0]
            elo1 = str(result[1])

            t2 = find_userid_by_name(ctx, p2)
            if t2 is None:
                await ctx.send('No user found by the name "' + p2 + '"!')
                conn.commit()
                conn.close()
                return

            c.execute("SELECT name, elo FROM players_team where ID = ?", [t2])
            result = c.fetchone()
            if result is None:
                await ctx.send('No user found by the name "' + p2 + '"!')
                conn.commit()
                conn.close()
                return
            name2 = result[0]
            elo2 = str(result[1])

            wins_together = 0
            loss_together = 0
            wins_against = 0
            loss_against = 0

            c.execute(
                "SELECT s1, s2, ID FROM games_team where (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND s1 != s2",
                [t1, t1, t1, t1, t2, t2, t2, t2],
            )
            game = c.fetchone()
            while game is not None:
                s1 = game[0]
                s2 = game[1]
                if s1 > s2:
                    wins_together += 1
                elif s1 < s2:
                    loss_together += 1

                game = c.fetchone()

            c.execute(
                "SELECT s1, s2, ID FROM games_team where (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND s1 != s2",
                [t1, t1, t1, t1, t2, t2, t2, t2],
            )
            game = c.fetchone()
            while game is not None:
                s1 = game[0]
                s2 = game[1]

                if s1 < s2:
                    wins_together += 1
                elif s1 > s2:
                    loss_together += 1

                game = c.fetchone()

            c.execute(
                "SELECT s1, s2 FROM games_team where (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND s1 != s2",
                [t1, t1, t1, t1, t2, t2, t2, t2],
            )
            game = c.fetchone()
            while game is not None:
                s1 = game[0]
                s2 = game[1]

                if s1 > s2:
                    wins_against += 1
                elif s1 < s2:
                    loss_against += 1

                game = c.fetchone()

            c.execute(
                "SELECT s1, s2 FROM games_team where (p5 == ? OR p6 == ? OR p7 == ? OR p8 == ?) AND (p1 == ? OR p2 == ? OR p3 == ? OR p4 == ?) AND s1 != s2",
                [t1, t1, t1, t1, t2, t2, t2, t2],
            )
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
                winrate_together = float(
                    "{0:.2f}".format((wins_together / total_together) * 100)
                )
                str_together = (
                    f"{name1} **[{elo1}]** and {name2} **[{elo2}]** have played "
                    f"{total_together} games together with a win rate of "
                    f"{winrate_together}% (**{wins_together}W - {loss_together}L**)."
                )
            else:
                str_together = (
                    f"{name1} **[{elo1}]** and {name2} **[{elo2}]** have not played together."
                )

            total_against = wins_against + loss_against
            if total_against > 0:
                winrate_against = float(
                    "{0:.2f}".format((wins_against / total_against) * 100)
                )
                str_against = (
                    f"{name1} **[{elo1}]** has played against {name2} **[{elo2}]** "
                    f"a total of {total_against} times with a win rate of "
                    f"{winrate_against}% (**{wins_against}W - {loss_against}L**) ."
                )
            else:
                str_against = (
                    f"{name1} **[{elo1}]** and {name2} **[{elo2}]** have not played against each other."
                )

            await ctx.send(str_together + "\n" + str_against)
            conn.commit()
            conn.close()


@client.command()
@commands.has_any_role("League Admin")
async def set_elo(ctx, name, new_val):
    """Adjusts a players ELO."""

    new_val = int(new_val)

    if ctx.channel.id == teams_channel.id:
        players_table = "players_team"
        leaderboard = leaderboard_team
    elif ctx.channel.id == ffa_channel.id:
        players_table = "players_ffa"
        leaderboard = leaderboard_ffa
    else:
        players_table = "players"
        leaderboard = leaderboard_solo

    player_id = find_userid_by_name(ctx, name)
    if player_id is None:
        await ctx.send("No user found by that name!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT name, elo FROM {players_table} WHERE ID = ?", [player_id])
    player = c.fetchone()

    if player is not None:
        name = player[0]
        c.execute(
            f"UPDATE {players_table} SET elo = ? WHERE ID = ?", [new_val, player_id]
        )

        out = f"{ctx.message.author.name} has set {name}'s Elo to **{new_val}**!"
        await ctx.send(out)
        conn.commit()
        await leaderboard()
        conn.close()


@client.command()
@commands.has_any_role("League Admin")
async def set_sigma(ctx, name, new_val):
    """Adjusts a players Sigma."""

    new_val = int(new_val)

    if ctx.channel.id == teams_channel.id:
        players_table = "players_team"
        leaderboard = leaderboard_team
    elif ctx.channel.id == ffa_channel.id:
        players_table = "players_ffa"
        leaderboard = leaderboard_ffa
    else:
        players_table = "players"
        leaderboard = leaderboard_solo

    player_id = find_userid_by_name(ctx, name)
    if player_id is None:
        await ctx.send("No user found by that name!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT name, sigma FROM {players_table} WHERE ID = ?", [player_id])
    player = c.fetchone()

    if player is not None:
        name = player[0]
        c.execute(
            f"UPDATE {players_table} SET sigma = ? WHERE ID = ?", [new_val, player_id]
        )

        out = f"{ctx.message.author.name} has set {name}'s Sigma to **{new_val}**!"
        await ctx.send(out)
        conn.commit()
        await leaderboard()
        conn.close()


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role("League Admin")
async def update_leaderboards(ctx):
    """Manually updates the leaderboards."""

    await leaderboard_solo()
    await leaderboard_team()
    await leaderboard_ffa()
    t = ctx.message.author.name
    await ctx.send(str(t) + " has updated the leaderboards.")


@client.command()
@commands.has_any_role("League Admin")
async def update_nickname(ctx, player: discord.Member, nickname):
    """Updates a players nickname."""

    playerID = player.id
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE players SET name = ? WHERE ID = ?", [nickname, playerID])
    c.execute("UPDATE players_team SET name = ? WHERE ID = ?", [nickname, playerID])
    c.execute("UPDATE players_ffa SET name = ? WHERE ID = ?", [nickname, playerID])

    conn.commit()
    conn.close()

    await ctx.send("Nickname updated.")


record_pattern = re.compile(".*\[.*\].*\[.*\].*\[.*\].*", flags=re.IGNORECASE)
ffa_record_pattern = re.compile(".*\[.*\].*\[.*\].*", flags=re.IGNORECASE)
results_pattern = re.compile("\[.*\]", flags=re.IGNORECASE)


@client.command()
@commands.has_any_role("League Admin", "TG League Admin")
async def record_team(ctx, *args):
    """Admin command for recording team games."""
    record_info = " ".join(args)
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send(
            "Invalid command. Command should look like this (capitalization included): \n !record_team [@player1, @player2] [@player3, @player4] [1,2,1,2,2,2]"
        )
        return

    team1_start = record_info.find("[")
    team1_end = record_info.find("]", team1_start) + 1
    team1_str = record_info[team1_start:team1_end]

    team2_start = record_info.find("[", team1_end)
    team2_end = record_info.find("]", team2_start) + 1
    team2_str = record_info[team2_start:team2_end]

    result_start = record_info.find("[", team2_end) + 1
    result_end = record_info.find("]", result_start)
    results = [int(k) for k in record_info[result_start:result_end].split(",")]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send(
            "Results should only contains 1s and 2s representing wins for each respective team."
        )
        return

    ids = []
    i = 0
    team1 = []
    while i < len(team1_str):
        c = team1_str[i]
        if c == "<":
            player_id = ""
            i += 2  # <@!361548991755976704>
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
            i += 2
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

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    games_table = "games_team"
    players_table = "players_team"

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 0
    else:
        game_id = int(game_id)

    values = "?, " + ("?, " * len(team1) + "NULL, " * (4 - len(team1))) * 2 + "?, ?"

    for result in results:

        game_id += 1

        if result == 1:
            values1 = (
                [str(game_id)]
                + [str(p) for p in team1]
                + [str(p) for p in team2]
                + ["won", "lost"]
            )
            c.execute(f"INSERT INTO {games_table} VALUES({values})", values1)
            team_won = team1
            team_lost = team2
        else:
            values2 = (
                [str(game_id)]
                + [str(p) for p in team1]
                + [str(p) for p in team2]
                + ["lost", "won"]
            )
            c.execute(f"INSERT INTO {games_table} VALUES({values})", values2)
            team_won = team2
            team_lost = team1

        team_won_ratings = []
        for t in team_won:
            try:
                c.execute(
                    f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(t)]
                )
                row = c.fetchone()
                elo = row[0]
                sigma = row[1]
                team_won_ratings.append(trueskill.Rating(elo, sigma))
            except:
                print(f"could not find {str(t)}")
        team_lost_ratings = []
        for t in team_lost:
            c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(t)])
            row = c.fetchone()
            elo = row[0]
            sigma = row[1]
            team_lost_ratings.append(trueskill.Rating(elo, sigma))

        team_won_ratings, team_lost_ratings = trueskill.rate(
            [team_won_ratings, team_lost_ratings]
        )

        for i, t in enumerate(team_won):
            c.execute(
                f"UPDATE {players_table} SET win = win + 1 where ID = ?", [str(t)]
            )
            c.execute(
                f"UPDATE {players_table} SET streak = streak + 1 WHERE ID = ?", [str(t)]
            )
            c.execute(
                f"UPDATE {players_table} SET elo = ? where ID = ?",
                [team_won_ratings[i].mu, t],
            )
            c.execute(
                f"UPDATE {players_table} SET sigma = ? where ID = ?",
                [team_won_ratings[i].sigma, t],
            )

        for i, t in enumerate(team_lost):
            c.execute(
                f"UPDATE {players_table} SET loss = loss + 1 where ID = ?", [str(t)]
            )
            c.execute(f"UPDATE {players_table} SET streak = 0 WHERE ID = ?", [str(t)])
            c.execute(
                f"UPDATE {players_table} SET elo = ? where ID = ?",
                [team_lost_ratings[i].mu, t],
            )
            c.execute(
                f"UPDATE {players_table} SET sigma = ? where ID = ?",
                [team_lost_ratings[i].sigma, t],
            )

    conn.commit()
    conn.close()

    await leaderboard_team()


@client.command()
@commands.has_any_role("League Admin")
async def record(ctx, *args):
    """Admin command for recording 1v1s."""

    if not ctx.channel.id == ones_channel.id:
        await ctx.send("Please only use this command in the 1v1s channel.")
        return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    games_table = "games"
    players_table = "players"

    player1 = args[0][2:-1]
    player2 = args[1][2:-1]
    print(player1, player2)

    if player1 == player2:
        await ctx.send(
            "Invalid command. Command should look like this: \n !record @player1 @player2 X-Y"
        )
        return

    if len(args[2].split("-")) != 2:
        await ctx.send(
            "Invalid command. Command should look like this: \n !record @player1 @player2 X-Y"
        )

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

    player1_wins, player2_wins = args[2].split("-")
    player1_wins = int(player1_wins)
    player2_wins = int(player2_wins)

    for result in generate_sequence(player1_wins, player2_wins):

        game_id += 1

        if result == 1:
            c.execute(
                f"INSERT INTO {games_table} VALUES(?, ?, ?, ?, ?, strftime('%s', 'now'))",
                [str(game_id), str(player1), str(player2), "won", "lost"],
            )
            player_won = player1
            player_lost = player2
        else:
            c.execute(
                f"INSERT INTO {games_table} VALUES(?, ?, ?, ?, ?, strftime('%s', 'now'))",
                [str(game_id), str(player1), str(player2), "lost", "won"],
            )
            player_won = player2
            player_lost = player1

        c.execute(
            f"SELECT elo, sigma, win, loss FROM {players_table} where ID = ?",
            [str(player_won)],
        )
        row = c.fetchone()
        elo1 = row[0]
        sigma1 = row[1]
        total_games1 = row[2] + row[3]

        c.execute(
            f"SELECT elo, sigma, win, loss FROM {players_table} where ID = ?",
            [str(player_lost)],
        )
        row = c.fetchone()
        elo2 = row[0]
        sigma2 = row[1]
        total_games2 = row[2] + row[3]

        player_won_rating, player_lost_rating = trueskill.rate_1vs1(
            trueskill.Rating(elo1, sigma1), trueskill.Rating(elo2, sigma2)
        )
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

        c.execute(
            f"UPDATE {players_table} SET win = win + 1 where ID = ?", [str(player_won)]
        )
        c.execute(
            f"UPDATE {players_table} SET streak = streak + 1 WHERE ID = ?",
            [str(player_won)],
        )
        c.execute(
            f"UPDATE {players_table} SET elo = ? where ID = ?", [elo1, str(player_won)]
        )
        c.execute(
            f"UPDATE {players_table} SET sigma = ? where ID = ?",
            [sigma1, str(player_won)],
        )

        c.execute(
            f"UPDATE {players_table} SET loss = loss + 1 where ID = ?",
            [str(player_lost)],
        )
        c.execute(
            f"UPDATE {players_table} SET streak = 0 WHERE ID = ?", [str(player_lost)]
        )
        c.execute(
            f"UPDATE {players_table} SET elo = ? where ID = ?", [elo2, str(player_lost)]
        )
        c.execute(
            f"UPDATE {players_table} SET sigma = ? where ID = ?",
            [sigma2, str(player_lost)],
        )

    c.execute(
        f"UPDATE {players_table} SET last_played_time = strftime('%s', 'now') where ID = ? or ID = ?",
        [str(player1), str(player2)],
    )
    conn.commit()
    conn.close()

    await compare(ctx, name1, name2)
    await leaderboard_solo()


@client.command()
@commands.has_any_role("League Admin")
async def delete_records(ctx, num_games):
    """Admin command for deleting last N recorded games."""

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    c.execute(
        f""" DELETE from games where ID IN (SELECT ID from games order by ID desc limit {num_games})"""
    )
    conn.commit()
    conn.close()

    await leaderboard_solo()


@client.command()
async def simulate(ctx, p1, p2, results_str):
    """Simulate elo after series of games - similar to record except the results are not actually saved. It also does not give the correct results for players with less than 20 games."""
    if not results_pattern.match(results_str):
        print("regex matching failed")
        await ctx.send(
            "Invalid command. Command should look like this (capitalization included): \n !simulate player1 player2 [1,2,1,2,2,2]"
        )
        return

    # results = [int(k) for k in results_str[1:-1].split(',')]
    try:
        results = eval(results_str)
    except:
        await ctx.send(
            "Invalid command. Command should look like this (capitalization included): \n !simulate player1 player2 [1,2,1,2,2,2]"
        )

    # print(results)

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send(
            "Results should only contains 1s and 2s representing wins for each respective team."
        )
        return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()
    t1 = find_userid_by_name(ctx, p1)
    if t1 is None:
        await ctx.send('No user found by the name "' + p1 + '"!')
        conn.close()
        return

    c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t1])
    result = c.fetchone()
    if result is None:
        await ctx.send('No user found by the name "' + p1 + '"!')
        conn.close()
        return

    name1 = result[0]
    elo1 = float(result[1])
    sigma1 = float(result[2])

    player_1_rating = trueskill.Rating(elo1, sigma1)

    t2 = find_userid_by_name(ctx, p2)
    if t2 is None:
        await ctx.send('No user found by the name "' + p2 + '"!')
        conn.close()
        return

    c.execute("SELECT name, elo, sigma FROM players where ID = ?", [t2])
    result = c.fetchone()
    if result is None:
        await ctx.send('No user found by the name "' + p2 + '"!')
        conn.close()
        return

    name2 = result[0]
    elo2 = float(result[1])
    sigma2 = float(result[2])

    player_2_rating = trueskill.Rating(elo2, sigma2)

    for result in results:
        if result == 1:
            player_1_rating, player_2_rating = trueskill.rate_1vs1(
                player_1_rating, player_2_rating
            )
        else:
            player_2_rating, player_1_rating = trueskill.rate_1vs1(
                player_2_rating, player_1_rating
            )

    s = "Simulated Elos:\n"
    s += f"{name1}: {player_1_rating.mu:.1f} (sigma={player_1_rating.sigma:.1f})\n"
    s += f"{name2}: {player_2_rating.mu:.1f} (sigma={player_2_rating.sigma:.1f})\n"

    await ctx.send(s)

    conn.close()


@client.command()
async def balance(ctx, *args):
    players_table = "players"
    if ctx.channel.id == teams_channel.id:
        players_table += "_team"

    if len(args) % 2 == 1:
        await ctx.send("Uneven number of players.")
        print("Uneven number of players")
        print(args)

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    names = []
    elos = []

    for name in args:
        id = find_userid_by_name(ctx, name)
        if id is None:
            await ctx.send('No user found by the name "' + name + '"!')
            conn.close()
            return

        c.execute("SELECT name, elo FROM players where ID = ?", [id])
        result = c.fetchone()
        if result is None:
            await ctx.send('No user found by the name "' + name + '"!')
            conn.close()
            return

        name = result[0]
        elo = float(result[1])

        names.append(name)
        elos.append(elo)

    elo_avg = np.mean(elos)
    players_per_team = len(names) // 2
    best_diff = float("inf")
    betterteam = True
    curr_names = deque()
    curr_elos = deque()
    best_names = None

    def dfs(idx=0, count=0):
        nonlocal best_names, best_diff, betterteam
        if (idx - count) < players_per_team:
            dfs(idx + 1, count)
        curr_names.append(names[idx])
        curr_elos.append(elos[idx])
        if count + 1 < players_per_team:
            dfs(idx + 1, count + 1)
        elif abs(np.mean(curr_elos) - elo_avg) < best_diff:
            betterteam = 2 - (np.mean(curr_elos) - elo_avg >= 0)
            best_diff = abs(np.mean(curr_elos) - elo_avg)
            best_names = list(curr_names)
        curr_names.pop()
        curr_elos.pop()

    dfs()

    team1 = best_names
    team2 = [n for n in names if n not in team1]

    await ctx.send(f"Team 1: {team1}, Team 2: {team2}")
    await ctx.send(
        f"Average elo difference of {best_diff*2:.2f} in favor of Team {betterteam}"
    )

    conn.close()


@client.command()
async def simulate_team(ctx, *args):
    """Simulate elo after series of games - similar to record_legacy except the results are not actually saved. It also does not give the correct results for players with less than 20 games."""
    record_info = " ".join(args)
    if not record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send(
            "Invalid command. Command should look like this (capitalization included): \n !simulate [@player1, @player2] [@player3, @player4] [1,2,1,2,2,2]"
        )
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
    results = [int(k) for k in record_info[result_start:result_end].split(",")]

    if np.any([np.any([np.array(results) > 2]), np.any(np.array(results) < 1)]):
        await ctx.send(
            "Results should only contains 1s and 2s representing wins for each respective team."
        )
        return

    ids = []
    i = 0
    team1 = []
    while i < len(team1_str):
        c = team1_str[i]
        if c == "<":
            player_id = ""
            i += 3  # <@!361548991755976704>
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

        team_won_ratings, team_lost_ratings = trueskill.rate(
            [team_won_ratings, team_lost_ratings]
        )

    if last_result != 1:
        team_won_ratings, team_lost_ratings = team_lost_ratings, team_won_ratings

    s = "Simulated Elos:\n"
    for i, t in enumerate(team1):
        s += f"<@!{t}>: {team_won_ratings[i].mu:.1f}\n"
    for i, t in enumerate(team2):
        s += f"<@!{t}>: {team_lost_ratings[i].mu:.1f}\n"

    await ctx.send(s)

    conn.close()


@client.command()
@commands.has_any_role("League Admin", "TG League Admin")
async def record_ffa(ctx, *args):
    """Admin command for recording ffa games."""
    record_info = " ".join(args)
    if not ffa_record_pattern.match(record_info):
        print("regex matching failed")
        await ctx.send(
            "Invalid command. Command should look like this (capitalization included): \n !record_ffa [@winner] [@loser1, @loser2]"
        )
        return

    winner_start = record_info.find("[")
    winner_end = record_info.find("]", winner_start) + 1
    winner_str = record_info[winner_start:winner_end]

    losers_start = record_info.find("[", winner_end)
    losers_end = record_info.find("]", losers_start) + 1
    losers_str = record_info[losers_start:losers_end]

    ids = []
    i = 0
    winner = []
    while i < len(winner_str):
        c = winner_str[i]
        if c == "<":
            player_id = ""
            i += 2  # <@!361548991755976704>
            c = winner_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = winner_str[i]
            winner.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(winner) != 1:
        await ctx.send("There should be one and only one winner.")
        await ctx.send(
            "Invalid command. Command should look like this (capitalization included): \n !record_ffa [@winner] [@loser1, @loser2]"
        )
        return

    i = 0
    losers = []
    while i < len(losers_str):
        c = losers_str[i]
        if c == "<":
            player_id = ""
            i += 2
            c = losers_str[i]
            while c != ">":
                player_id += c
                i += 1
                c = losers_str[i]
            losers.append(int(player_id))
            ids.append(int(player_id))
        i += 1
    if len(losers) == 0:
        await ctx.send("Team 2 empty.")
        return

    conn = sqlite3.connect(db_path, uri=True)
    c = conn.cursor()

    games_table = "games_ffa"
    players_table = "players_ffa"

    c.execute(f"SELECT MAX(ID) from {games_table}")
    game_id = c.fetchone()[0]
    if game_id is None:
        game_id = 0
    else:
        game_id = int(game_id)
    game_id += 1

    values = [game_id, str(winner[0]), str(losers)]
    c.execute(f"INSERT INTO {games_table} VALUES(?, ?, ?)", values)

    player_ratings = []
    for player in winner:
        c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(player)])
        row = c.fetchone()
        elo = row[0]
        sigma = row[1]
        player_ratings.append(trueskill.Rating(elo, sigma))
    for player in losers:
        c.execute(f"SELECT elo, sigma FROM {players_table} where ID = ?", [str(player)])
        row = c.fetchone()
        elo = row[0]
        sigma = row[1]
        player_ratings.append(trueskill.Rating(elo, sigma))

    ranks = [0] + [1] * len(losers)
    ranks = list(range(len(player_ratings)))

    new_player_ratings = trueskill.rate([(rating,) for rating in player_ratings], ranks)
    new_player_ratings = [rating[0] for rating in new_player_ratings]

    for i, t in enumerate(winner + losers):
        c.execute(
            f"UPDATE {players_table} SET {'win = win + 1' if i == 0 else 'loss = loss + 1'} where ID = ?",
            [str(t)],
        )
        c.execute(
            f"UPDATE {players_table} SET streak = {'streak + 1' if i == 0 else '0'} WHERE ID = ?",
            [str(t)],
        )
        c.execute(
            f"UPDATE {players_table} SET elo = ? where ID = ?",
            [new_player_ratings[i].mu, t],
        )
        c.execute(
            f"UPDATE {players_table} SET sigma = ? where ID = ?",
            [new_player_ratings[i].sigma, t],
        )

    conn.commit()
    conn.close()

    await leaderboard_ffa()


async def my_background_task():

    await client.wait_until_ready()
    print("task started")
    while True:
        await leaderboard_solo(decay=False)
        await leaderboard_team()
        await leaderboard_ffa()
        print("The leaderboards have automatically updated.")
        await asyncio.sleep(86400)  # task runs every day
    print("bot down")


@client.event
async def on_ready():
    print("Bot has now logged on")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run risk bot.")
    parser.add_argument("--token", help="discord token", required=True)

    args = parser.parse_args()

    client.loop.create_task(my_background_task())
    client.run(args.token)
