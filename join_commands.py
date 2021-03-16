from discord.ext import tasks

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

# Lists and Variables

PLAYERS = []
PLAYERS2 = []
PLAYERS3 = []
repeat_list = []
no_score = []

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
    '''Admin command for ending the current lobby.'''

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
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        c.execute("SELECT elo FROM players_team WHERE ID = ?", [t])
        mon = c.fetchone()

        if mon == None:
            c.execute('INSERT INTO players_team VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, NULL, 400)',
                    [t, n, "Empty", date])
            await ctx.channel.send("You are now registered.")
            role = discord.utils.get(ctx.guild.roles, name="League")
            await member.add_roles(role)
            conn.commit()

        c.execute("SELECT ID, name, elo FROM players_team where ID = ?", [t])
        creator = ctx.message.author.name
        results = c.fetchone()
        ids = results[0]
        pts = int(round(results[2]))

        c = conn.cursor()

        c.execute("SELECT currentg FROM players_team WHERE ID = ?", [t])

        if gametype == None:

            if t in PLAYERS2:
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME2 and c.fetchone()[0] is None:

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
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        c.execute("SELECT elo FROM players_team WHERE ID = ?", [t])
        mon = c.fetchone()

        if mon == None:
            c.execute('INSERT INTO players_team VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, NULL, 400)',
                    [t, n, "Empty", date])
            await ctx.channel.send("You are now registered.")
            role = discord.utils.get(ctx.guild.roles, name="League")
            await member.add_roles(role)
            conn.commit()

        c.execute("SELECT ID, name, elo FROM players_team where ID = ?", [t])
        creator = ctx.message.author.name
        results = c.fetchone()
        ids = results[0]
        pts = int(round(results[2]))

        c = conn.cursor()

        c.execute("SELECT currentg FROM players_team WHERE ID = ?", [t])

        if gametype == None:

            if t in PLAYERS3:
                joined_dic[t] = gettime()
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME3 and c.fetchone()[0] is None:

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
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        c.execute("SELECT elo FROM players WHERE ID = ?", [t])
        mon = c.fetchone()

        if mon == None:
            c.execute('INSERT INTO players VALUES(?, ?, 0, 0, 1500, NULL, 0, 0, 0, 0, ?, 0, ?, 0, NULL, 400)',
                    [t, n, "Empty", date])
            await ctx.channel.send("You are now registered.")
            role = discord.utils.get(ctx.guild.roles, name="League")
            await member.add_roles(role)
            conn.commit()

        c.execute("SELECT ID, name, elo FROM players where ID = ?", [t])
        creator = ctx.message.author.name
        results = c.fetchone()
        ids = results[0]
        pts = int(round(results[2]))

        c = conn.cursor()

        c.execute("SELECT currentg FROM players WHERE ID = ?", [t])
        Y = c.fetchone()[0]
        if Y is not None:
            await ctx.send("You're still in a game.")
            return

        c.execute("SELECT currentg FROM players WHERE ID = ?", [t])

        if gametype == None:

            if t in PLAYERS:
                await ctx.channel.send("You're already in the lobby.")
                return

            if GAME and c.fetchone()[0] is None:

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

            if GAME and c.fetchone()[0] is None:

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

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def noscore(ctx):
    """Shows list of players that haven't voted on latest game."""

    global no_score

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for game_id in c.execute("SELECT MAX(ID) FROM GAMES"):
        game_ID = (game_id[0])
        
    await ctx.send("**Game #" + str(game_ID) + "**: " + ', '.join(no_score))

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