#!/usr/bin/env python3
"""
Email configuration test script
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.development')

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_from = os.getenv('SMTP_FROM')
    admin_email = os.getenv('ADMIN_EMAIL')
    
    print(f"Testing SMTP Configuration:")
    print(f"Host: {smtp_host}")
    print(f"Port: {smtp_port}")
    print(f"User: {smtp_user}")
    print(f"From: {smtp_from}")
    print(f"Admin: {admin_email}")
    print("-" * 50)
    
    try:
        # Connect to SMTP server
        print(f"1. Connecting to {smtp_host}:{smtp_port}...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(2)  # Enable detailed debug output
        
        # Start TLS
        print("2. Starting TLS...")
        server.starttls()
        
        # Login
        print(f"3. Logging in as {smtp_user}...")
        server.login(smtp_user, smtp_password)
        print("✅ Login successful!")
        
        # Send test email
        print("4. Sending test email...")
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = admin_email
        msg['Subject'] = 'SMTP Configuration Test'
        
        body = """
        This is a test email to verify SMTP configuration.
        
        If you receive this email, your SMTP settings are working correctly!
        
        Configuration:
        - Host: {}
        - Port: {}
        - User: {}
        """.format(smtp_host, smtp_port, smtp_user)
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
        print(f"✅ Test email sent to {admin_email}")
        
        # Close connection
        server.quit()
        print("✅ Connection closed successfully")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPossible causes:")
        print("1. Wrong username or password")
        print("2. For Zoho: Use full email address as username")
        print("3. For Gmail: Use app-specific password")
        print("4. Account may require app-specific password or 2FA setup")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SMTP Email Configuration Test")
    print("=" * 50)
    
    success = test_smtp_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Email configuration is working correctly!")
    else:
        print("❌ Email configuration failed. Please check the settings above.")
    print("=" * 50)