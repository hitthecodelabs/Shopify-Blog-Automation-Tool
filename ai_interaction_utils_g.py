import json

import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.preview.generative_models import GenerativeModel

def generate_content(model_name, prompt, show_output=False, show_tokens=False):
    """
    Generates content using Google's AI models (Bison, Unicorn, Gemini).

    Parameters:
    - model_name: (str) The name of the model to use ('bison', 'unicorn', 'gemini').
    - prompt: (str) The input text to generate content for.
    - show_output: (bool, optional) If True, print the generated content. Default is False.
    - show_tokens: (bool, optional) If True, print the token counts. Default is False.

    Returns:
    - output: (str) The generated content from the model.
    """
    
    # Initialize a generic model to calculate tokens for all models
    g_model = GenerativeModel("gemini-pro")
    
    # Depending on the model, initialize the appropriate client and set parameters
    if model_name == 'bison':
        parameters = {"candidate_count": 1, "max_output_tokens": 2048 , "temperature": 1, "top_k": 40}
        model = TextGenerationModel.from_pretrained("text-bison@002")
    elif model_name == 'unicorn':
        parameters = {"candidate_count": 1, "max_output_tokens": 1024, "temperature": 1, "top_k": 40}
        model = TextGenerationModel.from_pretrained("text-unicorn@001")
    elif model_name == 'gemini':
        parameters = {"max_output_tokens": 8192, "temperature": 0.9, "top_p": 1}
        model = GenerativeModel("gemini-pro")
    else:
        # Throw an error if an unrecognized model name is provided
        raise ValueError("Model not recognized")

    # Generate response based on the model
    if model_name in ['bison', 'unicorn']:
        # Generate text and capture the response for Bison and Unicorn
        response = model.predict(prompt, **parameters)
        output = response.text[1:]  # Adjust based on actual response format
        
        # Calculate token counts for input and output
        input_tokens = g_model.count_tokens(prompt).total_tokens
        output_tokens = g_model.count_tokens(output).total_tokens
        d = {"input_tokens":input_tokens, 
             "output_tokens":output_tokens, 
             "total_tokens":input_tokens+output_tokens}
        
    elif model_name in ['gemini']:
        # Generate content specifically for Gemini
        gemini_response = model.generate_content(prompt, generation_config=parameters)
        tokens = gemini_response._raw_response.usage_metadata
        d = {"input_tokens":tokens.prompt_token_count, 
             "output_tokens":tokens.candidates_token_count, 
             "total_tokens":tokens.total_token_count}
        output = gemini_response.text  # Adjust based on actual response format

    # Print token count information if requested
    if show_tokens:
        print(d)

    # Print the output text if requested
    if show_output:
        print(output)

    # Return the generated content
    return output
