// WSL NAT helper: send one HTTP request from Windows to its loopback 9Router.
// Reads the request from stdin; writes only the API response to stdout.
let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', value => raw += value);
process.stdin.on('end', async () => {
  try {
    const req = JSON.parse(raw);
    const response = await fetch(req.url, {method: 'POST', headers: req.headers,
      body: JSON.stringify(req.payload), signal: AbortSignal.timeout(90000)});
    const body = await response.text();
    if (!response.ok) throw new Error(`9Router HTTP ${response.status}: ${body}`);
    process.stdout.write(body);
  } catch (error) {
    process.stderr.write(error.message);
    process.exitCode = 1;
  }
});
