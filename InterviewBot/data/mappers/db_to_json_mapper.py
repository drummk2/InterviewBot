from typing import List

from data.dao.family_member_dao import FamilyMemberDAO
from data.entities.family_member import FamilyMember
import json


class DBToJSONMapper:
    union_count = 0

    def __init__(self):
        self.family_member_dao = FamilyMemberDAO()

    @staticmethod
    def add_person(family_member: FamilyMember, data: dict) -> None:
        person_obj = {
            "id": str(family_member.unique_id),
            "name": f"{family_member.forename} {family_member.surname}".strip(),
        }

        if family_member.birthyear:
            person_obj["birthyear"] = int(family_member.birthyear)

        if family_member.deathyear:
            person_obj["deathyear"] = int(family_member.deathyear)

        if family_member.birthplace:
            person_obj["birthplace"] = family_member.birthplace

        if family_member.deathplace:
            person_obj["deathplace"] = family_member.deathplace

        data["persons"][str(family_member.unique_id)] = person_obj

    @staticmethod
    def backwards_link_exists(unique_id: str, data: dict) -> bool:
        for link in data["links"]:
            if ("u" in link[0]) and (link[1] == unique_id):
                return True
        return False

    @staticmethod
    def create_empty_union_and_link(data: dict) -> None:
        # Create an empty union for the single member of the family.
        family_member_id = data['start']
        data["unions"][f"u{family_member_id}"] = {
            "id": f"u{family_member_id}",
            "partner": [],
            "children": []
        }

        # Create an empty link for the single member of the family.
        data["links"].append([family_member_id, f"u{family_member_id}"])

    @staticmethod
    def initialise_json_representation(family_members: List[FamilyMember]) -> dict:
        return {
            "start": str(family_members[0].unique_id),
            "persons": {},
            "unions": {},
            "links": []
        }

    @staticmethod
    def link_exists(unique_id: str, data: dict) -> bool:
        for link in data["links"]:
            if unique_id in link:
                return True
        return False

    @staticmethod
    def get_parent_union(father: int, mother: int, data: dict) -> int | None:
        for union in data["unions"].values():
            if str(father) in union["partner"] and str(mother) in union["partner"]:
                return union["id"]
        return None

    @staticmethod
    def get_union(family_member: FamilyMember, data: dict) -> int:
        for union in data["unions"].values():
            if str(family_member.unique_id) in union["partner"]:
                return union["id"]
        return None

    def create_unions_and_links(self, family_member: FamilyMember, family_members: List[FamilyMember], data: dict) -> None:
        # Initialise any unions based on known marriages.
        if family_member.unions:
            for union in family_member.unions.split(","):
                # If a union does not already exist for this family member, create a new one.
                union_id = self.get_union(family_member, data)
                new_union_id = ""

                if union_id is None:
                    new_union_id = f"u{self.union_count}"
                    data["unions"][f"{new_union_id}"] = {
                        "id": f"{new_union_id}",
                        "partner": [str(family_member.unique_id), union],
                        "children": family_member.children.split(",")
                    }
                    self.union_count += 1

                # Set the 'own union' for this family member.
                if data["persons"][str(family_member.unique_id)].get("own_unions"):
                    data["persons"][str(family_member.unique_id)]["own_unions"].append(
                        union_id if union_id else f"{new_union_id}")
                else:
                    data["persons"][str(family_member.unique_id)]["own_unions"] = [
                        union_id if union_id else f"{new_union_id}"]

                # Create a union for this family member.
                data["links"].append([str(family_member.unique_id), union_id if union_id else f"{new_union_id}"])

        # For each child, append a "parent_union" subkey to their respective entries.
        if family_member.children:
            for child in family_member.children.split(","):
                if data["persons"].get(child):
                    # Find the union containing both the child's mother and father, and set this to be the child's 'parent union'.
                    father = next((x.father for x in family_members if x.unique_id == int(child)), None)
                    mother = next((x.mother for x in family_members if x.unique_id == int(child)), None)
                    parent_union_id = self.get_parent_union(father if father else "-1", mother if mother else "-1", data)

                    # If a parent union does not already exist, then create a placeholder union.
                    if parent_union_id is None:
                        data["unions"][f"u{self.union_count}"] = {
                            "id": f"u{self.union_count}",
                            "partner": [str(family_member.unique_id), "-1"],
                            "children": family_member.children.split(",")
                        }
                        parent_union_id = f"u{self.union_count}"
                        self.union_count += 1

                    data["persons"][child]["parent_union"] = parent_union_id

                    # Create an empty union as well, to ensure that the tree can be displayed.
                    if not self.get_union(family_member, data):
                        data["links"].append([str(family_member.unique_id), f"u{self.union_count}"])

                    # Has a backwards link already been created for this child? If not, create one.
                    if not self.backwards_link_exists(child, data):
                        data["links"].append([parent_union_id, str(child)])

    def get_current_tree_representation(self) -> str:
        # Retrieve the full list of family members from our local DB.
        family_members = self.family_member_dao.get_all()

        # Determine whether or not our list is empty.
        if family_members:
            # Due to the way in which family_tree.js functions, special actions must be taken for the case in which there
            # is only a single person in the family. If there is more than one family member proceed as normal.
            # Construct an initial representation of the family tree that we will be displaying. Otherwise, an empty
            # link and union must be created to ensure that the single person is displayed.
            data = self.initialise_json_representation(family_members)

            # Flesh out the family tree with each family member's details.
            for family_member in family_members:
                self.add_person(family_member, data)
                self.create_unions_and_links(family_member, family_members, data)

            if len(family_members) == 1:
                self.create_empty_union_and_link(data)

            return f"{json.dumps(data)}"
        else:
            return "{}"
