from collections.abc import Sequence
from typing import Literal, TypedDict

from rich import print

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
        return next(
            entry["content"] for entry in self.entries if entry["role"] == "assistant"
        )

    def add_entry(self, role: Role, content: str) -> None:
        self.entries.append({"role": role, "content": content})

    def reset(
        self, developer_content: str = SYSTEM_PROMPT, greeting: str = DEFAULT_GREETING
    ) -> None:
        self.entries.clear()
        self.add_entry("developer", developer_content)
        self.add_entry("assistant", greeting)

    def get_entries(self) -> Sequence[Entry]:
        """
        Warning: do not mutate the object returned by this method!
        """
        return self.entries

    def get_augmented_entries(self, developer_prompt: str):
        """
        Return a shallow copy of the conversation
        that's augmented by the provided prompt
        """

        result = [*self.get_entries()] + [
            {"role": "developer", "content": developer_prompt}
        ]
        print(result)
        print(self.get_entries() is result)
        return result


if __name__ == "__main__":
    c = Conversation()
    c.get_augmented_entries("You are a paperweight")
