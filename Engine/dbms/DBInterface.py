from app import app, db
from urllib.parse import unquote
from dbms.DBModels import User, Card, Currency, Transaction, user_currency, TransactionState, TransactionTarget, TransactionType
import json
from requests import get
import time

from sqlalchemy import update

with app.app_context():
        #db.drop_all()
        db.create_all()

class CRUD:
    def __init__(self):
        self.session = db.session

    def create(self, model):
        try:
            self.session.add(model)
            self.session.commit()
            return {"status": "success", "message": "Success!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def read(self, model, id):
        return self.session.query(model).filter(model.id == id).first()

    def update(self, model, id, updates):
        try:
            self.session.query(model).filter(model.id == id).update(updates)
            self.session.commit()
            return {"status": "success", "message": "Success!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def delete(self, model, id):
        self.session.query(model).filter(model.id == id).delete()
        self.session.commit()

#get the id of label
def db_get_currency_id(label):
    curr = Currency.query.filter_by(label = label).first()
    return curr.id

#Exchange A to amount B, returns amount needed to get amount of B
def db_exchange_to(curr_a, curr_b, amount):
    currency_a = Currency.query.filter_by(label = curr_a).first()
    if currency_a is None:
        return {"message": f"Currency with label:{curr_a} not found.", "code":503}

    currency_b = Currency.query.filter_by(label = curr_b).first()
    if currency_b is None:
        return {"message": f"Currency with label:{curr_b} not found.", "code":503}
      
    return {"result": (amount / currency_b.per)*currency_a.per, "code":200}

#Exchange amount A for B, returns num of B you will get for amount of A
def db_exchange_from(curr_a, curr_b, amount):
    currency_a = Currency.query.filter_by(label = curr_a).first()
    if currency_a is None:
        return {"message": f"Currency with label:{curr_a} not found.", "code":404}

    currency_b = Currency.query.filter_by(label = curr_b).first()
    if currency_b is None:
        return {"message": f"Currency with label:{curr_b} not found.", "code":503}
      
    return {"result": (amount / currency_a.per)*currency_b.per, "code":200}

#Find a user with a specified email
def db_get_user_by_email(user_email) -> User:
    user = User.query.filter_by(email=user_email).first()    
    return user

#Get the email of a User with specified ID
def db_get_email_by_id(user_id : int):
    user = User.query.filter_by(id=user_id).first()
    if user:
        return user.email
    else:
        return None

#Add balance to card
def db_add_card_balance(card_num, amount):
    card = Card.query.filter_by(number = card_num).first()
    if card is None:
        return {"message": f"Card with number:{card_num} not found", "code":400}

    card.balance += amount
    db.session.commit()
    return {"message": "Success!", "code":200}

#Verify user
def db_user_verify(user_id, card_num, card_exp, card_cvv):
    user = User.query.get(user_id)
    if user is None:
        return {"message":f"User with id:{user_id} not found", "code":400}
    
    card = Card.query.filter_by(number = card_num).first()
    if card is None:
        return {"message": "Invalid card information", "code":422}
    if card.expiration_date != card_exp:
        return {"message": "Invalid card information", "code":422}
    if card.safety_code != card_cvv:
        return {"message": "Invalid card information", "code":422}

    amount_needed = db_exchange_to('RSD','USD',1)
    if amount_needed["code"] != 200:
        return amount_needed
    if card.balance < amount_needed["result"]:
        return {"message": "Payment needed", "code":402}

    card.balance -= amount_needed["result"]
    user.verified = True
    card.user_id = user_id

    currency = Currency.query.filter_by(label = 'RSD').first()
    if currency is None:
        return {"message": "There are no exchange rates in the DataBase", "code":503}

    user.balance.append(currency)

    db.session.commit()

    return {"message": "Success!", "code":200}

#Try to get user's card
def db_get_user_card(user_id):
    user = User.query.get(user_id)
    if user is None:
        return {"message":f"User with id:{user_id} not found", "code":400, "card": None}

    if user.card is None:
        return {"message": "User is not verified", "code": 404, "card": None}

    return {"message": "Success!", "code": 200, "card": user.card}

#Load exchange rates to db
def get_exchange_rate_and_save():
    api_url = 'https://open.er-api.com/v6/latest/RSD'
    response = get(api_url)
    exchange_rate_data = response.json()

    for key in exchange_rate_data["rates"]:
        #print(key)
        if exchange_rate_data["rates"][key] is int:
            continue
        db.session.add(Currency(key, exchange_rate_data["rates"][key]))

    db.session.commit()

#Get all currency labels
def db_currency_labels():
    labels = db.session.query(Currency.label).all()
    if labels is None:
        return None
    labels = [tuple(row) for row in labels]
    return json.dumps(labels)

#Transfer money from card to online accout
def db_card_balance_transfer(user_id, new_amount):
    user = User.query.get(user_id)
    if user is None:
        return {"message":f"User with id:{user_id} not found.", "code":404}

    if user.verified == False:
        return {"message":"User is not verified.", "code":401}

    if user.card.balance < new_amount:
        return {"message": "Amount asked to transfer is greater then card balance.", "code":402}

    
    user.card.balance -= new_amount
    temp_curr = db.session.query(user_currency).filter_by(user_id = user.id, currency_id= db_get_currency_id('RSD')).first()

    stmt = update(user_currency).where(
        (user_currency.c.user_id == user.id) &
        (user_currency.c.currency_id == db_get_currency_id('RSD'))
    ).values(amount=temp_curr.amount + new_amount)
    db.session.execute(stmt)

    db.session.commit()
    return {"message":"Success!", "code":200}

#Buy currency
def db_exchange_buy(f_user_id, f_label, amount):
    user = User.query.filter_by(id=f_user_id).first()
    if user is None:
        return {"message":f"User with id:{f_user_id} not found.", "code":404}

    exchange_result = db_exchange_to('RSD', f_label, amount)
    if exchange_result['code'] != 200:
        return exchange_result

    amount_needed = exchange_result['result']

    user_rsd = db.session.query(user_currency).filter_by(user_id = user.id, currency_id= db_get_currency_id('RSD')).first()
    if user_rsd.amount < amount_needed:
        return {"message": "Insufficient founds.", "code":402}

    target_currency = Currency.query.filter_by(label=f_label).first()
    if target_currency not in user.balance:
        user.balance.append(target_currency)

    user_target = db.session.query(user_currency).filter_by(user_id = user.id, currency_id= target_currency.id).first()

    stmt = update(user_currency).where(
        (user_currency.c.user_id == user.id) &
        (user_currency.c.currency_id == db_get_currency_id('RSD'))
    ).values(amount=user_rsd.amount - amount_needed)
    db.session.execute(stmt)

    stmt = update(user_currency).where(
        (user_currency.c.user_id == user.id) &
        (user_currency.c.currency_id == target_currency.id)
    ).values(amount=user_target.amount + amount)
    db.session.execute(stmt)

    db.session.commit()

    return {"message":f"Account was charged for {amount_needed:.2f}RSD", "code":200}

#sell currency
def db_exchange_sell(f_user_id, f_label, amount):
    user = User.query.filter_by(id=f_user_id).first()
    if user is None:
        return {"message":f"User with id:{f_user_id} not found.", "code":404}

    exchange_result = db_exchange_from(f_label, 'RSD', amount)
    if exchange_result['code'] != 200:
        return exchange_result

    amount_to_add = exchange_result['result']
    
    source_currency_id = db_get_currency_id(f_label)
    user_source = db.session.query(user_currency).filter_by(user_id = user.id, currency_id= source_currency_id).first()
    if user_source.amount < amount:
        return {"message": "Insufficient founds.", "code":402}

    user_rsd = db.session.query(user_currency).filter_by(user_id = user.id, currency_id= db_get_currency_id('RSD')).first()

    stmt = update(user_currency).where(
        (user_currency.c.user_id == user.id) &
        (user_currency.c.currency_id == db_get_currency_id('RSD'))
    ).values(amount=user_rsd.amount + amount_to_add)
    db.session.execute(stmt)

    stmt = update(user_currency).where(
        (user_currency.c.user_id == user.id) &
        (user_currency.c.currency_id == source_currency_id)
    ).values(amount=user_source.amount - amount)
    db.session.execute(stmt)

    db.session.commit()

    return {"message":f"{amount_to_add:.2f}RSD has been added to the Account", "code":200}

#Begin Transaction
def db_beggin_transaction(f_user_id, f_amount: float, f_curr_label, f_trans):
    user = User.query.filter_by(id=f_user_id).first()
    transaction = Transaction.query.filter_by(id=f_trans.id).first()
    f_amount = float(f_amount)

    #time.sleep(10)
    cur_check = Currency.query.filter_by(label=f_curr_label).first()
    if cur_check not in user.balance:
        transaction.status = TransactionState.rejected.value
        db.session.commit()
        return
        
    user_curr_beggining_amount = db.session.query(user_currency).filter_by(user_id = user.id, currency_id= db_get_currency_id(f_curr_label)).first()

    if user_curr_beggining_amount.amount < f_amount:
        transaction.status = TransactionState.rejected.value
        db.session.commit()
        return

    stmt = update(user_currency).where(
        (user_currency.c.user_id == user.id) &
        (user_currency.c.currency_id == db_get_currency_id(f_curr_label))
    ).values(amount=user_curr_beggining_amount.amount - f_amount)
    db.session.execute(stmt)

    recipient = User.query.filter_by(id=f_trans.recipient).first()

    if f_trans.target == TransactionTarget.card.value:
        rec_card = User.query.filter_by(id=recipient.id).first()        
        rec_card.card.balance += f_amount
    else:
        target_currency = Currency.query.filter_by(label=f_curr_label).first()
        if target_currency not in recipient.balance:
            recipient.balance.append(target_currency)
        rec_curr_beggining_amount = db.session.query(user_currency).filter_by(user_id = recipient.id, currency_id= db_get_currency_id(f_curr_label)).first()

        stmt = update(user_currency).where(
        (user_currency.c.user_id == f_trans.recipient) &
        (user_currency.c.currency_id == db_get_currency_id(f_curr_label))
        ).values(amount=rec_curr_beggining_amount.amount + f_amount)
        db.session.execute(stmt)

    
    transaction.status = TransactionState.accepted.value

    db.session.commit()

#Transaction to card
def db_transaction_card(f_user_id, f_card_num, f_amount:float):
    user = User.query.filter_by(id=f_user_id).first()
    if user is None:
        return {"message":f"User with id:{f_user_id} not found.", "code":404}

    card = Card.query.filter_by(number = f_card_num).first()
    if card is None:
        return {"message": f"Card with number:{f_card_num} not found", "code":400}

    trans = Transaction(card.owner.id, 'RSD', f_amount, TransactionType.at_the_expense.value, TransactionTarget.card.value, f_user_id)
    db.session.add(trans)
    for item in user.transactions:
        if item == trans:
            trans = item
    
    db.session.commit()   

    #promeniti da spawnuje poseban proces kad bude trebalo 
    db_beggin_transaction(f_user_id, f_amount, 'RSD', trans)

    return {"message": f"Transaction created.", "code":200}

#Transaction to account
def db_transaction_account(f_user_id, f_acc_email, f_amount:float, f_label):
    user = User.query.filter_by(id=f_user_id).first()
    if user is None:
        return {"message":f"User with id:{f_user_id} not found.", "code":404}

    recipient = User.query.filter_by(email=f_acc_email).first()
    if recipient is None:
        return {"message": f"User with email:{f_acc_email} not found", "code":400}

    trans = Transaction(recipient.id, f_label, f_amount, TransactionType.at_the_expense.value, TransactionTarget.account.value, f_user_id)
    db.session.add(trans)
    for item in user.transactions:
        if item == trans:
            trans = item
    
    db.session.commit()   

    #promeniti da spawnuje poseban proces kad bude trebalo 
    db_beggin_transaction(f_user_id, f_amount, f_label, trans)

    return {"message": f"Transaction created.", "code":200}

#Get card by number
def db_get_card(f_card_num):
    card = Card.query.filter_by(number=f_card_num).first()
    if card is None:
        return {"message" : f"Card with number: {f_card_num} not found", "code":400}
    else:
        return card