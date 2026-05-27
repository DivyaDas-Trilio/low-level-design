from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    
class Orders(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    product_name = Column(String)
    
    
import pdb; pdb.set_trace()
# Create an SQLite database in memory
engine = create_engine('sqlite:///:memory', echo=True)   

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Example of adding a user
def add_users():
    new_user = Users(name='John Doe', email='john.doe@example.com')
    session.add(new_user)
    session.commit()
    
def get_users():
    session.get(Users, 1)
    return session.query(Users).all()

print(get_users())