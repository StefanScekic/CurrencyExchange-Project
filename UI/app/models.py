from datetime import datetime
from app import login_manager, users
from flask_login import UserMixin
import requests, json

@login_manager.user_loader
def load_user(user_id):
    req = 'http://localhost:5001/users/' + str(user_id)
    response = requests.get(req)
    if(response.status_code == 200):
        data = response.text
        data_dict = json.loads(data)

        user = User(id=int(data_dict["id"]),
                    first_name=data_dict["first_name"],
                    last_name=data_dict["last_name"],
                    address=data_dict["address"],
                    city=data_dict["city"],
                    state=data_dict["state"],
                    phone=data_dict["phone"],
                    email=data_dict["email"],
                    password=data_dict["password"],
                    verified = bool(data_dict["verified"]),
                    admin = bool(data_dict["admin"]))
        
        user.load_balance((data_dict["balance"]))
        user.load_transactions((data_dict["transactions"]))
        print(user)
        print(user.transactions)
        return user
    else:
        print("Error calling users endpoint")
    #API CALL TO GET CURRENT USER

class User(UserMixin):
    balance = {}
    transactions = []

    def load_transactions(self, transactions):
        self.transactions = transactions

    def load_balance(self, balance):
        self.balance = balance

    def __init__(self, id, first_name, last_name, address, city, state, phone, email, password, verified, admin):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.city = city
        self.state = state
        self.phone = phone
        self.email = email
        self.password = password
        self.verified = verified
        self.admin = admin


    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.address}', '{self.city}', '{self.state}', '{self.phone}', '{self.email}')"


class Card(UserMixin):
    def __init__(self, number, name, expiration_date, safety_code, balance):
        self.id = id
        self.number = number
        self.name = name
        self.expiration_date = expiration_date
        self.safety_code = safety_code
        self.balance = balance
        
    def __repr__(self):
        return f"Card('{self.number}', '{self.name}', '{self.expiration_date}', '{self.safety_code}')"