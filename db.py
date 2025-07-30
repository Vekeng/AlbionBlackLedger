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
    cursor.close()

def truncate(): 
    cursor = sqlite3.connect("marketdata.db")
    cursor.execute("DELETE FROM orders")
    cursor.commit()
    cursor.close()