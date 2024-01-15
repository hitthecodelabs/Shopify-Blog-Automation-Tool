import os
import re
import  json
import requests

from time import sleep
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

load_dotenv()

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_shopify_product_count(store_url, access_token):

    # Standardize the shop URL format
    if not store_url.startswith('https://'):
        store_url = 'https://' + store_url

    api_url = f"{store_url}/admin/api/2024-01/products/count.json"
    headers = {'X-Shopify-Access-Token': access_token}

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    try:
        count = response.json().get('count')
        if count is not None:
            return count
        else:
            raise ValueError("Invalid response format: 'count' key not found.")
    except ValueError as e:
        raise Exception(f"Error parsing response: {e}")

def get_shop_info_from_shopify(store_url, access_token):
    """
    Get information about a Shopify store.

    :param store_url: URL of the Shopify store
    :param access_token: The Shopify API access token
    :return: A response object containing the API response
    """
    # Standardize the shop URL format
    if not store_url.startswith('https://'):
        store_url = 'https://' + store_url
    
    # Prepare the URL and headers
    url = f"{store_url}/admin/api/2024-01/shop.json"
    headers = {
        "X-Shopify-Access-Token": access_token
    }

    # Make the GET request and return the JSON response
    return requests.get(url, headers=headers).json()

def get_product_maps_from_shopify(admin_store_url, access_token):
    
    # Standardize the shop URL format
    if not admin_store_url.startswith('https://'):
        admin_store_url = 'https://' + admin_store_url
    
    # Get shop information
    acc_info = get_shop_info_from_shopify(admin_store_url, access_token)

    # Extract domain and construct sitemap URL
    domain = acc_info['shop']['domain']
    sitemap_url = f"https://{domain}/sitemap.xml"

    # Fetch the sitemap
    response = requests.get(sitemap_url)

    # Check response status and process the sitemap
    if response.status_code == 200:
        map_soup = BeautifulSoup(response.text, "lxml-xml")
        product_maps = [i.text for i in map_soup.find_all("loc") if "products" in i.text]
        return product_maps
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")
        
def fetch_and_parse_urls(url_list):
    combined_data = []

    for url in url_list:
        # Fetch the get_all_shopify_products
        response = requests.get(url)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, "lxml-xml")

        # Extract relevant data
        data = [item for item in soup.find_all("url") if len(item.find_all("image")) > 0]
        combined_data.extend(data)

    # Process and structure the extracted data
    data_dict = {
        item.find("image:loc").text.split("?")[0]: [
            item.find("image:loc").text,
            item.find("loc").text,
            item.find("lastmod").text
        ] for item in combined_data
    }

    return data_dict

def get_all_shopify_products(store_url, access_token):
    
    if not store_url.startswith('https://'):
        store_url = 'https://' + store_url
        
    base_url = f"{store_url}/admin/api/2024-01/products.json?limit=250"
    headers = {'X-Shopify-Access-Token': access_token}
    all_products = []

    def get_next_page_link(link_header):
        links = link_header.split(',')
        for link in links:
            if 'rel="next"' in link:
                return link.split(';')[0].strip('<> ')
        return None

    # Initial request
    response = requests.get(base_url, headers=headers)
    while True:
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}, {response.text}")

        # Process response
        data = response.json()
        all_products.extend(data['products'])
        print(len(all_products), end=" | ")

        # Check for next page
        link_header = response.headers.get('Link')
        if link_header:
            next_page_url = get_next_page_link(link_header)
            if next_page_url:
                response = requests.get(next_page_url, headers=headers)
            else:break
        else:break
        sleep(0.4)

    return all_products

def generate_content(client, messages, model='gpt-3.5-turbo-1106', show_output=False, show_tokens=False):
    chat_completion = client.chat.completions.create(
            messages=messages,
            max_tokens=800,
            temperature=0.9,
            model=model,
            response_format={ "type": "json_object" },
        )
    D = chat_completion.model_dump()
    if show_tokens:print(D['usage'])
    json_output = D['choices'][0]['message']['content']
    if show_output:print(json_output)
    return json_output

def validate_and_retry(client, messages, model, expected_keys, max_attempts=3, show_tokens=False):
    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON
            json_output = generate_content(client, messages, model=model, show_tokens=show_tokens)
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

    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def validate_and_retry_dynamic(client, messages, model, min_features, max_attempts=3, show=False, show_tokens=False):
    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON
            json_output = generate_content(client, messages, model=model, show_tokens=show_tokens)
            info = json.loads(json_output)
            if show:print(info)

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

            # Check if the number of features/benefits and content match
            if feature_count != content_count or feature_count < min_features or content_count < min_features:
                print(f"Mismatch or insufficient features and content. Features: {feature_count}, Contents: {content_count}. Retrying...")
                continue

            return json_output, info  # Return both raw JSON and parsed information

        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Retrying ({attempt + 1}/{max_attempts})...")

    raise ValueError("Maximum attempts reached. Failed to generate valid content.")

def validate_and_retry_guide(client, messages, model, min_steps, max_attempts=3, show=False, show_tokens=False):
    for attempt in range(max_attempts):
        try:
            # Generate content and attempt to parse it as JSON
            json_output = generate_content(client, messages, model=model, show_tokens=show_tokens)
            info = json.loads(json_output)
            if show:print(info)

            # Validate the basic structure
            required_keys = {"subheader_3", "subheader_3_message"}
            if not all(key in info for key in required_keys):
                missing_keys = required_keys - info.keys()
                print(f"Missing keys: {missing_keys}. Retrying...")
                continue

            # Check the dynamic number of guide steps and their corresponding content
            step_keys = [key for key in info if key.startswith("guide_step_") and not key.endswith("_content")]
            step_content_keys = [key for key in info if key.startswith("guide_step_") and key.endswith("_content")]
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

    raise ValueError("Maximum attempts reached. Failed to generate valid content.")
    
