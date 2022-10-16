from ctypes.wintypes import WORD
from datetime import datetime
from discord.ext import commands
import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import timedelta

# Prefix for accessing the bot in Discord client
BOT_PREFIX = "$repost "

# I'm so sorry I literally can't think of a better way to do this.
# Function sets up stuff for each Discord server, or "guild"
def serverSetup(ctx, conn, cursor):

    # Create new settings row for guild in main database
    cursor.execute(
        "INSERT INTO settings (guildID) VALUES (?)", (ctx.id,))
    conn.commit()

    # Connect to server's database if it exists. Otherwise, create one.
    try:
        guildConn = sqlite3.connect(
            f'file:{ctx.id}.sqlite?mode=rw', uri=True)
        guildCursor = guildConn.cursor()
    except sqlite3.OperationalError:
        guildConn = sqlite3.connect(f'{ctx.id}.sqlite')
        guildCursor = guildConn.cursor()

        guildCursor.execute(
            "CREATE TABLE members (memberID INTEGER PRIMARY KEY, count INTEGER DEFAULT '0')")

        guildCursor.execute(
            "CREATE TABLE chat (messageID INTEGER PRIMARY KEY, date DATE, messageDesc TEXT, memberID INTEGER, FOREIGN KEY(memberID) REFERENCES members(memberID))")

        for member in ctx.members:
            guildCursor.execute(
                "INSERT INTO members (memberID) VALUES (?)", (member.id,))

        guildConn.commit()

    return guildConn, guildCursor


# Function to clear old data from chat logs
def clear(cursor, LENGTH):
    cursor.execute(
        "DELETE FROM chat WHERE (date < DATETIME('now', ?))", (LENGTH,))


# Function to write message into database
def writechat(conn, cursor, message):
    # Put time, message content, and user into database, then commit
    cursor.execute("INSERT INTO chat (date, messageDesc, memberID) VALUES (DATETIME('NOW', 'LOCALTIME'), ?, ?)",
                   (message.content, message.author.id,))
    conn.commit()


# Function to write count of timeouts in database
def writeban(conn, cursor, message):

    # Otherwise, pull up their count, add 1 to it, and update it. Also commit it.
    count = cursor.execute(
        "SELECT count FROM members WHERE memberID = ?", (message.author.id,)).fetchone()[0]
    count += 1
    cursor.execute("UPDATE members SET count=? WHERE memberID=?",
                   (count, message.author.id,))
    conn.commit()

    # We'll return the count for the announcement
    return str(count)


# Function to handle repost logic
async def repost(conn, cursor, message, ROLE_ID):
    # Assign content to variable, and then change it for images
    mes = message.content

    # Returns 0 if not a repost, 1 if a repost
    real = cursor.execute(
        "SELECT EXISTS(SELECT messageDesc FROM chat WHERE messageDesc = ?)", (mes,)).fetchone()

    # If it's a repost, announce it to the channel
    # remove the role from anyone who has it
    # and give the reposter the role
    # If it's not a repost, record post to database
    if real[0] == 0:
        writechat(conn, cursor, message)
        return

    if real[0] == 1:
        # Get the whole row into a variable
        post = cursor.execute(
            "SELECT * FROM chat WHERE messageDesc = ?", (mes,)).fetchone()
        time1, time2 = post[1].split()

        # Announcement, using row information
        await message.channel.send("Repost from " + message.author.mention + ".\n\n >>> On " + str(time1) + ", at " + str(time2) + ", <@" + str(post[3]) + "> posted: \n```" + post[2] + "```")

        # Don't do role stuff if no role is set
        if message.guild.get_role(ROLE_ID) == None:
            await message.channel.send("No repost role set!")
            return

        # Go through users with role
        role = discord.utils.get(message.guild.roles, id=ROLE_ID)

        # Extra shame if the reposter already has the role
        if role in message.author.roles:
            await message.channel.send(message.author.mention + " already has the reposter role! They're a double reposter!")
        else:
            # Removal
            try:
                for member in message.guild.members:
                    if role in member.roles:
                        await member.remove_roles(role)

                # Assignment
                await message.author.add_roles(role)
            except discord.errors.Forbidden:
                await message.channel.send("Make sure my role is higher than the repost role! Otherwise, I can't assign or remove any roles!")


