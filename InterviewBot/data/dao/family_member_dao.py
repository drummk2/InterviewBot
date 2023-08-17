from data.db.db_connector import get_db_connection
from data.entities.family_member import FamilyMember
from typing import List
import sqlite3


class FamilyMemberDAO:
    def __init__(self):
        self.connection = None

    def __del__(self):
        if self.connection:
            self.connection.close()

    @staticmethod
    def map_to_domain_objects(rows: List) -> List[FamilyMember]:
        family_members = []
        for row in rows:
            family_members.append(FamilyMember(*row))
        return family_members

    def delete(self, family_member_id: int) -> bool:
        if family_member_id < 0:
            return False

        try:
            self.connection = get_db_connection()
            self.connection.execute(f"DELETE FROM FamilyMember WHERE id = {family_member_id}")
            self.connection.commit()
            return True
        except sqlite3.Error as error:
            print("Failed to delete from FamilyMember table:", error)
            return False
        finally:
            if self.connection:
                self.connection.close()

    def get_all(self) -> List[FamilyMember]:
        try:
            self.connection = get_db_connection()
            results = self.connection.execute('SELECT * FROM FamilyMember').fetchall()
            return self.map_to_domain_objects(results)
        except sqlite3.Error as error:
            print("Failed to retrieve all from the FamilyMember table:", error)
        finally:
            if self.connection:
                self.connection.close()

    def get_by(self, field_name: str, field_value: str) -> List[FamilyMember]:
        try:
            self.connection = get_db_connection()
            results = self.connection.execute(f"SELECT * FROM FamilyMember WHERE {field_name} = '{field_value}'").fetchall()
            return self.map_to_domain_objects(results)
        except sqlite3.Error as error:
            print("Failed to retrieve from the FamilyMember table:", error)
        finally:
            if self.connection:
                self.connection.close()

    def get_next_for_questioning(self) -> FamilyMember:
        try:
            self.connection = get_db_connection()
            result = self.connection.execute('SELECT * FROM FamilyMember WHERE father IS NULL AND mother IS NULL ORDER BY rowid LIMIT 1').fetchone()
            return FamilyMember(*result)
        except sqlite3.Error as error:
            print("Failed to retrieve from the FamilyMember table:", error)
        finally:
            if self.connection:
                self.connection.close()

    def insert(self, family_member: FamilyMember) -> int | None:
        try:
            self.connection = get_db_connection()
            cursor = self.connection.cursor()
            cursor.execute(
                'INSERT INTO FamilyMember(forename, surname, birthyear, deathyear, birthplace, deathplace, father, mother, children, unions, familial_title, biography)'
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (family_member.forename,
                 family_member.surname,
                 family_member.birthyear,
                 family_member.deathyear,
                 family_member.birthplace,
                 family_member.deathplace,
                 family_member.father,
                 family_member.mother,
                 family_member.children,
                 family_member.unions,
                 family_member.familial_title,
                 family_member.biography))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as error:
            print("Failed to insert into FamilyMember table:", error)
        finally:
            if self.connection:
                self.connection.close()

    def update(self, family_member_id: int, field_name: str, field_value: str) -> int | None:
        # If an invalid ID has been supplied, return -1 to indicate an invalid update request.
        if family_member_id is None or family_member_id < 0:
            return -1

        # Otherwise, proceed with the update request.
        try:
            self.connection = get_db_connection()
            cursor = self.connection.cursor()
            cursor.execute(f"UPDATE FamilyMember SET {field_name} = ? WHERE id = {family_member_id}", [field_value])
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as error:
            print("Failed to update FamilyMember table:", error)
        finally:
            if self.connection:
                self.connection.close()