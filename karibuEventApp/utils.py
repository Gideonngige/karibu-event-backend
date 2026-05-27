import os
import resend

# Email sending utility using Resend
resend.api_key = os.environ.get("RESEND_API_KEY")
def send_email(to_email, subject, html):
    # Debugging logs (similar to your example)
    print(f"Resend from email: {os.environ.get('RESEND_EMAIL')}")
    
    params = {
        "from": os.environ.get("RESEND_EMAIL"),
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    try:
        email = resend.Emails.send(params)
        print(f"Email sent! ID: {email['id']}")
    except Exception as e:
        print(f"Error sending email: {e}")