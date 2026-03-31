from typing import Literal, TypedDict

Role = Literal["developer", "assistant", "user"]


class Entry(TypedDict):
    role: Role
    content: str


SYSTEM_PROMPT = (
    "You are a helpful AI assistant tasked with helping the user"
    " find materials within a database of documents.  "
)

DEFAULT_GREETING = "How can I help you today?"

class Conversation:
    def __init__(self, greeting: str | None = None):
        self.entries: list[Entry] = [
            {"role": "developer", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": greeting or DEFAULT_GREETING},
        ]

    def __len__(self):
        return len(self.entries)


    def first_assistant_prompt(self):
        return next(entry['content'] for entry in self.entries)

    def add_entry(self, role: Role, content: str) -> None:
        self.entries.append({"role": role, "content": content})

    def to_dict(self) -> list[Entry]:
        return self.entries
