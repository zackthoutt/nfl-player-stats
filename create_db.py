from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Numeric, String
import pandas as pd


class NFLDatabaseConverter():

    def __init__(self, db_file):
        self.db_file = db_file
        self.engine = create_engine('sqlite:///{}'.format(db_file), echo=True)

    def create_table_from_json(self, name, json_file):
        Base = declarative_base()
        global table_name
        table_name = name

        class Profile(Base):
            __tablename__ = table_name

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

        Base.metadata.create_all(self.engine)
        self.profiles_df = pd.read_json(json_file)
        self.profiles_df.set_index('player_id', inplace=True)
        self.profiles_df.to_sql(name=name, con=self.engine, if_exists='replace')


if __name__ == '__main__':
    DATABASE_FILE = 'nfl-player-stats.db'
    PROFILES_JSON = 'profiles_1512362725.022629.json'
    PROFILES_TABLE_NAME = 'profiles'

    db_converter = NFLDatabaseConverter(DATABASE_FILE)
    db_converter.create_table_from_json(name=PROFILES_TABLE_NAME, json_file=PROFILES_JSON)

