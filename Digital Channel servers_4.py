import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3



# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Zabbix API configuration
zabbix_url = "https://zabbix.bk.rw/zabbix/api_jsonrpc.php"
zabbix_headers = {"Content-Type": "application/json"}
zabbix_user = "jkabayiza"
zabbix_password = "P@$$W0rd_32"

# Office 365 email configuration
smtp_server = "smtp.office365.com"
smtp_port = 587
sender_email = "dcmonitor@bk.rw"
sender_password = "!23456BoK"
recipients = ["datacenter@bk.rw", "digitalchannels@bk.rw", "monitoring@bk.rw", "databaseunit@bk.rw"]

# Server categories with their IPs
categories = {
    "DCORE (USSD & BKAPP)": [
        "10.24.34.43", "10.24.34.44", "10.102.148.96", "10.102.148.98", "10.102.148.99",
        "10.102.148.100", "10.102.148.92", "10.102.148.93", "10.102.148.94", "172.16.20.81",
        "172.16.20.88", "10.102.148.118", "10.103.34.43", "10.103.34.44", "10.103.148.101",
        "10.103.148.98", "10.103.148.95", "10.103.148.97", "10.103.148.100", "10.103.148.103",
        "10.103.148.99"
    ],
    "SMS GATEWAY": [
        "10.102.149.17", "10.102.149.18", "10.102.149.236", "10.103.149.17", "10.103.149.18",
        "10.103.149.236"
    ],
    "IB 1.0 (OLD INTERNET BANKING)": [
        "10.102.149.122", "10.102.149.123", "10.102.149.128", "10.102.149.129", "10.102.149.124",
        "10.102.149.125", "10.24.34.27", "10.24.34.29", "10.24.34.60", "10.103.149.122",
        "10.103.149.123", "10.103.149.128", "10.103.149.129", "10.103.149.124", "10.103.149.125",
        "10.103.34.27", "10.103.34.29", "10.103.34.60"
    ],
    "ESB": [
        "10.24.34.88", "10.24.34.90", "10.24.34.91", "10.24.34.92", "10.24.34.93", "10.24.34.94",
        "172.16.20.99", "172.16.20.100", "172.16.20.101", "172.16.20.101", "10.102.139.26",
        "10.102.139.27", "10.102.149.206", "10.103.34.97", "10.103.34.93", "10.103.34.94",
        "10.103.34.95", "10.103.34.96", "10.103.34.98", "172.16.120.99", "172.16.120.100",
        "172.16.120.101", "172.16.120.102", "10.103.139.26", "10.103.139.27", "10.103.149.206"
    ],
    "DCORE (AGENCY BANKING)": [
        "10.24.34.66", "10.24.34.67", "10.24.34.68", "10.24.34.69", "10.24.34.81", "10.24.34.82",
        "10.24.34.83", "10.24.34.84", "10.24.34.85", "10.24.34.86", "10.103.34.66", "10.103.34.67",
        "10.103.34.68", "10.103.34.69", "10.103.34.87", "10.103.34.88", "10.103.34.89",
        "10.103.34.90", "10.103.34.91", "10.103.34.92"
    ],
    "DCORE (DIGITALHQ)": [
        "10.102.148.120", "10.102.148.124", "10.103.148.92", "10.103.148.109"
    ],
    "DCORE (INTERNET BANKING)": [
        "10.24.34.56", "10.24.34.57", "10.24.34.130", "10.24.34.131", "10.103.34.52",
        "10.103.34.130", "10.103.34.131"
    ],
    "SWIFT ALLIANCE (Windows)": [
        "10.102.138.6", "10.103.138.6"
    ],
    "SYBRIN (Windows)": [
        "10.24.38.41", "10.24.38.42", "10.24.38.94", "10.24.38.95", "10.24.38.57", "10.24.38.43",
        "10.24.38.113", "10.102.149.201", "10.24.38.83", "10.103.138.53", "10.103.138.54",
        "10.103.138.94", "10.103.138.95", "10.103.138.56", "10.103.138.55", "10.103.34.146",
        "10.103.149.201"
    ],
    "DATABASE SERVERS": [
        "10.24.38.78", "10.103.38.78"
    ]
}

# Authenticate with Zabbix API
def zabbix_login():
    login_payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": zabbix_user,
            "password": zabbix_password
        },
        "id": 1
    }
    response = requests.post(zabbix_url, json=login_payload, headers=zabbix_headers, verify=False)
    result = response.json().get("result")
    if result:
        print("Zabbix authentication successful.")
    else:
        print("Failed to authenticate with Zabbix API:", response.json())
    return result


def get_host_by_ip(auth_token, ip):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {"ip": ip},
            "output": ["hostid", "name"]
        },
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(zabbix_url, json=payload, headers=zabbix_headers, verify=False)
    return response.json().get("result")


