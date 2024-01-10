import re
import json
import requests
import tiktoken
from time import sleep
from openai import OpenAI
from urllib.parse import urlparse

def generate_content(client, messages, model='gpt-3.5-turbo-1106', show_output=False, show_tokens=False):
    """
    This function generates content by interacting with an OpenAI model specified by the user. 
    It sends messages to the model and retrieves the generated response in JSON format.

    Parameters:
    - client: The OpenAI API client instance to use for making requests.
    - messages: A list of message dicts representing the conversation history where each message contains a 'role' and 'content'.
    - model: The identifier of the model to use for the chat completion. Default is 'gpt-3.5-turbo-1106'.
    - show_output: If True, prints the content of the generated messages.
    - show_tokens: If True, prints the token usage information.

    Returns:
    - json_output: The content of the generated message in JSON format.

    The function first calls the OpenAI API's chat completions endpoint to generate a response from the provided messages. 
    It then processes the response to extract the usage information (if show_tokens is True) and the actual generated content. 
    If show_output is True, the function also prints the generated content before returning it.
    """
    # Generate the chat completion using the OpenAI API.
    chat_completion = client.chat.completions.create(
            messages=messages,
            # max_tokens=600,  # Uncomment and adjust as necessary.
            temperature=0.9,  # Adjust the randomness of the output (0.0-1.0).
            model=model,  # Model to use for completion.
            response_format={"type": "json_object"},  # The format of the response.
        )
    
    # Dump the model's response to access detailed information.
    D = chat_completion.model_dump()
    
    # If requested, print the token usage information.
    if show_tokens:
        print(D['usage'])
    
    # Extract and print the generated message content.
    json_output = D['choices'][0]['message']['content']
    if show_output:
        print(json_output)
    
    # Return the generated content.
    return json_output

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """
    Returns the number of tokens used by a list of messages for a specific model.

    Parameters:
    - messages: A list of dictionaries representing the conversation. Each dictionary
                should have keys like "role" and "content".
    - model: A string specifying the AI model's version (default is "gpt-3.5-turbo-0613").

    Returns:
    - An integer representing the total number of tokens that the provided messages
      would consume when encoded for the specified AI model.

    This function calculates the token count to understand how much of the model's
    capacity the messages are using, which is important for managing API usage and
    ensuring efficient interactions.
    """
    try:
        # Retrieve the encoding method for the specified model
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback encoding if the specified model's encoding isn't found
        encoding = tiktoken.get_encoding("cl100k_base")

    # Check if the model is a GPT model (future models might have different formats)
    if "gpt" in model:
        num_tokens = 0  # Initialize the token count
        # Calculate the number of tokens for each message
        for message in messages:
            # Add tokens for message delimiters and structure
            num_tokens += 4  # <im_start>{role/name}\n{content}<im_end>\n
            # Add tokens for the content of the message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # Adjust for name key presence
                    num_tokens -= 1  # Role is omitted if name is present
        # Add tokens for the assistant's reply priming
        num_tokens += 2  # <im_start>assistant
        return num_tokens
    else:
        # Raise error if the function doesn't support the provided model
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")

def calculate_pricing(input_tokens, output_tokens, model_name='gpt-4'):
    """
    Calculate the pricing for using an AI model based on the number of input and output tokens.

    Parameters:
    - input_tokens (int): The number of tokens in the input.
    - output_tokens (int): The number of tokens in the output.
    - model_name (str): The name of the model, either 'gpt-4' or 'gpt-3.5'.

    Returns:
    - float: The total cost of the operation.

    This function calculates the total cost by considering separate costs for input and
    output tokens and varies the pricing based on the model selected, allowing for a detailed
    understanding of the expense associated with the model's usage.
    """
    # Define the cost per 1,000 tokens for each model
    pricing = {
        'gpt-4': {'input_cost_per_1k': 0.01, 'output_cost_per_1k': 0.03},
        'gpt-3.5': {'input_cost_per_1k': 0.001, 'output_cost_per_1k': 0.002}
    }

    # Check if the model_name is valid
    if model_name not in pricing:
        raise ValueError(f"Invalid model_name {model_name}. Choose either 'gpt-4' or 'gpt-3.5'.")

    # Retrieve the costs for the selected model
    input_cost_per_1k = pricing[model_name]['input_cost_per_1k']
    output_cost_per_1k = pricing[model_name]['output_cost_per_1k']

    # Calculate the costs for input and output separately
    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k

    # Sum the input and output costs to get the total cost
    total_cost = input_cost + output_cost

    return total_cost

