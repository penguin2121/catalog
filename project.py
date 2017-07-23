from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///categoryproject.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/catalog/')
@app.route('/')
def home():
    animals = session.query(Category).all()
    newest_items = session.query(Item).order_by(Item.time).limit(5).all()  # this may not be reporting in descending order
    return render_template('home.html', categories=animals, items=newest_items)


@app.route('/catalog/<string:category_name>/items/')
def displayItemsInCategory(category_name):
    animal = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=animal).one()
    return 'this is the page for the ' + animal.name + ' category' + items.name


@app.route('/catalog/<string:category_name>/add/')
def createNewItem(category_name):
    return 'this page lets you create a new item'


@app.route('/catalog/<string:category_name>/<string:item_name>/')
def displayItemDetails(category_name, item_name):
    return 'this is the page for the ' + category_name + ' category\'s ' + item_name + '\'s list'


@app.route('/catalog/<string:category_name>/<string:item_name>/edit/')
def editItemDetails(category_name, item_name):
    return 'this page lets you edit an item'


@app.route('/catalog/<string:category_name>/<string:item_name>/delete/')
def deleteItem(category_name, item_name):
    return 'this page lets you delete an item'

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)