import os
import json
import logging
import tempfile
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

from uttils import *

app = Flask(__name__)
app.secret_key = 'zabcdefghijklmnopqrstuvwxyz_secret_key_zabcdefghijklmnopqrstuvwxyz'

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/logout')
def logout():
    # Clear all data stored in session
    session.clear()
    # Redirect to the login page
    return redirect(url_for('index'))

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        access_token = request.form['access_token']
        shop_url = request.form['shop_url']

        # Standardize the shop URL format
        if not shop_url.startswith('https://'):
            shop_url = 'https://' + shop_url

        # Validate access token and shop URL
        try:
            shop_info = get_shop_info_from_shopify(shop_url, access_token)
            if 'shop' in shop_info:
                # Store the entire shop_info object in session
                session['shop_info'] = shop_info
                session['access_token'] = access_token
                return render_template('home.html', shop_info=shop_info)
            else:
                # Invalid token or URL
                return "Invalid token or URL. Please try again.", 400
        except Exception as e:
            # Handle exceptions (e.g., network errors)
            return f"An error occurred: {e}", 500

    else:
        # For GET requests, check if shop info is in session
        shop_info = session.get('shop_info')
        if shop_info:
            # If shop info is available in session, render the home page with it
            return render_template('home.html', shop_info=shop_info)
        else:
            # If no shop info in session, redirect to index page for new login
            return redirect(url_for('index'))
        
@app.route('/load_products')
def load_products():
    # Check if 'n_products' exists in the session
    n_products_exists = 'n_products' in session
    n_products = session.get('n_products', 0)

    return render_template('load_products.html', n_products_exists=n_products_exists, n_products=n_products)
    
@app.route('/get_product_count')
def get_product_count():
    shop_info = session.get('shop_info')
    # print(shop_info)
    if shop_info:
        access_token = session.get('access_token')
        myshopify_domain = shop_info.get('shop')['myshopify_domain']
        # print(access_token)
        # print(myshopify_domain)

        if access_token and myshopify_domain:
            try:
                
                admin_store_url = f"https://{myshopify_domain}"
                
                # Initialize or update the JSON file with products
                result_file_path = session.get('result_file_path')

                if not result_file_path:
                    
                    product_maps = get_product_maps_from_shopify(admin_store_url, access_token)
                    result = fetch_and_parse_urls(product_maps)
                    n_products = len(result)

                    # First batch, create a new file and write products
                    _, result_file_path = tempfile.mkstemp(suffix='.json')
                    with open(result_file_path, 'w', encoding='utf8') as file:
                        json.dump(result, file, ensure_ascii=False, indent=4)
                    
                    session['result_file_path'] = result_file_path
                    session['n_products'] = n_products
                        
                return jsonify(n_products=n_products)
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            return jsonify(error="Shop details are incomplete. Please log in again."), 400
    else:
        return jsonify(error="You are not logged in. Please log in first."), 403
    
@app.route('/create_post')
def create_post():
    # Check if 'titles_file_path' exists in the session
    titles_file_exists = 'titles_file_path' in session

    return render_template('create_post.html', titles_file_exists=titles_file_exists)

@app.route('/load_products_batch')
def load_products_batch():
    shop_info = session.get('shop_info')
    if not shop_info:
        return jsonify(error="Not logged in."), 403

    # Check if products file path is already set in session
    if 'products_file_path' in session:
        # Check if all products are loaded
        if session.get('total_products_loaded', 0) >= session.get('initial_total_products', 0):
            return jsonify(message="All products are already loaded.", progress=100)
        
    access_token = session.get('access_token')
    myshopify_domain = shop_info.get('shop')['myshopify_domain']
    next_page_url = session.get('next_page_url')

    if not access_token or not myshopify_domain:
        return jsonify(error="Shop details are incomplete."), 400

    try:
        admin_store_url = f"https://{myshopify_domain}"

        if not next_page_url or next_page_url == 'null':
            next_page_url = None

        products, next_page_url = get_shopify_products_batch(admin_store_url, access_token, next_page_url)
        session['next_page_url'] = next_page_url

        # Initialize or update the JSON file with products
        all_products = []  # Initialize the all_products list
        products_file_path = session.get('products_file_path')
        if not products_file_path:
            _, products_file_path = tempfile.mkstemp(suffix='.json')
            session['products_file_path'] = products_file_path
            with open(products_file_path, 'w', encoding='utf8') as file:
                json.dump(products, file, ensure_ascii=False, indent=4)
        else:
            with open(products_file_path, 'r', encoding='utf8') as file:
                all_products = json.load(file)
            all_products.extend(products)
            with open(products_file_path, 'w', encoding='utf8') as file:
                json.dump(all_products, file, ensure_ascii=False, indent=4)

        # Calculate and update session with total products count
        total_products_loaded = len(all_products)
        session['total_products_loaded'] = total_products_loaded

        # Set initial total products if not set
        if 'initial_total_products' not in session:
            initial_total_products = get_shopify_product_count(admin_store_url, access_token)
            session['initial_total_products'] = initial_total_products
        else:
            initial_total_products = session['initial_total_products']

        progress = (total_products_loaded / initial_total_products) * 100 if initial_total_products else 0
        
        return jsonify(next_page_url=next_page_url, progress=progress)
    except Exception as e:
        logging.exception("Failed to load products: ")
        return jsonify(error=str(e)), 500

@app.route('/process_and_save_products')
def process_and_save_products():
    processed_data, presult2_file_path = process_product_data(session)

    presult2_file_path = session.get('products_file_path')

    if 'error' in processed_data:
        return jsonify({"error": processed_data["error"]}), 500

    return jsonify({"message": "Products processed and saved successfully", "file_path": presult2_file_path})

@app.route('/search_products')
def search_products():
    query = request.args.get('query', '').lower()
    titles_file_path = session.get('titles_file_path')

    if not titles_file_path or not query:
        return jsonify([])

    try:
        with open(titles_file_path, 'r', encoding='utf-8') as file:
            titles = json.load(file)

        # Filter titles based on the query
        filtered_titles = [title for title in titles if query in title.lower()]

        return jsonify(filtered_titles[:10])  # Limit to 10 suggestions
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/get_product_details')
def get_product_details():
    title = request.args.get('title', '')
    products_file_path = session.get('products_file_path')
    if not products_file_path or not title:
        return jsonify({"error": "Product details not found"})

    try:
        with open(products_file_path, 'r', encoding='utf-8') as file:
            all_products = json.load(file)
            product_details = all_products.get(title, {})

        return jsonify(product_details)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
