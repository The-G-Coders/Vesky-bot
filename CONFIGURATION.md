# Startup configuration

## Required environment variables

- **TOKEN** - Discord bot token
- **DATABASE_URL** - The url of a mongoDB database
- **DATABASE** - The name of the database to use
- **SHUTDOWN_PASSWORD** - The password used to shut down the bot
- **DEBUG_GUILD_ID** - The guild ID of the guild to use
- **POLL_CHANNEL_ID** - The channel ID of the channel to use for polls
- **ANNOUNCEMENTS_CHANNEL_ID** - The channel ID of the channel to use for announcements
- **BOT_CATEGORY_ID** - The category ID of the category to use for the bot commands

##### Boolean values, set to `true` or `anything else but null`

- **EVENTS** - Whether to load the events module
- **SLOWMODE** - Whether to load the slowmode module
- **POLLS** - Whether to load the polls module
- **UTILS** - Whether to load the utils module

#### OR

- **ENV_FILE** - Path to a file containing the required environment variables(eg. **relative**: `resources/.env` or **absolute**: `/home/user/.env`)
