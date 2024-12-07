let products = [];
let displayedProductCount = 0;
const PRODUCTS_PER_PAGE = 6; // Уменьшаем количество товаров на странице

// Настройка бесконечной прокрутки
function setupInfiniteScroll() {
    const scrollHandler = () => {
        const scrollPosition = window.innerHeight + window.scrollY;
        const documentHeight = document.documentElement.scrollHeight;
        
        // Загружаем новые товары, когда пользователь приближается к концу страницы
        if (scrollPosition >= documentHeight - 800) {
            loadMoreProducts();
        }
    };

    window.addEventListener('scroll', scrollHandler);
}

// Загрузка товаров
async function loadProducts() {
    try {
        const response = await fetch('products.json');
        const data = await response.json();
        products = Array.isArray(data) ? data : data.products || [];
        displayedProductCount = 0;
        document.getElementById('products-container').innerHTML = '';
        await loadMoreProducts();
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
    }
}

// Загрузка дополнительных товаров
async function loadMoreProducts() {
    if (displayedProductCount >= products.length) {
        return; // Все товары уже загружены
    }

    const productsContainer = document.getElementById('products-container');
    const endIndex = Math.min(displayedProductCount + PRODUCTS_PER_PAGE, products.length);
    const fragment = document.createDocumentFragment();

    for (let i = displayedProductCount; i < endIndex; i++) {
        const product = products[i];
        const productCard = createProductCard(product);
        fragment.appendChild(productCard);
    }

    productsContainer.appendChild(fragment);
    displayedProductCount = endIndex;
}

// Создание карточки товара
function createProductCard(product) {
    const card = document.createElement('div');
    card.classList.add('product-card');

    // Создаем контейнер для изображения
    const imageContainer = document.createElement('div');
    imageContainer.classList.add('product-image-container');

    const image = document.createElement('img');
    image.src = product.images[0] || 'default-image.jpg';
    image.alt = product.name;
    image.classList.add('product-image');
    imageContainer.appendChild(image);

    // Создаем контейнер для информации о товаре
    const info = document.createElement('div');
    info.classList.add('product-info');

    const name = document.createElement('h3');
    name.classList.add('product-name');
    name.textContent = product.name;

    const description = document.createElement('p');
    description.classList.add('product-description');
    description.textContent = product.description;

    const price = document.createElement('div');
    price.classList.add('product-price');
    price.textContent = `${product.price} ₽`;

    // Создаем контейнер для цветов
    const colors = document.createElement('div');
    colors.classList.add('product-colors');
    const colorsLabel = document.createElement('span');
    colorsLabel.textContent = 'Цвета: ';
    colors.appendChild(colorsLabel);

    product.colors.forEach(color => {
        const colorDot = document.createElement('span');
        colorDot.classList.add('color-dot');
        colorDot.style.backgroundColor = color;
        colors.appendChild(colorDot);
    });

    // Создаем контейнер для размеров
    const sizes = document.createElement('div');
    sizes.classList.add('product-sizes');
    const sizesLabel = document.createElement('span');
    sizesLabel.textContent = 'Размеры: ';
    sizes.appendChild(sizesLabel);

    product.sizes.forEach(size => {
        const sizeButton = document.createElement('button');
        sizeButton.classList.add('size-button');
        sizeButton.textContent = size;
        sizes.appendChild(sizeButton);
    });

    // Добавляем все элементы в карточку
    card.appendChild(imageContainer);
    info.appendChild(name);
    info.appendChild(description);
    info.appendChild(price);
    info.appendChild(colors);
    info.appendChild(sizes);
    card.appendChild(info);

    return card;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    setupInfiniteScroll();
});
