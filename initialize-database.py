import pymongo
import datetime
import os
from dotenv import load_dotenv

## necessary for python-dotenv ##
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
mongo = 'mongodb+srv://daniel:Z47c6cI1SfOvWElZ@schoolserver.coq5b.mongodb.net/myProject?retryWrites=true&w=majority'#o.s.getenv('MONGO')
print(mongo)
client = pymongo.MongoClient(mongo)

db = client['myProject']

users = db['users']
roles = db['roles']
licenses = db['licenses']
purchases = db['purchases']
#recipes = db['recipes']
#categories = db['categories']


def add_role(role_name):
    role_data = {
        'role_name': role_name
    }
    return roles.insert_one(role_data)


def add_category(category_name):
    category_data = {
        'category_name': category_name
    }
    return categories.insert_one(category_data)

def add_license():
    licenseData = {
        "first_name": "James",
        "last_name": "Smith",
        "licenseKey": "4e509aa9-765b-302c-d312-2d9a893dc9f2",
        "email": "j.smith342@gmail.com",
        "machine": {
            "active": True,
            "machineId": "05e86fd5-8ccc-80bc-00f8-50c8399a7abe",
            "networkId": "54.110.211.141"
        },
        "discord": {
            "active": True,
            "userId": "513532372243709952",
            "username": "yzyszn#3409"
        },
        "renewal": {
            "isRenewal": True,
            "valid": True,
            "date": "2021-12-14",
            "renewID": "0eb0a6fb-0cda-47e7-248c-a0d00ffab880",
            "length": "6 Months",
            "price": 200,
            "canUnbind": True
        },
        'date_modified': datetime.datetime.now()
    }
    return licenses.insert_one(licenseData)

def add_purchaser():
    
    return purchases.insert_one(purchaser)




def add_user(first_name, last_name, email, password, role):
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password,
        'role': role,
        'licenseKey': '53094ad8-2400-f6cd-edaf-49b08abc9475',
        'date_added': datetime.datetime.now(),
        'date_modified': datetime.datetime.now()
    }
    return users.insert_one(user_data)


def add_recipe(recipe_name, category, ingredients, preparation, notes, first_name, last_name):
    recipe_data = {
        'recipe_name': recipe_name,
        'category': category,
        'ingredients': ingredients,
        'preparation': preparation,
        'notes': notes,
        'first_name': first_name,
        'last_name': last_name,
        'date_added': datetime.datetime.now(),
        'date_modified': datetime.datetime.now()
    }
    return recipes.insert_one(recipe_data)


def initial_database():
    # add roles
    #admin = add_role('admin')
    #print(str(admin))
    #contributor = add_role('contributor')
    #user = add_role('user')

    # add users
    #mike = add_user('Daniel', 'Bullock', 'd.bullock@dabullock.com', 'password100', 'admin')
    add_license()
    #add_purchaser()
    # add categories
    #main = add_category('Main dishes')
    #drink = add_category('Drinks')
    #desserts = add_category('Desserts')
    #apps = add_category('Appetizer')
    #s = add_category('Sides')

   
    # add recipe
    #chicken_parmesean = add_recipe('Chicken Parmesean', 'Main dishes',
              #                     'chicken', 'cook it good', 'cook it real good', 'Mike', 'Colbert')

global purchaser
#purchaser = 
def main():
    initial_database()
   

main()
