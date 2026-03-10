from pymongo import MongoClient
from datetime import datetime


class BudgetModel:

    def __init__(self, db):
        self.collection = db.budgets


    # -------------------------------------------------------
    # Create or update budget
    # -------------------------------------------------------
    def set_budget(self, user_id, category, monthly_budget, month, year):

        self.collection.update_one(
            {
                "user_id": user_id,
                "category": category,
                "month": month,
                "year": year
            },
            {
                "$set": {
                    "monthly_budget": monthly_budget
                }
            },
            upsert=True
        )


    # -------------------------------------------------------
    # Get budget for category
    # -------------------------------------------------------
    def get_budget(self, user_id, category, month, year):

        return self.collection.find_one({
            "user_id": user_id,
            "category": category,
            "month": month,
            "year": year
        })