def validate_and_retry(client, messages, model, expected_keys, max_attempts=3):
    """
    Attempts to generate and validate content based on the expected structure and elements.

    Parameters:
    - client: The client object used to interact with a content generation service.
    - messages: The messages or prompts used to generate content.
    - model: The model specified for generating content.
    - expected_keys: A set of keys expected to be present in the generated content.
    - max_attempts: The maximum number of attempts to generate valid content (default is 3).

    The function attempts to generate content up to a specified number of times. It validates the generated content
    by checking for the presence of expected keys and a correctly formatted product highlight in the introduction.
    If the validation fails, it retries until the maximum number of attempts is reached.

    Returns:
    - json_output: The raw JSON output from the last successful generation attempt.
    - info: The parsed JSON content as a dictionary.

    Raises:
    - ValueError: If the maximum number of attempts is reached and valid content is not generated.
    """

    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON
            json_output = generate_content(client, messages, model=model)
            info = json.loads(json_output)

            # Check if all expected keys are present
            if not all(key in info for key in expected_keys):
                missing_keys = expected_keys - info.keys()
                print(f"Missing keys: {missing_keys}. Retrying ({attempt + 1}/{max_attempts})...")
                continue

            # Validate the highlighted product in the introduction
            intro = info.get('introduction', '')
            if intro.count('*') == 2 and intro.find('*') < intro.rfind('*'):
                # Ensure the highlighted text is reasonable (e.g., not the entire introduction)
                start, end = intro.find('*'), intro.rfind('*')
                if 0 < end - start - 1 <= len(intro) / 2:
                    return json_output, info
                else:
                    print("Highlighted product format is incorrect or too long. Retrying...")
            else:
                print("Missing or incorrect product highlight in introduction. Retrying...")

        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")

    # Raise an error if all attempts fail
    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def validate_and_retry_dynamic(client, messages, model, min_features, max_attempts=3, show=False):
    """
    Attempts to dynamically generate and validate content based on the expected structure, elements, and a minimum number of features.

    Parameters:
    - client: The client object used to interact with a content generation service.
    - messages: The messages or prompts used to generate content.
    - model: The model specified for generating content.
    - min_features: The minimum number of features/benefits required in the generated content.
    - max_attempts: The maximum number of attempts to generate valid content (default is 3).
    - show: A boolean indicating whether to print the generated content for debugging (default is False).

    The function tries to generate content up to a specified number of times, validating the generated content
    by checking for the presence of a specific subheader ('subheader_2') and ensuring there is a minimum number of features/benefits
    that match with their corresponding content. If the validation fails, it retries until the maximum number of attempts is reached.

    Returns:
    - json_output: The raw JSON output from the last successful generation attempt.
    - info: The parsed JSON content as a dictionary.

    Raises:
    - ValueError: If the maximum number of attempts is reached and valid content is not generated.
    """

    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON
            json_output = generate_content(client, messages, model=model)
            info = json.loads(json_output)
            if show:
                print(info)  # Print the generated content if 'show' is True

            # Validate the presence of 'subheader_2'
            if "subheader_2" not in info:
                print("Missing 'subheader_2'. Retrying...")
                continue

            # Initialize counters for feature/benefit and content
            feature_count = 0
            content_count = 0

            # Iterate over keys to count features/benefits and content
            for key in info:
                if "tittel_" in key and not key.startswith("innhold_"):
                    feature_count += 1
                elif key.startswith("innhold_"):
                    content_count += 1

            # Check if the number of features/benefits and content match and meet the minimum requirement
            if feature_count != content_count or feature_count < min_features or content_count < min_features:
                print(f"Mismatch or insufficient features and content. Features: {feature_count}, Contents: {content_count}. Retrying...")
                continue

            return json_output, info  # Return both raw JSON and parsed information

        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")

    # Raise an error if all attempts fail
    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def validate_and_retry_guide(client, messages, model, min_steps, max_attempts=3, show=False):
    """
    Attempts to dynamically generate and validate guide content based on the expected structure, 
    elements, and a minimum number of steps.

    Parameters:
    - client: The client object used to interact with a content generation service.
    - messages: The messages or prompts used to generate content.
    - model: The model specified for generating content.
    - min_steps: The minimum number of guide steps required in the generated content.
    - max_attempts: The maximum number of attempts to generate valid content (default is 3).
    - show: A boolean indicating whether to print the generated content for debugging (default is False).

    The function tries to generate content up to a specified number of times, validating the generated content
    by checking for the presence of required keys ('subheader_3', 'subheader_3_message') and ensuring there is a minimum number of guide steps
    that match with their corresponding content. If the validation fails, it retries until the maximum number of attempts is reached.

    Returns:
    - json_output: The raw JSON output from the last successful generation attempt.
    - info: The parsed JSON content as a dictionary.

    Raises:
    - ValueError: If the maximum number of attempts is reached and valid content is not generated.
    """

    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON
            json_output = generate_content(client, messages, model=model)
            info = json.loads(json_output)
            if show:
                print(info)  # Print the generated content if 'show' is True

            # Validate the basic structure by checking the presence of required keys
            required_keys = {"subheader_3", "subheader_3_message"}
            if not all(key in info for key in required_keys):
                missing_keys = required_keys - info.keys()
                print(f"Missing keys: {missing_keys}. Retrying...")
                continue

            # Check the dynamic number of guide steps and their corresponding content
            step_keys = [key for key in info if key.startswith("guide_step_") and not key.endswith("_content")]
            step_content_keys = [key for key in info if key.startswith("guide_step_") and key.endswith("_content")]

            # Validate the count of steps and contents match and meet the minimum requirement
            if len(step_keys) != len(step_content_keys):
                print(f"Mismatch in step and content count. Steps: {len(step_keys)}, Contents: {len(step_content_keys)}. Retrying...")
                continue

            step_count = len(step_keys)
            if not (min_steps <= step_count):
                print(f"Incorrect number of guide steps: {step_count}. Retrying...")
                continue

            return json_output, info  # Return both raw JSON and parsed information

        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")

    # Raise an error if all attempts fail
    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def make_product_link(text, url, product):
    """
    Replaces a product name enclosed in asterisks within a given text with a clickable HTML link that has specific inline styles.

    Parameters:
    - text (str): The text where the product name is to be replaced. It should contain the product name enclosed in asterisks, like *productName*.
    - url (str): The URL to which the link should redirect. This is the href value for the generated anchor tag.
    - product (str): The exact product name expected to be enclosed in asterisks within the text. This helps ensure only the specific product name is replaced.

    Returns:
    - str: The modified text with the product name replaced by a clickable link with inline styles. If the product name enclosed in asterisks isn't found, the original text is returned unchanged.

    Description:
    The function searches for the product name enclosed in asterisks (e.g., *productName*) in the provided text. If found, it replaces this with an HTML anchor (<a>) tag that links to the provided URL and applies inline styles to make the product name stand out as a clickable link in the HTML view. The inline styles include a specified color, bold font weight, and underline text decoration. This method is particularly useful for ensuring the link is styled consistently and prominently, regardless of external CSS.

    Example:
    text = "Discover our innovative *SuperWidget* today!"
    url = "http://example.com/superwidget"
    product = "SuperWidget"
    make_product_link(text, url, product)
    # Output: 'Discover our innovative <a href="http://example.com/superwidget" style="color: #007bff; font-weight: bold; text-decoration: underline;">SuperWidget</a> today!'

    Note:
    The color for the link is defined within the function as a bright blue (#007bff), but you can customize this color by changing the 'link_color' variable.
    """

    # Find the product name enclosed in asterisks
    product_match = re.search(r'\*([^*]+)\*', text)
    if product_match:
        # Extract the product name
        product_name = product_match.group(1)
        # Define the color you want for the product link
        link_color = '#007bff'  # Bright blue, but you can choose any color
        # Replace the name with an anchor tag and inline style for color
        return text.replace(f"*{product}*", f'<a href="{url}" style="color: {link_color}; font-weight: bold; text-decoration: underline;">{product_name}</a>')
    return text  # Return the original text if no product name is found

