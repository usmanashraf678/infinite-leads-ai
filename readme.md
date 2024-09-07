# Infinite Lead Gen AI
This repo houses a Lead Generator AI that can scrape public facebook groups of your choice and process its results through GPT to identify potential leads for your business. The AI is built using OpenAI's GPT-3 and Apify's Facebook Scraper API. If you want to use this AI, you will need to have an OpenAI API key and an Apify API key.

## Installation
You should follow the following steps to clone the repo and run it on your PC locally:


### Clone the project
```
git clone https://github.com/usmanashraf678/infinite-leads-ai
```

### Create Virtual Environment
```
python3 -m venv venv
```

### Activate the Virtual Environment
```
Linux: source venv/bin/activate
Windows: .\venv\Scripts\activate
```


### Install dependencies
```
pip install -r requirements.txt
```

### Manually install dependencies
If you don't want to install dependencies using the requirements.txt file, you can install them manually using the following commands:
```
venv/Scripts/activate

pip install apify-client
pip install python-dotenv
pip install openai
```

### Create a .env file
Create a .env file in the root directory of the project and add the following variables to it:
```
API_KEY=your_apify_token
OPENAI_API_KEY=your_openai_api_key
```

### Run the project
python main.py

### Output
The results will be saved to the `processed_posts.csv` which contains the information about if the post was relevant based on our criteria and the supporting reasons behind it.


## Supporting materials
More details about the project can be found on [this](https://www.youtube.com/channel/UCt7vMb0-rQNnEIeviI4tOLw) youtube channel. Search for Kartab#003.




