from enum import Enum

class SpeakerRole(str, Enum):
    AGENT = "agent"
    CLIENT = "client"
    UNKNOWN = "unknown"
