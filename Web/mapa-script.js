(function () {
    'use strict';

    const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

    const parseDifficulty = (feature) => {
        const d = `${feature?.properties?.description ?? ''} ${feature?.properties?.name ?? ''}`;
        const m = d.match(/dificultad\\s*(\\d+)/i);
        if (!m) return null;
        const n = Number(m[1]);
        return Number.isFinite(n) ? n : null;
    };

    const normalizeText = (s) =>
        (s || '')
            .toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\\u0300-\\u036f]/g, '');

    const getRouteColor = (difficulty) => {
        if (!difficulty) return '#d4af37';
        if (difficulty <= 1) return '#e0c04a';
        if (difficulty === 2) return '#d4af37';
        return '#f2d063';
    };

    const getRouteWeight = (difficulty) => {
        if (!difficulty) return 4.5;
        if (difficulty <= 1) return 4;
        if (difficulty === 2) return 5;
        return 5.5;
    };

    const toast = (el, message) => {
        if (!el) return;
        el.textContent = message;
        el.classList.add('is-visible');
        window.clearTimeout(toast._t);
        toast._t = window.setTimeout(() => el.classList.remove('is-visible'), 2400);
    };

    const createRouteCard = ({ name, description, difficulty }) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'mapa-route';
        card.setAttribute('role', 'listitem');

        const title = document.createElement('div');
        title.className = 'mapa-route__title';

        const strong = document.createElement('strong');
        strong.textContent = name || 'Ruta';

        const badge = document.createElement('span');
        badge.className = 'mapa-badge';
        badge.textContent = difficulty ? `D${difficulty}` : 'Ruta';

        title.appendChild(strong);
        title.appendChild(badge);

        const meta = document.createElement('div');
        meta.className = 'mapa-route__meta';
        meta.textContent = description || 'Selecciona para enfocar en el mapa.';

        card.appendChild(title);
        card.appendChild(meta);
        return card;
    };

    const init = async () => {
        const mapEl = document.getElementById('map');
        if (!mapEl || typeof L === 'undefined') return;

        const panel = document.getElementById('mapaPanel');
        const toggle = document.getElementById('mapaRoutesToggle');
        const recenterBtn = document.getElementById('mapaRecenter');
        const listEl = document.getElementById('mapaRoutes');
        const countEl = document.getElementById('mapaCount');
        const searchEl = document.getElementById('mapaSearch');
        const toastEl = document.getElementById('mapaToast');

        const map = L.map(mapEl, {
            zoomControl: true,
            preferCanvas: true,
            worldCopyJump: true,
        });

        const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap',
        });

        const esri = L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            {
                maxZoom: 19,
                attribution: '&copy; Esri',
            },
        );

        esri.addTo(map);

        L.control.layers(
            {
                'Satélite (Esri)': esri,
                'Mapa (OSM)': osm,
            },
            {},
            { collapsed: true },
        ).addTo(map);

        L.control.scale({ imperial: false }).addTo(map);

        const routesGroup = L.featureGroup().addTo(map);
        const pointsGroup = L.featureGroup().addTo(map);

        let allBounds = null;

        const highlight = {
            layer: null,
            reset: () => {
                if (!highlight.layer) return;
                try {
                    highlight.layer.setStyle?.({ opacity: 0.95, weight: highlight.layer._baseWeight });
                } catch {}
                highlight.layer = null;
            },
            set: (layer) => {
                highlight.reset();
                highlight.layer = layer;
                try {
                    layer.setStyle?.({ opacity: 1, weight: (layer._baseWeight || 5) + 1.5 });
                } catch {}
            },
        };

        const kmlUrl = 'assets/images/Rutas%20Batuco%20Off%20Road%20(1).kml';
        let geojson = null;

        try {
            const res = await fetch(kmlUrl, { cache: 'no-cache' });
            const text = await res.text();
            const xml = new DOMParser().parseFromString(text, 'text/xml');
            geojson = (window.toGeoJSON?.kml && window.toGeoJSON.kml(xml)) || null;
        } catch (e) {
            toast(toastEl, 'No se pudo cargar el mapa de rutas.');
        }

        const features = Array.isArray(geojson?.features) ? geojson.features : [];

        const routeItems = [];

        const addRouteFeature = (feature) => {
            const name = feature?.properties?.name || 'Ruta';
            const description = (feature?.properties?.description || '').replace(/<[^>]*>/g, '').trim();
            const difficulty = parseDifficulty(feature);

            const color = getRouteColor(difficulty);
            const weight = getRouteWeight(difficulty);

            const layer = L.geoJSON(feature, {
                style: () => ({
                    color,
                    weight,
                    opacity: 0.95,
                    lineCap: 'round',
                    lineJoin: 'round',
                }),
                pointToLayer: (_feat, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        color: 'rgba(0,0,0,0.35)',
                        weight: 2,
                        fillColor: color,
                        fillOpacity: 0.9,
                    });
                },
                onEachFeature: (_feat, lyr) => {
                    lyr._baseWeight = weight;
                    const popup = `<strong>${name}</strong>${description ? `<br><span>${description}</span>` : ''}${
                        difficulty ? `<br><span>Dificultad: ${difficulty}</span>` : ''
                    }`;
                    lyr.bindPopup(popup, { closeButton: true });

                    lyr.on('click', () => {
                        highlight.set(lyr);
                    });
                },
            });

            const targetGroup =
                feature.geometry?.type === 'LineString' || feature.geometry?.type === 'MultiLineString'
                    ? routesGroup
                    : pointsGroup;

            layer.addTo(targetGroup);

            const bounds = layer.getBounds?.();
            if (bounds && bounds.isValid && bounds.isValid()) {
                allBounds = allBounds ? allBounds.extend(bounds) : bounds;
            }

            routeItems.push({
                feature,
                name,
                description,
                difficulty,
                layer,
                searchKey: normalizeText(`${name} ${description} ${difficulty ? `dificultad ${difficulty}` : ''}`),
            });
        };

        for (const f of features) addRouteFeature(f);

        if (countEl) countEl.textContent = `${routeItems.length}`;

        const renderList = (filterText) => {
            if (!listEl) return;
            const q = normalizeText(filterText);
            listEl.innerHTML = '';

            const visible = q ? routeItems.filter((r) => r.searchKey.includes(q)) : routeItems;

            for (const item of visible) {
                const card = createRouteCard(item);
                card.addEventListener('click', () => {
                    const bounds = item.layer.getBounds?.();
                    if (bounds && bounds.isValid && bounds.isValid()) {
                        map.fitBounds(bounds.pad(0.18), { animate: true, duration: 0.7 });
                    } else {
                        const ll = item.layer.getLatLng?.();
                        if (ll) map.setView(ll, 16, { animate: true, duration: 0.7 });
                    }
                    highlight.set(item.layer);
                    item.layer.openPopup?.();
                    toast(toastEl, `Enfocando: ${item.name}`);
                });
                listEl.appendChild(card);
            }

            if (countEl) countEl.textContent = `${visible.length}`;
        };

        renderList('');

        if (searchEl) {
            searchEl.addEventListener('input', () => renderList(searchEl.value), { passive: true });
        }

        const recenter = () => {
            if (allBounds && allBounds.isValid && allBounds.isValid()) {
                map.fitBounds(allBounds.pad(0.16), { animate: true, duration: 0.7 });
                toast(toastEl, 'Mapa recentrado.');
            }
        };

        recenterBtn?.addEventListener('click', recenter);

        toggle?.addEventListener('click', () => {
            if (!panel) return;
            const collapsed = panel.classList.toggle('is-collapsed');
            toggle.setAttribute('aria-expanded', String(!collapsed));
        });

        recenter();

        window.addEventListener('keydown', (e) => {
            if (e.key !== 'Escape') return;
            if (!panel || !toggle) return;
            panel.classList.add('is-collapsed');
            toggle.setAttribute('aria-expanded', 'false');
        });
    };

    try {
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
        else init();
    } catch (e) {}
})();
