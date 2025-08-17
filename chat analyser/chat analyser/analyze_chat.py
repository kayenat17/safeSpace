import requests

API_KEY = "AIzaSyBaNMgep5Hq6bKaMbaxWnXaKZxJ2fBNz7Y"  # <-- Put your actual Perspective API key here

def analyze_chat(text):
    """
    Analyze the toxicity of a given text using the Perspective API.
    Args:
        text (str): The text to analyze
    Returns:
        float: The toxicity score (0-1)
    """
    try:
        response = requests.post(
            f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={API_KEY}",
            json={
                "comment": {"text": text},
                "languages": ["en"],
                "requestedAttributes": {"TOXICITY": {}}
            }
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        score = response.json()["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
        print(f"Toxicity Score: {score}")
        return score
    except requests.exceptions.RequestException as e:
        print(f"Error analyzing text: {str(e)}")
        if "400" in str(e):
            print("\nThis might be because:")
            print("1. The API key is invalid")
            print("2. The API key doesn't have the necessary permissions")
            print("3. The API key hasn't been activated yet")
        return None

if __name__ == "__main__":
    # Test the function
    test_text = "You are beautiful I care for you"
    analyze_chat(test_text) 