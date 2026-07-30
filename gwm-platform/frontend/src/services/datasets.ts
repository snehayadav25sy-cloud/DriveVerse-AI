import api from './api'

export const fetchDatasets = async () => {
  const res = await api.get('/datasets')
  return res.data
}

export const downloadDataset = (datasetId: string) => {
  // Construct the download URL and trigger a browser download
  const token = localStorage.getItem('token');
  const url = `${api.defaults.baseURL}/datasets/${datasetId}/download`;
  
  // We can't just use window.location.href because we need to pass the Authorization header.
  // Instead, we fetch the blob and trigger a download via a temporary link.
  fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  .then(res => res.blob())
  .then(blob => {
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `dataset_${datasetId.slice(0, 8)}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(blobUrl);
  })
  .catch(err => console.error("Download failed:", err));
}
