from ingestson.raw import rows
from processing import extract_transforme


if __name__ == "__main__":
    data=row.to_row('./data')
    if data:
        extract_transforme.extract_from_rows(data[0])

