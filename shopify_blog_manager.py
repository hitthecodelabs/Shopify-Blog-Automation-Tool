import requests
import json

store_url = "https://yourstorename.myshopify.com"
access_token = "youraccesstoken"
blog_id = "actualblogID"  # Replace with the actual blog ID
headers = {
    "X-Shopify-Access-Token": access_token,
    "Content-Type": "application/json"
}
