from ctypes.wintypes import WORD
from datetime import datetime
from discord.ext import commands
import emoji
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
            f'file:{ctx.id}.sqlite?mode=rw', uri=True, timeout=10)
        guildCursor = guildConn.cursor()
    except sqlite3.OperationalError:
        guildConn = sqlite3.connect(f'{ctx.id}.sqlite', timeout=10)
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

# Function to write message into database
def writechat(conn, cursor, message):
    # Put time, message content, and user into database, then commit
    cursor.execute("INSERT INTO chat (date, messageDesc, memberID) VALUES (DATETIME('NOW', 'LOCALTIME'), ?, ?)",
                   (message.content, message.author.id,))
    conn.commit()


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

def channelLayout(x):
    return " <#" + x + ">\n"

def wordLayout(x):
    return " " + x + "\n"

# Functions to add new whitelisted words and whitelisted channels

async def addwordignore(ctx, cursor, conn):
    # Pull ignored word list and add to it, then put it back in the database
    ignoreWords = cursor.execute(
        "SELECT ignoreWords FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]
    newWord = ctx.message.content.split()[3]

    if newWord in ignoreWords:
        await ctx.message.channel.send("Word already in ignore list.")
        return

    ignoreWords += (" " + newWord)

    cursor.execute("UPDATE settings SET ignoreWords=? WHERE guildID=?",
                   (ignoreWords, ctx.message.guild.id))
    
    # Some formatting stuff
    ignoreWords = ignoreWords.split()
    listWords = "".join([wordLayout(x) for x in ignoreWords])
    await ctx.message.channel.send(f"Added '{newWord}' to ignored word list.\n >>> Ignoring words: ```{listWords}```")

    conn.commit()


async def addchannelignore(ctx, cursor, conn):
    # Pull ignored channel list and add to it, then put it back in the database
    ignoreChannels = cursor.execute(
        "SELECT ignoreChannels FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]
    newChannel = str(ctx.message.channel_mentions[0].id)

    if newChannel in ignoreChannels:
        await ctx.message.channel.send("Channel already in ignore list.")
        return

    if ignoreChannels == "":
        ignoreChannels = newChannel
    else:
        ignoreChannels += (" " + newChannel)

    cursor.execute("UPDATE settings SET ignoreChannels=? WHERE guildID=?",
                   (ignoreChannels, ctx.message.guild.id))

    # Some formatting stuff
    ignoreChannels = ignoreChannels.split()
    listChannels = "".join([channelLayout(x) for x in ignoreChannels])
    await ctx.message.channel.send(f"Added <#{newChannel}> to ignored channel list.\n >>> Ignoring channels:\n {listChannels}")

    conn.commit()


# Functions to delete whitelisted words and whitelisted channels
async def delwordignore(ctx, cursor, conn):
    # Pull up ignored word list and split it
    ignoreWords = cursor.execute(
        "SELECT ignoreWords FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]
    ignoreWords = ignoreWords.split()
    removeWord = ctx.message.content.split()[3]

    # If the word is in the list, remove it from the list and put the list back into the database
    if removeWord in ignoreWords:
        ignoreWords.remove(removeWord)
        ignoreWords = " ".join(ignoreWords)
        
        cursor.execute("UPDATE settings SET ignoreWords=? WHERE guildID=?",
                       (ignoreWords, ctx.message.guild.id))

        # Some formatting stuff
        ignoreWords = ignoreWords.split()
        listWords = "".join([wordLayout(x) for x in ignoreWords])
        await ctx.message.channel.send(f"Removed '{removeWord}' from ignored word list.\n >>> Ignoring words: ```{listWords}```")

        conn.commit()
        return

    # If the word isn't in the list, tell the user
    await ctx.message.channel.send("Word not found in ignored word list.")


async def delchannelignore(ctx, cursor, conn):
    # Pull up ignored channel list and split it
    ignoreChannels = cursor.execute(
        "SELECT ignoreChannels FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]
    ignoreChannels = ignoreChannels.split()
    removeChannel = str(ctx.message.channel_mentions[0].id)

    # If the word is in the list, remove it from the list and put the list back into the database
    if removeChannel in ignoreChannels:
        ignoreChannels.remove(removeChannel)
        ignoreChannels = " ".join(ignoreChannels)
        cursor.execute("UPDATE settings SET ignoreChannels=? WHERE guildID=?",
                       (ignoreChannels, ctx.message.guild.id))

        # Some formatting stuff
        ignoreChannels = ignoreChannels.split()
        listChannels = "".join([channelLayout(x) for x in ignoreChannels])
        await ctx.message.channel.send(f"Removed <#{removeChannel}> from ignored channel list.\n >>> Ignoring channels:\n {listChannels}")

        conn.commit()


async def listWord(ctx, cursor, conn):
    ignoreWords = cursor.execute(
        "SELECT ignoreWords FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]

    ignoreWords = ignoreWords.split()
    listWords = "".join([wordLayout(x) for x in ignoreWords])
    await ctx.message.channel.send(f">>> Ignoring words: ```{listWords}```")

async def listChannel(ctx, cursor, conn):
    ignoreChannels = cursor.execute(
        "SELECT ignoreChannels FROM settings WHERE guildID=?", (ctx.message.guild.id,)).fetchone()[0]

    ignoreChannels = ignoreChannels.split()
    listChannels = "".join([channelLayout(x) for x in ignoreChannels])
    await ctx.message.channel.send(f">>> Ignoring channels:\n {listChannels}")

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
        conn = sqlite3.connect('file:settings.sqlite?mode=rw', uri=True, timeout=10)
        cursor = conn.cursor()
    except sqlite3.OperationalError:
        conn = sqlite3.connect('settings.sqlite', timeout=10)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE settings (guildID INTEGER PRIMARY KEY, roleID INTEGER, ignoreChannels TEXT DEFAULT '', ignoreWords TEXT DEFAULT 'hey hello hi yo ^ yeah ya yea lol no nah nope')")

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

    # Command $repost add X will call the appropriate function
    @bot.command()
    async def add(ctx):
        try:
            funcCall = ctx.message.content.split()[2]
            if funcCall == 'word':
                await addwordignore(ctx, cursor, conn)
            if funcCall == 'channel':
                await addchannelignore(ctx, cursor, conn)
        except IndexError:
            raise commands.CommandNotFound

    # Command $repost delete X will call the appropriate function
    @bot.command()
    async def remove(ctx):
        try:
            funcCall = ctx.message.content.split()[2]
            if funcCall == 'word':
                await delwordignore(ctx, cursor, conn)
            if funcCall == 'channel':
                await delchannelignore(ctx, cursor, conn)
        except IndexError:
            raise commands.CommandNotFound

    @bot.command()
    async def registry(ctx):
        try:
            funcCall = ctx.message.content.split()[2]
            if funcCall == 'word':
                await listWord(ctx, cursor, conn)
            if funcCall == 'channel':
                await listChannel(ctx, cursor, conn)
        except IndexError:
            raise commands.CommandNotFound

    @bot.command()
    async def cleanup(ctx):
        guildConn = sqlite3.connect(
                f'file:{ctx.guild.id}.sqlite?mode=rw', uri=True, timeout=10)
        guildCursor = guildConn.cursor()
        guildCursor.execute(
            "DELETE FROM chat WHERE (date < DATETIME('now', '-30 day'))")
        await ctx.message.channel.send(f"Cleared past 30 days of logs.")
        
    @bot.command()
    async def use(ctx):
        await ctx.channel.send("```\n\
            - $repost setrole @REPOSTROLE: Set a role to be applied to the most recent reposter.\n\
            - $repost add word EXEMPTWORD: Add a word to the exemption list for reposts. \n\
            - $repost add channel #CHANNEL: Add a channel to the ignore list for reposts. \n\
            - $repost remove word EXEMPTWORD: Remove a word from the exemption list for reposts. \n\
            - $repost remove channel #CHANNEL: Remove a channel from the ignore list for reposts. \n\
            - $repost registry word/channel: List the exempt words/ignored channels. \n\```")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send("Command not found. Try typing '$repost use' for help using the bot.")

    # On message,
    @bot.event
    async def on_message(message):

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
                f'file:{message.guild.id}.sqlite?mode=rw', uri=True, timeout=10)
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
        IGNORE_CHANNELS = settings[2]
        EXEMPT_WORDS = settings[3]

        # Check for commands
        if message.author.guild_permissions.administrator == True:
            await bot.process_commands(message)

        

        # Only acknowledge whitelisted channel posts
        if str(message.channel.id) in IGNORE_CHANNELS.split():
            return

        # Ignore exempt phrases
        for i in EXEMPT_WORDS.split():
            if message.content == i:
                return

        # Weird logic to try to ignore mentions. Could probably be taken advantage of to repost, I suppose.
        if message.content.startswith("<") and message.content.endswith(">") and len(message.content.split()) == 1:
            return

        # Some logic to ignore emoji-only posts.
        # Custom emoji are formatted the same way as mentions, so there's no need for logic for them.
        messageList = emoji.demojize(message.content).split()
        res = all(each.startswith(":") and each.endswith(":") for each in messageList)
        if res == True:
            return

        if not message.content.startswith(BOT_PREFIX):
        # Check for reposts, ignoring blank messages with embeds
            if bool(message.embeds) == False:
                await repost(guildConn, guildCursor, message, ROLE_ID)
            else:
                if message.content != "":
                    await repost(guildConn, guildCursor, message, ROLE_ID)

        guildConn.close()
    # Run bot
    bot.run(TOKEN)


main()
