from db import pgvector
from openai_embedding import generate_embedding

def formatDict(data: list[dict]) -> str:
    """
    Example output:
        book_title: A Guide to Git and Github
        chapter_title: Next Steps
        chapter_url: http://launchschool.com/books/git/read/next_steps
    """
    result = ""
    for dic in data:
        for k, v in dic.items():
            if k not in ['id', 'cosine_similarity']:
                result += f"{k}: {v}\n"
        result += "\n"    
    return result.strip()

def main():
    print("/exit to quit this program")
    print("Assistant: Can I help you find a book?  Tell me what you're looking for...")
    while True:
        i = input("\nUser: ")
        if i == "/exit":
            print("Goodbye!")
            quit()

        embed = generate_embedding(i)
        result = pgvector.get_similar(embed, 5)

        print("\nAssistant: Here you go!")
        print(formatDict(result))   
        print("\nWas that it or would you like me to search for something else?") 

if __name__ == "__main__":
    main()    

