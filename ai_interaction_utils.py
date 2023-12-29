import tiktoken
from openai import OpenAI

def generate_content(prompt):
    """
    Generates content based on a specific aspect of the product or any given prompt.

    Parameters:
    - prompt: A string containing the text you want the AI to respond to.

    Returns:
    - A string containing the AI-generated response to the prompt.

    The function communicates with an AI model using the OpenAI API to generate a
    response based on the provided prompt. It utilizes a specific model and settings
    to tailor the response's creativity and format.
    """
    # Send the prompt to the AI and get a completion
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],  # The prompt from the user
        temperature=0.9,  # Controls the randomness of the output
        model="gpt-3.5-turbo-1106",  # Specifies the AI model used
        response_format={"type": "json_object"},  # Sets the format of the response
    )
    # Return the content of the AI's response
    return chat_completion.choices[0].message['content']

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
