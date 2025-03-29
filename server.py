from flask import Flask, request, jsonify
import hashlib
import base64
import random
import socket
import requests

app = Flask(__name__)

# Allow cross-origin requests (useful if hosting separately)
from flask_cors import CORS
CORS(app)

# Compute BattleEye ID
def compute_be_id(rid):
    rid_base64 = base64.b64encode(str(rid).encode('utf-8')).decode('utf-8')
    data = "BE" + rid_base64
    md5_hash = hashlib.md5(data.encode('ascii')).hexdigest()
    return md5_hash

# Check the ban reason via UDP
def check_ban_reason(rid):
    server_ip = "51.89.97.102"
    server_port = 61455
    be_id = compute_be_id(rid)

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.connect((server_ip, server_port))

    outgoing_data = bytearray(random.getrandbits(8) for _ in range(4))
    outgoing_data.extend(be_id.encode('utf-8'))

    client.send(outgoing_data)
    received_data, _ = client.recvfrom(1024)

    return received_data[4:].decode('ascii')

# Convert name to RID using API
def name_to_rid(name):
    try:
        response = requests.get(f"https://sc-cache.com/n/{name}")
        if response.status_code == 200 and response.text.startswith('{"id":'):
            rid = response.text.split('"id":')[1].split(',')[0]
            return rid
    except requests.exceptions.RequestException:
        return None

# API Endpoint to check ban status
@app.route('/check_ban', methods=['GET'])
def check_ban():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "No username provided"}), 400

    rid = name_to_rid(username)
    if not rid:
        return jsonify({"error": "User not found"}), 404

    ban_reason = check_ban_reason(rid)
    return jsonify({"username": username, "ban_reason": ban_reason})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
