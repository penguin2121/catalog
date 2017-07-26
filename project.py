import random
import string
import httplib2
import json
import requests
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import Flask, render_template, request, redirect
from flask import url_for, make_response, jsonify
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)

engine = create_engine('sqlite:///categoryproject.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Web client 1"

# This loads the JSON endpoints for all of the items in a category
@app.route('/catalog/<string:category_name>/JSON')
@app.route('/catalog/<string:category_name>/items/JSON')
def jsonCatalog(category_name):
    category_name = string.capwords(category_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=animal).all()
    return jsonify(Item=[item.serialize for item in items])


# This loads the JSON endpoints for individual items
@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def jsonItem(category_name, item_name):
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=animal, name=item_name).one()
    return jsonify(Item=item.serialize)


# This loads the home page (shows both categories and recent items)
@app.route('/catalog/')
@app.route('/')
def home():
    animals = session.query(Category).all()
    newest_items = session.query(Item).order_by(desc(Item.time))\
        .limit(5).all()
    if 'user_id' in login_session.keys():
        user_id = login_session['user_id']
    else:
        user_id = None
    return render_template('home.html', categories=animals,
                           items=newest_items, user_id=user_id)


# This loads the items in a category
@app.route('/catalog/<string:category_name>/')
@app.route('/catalog/<string:category_name>/items/')
def displayItemsInCategory(category_name):
    category_name = string.capwords(category_name)
    animals = session.query(Category).all()
    animal = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=animal).all()
    if 'user_id' in login_session.keys():
        user_id = login_session['user_id']
    else:
        user_id = None
    return render_template('categorypage.html', category_list=animals,
                           category=animal, items=items, user_id=user_id)


# This allows you to add items in a category if you are logged in.
@app.route('/catalog/<string:category_name>/add/', methods=['POST', 'GET'])
def createNewItem(category_name):
    category_name = string.capwords(category_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    if request.method == 'POST':
        if request.form['name']:
            new_item = Item(name=string.capwords(request.form['name']),
                            description=request.form['description'],
                            category=animal, user_id=login_session['user_id'])
            session.add(new_item)
            session.commit()
            return redirect(url_for('displayItemsInCategory',
                                    category_name=animal.name))
        else:
            return "ERROR: You need to enter an item name in the form."
    else:
        if 'user_id' not in login_session.keys():
            return redirect(url_for('login'))
        else:
            user_id = login_session['user_id']
            return render_template('additem.html', category=animal,
                                   user_id=user_id)


# This lets you see the details of an item.
@app.route('/catalog/<string:category_name>/<string:item_name>/')
def displayItemDetails(category_name, item_name):
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=animal, name=item_name).one()
    if 'user_id' in login_session.keys():
        user_id = login_session['user_id']
    else:
        user_id = None
    return render_template('itemdetails.html', category=animal, item=item,
                           user_id=user_id)


# This lets you edit an items details if you are logged in as the creator
# of the item.
@app.route('/catalog/<string:category_name>/<string:item_name>/edit/',
           methods=['POST', 'GET'])
def editItemDetails(category_name, item_name):
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name, category=animal).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = string.capwords(request.form['name'])
        if request.form['description']:
            item.description = request.form['description']
        session.add(item)
        session.commit()
        return redirect(url_for('displayItemDetails',
                                category_name=animal.name,
                                item_name=item.name))
    else:
        if 'user_id' not in login_session.keys():
            return redirect(url_for('login'))
        elif login_session['user_id'] != item.user_id:
            return redirect(url_for('login'))
        else:
            user_id = login_session['user_id']
            return render_template('edititem.html', category=animal,
                                   item=item, user_id=user_id)


# This lets you delete an item if you are logged in as the creator
# of the item.
@app.route('/catalog/<string:category_name>/<string:item_name>/delete/',
           methods=['POST', 'GET'])
def deleteItem(category_name, item_name):
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name, category=animal).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('displayItemsInCategory',
                                category_name=animal.name))
    else:
        if 'user_id' not in login_session.keys():
            return redirect(url_for('login'))
        elif login_session['user_id'] != item.user_id:
            return redirect(url_for('login'))
        else:
            user_id = login_session['user_id']
            return render_template('deleteitem.html', category=animal,
                                   item=item, user_id=user_id)


# This loads the login page.
@app.route('/login/')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for
                    x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# This logs the user in and then redirects them to the home page.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists.  If it doesn't, make a
    # new user entry in the database
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: ' \
              '150px;-webkit-border-radius: 150px;-moz-border-radius:150px;">'
    print "done!"
    return output


# This lets the user log out.
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('home'))
    else:
        response = make_response(json.dumps('Failed to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('home'))


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
