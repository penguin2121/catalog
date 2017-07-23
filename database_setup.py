from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False)
    name = Column(String(250))
    picture = Column(String(250))

    @property
    def serialize(self):
        # Returns object data in easily serializable format
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture
        }


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        # Returns object data in easily serializable format
        return {
            'id': self.id,
            'name': self.name,
        }


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(2000))
    time = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    category_id = Column(Integer, ForeignKey('category.id'))
    user = relationship(User)
    category = relationship(Category)

    @property
    def serialize(self):
        # Returns object data in easily serializable format
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'time': self.time,
            'user_id': self.user_id,
            'category_id': self.category_id
        }

engine = create_engine('sqlite:///categoryproject.db')
Base.metadata.create_all(engine)
