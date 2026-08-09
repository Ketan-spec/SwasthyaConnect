import sqlite3
import os
from typing import List, Dict, Tuple

# Helper to get DB path (same as in src/database.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))
DB_NAME = os.path.join(PROJECT_ROOT, "data", "swasthya_v1.db")

class AvailabilityService:
    """Service for managing doctor availability slots."""

    @staticmethod
    def get_free_slots(doctor_id: int, date: str) -> List[Dict]:
        """Return a list of free slots for a doctor on a given date.
        Args:
            doctor_id: ID of the doctor (from users table).
            date: ISO date string YYYY-MM-DD.
        Returns:
            List of dicts with keys: id, time_slot.
        """
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, time_slot FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND is_booked = 0
            ORDER BY time_slot
            """,
            (doctor_id, date),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def book_slot(doctor_id: int, date: str, time_slot: str) -> Tuple[bool, str]:
        """Mark a slot as booked.
        Returns (True, "") on success or (False, error_msg).
        """
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cur = conn.cursor()
        try:
            # Ensure slot exists and is free
            cur.execute(
                "SELECT id, is_booked FROM doctor_availability WHERE doctor_id = ? AND date = ? AND time_slot = ?",
                (doctor_id, date, time_slot),
            )
            row = cur.fetchone()
            if not row:
                return False, "Slot not found"
            if row[1] != 0:
                return False, "Slot already booked"
            # Book it
            cur.execute(
                "UPDATE doctor_availability SET is_booked = 1 WHERE id = ?",
                (row[0],),
            )
            conn.commit()
            return True, ""
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def release_slot(slot_id: int) -> Tuple[bool, str]:
        """Release a previously booked slot (set is_booked back to 0)."""
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE doctor_availability SET is_booked = 0 WHERE id = ?",
                (slot_id,),
            )
            conn.commit()
            return True, ""
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
