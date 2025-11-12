from assistant.models import AddressBook, Record, Birthday
from assistant.storage import save_data, load_data

def create_birthdays(book: AddressBook):
    birthdays = [
        ("John Smith", "01.01.1990"),
        ("Emma Brown", "12.12.1985"),
        ("Liam Johnson", "25.03.2000")
    ]

    for name, bday_str in birthdays:
        record = book.find(name)
        if not record:
            record = Record(name)
            book.add_record(record)
        if not record.birthday:
            record.add_birthday(bday_str)
    return book

if __name__ == "__main__":
    book = load_data()
    book = create_birthdays(book)
    save_data(book)
    print("Birthdays added successfully!")
