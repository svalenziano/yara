


def basic_rag(query, conversation):
    """
    Input: query and convo
    Side effects: mutate convo to reflect new interactions
    Return: last assistant response

    Algo:
        - Augment convo w chunks from vector DB
    """