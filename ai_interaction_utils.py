import re
import json
import requests
import tiktoken
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

def calculate_pricing(input_tokens, output_tokens, input_cost_per_1k=0.01, output_cost_per_1k=0.03):
    """
    Calculate the pricing for using an AI model based on the number of input and output tokens.

    Parameters:
    - input_tokens (int): The number of tokens in the input.
    - output_tokens (int): The number of tokens in the output.
    - input_cost_per_1k (float): Cost per 1,000 input tokens (default is 0.01 cents).
    - output_cost_per_1k (float): Cost per 1,000 output tokens (default is 0.03 cents).

    Returns:
    - float: The total cost of the operation.

    This function calculates the total cost by considering separate costs for input and
    output tokens, which allows for a detailed understanding of the expense associated
    with the model's usage.
    """
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

def create_article(admin_store_url, blog_id, access_token, new_title, tags, html_content, author):
    """
    Creates an article in a specified blog on Shopify.

    Parameters:
    - admin_store_url: The base URL of the admin store.
    - blog_id: The ID of the blog where the article will be created.
    - access_token: The access token for Shopify API authentication.
    - new_title: The title of the new article.
    - tags: A string of comma-separated tags for the article.
    - html_content: The HTML content of the article.

    The function makes a POST request to the Shopify API to create an article with the given details.
    It prints a success message if the article is created successfully or an error message otherwise.
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
            "author": author,
            "tags": tags,
            "body_html": html_content
        }
    })

    # Make the POST request to create the article
    response = requests.post(url, headers=headers, data=data)

    # Check the response status and print the appropriate message
    if response.status_code == 201:
        print("Article created successfully!")
    else:
        print("Error creating article:", response.status_code, response.text)

def create_article(admin_store_url, blog_id, access_token, new_title, tags, html_content, author):
    """
    Creates an article in a specified blog on Shopify.

    Parameters:
    - admin_store_url: The base URL of the admin store.
    - blog_id: The ID of the blog where the article will be created.
    - access_token: The access token for Shopify API authentication.
    - new_title: The title of the new article.
    - tags: A string of comma-separated tags for the article.
    - html_content: The HTML content of the article.
    - author: The name of the author for the new article.

    The function makes a POST request to the Shopify API to create an article with the given details.
    It prints a success message if the article is created successfully or an error message otherwise.
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
            "body_html": html_content
        }
    })

    # Make the POST request to create the article
    response = requests.post(url, headers=headers, data=data)

    # Check the response status and print the appropriate message
    if response.status_code == 201:
        print("Article created successfully!")
    else:
        print("Error creating article:", response.status_code, response.text)
