from flask import Flask, jsonify  # Import Flask and jsonify from flask module
import psutil  #  Library to access system information and process utilities
import socket  # Import socket library for network interface functionalities

# Function to get available network interfaces on the server
def get_network_interfaces():
    interfaces = psutil.net_if_addrs()  # Get network interfaces
    available_ips = []  # List to store available IPs
    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # If the address is IPv4
                available_ips.append((interface, addr.address))  # Add to the list
    return available_ips

# Call the function to get available IPs and display them to the user
available_ips = get_network_interfaces()
print("Available Network Interfaces and IP addresses:")
for i, (interface, ip) in enumerate(available_ips):
    print(f"{i+1}. {interface} - {ip}")

# User selects an IP address to use for the Flask application
ip_choice = int(input("Enter the number of the IP you want to use: "))
chosen_ip = available_ips[ip_choice - 1][1]  # Get the IP address from the list

# Initialize Flask app
app = Flask(__name__)
stored_ips = []  # List to keep track of stored IP addresses

# Define route to add new IP to the list of stored IPs
@app.route('/add/<ip>', methods=['POST'])
def add_ip(ip):
    global stored_ips  # Use the global variable to manage IPs
    if ip not in stored_ips:
        stored_ips.append(ip)
    print(f"Stored IPs: {stored_ips}")  # Debug line to print IPs that are stored
    return jsonify({'result': 'success'}), 200  # Return success as JSON

# Define route to get the list of stored IPs
@app.route('/get_ips', methods=['GET'])
def get_ips():
    global stored_ips  # Use the global variable to manage IPs
    print(f"Sending IPs: {stored_ips}")  # Debug line to print IPs that are sent
    return jsonify({'ips': stored_ips}), 200  # Return list of IPs as JSON

# Start the Flask app on the chosen IP and port 8000
if __name__ == '__main__':
    app.run(host=chosen_ip, port=8000)
