import requests

# Ensure this perfectly matches your exact topic capitalization on the ntfy app
NTFY_TOPIC = "mumama"

def force_immediate_test():
    message_body = "🚀 Connection Success! Your GitHub code and phone are communicating perfectly."
    
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    print(f"Directly hitting: {url}")
    
    response = requests.post(
        url, 
        data=message_body.encode('utf-8'),
        headers={
            "Title": "GitHub Cloud Test Alert",
            "Priority": "high",
            "Tags": "tada,phone"
        }
    )
    print(f"Server Status Code: {response.status_code}")

if __name__ == "__main__":
    force_immediate_test()
