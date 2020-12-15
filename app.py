import os
from dotenv import load_dotenv
import pymongo
import datetime
from bson.objectid import ObjectId
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
import bcrypt
from functools import wraps
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

## necessary for python-dotenv ##
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

mongo = os.getenv('MONGO')#'mongodb+srv://daniel:Z47c6cI1SfOvWElZ@schoolserver.coq5b.mongodb.net/myProject?retryWrites=true&w=majority'#os.getenv('MONGO')
print(mongo)
client = pymongo.MongoClient(mongo)

db = client['myProject'] # Mongo collection
users = db['users'] # Mongo document
roles = db['roles'] # Mongo document
licenses = db['licenses']
purchases = db['purchases']

login = LoginManager()
login.init_app(app)
login.login_view = 'login'

@login.user_loader
def load_user(username):
    u = users.find_one({"email": username})
    if not u:
        return None
    return User(username=u['email'], role=u['role'], id=u['_id'], first_name=u['first_name'], last_name=u['last_name'], licenseKey=u['licenseKey'])

class User:
    def __init__(self, id, username, role, first_name, last_name, licenseKey):
        self._id = id
        self.username = username
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.licenseKey = licenseKey

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

'''
    @staticmethod
    def check_password(password_hash, password):
        return check_password_hash(password_hash, password)
'''

### custom wrap to determine role access  ### 
def roles_required(*role_names):
    def decorator(original_route):
        @wraps(original_route)
        def decorated_route(*args, **kwargs):
            if not current_user.is_authenticated:
                print('The user is not authenticated.')
                return redirect(url_for('login'))
            
            print(current_user.role)
            print(role_names)
            if not current_user.role in role_names:
                print('The user does not have this role.')
                flash('Account access not permitted here', category='warning')
                return redirect(url_for('login'))
            else:
                print('The user is in this role.')
                return original_route(*args, **kwargs)
        return decorated_route
    return decorator


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return 'self register for an account'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        print(request.form['username'])
        user = users.find_one({"email": request.form['username']})
        print(user)
        if user and bcrypt.checkpw(request.form['password'].encode(),user['password'].encode()):
            user_obj = User(username=user['email'], role=user['role'], id=user['_id'], first_name=user['first_name'], last_name=user['last_name'], licenseKey=user['licenseKey'])
            login_user(user_obj)
            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
                return redirect(next_page)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("index"))

        flash("Wrong username or password!", category='error')
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/my-account/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'admin')
def my_account(user_id):
    edit_account = users.find_one({'_id': ObjectId(user_id)})
    if edit_account:
        return render_template('my-account.html', user=edit_account)
    flash('User not found.', 'warning')
    return redirect(url_for('index'))


