from services.client import HTTPClient
from utils.helpers import format_response

def main():
    client = HTTPClient()
    response = client.get("https://api.example.com")
    formatted = format_response(response)
    print(formatted)

if __name__ == "__main__":
    main()