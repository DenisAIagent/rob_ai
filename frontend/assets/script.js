async function analyze(description) {
  const resp = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description })
  });
  if (!resp.ok) throw new Error('Analyze failed');
  return resp.json();
}

async function generate(projectName, description) {
  const resp = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_name: projectName, description })
  });
  if (!resp.ok) throw new Error('Generate failed');
  return resp.json();
}

document.getElementById('generate-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const projectName = document.getElementById('project-name').value;
  const description = document.getElementById('description').value;
  document.getElementById('analysis').textContent = '';
  document.getElementById('progress-bar').value = 0;
  document.getElementById('logs').textContent = '';
  document.getElementById('download-link').style.display = 'none';
  try {
    const analysis = await analyze(description);
    document.getElementById('analysis').textContent = `Type: ${analysis.project_type}, Suggestions: ${analysis.suggestions.join(', ')}`;
    const gen = await generate(projectName, description);
    const jobId = gen.job_id;
    const wsProtocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${wsProtocol}://${location.host}/ws/logs/${jobId}`);
    ws.onmessage = (ev) => {
      const logs = document.getElementById('logs');
      logs.textContent += ev.data;
      logs.scrollTop = logs.scrollHeight;
    };
    const interval = setInterval(async () => {
      const resp = await fetch(`/api/status/${jobId}`);
      const data = await resp.json();
      if (data.status === 'completed') {
        clearInterval(interval);
        ws.close();
        document.getElementById('progress-bar').value = 100;
        document.getElementById('download-link').href = `/api/download/${jobId}`;
        document.getElementById('download-link').style.display = 'block';
      } else if (data.status === 'error') {
        clearInterval(interval);
        ws.close();
        alert('Generation failed');
      }
    }, 1000);
  } catch (err) {
    alert(err.message);
  }
});
