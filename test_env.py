from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get the token
token = os.getenv('TELEGRAM_BOT_TOKEN')

# Verify the token
if token:
    print("✅ .env file is loaded successfully!")
    print(f"Token found: {token[:10]}...{token[-5:]}")  # Only show part of the token for security
else:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
    print("\nPlease check that:")
    print("1. The .env file exists in the current directory")
    print("2. The file contains: TELEGRAM_BOT_TOKEN=your_token_here")
    print("3. There are no spaces around the equals sign")
    print("4. The token is not wrapped in quotes") 