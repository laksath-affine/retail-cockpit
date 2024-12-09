from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # This adds the necessary CORS headers to responses

@app.route('/generate_data', methods=['POST'])
def proxy():
    # Extract the query from the incoming JSON
    data = request.get_json()
    query = data.get('query')

    # Forward the request to the external API
    api_url = 'https://chatbotquinhtml.azurewebsites.net/api/chatbotquinpbihtml'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_url, json={'query': query}, headers=headers)

    # The external API returns HTML as a string
    html_content = response.text
    # print(html_content)
    return html_content

if __name__ == '__main__':
    app.run(port=5000, debug=True)
