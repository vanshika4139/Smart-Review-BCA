from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import os

app = Flask(__name__)

# Render ya local dono ke liye database path automatic handle karne ke liye
db_path = os.path.join(os.path.dirname(__file__), 'smart_review.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. DATABASE MODELS
class Product(db.Model):
    __tablename__ = 'mera_products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    reviews = db.relationship('Review', backref='product', lazy=True)

class Review(db.Model):
    __tablename__ = 'mera_reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('mera_products.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    sentiment_label = db.Column(db.String(20), nullable=False)
    aspects = db.Column(db.Text, nullable=True)

# Helper function jo database create bhi karega aur seed bhi karega
def init_db_safely():
    db.create_all()
    if Product.query.count() == 0:
        p1 = Product(name="Wireless ANC Headphones", description="High-quality sound with hybrid active noise cancellation.", category="Electronics", image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500")
        p2 = Product(name="Smart Fitness Watch", description="Amoled display with real-time heart rate and sleep tracking.", category="Electronics", image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500")
        p3 = Product(name="Ergonomic Gaming Mouse", description="Ultra-lightweight gaming mouse with customizable RGB.", category="Accessories", image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500")
        db.session.add_all([p1, p2, p3])
        db.session.commit()

# 2. APPLICATION ROUTES
@app.route('/')
def homepage():
    # Yeh line har baar check karegi ki database bana hai ya nahi, cloud par safe rehne ke liye
    init_db_safely()
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    pos_count = Review.query.filter_by(product_id=product_id, sentiment_label='Positive').count()
    neg_count = Review.query.filter_by(product_id=product_id, sentiment_label='Negative').count()
    neu_count = Review.query.filter_by(product_id=product_id, sentiment_label='Neutral').count()
    
    return render_template('product.html', product=product, pos=pos_count, neg=neg_count, neu=neu_count)

@app.route('/add_review/<int:product_id>', methods=['POST'])
def add_review(product_id):
    text = request.form.get('review_text')
    rating = int(request.form.get('rating'))
    
    lower_text = text.lower()
    if any(word in lower_text for word in ['bad', 'worst', 'bekar', 'waste', 'slow', 'ghatiya']):
        sentiment = 'Negative'
    elif any(word in lower_text for word in ['good', 'best', 'achha', 'awesome', 'love', 'mast']):
        sentiment = 'Positive'
    else:
        sentiment = 'Neutral'
        
    aspect_data = json.dumps({"Performance": sentiment, "Price": "Positive"})

    new_review = Review(
        product_id=product_id,
        review_text=text,
        rating=rating,
        sentiment_label=sentiment,
        aspects=aspect_data
    )
    db.session.add(new_review)
    db.session.commit()
    
    return redirect(url_for('product_detail', product_id=product_id))

if __name__ == '__main__':
    app.run(debug=True)
