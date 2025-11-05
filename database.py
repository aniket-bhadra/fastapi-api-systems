from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# engine takes all the configuration to connect with the db - its name, username, password, port, every detail it needs to connect to the db. We can pass all this as arguments or as a connection string. So the engine helps us connect with the db.
db_url = "postgresql://postgres:85207412369@localhost:5432/fastapiLearning"
engine = create_engine(db_url)

# sessionLocal is a factory that creates database sessions. 
# autocommit=False means changes won't be saved automatically; we must explicitly call session.commit() to save changes to the database.
# autoflush=False means changes stay in Python in memory and are NOT sent to the database until we manually call commit(). This gives us control over when database operations happen and improves performance.

# Both = False means without commit(), no data will even reach the database at all — it stays completely in Python memory until you call commit().
# bind=engine connects this session factory to our database engine.
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)