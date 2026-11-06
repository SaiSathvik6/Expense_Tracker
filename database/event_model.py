import calendar
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from bson import ObjectId
from database.connection import get_db


EVENTS_COLLECTION = "recurring_events"
EXECUTIONS_COLLECTION = "event_executions"


class EventModel:

    @staticmethod
    def create_event(
        title: str,
        category: str,
        amount: float,
        day_of_month: int,
        description: str = "",
        is_active: bool = True,
        event_type: str = "expense",
        frequency: str = "monthly",
    ) -> bool:
        db = get_db()
        try:
            db[EVENTS_COLLECTION].insert_one({
                "title": title.strip(),
                "category": category,
                "amount": amount,
                "day_of_month": day_of_month,
                "description": description.strip(),
                "is_active": is_active,
                "event_type": event_type,
                "frequency": frequency,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })
            return True
        except Exception as e:
            print(f"Error creating event: {e}")
            return False

    @staticmethod
    def get_all_events() -> List[Dict]:
        db = get_db()
        try:
            return list(db[EVENTS_COLLECTION].find().sort("day_of_month", 1))
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

    @staticmethod
    def get_active_events() -> List[Dict]:
        db = get_db()
        try:
            return list(db[EVENTS_COLLECTION].find({"is_active": True}).sort("day_of_month", 1))
        except Exception as e:
            print(f"Error fetching active events: {e}")
            return []

    @staticmethod
    def update_event(
        event_id: str,
        title: str,
        category: str,
        amount: float,
        day_of_month: int,
        description: str,
        is_active: bool,
        event_type: str = "expense",
        frequency: str = "monthly",
    ) -> bool:
        db = get_db()
        try:
            result = db[EVENTS_COLLECTION].update_one(
                {"_id": ObjectId(event_id)},
                {"$set": {
                    "title": title.strip(),
                    "category": category,
                    "amount": amount,
                    "day_of_month": day_of_month,
                    "description": description.strip(),
                    "is_active": is_active,
                    "event_type": event_type,
                    "frequency": frequency,
                    "updated_at": datetime.now(),
                }},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating event: {e}")
            return False

    @staticmethod
    def delete_event(event_id: str) -> bool:
        db = get_db()
        try:
            result = db[EVENTS_COLLECTION].delete_one({"_id": ObjectId(event_id)})
            db[EXECUTIONS_COLLECTION].delete_many({"event_id": event_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False

    @staticmethod
    def toggle_event(event_id: str, is_active: bool) -> bool:
        db = get_db()
        try:
            result = db[EVENTS_COLLECTION].update_one(
                {"_id": ObjectId(event_id)},
                {"$set": {"is_active": is_active, "updated_at": datetime.now()}},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error toggling event: {e}")
            return False

    @staticmethod
    def _execution_key(event_id: str, year: int, month: int) -> str:
        return f"{event_id}_{year}_{month:02d}"

    @staticmethod
    def _daily_execution_key(event_id: str, d: date) -> str:
        return f"{event_id}_{d.isoformat()}"

    @staticmethod
    def has_been_executed(event_id: str, year: int, month: int) -> bool:
        db = get_db()
        try:
            key = EventModel._execution_key(event_id, year, month)
            return db[EXECUTIONS_COLLECTION].find_one({"key": key}) is not None
        except Exception as e:
            print(f"Error checking execution: {e}")
            return False

    @staticmethod
    def has_been_executed_today(event_id: str, d: date) -> bool:
        db = get_db()
        try:
            key = EventModel._daily_execution_key(event_id, d)
            return db[EXECUTIONS_COLLECTION].find_one({"key": key}) is not None
        except Exception as e:
            print(f"Error checking daily execution: {e}")
            return False

    @staticmethod
    def mark_executed(event_id: str, year: int, month: int, expense_id=None) -> bool:
        db = get_db()
        try:
            key = EventModel._execution_key(event_id, year, month)
            db[EXECUTIONS_COLLECTION].update_one(
                {"key": key},
                {"$set": {
                    "key": key,
                    "event_id": event_id,
                    "year": year,
                    "month": month,
                    "executed_at": datetime.now(),
                    "expense_id": str(expense_id) if expense_id else None,
                }},
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"Error marking execution: {e}")
            return False

    @staticmethod
    def mark_executed_daily(event_id: str, d: date, expense_id=None) -> bool:
        db = get_db()
        try:
            key = EventModel._daily_execution_key(event_id, d)
            db[EXECUTIONS_COLLECTION].update_one(
                {"key": key},
                {"$set": {
                    "key": key,
                    "event_id": event_id,
                    "year": d.year,
                    "month": d.month,
                    "day": d.day,
                    "executed_at": datetime.now(),
                    "expense_id": str(expense_id) if expense_id else None,
                }},
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"Error marking daily execution: {e}")
            return False

    @staticmethod
    def get_execution_history(event_id: str) -> List[Dict]:
        db = get_db()
        try:
            return list(
                db[EXECUTIONS_COLLECTION].find({"event_id": event_id}).sort("executed_at", -1)
            )
        except Exception as e:
            print(f"Error fetching execution history: {e}")
            return []

    @staticmethod
    def _create_entry(event, entry_date: datetime, description: str) -> Tuple[bool, str]:
        """Post one entry for `event` to the collection matching its event_type.

        Returns (success, entry_label).
        """
        from database.models import ExpenseModel
        from database.investment_model import InvestmentModel
        from database.miscellaneous_model import MiscellaneousModel

        entry = dict(
            date=entry_date,
            category=event["category"],
            description=description,
            amount=event["amount"],
        )
        event_type = event.get("event_type", "expense")
        if event_type == "investment":
            return InvestmentModel.create_investment(**entry), "Investment"
        if event_type == "family":
            return MiscellaneousModel.create_entry(**entry), "Family entry"
        return ExpenseModel.create_expense(**entry), "Expense"

    @staticmethod
    def run_due_events(force: bool = False) -> List[Dict]:
        today = date.today()
        results = []

        for event in EventModel.get_active_events():
            frequency = event.get("frequency", "monthly")

            if frequency == "daily":
                results.append(EventModel._run_daily_event(event, today, force))
            else:
                results.append(EventModel._run_monthly_event(event, today, force))

        return results

    @staticmethod
    def _run_daily_event(event, today: date, force: bool) -> Dict:
        event_id = str(event["_id"])
        already_done = EventModel.has_been_executed_today(event_id, today)

        if already_done and not force:
            return {
                "event": event,
                "status": "skipped",
                "reason": "Already executed today",
                "due_date": today,
                "next_due": None,
            }

        entry_date = datetime(today.year, today.month, today.day)
        desc = event.get("description") or event["title"]
        success, entry_label = EventModel._create_entry(event, entry_date, f"[Auto-Daily] {desc}")

        if success:
            EventModel.mark_executed_daily(event_id, today)
            return {
                "event": event,
                "status": "executed",
                "reason": f"Daily {entry_label} created for {today.strftime('%d %b %Y')}",
                "due_date": today,
                "next_due": None,
            }
        return {
            "event": event,
            "status": "failed",
            "reason": f"Failed to create daily {entry_label.lower()} — will retry next app load",
            "due_date": today,
            "next_due": None,
        }

    @staticmethod
    def _run_monthly_event(event, today: date, force: bool) -> Dict:
        event_id = str(event["_id"])
        day = event["day_of_month"]

        last_day = calendar.monthrange(today.year, today.month)[1]
        effective_day = min(day, last_day)
        due_date = date(today.year, today.month, effective_day)

        if today.month == 12:
            next_due = date(today.year + 1, 1, min(day, 31))
        else:
            nm_last = calendar.monthrange(today.year, today.month + 1)[1]
            next_due = date(today.year, today.month + 1, min(day, nm_last))

        already_done = EventModel.has_been_executed(event_id, today.year, today.month)

        if already_done and not force:
            return {"event": event, "status": "skipped",
                    "reason": "Already executed this month",
                    "due_date": due_date, "next_due": next_due}

        if today < due_date and not force:
            return {"event": event, "status": "pending",
                    "reason": f"Due on {due_date.strftime('%d %b %Y')} (this month)",
                    "due_date": due_date, "next_due": next_due}

        if today > due_date and not already_done and not force:
            return {"event": event, "status": "next_month",
                    "reason": (
                        f"Scheduled day ({due_date.strftime('%d %b')}) already passed — "
                        f"next execution on {next_due.strftime('%d %b %Y')}"
                    ),
                    "due_date": due_date, "next_due": next_due}

        entry_date = datetime(today.year, today.month, effective_day)
        desc = event.get("description") or event["title"]
        success, entry_label = EventModel._create_entry(event, entry_date, f"[Auto] {desc}")

        if success:
            EventModel.mark_executed(event_id, today.year, today.month)
            return {"event": event, "status": "executed",
                    "reason": f"{entry_label} created for {due_date.strftime('%d %b %Y')}",
                    "due_date": due_date, "next_due": next_due}
        return {"event": event, "status": "failed",
                "reason": f"Failed to create {entry_label.lower()} — will retry next app load",
                "due_date": due_date, "next_due": next_due}

    @staticmethod
    def execute_single_event(event_id: str) -> bool:
        db = get_db()
        try:
            event = db[EVENTS_COLLECTION].find_one({"_id": ObjectId(event_id)})
            if not event:
                return False

            today = date.today()
            frequency = event.get("frequency", "monthly")
            desc = event.get("description") or event["title"]

            if frequency == "daily":
                entry_date = datetime(today.year, today.month, today.day)
                success, _ = EventModel._create_entry(event, entry_date, f"[Manual] {desc}")
                if success:
                    EventModel.mark_executed_daily(event_id, today)
                    return True
                return False

            day = event["day_of_month"]
            effective_day = min(day, calendar.monthrange(today.year, today.month)[1])
            entry_date = datetime(today.year, today.month, effective_day)
            success, _ = EventModel._create_entry(event, entry_date, f"[Manual] {desc}")

            if success:
                EventModel.mark_executed(event_id, today.year, today.month)
                return True
            return False
        except Exception as e:
            print(f"Error executing single event: {e}")
            return False
