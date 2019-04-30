
from TwitchWebsocket import TwitchWebsocket
import random, time, json, sqlite3, logging, os

from Log import Log
Log(__file__)

from Settings import Settings
from Database import Database

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

        self.ws = TwitchWebsocket(host=self.host, 
                                  port=self.port,
                                  chan=self.chan,
                                  nick=self.nick,
                                  auth=self.auth,
                                  callback=self.message_handler,
                                  capability=["tags", "commands"],
                                  live=live)
        self.ws.start_bot()

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
    PackCounter()
