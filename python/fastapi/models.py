import uuid
from sqlalchemy import Column, String, INT, TEXT, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Housing_data(Base):
    __tablename__ = 'housing_data'
    
    oftenplace = Column(TEXT, nullable=False, primary_key=True)
    wantplace = Column(TEXT, nullable=False, primary_key=True)
    time = Column(INT, nullable=False)
    less_month_avg = Column(INT, nullable=False)
    more_month_avg = Column(INT, nullable=False)
    less_year_avg = Column(INT, nullable=False)
    more_year_avg = Column(INT, nullable=False)
    rank_data = Column(INT, nullable=False)
    
class Place_coordinates(Base):
    __tablename__ = 'place_coordinates'
    
    wantplace = Column(TEXT, nullable=False, primary_key=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)