# Function to replace product name with a clickable link
def make_product_link(text, url, product):
    # Find the product name enclosed in asterisks
    product_match = re.search(r'\*([^*]+)\*', text)
    if product_match:
        # Extract the product name
        product_name = product_match.group(1)
        # Define the color you want for the product link
        link_color = '#007bff'  # Bright blue, but you can choose any color
        # Replace the name with an anchor tag
        return text.replace(f"*{product_name}*", f'<a href="{url}" style="color: {link_color}; font-weight: bold; text-decoration: underline;">{product}</a>')
    return text  # Return the original text if no product name is found

def html_1(meta_dscr, new_title, CSS_STYLE, new_introduction, img_alt_1, img_url_1, new_subheader, benefits_html):
    section1 = f'''<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="utf-8">
<meta name="description" content="{meta_dscr}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,700" rel="stylesheet">
<title>{new_title}</title>
{CSS_STYLE}
</head>
<body>
<p>{new_introduction}</p>
<p><img alt="{img_alt_1}" src="{img_url_1}" /></p>
<h2>{new_subheader}</h2>
{benefits_html}
'''
    return section1

def generate_html_section(info, handle, store_url, product_intro, css_style, img_alt, img_url, old_title):
    new_title = info['title'].capitalize()

    # The URL you want users to be redirected to when they click the product name
    product_url = store_url + handle

    # Update the introduction with the product link
    new_introduction = make_product_link(info['introduction'], product_url, old_title)

    new_subheader = info['subheader_1'].capitalize()
    new_benefits = info['benefits']
    meta_dscr = info['meta']

    # Split the benefits text into sentences
    sentences = re.split(r'(?<=[.!?]) +', new_benefits)

    # Create a string with each sentence wrapped in <p> tags
    # Here, consider using the <strong> tag for the first sentence to emphasize the most important benefit.
    benefits_html = ''.join(f'<p>{sentences[0]}</p>' if i == 0 else f'<p>{sentence}</p>' for i, sentence in enumerate(sentences) if sentence)

    return html_1(meta_dscr, new_title, css_style, new_introduction, img_alt, img_url, new_subheader, benefits_html)

def generate_html_section_2(info, img_alt, img_url):
    # Constructing the HTML for section 2
    section2 = f"<h2>{info['subheader_2'].capitalize()}</h2>\n"

    # Create a set to hold processed feature numbers
    processed_features = set()

    # Dynamically find and process all feature/benefit pairs
    for key in info.keys():
        if key.startswith('tittel_'):
            # Extract the number from the feature/benefit key
            number = key.split('_')[1]

            # Construct the expected content key
            content_key = f"innhold_{number}"

            # Check if the feature has not been processed and the corresponding content exists
            if number not in processed_features and content_key in info:
                subpoint = info[key]
                content = info[content_key]

                # Adding a class and id to the <h3> tag and wrapping the subpoint in <strong> tags
                section2 += f'<h3 class="feature-title" id="feature_{number}"><strong>{subpoint.capitalize()}</strong></h3>\n<p>{content}</p>\n'

                # Mark this feature number as processed
                processed_features.add(number)

    # Add image at the end of the section
    section2_p = str(section2)
    section2 += f'<p><img alt="{img_alt}" src="{img_url}"></p>\n'

    return section2, section2_p

def generate_html_section_3(info, handle, store_url, product_intro):
    # Extract the subheader, message, and conclusion sentences
    subhead_3 = info['subheader_3']
    content_sentence_2_1 = info['subheader_3_message']
    
    # The URL you want users to be redirected to when they click the product name
    product_url = store_url + handle

    # Update the conclusion with the product link
    final_sentence = make_product_link(info['final_sentence'], product_url, product_intro)

    # Constructing the ordered list for the guide steps
    guide_steps_html = ''
    for key, value in info.items():
        if key.startswith('guide_step_') and key.endswith('_content'):
            guide_steps_html += f'<li>{value}</li>\n'

    # Constructing the HTML for section 3
    section3 = f'''<h2>{subhead_3.capitalize()}</h2>
<p>{content_sentence_2_1}</p>
<ol>
{guide_steps_html}</ol>
'''

    # Constructing the HTML for the conclusion
    section3 += f'''<p><em><strong>{final_sentence}</strong></em></p>
</body>
</html>'''

    return section3

def extract_handle_and_title_from_url(url):
    """Extracts handle and title from the product URL."""
    handle = url.split("/")[-1]
    title = " ".join(handle.split("-")).capitalize()
    return handle, title

def get_next_page_link(link_header):
    if link_header is None:
        return None

    links = link_header.split(',')
    for link in links:
        if 'rel="next"' in link:
            return link.split(';')[0].strip('<> ')
    return None

def get_shopify_products_batch(store_url, access_token, next_page_url=None):
    headers = {'X-Shopify-Access-Token': access_token}
    if not next_page_url:
        if not store_url.startswith('https://'):
            store_url = 'https://' + store_url
        next_page_url = f"{store_url}/admin/api/2024-01/products.json?limit=250"

    response = requests.get(next_page_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    data = response.json()
    products = data['products']
    products2 = [{"id":i['id'], "title":i['title'], "body_html":i['body_html'], "tags":i['tags'], "status":i['status'], "options":i['options'], "handle":i['handle']} 
                for i in products]
    next_page_url = get_next_page_link(response.headers.get('Link'))

    return products2, next_page_url

