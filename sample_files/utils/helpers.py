def format_response(response):
    return f"Status: {response.status_code}, Data: {response.text[:100]}..."

def calculate_total(items):
    return sum(item.price for item in items)