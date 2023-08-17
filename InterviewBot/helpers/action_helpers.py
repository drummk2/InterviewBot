from data.dao.slot_dao import SlotDAO
from data.entities.family_member import FamilyMember
from rasa_sdk.executor import CollectingDispatcher


def focus_on_female_ancestor(dispatcher: CollectingDispatcher, next_family_member: FamilyMember):
    dispatcher.utter_message(f"Alright, let's focus on your {next_family_member.familial_title}, {next_family_member.forename}, next.")
    dispatcher.utter_message(f"May I ask what her father's name was?")

    # Update the 'current_focus' and 'current_child_id' slots in the DB.
    slot_dao = SlotDAO()
    slot_dao.update("current_focus", "male_ancestor")
    slot_dao.update("current_child_id", next_family_member.unique_id)

def focus_on_male_ancestor(dispatcher: CollectingDispatcher, next_family_member: FamilyMember):
    dispatcher.utter_message(f"Alright, let's focus on your {next_family_member.familial_title}, {next_family_member.forename}, next.")
    dispatcher.utter_message(f"May I ask what his father's name was?")

    # Update the 'current_focus' and 'current_child_id' slots in the DB.
    slot_dao = SlotDAO()
    slot_dao.update("current_focus", "male_ancestor")
    slot_dao.update("current_child_id", next_family_member.unique_id)