# Gift Card Marketplace

A full-stack Flask application for buying and selling gift cards with MongoDB database, featuring user authentication, QR code payment integration, and real-time notifications.

## Features

- **User Authentication**: Secure signup/login system with session management
- **Gift Card Management**: Upload, browse, and purchase gift cards
- **QR Code Payments**: Generate UPI QR codes for seamless payments
- **Real-time Notifications**: Telegram bot integration for instant updates
- **Responsive Design**: Modern UI with Bootstrap and custom CSS
- **MongoDB Database**: NoSQL database for flexible data storage
- **File Upload**: Image upload for gift card photos
- **Payment Verification**: Secure payment confirmation system

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **QR Code**: qrcode library
- **Image Processing**: Pillow
- **Notifications**: Telegram Bot API

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or cloud)
- Telegram Bot Token (optional, for notifications)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd giftcard-marketplace
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB**
   - Install MongoDB locally or use MongoDB Atlas
   - Create a database named `giftcard_marketplace`
   - Update the MongoDB connection string in `flask_app.py` if needed

5. **Configure environment variables** (optional)
   Create a `.env` file in the root directory:
   ```env
   FLASK_SECRET_KEY=your-secret-key-here
   MONGO_URI=mongodb://localhost:27017/giftcard_marketplace
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

6. **Run the application**
   ```bash
   python flask_app.py
   ```

7. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Project Structure

```
giftcard-marketplace/
├── flask_app.py              # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   ├── home.html           # Home page
│   ├── login.html          # Login page
│   ├── signup.html         # Signup page
│   ├── dashboard.html      # User dashboard
│   ├── upload.html         # Upload gift card
│   └── purchase.html       # Purchase gift card
├── static/                 # Static files
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   └── js/
│       └── main.js         # Main JavaScript
├── uploads/                # Uploaded images
└── static/qr/             # Generated QR codes
```

## Usage

### For Users

1. **Sign Up**: Create a new account with email and password
2. **Browse Cards**: View available gift cards on the home page
3. **Purchase Cards**: Click "Purchase Now" to buy a gift card
4. **Payment**: Scan the generated QR code with any UPI app
5. **Verification**: Click "Verify Payment" to complete the purchase

### For Sellers

1. **Login**: Sign in to your account
2. **Upload Card**: Fill out the form to upload a gift card
3. **Set Price**: Specify the price and payment details
4. **Receive Payments**: Get notified when someone purchases your card

## API Endpoints

- `GET /` - Home page with all available cards
- `GET /signup` - Signup page
- `POST /signup` - User registration
- `GET /login` - Login page
- `POST /login` - User authentication
- `GET /logout` - User logout
- `GET /dashboard` - User dashboard
- `GET /upload` - Upload gift card page
- `POST /upload` - Upload new gift card
- `GET /purchase/<card_id>` - Purchase gift card page
- `POST /api/initiate-purchase/<card_id>` - Generate QR code
- `POST /api/verify-payment/<card_id>` - Verify payment
- `POST /api/cancel-purchase/<card_id>` - Cancel purchase

## Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "password": "hashed_string",
  "created_at": "datetime"
}
```

### Gift Cards Collection
```json
{
  "_id": "ObjectId",
  "card_name": "string",
  "platform": "string",
  "expiry_date": "string",
  "price": "float",
  "owner_name": "string",
  "owner_phone": "string",
  "discount_description": "string",
  "image_url": "string",
  "owner_upi_id": "string",
  "owner_id": "ObjectId",
  "status": "string",
  "buyer_id": "ObjectId",
  "created_at": "datetime",
  "pending_since": "datetime",
  "purchased_at": "datetime"
}
```

## Configuration

### MongoDB Connection
Update the MongoDB URI in `flask_app.py`:
```python
app.config['MONGO_URI'] = 'mongodb://localhost:27017/giftcard_marketplace'
```

### Telegram Notifications
To enable Telegram notifications:
1. Create a Telegram bot using @BotFather
2. Get your bot token and chat ID
3. Update the variables in `flask_app.py`:
```python
BOT_TOKEN = "your-bot-token"
TELEGRAM_CHAT_ID = 'your-chat-id'
```

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- CSRF protection (Bootstrap forms)
- Input validation and sanitization
- Secure file upload handling
- SQL injection prevention (MongoDB)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub or contact the development team.

## Changelog

### Version 1.0.0
- Initial release
- User authentication system
- Gift card upload and purchase functionality
- QR code payment integration
- Telegram notifications
- Responsive design 