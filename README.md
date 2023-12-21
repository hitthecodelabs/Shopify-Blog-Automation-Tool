# Shopify-Blog-Automation-Tool

## Description
Shopify Blog Manager is a Python script designed to automate and manage various aspects of blog and article creation in a Shopify store. It simplifies interactions with Shopify's REST API for tasks like retrieving blog details, creating blogs with metafields, and managing articles.

## Features
- Retrieve blog details
- Create new blogs with custom metafields
- Create and manage articles in a Shopify blog
- Count articles in a blog

## Installation

```bash
git clone https://github.com/hitthecodelabs/Shopify-Blog-Automation-Tool.git
cd Shopify-Blog-Manager
```

## Usage
Before running the scripts, ensure that you have the necessary Shopify API credentials and store information. Here's a brief overview of the functions:

- `get_blogs()`: Retrieves all blogs from the Shopify store.
- `create_blog_with_metafields(title, key, value, type, namespace)`: Creates a new blog with specified metafields.
- `create_article(title, author, tags, body_html)`: Creates a new article in a specified blog.
- `get_articles()`: Retrieves all articles from a specified blog.
- `get_article_count()`: Retrieves the count of articles in a specified blog.

Example:
```python
from shopify_blog_manager import get_blogs, create_article

# List all blogs
print(get_blogs())

# Create a new article
create_article("New Article", "John Doe", "News, Updates", "<p>Content of the article.</p>")
```

## Contributing
Contributions to Shopify-Blog-Automation-Tool are welcome. Please ensure that your code adheres to the project's coding standards and include tests for new features or bug fixes.

## License
This project is licensed under the MIT License - see the LICENSE file for details.


