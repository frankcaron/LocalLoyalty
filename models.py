from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    membership_number = db.Column(db.String(20))
    email = db.Column(db.String(35))
    mv_url = db.Column(db.String(50), unique=True)
    foursquare_id = db.Column(db.Integer)
    credit_url = db.Column(db.String(50), unique=True)

    def __init__(self, first_name, last_name, membership_number, email):
        self.first_name = first_name
        self.last_name = last_name
        self.membership_number = membership_number
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.membership_number

    def save(self):
        db.session.add(self)
        db.session.commit()
