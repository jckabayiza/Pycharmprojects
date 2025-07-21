import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3
from datetime import datetime

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
sender_email = "zbx_monitor@bk.rw"
sender_password = "jNYCVkUPLbeztFDfHT7R"
recipients = ["jkabayiza@bk.rw"]
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


def get_color(value):
    """Return background color based on utilization percentage"""
    try:
        num = float(value)
        if num >= 90:
            return "background-color: #FFFF00;"  # Yellow
        elif num <= 20:
            return "background-color: #90EE90;"  # Green
    except (ValueError, TypeError):
        pass
    return ""


def bytes_to_gb(byte_value):
    try:
        return int(byte_value) / (1024 ** 3)
    except (ValueError, TypeError):
        return 0


def process_storage(items):
    """Calculate storage utilization percentages"""
    storage_details = []
    max_percent = 0

    for item in items:
        if "vfs.fs.size" in item["key_"]:
            if ",total" in item["key_"] or ":,total" in item["key_"]:
                total = bytes_to_gb(item["lastvalue"])
                used_key = item["key_"].replace("total", "used")
                used = next((bytes_to_gb(i["lastvalue"]) for i in items if i["key_"] == used_key), 0)

                if total > 0:
                    percent = (used / total) * 100
                    max_percent = max(max_percent, percent)

                    if ":,total" in item["key_"]:  # Windows
                        drive = item["key_"].split(":")[0]
                        storage_details.append(f"{drive}: {used:.1f}GB/{total:.1f}GB ({percent:.1f}%)")
                    else:  # Linux
                        mount = item["key_"].split(",")[0].split(".")[-1]
                        storage_details.append(f"{mount}: {used:.1f}GB/{total:.1f}GB ({percent:.1f}%)")

    return "<br>".join(storage_details), round(max_percent, 1) if max_percent > 0 else 'N/A'


def generate_html_report(data):
    """Generate report with conditional formatting"""
    html = f"""<html><body>
    <h1>Digital Channel Servers Resource Utilization Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"""

    for category, servers in data.items():
        html += f"""
        <h2>{category}</h2>
        <table border='1' style='border-collapse: collapse; width: 100%'>
            <tr>
                <th>IP</th>
                <th>Total Memory (GB)</th>
                <th>Memory Utilization (%)</th>
                <th>CPU Utilization (%)</th>
                <th>Storage Utilization (%)</th>
                <th>Storage Details</th>
            </tr>"""

        for ip, metrics in servers.items():
            html += f"""
            <tr>
                <td>{ip}</td>
                <td style='{get_color(metrics["total_memory"])}'>{metrics["total_memory"]}</td>
                <td style='{get_color(metrics["memory_utilization"])}'>{metrics["memory_utilization"]}</td>
                <td style='{get_color(metrics["cpu_utilization"])}'>{metrics["cpu_utilization"]}</td>
                <td style='{get_color(metrics["max_storage_percent"])}'>{metrics["max_storage_percent"]}</td>
                <td>{metrics["storage_details"]}</td>
            </tr>"""

        html += "</table>"

    return html + "</body></html>"


# Zabbix API functions (unchanged)
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
    return response.json().get("result")


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
    return response.json().get("result")


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


if __name__ == "__main__":
    auth_token = zabbix_login()
    report_data = {}

    for category, ips in categories.items():
        report_data[category] = {}

        for ip in ips:
            host_info = get_host_by_ip(auth_token, ip)

            if host_info:
                host_id = host_info[0]['hostid']
                items = get_resource_utilization(auth_token, host_id)

                # Process storage metrics
                storage_details, max_storage = process_storage(items)

                # Get other metrics
                total_memory = next((bytes_to_gb(item["lastvalue"]) for item in items
                                     if "total memory" in item["name"].lower()), 'N/A')

                memory_util = next((float(item["lastvalue"]) for item in items
                                    if "memory utilization" in item["name"].lower()), 'N/A')

                cpu_util = next((float(item["lastvalue"]) for item in items
                                 if "cpu utilization" in item["name"].lower()), 'N/A')

                report_data[category][ip] = {
                    "total_memory": f"{total_memory:.1f}" if isinstance(total_memory, float) else total_memory,
                    "memory_utilization": f"{memory_util:.1f}" if memory_util != 'N/A' else 'N/A',
                    "cpu_utilization": f"{cpu_util:.1f}" if cpu_util != 'N/A' else 'N/A',
                    "max_storage_percent": max_storage,
                    "storage_details": storage_details
                }
            else:
                report_data[category][ip] = {
                    "total_memory": 'N/A',
                    "memory_utilization": 'N/A',
                    "cpu_utilization": 'N/A',
                    "max_storage_percent": 'N/A',
                    "storage_details": 'N/A'
                }

    html_report = generate_html_report(report_data)
    send_email("Daily Server Resource Report", html_report)