from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User
import requests
import json

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=20)])
    address = StringField('Address', validators=[DataRequired(), Length(min=2, max=40)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=20)])
    state = StringField('State', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_email(self, email):
        req = 'http://localhost:5001/users/validate-email/' + email.data
        print(email.data)
        response = requests.get(req)
        if(response.status_code == 200):
            return
        else:
            raise ValidationError("That email is taken. Please choose a different one!")
         
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')    
    
class UpdateAccountForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=20)])
    address = StringField('Address', validators=[DataRequired(), Length(min=2, max=40)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=20)])
    state = StringField('State', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Update')            
        
class VerifyCardForm(FlaskForm):
    number = StringField('Card Number', validators=[DataRequired()])
    expiration_date = StringField('Expiration Date', validators=[DataRequired()])
    safety_code = StringField('Safety Code', validators=[DataRequired()])
    submit = SubmitField('Verify') 
    
class AddAssetsForm(FlaskForm):
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=0, message='Must enter a number greater than 0')])
    submit = SubmitField('Add')

class BuyForm(FlaskForm):
    currency = SelectField("Currency:", choices=[])
    amount = FloatField("Amount:")
    submit = SubmitField("Submit")

class SellForm(FlaskForm):
    currencies = [("EUR", "EUR"), ("USD", "USD")]
    currency = SelectField("Currency:", choices=[])
    amount = FloatField("Amount:")
    submit = SubmitField("Submit")
  
class AddAssetsToCardForm(FlaskForm):
    number = StringField('Card Number', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0, message='Must enter a number greater than 0')])
    submit = SubmitField('Add')
    
class TransactionForm(FlaskForm):
    email = StringField('Email / Card Number', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0, message='Must enter a number greater than 0')])
    currency = StringField('Label', validators=[DataRequired()])
    submit = SubmitField('Send')
