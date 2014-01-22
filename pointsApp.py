# --------------------------
# 
# Local Loyalty APp
# Frank Caron
# frank@frankcaron.com
# Jan 2014
#
# --------------------------

#
# DEPENDENCIES
#

from flask import Flask
from flask import request
from flask import redirect
from flask import json
import os
from pylcp.api import Client

#
# GLOBAL VARS
#

# Config
property_file_path = "/Users/frankcaron/.lcp/lcp.properties"
lcp_instance = "https://sandbox.lcp.points.com/v1" 

# App
app = Flask(__name__)

# Properties file
properties = dict(line.strip().split('=') for line in open(property_file_path))

# LCP Client
client = Client(lcp_instance, properties['macKeyIdentifier'], properties['macKey'])

# 
# Helpers
# 

def gift_Frank_points():
  request_json = json.dumps({ "firstName": "Frank", "lastName:": "Caron", "memberId": "dVNm" })
  response = client.post(str('/lps/' + properties['lp_id'] + '/mvs/'), data=request_json) 
  return str(response.status_code) + " " + response.text

#
# ROUTES
# Handle the basic paths
#

@app.route('/')
def get_access():
  return "Listening for pushes."

@app.route('/lcp')
def lcp_interaction():  
  resp = gift_Frank_points()
  return resp

@app.route('/foursquare/push', methods=['POST'])
def handle_4sq_push():
    
    # Capture the request body raw
    # and grab the check in information
    checkin_info = request.form.getlist('checkin')
    checkin_json_raw = checkin_info[0]
    checkin_json = json.loads(checkin_json_raw)

    # Determine the specific user
    print checkin_json['user']['firstName']
    print checkin_json['user']['lastName']
    print checkin_json['user']['id']
    print checkin_json['user']['contact']

    # Return junk HTML just in case someone finds the URL.
    return "You shouldn't see this."

#
# MANIFEST
#

if __name__ == '__main__':
    app.debug = True
    app.run()


