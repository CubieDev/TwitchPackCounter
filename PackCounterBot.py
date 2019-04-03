
from TwitchWebsocket import TwitchWebsocket
import random, time, json, sqlite3, logging, os

class Logging:
    def __init__(self):
        # Either of the two will be empty depending on OS
        prefix = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1]) + "\\".join(os.path.dirname(os.path.realpath(__file__)).split("\\")[:-1]) 
        prefix += "/Logging/"
        try:
            os.mkdir(prefix)
        except FileExistsError:
            pass
        log_file = prefix + os.path.basename(__file__).split('.')[0] + ".txt"
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        # Spacer
        logging.info("")

class Settings:
    def __init__(self, bot):
        logging.debug("Loading settings.txt file...")
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
                                data['Authentication'],
                                data["ClearAllowedUsers"],
                                data["ClearAllowedRanks"])
                logging.debug("Settings loaded into Bot.")
        except ValueError:
            logging.error("Error in settings file.")
            raise ValueError("Error in settings file.")
        except FileNotFoundError:
            # If the file is missing, create a standardised settings.txt file
            # With all parameters required.
            logging.error("Please fix your settings.txt file that was just generated.")
            with open('settings.txt', 'w') as f:
                standard_dict = {
                                    "Host": "irc.chat.twitch.tv",
                                    "Port": 6667,
                                    "Channel": "#<channel>",
                                    "Nickname": "<name>",
                                    "Authentication": "oauth:<auth>",
                                    "ClearAllowedUsers": [],
                                    "ClearAllowedRanks": ["moderator", "broadcaster"]
                                }
                f.write(json.dumps(standard_dict, indent=4, separators=(',', ': ')))
            raise ValueError("Please fix your settings.txt file that was just generated.")

class Database:
    # Using sqlite for simplicity, even though it doesn't store my dict in a convenient matter.
    def __init__(self):
        self.create_db()
    
    def create_db(self):
        sql = """
        CREATE TABLE IF NOT EXISTS PackCounter (
            gifter TEXT,
            recipient TEXT,
            tier INTEGER,
            time INTEGER
        )
        """
        logging.debug("Creating Database...")
        self.execute(sql)
        logging.debug("Database created.")

    def execute(self, sql, values=None, fetch=False):
        with sqlite3.connect("PackCounter.db") as conn:
            cur = conn.cursor()
            if values is None:
                cur.execute(sql)
            else:
                cur.execute(sql, values)
            conn.commit()
            if fetch:
                return cur.fetchall()
    
    def add_item(self, *args):
        try:
            logging.info(f"{args[0]} gifted {args[1]} a tier {args[2]}")
        except UnicodeEncodeError:
            try:
                logging.info(f"{args[0]} gifted ... a tier {args[2]}")
            except UnicodeEncodeError:
                logging.info(f"... gifted {args[1]} a tier {args[2]}")
        self.execute("INSERT INTO PackCounter(gifter, recipient, tier, time) VALUES (?, ?, ?, ?)", args)
    
    def get_total(self):
        return self.execute("SELECT SUM(tier) FROM PackCounter;", fetch=True)[0][0]
    
    def get_grouped_total(self):
        return self.execute("SELECT gifter, SUM(tier) FROM PackCounter GROUP BY gifter;", fetch=True)

    def clear(self):
        # Deletes all items
        self.execute("DELETE FROM PackCounter")

class PackCounter:
    def __init__(self):
        self.host = None
        self.port = None
        self.chan = None
        self.nick = None
        self.auth = None
        self.allowed_user = None
        self.clear_ranks = None
        live = True

        # Fill previously initialised variables with data from the settings.txt file
        Settings(self)

        self.db = Database()

        self.ws = TwitchWebsocket(self.host, self.port, self.message_handler, live=live)
        self.ws.login(self.nick, self.auth)

        # Make sure we're not live, as we cant send a message to multiple servers
        if type(self.chan) == list and not live:
            for chan in self.chan:
                self.ws.join_channel(chan)
        else:
            self.ws.join_channel(self.chan)
        self.ws.add_capability(["tags", "commands"])

    def setSettings(self, host, port, chan, nick, auth, allowed_user, clear_ranks):
        self.host = host
        self.port = port
        self.chan = chan
        self.nick = nick
        self.auth = auth
        self.allowed_user = allowed_user
        self.clear_ranks = clear_ranks

    def message_handler(self, m):
        try:
            if m.type == "366":
                logging.info(f"Successfully joined channel: #{m.channel}")

            elif m.type == "NOTICE":
                logging.info(m.message)

            elif m.type == "USERNOTICE":
                # If message is of an (anon)subgift, add the tier of it to a counter.
                if m.tags["msg-id"] in ["subgift", "anonsubgift"]:
                    self.add_to_counter(m)
                    #print(m.tags["system-msg"].replace("\\s", " "))
        
            elif m.type == "PRIVMSG":
                if m.message.startswith(("!packs", "!packcounter")):
                    self.send_pack_counter()

                elif m.message.startswith(("!details", "!packdetails", "!packgifters", "!gifters")):
                    self.send_pack_details()

                elif m.message.startswith(("!clear", "!packclear", "!clearpack")) and self.is_user_allowed(m):
                    # Send the pack counter beforehand just in case
                    self.send_pack_counter(clear=True)

                    self.db.clear()

                elif m.message.startswith(("!help", "!packshelp", "!packshelp")):
                    self.ws.send_message("This bot tracks gift subs. Commands: !packs/!packcounter (get the counter), !gifters/!packgifters (get each gifter's individual gift count), !clear (clear out counter, mod+)")
        except Exception as e:
            logging.error(e)

    def send_pack_counter(self, clear=False):
        # Get total amount of gift subscriptions
        total = self.db.get_total()

        # In case there are no gifts yet
        if total is None:
            total = 0

        # Perform integer division to get total divided by 5, rounded down
        packs = total // 5

        # Send to twitch chat
        out = f"Pack Counter{' before clearing' if clear else ''}: {packs:.0f}"
        logging.info(out)
        self.ws.send_message(out)

    def send_pack_details(self):
        # Get output in the form of 
        # Cubdroid: 5, Cubie: 7, Cuboid: 3
        grouped_total = self.db.get_grouped_total()
        if grouped_total:
            out = "Recent sub gifts: " + ", ".join(f"{o[0]}: {o[1]}" for o in grouped_total)
        else:
            out = "No recent sub gifts recorded."
        
        # Send to twitch chat
        logging.info(out)
        self.ws.send_message(out)

    def add_to_counter(self, m):
        # Add values to the database
        self.db.add_item(m.tags["display-name"], 
                         m.tags["msg-param-recipient-display-name"], 
                         int(m.tags["msg-param-sub-plan"]) / 1000,
                         m.tags["tmi-sent-ts"])
    
    def is_user_allowed(self, m):
        # Make sure the user has clear permissions
        for rank in self.clear_ranks:
            if rank in m.tags["badges"]:
                return True
        
        return m.user in self.allowed_user

if __name__ == "__main__":
    Logging()
    try:
        PackCounter()
    except Exception as e:
        logging.error(e)
