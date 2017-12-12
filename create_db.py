from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Numeric, String
import pandas as pd

PROFILES_JSON = 'profiles_1512362725.022629.json'
PROFILES_TABLE_NAME = 'profiles'
PROFILES_DB_FILE= 'nfl-player-stats.db'

engine = create_engine('sqlite:///{}'.format(PROFILES_DB_FILE), echo=True)
Base = declarative_base()


class Profile(Base):
    __tablename__ = PROFILES_TABLE_NAME

    player_id = Column(Integer, primary_key=True)
    name = Column(String(50))
    position = Column(String(2))
    height = Column(String(4))
    weight = Column(Integer)
    current_team = Column(String(3))
    birth_date = Column(String(10))
    birth_place = Column(String(30))
    death_date = Column(String(10))
    college = Column(String(30))
    high_school = Column(String(30))
    draft_team = Column(String(3))
    draft_round = Column(Integer)
    draft_position = Column(Integer)
    draft_year = Column(Integer)
    current_salary = Column(Integer)
    hof_induction_year = Column(Integer)

    def __str__(self):
        output = ''
        for c in self.__table__.columns:
            output += '{}: {}\n'.format(c.name, getattr(self, c.name))
        return output


Base.metadata.create_all(engine)

profiles_df = pd.read_json(PROFILES_JSON)
profiles_df.set_index('player_id', inplace=True)
profiles_df.to_sql(name=PROFILES_TABLE_NAME, con=engine, if_exists='replace')






