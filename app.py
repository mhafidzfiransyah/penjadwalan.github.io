from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ---------------------------- 📁 Config Path ----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(BASE_DIR, 'memory', 'tasks.json')

# ---------------------------- 🔐 Helper & Email ----------------------------

def send_email(recipient, subject, message):
    sender = 'no-reply@penjadwalan.app'
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    smtp_host = 'sandbox.smtp.mailtrap.io'
    smtp_port = 2525
    smtp_username = 'f7df94ee8b1b32'
    smtp_password = '6c22a4446768c8'

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            print(f"📬 Email terkirim ke {recipient}")
    except Exception as e:
        print(f"❌ Gagal kirim email ke {recipient} → {e}")

def load_tasks():
    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_tasks(data):
    with open(TASKS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ---------------------------- 🔔 Reminder Checker ----------------------------

def check_reminders():
    events = load_tasks()
    now = datetime.now()
    today = now.date()

    for event in events:
        try:
            event_dt = datetime.fromisoformat(event['start'])
            event_date = event_dt.date()

            reminder_days = event.get('reminder_days', [1])

            for days_before in reminder_days:
                reminder_date = event_date - timedelta(days=days_before)
                if reminder_date == today:
                    print(f"🔔 Reminder H-{days_before}: '{event['title']}' pada {event_dt.strftime('%Y-%m-%d %H:%M')}")

                    recipient = event.get('email')
                    if recipient:
                        subject = f"Reminder H-{days_before}: {event['title']}"
                        message = (
                            f"Halo,\n\n"
                            f"Ini pengingat H-{days_before} untuk acara '{event['title']}' "
                            f"yang akan diadakan pada {event_dt.strftime('%Y-%m-%d %H:%M')}.\n"
                            f"Jangan lupa, ya!\n\n"
                            f"— Sistem Penjadwalan"
                        )
                        send_email(recipient, subject, message)
        except Exception as e:
            print(f"[!] Error parsing event: {event} → {e}")

# ---------------------------- 🌐 Routes ----------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    events = load_tasks()
    for e in events:
        if 'reminder_days' not in e:
            e['reminder_days'] = [1]
    return jsonify(events)

@app.route('/api/schedules', methods=['POST'])
def add_schedule():
    new_event = request.json

    if not new_event.get('title') or not new_event.get('start'):
        return jsonify({"error": "Judul dan tanggal wajib diisi!"}), 400

    try:
        datetime.fromisoformat(new_event['start'])  # validasi format
    except ValueError:
        return jsonify({"error": "Format tanggal dan jam salah. Gunakan YYYY-MM-DDTHH:MM"}), 400

    new_event['id'] = str(int(datetime.now().timestamp() * 1000))
    new_event['reminder_days'] = new_event.get('reminder_days') or [1]

    events = load_tasks()
    events.append(new_event)
    save_tasks(events)

    print(f"[+] Event ditambahkan: {new_event['title']} ({new_event['start']})")

    recipient = new_event.get('email')
    if recipient:
        subject = f"Undangan: {new_event['title']}"
        message = (
            f"Halo,\n\n"
            f"Anda diundang untuk mengikuti acara:\n"
            f"Judul: {new_event['title']}\n"
            f"Tanggal: {new_event['start']}\n\n"
            f"— Sistem Penjadwalan"
        )
        send_email(recipient, subject, message)

    return jsonify({"message": "Event added!"}), 201

@app.route('/api/schedules/<event_id>', methods=['PUT'])
def update_schedule(event_id):
    updated_event = request.json

    try:
        datetime.fromisoformat(updated_event['start'])  # validasi
    except ValueError:
        return jsonify({"error": "Format tanggal dan jam salah"}), 400

    # Normalize reminder_days
    reminder_raw = updated_event.get('reminder_days', [1])
    if isinstance(reminder_raw, str):
        updated_event['reminder_days'] = [int(x.strip()) for x in reminder_raw.split(',') if x.strip().isdigit()]
    elif isinstance(reminder_raw, list):
        updated_event['reminder_days'] = [int(x) for x in reminder_raw if isinstance(x, int) or str(x).isdigit()]
    else:
        updated_event['reminder_days'] = [1]

    events = load_tasks()
    for event in events:
        if event['id'] == event_id:
            event.update(updated_event)
            print(f"[~] Event diperbarui: {event['title']} ({event['start']})")
            break

    save_tasks(events)
    return jsonify({"message": "Event updated!"})

@app.route('/api/schedules/<event_id>', methods=['DELETE'])
def delete_schedule(event_id):
    events = load_tasks()
    events = [e for e in events if e['id'] != event_id]
    save_tasks(events)
    print(f"[-] Event dihapus: {event_id}")
    return jsonify({"message": "Event deleted!"})

# ---------------------------- 🚀 App Runner ----------------------------

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_reminders, trigger='interval', hours=1)
    scheduler.start()

    import atexit
    atexit.register(lambda: scheduler.shutdown())

    try:
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


app = Flask(__name__)  # pastikan app variabel ini global
