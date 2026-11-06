from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bson import ObjectId
import config
from database.connection import get_db
from utils.helpers import get_month_start_end


class MiscellaneousModel:

    @staticmethod
    def create_entry(date: datetime, category: str, description: str, amount: float) -> bool:
        db = get_db()
        try:
            db[config.MISCELLANEOUS_COLLECTION].insert_one({
                "date": date,
                "category": category,
                "description": description,
                "amount": amount,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })
            return True
        except Exception as e:
            print(f"Error creating miscellaneous entry: {e}")
            return False

    @staticmethod
    def get_entries(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        db = get_db()
        query = {}
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = start_date
            if end_date:
                query["date"]["$lte"] = end_date
        if category:
            query["category"] = category
        return list(db[config.MISCELLANEOUS_COLLECTION].find(query).sort("date", -1))

    @staticmethod
    def get_monthly_total(year: int, month: int) -> float:
        start_date, end_date = get_month_start_end(year, month)
        return sum(e["amount"] for e in MiscellaneousModel.get_entries(start_date, end_date))

    @staticmethod
    def get_yearly_monthly_totals(year: int) -> Dict[int, float]:
        return {month: MiscellaneousModel.get_monthly_total(year, month) for month in range(1, 13)}

    @staticmethod
    def get_available_years() -> List[int]:
        db = get_db()
        try:
            entries = db[config.MISCELLANEOUS_COLLECTION].find({}, {"date": 1})
            years = {e["date"].year for e in entries if e.get("date")}
            return sorted(years, reverse=True) if years else [datetime.now().year]
        except Exception as e:
            print(f"Error getting available years: {e}")
            return [datetime.now().year]

    @staticmethod
    def update_entry(entry_id: str, date: datetime, category: str, description: str, amount: float) -> bool:
        db = get_db()
        try:
            result = db[config.MISCELLANEOUS_COLLECTION].update_one(
                {"_id": ObjectId(entry_id)},
                {"$set": {
                    "date": date,
                    "category": category,
                    "description": description,
                    "amount": amount,
                    "updated_at": datetime.now(),
                }},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating miscellaneous entry: {e}")
            return False

    @staticmethod
    def delete_entry(entry_id: str) -> bool:
        db = get_db()
        try:
            result = db[config.MISCELLANEOUS_COLLECTION].delete_one({"_id": ObjectId(entry_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting miscellaneous entry: {e}")
            return False

    @staticmethod
    def migrate_from_expenses(query: Dict) -> Tuple[int, int]:
        """Move every expense matching `query` into the miscellaneous collection.

        Documents keep their original _id and timestamps, so the move is lossless.
        Returns (migrated, failed).
        """
        db = get_db()
        migrated, failed = 0, 0
        for exp in list(db[config.EXPENSES_COLLECTION].find(query)):
            try:
                db[config.MISCELLANEOUS_COLLECTION].replace_one({"_id": exp["_id"]}, exp, upsert=True)
                db[config.EXPENSES_COLLECTION].delete_one({"_id": exp["_id"]})
                migrated += 1
            except Exception as e:
                print(f"Error migrating expense {exp['_id']}: {e}")
                failed += 1
        return migrated, failed
