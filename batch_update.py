# this script updates all messages currently stored in the database without
# an "author" property and gives them a default author
from google.cloud import datastore

if __name__ == "__main__":
    print("updating messages...")
    db = datastore.Client()
    db_query = db.query(kind="message")
    print("querying messages...")
    messages = list(db_query.fetch())
    print(f"queried {len(messages)} messages")
    for message in messages:
        message["author"] = "116594506775531743425"
        print(message["channel"], message["content"])
        db.put(message)
    print("done")