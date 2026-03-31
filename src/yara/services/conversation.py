"""
Planning:
    Conversation consists of one or more entries
    Entry can be a 'user', 'developer', or 'assistant' entry
    Each entry has a 'role' and a 'content' key
    Other entries are possible

    Methods:
        to_dict() - for the LLM
        to_string() - pretty-prints with Rich
"""
