from utils.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ARRAY
from sqlalchemy.sql import func


class Satellite(Base):
    """Core satellite table"""
    __tablename__ = "satellite"
    satellite_name = Column(String, index=True)
    satellite_id = Column(String, unique=True, primary_key = True)
    epoch = Column(String)
    mean_motion = Column(Float)
    eccentricity = Column(Float)
    inclination = Column(Float)
    ra_of_asc_node = Column(Float)
    arg_of_pericenter = Column(Float)
    mean_anomaly = Column(Float)
    ephemeris_type = Column(Integer)
    classification_type = Column(String)
    norad_cat_id = Column(Integer)
    element_set_no = Column(Integer)
    rev_at_epoch = Column(Integer)
    bstar =  Column(Float)
    mean_motion_dot = Column(Float)
    source = Column(String)

    def to_dict(self):
        """Convert all fields to dict"""
        values = {}
        for col in self.__table__.columns: # for each column in this object's __table__ attribute
            values[col.name] = getattr(self, col.name) # Get the object's value (pulls from db)
        return values
    
class Process(Base):
    """Process info table"""
    __tablename__ = "process"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert all fields to dict"""
        values = {}
        for col in self.__table__.columns: # for each column in this object's __table__ attribute
            values[col.name] = getattr(self, col.name) # Get the object's value (pulls from db)
        return values


class Prediction(Base):
    """Prediction info table"""
    __tablename__ = "prediction"
    satellite_name = Column(String, index=True)
    satellite_id = Column(String, primary_key = True)
    epoch = Column(DateTime, primary_key=True)
    elevation = Column(Float)
    geocentric_coords = Column(ARRAY(Float))
    geo_velocity_m_per_s = Column(ARRAY(Float))
    latitude = Column(Float)
    longitude = Column(Float)

    def to_dict(self):
        """Convert all fields to dict"""
        values = {}
        for col in self.__table__.columns: # for each column in this object's __table__ attribute
            values[col.name] = getattr(self, col.name) # Get the object's value (pulls from db)
        return values
    