from dataclasses import dataclass


@dataclass
class Slot:
    slot_name: str = None
    slot_value: str = None

    def __init__(
            self,
            slot_name: int,
            slot_value: str):
        self.slot_name = slot_name
        self.slot_value = slot_value