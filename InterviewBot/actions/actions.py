from constants import family_member_fields
from data.dao.family_member_dao import FamilyMemberDAO
from data.dao.slot_dao import SlotDAO
from data.entities.family_member import FamilyMember
from helpers.action_helpers import focus_on_female_ancestor, focus_on_male_ancestor
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import numpy as np
import random


class ActionBiographyForm(Action):
    @staticmethod
    def process_female_ancestors_biography(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the biography that was supplied in the user's most recent input.
        biography = tracker.latest_message['text']

        if biography:
            # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the mother's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the mother record with the newly learned biography.
            if len(results) > 0:
                mother_id = results[0].mother
                family_member_dao.update(mother_id, family_member_fields.BIOGRAPHY, biography)

                # Retrieve the details of the next ancestor that the bot should ask about.
                next_family_member = family_member_dao.get_next_for_questioning()
                if "father" in next_family_member.familial_title:
                    focus_on_male_ancestor(dispatcher, next_family_member)
                elif "mother" in next_family_member.familial_title:
                    focus_on_female_ancestor(dispatcher, next_family_member)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_male_ancestors_biography(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the biography that was supplied in the user's most recent input.
        biography = tracker.latest_message['text']

        if biography:
            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the father's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)
            title = None

            # Update the father record with the newly learned biography.
            if len(results) > 0:
                father_id = results[0].father
                family_member_dao.update(father_id, family_member_fields.BIOGRAPHY, biography)

                # Retrieve the father's overall title to be used to construct a follow-up question.
                father_results = family_member_dao.get_by(family_member_fields.ID, father_id)
                if len(father_results) > 0:
                    title = father_results[0].familial_title

                dispatcher.utter_message(f"Nice! I'll make a note of that.")
                dispatcher.utter_message(f"I think that's all that I need on your {title} for the moment. How about we talk about your {title.replace('father', 'mother')}? What was her name?")

                # Given that the next intent received should relate to a female ancestor, the most recent current_focus
                # is prematurely set to "She" in the event that the user uses "It's".
                # Update the 'current_focus' slot in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("current_focus", "female_ancestor")
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    def name(self) -> Text:
        return "action_biography_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_focus = slot_dao.get("current_focus")

        if current_focus.casefold() == "male_ancestor".casefold():
            return self.process_male_ancestors_biography(dispatcher, tracker)
        elif current_focus.casefold() == "female_ancestor".casefold():
            return self.process_female_ancestors_biography(dispatcher, tracker)


class ActionProcessConfirmationOfDeath(Action):
    @staticmethod
    def process_female_ancestors_confirmation_of_death(dispatcher: CollectingDispatcher):
        dispatcher.utter_message("I see. If you don't mind my asking, in what year did she die?")
        return [SlotSet("discussing_death", True)]

    @staticmethod
    def process_male_ancestors_confirmation_of_death(dispatcher: CollectingDispatcher):
        dispatcher.utter_message("I see. If you don't mind my asking, in what year did he die?")
        return [SlotSet("discussing_death", True)]

    def name(self) -> Text:
        return "action_process_confirmation_of_death"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_focus = slot_dao.get("current_focus")

        if current_focus.casefold() == "male_ancestor".casefold():
            return self.process_male_ancestors_confirmation_of_death(dispatcher)
        elif current_focus.casefold() == "female_ancestor".casefold():
            return self.process_female_ancestors_confirmation_of_death(dispatcher)


class ActionProcessConfirmationOfLife(Action):
    @staticmethod
    def process_female_ancestors_confirmation_of_life(dispatcher: CollectingDispatcher):
        # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
        slot_dao = SlotDAO()
        child_id = int(slot_dao.get("current_child_id"))

        # Get the mother's ID.
        family_member_dao = FamilyMemberDAO()
        results = family_member_dao.get_by(family_member_fields.ID, child_id)

        # Retrieve the mother's overall title to be used to construct a follow-up question.
        title = None
        if len(results) > 0:
            mother_results = family_member_dao.get_by(family_member_fields.ID, results[0].mother)
            if len(mother_results) > 0:
                title = mother_results[0].familial_title

        # Reply to the user.
        dispatcher.utter_message("That's wonderful to hear!")
        dispatcher.utter_message(f"If you could describe your {title} in 1 sentence, what would you say?\nPlease start your sentence with: 'A brief description:'.")

        return [SlotSet("discussing_death", False)]

    @staticmethod
    def process_male_ancestors_confirmation_of_life(dispatcher: CollectingDispatcher):
        # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
        slot_dao = SlotDAO()
        child_id = int(slot_dao.get("current_child_id"))

        # Get the father's ID.
        family_member_dao = FamilyMemberDAO()
        results = family_member_dao.get_by(family_member_fields.ID, child_id)

        # Retrieve the father's overall title to be used to construct a follow-up question.
        title = None
        if len(results) > 0:
            father_results = family_member_dao.get_by(family_member_fields.ID, results[0].father)
            if len(father_results) > 0:
                title = father_results[0].familial_title

        # Reply to the user.
        dispatcher.utter_message("That's wonderful to hear!")
        dispatcher.utter_message(f"If you could describe your {title} in a few lines, what would you say?\nPlease start your sentence with: 'A brief description:'.")

        return [SlotSet("discussing_death", False)]

    def name(self) -> Text:
        return "action_process_confirmation_of_life"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_focus = slot_dao.get("current_focus")

        if current_focus.casefold() == "male_ancestor".casefold():
            return self.process_male_ancestors_confirmation_of_life(dispatcher)
        elif current_focus.casefold() == "female_ancestor".casefold():
            return self.process_female_ancestors_confirmation_of_life(dispatcher)


class ActionProcessCorrectInformation(Action):
    def name(self) -> Text:
        return "action_process_correct_information"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        next_focus = slot_dao.get("next_focus")
        next_question = slot_dao.get("next_question")

        if next_focus:
            slot_dao.update("current_focus", next_focus)

        if next_question:
            dispatcher.utter_message(next_question)


class ActionProcessIncorrectInformation(Action):
    def name(self) -> Text:
        return "action_process_incorrect_information"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_question = slot_dao.get("current_question")
        last_id_updated = slot_dao.get("last_id_updated")
        if last_id_updated:
            last_id_updated = int(last_id_updated)

        last_fields_updated = slot_dao.get("last_fields_updated")
        last_fields_updated_list = []
        if last_fields_updated:
            last_fields_updated_list = last_fields_updated.split(",")

        if last_id_updated and len(last_fields_updated_list) > 0:
            family_member_dao = FamilyMemberDAO()

            # Iterate through the fields that were last updated and set them to "".
            for field_name in last_fields_updated_list:
                family_member_dao.update(last_id_updated, field_name, "")

            # Repeat the current question.
            dispatcher.utter_message("No problem.")
            dispatcher.utter_message(current_question)


class ActionProcessNameGiven(Action):
    @staticmethod
    def process_female_ancestors_name(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the name that was supplied in the user's most recent input.
        person = next(tracker.get_latest_entity_values("PERSON"), None)

        if person:
            mother_id = -1

            # Extract the mother's forename and surname.
            if np.char.count(person, " ") > 0:
                names = person.split(" ")
                forename = names[0]
                surname = names[1]
            else:
                forename = person
                surname = ""

            # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Retrieve the child's record in the DB.
            family_member_dao = FamilyMemberDAO()
            child_records = family_member_dao.get_by(family_member_fields.ID, child_id)
            child = None
            if len(child_records) > 0:
                child = child_records[0]

            # If a mother already exists for this child, then update that record as they have probably
            # just tried to correct the name, otherwise, create a new record to represent the mother,
            # update the child record, and link the new mother record to the child's father, if it exists.
            if child is not None:
                if child.mother:
                    family_member_dao.update(child.mother, "forename", forename.capitalize())
                    family_member_dao.update(child.mother, "surname", surname.capitalize())
                else:
                    # Create a new record to represent the mother.
                    mother = FamilyMember(None, forename.capitalize(), surname.capitalize(), None, None, None, None, None, None, child_id, None, None, None)
                    mother_id = family_member_dao.insert(mother)

                    # Update the mother record with a familial title, based on the child's familial title.
                    match child.familial_title:
                        # If the child is the user, then this female ancestor is their mother.
                        case "user":
                            family_member_dao.update(mother_id, family_member_fields.FAMILIAL_TITLE, "mother")
                        # If the child is the user's father, then this is their grandmother.
                        case "father":
                            family_member_dao.update(mother_id, family_member_fields.FAMILIAL_TITLE, "grandmother")
                        # If the child is the user's mother, then this is their grandmother.
                        case "mother":
                            family_member_dao.update(mother_id, family_member_fields.FAMILIAL_TITLE, "grandmother")
                        # If the child is the user's grandfather, then this is their great-grandmother.
                        case "grandfather":
                            family_member_dao.update(mother_id, family_member_fields.FAMILIAL_TITLE, "great-grandmother")
                        # If the child is the user's grandmother, then this is their great-grandmother.
                        case "grandmother":
                            family_member_dao.update(mother_id, family_member_fields.FAMILIAL_TITLE, "great-grandmother")
                        # Otherwise, append a "great" to the beginning of the child's title to add a generation.
                        case _:
                            family_member_dao.update(mother_id, family_member_fields.FAMILIAL_TITLE, f"great-{child.familial_title.replace('father', 'mother')}")

                    # Update the child record to reflect the newly identified mother.
                    family_member_dao.update(child_id, family_member_fields.MOTHER, mother_id)

                    # Determine whether or not a father already exists in the DB for this child. If so, link this mother to that father.
                    if child.father is not None:
                        # Retrieve the record for the father.
                        father_records = family_member_dao.get_by(family_member_fields.ID, child.father)
                        if len(father_records) > 0:
                            # Add a link to the father record.
                            father = father_records[0]
                            father.add_union(mother_id)
                            family_member_dao.update(father.unique_id, family_member_fields.UNIONS, father.unions)

                            # Add a link to the mother record.
                            mother.add_union(father.unique_id)
                            family_member_dao.update(mother_id, family_member_fields.UNIONS, mother.unions)

            # Reply to the user.
            if surname != "":
                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.FORENAME},{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", mother_id)
                slot_dao.update("current_question", "Would you mind if I ask what her name is?")
                slot_dao.update("next_focus", "female_ancestor")
                slot_dao.update("next_question", "So, where was she born, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"I've noted her name as being {forename} {surname}. Is that correct?", buttons = buttons)
            else:
                # Update the 'surname_required' slot in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("surname_required", "true")

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", mother_id)
                slot_dao.update("current_question", "Would you mind if I ask what her name is?")
                slot_dao.update("next_focus", "female_ancestor")
                slot_dao.update("next_question", "And what is her surname, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"Alright, I've written down her first name as {forename}. Is that right?", buttons = buttons)

    @staticmethod
    def process_female_ancestors_surname(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the surname that was supplied in the user's most recent input.
        surname = next(tracker.get_latest_entity_values("PERSON"), None)

        if surname:
            mother_id = -1

            # If the ancestor's full name is provided, just take the surname.
            if np.char.count(surname, " ") > 0:
                names = surname.split(" ")
                surname = names[1]

            # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the mother's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the mother record with the newly learned surname.
            if len(results) > 0:
                mother_id = results[0].mother
                family_member_dao.update(mother_id, family_member_fields.SURNAME, surname.capitalize())

            # Reply to the user.
            if surname != "":
                # Update the 'surname_required' slot in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("surname_required", "false")

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", mother_id)
                slot_dao.update("current_question", "Would you mind if I ask what her surname is?")
                slot_dao.update("next_focus", "female_ancestor")
                slot_dao.update("next_question", "So, where was she born, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"Great, so I've noted down her surname as {surname}. Am I correct?", buttons = buttons)
            else:
                dispatcher.utter_message(f"I'm sorry, but I didn't catch that.")

    @staticmethod
    def process_male_ancestors_name(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the name that was supplied in the user's most recent input.
        person = next(tracker.get_latest_entity_values("PERSON"), None)

        if person:
            father_id = -1

            # Extract the father's forename and surname.
            if np.char.count(person, " ") > 0:
                names = person.split(" ")
                forename = names[0]
                surname = names[1]
            else:
                forename = person
                surname = ""

            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Retrieve the child's record in the DB.
            family_member_dao = FamilyMemberDAO()
            child_records = family_member_dao.get_by(family_member_fields.ID, child_id)
            child = None
            if len(child_records) > 0:
                child = child_records[0]

            # If a father already exists for this child, then update that record as they have probably
            # just tried to correct the name, otherwise, create a new record to represent the father,
            # update the child record, and link the new father record to the child's mother, if it exists.
            if child is not None:
                if child.father:
                    father_id = child.father
                    family_member_dao.update(father_id, "forename", forename.capitalize())
                    family_member_dao.update(father_id, "surname", surname.capitalize())
                else:
                    # Initialise the new record and insert it into the DB.
                    father = FamilyMember(None, forename.capitalize(), surname.capitalize(), None, None, None, None, None, None, child_id, "-1", None, None)
                    father_id = family_member_dao.insert(father)

                    # Update the father record with a familial title, based on the child's familial title.
                    match child.familial_title:
                        # If the child is the user, then this male ancestor is their father.
                        case "user":
                            family_member_dao.update(father_id, family_member_fields.FAMILIAL_TITLE, "father")
                        # If the child is the user's father, then this is their grandfather.
                        case "father":
                            family_member_dao.update(father_id, family_member_fields.FAMILIAL_TITLE, "grandfather")
                        # If the child is the user's mother, then this is their grandfather.
                        case "mother":
                            family_member_dao.update(father_id, family_member_fields.FAMILIAL_TITLE, "grandfather")
                        # If the child is the user's grandfather, then this is their great-grandfather.
                        case "grandfather":
                            family_member_dao.update(father_id, family_member_fields.FAMILIAL_TITLE, "great-grandfather")
                        # If the child is the user's grandmother, then this is their great-grandfather.
                        case "grandmother":
                            family_member_dao.update(father_id, family_member_fields.FAMILIAL_TITLE, "great-grandfather")
                        # Otherwise, append a "great" to the beginning of the child's title to add a generation.
                        case _:
                            family_member_dao.update(father_id, family_member_fields.FAMILIAL_TITLE, f"great-{child.familial_title.replace('mother', 'father')}")

                    # Update the child record to reflect the newly identified father.
                    family_member_dao.update(child_id, family_member_fields.FATHER, father_id)

                    # Determine whether or not a mother already exists in the DB for this child. If so, link this father to that mother.
                    if child.mother is not None:
                        # Retrieve the record for the mother.
                        mother_records = family_member_dao.get_by(family_member_fields.ID, child.mother)
                        if len(mother_records) > 0:
                            # Add a link to the mother record.
                            mother = mother_records[0]
                            mother.add_union(father_id)
                            family_member_dao.update(mother.unique_id, family_member_fields.UNIONS, mother.unions)

                            # Add a link to the father record.
                            father.add_union(mother.unique_id)
                            family_member_dao.update(father_id, family_member_fields.UNIONS, father.unions)

            # Reply to the user.
            if surname != "":
                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.FORENAME},{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", father_id)
                slot_dao.update("current_question", "Would you mind if I ask what his name is?")
                slot_dao.update("next_focus", "male_ancestor")
                slot_dao.update("next_question", "So, where was he born, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"I've written down {forename} {surname} as his name. Is that correct?", buttons = buttons)
            else:
                # Update the 'surname_required' slot in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("surname_required", "true")

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", father_id)
                slot_dao.update("current_question", "Would you mind if I ask what his name is?")
                slot_dao.update("next_focus", "male_ancestor")
                slot_dao.update("next_question", "And what is his surname, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"So, his first name is {forename}, yes?", buttons = buttons)

    @staticmethod
    def process_male_ancestors_surname(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the surname that was supplied in the user's most recent input.
        surname = next(tracker.get_latest_entity_values("PERSON"), None)

        if surname:
            father_id = -1

            # If the ancestor's full name is provided, just take the surname.
            if np.char.count(surname, " ") > 0:
                names = surname.split(" ")
                surname = names[1]

            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the father's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the father record with the newly learned surname.
            if len(results) > 0:
                father_id = results[0].father
                family_member_dao.update(father_id, family_member_fields.SURNAME, surname.capitalize())

            # Reply to the user.
            if surname != "":
                # Update the 'surname_required' slot in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("surname_required", "false")

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", father_id)
                slot_dao.update("current_question", "Would you mind if I ask what his surname is?")
                slot_dao.update("next_focus", "male_ancestor")
                slot_dao.update("next_question", "So, where was he born, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"Ah, so his surname is {surname}, right?", buttons = buttons)
            else:
                dispatcher.utter_message(f"I'm sorry, but I didn't catch that.")

    @staticmethod
    def process_users_name(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the name that was supplied in the user's most recent input.
        person = next(tracker.get_latest_entity_values("PERSON"), None)

        if person:
            # Give the user the option of rolling back the previous update.
            buttons = [
                {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
            ]

            # Extract the user's forename and surname.
            if np.char.count(person, " ") > 0:
                names = person.split(" ")
                if len(names) == 3:
                    forename = f"{names[0]} {names[1]}"
                    surname = names[2]
                else:
                    forename = names[0]
                    surname = names[1]

                # Update the first row in the DB, as this is a placeholder that will become the main user (required by family_tree.js).
                family_member_dao = FamilyMemberDAO()
                family_member_dao.update(1, family_member_fields.FORENAME, forename.capitalize())
                family_member_dao.update(1, family_member_fields.SURNAME, surname.capitalize())

                # Update the 'forename', 'surname', and 'current_child_id' slots in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("forename", forename.capitalize())
                slot_dao.update("surname", surname.capitalize())
                slot_dao.update("current_child_id", 1)

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.FORENAME},{family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", 1)
                slot_dao.update("current_question", "Would you mind if I ask your name?")
                slot_dao.update("next_question", f"If you don't mind me asking, where are you originally from, {forename}?")

                dispatcher.utter_message(f"Nice to meet you! I've written down {forename} {surname} as your name. Is that right?", buttons = buttons)
            else:
                forename = person.capitalize()

                # Update the first row in the DB, as this is a placeholder that will become the main user (required by family_tree.js).
                FamilyMemberDAO().update(1, family_member_fields.FORENAME, forename)

                # Update the 'forename', 'surname_required', and 'current_child_id' slots in the DB.
                slot_dao = SlotDAO()
                slot_dao.update("forename", forename)
                slot_dao.update("surname_required", "true")
                slot_dao.update("current_child_id", 1)

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.FORENAME}, {family_member_fields.SURNAME}")
                slot_dao.update("last_id_updated", 1)
                slot_dao.update("current_question", "Would you mind if I ask your name?")
                slot_dao.update("next_question", "Sorry, but I didn't catch your surname. Would you mind if I ask what it is?")

                dispatcher.utter_message(f"The first name that you've given is {forename}, correct?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch your name.")

    @staticmethod
    def process_users_surname(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the surname that was supplied in the user's most recent input.
        surname = next(tracker.get_latest_entity_values("PERSON"), None)

        if surname:
            # If the ancestor's full name is provided, just take the surname.
            if np.char.count(surname, " ") > 0:
                names = surname.split(" ")
                surname = names[1]

            # Update the first row in the DB, as this is a placeholder that will become the main user (required by family_tree.js).
            FamilyMemberDAO().update(1, family_member_fields.SURNAME, surname.capitalize())

            # Update the 'surname', and 'surname_required' slots in the DB.
            slot_dao = SlotDAO()
            slot_dao.update("surname", surname.capitalize())
            slot_dao.update("surname_required", "false")

            # Update the fields required to roll back the previous update.
            slot_dao.update("last_fields_updated", f"{family_member_fields.SURNAME}")
            slot_dao.update("last_id_updated", 1)
            slot_dao.update("current_question", "Would you mind if I ask your surname?")
            slot_dao.update("next_question", "If you don't mind me asking, where are you originally from?")

            # Give the user the option of rolling back the previous update.
            buttons = [
                {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
            ]

            dispatcher.utter_message(f"The surname that you've given is {surname}, am  I right in saying that?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    def name(self) -> Text:
        return "action_process_name_given"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_focus = slot_dao.get("current_focus")
        surname_required = slot_dao.get("surname_required") == "true"

        if not surname_required:
            if current_focus.casefold() == "user".casefold():
                self.process_users_name(dispatcher, tracker)
            elif current_focus.casefold() == "male_ancestor".casefold():
                self.process_male_ancestors_name(dispatcher, tracker)
            elif current_focus.casefold() == "female_ancestor".casefold():
                self.process_female_ancestors_name(dispatcher, tracker)
        else:
            if current_focus.casefold() == "user".casefold():
                self.process_users_surname(dispatcher, tracker)
            elif current_focus.casefold() == "male_ancestor".casefold():
                self.process_male_ancestors_surname(dispatcher, tracker)
            elif current_focus.casefold() == "female_ancestor".casefold():
                self.process_female_ancestors_surname(dispatcher, tracker)


class ActionProcessPlaceGiven(Action):
    @staticmethod
    def process_female_ancestors_birthplace(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the birthplace that was supplied in the user's most recent input.
        birthplace = next(tracker.get_latest_entity_values("GPE"), None)

        if birthplace:
            # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the mother's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the mother record with the newly learned birthplace.
            if len(results) > 0:
                mother_id = results[0].mother
                family_member_dao.update(mother_id, family_member_fields.BIRTHPLACE, birthplace.capitalize())

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.BIRTHYEAR}")
                slot_dao.update("last_id_updated", mother_id)
                slot_dao.update("current_question", "So, where was she born, may I ask?")
                slot_dao.update("next_focus", "female_ancestor")
                slot_dao.update("next_question", "And in what year was she born, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message("Great, let me just make a note of that!")
                dispatcher.utter_message(f"So, she was born in {birthplace}. Is that correct?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_female_ancestors_place_of_death(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the place of death that was supplied in the user's most recent input.
        deathplace = next(tracker.get_latest_entity_values("GPE"), None)

        if deathplace:
            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the mother's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the mother record with the newly learned place of death.
            if len(results) > 0:
                mother_id = results[0].mother
                family_member_dao.update(mother_id, family_member_fields.DEATHPLACE, deathplace.capitalize())

                # Retrieve the mother's overall title to be used to construct a follow-up question.
                title = None
                mother_results = family_member_dao.get_by(family_member_fields.ID, mother_id)
                if len(mother_results) > 0:
                    title = mother_results[0].familial_title

                # Reply to the user.
                dispatcher.utter_message(f"If you could describe your {title} in a few lines, what would you say?\nPlease start your sentence with: 'A brief description:'.")
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

        return [SlotSet("discussing_death", False)]

    @staticmethod
    def process_male_ancestors_birthplace(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the birthplace that was supplied in the user's most recent input.
        birthplace = next(tracker.get_latest_entity_values("GPE"), None)

        if birthplace:
            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the father's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the father record with the newly learned birthplace.
            if len(results) > 0:
                father_id = results[0].father
                family_member_dao.update(father_id, family_member_fields.BIRTHPLACE, birthplace.capitalize())

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.BIRTHYEAR}")
                slot_dao.update("last_id_updated", father_id)
                slot_dao.update("current_question", "So, where was he born, may I ask?")
                slot_dao.update("next_focus", "male_ancestor")
                slot_dao.update("next_question", "And in what year was he born, may I ask?")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message("Great, let me just make a note of that!")
                dispatcher.utter_message(f"Ah, so he was born in {birthplace}. Am I correct?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_male_ancestors_place_of_death(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the place of death that was supplied in the user's most recent input.
        deathplace = next(tracker.get_latest_entity_values("GPE"), None)

        if deathplace:
            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the father's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the father record with the newly learned place of death.
            if len(results) > 0:
                father_id = results[0].father
                family_member_dao.update(father_id, family_member_fields.DEATHPLACE, deathplace.capitalize())

                # Retrieve the father's overall title to be used to construct a follow-up question.
                title = None
                father_results = family_member_dao.get_by(family_member_fields.ID, father_id)
                if len(father_results) > 0:
                    title = father_results[0].familial_title

                # Update the fields required to roll back the previous update.
                slot_dao.update("last_fields_updated", f"{family_member_fields.BIRTHYEAR}")
                slot_dao.update("last_id_updated", father_id)
                slot_dao.update("current_question", "So, where was he born, may I ask?")
                slot_dao.update("next_focus", "male_ancestor")
                slot_dao.update("next_question", f"If you could describe your {title} in a few lines, what would you say?\nPlease start your sentence with: 'A brief description:'.")

                # Give the user the option of rolling back the previous update.
                buttons = [
                    {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                    {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
                ]

                dispatcher.utter_message(f"Could I just verify that he was living in {deathplace} when he passed away?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

        return [SlotSet("discussing_death", False)]

    @staticmethod
    def process_users_birthplace(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the birthplace that was supplied in the user's most recent input.
        birthplace = next(tracker.get_latest_entity_values("GPE"), None)

        if birthplace:
            # Update the first row in the DB, as this is a placeholder that will become the main user (required by family_tree.js).
            FamilyMemberDAO().update(1, family_member_fields.BIRTHPLACE, birthplace.capitalize())

            # Update the fields required to roll back the previous update.
            slot_dao = SlotDAO()
            slot_dao.update("last_fields_updated", f"{family_member_fields.BIRTHPLACE}")
            slot_dao.update("last_id_updated", 1)
            slot_dao.update("current_question", "Would you mind if I ask where you're originally from?")
            slot_dao.update("next_question", f"Ah, I see, so you were born in {birthplace}. In what year would that have been, if you don't my asking?")

            # Give the user the option of rolling back the previous update.
            buttons = [
                {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
            ]

            dispatcher.utter_message(f"So you were born in {birthplace}. Is that correct?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    def name(self) -> Text:
        return "action_process_place_given"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_focus = slot_dao.get("current_focus")
        discussing_death = tracker.get_slot("discussing_death")

        if not discussing_death:
            if current_focus.casefold() == "user".casefold():
                return self.process_users_birthplace(dispatcher, tracker)
            elif current_focus.casefold() == "male_ancestor".casefold():
                return self.process_male_ancestors_birthplace(dispatcher, tracker)
            elif current_focus.casefold() == "female_ancestor".casefold():
                return self.process_female_ancestors_birthplace(dispatcher, tracker)
        else:
            if current_focus.casefold() == "male_ancestor".casefold():
                return self.process_male_ancestors_place_of_death(dispatcher, tracker)
            elif current_focus.casefold() == "female_ancestor".casefold():
                return self.process_female_ancestors_place_of_death(dispatcher, tracker)


class ActionProcessYearGiven(Action):
    # Potential ways of asking the user about whether or not their ancestor is still alive.
    questions_about_female_ancestors_status = ["I'm very sorry to have to ask, but is your <title> still alive?",
                                               "Forgive me for asking, but is your <title> still with us?",
                                               "If I may ask, is she still with us?",
                                               "If you don't mind my asking, is she still alive?"]

    questions_about_male_ancestors_status = ["I'm very sorry to have to ask, but is your <title> still alive?",
                                               "Forgive me for asking, but is your <title> still with us?",
                                               "If I may ask, is he still with us?",
                                               "If you don't mind my asking, is he still alive?"]

    @staticmethod
    def sliding_window(text):
        for i in range(len(text) - 3):
            substring = text[i:i + 4]
            if substring.isdigit():
                return substring
        return None

    @staticmethod
    def process_female_ancestors_birthyear(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the birthyear that was supplied in the user's most recent input.
        birthdate = next(tracker.get_latest_entity_values("DATE"), None)

        if birthdate:
            birthyear = ActionProcessYearGiven.sliding_window(birthdate)

            # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the mother's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the mother record with the newly learned birthyear.
            if len(results) > 0:
                mother_id = results[0].mother
                family_member_dao.update(mother_id, family_member_fields.BIRTHYEAR, birthyear)

                # Retrieve the mother's overall title to be used to construct a follow-up question.
                mother_results = family_member_dao.get_by(family_member_fields.ID, mother_id)
                if len(mother_results) > 0:
                    title = mother_results[0].familial_title

                    # Reply to the user.
                    buttons = [
                        {"title": "Yes", "payload": "/user_gives_confirmation_of_life"},
                        {"title": "No", "payload": "/user_gives_confirmation_of_death"}
                    ]

                    dispatcher.utter_message("Great, let me just make a note of that.")

                    # If the ancestor in question is older than a great-grandparent, do not seek confirmation of their death, and simply ask when they passed away.
                    if "great-great" in title:
                        dispatcher.utter_message("If you don't mind my asking, in what year did she die?")
                        return [SlotSet("discussing_death", True)]
                    else:
                        dispatcher.utter_message(random.choice(ActionProcessYearGiven.questions_about_female_ancestors_status).replace("<title>", title), buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_female_ancestors_year_of_death(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the year of death that was supplied in the user's most recent input.
        deathdate = next(tracker.get_latest_entity_values("DATE"), None)

        if deathdate:
            mother_id = -1
            deathyear = ActionProcessYearGiven.sliding_window(deathdate)

            # Retrieve the ID of the child to which this person is a mother from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the mother's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the mother record with the newly learned year of death.
            if len(results) > 0:
                mother_id = results[0].mother
                family_member_dao.update(mother_id, family_member_fields.DEATHYEAR, deathyear)

            # Update the fields required to roll back the previous update.
            slot_dao.update("last_fields_updated", f"{family_member_fields.DEATHYEAR}")
            slot_dao.update("last_id_updated", mother_id)
            slot_dao.update("current_question", "Would you mind if I ask when she died?")
            slot_dao.update("next_focus", "female_ancestor")
            slot_dao.update("next_question", "I see. And where was she living when he passed away?")

            # Give the user the option of rolling back the previous update.
            buttons = [
                {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
            ]

            # Reply to the user.
            dispatcher.utter_message("Let me just jot that down.")
            dispatcher.utter_message(f"So, she passed away in {deathyear}. Is that correct?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_male_ancestors_birthyear(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the birthyear that was supplied in the user's most recent input.
        birthdate = next(tracker.get_latest_entity_values("DATE"), None)

        if birthdate:
            birthyear = ActionProcessYearGiven.sliding_window(birthdate)

            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the father's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the father record with the newly learned birthyear.
            if len(results) > 0:
                father_id = results[0].father
                family_member_dao.update(father_id, family_member_fields.BIRTHYEAR, birthyear)

                # Retrieve the father's overall title to be used to construct a follow-up question.
                father_results = family_member_dao.get_by(family_member_fields.ID, father_id)
                if len(father_results) > 0:
                    title = father_results[0].familial_title

                    # Reply to the user.
                    buttons = [
                        {"title": "Yes", "payload": "/user_gives_confirmation_of_life"},
                        {"title": "No", "payload": "/user_gives_confirmation_of_death"}
                    ]

                    dispatcher.utter_message("Great, let me just write that down.")

                    # If the ancestor in question is older than a great-grandparent, do not seek confirmation of their death, and simply ask when they passed away.
                    if "great-great" in title:
                        dispatcher.utter_message("If you don't mind my asking, in what year did he die?")
                        return [SlotSet("discussing_death", True)]
                    else:
                        dispatcher.utter_message(random.choice(ActionProcessYearGiven.questions_about_male_ancestors_status).replace("<title>", title), buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_male_ancestors_year_of_death(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the year of death that was supplied in the user's most recent input.
        deathdate = next(tracker.get_latest_entity_values("DATE"), None)

        if deathdate:
            father_id = -1
            deathyear = ActionProcessYearGiven.sliding_window(deathdate)

            # Retrieve the ID of the child to which this person is a father from a pre-defined slot.
            slot_dao = SlotDAO()
            child_id = int(slot_dao.get("current_child_id"))

            # Get the father's ID.
            family_member_dao = FamilyMemberDAO()
            results = family_member_dao.get_by(family_member_fields.ID, child_id)

            # Update the father record with the newly learned year of death.
            if len(results) > 0:
                father_id = results[0].father
                family_member_dao.update(father_id, family_member_fields.DEATHYEAR, deathyear)

            # Update the fields required to roll back the previous update.
            slot_dao.update("last_fields_updated", f"{family_member_fields.DEATHYEAR}")
            slot_dao.update("last_id_updated", father_id)
            slot_dao.update("current_question", "Would you mind if I ask when he died?")
            slot_dao.update("next_focus", "male_ancestor")
            slot_dao.update("next_question", "I see. And where was he living when he passed away?")

            # Give the user the option of rolling back the previous update.
            buttons = [
                {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
            ]

            # Reply to the user.
            dispatcher.utter_message("Let me just jot that down.")
            dispatcher.utter_message(f"Ah, so he passed away in {deathyear}. Is that the correct year?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch that.")

    @staticmethod
    def process_users_birthyear(dispatcher: CollectingDispatcher, tracker: Tracker):
        # Retrieve the birthyear that was supplied in the user's most recent input.
        birthdate = next(tracker.get_latest_entity_values("DATE"), None)

        if birthdate:
            birthyear = ActionProcessYearGiven.sliding_window(birthdate)

            # Update the first row in the DB, as this is a placeholder that will become the main user (required by family_tree.js).
            FamilyMemberDAO().update(1, family_member_fields.BIRTHYEAR, birthyear)

            # Update the fields required to roll back the previous update.
            slot_dao = SlotDAO()
            slot_dao.update("last_fields_updated", f"{family_member_fields.BIRTHYEAR}")
            slot_dao.update("last_id_updated", 1)
            slot_dao.update("current_question", "Would you mind if I ask when you were born?")
            slot_dao.update("next_focus", "male_ancestor")
            slot_dao.update("next_question", "Perfect, I've just made a note of that. Would you mind if I ask about your father? What was his name?")

            # Give the user the option of rolling back the previous update.
            buttons = [
                {"title": "Yes, that's correct", "payload": "/user_confirms_correct_information"},
                {"title": "No, please undo that", "payload": "/user_confirms_incorrect_information"}
            ]

            dispatcher.utter_message(f"Am I right in saying that you were born in {birthyear}?", buttons = buttons)
        else:
            dispatcher.utter_message("I'm sorry, I didn't catch your birthdate.")

    def name(self) -> Text:
        return "action_process_year_given"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slot_dao = SlotDAO()
        current_focus = slot_dao.get("current_focus")
        discussing_death = tracker.get_slot("discussing_death")
        
        if not discussing_death:
            if current_focus.casefold() == "user".casefold():
                return self.process_users_birthyear(dispatcher, tracker)
            elif current_focus.casefold() == "male_ancestor".casefold():
                return self.process_male_ancestors_birthyear(dispatcher, tracker)
            elif current_focus.casefold() == "female_ancestor".casefold():
                return self.process_female_ancestors_birthyear(dispatcher, tracker)
        else:
            if current_focus.casefold() == "male_ancestor".casefold():
                return self.process_male_ancestors_year_of_death(dispatcher, tracker)
            elif current_focus.casefold() == "female_ancestor".casefold():
                return self.process_female_ancestors_year_of_death(dispatcher, tracker)