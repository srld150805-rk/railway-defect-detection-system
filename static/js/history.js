const rows = document.querySelector('#history-rows');
const table = document.querySelector('#history-table');
const empty = document.querySelector('#history-empty');
const message = document.querySelector('#history-message');

function addCell(row, value) {
  const cell = document.createElement('td');
  cell.textContent = value;
  row.append(cell);
  return cell;
}

async function loadHistory() {
  try {
    const response = await fetch('/api/history', { headers: { Accept: 'application/json' } });
    const payload = await response.json();
    if (!response.ok || payload.success !== true || !Array.isArray(payload.inspections)) {
      throw new Error('Inspection history is temporarily unavailable.');
    }

    const term = new URLSearchParams(window.location.search).get('q')?.trim();
    const inspections = payload.inspections.filter(item => !term || String(item.id) === term);
    rows.replaceChildren();
    for (const inspection of inspections) {
      const row = document.createElement('tr');
      const idCell = document.createElement('td');
      const link = document.createElement('a');
      link.href = `/inspection/${encodeURIComponent(inspection.id)}`;
      link.textContent = `INS-${String(inspection.id).padStart(4, '0')}`;
      idCell.append(link);
      row.append(idCell);

      const timestamp = new Date(inspection.inspected_at);
      addCell(row, Number.isNaN(timestamp.getTime()) ? 'Date unavailable' : timestamp.toLocaleString());
      const statusCell = document.createElement('td');
      const status = document.createElement('span');
      status.className = `status ${String(inspection.inspection_status).toLowerCase()}`;
      status.textContent = inspection.inspection_status;
      statusCell.append(status);
      row.append(statusCell);

      const detectionCell = document.createElement('td');
      if (inspection.detections.length) {
        inspection.detections.forEach((detection, index) => {
          if (index) detectionCell.append(document.createElement('br'));
          detectionCell.append(document.createTextNode(`${detection.defect_name} (${(detection.confidence * 100).toFixed(0)}%)`));
        });
      } else {
        detectionCell.textContent = 'No defects detected';
      }
      row.append(detectionCell);
      addCell(row, inspection.image_filename);

      const actionCell = document.createElement('td');
      const detailLink = document.createElement('a');
      detailLink.className = 'text-link';
      detailLink.href = `/inspection/${encodeURIComponent(inspection.id)}`;
      detailLink.textContent = 'Open';
      actionCell.append(detailLink);
      row.append(actionCell);
      rows.append(row);
    }
    const hasRecords = inspections.length > 0;
    table.classList.toggle('hidden', !hasRecords);
    empty.classList.toggle('hidden', hasRecords);
    message.textContent = '';
  } catch {
    message.textContent = 'Could not refresh inspection history. Showing any records already available.';
  }
}

loadHistory();
