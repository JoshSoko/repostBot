# repostBot

## Description
A joke bot for Discord designed to punish people by assigning a role to users who repost within a certain timeframe or by timing out users who mention a banned word.

## Features
- Any user who posts a text message that has been posted within a certain timeframe is assigned a specific role.
- Role can be changed within Discord client.
- Certain words can be banned, and anyone who uses them will be timed out for a certain amount of time.

## Use

0. Set up a new bot on Discord's development site. Put the API token into a .env file like so: TOKEN="YOURTOKENHERE"
1. Put the bot online by running the Python script. (The bot will only create a new database for a server upon joining)
2. Invite the bot to your server.
3. Set the role to be assigned with '$repost setrole' command. (Ex: $repost setrole @testrole)

### Optional Use
- Change the timeout time, in minutes, for banned words with the '$repost timeout' command.
  - Ex: $repost timeout 4
- Add or delete words to be banned (default: 'idiot')
  - Ex: $repost add banned clown
  - Ex: $repost delete banned clown

### Future Features
- Currently transitioning from settings kept on a separate file to settings kept on database. Because of this, the following settings don't work:
  - Setting exempt words
  - Setting channels for the bot to ignore


## Known Bugs
- Gifs, mentions, and emoji-only posts trigger the bot
