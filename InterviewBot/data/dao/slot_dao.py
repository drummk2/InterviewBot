from data.db.db_connector import get_db_connection
from data.entities.slot import Slot
import sqlite3


class SlotDAO:
    def __init__(self):
        self.connection = None

    def __del__(self):
        if self.connection:
            self.connection.close()

    def get(self, slot_name: str) -> str:
        try:
            self.connection = get_db_connection()
            result = self.connection.execute(f"SELECT * FROM Slot WHERE slot_name = '{slot_name}'").fetchone()
            return Slot(*result).slot_value
        except sqlite3.Error as error:
            print("Failed to retrieve from the Slot table:", error)
        finally:
            if self.connection:
                self.connection.close()

    def update(self, slot_name: str, slot_value: str) -> int | None:
        # If an invalid name has been supplied, return -1 to indicate an invalid update request.
        if slot_name == "":
            return -1

        # Otherwise, proceed with the update request.
        try:
            self.connection = get_db_connection()
            cursor = self.connection.cursor()
            cursor.execute(f"UPDATE Slot SET slot_value = ? WHERE slot_name = ?", [slot_value, slot_name])
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as error:
            print("Failed to update Slot table:", error)
        finally:
            if self.connection:
                self.connection.close()