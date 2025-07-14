import yoomoney
from yoomoney import Client
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv('static/.env')
CLIENT_ID = os.getenv('YOOMONEY_CLIENT_ID')

client = Client(CLIENT_ID)

def verify_payment(operation_id):
    history = client.operation_history(label=operation_id)
    for operation in history.operations:
        if operation.status == "success":
            conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'users.db'))
            c = conn.cursor()
            c.execute("UPDATE users SET multiplier = multiplier * 3 WHERE user_id = ?", (operation.label,))
            conn.commit()
            conn.close()
            return True
    return False