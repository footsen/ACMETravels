let map;
let countryLayer;
let visitData = {};
const counts = { chris: 0, maggie: 0, allyson: 0, edward: 0 };
let selected = { chris: true, maggie: true, allyson: true, edward: true };

document.addEventListener('DOMContentLoaded', async () => {
  map = L.map('map', {
    worldCopyJump: false,
    noWrap: true,
    maxBounds: [[-85, -180], [85, 180]],
    maxBoundsViscosity: 1.0
  }).setView([20, 0], 2);

  L.tileLayer('https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.png?api_key=bcbaa58f-a841-4a26-b825-32c67976c517', {
    attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
    maxZoom: 19
  }).addTo(map);

  // Load visit data
  const res = await fetch('acme-travels.json');
  const visits = await res.json();
  visits.forEach(v => {
    visitData[v.code] = {
      chris: v.chris,
      maggie: v.maggie,
      allyson: v.allyson,
      edward: v.edward
    };

    if (v.chris)   counts.chris++;
    if (v.maggie)  counts.maggie++;
    if (v.allyson) counts.allyson++;
    if (v.edward)  counts.edward++;
  });

  // Then update DOM
  document.getElementById('count-chris').textContent = counts.chris;
  document.getElementById('count-maggie').textContent = counts.maggie;
  document.getElementById('count-allyson').textContent = counts.allyson;
  document.getElementById('count-edward').textContent = counts.edward;

  // Load and add GeoJSON
  const geoRes = await fetch('world.geojson');
  const geojson = await geoRes.json();

  countryLayer = L.geoJSON(geojson, {
    style: getStyle,

    onEachFeature: (feature, layer) => {
      const props = feature.properties;
      const name = props.ADMIN || props.NAME || 'Unknown';
      const code = (props.ADM0_A3 || '').trim().toUpperCase();

      layer.on('click', () => {
        const v = visitData[code] || { chris: false, maggie: false, allyson: false, edward: false };
        const content = `
          <b>${name}</b><br>
          Chris: ${v.chris ? 'yes' : 'no'}<br>
          Maggie: ${v.maggie ? 'yes' : 'no'}<br>
          Allyson: ${v.allyson ? 'yes' : 'no'}<br>
          Edward: ${v.edward ? 'yes' : 'no'}
        `;
        layer.bindPopup(content).openPopup();
      });
    }
  }).addTo(map);

  // Checkbox listeners
  ['chris', 'maggie', 'allyson', 'edward'].forEach(id => {
    document.getElementById(id).addEventListener('change', e => {
      selected[id] = e.target.checked;
      countryLayer.setStyle(getStyle);
    });
  });
});

function getStyle(feature) {
  const props = feature.properties;
  let code = (props.ADM0_A3 || '').trim().toUpperCase();

  const defaultStyle = { fillColor: '#f0f0f0', weight: 0.5, color: '#aaa', fillOpacity: 0.3 };

  if (!code || !visitData[code]) return defaultStyle;

  const v = visitData[code];
  let count = 0;
  if (selected.chris   && v.chris)   count++;
  if (selected.maggie  && v.maggie)  count++;
  if (selected.allyson && v.allyson) count++;
  if (selected.edward  && v.edward)  count++;

  if (count === 0) return defaultStyle;

  return {
    fillColor: '#ff6b6b',
    weight: 1,
    opacity: 1,
    color: 'white',
    fillOpacity: (count / 4) * 0.7 + 0.3
  };
}