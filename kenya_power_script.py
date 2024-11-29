import tweepy
import os
import smtplib
import pytesseract
from PIL import Image
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Modified environment variable loading
if os.getenv('RAILWAY_ENVIRONMENT'):
    # On Railway, environment variables are set directly
    logging.info("Running on Railway - using Railway environment variables")
else:
    # Local development - load from .env file
    logging.info("Running locally - loading from .env file")
    load_dotenv()

# Add validation for required environment variables
required_vars = ['GMAIL_USER', 'GMAIL_PASSWORD', 'SUBSCRIBED_EMAILS', 'ESTATE_NAMES', 'TWITTER_BEARER_TOKEN']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logging.error(error_msg)
    raise ValueError(error_msg)

# After load_dotenv()
logging.info(f"Raw GMAIL_USER: '{os.getenv('GMAIL_USER')}'")
logging.info(f"Raw GMAIL_PASSWORD: '{os.getenv('GMAIL_PASSWORD')}'")
logging.info(f"Raw SUBSCRIBED_EMAILS: '{os.getenv('SUBSCRIBED_EMAILS')}'")
logging.info(f"Raw ESTATE_NAMES: '{os.getenv('ESTATE_NAMES')}'")

# Twitter API credentials (Bearer Token for API v2)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Gmail credentials
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Gmail password stored in environment variable

# Safer environment variable handling with defaults
SUBSCRIBED_EMAILS = [email.strip() for email in os.getenv("SUBSCRIBED_EMAILS", "").split(',') if email.strip()]
ESTATE_NAMES = [name.strip() for name in os.getenv("ESTATE_NAMES", "").split(',') if name.strip()]

# Add validation with better debugging
if not SUBSCRIBED_EMAILS:
    logging.error(f"No subscribed emails found. Raw value: '{os.getenv('SUBSCRIBED_EMAILS')}'")
    SUBSCRIBED_EMAILS = []

if not ESTATE_NAMES:
    logging.error(f"No estate names found. Raw value: '{os.getenv('ESTATE_NAMES')}'")
    ESTATE_NAMES = []

# Initialize Tesseract path - modify for Railway deployment
if os.getenv('RAILWAY_ENVIRONMENT'):
    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
elif os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:  # Linux/MacOS
    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# Function to send email alert
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = ",".join(SUBSCRIBED_EMAILS)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
            logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

# Function to analyze tweet content and images for estate name
def analyze_tweet(content, images):
    matched_estates = set()  # Use a set to prevent duplicates
    
    # Check if any estate name is in the tweet content
    for estate in ESTATE_NAMES:
        if estate.strip().lower() in content.lower():
            matched_estates.add(estate.strip())

    # Check images
    for image_url in images:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            img = Image.open(response.raw)
            text = pytesseract.image_to_string(img)
            # Check if any estate name is in the OCR text
            for estate in ESTATE_NAMES:
                if estate.strip().lower() in text.lower():
                    matched_estates.add(estate.strip())
                    
    return bool(matched_estates), list(matched_estates)  # Convert set back to list before returning

# Main function to monitor Twitter using search_recent_tweets
def monitor_twitter():
    # Initialize the Tweepy Client for API v2
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

    try:      
        # Search for recent tweets from Kenya Power's official account  
        # Create a query with OR conditions for each estate name
        estate_conditions = " OR ".join(f'"{name.strip()}"' for name in ESTATE_NAMES)
        query = f'from:KenyaPower_Care ({estate_conditions}) -is:retweet -is:reply'
        
        response = client.search_recent_tweets(
            query=query,
            max_results=10,  # Fetch up to 10 recent tweets
            tweet_fields=["text", "attachments"],  # Get tweet text and attachments
            expansions="attachments.media_keys",  # Expand media information
            media_fields=["url"]  # Get media URLs
        )

        if response.data is None:
            logging.info("No tweets found")
            return

        tweets = response.data
        media_map = {media.media_key: media.url for media in response.includes.get("media", [])}
        
        for tweet in tweets:
            content = tweet.text
            media_keys = tweet.attachments.get("media_keys", []) if tweet.attachments else []
            images = [media_map[key] for key in media_keys]

            has_matches, matched_estates = analyze_tweet(content, images)
            if has_matches:
                estates_string = ", ".join(matched_estates)
                send_email(
                    subject="Power Maintenance Alert",
                    body=f"Kenya Power posted about maintenance in {estates_string}:\n\n{content}\n\nTweet Link: https://x.com/{tweet.id}"
                )
    except tweepy.TooManyRequests:
        logging.info("Rate limit reached. Waiting 15 minutes before trying again...")
        time.sleep(15 * 60)  # Wait 15 minutes
    except tweepy.TwitterServerError:
        logging.info("Twitter server error. Waiting 1 minute before trying again...")
        time.sleep(60)  # Wait 1 minute
    except Exception as e:
        logging.error(f"Error fetching tweets: {e}")

def is_within_time_window():
    # Get current time in EAT (UTC+3)
    current_time = time.gmtime(time.time() + 3 * 3600)  # UTC+3 for EAT
    current_hour = current_time.tm_hour
    
    # Check if current time is between 19:00 (7PM) and 21:00 (9PM)
    return 19 <= current_hour < 21

if __name__ == "__main__":
    while True:
        if is_within_time_window():
            logging.info("Running Twitter monitor...")
            monitor_twitter()
            # Sleep for 15 minutes before checking again
            time.sleep(15 * 60)
        else:
            # Check again in 5 minutes
            logging.info("Outside monitoring window. Waiting...")
            time.sleep(5 * 60)
