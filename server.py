from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime  # Import the datetime module

app = Flask(__name__)

# Path to the CSV file
csv_file = 'sensor_data.csv'

# Ensure the CSV file has a header row if it doesn't exist
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Temperature', 'Humidity', 'Sound', 'Timestamp'])  # Add relevant headers

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    print(f"Received data: {data}")
    
    # Extract data from the JSON payload
    temperature = data.get('temperature', None)
    humidity = data.get('humidity', None)
    sound = data.get('sound', None)
    
    # Get the exact date and time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Format: YYYY-MM-DD HH:MM:SS
    
    # Save data to CSV
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([temperature, humidity, sound, current_time])
    
    return jsonify({"status": "success", "message": "Data received and saved to CSV"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
