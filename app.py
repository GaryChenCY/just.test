from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'   # 配置相對於應用程式實例資料夾的 SQLite 資料庫
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = 'your_secret_key'  # 添加SECRET_KEY配置
db = SQLAlchemy(app)  # 使用擴展初始化應用程式
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # 指定登入畫面
login_manager.login_message = 'Please log in to access this page.'

class User(db.Model, UserMixin):  # db.Model定義模型類別的子類別
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phonenumber = db.Column(db.String(20), nullable=False)
    verification_code = db.Column(db.String(6), nullable=True)
    with app.app_context():
        db.create_all()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    with app.app_context():
        db.create_all()

@app.route('/') #尚未註冊、登入瀏覽畫面
def home():
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST']) #後台得登入處理
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



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

@app.route('/send-verification-code', methods=['POST'])     #處理手機驗證碼     """ 這部分出來的驗證碼隨便輸入都能註冊成功，需調整 """
def send_verification_code():
    with app.app_context():
        data = request.json
        phonenumber = data['phonenumber']

        # 產生隨機6位驗證碼
        verification_code = ''.join(random.choices(string.digits, k=6))

        # 檢查是否有重複的驗證碼
        existing_user = User.query.filter_by(verification_code=verification_code).first()
        while existing_user:
            verification_code = ''.join(random.choices(string.digits, k=6))
            existing_user = User.query.filter_by(verification_code=verification_code).first()

        # Here you would implement sending the verification code via SMS
        # For demonstration purposes, we just print it to the console
        print(f'Phone number: {phonenumber}, Verification code: {verification_code}')
    
    return jsonify({'success': True})

@app.route('/admin') #後台網頁 需處理輸入網址就能進後台的問題!!!
@login_required
def admin():
    return render_template('admin.html')

@app.route('/admin/add_product', methods=['POST']) #後台新增產品
@login_required
def add_product():
    # 增加產品邏輯
    name = request.form['product_name']
    description = request.form['product_description']
    price = request.form['product_price']
    image = request.files['product_image']

    """ static/images """ # 新增圖片路徑
    # Save image file to static/images directory (這裡需要處理一下限制圖片大小判斷(尚未處理)!!)
    image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(image_filename)

    product = Product(name=name, description=description, price=price, image=image_filename)
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/products')
@login_required
def get_products():
    # 取得產品列表
    products = Product.query.all()
    product_list = [{'id': product.id, 'name': product.name, 'description': product.description, 'price': product.price, 'image': url_for('static', filename=f'images/{os.path.basename(product.image)}')} for product in products]
    return jsonify({'products': product_list})

@app.route('/admin/delete_product/<int:id>', methods=['DELETE']) #處理後台刪除產品
@login_required
def delete_product(id):
    # 删除產品
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    if not os.path.exists('static/images'):
        os.makedirs('static/images')
    with app.app_context():
        db.create_all()
        # 檢查是否有用户，如果没有則添加一個用户
        if User.query.count() == 0:
            admin_user = User(nickname='admin', email='admin@example.com', password='admin123')
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)


""" 須解決項目 """
# 1 傳送驗證碼問題
# 2 登入405問題
# 3 登入頁面需再精美(商品部分)使用者端尚未能看到後台新增的商品 ，商品訂購按鈕後續尚未完成

# 後台網址登入 http://127.0.0.1:5000/login  帳號:admin@example.com 密碼:admin123，但後台網址還少了登出 和銷售數據 功能

