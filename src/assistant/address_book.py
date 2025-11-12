from assistant.models import Record, Field, AddressBook
from assistant.handlers import input_error


class Address(Field):
    """Клас для зберігання адреси (рядок без валідації)."""
    def __init__(self, value: str):
        super().__init__(value)


@input_error
def add_address(args: list[str], book: AddressBook) -> str:
    """Додає адресу до контакту."""
    name, address_str, *_ = args
    record = book.find(name)
    if not record:
        raise KeyError
    if not hasattr(record, "addresses"):
        record.addresses = []
    record.addresses.append(Address(address_str))
    return "Address added."


@input_error
def change_address(args: list[str], book: AddressBook) -> str:
    """Редагує адресу контакту за старим значенням."""
    name, old_address, new_address, *_ = args
    record = book.find(name)
    if not record or not hasattr(record, "addresses"):
        raise KeyError
    for addr in record.addresses:
        if addr.value == old_address:
            addr.value = new_address
            return "Address updated."
    return "Old address not found."


@input_error
def show_address(args: list[str], book: AddressBook) -> str:
    """Показує всі адреси контакту."""
    name = args[0]
    record = book.find(name)
    if not record or not hasattr(record, "addresses"):
        raise KeyError
    return "; ".join(addr.value for addr in record.addresses) or "No addresses."


@input_error
def remove_address(args: list[str], book: AddressBook) -> str:
    """Видаляє адресу контакту за значенням."""
    name, address_str, *_ = args
    record = book.find(name)
    if not record or not hasattr(record, "addresses"):
        raise KeyError
    record.addresses = [addr for addr in record.addresses if addr.value != address_str]
    return "Address removed."