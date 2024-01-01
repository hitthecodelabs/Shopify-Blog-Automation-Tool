import re
import json
import tiktoken
from openai import OpenAI

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
    Attempts to generate content using the OpenAI API and validates the resulting JSON structure.
    It retries the content generation up to a specified number of attempts if the JSON is not valid
    or the expected keys are missing.

    Parameters:
    - client: The OpenAI API client instance to use for making requests.
    - messages: A list of message dicts representing the conversation history for the API request.
    - model: The identifier of the model to use for the chat completion.
    - expected_keys: A set of strings representing the keys expected to be in the JSON response.
    - max_attempts: The maximum number of attempts to make (default is 3).

    Returns:
    - json_output: The raw JSON output from the API if successful.
    - info: The parsed JSON data as a Python dictionary if successful.

    The function first attempts to generate content using the provided client, messages, and model.
    It then checks whether the generated content is valid JSON and contains all the expected keys.
    If the JSON is invalid or keys are missing, it retries the generation and validation process up
    to the maximum number of attempts specified. If it fails after all attempts, it raises a ValueError.

    Exceptions:
    - ValueError: Raised when the maximum number of attempts is reached without successful validation.
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

            # Validate the 'introduction' for the highlighted product
            introduction = info.get("introduction", "")
            if not re.search(r"\*\*[^*]+\*\*", introduction):
                print(f"The product is not properly highlighted in 'introduction'. Retrying ({attempt + 1}/{max_attempts})...")
                continue

            return json_output, info  # All validations passed

        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")

    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def validate_and_retry_dynamic(client, messages, model, min_features, max_attempts=3):
    """
    Attempts to generate content dynamically using the OpenAI API and validates the resulting JSON
    structure, focusing on ensuring a minimum number of features/benefits. It retries the content
    generation up to a specified number of attempts if the JSON is not valid or if the feature/benefit
    count is below the minimum required.

    Parameters:
    - client: The OpenAI API client instance to use for making requests.
    - messages: A list of message dicts representing the conversation history for the API request.
    - model: The identifier of the model to use for the chat completion.
    - min_features: The minimum number of feature/benefit pairs expected in the response.
    - max_attempts: The maximum number of attempts to make (default is 3).

    Returns:
    - json_output: The raw JSON output from the API if successful.
    - info: The parsed JSON data as a Python dictionary if successful.

    The function first attempts to generate content using the provided client, messages, and model.
    It then checks whether the generated content is valid JSON and contains a minimum number of
    features/benefits, each paired with corresponding content. If the JSON is invalid, or the feature/benefit
    count is insufficient, it retries the generation and validation process up to the maximum number of
    attempts specified. If it fails after all attempts, it raises a ValueError.

    Exceptions:
    - ValueError: Raised when the maximum number of attempts is reached without successful validation.
    """
    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON.
            json_output = generate_content(client, messages, model=model)
            info = json.loads(json_output)
            
            # Validate the presence of 'subheader_2' in the JSON.
            if "subheader_2" not in info:
                print("Missing 'subheader_2'. Retrying...")
                continue

            # Identify and count the feature and content keys.
            feature_keys = [key for key in info if key.startswith("feature/benefit") and not key.endswith("content")]
            feature_content_keys = [key for key in info if key.startswith("feature/benefit") and key.endswith("content")]
            
            # Check for a mismatch between feature titles and their content.
            if len(feature_keys) != len(feature_content_keys):
                print(f"Mismatch in feature and content count. Features: {len(feature_keys)}, Contents: {len(feature_content_keys)}. Retrying...")
                continue

            # Validate the number of features/benefits against the minimum required.
            feature_count = len(feature_keys)
            if not (min_features <= feature_count):
                print(f"Incorrect number of features/benefits: {feature_count}. Retrying...")
                continue
            
            # If validation passes, return the raw JSON and the parsed information.
            return json_output, info
            
        except json.JSONDecodeError:
            # If JSON decoding fails, print an error message and retry.
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")
    
    # If all attempts fail, raise an error indicating the failure.
    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def validate_and_retry_guide(client, messages, model, min_steps, max_attempts=3):
    """
    Attempts to generate content dynamically using the OpenAI API and validates the resulting JSON
    structure, focusing on ensuring a minimum number of guide steps. It retries the content
    generation up to a specified number of attempts if the JSON is not valid or if the guide step
    count is below the minimum required.

    Parameters:
    - client: The OpenAI API client instance to use for making requests.
    - messages: A list of message dicts representing the conversation history for the API request.
    - model: The identifier of the model to use for the chat completion.
    - min_steps: The minimum number of guide steps expected in the response.
    - max_attempts: The maximum number of attempts to make (default is 3).

    Returns:
    - json_output: The raw JSON output from the API if successful.
    - info: The parsed JSON data as a Python dictionary if successful.

    The function first attempts to generate content using the provided client, messages, and model.
    It then checks whether the generated content is valid JSON and contains a minimum number of
    guide steps, each paired with corresponding content. If the JSON is invalid, or the guide step
    count is insufficient, it retries the generation and validation process up to the maximum number of
    attempts specified. If it fails after all attempts, it raises a ValueError.

    Exceptions:
    - ValueError: Raised when the maximum number of attempts is reached without successful validation.
    """
    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON.
            json_output = generate_content(client, messages, model=model)
            info = json.loads(json_output)
            
            # Validate the presence of required keys in the JSON.
            required_keys = {"subheader_3", "subheader_3_message", "Konklusjon", "final_sentence"}
            if not all(key in info for key in required_keys):
                missing_keys = required_keys - info.keys()
                print(f"Missing keys: {missing_keys}. Retrying...")
                continue

            # Identify and count the guide step and content keys.
            step_keys = [key for key in info if key.startswith("guide_step_") and not key.endswith("_content")]
            step_content_keys = [key for key in info if key.startswith("guide_step_") and key.endswith("_content")]
            
            # Check for a mismatch between guide step titles and their content.
            if len(step_keys) != len(step_content_keys):
                print(f"Mismatch in step and content count. Steps: {len(step_keys)}, Contents: {len(step_content_keys)}. Retrying...")
                continue

            # Validate the number of guide steps against the minimum required.
            step_count = len(step_keys)
            if not (min_steps <= step_count):
                print(f"Incorrect number of guide steps: {step_count}. Retrying...")
                continue
            
            # If validation passes, return the raw JSON and the parsed information.
            return json_output, info
            
        except json.JSONDecodeError:
            # If JSON decoding fails, print an error message and retry.
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")
    
    # If all attempts fail, raise an error indicating the failure.
    raise ValueError("Maximum attempts reached. Failed to generate valid content.")
