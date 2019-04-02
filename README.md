# TwitchPackCounter
Twitch Bot to keep track of gift subscriptions

---
# Note
This Bot was written for one streamer in particular, which means this script likely will not be useful to anyone else, but people interested in checking out how I use my [TwitchWebsocket](https://github.com/CubieDev/TwitchWebsocket) library.

---
# Functionality
This Bot will return the amount of gifted subscriptions divided by 5, rounded down, upon using the command "!packs".

It also returns who the gifters are in the command "!details".

As of right now, data is stored merely in memory, meaning that if the program crashes the data is lost. In the future this may be changed if it is requested by the streamer in question.

---

# Settings
This bot is controlled by a settings.txt file, which looks like:
```
{
    "Host": "irc.chat.twitch.tv",
    "Port": 6667,
    "Channel": "#<channel>",
    "Nickname": "<name>",
    "Authentication": "oauth:<auth>"
}
```

| **Parameter**        | **Meaning** | **Example** |
| -------------------- | ----------- | ----------- |
| Host                 | The URL that will be used. Do not change.                         | "irc.chat.twitch.tv" |
| Port                 | The Port that will be used. Do not change.                        | 6667 |
| Channel              | The Channel that will be connected to.                            | "#CubieDev" |
| Nickname             | The Username of the bot account.                                  | "CubieB0T" |
| Authentication       | The OAuth token for the bot account.                              | "oauth:pivogip8ybletucqdz4pkhag6itbax" |

*Note that the example OAuth token is not an actual token, but merely a generated string to give an indication what it might look like.*

I got my real OAuth token from https://twitchapps.com/tmi/.

---

# Other Twitch Bots

* [TwitchGoogleTranslate](https://github.com/CubieDev/TwitchGoogleTranslate)
* [TwitchCubieBot](https://github.com/CubieDev/TwitchCubieBot)
* [TwitchPickUser](https://github.com/CubieDev/TwitchPickUser)
* [TwitchDialCheck](https://github.com/CubieDev/TwitchDialCheck) (Streamer specific bot)
