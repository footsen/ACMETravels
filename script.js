let map;
let countryLayer;
let visitData = {};
let selected = { chris: true, maggie: true, allyson: true, edward: true };

document.addEventListener('DOMContentLoaded', async () => {
map = L.map('map', {
  worldCopyJump: false,
  noWrap: true,
  maxBounds: [[-85, -180], [85, 180]],
  maxBoundsViscosity: 1.0
}).setView([100, 0], 2);

L.tileLayer('https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19,
  noWrap: false
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
  });

  // Load and add GeoJSON
  const geoRes = await fetch('world.geojson');
  const geojson = await geoRes.json();

countryLayer = L.geoJSON(geojson, {
  style: getStyle,
//  onEachFeature: (feature, layer) => {
//    layer.bindTooltip((feature.properties.ADMIN || feature.properties.NAME || 'Unknown').trim());
//  }
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
    fillOpacity: (count / 4) + 0.3
  };
}