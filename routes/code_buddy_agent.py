from flask import Blueprint, request, jsonify
import json
import time
import requests

code_buddy_bp = Blueprint("code_buddy", __name__)

@code_buddy_bp.route("/code-buddy", methods=["POST", "OPTIONS"])
def code_buddy_handler():
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    if request.method == 'OPTIONS':
        return '', 200, headers

    if request.method != 'POST':
        return jsonify({'error': 'Method Not Allowed'}), 405, headers

    try:
        body = request.json
        prompt = body.get('prompt')
        slug = body.get('slug')

        BASE_URL = 'https://genai-code-buddy-api.stackspot.com'
        TOKEN_URL = 'https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token'
        CLIENT_ID = 'c562b3cc-4293-48c1-b71b-79ca487df3e4'
        CLIENT_SECRET = 'unzOR2sQ1aDNF4J1oYv4ZP35239F8cmE631qqOisku4x96Iy9raVS8GUPAXu2TrB'

        token_response = requests.post(
            TOKEN_URL,
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'client_credentials'
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        token = token_response.json()['access_token']

        exec_response = requests.post(
            f"{BASE_URL}/v1/quick-commands/create-execution/{slug}",
            json={
                "input_data": prompt,
                "quick_command_name": "text-generation"
            },
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        execution_id = exec_response.text.strip('"')

        while True:
            status_response = requests.get(
                f"{BASE_URL}/v1/quick-commands/callback/{execution_id}",
                headers={'Authorization': f'Bearer {token}'}
            )
            status_data = status_response.json()
            status = status_data.get('progress', {}).get('status')

            if status == 'COMPLETED':
                result = status_data['steps'][0]['step_result']['answer']
                break
            if status == 'FAILURE':
                raise Exception('Execution failed')

            time.sleep(2)

        return jsonify({'message': result}), 200, headers

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500, headers
