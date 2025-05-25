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