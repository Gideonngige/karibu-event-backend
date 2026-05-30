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

# phone number normalize
def normalize_phone(phone):
    phone = phone.strip().replace(" ", "").replace("+", "")

    # If already in 254 format
    if phone.startswith("2547") and len(phone) == 12:
        return phone

    # If starts with 07...
    if phone.startswith("07") and len(phone) == 10:
        return "254" + phone[1:]

    # If starts with 7...
    if phone.startswith("7") and len(phone) == 9:
        return "254" + phone
    if phone.startswith("2541") and len(phone) == 10:
        return "254" + phone[2:]
    # if number start with 1 or 01 and has 9 digits, assume it's a local number without country code
    if (phone.startswith("1") or phone.startswith("01")) and len(phone) == 9:
        return "254" + phone.lstrip("0")

    raise ValueError("Invalid phone number format")