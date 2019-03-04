
from TwitchWebsocket import TwitchWebsocket
import random, time, json, sqlite3

class Settings:
    def __init__(self, bot):
        try:
            # Try to load the file using json.
            # And pass the data to the GoogleTranslate class instance if this succeeds.
            with open("settings.txt", "r") as f:
                settings = f.read()
                data = json.loads(settings)
                bot.setSettings(data['Host'],
                                data['Port'],
                                data['Channel'],
                                data['Nickname'],
                                data['Authentication'])
        except ValueError:
            raise ValueError("Error in settings file.")
        except FileNotFoundError:
            # If the file is missing, create a standardised settings.txt file
            # With all parameters required.
            with open('settings.txt', 'w') as f:
                standard_dict = {
                                    "Host": "irc.chat.twitch.tv",
                                    "Port": 6667,
                                    "Channel": "#<channel>",
                                    "Nickname": "<name>",
                                    "Authentication": "oauth:<auth>",
                                }
                f.write(json.dumps(standard_dict, indent=4, separators=(',', ': ')))
                raise ValueError("Please fix your settings.txt file that was just generated.")

class Database:
    def __init__(self):
        self.create_db()
    
    def create_db(self):
        sql = """
        CREATE TABLE IF NOT EXISTS BitMessages (
            full_message TEXT PRIMARY KEY,
            tags TEXT,
            command TEXT,
            user TEXT,
            type TEXT,
            params TEXT,
            channel TEXT,
            message TEXT)
        """
        self.execute(sql)

    def execute(self, sql, values=None, fetch=False):
        with sqlite3.connect("Message.db") as conn:
            cur = conn.cursor()
            if values is None:
                cur.execute(sql)
            else:
                cur.execute(sql, values)
            conn.commit()
            if fetch:
                return cur.fetchall()
    
    def add_item(self, *args):
        self.execute("INSERT INTO BitMessages(full_message, tags, command, user, type, params, channel, message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", args)

class PackCounter:
    def __init__(self):
        self.host = None
        self.port = None
        self.chan = None
        self.nick = None
        self.auth = None
        self.gifts = {'ButtonsDuckman': 1.0, 'TEditsV1': 1.0}
        
        # Fill previously initialised variables with data from the settings.txt file
        Settings(self)

        self.db = Database()

        self.ws = TwitchWebsocket(self.host, self.port, self.message_handler, live=True)
        self.ws.login(self.nick, self.auth)
        #for chan in ["ninja", "Gotaga", "Gaules", "MontanaBlack88", "Lirik", "mckyTV", "forsen", "rekkies", "cloakzy", "SolaryFortnite", "Nickmercs", "cohhcarnage", "Pow3Rtv", "Greekgodx"]:
        #    self.ws.join_channel(chan)
        self.ws.join_channel(self.chan)
        self.ws.add_capability(["tags", "commands"])

    def setSettings(self, host, port, chan, nick, auth):
        self.host = host
        self.port = port
        self.chan = chan
        self.nick = nick
        self.auth = auth

    def message_handler(self, m):
        if m.type == "USERNOTICE":
            # If message is of an (anon)subgift, add the tier of it to a counter.
            if m.tags["msg-id"] in ["subgift", "anonsubgift"]:
                if m.tags["display-name"] in self.gifts:
                    self.gifts[m.tags["display-name"]] += int(m.tags["msg-param-sub-plan"]) / 1000
                else:
                    self.gifts[m.tags["display-name"]] = int(m.tags["msg-param-sub-plan"]) / 1000
                from pprint import pprint
                pprint(self.gifts)

                # For testing purposes also add it to a database
                self.add_message_to_db(m)

            elif m.tags["msg-id"] not in ["sub", "resub", "raid", "ritual", "submysterygift", "anongiftpaidupgrade", "giftpaidupgrade"]:
                print(m)
                self.add_message_to_db(m)
        
        elif m.type == "PRIVMSG":
            if m.message.startswith(("!packs", "!packcounter")):
                # Get total amount of gift subscriptions
                total = sum([self.gifts[key] for key in self.gifts])

                # Perform integer division to get total divided by 5, rounded down
                packs = total // 5

                # Send to twitch chat
                print(f"Pack Counter: {packs}")
                self.ws.send_message(f"Pack Counter: {packs:.0f}")

            elif m.message.startswith(("!details", "!packdetails")):
                # Get output in the form of 
                # User: 3, User: 5, User: 2
                output = ", ".join([f"{key}: {self.gifts[key]:.0f}" for key in self.gifts])
                
                # Send to twitch chat
                print(output)
                self.ws.send_message(output)

    def add_message_to_db(self, m):
        self.db.add_item(m.full_message, json.dumps(m.tags), m.command, m.user, m.type, m.params, m.channel, m.message)

if __name__ == "__main__":
    PackCounter()

#if m.type not in ["PRIVMSG", "MODE", "CAP * ACK", "353", "PART", "JOIN", "366", "CLEARCHAT", "CLEARMSG", "001", "002", "003", "004", "375", "376", "372"]:
#    print(m)