def validate_store_url(url):
    """
    Validates the store URL provided by the user with intense checks.

    Parameters:
    - url: The store URL to be validated.

    Returns:
    - The validated URL if it's correct or raises a ValueError with an appropriate message.
    """

    # Normalize and strip leading/trailing whitespaces from the URL
    url = url.strip()

    # Check if the URL is well-formed
    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError("The provided URL is malformed. Please provide a valid URL.")

    # Check if the URL uses a valid scheme (http or https)
    if parsed_url.scheme not in ['http', 'https']:
        raise ValueError("The provided URL must start with 'http://' or 'https://'.")

    # Remove multiple slashes and backslashes except for protocol part
    url = parsed_url.scheme + '://' + re.sub(r'[/\\]+', '/', parsed_url.netloc + parsed_url.path)

    # Check for common typos and mistakes in domain names
    if '..' in url or '//' in url[8:]:  # excluding the '//' in 'http://'
        raise ValueError("The provided URL contains invalid characters or sequence of characters.")

    # Ensure URL ends with a single "/"
    if not url.endswith('/'):
        url += '/'

    # Add more checks here if necessary (e.g., domain name validation, checking against a list of valid domains, etc.)

    return url

def create_article(admin_store_url, blog_id, access_token, new_title, img_url, img_alt, tags, html_content, author):
    """
    Creates an article with an image in a specified blog on the Shopify store using the Shopify Admin API.

    This function makes an HTTP POST request to the Shopify API's article endpoint for a specific blog. It creates a new article with the given details including title, author, tags, image, and HTML content.

    Parameters:
    - admin_store_url (str): The base URL of the admin store, e.g., 'https://example.myshopify.com'.
    - blog_id (str): The ID of the blog where the article will be created.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - new_title (str): The title of the new article.
    - img_url (str): The source URL for the image associated with the article.
    - img_alt (str): The alternative text for the image.
    - tags (str): A string of comma-separated tags for the article.
    - html_content (str): The HTML content of the article.
    - author (str): The name of the author for the new article.

    The function sends a POST request to the Shopify API to create an article with the given details. If the article
    is created successfully, it prints a success message. If there's an error, it prints an error message with details.

    Returns:
    - None: This function doesn't return anything. It prints messages to indicate the success or failure of the operation.

    Raises:
    - Exception: If the request fails or the response status is not 201, it raises an exception with the error code and text.
    """
    
    # Construct the URL for the API endpoint
    url = f"{admin_store_url}/admin/api/2023-10/blogs/{blog_id}/articles.json"

    # Set the headers for the request
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    # Prepare the data to be sent in the request
    data = json.dumps({
        "article": {
            "title": new_title,
            "author": author,  # Set the author name
            "tags": tags,
            'image': {"src": img_url, "alt": img_alt},  # Include the image details
            "body_html": html_content
        }
    })

    # Make the POST request to create the article
    response = requests.post(url, headers=headers, data=data)

    # Check the response status and print the appropriate message
    if response.status_code == 201:
        print("Article created successfully!")
    else:
        # Raises an exception if something goes wrong
        raise Exception(f"Error creating article: {response.status_code}, {response.text}")

