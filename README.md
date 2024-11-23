# Kenya Power Maintenance Alert System

This project monitors Kenya Power's official Twitter account (@KenyaPower_Care) for tweets about power maintenance in specific estates and sends email notifications to subscribed users when relevant tweets are found.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/kenya-power-alerts.git
```

### 2. Create and Activate Virtual Environment

#### On Windows:
```bash
python -m venv kenya-power-project
kenya-power-project\Scripts\activate
```

#### On MacOS/Linux:
```bash
python3 -m venv kenya-power-project
source kenya-power-project/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

#### Install Tesseract
#### On MacOS:
```bash
brew install tesseract
```

#### On Windows:
```bash
choco install tesseract
```
Or  
1. Go to https://github.com/UB-Mannheim/tesseract/wiki and download the installer for your version of Windows.
2. Run the installer (make sure to note the installation path)

#### On Linux:
```bash
sudo apt-get install tesseract-ocr
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root directory with the following structure:
```
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
GMAIL_USER=your_gmail_address
GMAIL_PASSWORD=your_gmail_app_password
SUBSCRIBED_EMAILS=['email1@example.com', 'email2@example.com']
ESTATE_NAMES=['Estate1', 'Estate2', 'Estate3']
```


### 5. Get Gmail App Password

1. Go to your Google Account settings (https://myaccount.google.com/)
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled
4. Under "Signing in to Google," select App passwords
5. Select "Mail" and your device
6. Click "Generate"
7. Copy the 16-character password

### 6. Get Twitter Bearer Token

1. Go to the Twitter Developer Portal (https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app (if you haven't already)
3. Navigate to your app's settings
4. Under "Keys and tokens," find your Bearer Token
   - If you need to create a new one, click "Generate"
5. Copy the Bearer Token

### 7. Configure the Project

1. Update your `.env` file with:
   - The Twitter Bearer Token
   - Your Gmail address
   - The Gmail App Password you generated
   - List of email addresses to receive notifications
   - List of estate names to monitor

Example `.env` file:
```
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAxxxxxxxxxxxxxxxxxxxxx
GMAIL_USER=your.email@gmail.com
GMAIL_PASSWORD=your16charapppassword
SUBSCRIBED_EMAILS=['email1@gmail.com', 'email2@gmail.com']
ESTATE_NAMES=['Kileleshwa', 'Kilimani', 'Westlands']
```

### 8. Run the Project

With your virtual environment activated, run the script:
```bash
python kenya_power_script.py
```


The script will:
- Run between 7 PM and 9 PM EAT
- Check Kenya Power's tweets every 15 minutes
- Send email notifications when relevant maintenance announcements are found

## Notes

- The script uses Tesseract OCR to extract text from images. Make sure Tesseract is installed on your system:
  - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
  - Linux: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

- The script will only monitor tweets during the specified time window (7 PM - 9 PM EAT)
- Outside the monitoring window, it checks every 5 minutes if it should start monitoring

## Contributing

Feel free to fork this repository and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.