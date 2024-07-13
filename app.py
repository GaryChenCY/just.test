from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phonenumber = db.Column(db.String(20), nullable=False)
    verification_code = db.Column(db.String(6), nullable=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/signup', methods=['POST'])
def signup():
    with app.app_context():
        nickname = request.form['nickname']
        email = request.form['email']
        password = request.form['password']
        phonenumber = request.form['phonenumber']
        verification = request.form['verification']

        user = User(nickname=nickname, email=email, password=password, phonenumber=phonenumber, verification_code=verification)
        db.session.add(user)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/send-verification-code', methods=['POST'])
def send_verification_code():
    with app.app_context():
        data = request.json
        phonenumber = data['phonenumber']

        # Generate a random 6-digit verification code
        verification_code = ''.join(random.choices(string.digits, k=6))

        # Check for duplicate codes
        existing_user = User.query.filter_by(verification_code=verification_code).first()
        while existing_user:
            verification_code = ''.join(random.choices(string.digits, k=6))
            existing_user = User.query.filter_by(verification_code=verification_code).first()

        # Here you would implement sending the verification code via SMS
        # For demonstration purposes, we just print it to the console
        print(f'Phone number: {phonenumber}, Verification code: {verification_code}')

    return jsonify({'success': True})

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/admin/delete_product/<int:id>', methods=['DELETE'])
def delete_product(id):
    with app.app_context():
        product = Product.query.get(id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    with app.app_context():
        name = request.form['product_name']
        description = request.form['product_description']
        price = request.form['product_price']
        image = request.files['product_image']

        # Save image file to static/images directory
        image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_filename)

        product = Product(name=name, description=description, price=price, image=image_filename)
        db.session.add(product)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/products')
def get_products():
    with app.app_context():
        products = Product.query.all()
        product_list = [{'id': product.id, 'name': product.name, 'description': product.description, 'price': product.price, 'image': url_for('static', filename=f'images/{os.path.basename(product.image)}')} for product in products]
    return jsonify({'products': product_list})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
