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

@client.command()
@commands.has_any_role('League Admin', 'Primary Developer')
async def forcejoin(ctx, player):
    '''Forcejoins a user into the lobby.'''

    global PLAYERS, PLAYERS2, PLAYERS3, GAME, GAME2, GAME3, RUNNING, RUNNING2, RUNNING3, db_path, joined_dic

    if ctx.channel.id == ones_channel.id:

        t = ctx.message.author.id
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        player = find_userid_by_name(ctx, player)
        if player is None:
            await ctx.channel.send("No user found by that name.")
            return
        c.execute("SELECT name FROM players WHERE ID = ?", [player])
        user = c.fetchone()
        name = user[0]

        if GAME:
            PLAYERS = list(set(PLAYERS))
            PLAYERS.append(player)
            joined_dic[player] = gettime()

            await ctx.channel.send(f"**{name}** was forced into the lobby.")

        conn.commit()
        conn.close()

    if ctx.channel.id == twos_channel.id:

        t = ctx.message.author.id
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        player = find_userid_by_name(ctx, player)
        if player is None:
            await ctx.channel.send("No user found by that name.")
            return
        c.execute("SELECT name FROM players_team WHERE ID = ?", [player])
        user = c.fetchone()
        name = user[0]

        if GAME2:
            PLAYERS2 = list(set(PLAYERS2))
            PLAYERS2.append(player)
            joined_dic[player] = gettime()

            await ctx.channel.send(f"**{name}** was forced into the lobby.")

        conn.commit()
        conn.close()

    if ctx.channel.id == threes_channel.id:

        t = ctx.message.author.id
        conn = sqlite3.connect(db_path, uri=True)
        c = conn.cursor()
        player = find_userid_by_name(ctx, player)
        if player is None:
            await ctx.channel.send("No user found by that name.")
            return
        c.execute("SELECT name FROM players_team WHERE ID = ?", [player])
        user = c.fetchone()
        name = user[0]

        if GAME3:
            PLAYERS3 = list(set(PLAYERS3))
            PLAYERS3.append(player)
            joined_dic[player] = gettime()

            await ctx.channel.send(f"**{name}** was forced into the lobby.")

        conn.commit()
        conn.close()


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def dm(ctx):

    """Add or remove direct messaging notifications for games."""

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    t = ctx.author.id
    n = ctx.author.name
    c.execute("SELECT name FROM DM WHERE ID = ?", [t])
    check = c.fetchone()

    if check is None:
        
        c.execute("INSERT into DM VALUES (?,?)", [t,n])
        await ctx.send("Enabled direct messaging.")
        conn.commit()
        conn.close()
    
    if check is not None:
    
        c.execute("DELETE from DM WHERE ID = ?", [t])
        await ctx.send("Disabled direct messaging.")
        conn.commit()
        conn.close()

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def mute(ctx, name):
    '''Mutes a user from the channel.'''
    
    global joined_dic

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        activity_channel = ctx.guild.get_channel(790313358816968715)
        n = ctx.author.name
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return
        c.execute("SELECT name, ID FROM players where ID = ?", [t])
        player = c.fetchone()
        names = player[0]
        ids = player[1]
        member = ctx.guild.get_member(ids)
        banjo_role = discord.utils.get(ctx.guild.roles, name="League")
        await member.remove_roles(banjo_role)
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.add_roles(muted_role)
        await ctx.send("**" + str(names) + "** was muted by **" + str(n) + "**.")
        await activity_channel.send("**" + str(names) + "** was muted by **" + str(n) + "**.")

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def unmute(ctx, name):
    '''Unmutes a user from the channel.'''

    global joined_dic

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        n = ctx.author.name
        activity_channel = ctx.guild.get_channel(790313358816968715)
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return
        c.execute("SELECT name, ID FROM players where ID = ?", [t])
        player = c.fetchone()
        names = player[0]
        ids = player[1]
        member = ctx.guild.get_member(ids)
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.remove_roles(muted_role)
        banjo_role = discord.utils.get(ctx.guild.roles, name="League")
        await member.add_roles(banjo_role)
        await ctx.send("**" + str(names) + "** was unmuted by **" + str(n) + "**.")
        await activity_channel.send("**" + str(names) + "** was unmuted by **" + str(n) + "**.")