def delete_article(store_url, access_token, blog_id, article_id):
    """
    Deletes an article from a specified blog on the Shopify store using the Shopify Admin API.

    This function makes an HTTP DELETE request to the Shopify API's article endpoint for a specific article in a blog. It removes the specified article if it exists.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - blog_id (str): The ID of the blog from which the article will be deleted.
    - article_id (str): The ID of the article to delete.

    The function sends a DELETE request to the Shopify API to remove an article with the specified ID. If the article
    is deleted successfully, it prints a success message. If there's an error, it raises an exception with details.

    Returns:
    - None: This function doesn't return anything. It prints a message to indicate the success of the operation or raises an exception in case of failure.

    Raises:
    - Exception: If the request fails or the response status is not 200, it raises an exception with the error code and text.
    """
    
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    response = requests.delete(f"{store_url}/admin/api/2023-10/blogs/{blog_id}/articles/{article_id}.json", headers=headers)
    
    # Check the response status and print the appropriate message
    if response.status_code == 200:
        print("Article deleted successfully!")  # Inform the user of success
    else:
        # Raises an exception if something goes wrong
        raise Exception(f"Error: {response.status_code}, {response.text}")

def get_specific_article(store_url, access_token, blog_id, article_id):
    """
    Retrieves a specific article from a Shopify blog based on the article ID.

    Args:
    - store_url (str): The URL of the Shopify store.
    - access_token (str): The access token for authenticating with the Shopify API.
    - blog_id (int): The ID of the blog that contains the article.
    - article_id (int): The ID of the article to retrieve.

    Returns:
    - dict: A dictionary containing the JSON response with the article details if the request is successful.

    Raises:
    - Exception: If the request to the Shopify API fails, an exception is raised with the error code and message.

    Example usage:
    article = get_specific_article('https://example.myshopify.com', 'your-access-token', 241253187, 134645308)
    """

    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    url = f"{store_url}/admin/api/2024-01/blogs/{blog_id}/articles/{article_id}.json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Returns the article details
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")  # Raises an exception if something goes wrong

