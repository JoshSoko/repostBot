# repostBot

## Description
A joke bot for Discord designed to punish people by assigning a role to users who repost within a certain timeframe or by timing out users who mention a banned word.

## Features
- Any user who posts a text message that has been posted within a certain timeframe is assigned a specific role.
- Role can be changed within Discord client.
- Certain words can be banned, and anyone who uses them will be timed out for a certain amount of time.

## Use
0. Set up a new bot on Discord's development site. Put the API token into a .env file like so: TOKEN="YOURTOKENHERE"
1. Put the bot online by running the Python script.
2. Invite the bot to your server.
3. Set the role to be assigned with '$repost setrole' command. (Ex: $repost setrole @testrole)

(NOTE: The bot can handle steps 1 and 2 interchangeably!)

### Optional Use
- Change the timeout time, in minutes, for banned words with the '$repost timeout' command.
  - Ex: $repost timeout 4
- Add or remove words to be banned (Default: 'idiot').
  - Ex: $repost add ban clown
  - Ex: $repost remove ban clown
- Add or remove words to ignore (Default: 'hey hello hi yo ^ yeah ya yea lol no nah nope').
  - Ex: $repost add word whatever
  - Ex: $repost remove word whatever
- Add or remove channels for the bot to overlook (None by default. Bot commands will still function in channels.).
  - Ex: $repost add channel #test
  - Ex: $repost remove channel #test
- Retrieve a list of banned words, exempt words, or ignored channels.
  - Ex: $repost registry ban/word/channel
- Pull up a list of these commands.
  - Ex: $repost use
- Set time for repost storage, between 0 and 90 days. (Default: 2 days.)
  - Ex: $repost length #

## Notes
- This bot exclusively checks text posts. It ignores any embeds altogether.
