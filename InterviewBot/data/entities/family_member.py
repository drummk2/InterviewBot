from dataclasses import dataclass


@dataclass
class FamilyMember:
    unique_id: int = None,
    forename: str = None,
    surname: str = None,
    birthyear: str = None,
    deathyear: str = None,
    birthplace: str = None,
    deathplace: str = None,
    father: int = None,
    mother: int = None,
    children: str = None,
    unions: str = None,
    familial_title: str = None
    biography: str = None

    def __init__(
            self,
            unique_id: int,
            forename: str,
            surname: str,
            birthyear: str,
            deathyear: str,
            birthplace: str,
            deathplace: str,
            father: int,
            mother: int,
            children: str,
            unions: str,
            familial_title: str,
            biography: str):
        self.unique_id = unique_id
        self.forename = forename
        self.surname = surname
        self.birthyear = birthyear
        self.deathyear = deathyear
        self.birthplace = birthplace
        self.deathplace = deathplace
        self.father = father
        self.mother = mother
        self.children = children
        self.unions = unions
        self.familial_title = familial_title
        self.biography = biography

    def add_child(self, family_member_id: int) -> None:
        if self.children == "" or self.children is None:
            self.children = f"{family_member_id}"
        else:
            self.children += f",{family_member_id}"

    def add_union(self, spouse_id: int) -> None:
        if self.unions == "" or self.unions == "-1" or self.unions is None:
            self.unions = f"{spouse_id}"
        else:
            self.unions += f",{spouse_id}"