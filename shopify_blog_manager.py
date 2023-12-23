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
    """
    Creates a new blog with specified metafields in the Shopify store using the Shopify Admin API.

    This function makes an HTTP POST request to the Shopify API's blog creation endpoint. It includes metafields in the request, allowing for additional custom data to be associated with the blog. The function automatically retries on encountering specific exceptions (like network-related errors) with exponential backoff.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - title (str): Title of the new blog.
    - key (str): Key for the metafield.
    - value (str): Value for the metafield.
    - type (str): Type of the metafield (e.g., 'string', 'integer').
    - namespace (str): Namespace for the metafield, used for grouping and identifying metafields.

    Returns:
    - dict: A dictionary object containing the response data with details of the created blog if successful.

    Raises:
    - Exception: If the request fails or the response status is not 201, it raises an exception with the error code and text.

    Usage:
    - new_blog = create_blog_with_metafields('https://example.myshopify.com', 'your_access_token', 'My New Blog', 'sponsor', 'Shopify', 'string', 'global')
      print(new_blog)  # Prints the details of the newly created blog.
    """
    pass

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def create_article(store_url, access_token, blog_id, title, author, tags, body_html):
    """
    Creates a new article in a specified blog on the Shopify store using the Shopify Admin API.

    This function makes an HTTP POST request to the Shopify API's article creation endpoint for a specific blog. It includes details such as the article's title, author, tags, and body. The function automatically retries on encountering specific exceptions (like network-related errors) with exponential backoff.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - blog_id (str): The ID of the blog where the article will be created.
    - title (str): Title of the new article.
    - author (str): Author of the new article.
    - tags (str): Comma-separated tags for the new article.
    - body_html (str): HTML content of the new article.

    Returns:
    - dict: A dictionary object containing the response data with details of the created article if successful.

    Raises:
    - Exception: If the request fails or the response status is not 201, it raises an exception with the error code and text.

    Usage:
    - new_article = create_article('https://example.myshopify.com', 'your_access_token', '123456789', 'My First Article', 'John Doe', 'Fashion, Trends', '<p>This is the body of my article.</p>')
      print(new_article)  # Prints the details of the newly created article.
    """
    pass

@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def get_articles(store_url, access_token, blog_id):
    """
    Retrieves all articles from a specified blog in the Shopify store using the Shopify Admin API.

    This function makes an HTTP GET request to the Shopify API's articles endpoint for a specific blog. It is decorated with a retry mechanism which retries the request on encountering specific exceptions (like network-related errors) with exponential backoff.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - blog_id (str): The ID of the blog from which to retrieve articles.

    Returns:
    - dict: A dictionary object containing the response data with details of all articles if successful.

    Raises:
    - Exception: If the request fails or the response status is not 200, it raises an exception with the error code and text.

    Usage:
    - articles = get_articles('https://example.myshopify.com', 'your_access_token', '123456789')
      print(articles)  # Prints the list of articles retrieved from the specified blog.
    """
    pass
    
@retry(wait=wait_random_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def get_article_count(store_url, access_token, blog_id):
    """
    Retrieves the count of articles in a specified blog on the Shopify store using the Shopify Admin API.

    This function makes an HTTP GET request to the Shopify API's article count endpoint for a specific blog. It is decorated with a retry mechanism which retries the request on encountering specific exceptions (like network-related errors) with exponential backoff.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - blog_id (str): The ID of the blog for which to retrieve the article count.

    Returns:
    - dict: A dictionary object containing the response data with the count of articles if successful.

    Raises:
    - Exception: If the request fails or the response status is not 200, it raises an exception with the error code and text.

    Usage:
    - article_count = get_article_count('https://example.myshopify.com', 'your_access_token', '123456789')
      print(article_count)  # Prints the count of articles in the specified blog.
    """
    pass
