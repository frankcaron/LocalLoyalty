## Local Loyalty

A small project for [Points](http://www.points.com)' internal "Dragon's Den"-esque competition. Uses Foursquare's push API to award points when a user checks in at a specific venue.

## Setup

This impl requires the following:

* An ngrok URL configured for an app on foursquare that points to your localhost/foursquare/push for push notification
* A properties file located at `/Users/.../.lcp` named `lcp.properties` with the following format:

    macAlgorithm=YOURVALHERE
    macKey=YOURVALHERE
    macKeyIdentifier=YOURVALHERE
    lp_id=YOURVALHERE

## Attributions

Libs/frameworks used follow:

    * Flask
    * PyLCP

## Contributions

Welcome, appreciated, etc.. Just don't steal my idea for the competition, internal peeps! ;)

    