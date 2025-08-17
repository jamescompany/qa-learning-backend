import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path
from jinja2 import Template
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM or settings.SMTP_USER
        self.enabled = all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password
        ])
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send an email"""
        if not self.enabled:
            logger.warning("Email service is not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = to_email
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Add text and HTML parts
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)
            
            # Prepare recipients
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg, to_addrs=recipients)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, user_email: str, username: str, verification_code: str) -> bool:
        """Send welcome email with verification code"""
        subject = f"Welcome to {settings.APP_NAME}!"
        
        body = f"""
        Hello {username},
        
        Welcome to {settings.APP_NAME}! We're excited to have you on board.
        
        To verify your email address, please use the following code:
        
        {verification_code}
        
        This code will expire in 24 hours.
        
        If you didn't create an account with us, please ignore this email.
        
        Best regards,
        The {settings.APP_NAME} Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Welcome to {settings.APP_NAME}!</h2>
                <p>Hello <strong>{username}</strong>,</p>
                <p>We're excited to have you on board.</p>
                <p>To verify your email address, please use the following code:</p>
                <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #4CAF50; margin: 0;">{verification_code}</h1>
                </div>
                <p><small>This code will expire in 24 hours.</small></p>
                <p>If you didn't create an account with us, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_password_reset_email(self, user_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        subject = f"Password Reset Request - {settings.APP_NAME}"
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        
        body = f"""
        Hello {username},
        
        We received a request to reset your password for your {settings.APP_NAME} account.
        
        To reset your password, click the link below:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        
        Best regards,
        The {settings.APP_NAME} Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Password Reset Request</h2>
                <p>Hello <strong>{username}</strong>,</p>
                <p>We received a request to reset your password for your {settings.APP_NAME} account.</p>
                <p>To reset your password, click the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
                <p><small>This link will expire in 1 hour.</small></p>
                <p>If you didn't request a password reset, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_notification_email(
        self,
        user_email: str,
        username: str,
        notification_type: str,
        notification_data: dict
    ) -> bool:
        """Send notification email"""
        subject = f"New {notification_type} - {settings.APP_NAME}"
        
        if notification_type == "comment":
            post_title = notification_data.get("post_title", "your post")
            commenter = notification_data.get("commenter", "Someone")
            
            body = f"""
            Hello {username},
            
            {commenter} commented on {post_title}.
            
            Visit {settings.APP_NAME} to view the comment.
            
            Best regards,
            The {settings.APP_NAME} Team
            """
            
        elif notification_type == "follower":
            follower = notification_data.get("follower", "Someone")
            
            body = f"""
            Hello {username},
            
            {follower} started following you on {settings.APP_NAME}.
            
            Visit their profile to learn more about them.
            
            Best regards,
            The {settings.APP_NAME} Team
            """
            
        else:
            body = f"""
            Hello {username},
            
            You have a new notification on {settings.APP_NAME}.
            
            Visit the app to learn more.
            
            Best regards,
            The {settings.APP_NAME} Team
            """
        
        return self.send_email(user_email, subject, body)
    
    def send_test_email(self, to_email: str) -> bool:
        """Send test email to verify configuration"""
        subject = f"Test Email - {settings.APP_NAME}"
        
        body = f"""
        This is a test email from {settings.APP_NAME}.
        
        If you're receiving this, your email configuration is working correctly!
        
        SMTP Configuration:
        - Host: {self.smtp_host}
        - Port: {self.smtp_port}
        - From: {self.smtp_from}
        
        Best regards,
        The {settings.APP_NAME} Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Test Email</h2>
                <p>This is a test email from <strong>{settings.APP_NAME}</strong>.</p>
                <p style="color: green;">✓ If you're receiving this, your email configuration is working correctly!</p>
                <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4>SMTP Configuration:</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li>📧 Host: {self.smtp_host}</li>
                        <li>🔌 Port: {self.smtp_port}</li>
                        <li>📤 From: {self.smtp_from}</li>
                    </ul>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)


# Global email service instance
email_service = EmailService()