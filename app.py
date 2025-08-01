from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory, send_file
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import os
import requests
import qrcode
import uuid
from io import BytesIO
from datetime import datetime
import json


BOT_TOKEN = "7394867216:AAGZ_UMGP3QIx19gSvMnlP_nljiU1ZH800U"
TELEGRAM_CHAT_ID = '1850275200'

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  

app.config['MONGO_URI'] = 'mongodb://localhost:27017/giftcard_marketplace'
mongo = PyMongo(app)


app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['QR_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'qr')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16 MB


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)


@app.route('/')
def home():
   
    cards = list(mongo.db.gift_cards.find({'status': 'available'}))
   
    for card in cards:
        card['_id'] = str(card['_id'])
        if 'owner_id' in card:
            card['owner_id'] = str(card['owner_id'])
    return render_template('home.html', cards=cards)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirmPassword', '')
        
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))
        
       
        if mongo.db.users.find_one({'email': email}):
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        
        
        user = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(user)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = mongo.db.users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        flash('Please login to access dashboard!', 'error')
        return redirect(url_for('login'))
    
    user_cards = list(mongo.db.gift_cards.find({'owner_id': session['user_id']}))
    
    purchased_cards = list(mongo.db.gift_cards.find({'buyer_id': session['user_id']}))
    
    for card in user_cards + purchased_cards:
        card['_id'] = str(card['_id'])
        if 'owner_id' in card:
            card['owner_id'] = str(card['owner_id'])
        if 'buyer_id' in card:
            card['buyer_id'] = str(card['buyer_id'])
    
    return render_template('dashboard.html', user_cards=user_cards, purchased_cards=purchased_cards)

@app.route('/upload', methods=['GET', 'POST'])
def upload_card():
    """Upload a new gift card"""
    if 'user_id' not in session:
        flash('Please login to upload cards!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            source = request.form['source']
            description = request.form.get('description', '')
            expiry_date = request.form['expiry_date']
            price = float(request.form.get('price', 0))
            owner_name = request.form['owner_name']
            phone = request.form['phone']
            upi_id = request.form.get('upi_id')
            image = request.files['image']

            if image:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
            else:
                flash('Image upload failed!', 'error')
                return redirect(url_for('upload_card'))

            new_card = {
                'card_name': name,
                'platform': source,
                'expiry_date': expiry_date,
                'price': price,
                'owner_name': owner_name,
                'owner_phone': phone,
                'discount_description': description,
                'image_url': filename,
                'owner_upi_id': upi_id,
                'owner_id': session['user_id'],
                'status': 'available',
                'created_at': datetime.utcnow()
            }
            
            mongo.db.gift_cards.insert_one(new_card)

            message = (
                f"🎁 New Gift Card Uploaded!\n"
                f"Card: {name} ({source})\n"
                f"Price: ₹{price}\n"
                f"Expires: {expiry_date}\n"
                f"Owner: {owner_name} ({phone})\n"
                f"UPI ID: {upi_id}\n"
                f"Note: {description}"
            )
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
            )

            flash('Card uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error uploading card: {str(e)}', 'error')
            return redirect(url_for('upload_card'))
    
    return render_template('upload.html')

@app.route('/review-order/<card_id>')
def review_order(card_id):
    """Review order before proceeding to payment"""
    if 'user_id' not in session:
        flash('Please login to review orders!', 'error')
        return redirect(url_for('login'))
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    
    if not card:
        flash('Card not found!', 'error')
        return redirect(url_for('home'))
    
    if card['status'] != 'available':
        flash('Card is not available for purchase!', 'error')
        return redirect(url_for('home'))
    
    if card['owner_id'] == session['user_id']:
        flash('You cannot buy your own card!', 'error')
        return redirect(url_for('home'))
    
    card['_id'] = str(card['_id'])
    card['owner_id'] = str(card['owner_id'])
    
    order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    order_date = datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')
    
    return render_template('review_order.html', card=card, order_id=order_id, order_date=order_date)

@app.route('/purchase/<card_id>')
def purchase_card(card_id):
    """Purchase a gift card"""
    if 'user_id' not in session:
        flash('Please login to purchase cards!', 'error')
        return redirect(url_for('login'))
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    
    if not card:
        flash('Card not found!', 'error')
        return redirect(url_for('home'))
    
    if card['status'] != 'available':
        flash('Card is not available for purchase!', 'error')
        return redirect(url_for('home'))
    
    if card['owner_id'] == session['user_id']:
        flash('You cannot buy your own card!', 'error')
        return redirect(url_for('home'))
    
    card['_id'] = str(card['_id'])
    card['owner_id'] = str(card['owner_id'])
    
    return render_template('purchase.html', card=card)

