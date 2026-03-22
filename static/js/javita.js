const API_URL = "/api";

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');

    // Seleccionamos el botón de cambio de modo
    const btn = document.querySelector('button[onclick="toggleDarkMode()"]');

    if (btn) {
        const iconName = isDark ? 'sun' : 'moon';
        const text = isDark ? 'Modo Claro' : 'Modo Oscuro';

        // Actualizamos el contenido del botón
        btn.innerHTML = `<i data-lucide="${iconName}" id="mode-icon" class="w-3.5 h-3.5"></i> ${text}`;

        // Re-inicializamos los iconos de Lucide para que se renderice el nuevo icono
        if (window.lucide) {
            lucide.createIcons();
        }
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    // Clases para el diseño del toast
    toast.className = `p-4 px-6 bg-white dark:bg-neutral-900 border-l-4 ${type === 'error' ? 'border-red-500' : 'border-brand'} shadow-2xl flex items-center gap-4 text-[11px] font-black uppercase tracking-widest light-mode-black animate-fade-in`;

    toast.innerHTML = `
        <i data-lucide="${type === 'error' ? 'x-circle' : 'check-circle'}" class="w-4 h-4 ${type === 'error' ? 'text-red-500' : 'text-brand'}"></i> 
        ${message}
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    // Animación de salida y remoción
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function switchTab(tab) {
    const tabs = ['explorar', 'favoritos', 'nosotros'];

    tabs.forEach(t => {
        const section = document.getElementById(`section-${t}`);
        const btn = document.getElementById(`tab-${t}`);

        if (section) {
            section.classList.toggle('hidden', tab !== t);
        }

        if (btn) {
            if (tab === t) {
                btn.classList.remove('opacity-40');
                btn.querySelector('.indicator').classList.remove('hidden');
            } else {
                btn.classList.add('opacity-40');
                btn.querySelector('.indicator').classList.add('hidden');
            }
        }
    });

    if (tab === 'favoritos') {
        cerrarDetalle();
        cargarFavoritos();
    } else if (tab === 'nosotros') {
        document.getElementById("nosotros-list").innerHTML = "";
    }
}

/**
 * Permite realizar la búsqueda al presionar la tecla Enter en el input.
 */
function handleSearch(e) {
    if (e.key === 'Enter') buscarPais();
}

/**
 * Realiza una petición al backend de Flask para obtener información de un país.
 */
async function buscarPais() {
    const inputField = document.getElementById('search-input');
    const query = inputField.value.trim();

    if (!query || query.length < 2) return;

    const container = document.getElementById('search-result-container');

    try {
        const res = await fetch(`${API_URL}/pais/${encodeURIComponent(query)}`);
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || "Destino no encontrado");

        // Renderizamos el ticket con la opción de añadir a favoritos (true)
        container.innerHTML = renderTicket(data, true);
        if (window.lucide) lucide.createIcons();

    } catch (err) {
        showToast(err.message, "error");
    }
}

/**
 * Carga la lista de favoritos desde la base de datos a través de la API.
 */
async function cargarFavoritos() {
    const list = document.getElementById('fav-list');
    try {
        const res = await fetch(`${API_URL}/favoritos`);
        const data = await res.json();

        document.getElementById('fav-counter').innerText = `${data.length} DESTINOS ARCHIVADOS`;

        if (data.length === 0) {
            list.innerHTML = `<p class="text-center py-20 opacity-30 uppercase tracking-widest text-xs">Su bitácora está vacía</p>`;
            return;
        }

        list.innerHTML = data.map(f => `
            <div onclick="verDetalleFavorito('${f.nombre}')" class="bg-white dark:bg-[#0a0a0a] p-10 border border-black/10 dark:border-white/10 flex items-center justify-between hover:border-brand dark:hover:border-brand transition-all cursor-pointer shadow-2xl group animate-fade-in">
                <div class="flex items-center gap-14">
                    <span class="text-7xl font-serif text-brand group-hover:scale-110 transition-transform duration-500">${f.id}</span>
                    <div>
                        <p class="text-[10px] font-black text-black/40 dark:text-white/40 uppercase tracking-[0.4em] mb-2">PASAPORTE CONFIRMADO</p>
                        <h4 class="text-5xl font-light text-black dark:text-white">${f.nombre}</h4>
                    </div>
                </div>
                <button onclick="eliminarFavorito('${f.id}', '${f.nombre}', event)" class="text-black/40 dark:text-white/40 hover:opacity-100 hover:text-red-500 p-4 transition-all">
                    <i data-lucide="trash-2" class="w-8 h-8"></i>
                </button>
            </div>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        showToast("Error de conexión con la bitácora", "error");
    }
}

/**
 * Guarda un país en la tabla de favoritos.
 */
