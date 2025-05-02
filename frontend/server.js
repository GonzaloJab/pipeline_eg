const express = require('express');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname, 'public')));

app.use(express.json());

// Health-check endpoint for the frontend
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

const API_URL = '/api';  // Connect to FastAPI service by service name

async function fetchTasks() {
  const res = await fetch(API_URL);
  return res.json();
}

async function deleteTask(index) {
  await fetch(`${API_URL}/${index}`, { method: 'DELETE' });
}

app.listen(3000, () => {
  console.log('Frontend service is running on port 3000');
});

module.exports = { fetchTasks, deleteTask };
