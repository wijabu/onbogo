#!usr/bin/env python3

import schedule
import time

import notify
import sales


def main():
    sales.get_ad(sales.sale_url),
    sales.find_my_sale(),
    alert_msg = "\n".join(sales.my_sale_items)
    notify.send_alert(alert_msg)


schedule.every().thursday.at("10:00").do(main)


while True:
    schedule.run_pending()
    time.sleep(1)
