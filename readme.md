## Local Loyalty

A small project for [Points](http://www.points.com)' internal "Dragon's Den"-esque competition.
Uses Foursquare's push API to award points when a user checks in at a specific venue. 

Check out the [demo video here](https://www.youtube.com/watch?v=XK2ZrzlHRrQ).

## Setup

This impl requires the following:

* An ngrok URL configured for an app on foursquare that points to your localhost/foursquare/push for push notification
* An environment variable called CONFIG that points to your configuration file.
  Take a look at sample.cfg for a good example of what you can configure
  
## Pavement

There are some convenience functions/scripts to help with the following:

* delete db
* set config

## Attributions

Libs/frameworks used follow:

    * Flask
    * PyLCP
    * SendGrid
    * Foursquare SDK

## Contributions

Welcome, appreciated, etc.. Just don't steal my idea for the competition, internal peeps! ;)
    