@app.route('/update-myaccount/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'admin')
def update_myaccount(user_id):
    if request.method == 'POST':
        form = request.form
        update_account = users.find_one({'_id': ObjectId(user_id)})
        password = request.form['password']
        if password != form['confirm_password']:
            flash('Passwords must match', 'warning')
            return redirect(url_for('my_account', user_id=user_id))
        if '$2b' not in password:
            password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        users.update({'_id': ObjectId(user_id)},
            {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'email': form['email'],
            'licenseKey': form['licenseKey'],
            'password': password,
            'role': form['role'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        flash(update_account['email'] + ' has been modified.', 'success')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


##########  Admin functionality -- User management ##########

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_users():
    newKeyToMake = str(uuid.uuid4())
    return render_template('users.html', all_roles=roles.find(), all_users=users.find(), newKey=newKeyToMake)


@app.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_add_user():
    if request.method == 'POST':
        form = request.form
        license = licenses.find_one({'licenseKey': form['licenseKey']})
        if license == None:
            flash("License key not found, please enter an existing key", "warning")
            return redirect(url_for('admin_users'))
        password = request.form['password']
        if password != form['confirm_password']:
            flash('Passwords must match', 'warning')
            return redirect(url_for('admin_users'))
        password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        email = users.find_one({"email": request.form['email']})
        if email:
            flash('This email is already registered.', 'warning')
            return 'This email has already been registered.'
        new_user = {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'email': form['email'],
            'licenseKey': form['licenseKey'],
            'password': password,
            'role': form['role'],
            'date_added': datetime.datetime.now(),
            'date_modified': datetime.datetime.now()
        }
        users.insert_one(new_user)
        flash(new_user['email'] + ' user has been added.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('users.html', all_roles=roles.find(), all_users=users.find())

@app.route('/admin/delete-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_delete_user(user_id):
    delete_user = users.find_one({'_id': ObjectId(user_id)})
    if delete_user:
        users.delete_one(delete_user)
        flash(delete_user['email'] + ' has been deleted.', 'warning')
        return redirect(url_for('admin_users'))
    flash('User not found.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/edit-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_edit_user(user_id):
    edit_user = users.find_one({'_id': ObjectId(user_id)})
    if edit_user:
        return render_template('edit-user.html', user=edit_user, all_roles=roles.find())
    flash('User not found.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/update-user/<user_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_update_user(user_id):
    if request.method == 'POST':
        form = request.form

        password = request.form['password']
        if password != form['confirm_password']:
            flash('Passwords must match', 'warning')
            return redirect(url_for('admin_edit_user', user_id=user_id))
        if '$2b' not in password:
            password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        users.update({'_id': ObjectId(user_id)},
            {
            'first_name': form['first_name'],
            'last_name': form['last_name'],
            'email': form['email'],
            'licenseKey': form['licenseKey'],
            'password': password,
            'role': form['role'],
            'date_added': form['date_added'],
            'date_modified': datetime.datetime.now()
            })
        update_user = users.find_one({'_id': ObjectId(user_id)})
        flash(update_user['email'] + ' has been added.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('users.html', all_roles=roles.find(), all_users=users.find())

##########  Licenses ##########
### VIEW LICENSE IINFO AS A USER
## You can deactivate your license key from current machine
## as well as view all successful purchases
@app.route('/my-license', methods=['GET', 'POST'])
@login_required
@roles_required('user', 'admin')
def my_license():
    this_license = licenses.find_one({'licenseKey': current_user.licenseKey})
    if this_license:
        renewDate = this_license['renewal']['date']
        active = this_license['machine']['active']
        renewPrice = str(this_license['renewal']['price'])
        purchaseHistory = purchases.find_one({'licenseKey': current_user.licenseKey})
        if purchaseHistory:
            total = len(purchaseHistory['purchaseRecords'])
        else: 
            total = 0
        return render_template('my-license.html', renewDate=renewDate, renewPrice=renewPrice, active=active, attemptedCheckouts=total)
    flash('License not found.', 'warning')
    return redirect(url_for('index'))


#Load and display all of a users successful purchases on their license
@app.route('/my-license/checkouts', methods=['GET'])
@login_required
@roles_required('user', 'admin')
def my_checkouts():
    purchaseHistory = purchases.find_one({'licenseKey': current_user.licenseKey})
    if purchaseHistory:
        successfulPurchases = list()
        totalSuccess = 0
        for checkout in purchaseHistory['purchaseRecords']:
            if checkout['status'] == 'Success':
                successfulPurchases.append(checkout)
                totalSuccess+=1
        successfulPurchases.reverse()
        return render_template('my-checkouts.html', totalSuccess=totalSuccess, checkouts=successfulPurchases)
    flash('No Purchase Records for {}'.format(current_user.licenseKey), 'warning')
    return redirect(url_for('my_license'))

# VIEW ALL Licenses w/ admin features
@app.route('/licenses/manage', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def license_manager():
    return render_template('licenses.html', all_roles=roles.find(), all_users=licenses.find())

# Load new license form 
@app.route('/licenses/new-license', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def new_license():

    keyToUse = str(uuid.uuid4())
    return render_template('new-license.html', firstName=current_user.first_name, lastName=current_user.last_name, newKey=keyToUse)

@app.route('/licenses/add-license', methods=['POST'])
@login_required
@roles_required('admin')
def add_license():
    if request.method == 'POST':
        form = request.form
        if form['length'] == '3':
            date = datetime.date.today()
            date+=datetime.timedelta(3 * 30)
            time = '3 Months'
        if form['length'] == '6':
            date = datetime.date.today()
            date+=datetime.timedelta(6 * 30)
            time = '6 Months'
        if form['length'] == 'year':
            date = datetime.date.today()
            date+=datetime.timedelta(365)
            time = '1 Year'
        licenseData = {
            "first_name": form['first_name'],
            "last_name": form['last_name'],
            "licenseKey": form['licenseKey'],
            "email": form['email'],
            "machine": {
                "active": False,
                "machineId": None,
                "networkId": None
            },
            "discord": {
                "active": False,
                "userId": None,   # discord ID is automatically gotten when they join our support chat
                "username": form['discord']
            },
            "renewal": {
                "isRenewal": True,
                "valid": True,
                "date": str(date),
                "renewID": str(uuid.uuid4()),
                "length": time,
                "price": int(form['price']),
                "canUnbind": True
            },
            'date_modified': datetime.datetime.now()
        }
        licenses.insert_one(licenseData)
        flash('Saved New License: {}'.format(form['licenseKey']), 'success')
        return redirect(url_for('license_manager'))
    else:
        return render_template('new-license.html', firstName=current_user.first_name, lastName=current_user.last_name)

##deactivates the license key from the current computer, so a user can switch devices
@app.route('/licenses/deactivate-key', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'user')
def deactivate_license():
    if request.method == 'POST':
        form = request.form
        if form['active'] == 'false':
            try:
                update_license = licenses.find_one({'licenseKey': current_user.licenseKey})
                update_license['machine']['active'] = False
                update_license['machine']['machineId'] = None
                update_license['machine']['networkId'] = None

                licenses.update({'_id': ObjectId(update_license['_id'])},
                    update_license)

            except Exception as e:
                print(e)
                flash('Unknown Error Deactivating License', 'warning')
                return redirect(url_for('my_license'))
            flash('Deactivated License', 'success')
            return redirect(url_for('my_license'))
        else:
            flash('License already activated', 'warning')
            return redirect(url_for('my_license'))
    return redirect(url_for('my_license'))

# DELETEs License key
@app.route('/licenses/delete-license/<license_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def delete_license(license_id):
    delete_license = licenses.find_one({'_id': ObjectId(license_id)})
    if delete_license:
        licenses.delete_one(delete_license)
        flash(delete_license['licenseKey'] + ' has been deleted.', 'warning')
        return redirect(url_for('license_manager'))
    flash('License not found.', 'warning')
    return redirect(url_for('license_manager'))

# LOAD LICENSE EDIT TEMPLATE
@app.route('/licenses/edit-license/<license_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_license(license_id):
    edit_licenes = licenses.find_one({'_id': ObjectId(license_id)})
    if edit_licenes:
        return render_template('edit-license.html', license=edit_licenes, all_roles=roles.find(), user_email=session['_user_id'])
    flash('License not found.', 'warning')
    return redirect(url_for('license_manager'))

# UPDATE License info
@app.route('/licenses/update-license/<license_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def update_license(license_id):
    if request.method == 'POST':
        form = request.form
        try:
            update_license = licenses.find_one({'_id': ObjectId(license_id)})

            if form['active'] == 'false':
                update_license['machine']['active'] = False
                update_license['machine']['machineId'] = None
                update_license['machine']['networkId'] = None

            update_license['licenseKey'] = form['licenseKey']
            update_license['email'] = form['email']
            update_license['first_name'] = form['first_name']
            update_license['last_name'] = form['last_name']
            update_license['discord']['username'] = form['discord']

            licenses.update({'_id': ObjectId(license_id)},
                update_license)
        except Exception as e:
            print(e)
            flash('Unknown Error Updating License', 'warning')
            return redirect(url_for('license_manager'))
        flash('Updated License', 'success')
        return redirect(url_for('license_manager'))
    return render_template('licenses.html', all_roles=roles.find(), all_users=licenses.find())

# search license not fully implemented
@app.route('/licenses/search', methods=['POST'])
@login_required
@roles_required('admin', 'user')
def serch_license():
    if request.method == 'POST':
        form = request.form
        allLicense = licenses.find()
        search_data = form['search_string']
        #search_terms = search_data.split(' ')
        if search_data == '':
            flash('Please enter search keywords', 'warning')
            return redirect(url_for('index'))
        results = list()
        for license in allLicense:
            if search_data.lower() in license['licenseKey'].lower():
                results.append(license)
        if len(results) == 0:
            flash('No Licenses matching search', 'warning')
            return redirect(url_for('index'))
        return 'Search feature not yet complete, found %s results'%(len(results))
    else:
        return redirect(url_for('index'))



if __name__ == "__main__":
    app.run(debug=True)
