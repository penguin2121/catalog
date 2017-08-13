import random
import string
import httplib2
import json
import requests
from functools import wraps
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import Flask, render_template, request, redirect
from flask import url_for, make_response, jsonify, flash
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


def login_required(f):
    """
    This checks to see if a user is logged in before allowing a user to view
    a page when used as a decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in login_session.keys():
            flash("You Must Login In Order to Perform that Action")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# This loads the JSON endpoints for all of the items in a category
@app.route('/catalog/<string:category_name>/JSON')
@app.route('/catalog/<string:category_name>/items/JSON')
def jsonCatalog(category_name):
    """
    This returns a JSON object containing the information about
    every item in a category.
    """
    category_name = string.capwords(category_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=animal).all()
    return jsonify(Item=[item.serialize for item in items])


# This loads the JSON endpoints for individual items
@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def jsonItem(category_name, item_name):
    """
    This returns a JSON object containing the information for a specific item.
    """
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=animal, name=item_name).one()
    return jsonify(Item=item.serialize)


# This loads the home page (shows both categories and recent items)
@app.route('/catalog/')
@app.route('/')
def home():
    """
    This displays the home screen.  If the user is logged in, they have the
    option to log out.  (This log in/log out option is available on all pages).
    """
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
    """
    This displays the items in a category.  If user_id is entered, the
    option to create an item will be displayed.
    """
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
@login_required
def createNewItem(category_name):
    """
    This loads the user create item page on a get request, as long as the user
    is logged in.  If the user is logged in while a POST request is sent,
    a new item is added to the database with the owner set to the logged in
    user.
    """
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
        user_id = login_session['user_id']
        return render_template('additem.html', category=animal,
                               user_id=user_id)


# This lets you see the details of an item.
@app.route('/catalog/<string:category_name>/<string:item_name>/')
def displayItemDetails(category_name, item_name):
    """
    This displays the details of an item.  The user_id is passed into the html
    template because it is used to display the edit/delete buttons if the user
    is logged into the account owning the item.
    """
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
@login_required
def editItemDetails(category_name, item_name):
    """
    This handles opens the edit item html page when a GET request is received
    and the user_id matches the item's user_id looking to be edit.  If a POST
    request is sent, after verification that the user id exists and matches the
    item's, the item is edited in the database.
    """
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category=animal).one()
    if login_session['user_id'] != item.user_id:
        return redirect(url_for('login'))
    else:
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
            return render_template('edititem.html', category=animal,
                                   item=item,
                                   user_id=login_session['user_id'])





# This lets you delete an item if you are logged in as the creator
# of the item.
@app.route('/catalog/<string:category_name>/<string:item_name>/delete/',
           methods=['POST', 'GET'])
@login_required
def deleteItem(category_name, item_name):
    """
    This handler opens the delete item html page when a GET request is received
    and the id matches the item looking to be delted.  If a POST request is
    sent, after verification that the user id exists and matches the item's,
    the item is deleted from the database.
    """
    category_name = string.capwords(category_name)
    item_name = string.capwords(item_name)
    animal = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name, category=animal).one()
    if login_session['user_id'] != item.user_id:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            session.delete(item)
            session.commit()
            return redirect(url_for('displayItemsInCategory',
                                    category_name=animal.name))
        else:
            user_id = login_session['user_id']
            return render_template('deleteitem.html', category=animal,
                                   item=item, user_id=user_id)


# This loads the login page.
@app.route('/login/')
def login():
    """
    Creates a random state to verify the user is  who they say
    they are throughout the login process. Allows the user to
    login via a Google sign in button.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for
                    x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# This logs the user in and then redirects them to the home page.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API and places it inside a session
    variable named loging_session.
    """
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
    """
    Allows the user to disconnect from their login.
    This code deletes all copies of the login_session data from the server.
    When logged out, the user is redirected back to the home screen.
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
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
    """
    This function returns a users ID given their email address.
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    """
    This returns a user given a user_id.
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    """
    This creates a new user in the database given the login_session information
    """
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
    app.run(host='0.0.0.0', port=80)
