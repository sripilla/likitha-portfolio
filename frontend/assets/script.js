// Contact form → FastAPI backend.
// Same-origin by default: since FastAPI serves this file itself, "/api/contact"
// resolves correctly whether the site runs on localhost or the production domain.

const form = document.getElementById('contact-form');
const statusEl = document.getElementById('form-status');
const submitBtn = document.getElementById('submit-btn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    name: document.getElementById('name').value.trim(),
    email: document.getElementById('email').value.trim(),
    message: document.getElementById('message').value.trim(),
    website: document.getElementById('website').value, // honeypot
  };

  if (payload.name.length < 2 || payload.message.length < 10) {
    setStatus('Please fill in all fields (message needs at least 10 characters).', 'error');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'sending...';
  setStatus('', '');

  try {
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.status === 429) {
      setStatus('Too many messages sent — please try again later.', 'error');
      return;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = Array.isArray(err.detail)
        ? err.detail.map((d) => d.msg).join(' ')
        : err.detail || 'Something went wrong. Please try again.';
      setStatus(detail, 'error');
      return;
    }

    const data = await res.json();
    setStatus(data.message || 'Message sent!', 'success');
    form.reset();
  } catch (err) {
    setStatus('Network error — please check your connection and try again.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'send_message()';
  }
});

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = 'form-status mono' + (kind ? ' ' + kind : '');
}
