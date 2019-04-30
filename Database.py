
import sqlite3, logging, random
logger = logging.getLogger(__name__)

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
        logger.debug("Creating Database...")
        self.execute(sql)
        logger.debug("Database created.")

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
            logger.info(f"{args[0]} gifted {args[1]} a tier {args[2]}")
        except UnicodeEncodeError:
            try:
                logger.info(f"{args[0]} gifted ... a tier {args[2]}")
            except UnicodeEncodeError:
                logger.info(f"... gifted {args[1]} a tier {args[2]}")
        self.execute("INSERT INTO PackCounter(gifter, recipient, tier, time) VALUES (?, ?, ?, ?)", args)
    
    def get_total(self):
        return self.execute("SELECT SUM(tier) FROM PackCounter;", fetch=True)[0][0]
    
    def get_grouped_total(self):
        return self.execute("SELECT gifter, SUM(tier) FROM PackCounter GROUP BY gifter ORDER BY 2 DESC;", fetch=True)

    def clear(self):
        # Deletes all items
        self.execute("DELETE FROM PackCounter")