from app import app
import requests
from flask import request, jsonify
import json
from dbms.DBInterface import CRUD, db_get_user_by_email, db_get_email_by_id, db_add_card_balance,\
    db_user_verify, db_get_user_card, get_exchange_rate_and_save, db_currency_labels, db_card_balance_transfer,\
    db_exchange_buy, db_exchange_sell, db_transaction_card, db_transaction_account, db_get_card
from dbms.DBModels import User, Card, Transaction, Currency

crud = CRUD()

#get_exchange_rate_and_save()

#region Pomocne funkcije i strukture

#Pretvara model u JSON dict
def model_as_dict(model):
    if model is None:
        return {}
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}

class UserData:
    def __init__(self, user):
        self.id = user.id
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.address = user.address
        self.city = user.city
        self.state = user.state
        self.phone = user.phone
        self.email = user.email
        self.verified = user.verified
        self.admin = user.admin
        self.password = user.password
        self.card = user.card.to_dict() if user.card else None
        self.transactions = [t.to_dict() for t in user.transactions]
        self.balance = user.balance_list()
#endregion

#region UserAPI

#Call for currency
@app.route("/loadc", methods=['GET'])
def loadc():
    get_exchange_rate_and_save()
    return "", 200

#Get user with specified id
@app.route("/users/<int:user_id>", methods=['GET'])
def get_user_by_id(user_id : int):
    user = crud.read(User, user_id)
    if user == None:
        return f"User with id:{user_id} not found", 404
    else:
        return UserData(user).__dict__, 200

#Get user with specified email
@app.route("/users/<string:user_email>", methods=['GET'])
def get_user_by_email(user_email : str):
    user = db_get_user_by_email(user_email)
    if user == None:
        return f"User with email:{user_email} not found", 404
    else:
        return model_as_dict(user), 200

#Create a new user, status code 201: Created, status code 422: Unprocessable entry
@app.route("/users", methods=['POST'])
def post_user():
    result = crud.create(User(request.form["first_name"], request.form["last_name"], request.form["address"], request.form["city"], request.form["state"], request.form["phone"], request.form["email"], request.form["password"]))
    if result["status"] == "success":
        return result["message"], 201
    else:
        return result["message"], 422

#Update a existing user
@app.route("/users/<user_id>", methods=['POST'])
def put_user(user_id):
    result = crud.update(User, user_id, {"first_name": request.form["first_name"],
                                         "last_name": request.form["last_name"],
                                         "address": request.form["address"],
                                         "city": request.form["city"],
                                         "state": request.form["state"],
                                         "phone": request.form["phone"],
                                         "email": request.form["email"]})
    if result["status"] == "success":
        return result["message"], 200
    else:
        return result["message"], 400
        
#Get the email of a specified user
@app.route("/users/email/<user_id>", methods=['GET'])
def get_email_by_id(user_id):
    email = db_get_email_by_id(user_id)
    if email == None:
        return f"Email of a user with id:{user_id} not found.", 404
    else:
        return email, 200   

#Verify user
@app.route("/users/<user_id>/card/verify", methods=['POST'])
def verify_user(user_id):
    result = db_user_verify(user_id, request.form["card_num"], request.form["card_exp"], request.form["card_cvv"])
    return result["message"], result["code"]

#Get card for user
@app.route("/users/<user_id>/card", methods=['GET'])
def get_user_card(user_id):
    result = db_get_user_card(user_id)
    if result["card"] is None:
        return result["message"], result["code"]

    return model_as_dict(result["card"]), result["code"]

#Check if email is in use
@app.route("/users/validate-email/<user_email>", methods=['GET'])
def validate_email(user_email):
    user = db_get_user_by_email(user_email)
    if user is None:
        return "Email is safe to use!", 200
    
    return f"Email:{user_email} is already in use.", 409

#Add account balance from card
@app.route("/users/<user_id>/card/balance/transfer/<string:amount>", methods=['POST'])
def card_balance_transfer(user_id, amount):
    result = db_card_balance_transfer(user_id, float(amount))
    return result["message"], result["code"]

#Exchange sell
@app.route("/users/<user_id>/balance/sell-currency/<label>/<float:amount>", methods=['POST'])
def sell_currency(user_id, label, amount):
    result = db_exchange_sell(user_id, label, amount)
    return result['message'], result['code']

#Exchange buy
@app.route("/users/<user_id>/balance/buy-currency/<label>/<float:amount>", methods=['POST'])
def buy_currency(user_id, label, amount):
    result = db_exchange_buy(user_id, label, amount)
    return result['message'], result['code']

#New Transaction to account
@app.route("/users/<user_id>/transactions/new-payment/online", methods=['POST'])
def payment_account(user_id):
    result = db_transaction_account(user_id, request.form['email'], request.form['amount'], request.form['label'])
    return result['message'], result['code']

#New Transaction to card
@app.route("/users/<user_id>/transactions/new-payment/card", methods=['POST'])
def payment_card(user_id):
    result = db_transaction_card(user_id, request.form['card_num'], request.form['amount'])
    return result['message'], result['code']
    
#endregion

#region CardAPI

#Create a new card
@app.route("/cards", methods=['POST'])
def post_card():
    result = crud.create(Card(request.form["card_number"], request.form["username"], request.form["exp_date"], request.form["cvv"]))
    if result["status"] == "success":
        return result["message"], 201
    else:
        return result["message"], 422

#Add balance to card
@app.route("/cards/<card_num>/balance/<string:amount>", methods=['POST'])
def add_balance(card_num, amount):
    amountFloat = float(amount)
    result = db_add_card_balance(card_num, amountFloat)
    return result["message"], result["code"]
    
#Get card by number
@app.route("/cards/<card_num>", methods=['GET'])
def get_card(card_num):
    result = db_get_card(card_num)
    if result is None:
        return result["message"], result["code"]
    else:
        return model_as_dict(result), 200


#endregion

@app.route("/currencys/labels", methods=['GET'])
def get_all_labels():
    labels = db_currency_labels()
    if labels is None:
        return "No labels in db", 404

    return labels, 200
