# Shopify Blog Automation Tool

## Description
The Shopify Blog Automation Tool is a comprehensive Flask app designed to streamline and automate the management of blogs and articles within Shopify stores. It harnesses the power of the Shopify Admin API, offering a robust set of functionalities to interact with various blog-related endpoints efficiently. This toolkit simplifies tasks such as article creation, update, deletion, and retrieval, along with validating and formatting content, thereby enhancing productivity and management ease..

Useful References:
- [Shopify API Documentation](https://shopify.dev/)
- [API Rate Limits](https://shopify.dev/docs/api/admin-rest#rate_limits)

## Features
- **Advanced Article Management**: Comprehensive tools for creating, updating, deleting, and retrieving articles, along with dynamic validation and formatting.
- **Efficient Token and Pricing Calculations**: Estimate the usage and cost associated with AI-generated content.
- **Robust URL and Content Validation**: Ensure the integrity and correctness of URLs and content with advanced validation techniques.
- **Bulk Article Retrieval and Management**: Retrieve and manage articles en masse with improved functionality, catering to both forward and backward directions relative to a specific date.

## Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/hitthecodelabs/Shopify-Blog-Automation-Tool.git
cd Shopify-Blog-Automation-Tool
```

## Usage
Before utilizing the scripts, ensure you possess the necessary Shopify API credentials and store details. Configure your environment with the appropriate store URL and access token.

Functions overview:

- `generate_content(client, messages, model)`: Interacts with an OpenAI model to generate responses based on a series of messages.
- `calculate_pricing(input_tokens, output_tokens, model_name)`: Estimates the cost of using an AI model based on the number of input and output tokens.
- `validate_and_retry(client, messages, model, expected_keys)`: Validates the generated content based on expected structure and elements, with retry capability.
- `make_product_link(text, url, product)`: Formats and converts a product name in text into a clickable HTML link.
- `validate_store_url(url)`: Performs intense checks to ensure the store URL's correctness and security.
- `create_or_replace_article_(admin_store_url, blog_id, access_token, ...)`: Creates a new article or replaces an existing one in a specified blog.
- `get_all_articles_combined(store_url, access_token, blog_id, initial_max_date)`: Retrieves all unique articles by fetching in both forward and backward directions relative to a specified date.

Example usage:

```python
from shopify_blog_manager import validate_store_url, create_article

store_url = validate_store_url("https://example.myshopify.com")
access_token = "your_access_token"

# Validate and create a new article
blog_id = "your_blog_id"
title = "Innovative Strategies"
author = "Jean Paul"
tags = "Business, Innovation"
content = "<p>Discover groundbreaking business strategies.</p>"

create_article(store_url, access_token, blog_id, title, author, tags, content)
```

## Contributing
Contributions are welcome! If you'd like to improve the Shopify Blog Automation Tool, please ensure your code adheres to the project's coding standards and includes tests for new features or bug fixes. Submit a pull request with your proposed changes.

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
