from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import matplotlib.pyplot as plt
from io import BytesIO
from quin_insight import quin_description
app = Flask(__name__)
CORS(app)

@app.route('/')  # Root route to serve the HTML file
def serve_html():
    return send_from_directory('.', 'index.html')  # Replace 'index.html' with your actual HTML filename

@app.route('/generate_data', methods=['POST'])
def generate_data():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    _, description, _ = quin_description(query)
    print(f"Received query: {query}")
    print(f"Received query: {description}")

    try:
        generated_data = [
            {
                'description': description.split('Insights: ')[-1].split('\n')[0],
                "image_path": "/static/images/xYukB.png"  # Path to the local image
            }
        ]
    except Exception as e:
        generated_data = [
            {
                'description': 'No results found',
                "image_path": "/static/images/xYukB.png"  # Path to the local image
            }
        ]

    return jsonify(generated_data)

if __name__ == '__main__':
    app.run(debug=True)