async function guardarFavorito(id, nombre) {
    try {
        const res = await fetch(`${API_URL}/favoritos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id.toUpperCase(), nombre: nombre })
        });

        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || "Fallo al guardar");
        }

        showToast(`¡${nombre} añadido a su bitácora!`);
        cargarFavoritos();
    } catch (e) {
        showToast(e.message, "error");
    }
}

/**
 * Elimina un país de la tabla de favoritos.
 */
async function eliminarFavorito(id, nombre, e) {
    if (e) e.stopPropagation();

    try {
        const res = await fetch(`${API_URL}/favoritos/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error("No se pudo eliminar");

        cargarFavoritos();
        showToast(`${nombre} removido de la colección.`);
    } catch (e) {
        showToast("Error al eliminar", "error");
    }
}

/**
 * Muestra la información detallada de un país seleccionado desde favoritos.
 */
async function verDetalleFavorito(nombre) {
    document.getElementById('fav-main-view').classList.add('hidden');
    const detail = document.getElementById('fav-detail');
    const container = document.getElementById('fav-detail-container');

    detail.classList.remove('hidden');
    container.innerHTML = `<div class="py-20 text-center animate-pulse">Sincronizando datos de vuelo...</div>`;

    try {
        const res = await fetch(`${API_URL}/pais/${encodeURIComponent(nombre)}`);
        const data = await res.json();

        // Renderizamos el ticket sin el botón de añadir (false)
        container.innerHTML = renderTicket(data, false);
        if (window.lucide) lucide.createIcons();

    } catch (e) {
        container.innerHTML = `<p class="text-red-500 py-10">Error al sincronizar datos del servidor.</p>`;
    }
}

/**
 * Regresa a la vista general de la lista de favoritos.
 */
function cerrarDetalle() {
    document.getElementById('fav-main-view').classList.remove('hidden');
    document.getElementById('fav-detail').classList.add('hidden');
}

/**
 * Genera el código HTML para mostrar el "Ticket" informativo del país.
 */
function renderTicket(data, showAddBtn) {
    const campos = [
        { l: 'CAPITAL', v: data.capital, i: 'map-pin' },
        { l: 'POBLACIÓN', v: data.poblacion, i: 'users' },
        { l: 'IDIOMAS', v: data.idiomas, i: 'languages' },
        { l: 'SUPERFICIE', v: data.area, i: 'maximize-2' },
        { l: 'REGIÓN', v: data.region, i: 'globe' },
        { l: 'HUSO HORARIO', v: data.zonaHoraria, i: 'clock' }
    ];

    return `
        <div class="w-full bg-white dark:bg-[#0a0a0a] text-black dark:text-white rounded-sm shadow-2xl overflow-hidden border border-black/10 dark:border-white/5 animate-fade-in transition-colors duration-500">
            <div class="h-2 w-full bg-brand"></div>
            <div class="p-6 md:p-10"> 
                <div class="flex flex-col lg:flex-row justify-between items-start mb-10 border-b border-black/10 dark:border-white/10 pb-8">
                    <div>
                        <span class="text-[10px] font-black tracking-[0.4em] text-brand uppercase">First Class Global</span>
                        <h2 class="text-5xl md:text-6xl font-serif mt-3 leading-none">${data.nombre}</h2> 
                    </div>
                    <div class="text-left lg:text-right mt-6 lg:mt-0">
                        <p class="text-[9px] font-bold text-black/40 dark:text-white/40 uppercase tracking-widest">GATEWAY</p>
                        <p class="text-4xl md:text-5xl font-light text-brand tracking-tighter">${data.id}</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                    <div class="relative group flex justify-center bg-black/5 dark:bg-black/40 border border-black/5 dark:border-white/5 p-4 rounded-sm">
                        <img src="${data.bandera}" class="w-full h-56 object-contain drop-shadow-lg grayscale-[0.2] group-hover:grayscale-0 transition-all duration-700" alt="Bandera">
                    </div>
                    <div class="grid grid-cols-2 gap-x-6 gap-y-8 font-sans-ui content-center">
                        ${campos.map(item => `
                            <div class="space-y-1.5">
                                <p class="text-[9px] font-black text-brand uppercase tracking-widest flex items-center gap-1.5">
                                    <i data-lucide="${item.i}" class="w-3.5 h-3.5"></i> ${item.l}
                                </p>
                                <p class="text-lg font-bold leading-tight">${item.v || 'N/A'}</p> 
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="mt-12 grid grid-cols-1 ${showAddBtn ? 'sm:grid-cols-3' : 'sm:grid-cols-2'} gap-3 w-full"> 
                    <a href="${data.mapa}" target="_blank" class="w-full text-center px-6 py-3.5 text-[10px] font-black tracking-widest bg-neutral-900 dark:bg-[#1a1c2c] text-white uppercase hover:bg-brand transition-all">
                        Ver Mapas
                    </a>
                    ${showAddBtn ? `
                        <button onclick="guardarFavorito('${data.id}', '${data.nombre}')" class="w-full text-center px-6 py-3.5 text-[10px] font-black tracking-widest bg-brand text-white dark:text-black uppercase hover:bg-brand-hover transition-all shadow-sm hover:shadow-lg">
                            Favoritos
                        </button>
                    ` : ''}
                    <button onclick="cargarTurismo('${data.latitud || ''}', '${data.longitud || ''}', this)" class="w-full text-center px-6 py-3.5 text-[10px] font-black tracking-widest bg-neutral-900 dark:bg-[#1a1c2c] text-white uppercase hover:bg-brand transition-all">
                        Ver Lugares Turísticos
                    </button>
               </div>
               <div class="contenedor-turismo mt-6 w-full"></div>
            </div>
        </div>
    `;
}

// Nueva firma de función: acepta btnElement
async function cargarTurismo(lat, lon, btnElement) {
    if (!lat || !lon) {
        showToast('Coordenadas no disponibles para este destino', 'error');
        return;
    }

    // Buscamos el contenedor relativo al botón que desencadenó la acción
    const container = btnElement.parentElement.nextElementSibling;

    // Estado de carga (Loading UI)
    container.innerHTML = `
        <div class="py-10 text-center animate-pulse">
            <p class="text-[11px] font-black text-brand uppercase tracking-[0.3em]">
                Buscando Lugares Turísticos, espera un momento...
            </p>
        </div>
    `;

    try {
        const res = await fetch(`${API_URL}/turismo/${lat}/${lon}`);
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || "No se pudo contactar al radar turístico");

        if (!data.data || data.data.length === 0) {
            container.innerHTML = `
                <div class="py-10 text-center">
                    <p class="text-[10px] text-black/40 dark:text-white/40 uppercase tracking-widest">
                        Sin datos turísticos en la zona centro.
                    </p>
                </div>
            `;
            return;
        }

        // Renderizado del Grid de Turismo adaptativo (Modo Claro/Oscuro)
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full animate-fade-in">
                ${data.data.map(lugar => `
                    <div class="p-6 border border-black/10 dark:border-white/10 bg-black/5 dark:bg-[#0f0f0f] hover:border-brand dark:hover:border-brand transition-all duration-300">
                        <p class="text-[10px] font-black uppercase tracking-widest text-brand mb-3">
                            ${lugar.categoria} • ${lugar.distancia}
                        </p>
                        <h4 class="text-xl font-serif leading-tight mb-2">
                            ${lugar.nombre}
                        </h4>
                        <p class="text-[11px] text-black/50 dark:text-white/50 font-sans-ui truncate" title="${lugar.direccion}">
                            ${lugar.direccion}
                        </p>
                    </div>
                `).join('')}
            </div>
        `;

        if (window.lucide) lucide.createIcons();

    } catch (err) {
        container.innerHTML = '';
        showToast(err.message, "error");
    }
}

