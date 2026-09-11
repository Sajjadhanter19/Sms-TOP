from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# --- CONFIG ---
API1_URL   = "http://147.135.212.197/crapi/st/viewstats"
API1_TOKEN = "SE5XREZBUzRfTpVnX2dQh3NQcYB2dZBWQ4JpXVxmblp2alCDi25oZg=="

API2_URL   = "http://147.135.212.197/crapi/st/viewstats"
API2_TOKEN = "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw=="

API3_URL = "https://pscall.net/restapi/smsreport"
API3_KEY = "SFNYSj1SS16DgYdyf4KIgA=="

# Country Database
country_db = {
    "1":"🇺🇸 USA/Canada", "93":"🇦🇫 Afghanistan", "92":"🇵🇰 Pakistan", "91":"🇮🇳 India",
    "20":"🇪🇬 Egypt", "44":"🇬🇧 UK", "971":"🇦🇪 UAE", "966":"🇸🇦 Saudi Arabia",
    "7":"🇷🇺 Russia", "49":"🇩🇪 Germany", "33":"🇫🇷 France", "62":"🇮🇩 Indonesia"
}

def get_country(number):
    clean = str(number).replace("+","").replace(" ","")
    for l in range(4, 0, -1):
        if clean[:l] in country_db:
            return country_db[clean[:l]]
    return "🌍 Other Countries"

def fetch_all_sms():
    all_sms = []
    
    # API 1
    try:
        r1 = requests.get(API1_URL, params={"token": API1_TOKEN}, timeout=5)
        if r1.status_code == 200 and isinstance(r1.json(), list):
            for row in r1.json():
                all_sms.append({"service": row[0] or "Unknown", "number": str(row[1] or ""), "message": row[2] or "", "date": row[3] or ""})
    except Exception as e: pass

    # API 2
    try:
        r2 = requests.get(API2_URL, params={"token": API2_TOKEN}, timeout=5)
        if r2.status_code == 200 and isinstance(r2.json(), list):
            for row in r2.json():
                all_sms.append({"service": row[0] or "Unknown", "number": str(row[1] or ""), "message": row[2] or "", "date": row[3] or ""})
    except Exception as e: pass

    # API 3
    try:
        r3 = requests.get(API3_URL, params={"key": API3_KEY, "start": 0, "length": 30}, timeout=5, verify=False)
        if r3.status_code == 200 and r3.json().get("result") == "success":
            for item in r3.json().get("data", []):
                all_sms.append({"service": item.get("cli", "Unknown"), "number": str(item.get("num", "")), "message": item.get("sms", ""), "date": item.get("dateadded", "")})
    except Exception as e: pass

    return all_sms

# Web HTML UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Live OTP Dashboard</title>
    <style>
        body { font-family: Arial; background: #0f172a; color: white; padding: 20px; text-align: center; }
        .box { background: #1e293b; padding: 20px; border-radius: 10px; max-width: 500px; margin: auto; }
        select { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; background: #0f172a; color: white; border: 1px solid #334155; }
        .card { background: #334155; padding: 15px; margin-top: 15px; border-radius: 8px; text-align: left; }
        .code { background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>📱 Live OTP Dashboard</h1>
    <div class="box">
        <label><b>Select Country:</b></label>
        <select id="countrySelect" onchange="loadNumbers()"><option value="">-- Choose Country --</option></select>

        <label><b>Select Number:</b></label>
        <select id="numberSelect" onchange="fetchOTP()"><option value="">-- Choose Number --</option></select>
    </div>

    <div id="otpContainer" style="max-width: 500px; margin: auto;"></div>

    <script>
        let allData = [];

        async function init() {
            let res = await fetch('/api/live-data');
            allData = await res.json();
            
            let countries = [...new Set(allData.map(item => item.country))];
            let cSelect = document.getElementById("countrySelect");
            cSelect.innerHTML = '<option value="">-- Choose Country --</option>';
            countries.forEach(c => { cSelect.innerHTML += `<option value="${c}">${c}</option>`; });
        }

        function loadNumbers() {
            let selectedCountry = document.getElementById("countrySelect").value;
            let filtered = allData.filter(item => item.country === selectedCountry);
            let numbers = [...new Set(filtered.map(item => item.number))];
            
            let nSelect = document.getElementById("numberSelect");
            nSelect.innerHTML = '<option value="">-- Choose Number --</option>';
            numbers.forEach(n => { nSelect.innerHTML += `<option value="${n}">${n}</option>`; });
        }

        function fetchOTP() {
            let selectedNumber = document.getElementById("numberSelect").value;
            let container = document.getElementById("otpContainer");
            container.innerHTML = "";

            let messages = allData.filter(item => item.number === selectedNumber);
            messages.forEach(m => {
                let codeMatch = m.message.match(/\\b\\d{3}[-\\s]\\d{3}\\b|\\b\\d{4,8}\\b/);
                let code = codeMatch ? codeMatch[0] : "N/A";

                container.innerHTML += `
                    <div class="card">
                        <p><b>📱 Number:</b> ${m.number}</p>
                        <p><b>🔑 OTP Code:</b> <span class="code">${code}</span></p>
                        <p><b>🛠 Service:</b> ${m.service}</p>
                        <p><b>⌚ Time:</b> ${m.date}</p>
                        <p><b>💬 Message:</b> ${m.message}</p>
                    </div>
                `;
            });
        }

        init();
        setInterval(init, 5000); // Live Auto Refresh Every 5s
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/live-data')
def live_data():
    sms_list = fetch_all_sms()
    for item in sms_list:
        item["country"] = get_country(item["number"])
    return jsonify(sms_list)

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()
    print("🚀 Server Started! Open: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

