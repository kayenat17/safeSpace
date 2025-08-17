# Chat Analyzer

A Python-based tool for analyzing text toxicity using the Perspective API.

## Setup

1. Make sure you have Python 3.6 or higher installed on your system.

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Perspective API key:
```
PERSPECTIVE_API_KEY=your_api_key_here
```

You can get an API key from the [Perspective API website](https://perspectiveapi.com/).

## Usage

```python
from analyze_chat import analyze_chat

# Analyze a text
score = analyze_chat("Your text here")
```

The function returns a toxicity score between 0 and 1, where higher scores indicate more toxic content.

## Features

- Text toxicity analysis using Google's Perspective API
- Environment variable support for API key management
- Error handling for API requests
- Simple and easy-to-use interface

## Example

```python
# Example usage
text = "You are beautiful I care for you"
score = analyze_chat(text)
if score is not None:
    print(f"Toxicity score: {score}")
```

## Requirements

- Python 3.6+
- requests
- python-dotenv 