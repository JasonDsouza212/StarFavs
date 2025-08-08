from dataclasses import dataclass


@dataclass
class CreateUserInput:
    email: str
    name: str
