# // const firebaseConfig = {
# //   apiKey: "AIzaSyAJ7iPLqkPhJkd6LuWvIdxdJ29TtnBNhNg",
# //   authDomain: "feastchoiceapp.firebaseapp.com",
# //   projectId: "feastchoiceapp",
# //   storageBucket: "feastchoiceapp.appspot.com",
# //   messagingSenderId: "803250173239",
# //   appId: "1:803250173239:web:6a6a03a380460e574816b2"
# // };
# // Your web app's Firebase configuration
# const firebase = require("firebase")

# firebase.initializeApp({
#   apiKey: "AIzaSyAJ7iPLqkPhJkd6LuWvIdxdJ29TtnBNhNg",
#   authDomain: "feastchoiceapp.firebaseapp.com",
#   projectId: "feastchoiceapp"
# })
#
# var db = firebase.firestore()

import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db as realtimedatabase

# Use the application default credentials
cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://feastchoiceapp-default-rtdb.europe-west1.firebasedatabase.app/'})

db = firestore.client()

# To find out the highest sequenceInteger currently from allRecipes collection
# returns the integer value
#TODO how to get proper where limit to query most cheaply
def query_highest_sequenceInteger_field(db):
    all_recipes_ref = db.collection(u'allRecipes')
    query = all_recipes_ref.where(
        u'sequenceInteger', u'>', 30).order_by(
            u'sequenceInteger', direction=firestore.Query.DESCENDING).limit(1)
    
    doc_snapshot = query.get()
    doc_dict = doc_snapshot[0].to_dict()

    if 'sequenceInteger' not in doc_dict:
        return -1

    return doc_dict['sequenceInteger']

# adds sequenceInteger to all new recipes in AllRecipes collection.
# needed for random querying of recipes
# return list of dicts

def add_sequenceInteger_to_new_dicts(list_of_dicts, current_max):
    for d in list_of_dicts:
        d['sequenceInteger'] = current_max + 1
        current_max += 1

    return list_of_dicts


#update realtimedatabase with current max sequence integer
def update_realtimedatabase_max_sequence_integer(ref, realtimedatabase, max_sequence_integer):
    ref = realtimedatabase.reference("/")
    ref.update({'max_sequence_integer' : max_sequence_integer})


def main(db):
    with open('recipe_data.json', encoding='utf-8') as f:
        data = json.load(f)



    # can be used to update max sequence integerr
    ref = realtimedatabase.reference("/")
    max_value = query_highest_sequenceInteger_field(db)

    update_realtimedatabase_max_sequence_integer(ref, realtimedatabase, max_value)
    

    # data = add_sequenceInteger_to_new_dicts(data, max_value)
    
    # for recipe in data:
    #     db.collection(u"allRecipes").add(recipe)

    # update_realtimedatabase_max_sequence_integer(ref, realtimedatabase, max_value)
    
main(db)
