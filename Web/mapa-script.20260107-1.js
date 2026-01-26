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

    const toLatLng = ([lng, lat]) => L.latLng(lat, lng);

    const flattenLineCoords = (geometry) => {
        if (!geometry) return [];
        if (geometry.type === 'LineString') return geometry.coordinates || [];
        if (geometry.type === 'MultiLineString') {
            return (geometry.coordinates || []).flatMap((segment) => segment || []);
        }
        return [];
    };

    const computeDistanceKm = (coords) => {
        if (!coords || coords.length < 2) return 0;
        let total = 0;
        for (let i = 1; i < coords.length; i += 1) {
            const a = toLatLng(coords[i - 1]);
            const b = toLatLng(coords[i]);
            total += a.distanceTo(b);
        }
        return total / 1000;
    };

    const formatKm = (value) => {
        if (!Number.isFinite(value)) return '—';
        return value >= 10 ? value.toFixed(1) : value.toFixed(2);
    };

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

    const createRouteCard = ({ name, description, difficulty, distanceKm }) => {
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
        const details = [
            description || 'Selecciona para enfocar en el mapa.',
            distanceKm ? `${formatKm(distanceKm)} km` : null,
            difficulty ? `Dificultad ${difficulty}` : null,
        ].filter(Boolean);
        meta.textContent = details.join(' · ');

        card.appendChild(title);
        card.appendChild(meta);
        return card;
    };

    const init = async () => {
        const mapEl = document.getElementById('map');
        const toastEl = document.getElementById('mapaToast');
        if (!mapEl) return;
        if (typeof L === 'undefined') {
            mapEl.innerHTML = '<div class="mapa-error">No se pudo cargar el mapa. Revisa tu conexión e intenta nuevamente.</div>';
            toast(toastEl, 'No se pudo cargar el mapa.');
            return;
        }

        const panel = document.getElementById('mapaPanel');
        const toggle = document.getElementById('mapaRoutesToggle');
        const recenterBtn = document.getElementById('mapaRecenter');
        const listEl = document.getElementById('mapaRoutes');
        const countEl = document.getElementById('mapaCount');
        const searchEl = document.getElementById('mapaSearch');
        const statRoutes = document.getElementById('mapaStatRoutes');
        const statKm = document.getElementById('mapaStatKm');
        const statDifficulty = document.getElementById('mapaStatDifficulty');
        const spotlightTitle = document.getElementById('mapaSpotlightTitle');
        const spotlightDesc = document.getElementById('mapaSpotlightDesc');
        const spotlightDistance = document.getElementById('mapaSpotlightDistance');
        const spotlightDifficulty = document.getElementById('mapaSpotlightDifficulty');
        const spotlightFocus = document.getElementById('mapaSpotlightFocus');
        const spotlightPlay = document.getElementById('mapaSpotlightPlay');

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
        let activeRoute = null;
        let runner = null;
        let runnerTimer = null;
        let trail = null;
        let motionLine = null;

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

        const resetRunner = () => {
            if (runnerTimer) {
                window.clearInterval(runnerTimer);
                runnerTimer = null;
            }
            if (runner) {
                try {
                    map.removeLayer(runner);
                } catch {}
                runner = null;
            }
            if (trail) {
                try {
                    map.removeLayer(trail);
                } catch {}
                trail = null;
            }
            if (motionLine) {
                try {
                    map.removeLayer(motionLine);
                } catch {}
                motionLine = null;
            }
            if (spotlightPlay) spotlightPlay.textContent = 'Recorrido';
        };

        const setSpotlight = (item) => {
            activeRoute = item;
            if (!item) return;
            if (spotlightTitle) spotlightTitle.textContent = item.name || 'Ruta';
            if (spotlightDesc) spotlightDesc.textContent = item.description || 'Ruta destacada del Fundo Moraga.';
            if (spotlightDistance) {
                spotlightDistance.textContent = item.distanceKm ? `${formatKm(item.distanceKm)} km` : '— km';
            }
            if (spotlightDifficulty) {
                spotlightDifficulty.textContent = item.difficulty ? `Dificultad ${item.difficulty}` : 'Dificultad —';
            }
            if (spotlightFocus) spotlightFocus.disabled = false;
            if (spotlightPlay) spotlightPlay.disabled = !item.pathCoords || item.pathCoords.length < 2;
        };

        const animateRoute = (item) => {
            if (!item?.pathCoords || item.pathCoords.length < 2) return;
            resetRunner();
            const latlngs = item.pathCoords.map((coord) => toLatLng(coord));
            motionLine = L.polyline(latlngs, {
                color: item.color,
                weight: Math.max(2, item.weight - 1),
                opacity: 0.9,
                dashArray: '6 14',
            }).addTo(map);

            let dashOffset = 0;
            const animateDash = () => {
                dashOffset = (dashOffset + 1) % 20;
                try {
                    motionLine.setStyle({ dashOffset: `${dashOffset}` });
                } catch {}
            };

            runner = L.circleMarker(latlngs[0], {
                radius: 6,
                color: 'rgba(0,0,0,0.4)',
                weight: 2,
                fillColor: item.color,
                fillOpacity: 0.95,
            }).addTo(map);
            trail = L.polyline([latlngs[0]], {
                color: item.color,
                weight: Math.max(3, item.weight),
                opacity: 0.85,
            }).addTo(map);

            let idx = 0;
            runnerTimer = window.setInterval(() => {
                animateDash();
                idx += 1;
                if (idx >= latlngs.length) {
                    resetRunner();
                    return;
                }
                runner.setLatLng(latlngs[idx]);
                trail.addLatLng(latlngs[idx]);
            }, 70);
        };

        const kmlSources = [
            'https://fundomoragastorage.blob.core.windows.net/assets/data/rutas-batuco-off-road.kml',
            'https://fundomoragastorage.blob.core.windows.net/assets/images/Rutas%20Batuco%20Off%20Road%20%281).kml',
        ];
        let geojson = null;

        try {
            let kmlText = '';
            for (const url of kmlSources) {
                const res = await fetch(url, { cache: 'no-cache' });
                if (!res.ok) continue;
                kmlText = await res.text();
                if (kmlText.trim()) break;
            }

            if (!kmlText) {
                throw new Error('KML vacío');
            }

            if (!window.toGeoJSON?.kml) {
                throw new Error('toGeoJSON no disponible');
            }

            const xml = new DOMParser().parseFromString(kmlText, 'text/xml');
            geojson = window.toGeoJSON.kml(xml) || null;
        } catch (e) {
            toast(toastEl, 'No se pudo cargar el mapa de rutas.');
        }

        const features = Array.isArray(geojson?.features) ? geojson.features : [];

        const routeItems = [];

        const addRouteFeature = (feature) => {
            const name = feature?.properties?.name || 'Ruta';
            const description = (feature?.properties?.description || '').replace(/<[^>]*>/g, '').trim();
            const difficulty = parseDifficulty(feature);
            const lineCoords = flattenLineCoords(feature.geometry);
            const distanceKm = computeDistanceKm(lineCoords);

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
                        if (lyr._routeItem) {
                            setSpotlight(lyr._routeItem);
                            resetRunner();
                        }
                    });
                },
            });
            layer._baseWeight = weight;

            const targetGroup =
                feature.geometry?.type === 'LineString' || feature.geometry?.type === 'MultiLineString'
                    ? routesGroup
                    : pointsGroup;

            layer.addTo(targetGroup);

            const bounds = layer.getBounds?.();
            if (bounds && bounds.isValid && bounds.isValid()) {
                allBounds = allBounds ? allBounds.extend(bounds) : bounds;
            }

            const routeItem = {
                feature,
                name,
                description,
                difficulty,
                layer,
                pathCoords: lineCoords,
                distanceKm,
                color,
                weight,
                searchKey: normalizeText(`${name} ${description} ${difficulty ? `dificultad ${difficulty}` : ''}`),
            };

            try {
                layer.eachLayer?.((child) => {
                    child._routeItem = routeItem;
                });
            } catch {}

            routeItems.push(routeItem);
        };

        for (const f of features) addRouteFeature(f);

        if (countEl) countEl.textContent = `${routeItems.length}`;
        if (statRoutes) statRoutes.textContent = `${routeItems.length}`;

        const totalKm = routeItems.reduce((acc, item) => acc + (item.distanceKm || 0), 0);
        const maxDifficulty = routeItems.reduce((acc, item) => Math.max(acc, item.difficulty || 0), 0);
        if (statKm) statKm.textContent = totalKm ? formatKm(totalKm) : '—';
        if (statDifficulty) statDifficulty.textContent = maxDifficulty ? `D${maxDifficulty}` : '—';

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
                    setSpotlight(item);
                    resetRunner();
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

        if (spotlightFocus) {
            spotlightFocus.addEventListener('click', () => {
                if (!activeRoute) return;
                const bounds = activeRoute.layer.getBounds?.();
                if (bounds && bounds.isValid && bounds.isValid()) {
                    map.fitBounds(bounds.pad(0.18), { animate: true, duration: 0.7 });
                }
                highlight.set(activeRoute.layer);
            });
        }

        if (spotlightPlay) {
            spotlightPlay.addEventListener('click', () => {
                if (!activeRoute) return;
                if (runnerTimer) {
                    resetRunner();
                    return;
                }
                spotlightPlay.textContent = 'Detener';
                animateRoute(activeRoute);
            });
        }

        if (routeItems[0]) setSpotlight(routeItems[0]);
        recenter();

        window.addEventListener('keydown', (e) => {
            if (e.key !== 'Escape') return;
            if (!panel || !toggle) return;
            panel.classList.add('is-collapsed');
            toggle.setAttribute('aria-expanded', 'false');
            resetRunner();
        });
    };

    try {
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
        else init();
    } catch (e) {}
})();

