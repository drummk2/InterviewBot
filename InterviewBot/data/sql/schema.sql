DROP TABLE IF EXISTS FamilyMember;
DROP TABLE IF EXISTS Slot;

CREATE TABLE FamilyMember (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT,
    [forename] TEXT,
    [surname] TEXT,
    [birthyear] TEXT,
    [deathyear] TEXT,
    [birthplace] TEXT,
    [deathplace] TEXT,
    [father] INTEGER,
    [mother] INTEGER,
    [children] TEXT,
    [unions] TEXT,
    [familial_title] TEXT,
    [biography] TEXT
);

CREATE TABLE Slot (
    [slot_name] TEXT PRIMARY KEY,
    [slot_value] TEXT
);

-- Preload data in the FamilyMember table.
INSERT INTO FamilyMember(forename, surname, birthyear, deathyear, birthplace, deathplace, father, mother, children, unions, familial_title, biography)
VALUES ('', '', '', '', '', '', NULL, NULL, NULL, NULL, 'user', '');

-- Preload data into the Slot table.
INSERT INTO Slot(slot_name, slot_value)
VALUES ('current_child_id', '-1');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('current_focus', 'user');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('current_question', '');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('forename', '');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('last_fields_updated', '');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('last_id_updated', '');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('next_focus', 'user');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('next_question', '');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('surname', '');

INSERT INTO Slot(slot_name, slot_value)
VALUES ('surname_required', 'false');