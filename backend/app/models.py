from app import db
from datetime import datetime, timezone

# user model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # relationship with Porfolio (1 user has N porfolios)
    portfolios = db.relationship('Portfolio', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

# portfel model
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # foreign key connect with uiser
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # relationship with shares (1 portfolio has N shares)
    stocks = db.relationship(
        'Stock', 
        backref='portfolio', 
        lazy='dynamic',
        cascade="all, delete-orphan" # delete portfolio -> delete all stocks
    )

    def __repr__(self):
        return f'<Portfolio {self.name}>'

# model of single stock/share in portfoio
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False) # i.e. "AAPL"
    shares = db.Column(db.Numeric(10, 4), nullable=False) # stock number (moze byc ulamkowa)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False) # purchase price
    purchase_date = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    
    # foreign key connect with protfolio
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)

    def __repr__(self):
        return f'<Stock {self.ticker}, Shares: {self.shares}>'