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
    let currentCountryName = null; // Guardamos el nombre completo para las peticiones
    let isCurrentCountryFavorite = false; // Nueva variable de estado para el frontend

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
        resetFavoriteButtonState(); // Resetea el botón antes de una nueva búsqueda

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
            countrySource.textContent = data.fuente === "base de datos" ? "Desde tu base de datos" : "Desde API externa";
            currentCountryId = data.id;
            currentCountryName = data.nombre; // Almacenamos el nombre
            isCurrentCountryFavorite = data.is_favorite; // Actualizamos el estado

            updateFavoriteUI(isCurrentCountryFavorite); // Llama a la función para actualizar la UI

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
                // Si ya es favorito, lo quitamos
                response = await fetch(`http://localhost:8000/removerFav/${currentCountryName}`, {
                    method: 'DELETE', // Usamos DELETE
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Error al remover de favoritos.");
                }
                alert(data.mensaje);
                isCurrentCountryFavorite = false; // Actualizamos el estado
            } else {
                // Si no es favorito, lo agregamos
                response = await fetch(`http://localhost:8000/agregarFav/${currentCountryName}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Error al agregar a favoritos.");
                }
                alert(data.mensaje);
                isCurrentCountryFavorite = true; // Actualizamos el estado
            }

            updateFavoriteUI(isCurrentCountryFavorite); // Actualiza la UI después de la operación

        } catch (error) {
            console.error("Error al gestionar favoritos:", error);
            showError(`Error al gestionar favoritos: ${error.message}`);
        }
    });

    // Función auxiliar para actualizar la UI del botón y la etiqueta
    function updateFavoriteUI(isFavorite) {
        if (isFavorite) {
            favoriteTag.textContent = "Favorito";
            favoriteTag.classList.remove('bg-red-200', 'text-red-800');
            favoriteTag.classList.add('bg-yellow-200', 'text-yellow-800');
            favoriteTag.classList.remove('hidden');

            favoriteButton.textContent = "Quitar de Favoritos";
            favoriteButton.classList.remove('bg-green-600', 'hover:bg-green-700', 'bg-gray-400', 'cursor-not-allowed');
            favoriteButton.classList.add('bg-red-600', 'hover:bg-red-700');
            favoriteButton.disabled = false; // Siempre habilitado para alternar
        } else {
            favoriteTag.textContent = "No Favorito";
            favoriteTag.classList.remove('bg-yellow-200', 'text-yellow-800');
            favoriteTag.classList.add('bg-red-200', 'text-red-800');
            favoriteTag.classList.remove('hidden');

            favoriteButton.textContent = "Agregar a Favoritos";
            favoriteButton.classList.remove('bg-red-600', 'hover:bg-red-700', 'bg-gray-400', 'cursor-not-allowed');
            favoriteButton.classList.add('bg-green-600', 'hover:bg-green-700');
            favoriteButton.disabled = false; // Siempre habilitado para alternar
        }
    }

    // Función para resetear el botón al inicio de una nueva búsqueda
    function resetFavoriteButtonState() {
        favoriteButton.textContent = "Agregar a Favoritos";
        favoriteButton.classList.remove('bg-red-600', 'hover:bg-red-700', 'bg-gray-400', 'cursor-not-allowed');
        favoriteButton.classList.add('bg-green-600', 'hover:bg-green-700');
        favoriteButton.disabled = false;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
        errorMessage.textContent = '';
    }
});
