from flask import Flask
from flask import request
import sqlite3

app = Flask(__name__)

@app.route('/marketorders.ingest', methods = ['POST'])
def ingest():
    if request.method == 'POST': 
        cursor = sqlite3.connect("marketdata.db")
        for row in request.json['Orders']: 
            app.logger.info(row)
            cursor.execute('''
                INSERT OR REPLACE INTO orders (
                    Id,
                    ItemTypeId,
                    ItemGroupTypeId,
                    LocationId,
                    QualityLevel,
                    EnchantmentLevel,
                    UnitPriceSilver,
                    Amount,
                    AuctionType,
                    Expires
                ) VALUES (
                    :Id,
                    :ItemTypeId,
                    :ItemGroupTypeId,
                    :LocationId,
                    :QualityLevel,
                    :EnchantmentLevel,
                    :UnitPriceSilver,
                    :Amount,
                    :AuctionType,
                    :Expires
                ) 
            ''', row)
    cursor.commit()
    cursor.close()
    return "success"

if __name__ == '__main__': 
    app.run()