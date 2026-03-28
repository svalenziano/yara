from yara.db.pgvector import setup, nuke

if __name__ == "__main__":
    
    nuke()
    setup()