@app.route('/api/initiate-purchase/<card_id>', methods=['POST'])
def initiate_purchase(card_id):
    """Initiate purchase and generate QR code"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    
    if card['status'] != 'available':
        return jsonify({'error': 'Card is not available'}), 400
    
    mongo.db.gift_cards.update_one(
        {'_id': ObjectId(card_id)},
        {
            '$set': {
                'status': 'pending',
                'buyer_id': session['user_id'],
                'pending_since': datetime.utcnow()
            }
        }
    )
    
    try:
        upi_id = card['owner_upi_id']
        amount = card['price']
        payee_name = card['owner_name'].replace(" ", "")
        
        print(f"QR Generation Debug - UPI ID: {upi_id}, Amount: {amount}, Payee: {payee_name}")
        
        if not upi_id or not upi_id.strip():
            print("QR Generation Error: Missing UPI ID")
            return jsonify({'error': 'UPI ID is required for payment'}), 400
        
        if not amount or amount <= 0:
            print("QR Generation Error: Invalid amount")
            return jsonify({'error': 'Invalid amount for payment'}), 400
        
        upi_url = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount}&cu=INR"
        print(f"QR Generation Debug - UPI URL: {upi_url}")
        
        img = qrcode.make(upi_url)
        filename = f"{uuid.uuid4().hex}.png"
        qr_path = os.path.join(app.config['QR_FOLDER'], filename)
        
        print(f"QR Generation Debug - QR Path: {qr_path}")
        
        os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
        
        img.save(qr_path)
        
        if os.path.exists(qr_path):
            file_size = os.path.getsize(qr_path)
            print(f"QR Generation Debug - File created successfully, size: {file_size} bytes")
        else:
            print("QR Generation Error: File was not created")
            return jsonify({'error': 'Failed to save QR code file'}), 500
        
        qr_url = f"/static/qr/{filename}"
        print(f"QR Generation Debug - QR URL: {qr_url}")
        
        return jsonify({'qr_code_url': qr_url})
        
    except Exception as e:
        print(f"QR Generation Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate QR code: {str(e)}'}), 500

@app.route('/api/verify-payment/<card_id>', methods=['POST'])
def verify_payment(card_id):
    """Verify payment and complete purchase"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    
    if card['status'] == 'purchased':
        return jsonify({'error': 'Card already purchased'}), 400
    
     
    mongo.db.gift_cards.update_one(
        {'_id': ObjectId(card_id)},
        {
            '$set': {
                'status': 'purchased',
                'buyer_id': session['user_id'],
                'purchased_at': datetime.utcnow()
            }
        }
    )
    
    buyer = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    buyer_name = buyer['username'] if buyer else 'Unknown Buyer'
    
    message = (
        f"✅ Gift Card Purchased!\n"
        f"Card: {card['card_name']} ({card['platform']})\n"
        f"Price: ₹{card['price']}\n"
        f"Owner: {card['owner_name']} ({card['owner_phone']})\n"
        f"Buyer: {buyer_name}\n"
        f"Transaction completed successfully!"
    )
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
    )
    
    return jsonify({'message': 'Purchase completed successfully!'})

@app.route('/api/cancel-purchase/<card_id>', methods=['POST'])
def cancel_purchase(card_id):
    """Cancel pending purchase"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    
    if card['buyer_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    mongo.db.gift_cards.update_one(
        {'_id': ObjectId(card_id)},
        {
            '$set': {
                'status': 'available',
                'buyer_id': None,
                'pending_since': None
            }
        }
    )
    
    return jsonify({'message': 'Purchase cancelled successfully!'})

@app.route('/edit-card/<card_id>', methods=['GET', 'POST'])
def edit_card(card_id):
    """Edit a gift card"""
    if 'user_id' not in session:
        flash('Please login to edit cards!', 'error')
        return redirect(url_for('login'))
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    if not card:
        flash('Card not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if str(card['owner_id']) != session['user_id']:
        flash('You can only edit your own cards!', 'error')
        return redirect(url_for('dashboard'))
    
    if card['status'] == 'purchased':
        flash('Cannot edit a purchased card!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            source = request.form['source']
            description = request.form.get('description', '')
            expiry_date = request.form['expiry_date']
            price = float(request.form.get('price', 0))
            owner_name = request.form['owner_name']
            phone = request.form['phone']
            upi_id = request.form.get('upi_id')
            image = request.files.get('image')

            update_data = {
                'card_name': name,
                'platform': source,
                'expiry_date': expiry_date,
                'price': price,
                'owner_name': owner_name,
                'owner_phone': phone,
                'discount_description': description,
                'owner_upi_id': upi_id,
                'updated_at': datetime.utcnow()
            }

            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                update_data['image_url'] = filename

            mongo.db.gift_cards.update_one(
                {'_id': ObjectId(card_id)},
                {'$set': update_data}
            )

            flash('Card updated successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error updating card: {str(e)}', 'error')
            return redirect(url_for('edit_card', card_id=card_id))
    
    card['_id'] = str(card['_id'])
    return render_template('edit_card.html', card=card)

@app.route('/delete-card/<card_id>', methods=['POST'])
def delete_card(card_id):
    """Delete a gift card"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to delete cards!'}), 401
    
    card = mongo.db.gift_cards.find_one({'_id': ObjectId(card_id)})
    if not card:
        return jsonify({'error': 'Card not found!'}), 404
    
    
    if str(card['owner_id']) != session['user_id']:
        return jsonify({'error': 'You can only delete your own cards!'}), 403
    
   
    if card['status'] == 'purchased':
        return jsonify({'error': 'Cannot delete a purchased card!'}), 400
    
    try:
        
        mongo.db.gift_cards.delete_one({'_id': ObjectId(card_id)})
        return jsonify({'message': 'Card deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': f'Error deleting card: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/qr/<filename>')
def qr_file(filename):
    """Serve QR code images"""
    print(f"QR File Request - Filename: {filename}")
    print(f"QR File Request - Folder: {app.config['QR_FOLDER']}")
    
    
    file_path = os.path.join(app.config['QR_FOLDER'], filename)
    if os.path.exists(file_path):
        print(f"QR File Request - File exists, size: {os.path.getsize(file_path)} bytes")
    else:
        print(f"QR File Request - File does not exist: {file_path}")
    
    return send_from_directory(app.config['QR_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 