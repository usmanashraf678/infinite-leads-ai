import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from utils import save_to_json, get_new_posts, save_raw_posts_to_csv, extract_listing_details, read_sample_results, save_posts_with_gpt_results_to_csv, hit_apify_api

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("facebook_scraper.log"),
        logging.StreamHandler()
    ],
)



groups = [
    {
        "group_url": "https://www.facebook.com/groups/468407051306591",
        "max_posts": 10,
        "view_option": "CHRONOLOGICAL",
    }
]


def parse_apify_response(results):
    posts = []
    images = []
    for data in results:
        post = {
            "apify_post_id": data["id"],
            "fb_post_id": data["legacyId"],
            "user_name": data["user"]["name"],
            "post_content": data["text"],
            "post_url": data["url"],
            "group_url": data["facebookUrl"],
            "creation_date": data["time"],
        }
        posts.append(post)

        attachment_count = 0
        for attachment in data.get("attachments", []):
            attachment_count += 1
            image_url = attachment.get("photo_image", {}).get("uri") or attachment.get(
                "image", {}
            ).get("uri")

            if image_url:
                if attachment.get("id") is None:
                    logging.info(
                        f"Attachment ID is missing for post {data['legacyId']}"
                    )
                    attachment["id"] = data["legacyId"] + "_" + str(attachment_count)

                images.append(
                    {
                        "fb_image_id": attachment.get("id"),
                        "fb_post_id": data["legacyId"],
                        "image_url": image_url,
                    }
                )

    return posts, images

def scrape_facebook_group(group_url, results_limit, view_option, formatted_date):
    """

    `scrape_facebook_group` scrapes a Facebook group for posts and images, extracts relevant data, and saves it to a csv.

    :param group_url: URL of a public Facebook group to scrape.
    :param results_limit: Number of posts to scrape (default: 20). If not set, only the initial page is returned.
    :param view_option: Sorting order for posts. Options: "CHRONOLOGICAL", "RECENT_ACTIVITY", "TOP_POSTS", "CHRONOLOGICAL_LISTINGS" (default: "CHRONOLOGICAL").

    """
    logging.info("Starting to scrape Facebook group")
    
    # results = hit_apify_api(group_url, results_limit, view_option, formatted_date)
    results = read_sample_results() # for debugging only


    posts, images = parse_apify_response(results)

    new_posts = get_new_posts(posts)
    save_raw_posts_to_csv(new_posts)
    
    listings_details = extract_listing_details(new_posts)
    logging.info(listings_details)
    
    save_posts_with_gpt_results_to_csv(listings_details)


def scrape_a_batch_of_groups(groups):
    """
    `scrape_a_batch_of_groups` scrapes multiple Facebook groups for posts and images, extracts relevant data, and saves it to csv files.

    :param group_urls: List of URLs of public Facebook groups to scrape.
    :param results_limit: Number of posts to scrape per group.
    :param view_option: Sorting order for posts. Options: "CHRONOLOGICAL", "RECENT_ACTIVITY", "TOP_POSTS", "CHRONOLOGICAL_LISTINGS" (default: "CHRONOLOGICAL").

    """

    logging.info("Starting to scrape Facebook groups")

    # read tagret groups from yaml file

    # Get date 3 days ago
    today = datetime.today()
    three_days_ago = today - timedelta(days=3)
    formatted_date = three_days_ago.strftime("%Y-%m-%d")

    for group in groups:
        group_url = group["group_url"]
        results_limit = group["max_posts"]
        view_option = group["view_option"]

        logging.info("Scraping group: %s", group_url)
        scrape_facebook_group(group_url, results_limit, view_option, formatted_date)

    logging.info("Finished scraping Facebook groups")


if __name__ == "__main__":
    scrape_a_batch_of_groups(groups)
