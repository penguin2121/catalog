from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Category, Item, Base

engine = create_engine('sqlite:///categoryproject.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Admin User
admin = User(name="Admin", email="admin@gmail.com")
session.add(admin)
session.commit()

# Items for Dog
dog = Category(name='Dog')

session.add(dog)
session.commit()

pug = Item(name="Pug", description="The Pug is a breed of dog with physically "
           "distinctive features of a wrinkly, short-muzzled face, and curled "
           "tail. The breed has a fine, glossy coat that comes in a variety of"
           " colours, most often fawn or black, and a compact square body with"
           "well-developed muscles.", user=admin, category=dog)
session.add(pug)
session.commit()

labrador = Item(name="Labrador Retriever", description="This versatile hunting"
                " breed comes in three colors - yellow, black and chocolate - "
                "and because of their desire to please their master they excel"
                " as guide dogs for the blind, as part of search-and-rescue "
                "teams or in narcotics detection with law enforcement.",
                user=admin, category=dog)
session.add(labrador)
session.commit()

beagle = Item(name="Beagle", description="Small, compact, and hardy, Beagles "
              "are active companions for kids and adults alike. Canines in "
              "this dog breed are merry and fun loving, but being hounds, "
              "they can also be stubborn and require patient, creative "
              "training techniques.", user=admin, category=dog)
session.add(beagle)
session.commit()

# Items for Cat
cat = Category(name='Cat')
session.add(cat)
session.commit()

siamese = Item(name="Siamese", description="The carefully refined modern "
               "Siamese is characterized by blue almond-shaped eyes; a "
               "triangular head shape; large ears; an elongated, slender,"
               " and muscular body; and point colouration.", user=admin,
               category=cat)
session.add(siamese)
session.commit()

persian = Item(name="Persian", description="The Persian cat is a long-"
               "haired breed of cat characterized by its round face and"
               " short muzzle. It is also known as the Persian Longhair.",
               user=admin, category=cat)
session.add(persian)
session.commit()

shorthair = Item(name="American Shorthair", description="Although it is "
                 "not an extremely athletic cat, the American Shorthair "
                 "has a large, powerfully-built body. According to the "
                 "breed standard of the Cat Fanciers' Association, the "
                 "American Shorthair is a true breed of working cat. They"
                 " have round faces and short ears.", user=admin,
                 category=cat)
session.add(persian)
session.commit()

print("Added Items to Database")