@client.command()
async def members(ctx):

    guild = ctx.guild
    for member in guild.members:
        print(member)

@client.command()
async def signup(ctx):

    """Tournament signups."""

    t = ctx.author.id
    name = ctx.author.name
    date = datetime.datetime.now()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:

        c.execute("SELECT name FROM tournament WHERE ID = ?", [t])
        row = c.fetchone()[0]

    except:
            
        await ctx.send("What position would you like to play? (Options: GoalKeeper, Defense, Offense, Mobility)")

        def check(message):
            return message.channel == ctx.channel and message.author.id == int(t)

        try:

            message = await client.wait_for('message', timeout=30, check=check)

            position = message.content
            print(position)

            c.execute("INSERT INTO tournament VALUES (?,?,?,?)", [t,name,position,date])
            conn.commit()
            conn.close()

            await ctx.send(f"You are now signed up as **{name}** and the position you applied for was **{position}**!")

        except asyncio.TimeoutError:

            error_msg2 = await ctx.send("Oops! Too late.")
            await error_msg2.edit(delete_after=5)
            return

    else:

        await ctx.send("You have already signed up!")

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def ban(ctx, name, *, reason):
    '''Bans a user from the channel.'''

    global joined_dic

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()   
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        activity_channel = ctx.guild.get_channel(790313358816968715)
        n = ctx.author.name
        t = find_userid_by_name(ctx, name)
        reasons = "{}".format(reason)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return
        c.execute("SELECT name, ID FROM players where ID = ?", [t])
        player = c.fetchone()
        names = player[0]
        ids = player[1]
        member = ctx.guild.get_member(ids)
        banned_role = discord.utils.get(ctx.guild.roles, name="Banned")
        await member.add_roles(banned_role)
        banjo_role = discord.utils.get(ctx.guild.roles, name="Banjo")
        await member.remove_roles(banjo_role)
        await ctx.send("**" + str(names) + "** was banned for " + str(reasons) + " by **" + str(n) + "**.")
        await activity_channel.send("**" + str(names) + "** was banned for " + str(reasons) + " by **" + str(n) + "**.")


@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role('League Admin')
async def unban(ctx, name):
    '''Unbans a user from the channel.'''

    global joined_dic

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()     
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        n = ctx.author.name
        activity_channel = ctx.guild.get_channel(790313358816968715)
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return
        c.execute("SELECT name, ID FROM players where ID = ?", [t])
        player = c.fetchone()
        names = player[0]
        ids = player[1]
        member = ctx.guild.get_member(ids)
        banned_role = discord.utils.get(ctx.guild.roles, name="Banned")
        await member.remove_roles(banned_role)
        banjo_role = discord.utils.get(ctx.guild.roles, name="Banjo")
        await member.add_roles(banjo_role)
        await ctx.send("**" + str(names) + "** was unbanned by **" + str(n) + "**.")
        await activity_channel.send("**" + str(names) + "** was unbanned by **" + str(n) + "**.")

