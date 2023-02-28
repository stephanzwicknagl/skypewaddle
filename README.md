# Skype Waddle

[![Skype Waddle](/assets/icon-192x192.png)](https://skypewaddle.herokuapp.com/)

A dash based web app for reviewing skype habits. It uses the personal data, available from your skype account, to generate visualizations of your skype conversations.

This app is currently hosted at [https://skypewaddle.herokuapp.com/](https://skypewaddle.herokuapp.com/)

## Features

- Upload your own skype data to generate personalized visualizations or use sample data to get a feel for the app
- Select the conversation partner
- The app currently features the following visualizations:
  - total duration of calls
  - total number of calls
  - a yearly view of the durations of your calls
  - which weekdays you skyped the most
  - and more...
- Results change dynamically depending on your timezone
- An info page describing how to use the app and the story of how it came about

Tools used:

- dash for the web app
- bootstrap for styling
- fast json parsing with orjson
- xml parsing with lxml
- managing callbacks in the background with celery
- generating plots with plotly
- pandas, numpy, and other python data science tools

## Preview

![Preview](/docs/img/landing.png)
![Duration plot](/docs/img/duration.png)
![Calendar plot](/docs/img/calendar.png)
![Info modal](/docs/img/info.png)
