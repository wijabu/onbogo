#!usr/bin/env python3

import notify, sales
from sales import sale_url
from sales import my_sale_items

if __name__ == "__main__":
    sales.get_ad(sale_url)
    sales.find_my_sale()
    alert_msg = "\n".join(my_sale_items)
    print(alert_msg)
    notify.send_alert(alert_msg)