def get_articles(store_url, access_token, blog_id):
    """
    Retrieves the list of articles from a specified blog on the Shopify store using the Shopify Admin API.

    This function makes an HTTP GET request to the Shopify API's article endpoint for a specific blog. It fetches the list of all articles within that blog.

    Parameters:
    - store_url (str): The base URL of the Shopify store, e.g., 'https://example.myshopify.com'.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - blog_id (str): The ID of the blog for which to retrieve the list of articles.

    The function sends a GET request to the Shopify API to retrieve all articles for the specified blog ID. If the request
    is successful, it returns the list of articles. If there's an error, it raises an exception with details.

    Returns:
    - dict: A dictionary object containing the response data with the list of articles if successful.

    Raises:
    - Exception: If the request fails or the response status is not 200, it raises an exception with the error code and text.
    """
    
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    response = requests.get(f"{store_url}/admin/api/2023-10/blogs/{blog_id}/articles.json", headers=headers)
    
    # Check the response status and return the list of articles or raise an exception
    if response.status_code == 200:
        return response.json()  # Returns the list of articles
    else:
        # Raises an exception if something goes wrong
        raise Exception(f"Error: {response.status_code}, {response.text}")

def count_articles_in_blog(store_url, access_token, blog_id):
    """
    Counts the number of articles in a specific blog on a Shopify store.

    Args:
    - store_url (str): The URL of the Shopify store.
    - access_token (str): The access token for authenticating with the Shopify API.
    - blog_id (int): The ID of the blog for which the article count is required.

    Returns:
    - dict: A dictionary containing the JSON response with the count of articles if the request is successful.

    Raises:
    - Exception: If the request to the Shopify API fails, an exception is raised with the error code and message.

    Example usage:
    article_count = count_articles_in_blog('https://example.myshopify.com', 'your-access-token', 241253187)
    """

    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    url = f"{store_url}/admin/api/2024-01/blogs/{blog_id}/articles/count.json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Returns the count of articles
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")  # Raises an exception if something goes wrong

def create_or_replace_article_(admin_store_url, blog_id, access_token, new_title, img_url, img_alt, tags, html_content, author, article_handle):
    """
    Creates a new article or replaces an existing one with the same handle in a specified blog on the Shopify store.

    This function first checks if an article with the provided handle already exists in the specified blog. If it does,
    the existing article is deleted. Then, a new article with the provided details is created.

    Parameters:
    - admin_store_url (str): The base URL of the admin store, e.g., 'https://example.myshopify.com'.
    - blog_id (str): The ID of the blog where the article will be created or replaced.
    - access_token (str): The access token used for authenticating with the Shopify API.
    - new_title (str): The title of the new article.
    - img_url (str): The source URL for the image associated with the article.
    - img_alt (str): The alternative text for the image.
    - tags (str): A string of comma-separated tags for the article.
    - html_content (str): The HTML content of the article.
    - author (str): The name of the author for the new article.
    - article_handle (str): The handle of the article to check and replace.

    The function first retrieves all articles from the specified blog. If an article with the given handle exists,
    it is deleted. Finally, a new article is created with the provided details.

    Returns:
    - None: This function doesn't return anything. It performs operations to delete and/or create articles.
    """
    
    # Retrieve the list of articles from the blog
    articles = get_articles(admin_store_url, access_token, blog_id)
    
    # Check if any article matches the handle provided
    for article in articles.get('articles', []):
        if article['handle'] == article_handle:
            print(f"Article with handle '{article_handle}' exists. Deleting...")
            delete_article(admin_store_url, access_token, blog_id, article['id'])  # Delete the existing article
            break  # Exit the loop as we've found and deleted the article
    
    # Create the new article
    create_article_(admin_store_url, blog_id, access_token, new_title, img_url, img_alt, tags, html_content, author)

