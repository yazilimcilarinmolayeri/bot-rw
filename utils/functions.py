import csv


def os_release() -> str:
    with open("/etc/os-release") as file:
        reader = dict(csv.reader(file, delimiter="="))

    return reader["PRETTY_NAME"]
