from flask import Flask, request, jsonify, render_template
from db import events
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    data = list(events.find().sort("timestamp", -1).limit(10))
    return render_template('index.html', data=data)

@app.route('/webhook', methods=['POST'])
def webhook():
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    if event_type == "push":
        data = {
            "author": payload["pusher"]["name"],
            "action": "push",
            "to_branch": payload["ref"].split("/")[-1],
            "timestamp": datetime.utcnow()
        }
    elif event_type == "pull_request":
        action = payload["action"]
        if action == "opened":
            data = {
                "author": payload["pull_request"]["user"]["login"],
                "action": "pull_request",
                "from_branch": payload["pull_request"]["head"]["ref"],
                "to_branch": payload["pull_request"]["base"]["ref"],
                "timestamp": datetime.utcnow()
            }
        elif action == "closed" and payload["pull_request"]["merged"]:
            data = {
                "author": payload["pull_request"]["user"]["login"],
                "action": "merge",
                "from_branch": payload["pull_request"]["head"]["ref"],
                "to_branch": payload["pull_request"]["base"]["ref"],
                "timestamp": datetime.utcnow()
            }
        else:
            return jsonify({"msg": "Ignored"}), 200
    else:
        return jsonify({"msg": "Unsupported event"}), 400

    events.insert_one(data)
    return jsonify({"msg": "Event stored"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    latest = list(events.find().sort("timestamp", -1).limit(10))
    for doc in latest:
        doc["_id"] = str(doc["_id"])
        doc["timestamp"] = doc["timestamp"].strftime("%d %B %Y - %I:%M %p UTC")
    return jsonify(latest)

if __name__ == '__main__':
    app.run(port=5000)