def get_articles_by_published_date(store_url, access_token, blog_id, max_date, limit):
    """
    Retrieves a list of articles from a specific Shopify blog that were published before a specified date.

    Args:
    - store_url (str): The URL of the Shopify store.
    - access_token (str): The access token for authenticating with the Shopify API.
    - blog_id (int): The ID of the blog from which to retrieve articles.
    - max_date (str): The maximum publication date for articles to retrieve. Articles published after this date will not be included. The date should be in ISO 8601 format (e.g., '2024-01-10T10:00:00-05:00').
    - limit (int): The maximum number of articles to retrieve.

    Returns:
    - dict: A dictionary containing the JSON response with the list of articles if the request is successful.

    Raises:
    - Exception: If the request to the Shopify API fails, an exception is raised with the error code and message.

    Example usage:
    articles = get_articles_by_published_date('https://example.myshopify.com', 'your-access-token', 123, '2024-01-10T10:00:00-05:00', 10)
    """

    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    response = requests.get(f"{store_url}/admin/api/2023-10/blogs/{blog_id}/articles.json?limit={limit}&published_at_max={max_date}", headers=headers)
    if response.status_code == 200:
        return response.json()  # Returns the list of articles
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")  # Raises an exception if something goes wrong

def get_all_articles_improved(store_url, access_token, blog_id, initial_max_date, direction='backward'):
    """
    Retrieves all articles from a Shopify blog in a specified direction relative to an initial date.

    This function fetches articles in batches, avoiding duplicates and ensuring only unique articles are considered.
    It continues fetching articles until no more are found in the specified direction.

    Parameters:
    - store_url (str): The base URL of the Shopify store.
    - access_token (str): The access token for authentication with the Shopify API.
    - blog_id (str): The ID of the blog from which to fetch articles.
    - initial_max_date (str): The ISO 8601 formatted date from which to start fetching articles.
      For 'backward', articles before this date are fetched; for 'forward', articles after this date.
    - direction (str): The direction to fetch articles, either 'backward' or 'forward'.
      Default is 'backward'.

    Returns:
    - all_articles (list): A list of unique articles fetched from the Shopify store.

    Raises:
    - Exception: If the request to Shopify API fails.

    Note:
    - This function requires the 'requests' library. Install it via 'pip install requests' if necessary.
    - Ensure that 'access_token' and 'store_url' are correct to avoid unauthorized errors.
    - Adjust the 'sleep' duration if you encounter rate-limiting issues with the Shopify API.
    """
    
    all_articles = []  # To hold all the fetched articles
    article_ids = set()  # To track the IDs of articles already added to avoid duplicates
    max_date = initial_max_date  # The initial date to start fetching articles from
    limit = 250  # Shopify's limit for the number of articles per request
    last_article_id = None  # To track the ID of the last article fetched in the previous batch

    while True:
        # Fetch a batch of articles from Shopify
        batch = get_articles_by_published_date(store_url, access_token, blog_id, max_date, limit)
        articles = batch.get('articles', [])

        # If no articles were returned or the last article is the same as before, stop fetching
        if not articles or (last_article_id == articles[-1]['id']):
            break

        # Add each new article to the all_articles list and its ID to the article_ids set
        for article in articles:
            article_id = article['id']
            if article_id not in article_ids:
                all_articles.append(article)
                article_ids.add(article_id)

        # Update the last_article_id and max_date for the next batch fetch
        last_article_id = articles[-1]['id']
        last_article_date = articles[-1]['published_at']
        last_article_datetime = datetime.strptime(last_article_date, '%Y-%m-%dT%H:%M:%S%z')
        if direction == 'backward':
            max_date = (last_article_datetime - timedelta(seconds=1)).isoformat()
        elif direction == 'forward':
            max_date = (last_article_datetime + timedelta(seconds=1)).isoformat()

        print(len(all_articles))  # Print the number of articles fetched so far
        sleep(1)  # Sleep to avoid hitting the rate limit of the Shopify API

    return all_articles

