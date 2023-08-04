#!/usr/bin/env python3

import os
import http.client
import urllib
import smtplib
import ssl
import json
import logging
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# define variables from json files
with open("onbogo/static/files/providers.json", "r") as providers:
    providers = json.load(providers)


def send_email(
    message: str,
    sender_credentials: tuple,
    receiver_email: str,
    subject: str = "BOGO Alert!",
    smtp_server="smtp.gmail.com",
    smtp_port: int = "587"
):
    sender_email, email_password = sender_credentials

    email_message = f"Subject:{subject}\nTo:{receiver_email}\n{message}"

    conn = smtplib.SMTP(smtp_server, smtp_port)
    conn.ehlo()
    conn.starttls()
    conn.login(sender_email, email_password)
    conn.sendmail(sender_email, receiver_email, email_message)
    conn.quit()


def send_sms_via_email(
    number: str,
    message: str,
    provider: str,
    sender_credentials: tuple,
    subject: str = "BOGO Alert!",
    smtp_server="smtp.gmail.com",
    smtp_port: int = "465",
):
    sender_email, email_password = sender_credentials
    receiver_email = f"{number}@{providers.get(provider).get('sms')}"

    email_message = f"Subject:{subject}\nTo:{receiver_email}\n{message}"

    with smtplib.SMTP_SSL(
        smtp_server, smtp_port, context=ssl.create_default_context()
    ) as email:
        email.login(sender_email, email_password)
        email.sendmail(sender_email, receiver_email, email_message)


def send_push(message: str, push_credentials: tuple):
    api_token, user_key = push_credentials
    push_message = message

    # create connection
    conn = http.client.HTTPSConnection("api.pushover.net:443")

    # make POST request to send message
    conn.request(
        "POST",
        "/1/messages.json",
        urllib.parse.urlencode(
            {
                "token": api_token,
                "user": user_key,
                "message": push_message,
                "title": "BOGO Alert!",
                "url": "",
                "priority": "0",
            }
        ),
        {"Content-type": "application/x-www-form-urlencoded"},
    )
    conn.getresponse()


def send_alert(alert_msg, user):
    sender_credentials = (os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD"))
    push_credentials = (os.getenv("API_TOKEN"), os.getenv("USER_KEY"))
    
    message = alert_msg
    notification = user["notification"]

    if notification == "email":
        receiver_email=user["email"]

        logging.debug("Sending EMAIL notification")
        send_email(message, sender_credentials, receiver_email)

    elif notification == "text" or "sms" or "text / sms":
        number=user["phone"]
        provider=user["provider"]

        logging.debug("Sending SMS notification")
        send_sms_via_email(number, message, provider, sender_credentials)

    elif notification == "push":
        send_push(message, push_credentials)


if __name__ == "__main__":
    send_alert()