@client.command()
async def stats(ctx):
    '''Shows a players statistics.'''

    global db_path, joined_dic

    if ctx.channel.id == na_lobby_channel.id or ctx.channel.id == admin_channel.id:

        x = ctx.author.id
        joined_dic[x] = gettime()
            
        name = str(ctx.message.content)[7:]
        t = find_userid_by_name(ctx, name)
        if t is None:
            await ctx.channel.send("No user found by that name!")
            return

        conn = sqlite3.connect(db_path, uri=True)

        c = conn.cursor()
        c.execute("SELECT name, elo, win, loss, streak, profile, fresh_warns, record, perms, rank FROM players where ID = ?", [t])
        player = c.fetchone()

        if player is not None:
            name = player[0]
            pts = player[1]
            win = player[2]
            loss = player[3]
            streak = player[4]
            warns = player[6]
            peak = player[7]
            description = player[8]
            rank = player[9]
            total_games = win + loss
            c.execute("SELECT total_warns FROM warnings WHERE ID = ?", [t])
            warnings = c.fetchone()[0]

            grandmaster = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grandmaster.png"
            master = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/master.png"
            adept = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/adept.png""
            diamond = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/diamond.png"
            platinum = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/platinum.png"
            gold = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/gold.png"
            silver = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/silver.png"
            bronze = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/bronze.png"
            grass = "https://raw.githubusercontent.com/KaramAbuaisha/Risk-bot/clean/assets/league-icons/grass.png"


            if streak > 0:
                streak = f"{streak}"
            if total_games == 0:
                await ctx.channel.send(name + " played no games and has an elo of **" + str(pts) + "**.")

            if rank < 3:
                url = grandmaster
                emoji = "<:0_:799828770110439425>"

            if rank > 2 < 7:
                url = master
                emoji = "<:1_:799828770402861146>"
            
            if rank > 6 < 13:
                url = diamond
                emoji = "<:2_:799828770470363136>"

            if rank > 11 < 20:
                url = platinum
                emoji = "<:3_:799828770100871220>"

            if rank > 19 < 26:
                url = gold
                emoji = "<:4_:799828770541928478>"

            if rank > 24 < 31:
                url = silver
                emoji = "<:5_:799828770562244639>"
            
            if rank > 29:
                url = bronze
                emoji = "<:6_:799828770651111445>"

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT p1,p2,p3,p4,p5,p6,p7,p8,id,s1,s2 FROM games WHERE (p1 == ? OR p2 == ? or p3 == ? or p4 == ? or p5 == ? or p6 == ? or p7 == ? or p8 == ?) AND (s1 is not NULL or s2 is not NULL) ORDER BY ID DESC LIMIT 10", [t,t,t,t,t,t,t,t])
            recent_games = c.fetchall()

            recent_perf = ""

            # for emoji in ctx.guild.emojis:
            #     print(f"{emoji.id} - {emoji.name}")

            for items in recent_games:
                team = 1 if t in items[0:4] else 2
                s1 = items[9]
                s2 = items[10]
                if team == 1:
                    if s1 > s2:
                        recent_perf += "W"
                    else:
                        recent_perf+= "L"
                                    
                else:
                    if s2 > s1:
                        recent_perf += "W"
                    else:
                        recent_perf += "L"

            rp = "-".join(recent_perf)

            if int(streak) > 0:
                streak = f"{streak}"

            if total_games == 0:
                await ctx.channel.send(name + " played no games and has an elo of **" + str(pts) + "**.")

            else:
                winrate = float("{0:.2f}".format((win / total_games) * 100)) 
                embed = discord.Embed(
                    colour=0x1F1E1E
                )
                embed.set_thumbnail(url=f"{url}")
                embed.add_field(name=f"{name} {emoji}\n\u200b",
                                value=f"RANK: **{rank}** | **{win}**W-**{loss}**L **{winrate}**%\n\nRecent Performance:\n{rp}",
                                inline=False)
                embed.add_field(name='\n\u200b', value=f'ELO: **{pts}**')
                embed.add_field(name='\n\u200b', value=f'Peak: **{peak}**')
                await ctx.send(embed=embed)

        else:
            await ctx.channel.send("No user found by that name!")

        conn.commit()
        conn.close()

def isName(memberName, member):
    name = member.display_name
    name = name.upper()
    pattern = re.compile('[\W_]+')
    if memberName.upper() in pattern.sub('', name).upper():
        return True
    else:
        return False