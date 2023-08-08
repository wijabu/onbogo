# BOGO Sales Alerts
Scrapes weekly ads for sales and sends user notifications.

This web app allows users to create profiles, find and save their nearest grocery store, save keywords / favorite groceries, and choose a preferred method of notification (email or text / sms). 

Users can also log into the app to update their favorites and manually trigger notifications at any time. 

##### Disclaimer

> This project is a work in progress. Version 1.0 was a POC for the Python program functionality. 
> Version 2.0 is an evolution from a simple Python script to a complete Flask application.

## DEPENDENCIES:

1. APScheduler (https://pypi.org/project/beautifulsoup4/) for running background process for cron-like capabilities
2. Beautiful Soup (https://pypi.org/project/beautifulsoup4/) for html parsing
3. Flask (https://pypi.org/project/flask/) for application framework
4. pymongo (https://pypi.org/project/pymongo/) for interacting with MongoDB


## FUTURE PLANS: 
1. Validating the automated notifications functionality
2. Adding other sales / specials in addition to BOGO items
3. Add saved sale items to a Shopping List with photos and links
4. Convert the Flask application into a Progressive Web Application (PWA)
