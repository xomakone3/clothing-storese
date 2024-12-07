let products = [];
let displayedProductCount = 0;
const PRODUCTS_PER_PAGE = 10; // Количество товаров за один раз

// Настройка бесконечной прокрутки
function setupInfiniteScroll() {
    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
            loadMoreProducts();
        }
    });
}

// Загрузка товаров
async function loadProducts() {
    try {
        const response = await fetch('products.json');
        const data = await response.json();
        products = data.products;
        displayedProductCount = 0;
        document.getElementById('products-container').innerHTML = '';
        loadMoreProducts();
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
    }
}

// Загрузка дополнительных товаров
function loadMoreProducts() {
    const productsContainer = document.getElementById('products-container');
    const endIndex = Math.min(displayedProductCount + PRODUCTS_PER_PAGE, products.length);

    for (let i = displayedProductCount; i < endIndex; i++) {
        const product = products[i];
        const productCard = createProductCard(product);
        productsContainer.appendChild(productCard);
    }

    displayedProductCount = endIndex;

    // Если все товары загружены, отключаем бесконечную прокрутку
    if (displayedProductCount >= products.length) {
        window.removeEventListener('scroll', setupInfiniteScroll);
    }
}

// Создание карточки товара
function createProductCard(product) {
    const card = document.createElement('div');
    card.classList.add('product-card');

    const image = document.createElement('img');
    image.src = product.images[0] || 'default-image.jpg';
    image.alt = product.title;

    const title = document.createElement('h3');
    title.textContent = product.title;

    const description = document.createElement('p');
    description.textContent = product.description;

    const price = document.createElement('div');
    price.classList.add('price');
    price.textContent = `${product.price} ₽`;

    const colors = document.createElement('div');
    colors.classList.add('colors');
    product.colors.forEach(color => {
        const colorDot = document.createElement('span');
        colorDot.classList.add('color-dot');
        colorDot.style.backgroundColor = color;
        colors.appendChild(colorDot);
    });

    const sizes = document.createElement('div');
    sizes.classList.add('sizes');
    product.sizes.forEach(size => {
        const sizeButton = document.createElement('button');
        sizeButton.textContent = size;
        sizes.appendChild(sizeButton);
    });

    card.appendChild(image);
    card.appendChild(title);
    card.appendChild(description);
    card.appendChild(price);
    card.appendChild(colors);
    card.appendChild(sizes);

    return card;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    setupInfiniteScroll();
});
