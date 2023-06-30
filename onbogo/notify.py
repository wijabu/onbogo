#!/usr/bin/env python3

import smtplib
import ssl
import json
import logging

logging.basicConfig(
    # filename='myLogFile.txt', # use this to write logs to specified file
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# define variables from json files
with open("providers.json", "r") as providers:
    providers = json.load(providers)

with open(
    "../config.json", "r"
) as config:  # defines sender credentials for SMS / EMAIL / PUSH notifications
    config = json.load(config)

with open(
    "../profile.json", "r"
) as profile:  # will be replaced in the future with user-created profiles
    profile = json.load(profile)
    alert_pref = profile.get("alert_pref")


def send_email(
    message: str,
    sender_credentials: tuple,
    subject: str = "BOGO Alert!",
    smtp_server="smtp.gmail.com",
    smtp_port: int = "587",
):
    sender_email, email_password = sender_credentials
    receiver_email = profile.get("recipient_email")

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


def send_alert(alert_msg):
    sender_credentials = (config.get("email"), config.get("password"))
    message = alert_msg

    if alert_pref == "email":
        logging.debug("Sending EMAIL notification")
        send_email(message, sender_credentials)

    elif alert_pref == "text":
        number = profile.get("recipient_phone")
        provider = profile.get("phone_provider")

        logging.debug("Sending SMS notification")

        send_sms_via_email(number, message, provider, sender_credentials)


if __name__ == "__main__":
    send_alert()
