# create a database SSL/TLS certificate using the following command:
# openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout database.key -out database.crt

from flask import Flask, jsonify  # Import Flask framework and jsonify for API responses
import ssl  # Import Python's SSL/TLS module to handle certificates
import psutil  # Import psutil to fetch system information like available network interfaces
import socket  # Import socket to manipulate and use network interfaces

# Create an SSL context for a secure server
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('database.crt', 'database.key')  # Load the certificate and key files

# Function to get available network interfaces and their IP addresses
def get_network_interfaces():
    interfaces = psutil.net_if_addrs()
    available_ips = []
    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                available_ips.append((interface, addr.address))
    return available_ips

# Fetch and display the available network interfaces
available_ips = get_network_interfaces()
print("Available Network Interfaces and IP addresses:")
for i, (interface, ip) in enumerate(available_ips):
    print(f"{i+1}. {interface} - {ip}")

# Prompt the user to select an IP address for the server
ip_choice = int(input("Enter the number of the IP you want to use: "))
chosen_ip = available_ips[ip_choice - 1][1]

app = Flask(__name__)  # Initialize the Flask application
stored_ips = []  # List to store the IPs

# Define the route to add an IP to the stored list
@app.route('/add/<ip>', methods=['POST'])
def add_ip(ip):
    global stored_ips
    if ip not in stored_ips:  # Check if IP is already stored
        stored_ips.append(ip)  # Add IP to the list if it isnt
    print(f"Stored IPs: {stored_ips}")  # Debug line to print stored IPs
    return jsonify({'result': 'success'}), 200  # Return success as 200

# Define the route to get the list of stored IPs
@app.route('/get_ips', methods=['GET'])
def get_ips():
    global stored_ips
    print(f"Sending IPs: {stored_ips}")  # Debug line to print sent IPs
    return jsonify({'ips': stored_ips}), 200  # Return success as 200

# Start the Flask application on the chosen IP and port 8000 with SSL context
if __name__ == '__main__':
    app.run(host=chosen_ip, port=8000, ssl_context=context)