# Function to time out person for saying banned word
async def wordban(conn, cursor, message, TIMEOUT_TIME):
    # How long to time out the offender
    time = timedelta(minutes=TIMEOUT_TIME)

    # The bot can't time out an admin, so we're going to raise an exception if that happens
    try:
        # Otherwise, we're going to time out the offender
        await message.author.timeout(time, reason="Timed out for saying a banned word!")
    except discord.errors.Forbidden:
        print("Admin unable to be timed out")

    # Call a function to write to the database
    count = writeban(conn, cursor, message)


    # And inform the channel of the offense
    await message.channel.send(message.author.mention + " has been timed out for saying a banned word.\nThey have said a banned word " + count + " times.")


# Functions to add new banned words, whitelisted words, and whitelisted channels
async def addwordban(ctx, cursor, conn):
    # Pull banned word list and add to it, then put it back in the database
    bannedWords = cursor.execute(
        "SELECT wordban FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]
    newWord = ctx.message.content.split()[3]
    bannedWords += (" " + newWord)
    await ctx.message.channel.send(f"Added {newWord} to banned word list. {bannedWords}.")
    cursor.execute("UPDATE settings SET wordban=? WHERE guildID=?",
                   (bannedWords, ctx.message.guild.id))
    conn.commit()


async def addwordignore(ctx, cursor, conn):
    return


async def addchannelignore(ctx, cursor, conn):
    return


# Functions to delete banned words, whitelisted words, and whitelisted channels
async def delwordban(ctx, cursor, conn):
    # Pull up banned word list and split it
    bannedWords = cursor.execute(
        "SELECT wordban FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]
    bannedWords = bannedWords.split()
    removeWord = ctx.message.content.split()[3]

    # If the word is in the list, remove it from the list and put the list back into the database
    if removeWord in bannedWords:
        bannedWords.remove(removeWord)
        bannedWords = " ".join(bannedWords)
        await ctx.message.channel.send(f"Removed {removeWord} from banned word list. {bannedWords}.")
        cursor.execute("UPDATE settings SET wordban=? WHERE guildID=?",
                       (bannedWords, ctx.message.guild.id))
        conn.commit()
        return

    # If the word isn't in the list, tell the user
    await ctx.message.channel.send("Word not found in banned word list.")


async def delwordignore(ctx, cursor, conn):
    return


async def delchannelignore(ctx, cursor, conn):
    return


def main():

    # Tell Discord the bot intents
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.message_content = True
    intents.members = True

    # Pull info from .env file
    load_dotenv()
    TOKEN = os.getenv('TOKEN')

    # Set bot as Discord client
    bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

    # Load up database; create database and tables if they doesn't exist.
    try:
        conn = sqlite3.connect('file:settings.sqlite?mode=rw', uri=True)
        cursor = conn.cursor()
    except sqlite3.OperationalError:
        conn = sqlite3.connect('settings.sqlite')
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE settings (guildID INTEGER PRIMARY KEY, roleID INTEGER, length TEXT DEFAULT '-2 days', wordban TEXT DEFAULT 'idiot', timeout INTEGER DEFAULT '2', ignoreChannels TEXT, ignoreWords TEXT DEFAULT 'hey hello hi yo ^ yeah ya yea lol no nah nope')")

    # On launch, print to console
    @bot.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(bot))

    # On joining a guild, make the guild a database
    @bot.event
    async def on_guild_join(joined):

        # Create new settings row for guild in main database
        serverSetup(joined, conn, cursor)

    # Command to set the reposter role
    @bot.command()
    async def setrole(ctx):
        try:
            ROLE_ID = ctx.message.role_mentions[0].id
            cursor.execute("UPDATE settings SET roleID=? WHERE guildID=?",
                           (ROLE_ID, ctx.message.guild.id,))
            await ctx.message.channel.send(f"Updated reposter role to <@&{ROLE_ID}>.")
            conn.commit()
        except IndexError:
            return

    # Command to set auto-timeout time
    @bot.command()
    async def timeout(ctx):
        try:
            timelimit = ctx.message.content.split()[2]
            if timelimit.isnumeric():
                TIMEOUT_TIME = int(timelimit)
                cursor.execute("UPDATE settings SET timeout=? WHERE guildID=?",
                               (TIMEOUT_TIME, ctx.message.guild.id,))
                await ctx.message.channel.send(f"Timeout time for banned words set to {TIMEOUT_TIME} minutes.")
                conn.commit()
        except IndexError:
            return

    # Command $repost add X will call the appropriate function
    @bot.command()
    async def add(ctx):
        try:
            funcCall = ctx.message.content.split()[2]
            if funcCall == 'banned':
                await addwordban(ctx, cursor, conn)
            if funcCall == 'word':
                await addwordignore(ctx, cursor, conn)
            if funcCall == 'channel':
                await addchannelignore(ctx, cursor, conn)
        except IndexError:
            return

    # Command $repost delete X will call the appropriate function
    @bot.command()
    async def delete(ctx):
        try:
            funcCall = ctx.message.content.split()[2]
            if funcCall == 'banned':
                await delwordban(ctx, cursor, conn)
            if funcCall == 'word':
                await delwordignore(ctx, cursor, conn)
            if funcCall == 'channel':
                await delchannelignore(ctx, cursor, conn)
        except IndexError:
            return

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send("Command not found.")

    # On message,
    @bot.event
    async def on_message(message):

        # Check for commands
        await bot.process_commands(message)

        # Ignore if this bot sent it
        if message.author == bot.user:
            return

        # Check if server has settings and a database
        serverExist = cursor.execute(
            "SELECT EXISTS(SELECT guildID FROM settings WHERE guildID = ?)", (message.guild.id,)).fetchone()

        # If 1, load them up. If 0, make them.
        if serverExist[0] == 1:
            settings = (cursor.execute(
                "SELECT * FROM settings WHERE guildID = ?", (message.guild.id,))).fetchall()[0]
            guildConn = sqlite3.connect(
                f'file:{message.guild.id}.sqlite?mode=rw', uri=True)
            guildCursor = guildConn.cursor()
        else:
            guildConn, guildCursor = serverSetup(message.guild, conn, cursor)
            settings = (cursor.execute(
                "SELECT * FROM settings WHERE guildID = ?", (message.guild.id,))).fetchall()[0]

        # Check if poster exists in database
        memberExist = guildCursor.execute(
            "SELECT EXISTS(SELECT memberID FROM members WHERE memberID = ?)", (message.author.id,)).fetchone()

        # Add them if they don't
        if memberExist[0] == 0:
            guildCursor.execute(
                "INSERT INTO members (memberID) VALUES (?)", (message.author.id,))

        # Load options into variables
        ROLE_ID = settings[1]
        DELETE_TIME = settings[2]
        BANNED_WORDS = settings[3]
        TIMEOUT_TIME = settings[4]
        IGNORE_CHANNELS = str(settings[5])
        EXEMPT_WORDS = settings[6]

        # Only acknowledge whitelisted channel posts
        if message.channel.id in IGNORE_CHANNELS.split():
            return

        # Ignore exempt phrases
        for i in EXEMPT_WORDS.split():
            if message.content == i:
                return


        # Whenever a message is sent, clear anything that's too old in the chat database.
        clear(guildCursor, DELETE_TIME)

        if not message.content.startswith(BOT_PREFIX):
            # Check for banned word
            for i in BANNED_WORDS.split():
                if i in message.content:
                    await wordban(guildConn, guildCursor, message, TIMEOUT_TIME)

            # Check for reposts
            if message.content != "":
                await repost(guildConn, guildCursor, message, ROLE_ID)

    # Run bot
    bot.run(TOKEN)


main()
