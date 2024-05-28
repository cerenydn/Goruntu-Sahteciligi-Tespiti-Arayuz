from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import sqlite3
import shutil
from PIL import Image
import numpy as np
from keras.models import load_model
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Flask-Login yapılandırması
login_manager = LoginManager()
login_manager.init_app(app)

# Kullanıcı sınıfı tanımı
class User(UserMixin):
    def __init__(self, user_id, role):
        self.id = user_id
        self.role = role

    @property
    def is_admin(self):
        return self.role == 'admin'


# Kullanıcı kimliğini yükleyen fonksiyon
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['role'])
    return None

# Veritabanı bağlantısı fonksiyonu
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanını başlatma fonksiyonu
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    conn.commit()
    conn.close()

# Veritabanını başlat
init_db()

# Admin oluşturma fonksiyonu
def create_admin(email, password):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (ad, soyad, email, password, role) VALUES (?, ?, ?, ?, ?)', 
                     ('Admin', 'User', email, password, 'admin'))
        conn.commit()
        print(f"{email} isimli kullanıcı başarıyla yönetici olarak tanımlandı.")
    except sqlite3.IntegrityError:
        print("Bu e-posta adresi zaten bir kullanıcıya aittir.")
    finally:
        conn.close()


# Örnek bir yönetici oluşturma
create_admin('ydnceren00@gmail.com', '123')

# Giriş sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()
        if user:
            user_obj = User(user['id'], user['role'])
            login_user(user_obj)
            flash('Giriş başarılı', 'success')
            return redirect(url_for('index'))
        else:
            flash('Geçersiz e-posta veya şifre', 'danger')
    return render_template('login.html')

# Çıkış sayfası
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Çıkış yapıldı', 'success')
    return redirect(url_for('index'))

# Yetkilendirilmiş sayfa
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# TensorFlow uyarılarını sessize alma
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Keras modelini yükleme
model = load_model('my_model.h5')

# Resmi hazırlama fonksiyonu
def prepare_image(image, target_size=(128, 128)):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = np.array(image) / 255.0
    return image

@app.route('/', methods=['GET'])
def index():
    user_name = session.get('user_name')
    return render_template('index.html', user_name=user_name)

@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = f"{user['ad']} {user['soyad']}"
            flash('Giriş Başarılı', 'success')
            return redirect(url_for('index'))
        else:
            flash('E-posta veya şifre yanlış!', 'danger')
    return render_template('giris.html')

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (ad, soyad, email, password, role) VALUES (?, ?, ?, ?, ?)', 
                         (ad, soyad, email, password, 'user'))
            conn.commit()
            flash('Başarıyla kayıt oldunuz!', 'success')
            return redirect(url_for('giris'))
        except sqlite3.IntegrityError:
            flash('Bu e-posta adresi zaten kayıtlı.', 'danger')
        finally:
            conn.close()
    return render_template('kayit.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        image = Image.open(file.stream)
        prepared_image = prepare_image(image)
        prepared_image = prepared_image.reshape(-1, 128, 128, 3)
        
        prediction = model.predict(prepared_image)
        prediction_class = np.round(prediction[0][0])
        
        class_names = ['Forged', 'Authentic']
        result = {
            "prediction": class_names[int(prediction_class)],
            "confidence": f"{(1 - prediction[0][0]) * 100:.2f}%" if prediction[0][0] <= 0.5 else f"{(prediction[0][0]) * 100:.2f}%"
        }

        return jsonify(result)
    
    return "Error"

@app.route('/hakkimizda')
def hakkimizda():
    return render_template('hakkimizda.html')

@app.route('/iletisim')
def iletisim():
    return render_template('iletisim.html')

@app.route('/yardim')
def yardim():
    return render_template('yardim.html')

# Veritabanı yedekleme ve geri yükleme işlemleri
def backup_database():
    conn = get_db_connection()
    with open('database_backup.sql', 'w') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    conn.close()

def restore_database():
    conn = get_db_connection()
    with open('database_backup.sql', 'r') as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.close()

@app.route('/backup')
def backup():
    if 'user_id' not in session:
        flash('Bu işlemi yapabilmek için giriş yapmalısınız.', 'danger')
        return redirect(url_for('giris'))
    backup_database()
    flash('Veritabanı yedeği başarıyla oluşturuldu.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/restore')
def restore():
    if 'user_id' not in session:
        flash('Bu işlemi yapabilmek için giriş yapmalısınız.', 'danger')
        return redirect(url_for('giris'))
    restore_database()
    flash('Veritabanı yedeği başarıyla geri yüklendi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '' and uploaded_file.filename is not None:
            uploaded_file.save(os.path.join('static/uploads', uploaded_file.filename))
    return render_template('upload.html')

# Yönetim paneli
@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('index'))
    return render_template('admin_panel.html')


# Örnek bir kullanıcı veritabanı
users = [
    {'username': 'admin', 'role': 'admin'},
    {'username': 'user1', 'role': 'standard'},
    {'username': 'user2', 'role': 'standard'}
]

# Kullanıcıları görüntüleme
@app.route('/users')
def view_users():
    return render_template('view_users.html', users=users)

# Yeni kullanıcı ekleme
@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        users.append({'username': username, 'role': role})
        return redirect(url_for('view_users'))
    return render_template('add_user.html')

# Yetkilendirme seviyelerini ayarlama
@app.route('/users/roles', methods=['GET', 'POST'])
def set_roles():
    if request.method == 'POST':
        new_roles = request.form.getlist('role')
        for idx, user in enumerate(users):
            users[idx]['role'] = new_roles[idx]
        return redirect(url_for('view_users'))
    return render_template('set_roles.html', users=users)

from flask import jsonify

@app.route("/get_users")
def get_users():
    users = ...  # Kullanıcıları veritabanından alın veya başka bir kaynaktan çekin
    return render_template("user_list.html", users=users)


@app.route("/user_list")
def get_user_list():
    # Kullanıcıları veritabanından alın veya başka bir kaynaktan çekin
    users = [
        {"username": "user1", "email": "user1@example.com", "role": "Admin"},
        {"username": "user2", "email": "user2@example.com", "role": "Standart"},
        # Diğer kullanıcılar
    ]
    return render_template("user_list.html", users=users)
if __name__ == "__main__":
    app.run(debug=True)