def get_all_articles_combined(store_url, access_token, blog_id, initial_max_date):
    """
    Retrieves all unique articles from a Shopify blog by fetching articles in both forward and backward directions
    relative to an initial date. It avoids duplicates and ensures each article is counted only once.

    Parameters:
    - store_url (str): The base URL of the Shopify store.
    - access_token (str): The access token for authentication with the Shopify API.
    - blog_id (str): The ID of the blog from which to fetch articles.
    - initial_max_date (str): The ISO 8601 formatted date from which to start fetching articles in both directions.

    Returns:
    - all_articles (list): A list of unique articles fetched from the Shopify store.

    Raises:
    - Exception: If the request to Shopify API fails.

    Note:
    - This function requires the 'requests' library. Install it via 'pip install requests' if necessary.
    - Ensure that 'access_token' and 'store_url' are correct to avoid unauthorized errors.
    - The 'sleep' function is used to avoid hitting the rate limit of the Shopify API. Adjust as necessary.
    """
    
    all_articles = []  # To hold all the fetched articles
    article_ids = set()  # To track the IDs of articles already added to avoid duplicates
    max_date_backward = initial_max_date  # The initial date to start fetching articles backward from
    max_date_forward = initial_max_date  # The initial date to start fetching articles forward from
    limit = 250  # Shopify's limit for the number of articles per request
    last_article_id_backward = None  # To track the ID of the last article fetched in the backward direction
    last_article_id_forward = None  # To track the ID of the last article fetched in the forward direction

    while True:
        # Fetch a batch of articles in the backward direction from Shopify
        batch_backward = get_articles_by_published_date(store_url, access_token, blog_id, max_date_backward, limit)
        articles_backward = batch_backward.get('articles', [])
        sleep(1)  # Sleep to avoid hitting the rate limit

        # Fetch a batch of articles in the forward direction from Shopify
        batch_forward = get_articles_by_published_date(store_url, access_token, blog_id, max_date_forward, limit)
        articles_forward = batch_forward.get('articles', [])
        sleep(1)  # Sleep to avoid hitting the rate limit

        # If no more articles are returned in both directions, stop fetching
        if (not articles_backward or last_article_id_backward == articles_backward[-1]['id']) and \
           (not articles_forward or last_article_id_forward == articles_forward[-1]['id']):
            break

        # Add each new article from the backward batch to the all_articles list and its ID to the article_ids set
        for article in articles_backward:
            article_id = article['id']
            if article_id not in article_ids:
                all_articles.append(article)
                article_ids.add(article_id)

        # Add each new article from the forward batch to the all_articles list and its ID to the article_ids set
        for article in articles_forward:
            article_id = article['id']
            if article_id not in article_ids:
                all_articles.append(article)
                article_ids.add(article_id)

        # Update the last_article_ids and max_dates for both directions
        if articles_backward:
            last_article_id_backward = articles_backward[-1]['id']
            last_backward_date = datetime.strptime(articles_backward[-1]['published_at'], '%Y-%m-%dT%H:%M:%S%z')
            max_date_backward = (last_backward_date - timedelta(seconds=1)).isoformat()

        if articles_forward:
            last_article_id_forward = articles_forward[-1]['id']
            last_forward_date = datetime.strptime(articles_forward[-1]['published_at'], '%Y-%m-%dT%H:%M:%S%z')
            max_date_forward = (last_forward_date + timedelta(seconds=1)).isoformat()

        print(len(all_articles))  # Print the number of unique articles fetched so far

    return all_articles

def update_shopify_article(store_url, access_token, blog_id, article_id, title, author, tags, body_html, published_at):
    """
    Updates an article in a Shopify store.

    Parameters:
    - store_url (str): The base URL of the Shopify store.
    - access_token (str): The access token for authentication with the Shopify API.
    - blog_id (str): The ID of the blog containing the article.
    - article_id (str): The ID of the article to update.
    - title (str): The new title of the article.
    - author (str): The author of the article.
    - tags (str): Comma-separated tags for the article.
    - body_html (str): The HTML content of the article.
    - published_at (str): The publication date and time in UTC (e.g., "Thu Mar 24 15:45:47 UTC 2011").

    Returns:
    - response (dict): The JSON response from the API which includes the updated article details.

    Raises:
    - Exception: If the request to Shopify API fails.
    """

    url = f"{store_url}/admin/api/2023-10/blogs/{blog_id}/articles/{article_id}.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "article": {
            "id": article_id,
            "title": title,
            "author": author,
            "tags": tags,
            "body_html": body_html,
            "published_at": published_at
        }
    }

    # Send the PUT request
    response = requests.put(url, headers=headers, data=json.dumps(data))

    # Check if the request was successful
    if response.status_code == 200:
        # Return the JSON response if the request was successful
        return response.json()
    else:
        # Raise an exception if something went wrong
        raise Exception(f"Error: {response.status_code}, {response.text}")

