document.addEventListener('DOMContentLoaded', () => {
const countryInput = document.getElementById('countryInput');
const searchButton = document.getElementById('searchButton');
const countryCard = document.getElementById('countryCard');
const countryName = document.getElementById('countryName');
const countryImage = document.getElementById('countryImage');
const countryCapital = document.getElementById('countryCapital');
const countryCurrency = document.getElementById('countryCurrency');
const countrySource = document.getElementById('countrySource');
const favoriteButton = document.getElementById('favoriteButton');
const errorMessage = document.getElementById('errorMessage');
const favoriteTag = document.getElementById('favoriteTag');

let currentCountryId = null;
let currentCountryName = null;
let isCurrentCountryFavorite = false;

searchButton.addEventListener('click', searchCountry);

countryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchCountry();
    }
});

async function searchCountry() {

    const countryNameQuery = countryInput.value.trim();

    if (!countryNameQuery) {
        showError("Por favor, ingresa el nombre de un país.");
        return;
    }

    hideError();
    countryCard.classList.add('hidden');
    favoriteTag.classList.add('hidden');
    resetFavoriteButtonState();

    try {

        const response = await fetch(`http://localhost:8000/pais/${countryNameQuery}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Error al buscar el país.");
        }

        countryName.textContent = data.nombre;
        countryImage.src = data.recurso_visual;
        countryImage.alt = `Bandera de ${data.nombre}`;
        countryCapital.textContent = data.capital;
        countryCurrency.textContent = data.moneda;
        countrySource.textContent = data.fuente === "base de datos"
            ? "Desde tu base de datos"
            : "Desde API externa";

        currentCountryId = data.id;
        currentCountryName = data.nombre;
        isCurrentCountryFavorite = data.is_favorite;

        updateFavoriteUI(isCurrentCountryFavorite);

        countryCard.classList.remove('hidden');

    } catch (error) {

        console.error("Error al obtener el país:", error);

        showError(`No se pudo encontrar el país: ${error.message}`);

        countryCard.classList.add('hidden');
        favoriteTag.classList.add('hidden');
    }
}

favoriteButton.addEventListener('click', async () => {

    if (!currentCountryId || !currentCountryName) {
        showError("Primero busca un país para poder agregarlo/quitarlo de favoritos.");
        return;
    }

    hideError();

    try {

        let response;
        let data;

        if (isCurrentCountryFavorite) {

            response = await fetch(`http://localhost:8000/removerFav/${currentCountryName}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Error al remover de favoritos.");
            }

            alert(data.mensaje);
            isCurrentCountryFavorite = false;

        } else {

            response = await fetch(`http://localhost:8000/agregarFav/${currentCountryName}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Error al agregar a favoritos.");
            }

            alert(data.mensaje);
            isCurrentCountryFavorite = true;
        }

        updateFavoriteUI(isCurrentCountryFavorite);

    } catch (error) {

        console.error("Error al gestionar favoritos:", error);

        showError(`Error al gestionar favoritos: ${error.message}`);
    }
});

function updateFavoriteUI(isFavorite) {

    if (isFavorite) {

        favoriteTag.textContent = "Favorito";
        favoriteTag.classList.remove('bg-red-200', 'text-red-800');
        favoriteTag.classList.add('bg-yellow-200', 'text-yellow-800');
        favoriteTag.classList.remove('hidden');

        favoriteButton.textContent = "Quitar de Favoritos";
        favoriteButton.classList.remove('bg-green-600','hover:bg-green-700');
        favoriteButton.classList.add('bg-red-600','hover:bg-red-700');

    } else {

        favoriteTag.textContent = "No Favorito";
        favoriteTag.classList.remove('bg-yellow-200','text-yellow-800');
        favoriteTag.classList.add('bg-red-200','text-red-800');
        favoriteTag.classList.remove('hidden');

        favoriteButton.textContent = "Agregar a Favoritos";
        favoriteButton.classList.remove('bg-red-600','hover:bg-red-700');
        favoriteButton.classList.add('bg-green-600','hover:bg-green-700');
    }
}

function resetFavoriteButtonState() {

    favoriteButton.textContent = "Agregar a Favoritos";

    favoriteButton.classList.remove(
        'bg-red-600',
        'hover:bg-red-700'
    );

    favoriteButton.classList.add(
        'bg-green-600',
        'hover:bg-green-700'
    );
}

function showError(message) {

    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {

    errorMessage.classList.add('hidden');
    errorMessage.textContent = '';
}



async function cargarNosotros() {

    const list = document.getElementById("nosotros-list");

    try {

        const response = await fetch("http://localhost:8000/Nosotros");
        const data = await response.json();

        list.innerHTML = data.map(persona => `
            <div class="bg-white p-6 rounded shadow cursor-pointer"
            onclick="toggleEquipo(this)">

                <h3 class="text-xl font-bold">${persona.nombre}</h3>

            </div>
        `).join("");

    } catch (error) {

        console.error("Error cargando equipo:", error);
    }
}

function toggleEquipo(element) {

    const detalle = element.querySelector(".detalle");
    detalle.classList.toggle("hidden");
}



});
