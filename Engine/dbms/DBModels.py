from datetime import datetime
from app import db
from enum import Enum

#region Enumeracije
class TransactionState(Enum):
    in_progress = 'U obradi'
    accepted = 'Odobreno'
    rejected = 'Odbijeno'

class TransactionTarget(Enum):
    account = 'Online racun'
    card = 'Kartica'

class TransactionType(Enum):
    in_favor = 'Uplata u korist'
    at_the_expense = 'Uplata na teret'
#endregion

#region Modeli
user_currency = db.Table('user_currency',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('currency_id', db.Integer, db.ForeignKey('currency.id'), primary_key=True),
    db.Column('amount', db.Float, default=0)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(20), nullable = False)
    last_name = db.Column(db.String(20), nullable = False)
    address = db.Column(db.String(50), nullable = False)
    city = db.Column(db.String(20), nullable = False)
    state = db.Column(db.String(20), nullable = False)
    phone = db.Column(db.String(50), nullable = False, unique = True)
    email = db.Column(db.String(50), nullable = False, unique = True)
    password = db.Column(db.String(200), nullable = False)
    verified = db.Column(db.Boolean(), default = False)
    admin = db.Column(db.Boolean(), default = False)

    card = db.relationship('Card', backref = 'owner', lazy=True, uselist=False)
    transactions = db.relationship('Transaction', backref = 'payer', lazy=True)
    balance = db.relationship('Currency', secondary=user_currency)

    def balance_list(self):
        temp_value = db.session.query(user_currency).filter_by(user_id = self.id).all()
        return {(Currency.query.filter_by(id=item[1]).first()).label : item[2] for item in temp_value}

    def __init__(self, first_name, last_name, address, city, state, phone, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.city = city
        self.state = state
        self.phone = phone
        self.email = email
        self.password = password

    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.address}', '{self.city}', '{self.state}', '{self.phone}', '{self.email}')"

class Card(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    number = db.Column(db.String(25), nullable = False, unique = True)
    username = db.Column(db.String(100), nullable = False)
    expiration_date = db.Column(db.String(15), nullable = False)
    safety_code = db.Column(db.String(5), nullable = False)
    balance = db.Column(db.Float(), default = 0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, number, username, expiration_date, safety_code):
        self.number = number
        self.username = username
        self.expiration_date = expiration_date
        self.safety_code = safety_code
        
    def __repr__(self):
        return f"Card('{self.number}', '{self.expiration_date}', '{self.safety_code}')"

    def to_dict(self):
        return {
            "id" : self.id,
            "number" : self.number,
            "username" : self.username,
            "expiration_date" : self.expiration_date,
            "safety_code" : self.safety_code,
            "balance" : self.balance,
            "user_id" : self.user_id
        }
 
class Currency(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    label = db.Column(db.String(5), unique = True)
    per = db.Column(db.Float())

    def __init__(self, label, per):
            self.label = label
            self.per = per

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "per": self.per
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    recipient = db.Column(db.Integer, nullable = False)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    label = db.Column(db.String(5), nullable = False)
    amount = db.Column(db.Float, nullable = False)
    change = db.Column(db.String(50), nullable = False)
    target = db.Column(db.String, nullable = False)
    status = db.Column(db.String, default = TransactionState.in_progress.value)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, recipient, label, amount, change, target, user_id):
            self.recipient = recipient
            self.label = label
            self.amount = amount
            self.change = change
            self.target = target
            self.user_id = user_id

    def to_dict(self):
        return {
            "id": self.id,
            "recipient": self.recipient,
            "date": self.date,
            "label": self.label,
            "amount" : self.amount,
            "change" : self.change,
            "target" : self.target,
            "status" : self.status,
            "user_id" : self.user_id
        }

#endregion