const API_URL = "/api";

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    
    // Seleccionamos el botón de cambio de modo
    const btn = document.querySelector('button[onclick="toggleDarkMode()"]');
    
    if (btn) {
        const iconName = isDark ? 'sun' : 'moon';
        const text = isDark ? 'Vuelo Diurno' : 'Vuelo Nocturno';
        
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
    toast.className = `p-4 px-6 bg-white dark:bg-neutral-900 border-l-4 ${type === 'error' ? 'border-red-500' : 'border-amber-400'} shadow-2xl flex items-center gap-4 text-[11px] font-black uppercase tracking-widest light-mode-black animate-fade-in`;
    
    toast.innerHTML = `
        <i data-lucide="${type === 'error' ? 'x-circle' : 'check-circle'}" class="w-4 h-4 ${type === 'error' ? 'text-red-500' : 'text-amber-500'}"></i> 
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
    document.getElementById('section-explorar').classList.toggle('hidden', tab !== 'explorar');
    document.getElementById('section-favoritos').classList.toggle('hidden', tab !== 'favoritos');
    
    const btnEx = document.getElementById('tab-explorar');
    const btnFav = document.getElementById('tab-favoritos');
    
    if (tab === 'explorar') {
        btnEx.classList.remove('opacity-40'); 
        btnFav.classList.add('opacity-40');
        btnEx.querySelector('.indicator').classList.remove('hidden');
        btnFav.querySelector('.indicator').classList.add('hidden');
    } else {
        btnFav.classList.remove('opacity-40'); 
        btnEx.classList.add('opacity-40');
        btnFav.querySelector('.indicator').classList.remove('hidden');
        btnEx.querySelector('.indicator').classList.add('hidden');
        cerrarDetalle();
        cargarFavoritos();
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
            <div onclick="verDetalleFavorito('${f.nombre}')" class="bg-black p-10 border border-white/10 flex items-center justify-between hover:border-amber-400 transition-all cursor-pointer shadow-2xl group animate-fade-in">
                <div class="flex items-center gap-14">
                    <span class="text-7xl font-serif text-amber-400 group-hover:scale-110 transition-transform duration-500">${f.id}</span>
                    <div>
                        <p class="text-[10px] font-black text-white/40 uppercase tracking-[0.4em] mb-2">PASAPORTE CONFIRMADO</p>
                        <h4 class="text-5xl font-light text-white">${f.nombre}</h4>
                    </div>
                </div>
                <button onclick="eliminarFavorito('${f.id}', '${f.nombre}', event)" class="text-white opacity-40 hover:opacity-100 hover:text-red-500 p-4 transition-all">
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
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id.toUpperCase() })
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
        {l: 'CAPITAL', v: data.capital, i: 'map-pin'},
        {l: 'POBLACIÓN', v: data.poblacion, i: 'users'},
        {l: 'IDIOMAS', v: data.idiomas, i: 'languages'},
        {l: 'SUPERFICIE', v: data.area, i: 'maximize-2'},
        {l: 'REGIÓN', v: data.region, i: 'globe'},
        {l: 'HUSO HORARIO', v: data.zonaHoraria, i: 'clock'}
    ];

    return `
        <div class="w-full bg-[#0a0a0a] rounded-sm shadow-2xl overflow-hidden border border-white/5 animate-fade-in">
            <div class="h-2 w-full bg-amber-400"></div>
            <div class="p-10 md:p-16">
                <div class="flex flex-col lg:flex-row justify-between items-start mb-16 border-b border-white/10 pb-12">
                    <div>
                        <span class="text-[11px] font-black tracking-[0.4em] text-amber-400 uppercase">First Class Global</span>
                        <h2 class="text-6xl md:text-8xl font-serif text-white mt-4 leading-none">${data.nombre}</h2>
                    </div>
                    <div class="text-left lg:text-right mt-8 lg:mt-0">
                        <p class="text-[10px] font-bold text-white/40 uppercase tracking-widest">GATEWAY</p>
                        <p class="text-5xl md:text-6xl font-light text-amber-400 tracking-tighter">${data.id}</p>
                    </div>
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-16">
                    <div class="relative group">
                        <img src="${data.bandera}" class="w-full h-80 object-cover shadow-2xl border border-white/10 grayscale-[0.2] group-hover:grayscale-0 transition-all duration-700" alt="Bandera">
                        <div class="absolute inset-0 border border-white/5 pointer-events-none"></div>
                    </div>
                    <div class="grid grid-cols-2 gap-x-10 gap-y-12 font-sans-ui">
                        ${campos.map(item => `
                            <div class="space-y-2">
                                <p class="text-[10px] font-black text-amber-400 uppercase tracking-widest flex items-center gap-2">
                                    <i data-lucide="${item.i}" class="w-3.5 h-3.5"></i> ${item.l}
                                </p>
                                <p class="text-xl font-bold text-white leading-tight">${item.v || 'N/A'}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="mt-16 flex flex-col sm:flex-row justify-center gap-4 w-full">
                    <a href="${data.mapa}" target="_blank" class="flex-1 lg:flex-none text-center px-10 py-5 text-[11px] font-black tracking-widest bg-[#1a1c2c] text-white uppercase hover:bg-white hover:text-black transition-all">
                        Ver Mapas
                    </a>
                    ${showAddBtn ? `
                        <button onclick="guardarFavorito('${data.id}', '${data.nombre}')" class="flex-1 lg:flex-none text-center px-10 py-5 text-[11px] font-black tracking-widest bg-amber-400 text-black uppercase hover:bg-white hover:text-amber-600 transition-all shadow-sm hover:shadow-lg">
                            Favoritos
                        </button>
                    ` : ''}
               </div>
            </div>
        </div>
    `;
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