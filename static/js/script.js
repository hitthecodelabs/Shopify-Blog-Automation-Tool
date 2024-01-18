// Toggles the theme between light and dark
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Sets the theme
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function handleCreatePostButtonDisplay(n_products) {
    const createNewPostButtonElement = document.getElementById('createNewPostButton');
    if (createNewPostButtonElement) {
        if (n_products > 0) {
            createNewPostButtonElement.classList.add('fade-visible');
        } else {
            createNewPostButtonElement.classList.remove('fade-visible');
        }
    }
}

function fetchProductCount() {
    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    const loadingMessageElement = document.getElementById('loadingMessage');
    const productCountElement = document.getElementById('productCount');
    const loadProductCountButtonElement = document.getElementById('loadProductCountButton');
    const createNewPostButtonElement = document.getElementById('createNewPostButton');

    // Show loading message if it exists
    if (loadingMessageElement) loadingMessageElement.style.display = 'block';

    // Clear previous product count if productCount element exists
    if (productCountElement) productCountElement.innerText = ''; 

    fetch('/get_product_count')
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator and message
            document.getElementById('loadingIndicator').style.display = 'none';
            if (loadingMessageElement) loadingMessageElement.style.display = 'none';
            if (loadProductCountButtonElement) loadProductCountButtonElement.style.display = 'none';

            if (data.error) {
                alert(data.error);
            } else {
                // Update product count if element exists
                if (productCountElement) productCountElement.innerText = 'Number of products in your store: ' + data.n_products;

                // Call the new function with the fetched product count
                handleCreatePostButtonDisplay(data.n_products);
            }

            if (!data.error && data.n_products > 0) {
                // Hide 'Load Products' button and show 'Create New Blog Post' button
                loadProductCountButtonElement.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while fetching product count');

            // Hide loading indicator and message
            document.getElementById('loadingIndicator').style.display = 'none';
            if (loadingMessageElement) loadingMessageElement.style.display = 'none';
        });
}

function checkInitialProductCount(n_products) {
    if (n_products > 0) {
        handleCreatePostButtonDisplay(n_products);
        document.getElementById('loadProductCountButton').style.display = 'none';
    } else {
        document.getElementById('createNewPostButton').style.display = 'none';
        document.getElementById('loadProductCountButton').style.display = 'block';
    }
}

window.onload = checkInitialProductCount;

// Update the progress bar based on loading progress
function updateLoadingIndicator(progress) {
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = `${progress}%`;
}

async function loadProducts() {
    document.getElementById('progressBarContainer').style.display = 'block';
    let next_page_url = null;

    while (true) {
        const response = await fetch(`/load_products_batch?next_page_url=${next_page_url ? encodeURIComponent(next_page_url) : ''}`);
        const data = await response.json();

        if (!data.next_page_url) {
            // No more products to load
            document.getElementById('loadProductsButton').style.display = 'none'; // Hide the load products button
            break;
        }
        next_page_url = data.next_page_url;
        updateLoadingIndicator(data.progress); // Update progress bar
    }

    // Process and save products after loading is complete
    await processAndSaveProducts();
    document.getElementById('progressBarContainer').style.display = 'none';
}

async function processAndSaveProducts() {
    const response = await fetch('/process_and_save_products');
    const data = await response.json();
    if (data.error) {
        console.error('Error processing products:', data.error);
        alert('An error occurred while processing products');
    } else {
        console.log('Products processed and saved successfully');
        // Post-processing actions
    }
}

// Event listener for theme preference on page load
document.addEventListener('DOMContentLoaded', (event) => {
    const storedTheme = localStorage.getItem('theme');
    setTheme(storedTheme || 'light'); // Set to stored theme, or default to light

    // Check if searchInput exists on the page before adding event listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(event) {
            const query = event.target.value;
            if (query.length > 1) { // Fetch suggestions for queries longer than 2 characters
                fetch(`/search_products?query=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(suggestions => {
                        displaySuggestions(suggestions);
                    })
                    .catch(error => console.error('Error:', error));
            } else {
                clearSuggestions();
            }
        });
    }
});

function displaySuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('suggestionsContainer');
    suggestionsContainer.innerHTML = ''; // Clear previous suggestions

    suggestions.forEach(title => {
        const suggestionElement = document.createElement('div');
        suggestionElement.classList.add('suggestion-item');
        suggestionElement.textContent = title;
        suggestionElement.onclick = () => selectSuggestion(title);
        suggestionsContainer.appendChild(suggestionElement);
    });
}

function clearSuggestions() {
    const suggestionsContainer = document.getElementById('suggestionsContainer');
    suggestionsContainer.innerHTML = '';
}

function selectSuggestion(title) {
    document.getElementById('searchInput').value = title; // Set the selected suggestion as the search input value
    clearSuggestions();

    // Optionally,fetch the detailed product info based on the selected title if needed
    fetch(`/get_product_details?title=${encodeURIComponent(title)}`)
    .then(response => response.json())
    .then(productDetails => {
        // Handle the product details (display them or use them in some way)
        console.log(productDetails);
    }).catch(error => console.error('Error:', error));
}

// Event listener for theme preference on page load
document.addEventListener('DOMContentLoaded', (event) => {
    const storedTheme = localStorage.getItem('theme');
    setTheme(storedTheme || 'light'); // Set to stored theme, or default to light
});
