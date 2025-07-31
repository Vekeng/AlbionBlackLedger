import sqlite3

def create(): 
    cursor = sqlite3.connect("marketdata.db")
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders ( 
                        Id INTEGER PRIMARY KEY, 
                        ItemTypeId TEXT NOT NULL, 
                        ItemGroupTypeId TEXT NOT NULL, 
                        LocationId INTEGER NOT NULL, 
                        QualityLevel INTEGER NOT NULL, 
                        EnchantmentLevel INTEGER NOT NULL, 
                        UnitPriceSilver INTEGER NOT NULL, 
                        Amount INTEGER NOT NULL, 
                        AuctionType TEXT NOT NULL, 
                        Expires TEXT NOT NULL)
                    '''
    );
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS claimed (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        buy_id INTEGER,
                        ItemTypeId TEXT NOT NULL,
                        buy_location TEXT NOT NULL,
                        buy_quality TEXT NOT NULL,
                        buy_amount INTEGER NOT NULL,
                        buy_price INTEGER NOT NULL,
                        sell_id INTEGER UNIQUE NOT NULL,
                        sell_location TEXT NOT NULL,
                        sell_quality TEXT NOT NULL,
                        sell_amount INTEGER NOT NULL,
                        sell_enchantment TEXT,
                        sell_price INTEGER NOT NULL,
                        enchantment TEXT,
                        profit INTEGER NOT NULL
                    );
                   '''
    )
    cursor.commit()
    cursor.close()

def truncate_flips(): 
    cursor = sqlite3.connect("marketdata.db")
    cursor.execute("DELETE FROM orders")
    cursor.commit()
    cursor.close()

def truncate_claimed():
    cursor = sqlite3.connect("marketdata.db")
    cursor.execute("DELETE FROM claimed")
    cursor.commit()
    cursor.close()