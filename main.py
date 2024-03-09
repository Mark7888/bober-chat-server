from flask import Flask, render_template, request, Response
from flask_sock import Sock

from firebase_functions import do_auth, send_message, generate_local_api_key

app = Flask(__name__)
sock = Sock(app)


@app.route('/')
def index():
    print("ok")
    return render_template('index.html')


@app.route('/authenticate', methods=['POST'])
def authenticate():
    messaging_token = request.json['messagingToken']
    auth_token = request.json['authToken']

    print("got messaging token: " + messaging_token)
    print("got auth token: " + auth_token)

    user_data = do_auth(auth_token)

    send_message(messaging_token, data={"auth_ack": "true", "api_key": generate_local_api_key(auth_token, user_data['email'])})

    return Response(status=200)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8088, debug=True)
