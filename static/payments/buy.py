import yoomoney
from yoomoney import Client, Quickpay
from dotenv import load_dotenv
import os

load_dotenv('static/.env')
CLIENT_ID = os.getenv('YOOMONEY_CLIENT_ID')
WALLET = os.getenv('YOOMONEY_WALLET')

client = Client(CLIENT_ID)

def initiate_payment(amount, user_id):
    quickpay = Quickpay(
        receiver=WALLET,
        quickpay_form="shop",
        targets="Покупка множителя",
        paymentType="PC",
        sum=amount,
        label=str(user_id)
    )
    return quickpay.redirected_url