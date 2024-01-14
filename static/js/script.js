function fetchProductCount() {
    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('productCount').innerText = ''; // Clear previous product count

    fetch('/get_product_count')
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator and the "Load Product Count" button
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('loadProductCountButton').style.display = 'none';

            if (data.error) {
                alert(data.error);
            } else {
                document.getElementById('productCount').innerText = 'Number of products in your store: ' + data.n_products;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while fetching product count');
            // Hide loading indicator
            document.getElementById('loadingIndicator').style.display = 'none';
        });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Check for stored theme preference, if any, when the page loads
document.addEventListener('DOMContentLoaded', (event) => {
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme) {
        setTheme(storedTheme);
    } else {
        setTheme('light'); // Default theme
    }
});
