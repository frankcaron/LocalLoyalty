from wtforms import Form, TextField, validators

class SignupForm(Form):
    first_name = TextField('First Name', [validators.Required(), validators.Length(max=80)])
    last_name = TextField('Last Name', [validators.Required(), validators.Length(max=80)])
    membership_number = TextField(
        label='Membership Number',
        default='dVNm',
        validators=[validators.Required(), validators.Length(max=20)])
    email = TextField('Email Address', [validators.Required(), validators.Length(min=6, max=35)])
