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
    newest_items = session.query(Item).order_by(desc(Item.time)).limit(5).all()  # this may not be reporting in descending order
    return render_template('home.html', categories=animals, items=newest_items)


@app.route('/catalog/<string:category_name>/')
@app.route('/catalog/<string:category_name>/items/')
def displayItemsInCategory(category_name):
    category_name = category_name.title()
    animals = session.query(Category).all()
    animal = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=animal).all()
    return render_template('categorypage.html', category_list=animals, category=animal, items=items)


@app.route('/catalog/<string:category_name>/add/', methods=['POST', 'GET'])
def createNewItem(category_name):
    category_name = category_name.title()
    animal = session.query(Category).filter_by(name=category_name).one()
    if request.method == 'POST':
        if request.form['name']:
            new_item = Item(name=request.form['name'].title(), description=request.form['description'], category=animal)
            session.add(new_item)
            session.commit()
            return redirect(url_for('displayItemsInCategory', category_name=animal.name))
        else:
            return "ERROR: You need to enter an item name in the form."
    else:
        return render_template('additem.html', category=animal)


@app.route('/catalog/<string:category_name>/<string:item_name>/')
def displayItemDetails(category_name, item_name):
    category_name = category_name.title()
    item_name = item_name.title()
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=animal, name=item_name).one()
    return render_template('itemdetails.html', category=animal, item=item)


@app.route('/catalog/<string:category_name>/<string:item_name>/edit/', methods=['POST', 'GET'])
def editItemDetails(category_name, item_name):
    category_name = category_name.title()
    item_name = item_name.title()
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name, category=animal).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name'].title()
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        session.commit()
        return redirect(url_for('displayItemDetails', category_name=animal.name, item_name=item.name))
    else:
        return render_template('edititem.html', category=animal, item=item)


@app.route('/catalog/<string:category_name>/<string:item_name>/delete/', methods=['POST', 'GET'])
def deleteItem(category_name, item_name):
    category_name = category_name.title()
    item_name = item_name.title()
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name, category=animal).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('displayItemsInCategory', category_name=animal.name))
    else:
        return render_template('deleteitem.html', category=animal, item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)