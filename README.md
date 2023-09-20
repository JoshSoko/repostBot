# repostBot

## Description
A joke bot for Discord designed to punish people by assigning a role to users who repost within a certain timeframe.

## Features
- Any user who posts a text message that has been posted within a certain timeframe is assigned a specific role.
- Role can be changed within Discord client.

## Use
0. Set up a new bot on Discord's development site. Put the API token into a .env file like so: TOKEN="YOURTOKENHERE"
1. Put the bot online by running the Python script.
2. Invite the bot to your server.
3. Set the role to be assigned with '$repost setrole' command. (Ex: $repost setrole @testrole)

(NOTE: The bot can handle steps 1 and 2 interchangeably!)

### Optional Use
- Add or remove words to ignore (Default: 'hey hello hi yo ^ yeah ya yea lol no nah nope').
  - Ex: $repost add word whatever
  - Ex: $repost remove word whatever
- Add or remove channels for the bot to overlook (None by default. Bot commands will still function in channels.).
  - Ex: $repost add channel #test
  - Ex: $repost remove channel #test
- Retrieve a list of exempt words or ignored channels.
  - Ex: $repost registry word/channel
- Pull up a list of these commands.
  - Ex: $repost use
- Clear anything out of database older than 30 days old
  - Ex: $repost cleanup

## Notes
- This bot exclusively checks text posts. It ignores any embeds altogether.
- Originally, you could set a custom timeframe and every time on_message would trigger, it would clear out messages from before that time. This bottlenecked sqlite too frequently, and switching sql databases would be outside the scope of this project.
