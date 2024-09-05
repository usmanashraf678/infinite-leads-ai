import logging
import json
from openai import OpenAI
import time
from dotenv import load_dotenv
import os
from apify_client import ApifyClient
import csv

apify_response_file = "apify_response.json"
apify_sample_response = "apify_sample_response.json"

load_dotenv(override=True)

API_KEY = os.getenv("API_KEY")
apify_client = ApifyClient(API_KEY)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def save_to_json(results, json_file_name):
    """
    The function `save_to_json` saves complete results to a JSON file with specified encoding and
    formatting.

    """
    logging.info("Saving complete results to JSON file")
    with open(json_file_name, "w", encoding="utf-8") as jsonfile:
        json.dump(results, jsonfile, ensure_ascii=False, indent=4)
    logging.info("Complete results saved to JSON file")


def save_raw_posts_to_csv(posts):
    """
    The function `save_raw_posts_to_csv` saves posts to a CSV file with specified encoding and formatting.

    """
    logging.info("Saving posts to CSV file")

    with open("posts.csv", "a", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        for post in posts:
            writer.writerow(
                [
                    post["apify_post_id"],
                    post["fb_post_id"],
                    post["user_name"],
                    post["post_content"],
                    post["post_url"],
                    post["group_url"],
                    post["creation_date"],
                ]
            )


def save_posts_with_gpt_results_to_csv(posts):
    """
    The function `save_raw_posts_to_csv` saves posts to a CSV file with specified encoding and formatting.

    """
    logging.info("Saving processed posts to CSV file")

    with open("processed_posts.csv", "a", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        for post in posts:
            writer.writerow(
                [
                    # post["apify_post_id"],
                    post["fb_post_id"],
                    post["user_name"],
                    post["relevant_intention"],
                    post["category"],
                    post["content"],
                ]
            )


def get_new_posts(posts):
    """
    The function `get_new_posts` filters out new posts from the complete list of posts.

    """
    logging.info("Filtering new posts")

    # read existing posts from posts.csv file
    existing_post_ids = set()
    try:
        with open("posts.csv", "r", encoding="utf-8") as csvfile:
            for line in csvfile:
                post_id = line.split(",")[0].strip()
                existing_post_ids.add(post_id)
    except FileNotFoundError:
        logging.error("Posts file not found")
    except UnicodeDecodeError as e:
        logging.error(f"Encoding error while reading the posts file: {e}")

    new_posts = []
    for post in posts:
        # Check if the post is new
        if post["apify_post_id"] not in existing_post_ids:
            new_posts.append(post)
    logging.info(f"Found {len(new_posts)} new posts")

    return new_posts


def extract_post_details(text):
    # Define the prompt

    system_prompt = f"""
    You are a expert business development officer. Your job is to identify possible leads for an immigration consultancy firm by analyzing facebook posts.
    The firm that you work for primarily focuses in student visa processing. 
    You should carefully study the posts provided and identify if there is a possiblity of a lead for the firm.
    Ignore posts that express gratitude for positive outcomes as they are already closed.
    You should focus only on cases that can be potential clients for the firm.

    """

    prompt = f"""
    The following text contains a post made in a facebook group regarding student visa in Australia.
    Your job is to identify if the job post contains an intention for the following:

    1. There is a change of course. A student is looking to change their educational instituion.
    2. A visa is to be processed or a visa processing agent is required. 
    3. Skill assessment is required by an applicant.
    4. A student needs to enroll in a new university.
    5. A student needs to get extension on their visa.

    You should reason through the job post and provide the result in JSON format where you provide a "Yes" or "No" for if any of the above intentions exist.
    You should also say the number of the intention for which you think this will fall under. There may be multiple categories as well. You can list them in a comma separated format.
    
    ```json
    Example response:
    {{
        "Relevant Intention": "Yes",
        "Category": "3, 5"
    }}
    ```

    
    Text: "{text}"
    """

    retries = 0
    max_retries = 5  # Set the maximum number of retries

    while retries < max_retries:
        try:
            completion = openai_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                model="gpt-3.5-turbo",
            )
            # Make the request to OpenAI API using the new interface

            # Extract the JSON from the response

            # response_text = completion.choices[0].message
            response_text = completion.choices[0].message.content
            logging.info(f"1. Response text: {response_text}")

            # response_text = completion['choices'][0]['message']['content']

            # Check if the response is empty
            if not response_text:
                logging.error("Empty response received from OpenAI.")
                return {"error": "Empty response received from OpenAI."}

            elif "NO DETAIL FOUND" in response_text:
                logging.error("NO DETAIL FOUND response received from OpenAI.")
                return {"error": "NO DETAIL FOUND response received from OpenAI."}

            # Remove backticks and any surrounding whitespace
            cleaned_response = response_text.strip().strip("```json").strip("```").strip()

            try:
                # Attempt to parse JSON from the cleaned response
                extracted_data = json.loads(cleaned_response)
                logging.info("Successfully extracted JSON data.")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}, {cleaned_response}")
                extracted_data = {"error": "Failed to extract data."}

            # time.sleep(10)

            logging.info(f"JSON read from cleaned response: {extracted_data}")
            return extracted_data

        except Exception as e:
            logging.error(f"Error for OpenAI: {e}")
            return {"error": str(e)}


def extract_listing_details(posts):
    """
    This function processes the posts to extract real estate-related parameters and prepares a list to be saved in the ScrapedListings table.
    """
    listings = []
    for post in posts:
        post_content = post["post_content"]
        extracted_data = extract_post_details(post_content)

        if "error" in extracted_data:
            logging.warning(
                f"Failed to extract data for post {post['fb_post_id']}: {extracted_data['error']}"
            )
            continue  # Skip this post if extraction failed

        listing = {
            "fb_post_id": post["fb_post_id"],
            "user_name": post["user_name"],
            "relevant_intention": extracted_data.get("Relevant Intention", "N/A"),
            "category": extracted_data.get("Category", "N/A"),
            "content": post["post_content"],
        }
        listings.append(listing)

    return listings


def read_sample_results():
    try:
        with open(apify_sample_response, "r", encoding="utf-8") as jsonfile:
            results = json.load(jsonfile)
    except FileNotFoundError:
        logging.error("Apify response file not found")
        results = []
    except UnicodeDecodeError as e:
        logging.error(f"Encoding error while reading the Apify response file: {e}")
        results = []

    return results


def hit_apify_api(group_url, results_limit, view_option, formatted_date):
    run_input = {
        "startUrls": [{"url": group_url}],
        "resultsLimit": results_limit,
        "viewOption": view_option,
        "onlyPostsNewerThan": formatted_date,
    }

    run = apify_client.actor("apify/facebook-groups-scraper").call(run_input=run_input)
    logging.info("Scraping done, fetching results")

    results = []
    for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)

    save_to_json(results, apify_response_file)

    return results
