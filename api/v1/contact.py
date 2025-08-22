from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
from services.email_service import email_service
from core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    phone: Optional[str] = None


class ContactResponse(BaseModel):
    success: bool
    message: str


@router.post("", response_model=ContactResponse)
async def send_contact_message(
    contact_data: ContactRequest,
    background_tasks: BackgroundTasks
):
    """
    Send a contact form message
    """
    try:
        # Prepare email content
        admin_email = settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else settings.SMTP_USER
        
        subject = f"Contact Form: {contact_data.subject}"
        
        body = f"""
        New contact form submission:
        
        Name: {contact_data.name}
        Email: {contact_data.email}
        Phone: {contact_data.phone or 'Not provided'}
        Subject: {contact_data.subject}
        
        Message:
        {contact_data.message}
        
        ---
        This message was sent from the {settings.APP_NAME} contact form.
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">New Contact Form Submission</h2>
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Name:</strong> {contact_data.name}</p>
                    <p><strong>Email:</strong> <a href="mailto:{contact_data.email}">{contact_data.email}</a></p>
                    <p><strong>Phone:</strong> {contact_data.phone or 'Not provided'}</p>
                    <p><strong>Subject:</strong> {contact_data.subject}</p>
                </div>
                <div style="background-color: #ffffff; padding: 20px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                    <h3>Message:</h3>
                    <p style="white-space: pre-wrap;">{contact_data.message}</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This message was sent from the {settings.APP_NAME} contact form.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email to admin
        email_sent = email_service.send_email(
            to_email=admin_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        if not email_sent:
            logger.error(f"Failed to send contact email from {contact_data.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message. Please try again later."
            )
        
        # Send confirmation email to user (in background)
        def send_confirmation():
            confirmation_subject = f"Thank you for contacting {settings.APP_NAME}"
            confirmation_body = f"""
            Dear {contact_data.name},
            
            Thank you for contacting us. We have received your message and will get back to you as soon as possible.
            
            Your message details:
            Subject: {contact_data.subject}
            
            We typically respond within 24-48 hours during business days.
            
            Best regards,
            The {settings.APP_NAME} Team
            """
            
            confirmation_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4CAF50;">Thank You for Contacting Us!</h2>
                    <p>Dear <strong>{contact_data.name}</strong>,</p>
                    <p>We have received your message and will get back to you as soon as possible.</p>
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Your message details:</strong></p>
                        <p>Subject: {contact_data.subject}</p>
                    </div>
                    <p>We typically respond within 24-48 hours during business days.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                </div>
            </body>
            </html>
            """
            
            email_service.send_email(
                to_email=contact_data.email,
                subject=confirmation_subject,
                body=confirmation_body,
                html_body=confirmation_html
            )
        
        background_tasks.add_task(send_confirmation)
        
        logger.info(f"Contact message sent successfully from {contact_data.email}")
        
        return ContactResponse(
            success=True,
            message="Your message has been sent successfully. We'll get back to you soon!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending contact message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending your message. Please try again later."
        )


@router.get("/test-email")
async def test_email_configuration():
    """
    Test email configuration (admin only endpoint)
    """
    # This should be protected with admin authentication in production
    test_email = settings.SMTP_USER
    
    if not email_service.enabled:
        return {
            "success": False,
            "message": "Email service is not configured",
            "config": {
                "smtp_host": email_service.smtp_host or "Not set",
                "smtp_port": email_service.smtp_port or "Not set",
                "smtp_user": "Set" if email_service.smtp_user else "Not set",
                "smtp_password": "Set" if email_service.smtp_password else "Not set"
            }
        }
    
    success = email_service.send_test_email(test_email)
    
    return {
        "success": success,
        "message": f"Test email {'sent' if success else 'failed'}",
        "recipient": test_email
    }