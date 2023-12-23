import json
import requests
from tenacity import (
    retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
)

store_url = "https://example.myshopify.com"
access_token = "your_access_token"
blog_id = "your_blog_id"  # Replace with the actual blog ID

headers = {
    "X-Shopify-Access-Token": access_token,
    "Content-Type": "application/json"
}

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def get_blogs(store_url, access_token):
    """
    Retrieves all blogs from the specified Shopify store using the Shopify Admin API.

    The function makes an HTTP GET request to the Shopify API's blog endpoint. It is decorated with a retry mechanism which retries the request on encountering specific exceptions (like network-related errors) with exponential backoff.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.

    Returns:
    - dict: A dictionary object containing the response data with all blogs if successful.

    Raises:
    - Exception: If the request fails or the response status is not 200, it raises an exception with the error code and text.

    Usage:
    - blogs = get_blogs('https://example.myshopify.com', 'your_access_token')
      print(blogs)  # Prints the list of blogs retrieved from the Shopify store.
    """
    pass
        
@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def create_blog_with_metafields(store_url, access_token, title, key, value, type, namespace):
    pass

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def create_article(store_url, access_token, blog_id, title, author, tags, body_html):
    pass

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def get_articles(store_url, access_token, blog_id):
    pass
    
@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def get_article_count(store_url, access_token, blog_id):
    pass
