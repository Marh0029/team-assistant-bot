from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps
import pickle  


class Field:
    """Базовий клас для всіх полів."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Клас для зберігання імені контакту."""
    def __init__(self, value):
        if not value:
            raise ValueError("Invalid name.")
        super().__init__(value)


class Phone(Field):
    """Клас для зберігання номера телефону з валідацією (10 цифр)."""
    def __init__(self, value):
        if not self._validate(value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)

    @staticmethod
    def _validate(value: str) -> bool:
        return value.isdigit() and len(value) == 10

    @property
    def phone_number(self) -> str:
        return self.value
    
    def update_number(self, new_number: str) -> None:
        """Оновлює номер телефону з валідацією."""
        if not self._validate(new_number):
            raise ValueError("Phone number must contain exactly 10 digits.")
        self.value = new_number


class Birthday(Field):
    """Клас для зберігання дати народження (формат DD.MM.YYYY)."""
    def __init__(self, value: str):
        try:
            # Перетворити рядок на datetime та зберегти у value
            dt = datetime.strptime(value, "%d.%m.%Y")
            super().__init__(dt.date())
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    @property
    def date_str(self) -> str:
        """Повертає дату у вихідному форматі."""
        return self.value.strftime("%d.%m.%Y")


class Record:
    """Клас для зберігання інформації про контакт."""
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone_number: str) -> None:
        """Додає номер телефону до запису."""
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number: str) -> None:
        """Видаляє номер телефону з запису."""
        phone = self.find_phone(phone_number)
        if phone:
            self.phones.remove(phone)

    def edit_phone(self, old_number: str, new_number: str) -> bool:
        """Редагує номер телефону в записі."""
        phone = self.find_phone(old_number)
        if phone:
            phone.update_number(new_number)
            return True
        return False
    
    def find_phone(self, phone_number: str) -> Phone | None:
        """Знаходить номер телефону в записі."""
        for ph in self.phones:
            if ph.phone_number == phone_number:
                return ph
        return None

    def add_birthday(self, birthday_str: str) -> None:
        """Додає день народження до контакту."""
        if self.birthday is not None:
            raise ValueError("Birthday already set.")
        self.birthday = Birthday(birthday_str)

    def __str__(self) -> str:
        phones_str = "; ".join(p.phone_number for p in self.phones) or "No phones"
        bday = self.birthday.date_str if self.birthday else "N/A"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {bday}"


class AddressBook(UserDict):
    """Клас для зберігання та управління колекцією записів."""
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        """Знаходить запис за ім'ям."""
        return self.data.get(name)

    def delete(self, name: str) -> None:
        """Видаляє запис за ім'ям."""
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> list[str]:
        """Повертає список вітальних повідомлень на наступний тиждень."""
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        greetings = []
        for rec in self.data.values():
            if rec.birthday:
                # оновити рік на поточний
                bday_this_year = rec.birthday.value.replace(year=today.year)
                # якщо вже пройшов у цьому році – брати наступний рік
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                if today <= bday_this_year <= next_week:
                    # якщо день народження припадає на вихідні – переносимо на наступний понеділок
                    congr_date = bday_this_year
                    if congr_date.weekday() >= 5:  # 5 = субота, 6 = неділя
                        congr_date = congr_date + timedelta(days=(7 - congr_date.weekday()))
                    greetings.append(
                        f"{congr_date.strftime('%Y-%m-%d')}: {rec.name.value}"
                    )
        return greetings


def save_data(book: AddressBook, filename: str = "addressbook.pkl") -> None:
    """Серіалізація адресної книги у файл за допомогою pickle."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename: str = "addressbook.pkl") -> AddressBook:
    """Десеріалізація адресної книги з файлу, або створення нової, якщо файл відсутній."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    """Декоратор для обробки помилок вводу користувача."""
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter the command followed by necessary arguments."
    return inner


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """Парсить вхідний рядок на команду та аргументи."""
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd = parts[0].lower()
    return cmd, parts[1:]


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """Додає або оновлює контакт у адресній книзі."""
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """Змінює номер телефону для вказаного контакту."""
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if not record:
        raise KeyError
    if record.edit_phone(old_phone, new_phone):
        return "Phone updated."
    return "Old phone not found."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    """Показує телефонні номери для вказаного контакту."""
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError
    phones = "; ".join(p.phone_number for p in record.phones) or "No phones."
    return phones


def show_all(book: AddressBook) -> str:
    """Показує всі контакти в адресній книзі."""
    if not book.data:
        return "No contacts."
    return "\n".join(str(rec) for rec in book.data.values())


@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    """Додає дату народження для вказаного контакту."""
    name, bday_str, *_ = args
    record = book.find(name)
    if not record:
        raise KeyError
    record.add_birthday(bday_str)
    return "Birthday added."


@input_error
def show_birthday(args: list[str], book: AddressBook) -> str:
    """Показує дату народження для вказаного контакту."""
    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError
    if record.birthday:
        return record.birthday.date_str
    return "Birthday not set."


def birthdays(book: AddressBook) -> str:
    """Показує дні народження, які відбудуться протягом наступного тижня."""
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(upcoming)


def main():
    #Завантажуэмо AddressBook з файлу
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        if command in ("close", "exit"):
            #Перед виходом зберігаємо AddressBook у файл
            save_data(book)
            print("Data saved. Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()