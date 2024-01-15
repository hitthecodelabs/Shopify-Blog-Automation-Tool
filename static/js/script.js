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

// Show and hide spinner while loading data
function fetchProductCount() {
    // Show loading indicator and message
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('productCount').innerText = ''; // Clear previous product count

    fetch('/get_product_count')
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator, the "Load Product Count" button, and the loading message
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('loadProductCountButton').style.display = 'none';
            document.getElementById('loadingMessage').style.display = 'none';

            if (data.error) {
                alert(data.error);
            } else {
                document.getElementById('productCount').innerText = 'Number of products in your store: ' + data.n_products;
                document.getElementById('createNewPostButton').style.display = 'block'; // Show the create new post button
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while fetching product count');
            // Hide loading indicator and message
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('loadingMessage').style.display = 'none';
        });
}

// Update the progress bar based on loading progress
function updateLoadingIndicator(progress) {
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = `${progress}%`;
}

// Load products and update the progress bar
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
        updateLoadingIndicator(data.progress);  // Update progress bar
    }

    document.getElementById('progressBarContainer').style.display = 'none';
}

// Event listener for theme preference on page load
document.addEventListener('DOMContentLoaded', (event) => {
    const storedTheme = localStorage.getItem('theme');
    setTheme(storedTheme || 'light'); // Set to stored theme, or default to light
});
