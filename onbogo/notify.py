#!/usr/bin/env python3

import smtplib, ssl, json

# from providers import PROVIDERS

with open("providers.json", "r") as providers:
    providers = json.load(providers)


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
    with open(
        "../config.json", "r"
    ) as config:  # defines sender credentials for SMS / EMAIL / PUSH notifications
        config = json.load(config)

    with open(
        "../profile.json", "r"
    ) as profile:  # will be replaced in the future with user-created profiles
        profile = json.load(profile)

    number = profile.get("recipient_phone")
    message = alert_msg
    provider = "AT&T"

    sender_credentials = (config.get("email"), config.get("password"))
    send_sms_via_email(number, message, provider, sender_credentials)


if __name__ == "__main__":
    send_alert()
