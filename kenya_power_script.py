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

# Load environment variables from .env file
load_dotenv()

# Twitter API credentials (Bearer Token for API v2)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Gmail credentials
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Gmail password stored in environment variable

# Estate name to check in tweets (case-insensitive)
ESTATE_NAME = os.getenv("ESTATE_NAME")

# Initialize Tesseract path - modify based on your OS
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:  # Linux/MacOS
    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# Function to send email alert
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = GMAIL_USER
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to analyze tweet content and images for estate name
def analyze_tweet(content, images):
    if ESTATE_NAME.lower() in content.lower():
        return True

    for image_url in images:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            img = Image.open(response.raw)
            text = pytesseract.image_to_string(img)
            if ESTATE_NAME.lower() in text.lower():
                return True
    return False

# Main function to monitor Twitter using search_recent_tweets
def monitor_twitter():
    # Initialize the Tweepy Client for API v2
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

    try:        
        # Search for recent tweets from Kenya Power's official account
        query = f"from:KenyaPower_Care {ESTATE_NAME} -is:retweet -is:reply"
        response = client.search_recent_tweets(
            query=query,
            max_results=10,  # Fetch up to 10 recent tweets
            tweet_fields=["text", "attachments"],  # Get tweet text and attachments
            expansions="attachments.media_keys",  # Expand media information
            media_fields=["url"]  # Get media URLs
        )

        if response.data is None:
            print("No tweets found")
            return

        tweets = response.data
        media_map = {media.media_key: media.url for media in response.includes.get("media", [])}
        
        for tweet in tweets:
            content = tweet.text
            media_keys = tweet.attachments.get("media_keys", []) if tweet.attachments else []
            images = [media_map[key] for key in media_keys]

            if analyze_tweet(content, images):
                send_email(
                    subject="Power Maintenance Alert",
                    body=f"Kenya Power posted about maintenance in {ESTATE_NAME}:\n\n{content}\n\nTweet Link: https://x.com/{tweet.id}"
                )
    except tweepy.TooManyRequests:
        print("Rate limit reached. Waiting 15 minutes before trying again...")
        time.sleep(15 * 60)  # Wait 15 minutes
    except tweepy.TwitterServerError:
        print("Twitter server error. Waiting 1 minute before trying again...")
        time.sleep(60)  # Wait 1 minute
    except Exception as e:
        print(f"Error fetching tweets: {e}")

def is_within_time_window():
    # Get current time in EAT (UTC+3)
    current_time = time.gmtime(time.time() + 3 * 3600)  # UTC+3 for EAT
    current_hour = current_time.tm_hour
    
    # Check if current time is between 19:00 (7PM) and 21:00 (9PM)
    return 19 <= current_hour < 21

if __name__ == "__main__":
    while True:
        if is_within_time_window():
            print("Running Twitter monitor...")
            monitor_twitter()
            # Sleep for 15 minutes before checking again
            time.sleep(15 * 60)
        else:
            # Check again in 5 minutes
            print("Outside monitoring window. Waiting...")
            time.sleep(5 * 60)
