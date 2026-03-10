from flask_mail import Message
from flask import current_app

def send_budget_alert(email, category, spent, budget):

    mail = current_app.extensions["mail"]

    msg = Message(
        subject="⚠ Budget Alert - ExpenseEye",
        recipients=[email]
    )

    msg.body = f"""
Hello,

Your spending alert has been triggered.

Category: {category}
Spent: ₹{spent}
Budget: ₹{budget}

Please review your expenses.

- Expense Eye Budget Manager
"""

    mail.send(msg)