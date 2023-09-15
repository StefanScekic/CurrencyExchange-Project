import os
import secrets
import requests
from flask import render_template, url_for, flash, redirect, request, abort
from app.models import User, Card
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, VerifyCardForm, AddAssetsForm, SellForm, BuyForm, TransactionForm, AddAssetsToCardForm
from app import app, bcrypt, users
from flask_login import login_user, logout_user, login_required, current_user
from app.apicalls import *
from urllib.parse import quote
import json

labels_request = 'http://localhost:5001/currencys/labels'
labels_response = requests.get(labels_request)
if labels_response.status_code == 200:
    labels = [item[0] for item in json.loads(labels_response.text)]
    #print(labels)
else:
    labels = []

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        
        req = 'http://localhost:5001/users'
        
        data = {
            "first_name": form.first_name.data,
            "last_name": form.last_name.data,
            "address": form.address.data,
            "city": form.city.data,
            "state": form.state.data,
            "phone": form.phone.data,
            "email": form.email.data,
            "password": hashed_password
        }

        response = requests.post(req, data=data)
        if(response.status_code == 201):
            print("All clear")
        else:
            print(f"Error calling postuser endpoint, error code {response.status_code}")
            return redirect(url_for('register'))

        flash(f'Your account has been created you can now log in!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        req = 'http://localhost:5001/users/' + form.email.data
        print(form.email.data)
        response = requests.get(req)
        if(response.status_code == 200):
            data = response.text
            data_dict = json.loads(data)
            print(data)
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
        else:
            print("Error calling users endpoint")
        print(user.password)
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        print(hashed_password)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/')
        else:
            flash('Login unsuccessful, please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()

    if form.validate_on_submit():
        req = 'http://localhost:5001/users/' + str(current_user.id)
        
        data = {
            "first_name": form.first_name.data,
            "last_name": form.last_name.data,
            "address": form.address.data,
            "city": form.city.data,
            "state": form.state.data,
            "phone": form.phone.data,
            "email" : current_user.email
        }
        
        response = requests.post(req, data=data)
        if(response.status_code == 200):
            print("All clear")    
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.address = form.address.data
            current_user.city = form.city.data
            current_user.state = form.state.data
            current_user.phone = form.phone.data
            flash('Your account has been updated!', 'success')
            return redirect(url_for('profile'))
        else:
            print("Error calling postuser endpoint")
        
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.phone.data = current_user.phone
        
    return render_template('profile.html', title='Profile', form=form)


@app.route("/verify", methods=['GET', 'POST'])
@login_required
def verify():
    form = VerifyCardForm()
    if form.validate_on_submit():
        req = 'http://localhost:5001/users/' + str(current_user.id) + '/card/verify'
        
        data = {
            "card_num" : form.number.data,
            "card_exp" : form.expiration_date.data,
            "card_cvv" : form.safety_code.data
        }
        
        response = requests.post(req, data=data)
        if(response.status_code == 200):
            print("All clear")
            flash(f'Your card has been successfully verified and attached to your account!', 'success')
            return redirect(url_for('index'))
        else:
            print(response.text)
            print("Error calling verifycard endpoint")
    return render_template('verify.html', title='Verify', form=form)


@app.route("/assets", methods=['GET', 'POST'])
@login_required
def assets():
    req = 'http://localhost:5001/users/' + str(current_user.id) + '/card'
    response = requests.get(req)
    if(response.status_code == 200):
        data = response.text
        card_dict = json.loads(data)
        card = Card(card_dict["number"],
                    card_dict["username"],
                    card_dict["expiration_date"],
                    card_dict["safety_code"],
                    card_dict["balance"])
    else:
        print("Error calling getcard endpoint")
    requ = 'http://localhost:5001/users/' + str(current_user.id)
    resp = requests.get(requ)
    if(resp.status_code == 200):
        data = resp.text
        data_dict = json.loads(data)
        print(data)
        balance_data = data_dict["balance"];
        print(balance_data)
        print("All clear") 
        balance = ""
        for key in balance_data:
            balance += key
            balance += " : "
            balance += str(balance_data[key])
            balance += "\n"
        else:
            print("Error calling ")
    return render_template('assets_info.html', title='Assets', card=card, balance=balance)


@app.route("/assets_add", methods=['GET', 'POST'])
@login_required
def assets_add():
    form = AddAssetsForm()
    if form.validate_on_submit():
        req = 'http://localhost:5001/users/' + str(current_user.id) + '/card/balance/transfer/' + str(form.amount.data)
        response = requests.post(req)
        if(response.status_code == 200):
            print("All clear")
        else:
            print("Error calling addassets endpoint")
    requ = 'http://localhost:5001/users/' + str(current_user.id)
    resp = requests.get(requ)
    if(resp.status_code == 200):
        data = resp.text
        data_dict = json.loads(data)
        print(data)
        balance_data = data_dict["balance"];
        print(balance_data)
        print("All clear") 
        balance = ""
        for key in balance_data:
            balance += key
            balance += " : "
            balance += str(balance_data[key])
            balance += "\n"
        else:
            print("Error calling ")
    req = 'http://localhost:5001/users/' + str(current_user.id) + '/card'
    response = requests.get(req)
    if(response.status_code == 200):
        data = response.text
        card_dict = json.loads(data)
        
        card = Card(card_dict["number"],
                    card_dict["username"],
                    card_dict["expiration_date"],
                    card_dict["safety_code"],
                    card_dict["balance"])
    else:
        print("Error calling getcard endpoint")
    return render_template('assets_add.html', title='Add Assets', card=card, form=form, balance=balance)


@app.route("/history", methods=['GET', 'POST'])
@login_required
def history():    
    return render_template('history.html', title="History", transactions=current_user.transactions)


@app.route("/add_card", methods=['GET', 'POST'])
@login_required
def add_card():
    form = VerifyCardForm()
    if form.validate_on_submit():
        req = 'http://localhost:5001/cards'
        
        data = {
            "username" : current_user.first_name + ' ' + current_user.last_name,
            "card_number" : form.number.data,
            "exp_date" : form.expiration_date.data,
            "cvv" : form.safety_code.data
        }
        
        response = requests.post(req, data=data)
        if(response.status_code == 201):
            print("All clear")
            flash(f'Card has been created succesfully!', 'success')
            return redirect(url_for('index'))
        else:
            print(response.text)
            print("Error calling verifycard endpoint")
    return render_template('add_card.html', title='Add card', form=form)

@app.route("/exchange", methods=["GET", "POST"])
def exchange():
    
    form_buy = BuyForm()
    form_sell = SellForm()

    form_buy.currency.choices = labels
    form_sell.currency.choices = [item for item in current_user.balance]

    if form_buy.validate_on_submit():
        user_id = current_user.id
        label = form_buy.currency.data
        amount = form_buy.amount.data
        response = requests.post(f'http://localhost:5001/users/{user_id}/balance/buy-currency/{label}/{amount}')
        message, code = response.text, response.status_code
        if code == 200:
            flash(f'{message}', 'success')
        else :
            flash(f'{message}', 'danger')
        return redirect(url_for('exchange'))

    if form_sell.validate_on_submit():
        user_id = current_user.id
        label = form_sell.currency.data
        amount = form_sell.amount.data
        response = requests.post(f'http://localhost:5001/users/{user_id}/balance/sell-currency/{label}/{amount}')
        message, code = response.text, response.status_code
        if code == 200:
            flash(f'{message}', 'success')
        else :
            flash(f'{message}', 'danger')
        return redirect(url_for('exchange'))

    return render_template("exchange.html", form_buy=form_buy, form_sell = form_sell)

@app.route("/add_assets_card", methods=['GET', 'POST'])
@login_required
def add_assets_card():
    form = AddAssetsToCardForm()
    if form.validate_on_submit():
        req = 'http://localhost:5001/cards/' + form.number.data + '/balance/' + str(form.amount.data)
        response = requests.post(req)
        if response.status_code == 200:
            flash(f'Assets succesfully added to card!', 'success')
            return redirect(url_for('index'))
        else:
            print(response.text)
            print("Error calling add assets to card endpoint")
    return render_template('add_assets_card.html', title='Add assets to card', form=form)


@app.route("/transactions", methods=['GET', 'POST'])
@login_required
def transactions():
    form = TransactionForm()
    if form.validate_on_submit():
        req = 'http://localhost:5001/users/' + form.email.data
        response = requests.get(req)
        if response.status_code == 200:
            #Transaction by account
            req = f'http://localhost:5001/users/{current_user.id}/transactions/new-payment/online'
            
            data = {
                "email" : form.email.data,
                "amount" : form.amount.data,
                "label" : form.currency.data
            }
            
            response = requests.post(req, data=data)
            message, code = response.text, response.status_code
            if code == 200:
                flash(f'{message}', 'success')
                return redirect(url_for('index'))
            else :
                flash(f'{message}', 'danger')
                return redirect(url_for('index'))
        req = 'http://localhost:5001/cards/' + form.email.data
        response = requests.get(req)
        if response.status_code == 200:
            #Transaction by card
            req = f'http://localhost:5001/{current_user.id}/transactions/new-payment/card'
            
            data = {
                "card_num" : form.email.data,
                "amount" : form.amount.data
            }
            
            response = requests.post(req, data=data)
            message, code = response.text, response.status_code
            if code == 200:
                flash(f'{message}', 'success')
                return redirect(url_for('index'))
            else :
                flash(f'{message}', 'danger')
                return redirect(url_for('index'))
    return render_template('transaction.html', title='Transaction', form=form, currencies = [item for item in current_user.balance])
