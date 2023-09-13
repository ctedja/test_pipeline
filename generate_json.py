import json

def main():
    # Sample data to be written to JSON file
    data = {
        "name": "John Doe",
        "age": 30,
        "city": "California"
    }

    # Create or overwrite a JSON file with the data
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

if __name__ == "__main__":
    main()