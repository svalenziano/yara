from yara.db.pgvector import nuke, setup

if __name__ == "__main__":
    nuke()
    setup()