async function mostrarEquipo() {
    const list = document.getElementById("nosotros-list");
    if (list.innerHTML.trim() !== "") {
        list.innerHTML = "";
    } else {
        await cargarNosotros();
    }
}

async function cargarNosotros() {
    const list = document.getElementById("nosotros-list");

    list.innerHTML = `<div class="py-20 text-center animate-pulse text-[11px] font-black tracking-widest uppercase opacity-50 light-mode-black transition-colors">Contactando a la tripulación...</div>`;

    try {
        const response = await fetch("/Nosotros");
        if (!response.ok) throw new Error("Error en la respuesta del servidor");
        const data = await response.json();

        list.innerHTML = data.map(persona => `
            <div class="bg-black/5 dark:bg-black p-8 border border-black/10 dark:border-white/10 flex items-center justify-between hover:border-brand transition-all cursor-default shadow-sm hover:shadow-2xl group animate-fade-in">
                <div class="flex items-center gap-8">
                    <div class="w-12 h-12 bg-brand rounded-full flex items-center justify-center text-black font-black text-xl shadow-lg">
                        ${persona.nombre.trim().charAt(0)}
                    </div>
                    <div>
                        <p class="text-[9px] font-black text-black/40 dark:text-white/40 uppercase tracking-[0.4em] mb-1">MEMBER</p>
                        <h4 class="text-2xl md:text-3xl font-light text-black dark:text-white">${persona.nombre.trim()}</h4>
                    </div>
                </div>
                <i data-lucide="award" class="w-8 h-8 text-black/20 dark:text-white/20 group-hover:text-brand transition-colors"></i>
            </div>
        `).join("");

        if (window.lucide) lucide.createIcons();

    } catch (error) {
        console.error("Error cargando equipo:", error);
        list.innerHTML = `<div class="py-10 text-center text-red-500 font-bold uppercase tracking-widest text-[11px]">Error al contactar a la tripulación</div>`;
        showToast("Error al cargar la información del equipo", "error");
    }
}

/**
 * Inicialización al cargar la ventana.
 */
window.onload = () => {
    if (window.lucide) lucide.createIcons();

    // Verificamos si el sistema ya está en modo oscuro para ajustar el texto inicial
    if (document.documentElement.classList.contains('dark')) {
        const btn = document.querySelector('button[onclick="toggleDarkMode()"]');
        if (btn) btn.innerHTML = `<i data-lucide="sun" id="mode-icon" class="w-3.5 h-3.5"></i> Vuelo Diurno`;
    }
};