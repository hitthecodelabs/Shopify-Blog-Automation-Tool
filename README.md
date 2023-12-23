# Shopify Blog Automation Tool

## Description
The Shopify Blog Automation Tool is a Python script designed to facilitate the automation and management of blogs and articles within a Shopify store. Utilizing the Shopify Admin API, this script offers a convenient way to interact with various blog-related endpoints, enabling tasks such as retrieving blog details, creating blogs with custom metafields, and managing articles.

Useful References:
- [Shopify API Documentation](https://shopify.dev/)
- [API Rate Limits](https://shopify.dev/docs/api/admin-rest#rate_limits)

## Features
- **Retrieve Blog Details**: Fetch all blog entries from your Shopify store.
- **Create Blogs with Metafields**: Enhance blog entries with additional metafield information.
- **Article Management**: Streamline the process of creating and retrieving articles.
- **Count Articles**: Quickly determine the number of articles within a specific blog.

## Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/hitthecodelabs/Shopify-Blog-Automation-Tool.git
cd Shopify-Blog-Automation-Tool
```

## Usage
Ensure you have the necessary Shopify API credentials and store information before running the scripts. Set up your environment with the store URL and access token.

Functions overview:

- `get_blogs(store_url, access_token)`: Retrieves all blogs from the Shopify store.
- `create_blog_with_metafields(store_url, access_token, title, key, value, type, namespace)`: Creates a new blog with specified metafields.
- `create_article(store_url, access_token, blog_id, title, author, tags, body_html)`: Creates a new article in a specified blog.
- `get_articles(store_url, access_token, blog_id)`: Retrieves all articles from a specified blog.
- `get_article_count(store_url, access_token, blog_id)`: Retrieves the count of articles in a specified blog.

Example usage:

```python
from shopify_blog_manager import get_blogs, create_article

store_url = "https://example.myshopify.com"
access_token = "your_access_token"

# List all blogs
print(get_blogs(store_url, access_token))

# Create a new article
blog_id = "your_blog_id"
create_article(store_url, access_token, blog_id, "New Article", "John Doe", "News, Updates", "<p>Content of the article.</p>")
```

## Contributing
Contributions are welcome! If you'd like to improve the Shopify Blog Automation Tool, please ensure your code adheres to the project's coding standards and includes tests for new features or bug fixes. Submit a pull request with your proposed changes.

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
