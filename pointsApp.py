from flask import Flask
from flask import request
from flask import redirect
from flask import json

# Gloabl Vars
app = Flask(__name__)


# Helpers

# Routes
# Handle the basic paths

@app.route('/')
def get_access():
  return "Listening for pushes."

@app.route('/foursquare/push', methods=['POST'])
def handle_4sq_push():
    ss=str(request.form)

    print 'ss: ' + ss + ' request.data: ' + str(request.data)
    return ss

  #grab the request body and display it
  #determine the specific user


# App manifest
if __name__ == '__main__':
    app.debug = True
    app.run()


