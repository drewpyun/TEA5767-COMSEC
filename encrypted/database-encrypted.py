# create a database SSL/TLS certificate using the following command:
# openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout database.key -out database.crt

from flask import Flask, jsonify
import ssl
import psutil
import socket

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('database.crt', 'database.key')

def get_network_interfaces():
    interfaces = psutil.net_if_addrs()
    available_ips = []
    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                available_ips.append((interface, addr.address))
    return available_ips

# Get available IPs
available_ips = get_network_interfaces()
print("Available Network Interfaces and IP addresses:")
for i, (interface, ip) in enumerate(available_ips):
    print(f"{i+1}. {interface} - {ip}")

# User chooses the IP
ip_choice = int(input("Enter the number of the IP you want to use: "))
chosen_ip = available_ips[ip_choice - 1][1]

app = Flask(__name__)
stored_ips = []  # List to store the IPs

@app.route('/add/<ip>', methods=['POST'])
def add_ip(ip):
    global stored_ips
    if ip not in stored_ips:
        stored_ips.append(ip)
    print(f"Stored IPs: {stored_ips}")  # Debug line to print stored IPs
    return jsonify({'result': 'success'}), 200

@app.route('/get_ips', methods=['GET'])
def get_ips():
    global stored_ips
    print(f"Sending IPs: {stored_ips}")  # Debug line to print sent IPs
    return jsonify({'ips': stored_ips}), 200

if __name__ == '__main__':
    app.run(host=chosen_ip, port=8000, ssl_context=context)