# Get server resource utilization using host ID instead of IP
def get_resource_utilization(auth_token, host_id):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "hostids": host_id,
            "output": ["key_", "lastvalue", "name"]
        },
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(zabbix_url, json=payload, headers=zabbix_headers, verify=False)
    result = response.json().get("result")

    if result:
        print(f"Data retrieved for host ID {host_id}: {result}")
    else:
        print(f"No data found for host ID {host_id}: {response.json()}")

    return result


# Helper to convert bytes to GB
def bytes_to_gb(byte_value):
    try:
        return round(int(byte_value) / (1024 ** 3), 2)
    except (ValueError, TypeError):
        return "N/A"


# Generate HTML report
def generate_html_report(data):
    html = "<html><body>"
    html += "<h1>Digital channel Servers Resource Utilization Report</h1>"

    if not data:
        html += "<p>No data available.</p>"

    for category, ips in data.items():
        html += f"<h2>{category}</h2><table border='1'><tr><th>IP</th><th>Total Memory (GB)</th><th>Memory Utilization (%)</th><th>CPU Utilization (%)</th><th>Storage</th></tr>"

        for ip, details in ips.items():
            html += f"<tr><td>{ip}</td><td>{details['total_memory']}</td><td>{details['memory_utilization']}</td><td>{details['cpu_utilization']}</td><td>{details['storage']}</td></tr>"

        html += "</table>"

    html += "</body></html>"
    return html


# Send email
def send_email(subject, html_content):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)


# Main script execution
if __name__ == "__main__":
    auth_token = zabbix_login()

    if not auth_token:
        raise Exception("Failed to authenticate with Zabbix API")

    report_data = {}

    for category, ips in categories.items():
        report_data[category] = {}

        for ip in ips:
            host_info = get_host_by_ip(auth_token, ip)

            if host_info:
                host_id = host_info[0]['hostid']  # Get the first matching host ID
                items = get_resource_utilization(auth_token, host_id)

                # Initialize default values
                total_memory = ''
                memory_utilization_percentage = ''
                cpu_usage = ''
                storage_utilization_details = ''

                # Extract required metrics from items
                total_memory = next((bytes_to_gb(item["lastvalue"]) for item in items if
                                     "total memory" in item["name"].lower()),
                                    'N/A')

                memory_utilization_percentage = next(
                    (float(item["lastvalue"]) for item in items if
                     "memory utilization" in item["name"].lower()), 'N/A')
                if memory_utilization_percentage != 'N/A':
                    memory_utilization_percentage = f"{memory_utilization_percentage:.1f}"

                cpu_usage = next((item["lastvalue"] for item in items if
                                  ("cpu utilization" in item["name"].lower() or
                                   "system.cpu.util" in item["key_"])), 'N/A')

                # Match Storage utilization
                storage_utilization_details = ''

                for item in items:
                    # For Linux volumes
                    if "vfs.fs.size" in item["key_"] and ",total" in item["key_"]:
                        volume_name = item["key_"].split(",")[0]  # Extract volume name (e.g., /, /data)
                        total_storage = bytes_to_gb(item["lastvalue"])
                        used_storage = next((bytes_to_gb(used["lastvalue"]) for used in items if
                                             used["key_"] == item["key_"].replace("total", "used")), None)
                        if used_storage is not None:
                            storage_utilization_details += f"{volume_name}: {used_storage} GB used of {total_storage} GB<br>"

                    # For Windows volumes
                    elif "vfs.fs.size" in item["key_"] and ":,total" in item["key_"]:
                        drive_letter = item["key_"].split(":")[0]  # Extract drive letter (e.g., C, D)
                        total_storage = bytes_to_gb(item["lastvalue"])
                        used_storage = next((bytes_to_gb(used["lastvalue"]) for used in items if
                                             used["key_"] == item["key_"].replace("total", "used")), None)
                        if used_storage is not None:
                            storage_utilization_details += f"{drive_letter}: {used_storage} GB used of {total_storage} GB<br>"

                report_data[category][ip] = {
                    "total_memory": total_memory,
                    "memory_utilization": memory_utilization_percentage,
                    "cpu_utilization": cpu_usage,
                    "storage": storage_utilization_details,
                }
            else:
                print(f"No host found for IP {ip}.")
                report_data[category][ip] = {
                    "total_memory": 'N/A',
                    "memory_utilization": 'N/A',
                    "cpu_utilization": 'N/A',
                    "storage": 'N/A',
                }

    html_report = generate_html_report(report_data)

    if html_report.strip() == "<html><body><h1>Server Resource Utilization Report</h1><p>No data available.</p></body></html>":
        print("No report generated; no data was retrieved.")
    else:
        send_email("Digital Channel Servers Resource Utilization Report", html_report)