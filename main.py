import threading
from server import app
from db import create
from flipper import find_flip
from ui import show_table

def run_server(): 
    app.run()


if __name__ == '__main__':
    create()
    ingest_thread = threading.Thread(target=run_server, daemon=True)
    ingest_thread.start()
    show_table(find_flip)  
