# repostBot

## Description
A joke bot for Discord designed to punish people by assigning a role to users who repost within a certain timeframe or by timing out users who mention a banned word.

## Features
- Any user who posts a text message that has been posted within a certain timeframe is assigned a specific role.
- Role can be changed within Discord client.
- Certain words can be banned, and anyone who uses them will be timed out for a certain amount of time.

### Future Features
- Currently transitioning from settings kept on a separate file to settings kept on database. Because of this, the following settings don't work:
  - Changing the banned words
  - Setting exempt words
  - Changing the time for database purging
  - Changing punishment timeout
  - Setting channels for the bot to ignore


## Known Bugs
- Gifs, mentions, and emoji-only posts trigger the bot



## Requirements
Requires a .env file with a variable TOKEN assigned to an API key.
