/* Premier Admin — shared module.
   Auth, API client, PDF builder, R2 upload, share helpers.
   Works against a same-origin /api/* Worker (CF Access in prod) OR
   localhost:8787 in dev (ADMIN_TOKEN bearer fallback).
*/
(function (global) {
  const isLocal = ['localhost', '127.0.0.1'].includes(location.hostname);
  const API_BASE = (global.PREMIER_API
    || (isLocal ? 'http://localhost:8787' : '')
  ).replace(/\/$/, '');
  const TOKEN_KEY = 'premier_admin_token';
  const BRAIN_URL = '../assets/brain.json';

  // ---------- auth ---------------------------------------------------------
  const getToken   = () => localStorage.getItem(TOKEN_KEY) || '';
  const setToken   = (t) => localStorage.setItem(TOKEN_KEY, t || '');
  const clearToken = () => localStorage.removeItem(TOKEN_KEY);

  async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    const tok = getToken();
    if (tok) headers.Authorization = `Bearer ${tok}`;
    const r = await fetch(API_BASE + path, {
      ...opts,
      headers,
      credentials: 'include',          // sends CF Access cookie in prod
    });
    if (r.status === 401) {
      if (!location.pathname.endsWith('/login.html')) {
        const next = encodeURIComponent(location.pathname + location.search);
        location.href = 'login.html?next=' + next;
      }
      throw new Error('Auth required');
    }
    if (!r.ok) {
      const txt = await r.text().catch(() => '');
      throw new Error(`${r.status} ${txt || r.statusText}`);
    }
    return r.status === 204 ? null : r.json();
  }

  async function whoami() {
    try { return await api('/api/admin/me'); } catch { return null; }
  }

  // ---------- inventory (for auto-filling quote line items) ----------------
  let brainCache = null;
  async function loadBrain() {
    if (brainCache) return brainCache;
    try { brainCache = await (await fetch(BRAIN_URL)).json(); } catch { brainCache = { machines: [], company: {} }; }
    return brainCache;
  }

  // ---------- clients ------------------------------------------------------
  async function listClients()         { return (await api('/api/admin/clients')).clients || []; }
  async function getClient(id)         { return (await api('/api/admin/clients/' + id)).client; }
  async function createClient(data)    { return (await api('/api/admin/clients', { method:'POST', body: JSON.stringify(data) })).client; }
  async function updateClient(id, p)   { return (await api('/api/admin/clients/' + id, { method:'PUT', body: JSON.stringify(p) })).client; }
  async function deleteClient(id)      { return api('/api/admin/clients/' + id, { method: 'DELETE' }); }

  // ---------- documents ----------------------------------------------------
  async function listDocuments(filters = {}) {
    const qs = new URLSearchParams(filters).toString();
    return (await api('/api/admin/documents' + (qs ? '?' + qs : ''))).documents || [];
  }
  async function getDocument(id) { return (await api('/api/admin/documents/' + id)).document; }

  async function uploadDocument({ client_id, kind, title, amount_cents, payload, pdfBlob }) {
    const b64 = await blobToBase64(pdfBlob);
    const res = await api('/api/admin/documents', {
      method: 'POST',
      body: JSON.stringify({ client_id, kind, title, amount_cents, payload, pdf_b64: b64 }),
    });
    return res.document;
  }
  async function rotateShare(id) { return api('/api/admin/documents/' + id + '/rotate', { method: 'POST' }); }
  async function deleteDocument(id) { return api('/api/admin/documents/' + id, { method:'DELETE' }); }

  // ---------- dashboard + briefings ---------------------------------------
  async function getDashboard()      { return api('/api/admin/dashboard'); }
  async function runBriefing()       { return (await api('/api/admin/briefing/run', { method: 'POST' })).briefing; }
  async function listBriefingHistory() { return (await api('/api/admin/briefings')).briefings || []; }

  // ---------- voice + uploads --------------------------------------------
  async function listBookings()          { return (await api('/api/admin/bookings')).bookings || []; }
  async function updateBooking(id, body) { return (await api('/api/admin/bookings/' + id, { method:'PUT', body: JSON.stringify(body) })).booking; }
  async function listCalls()             { return (await api('/api/admin/calls')).calls || []; }
  async function getCall(id)             { return (await api('/api/admin/calls/' + id)).call; }
  async function listUploads(filters={}) {
    const qs = new URLSearchParams(filters).toString();
    return (await api('/api/admin/uploads' + (qs ? '?' + qs : ''))).uploads || [];
  }
  async function generateUploadLink(clientId)  { return api('/api/admin/clients/' + clientId + '/upload-link', { method:'POST' }); }
  async function rotateUploadLink(clientId)    { return api('/api/admin/clients/' + clientId + '/upload-link', { method:'DELETE' }); }
  function uploadFileUrl(uploadId) { return (API_BASE || '') + '/api/admin/uploads/' + uploadId + '/file'; }

  // tiny markdown → HTML (just bullets + line breaks; safe-escapes everything else)
  function mdToHTML(md) {
    const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const lines = String(md || '').split(/\r?\n/);
    let html = '', inList = false;
    for (const raw of lines) {
      const line = raw.trimEnd();
      if (/^[-*]\s+/.test(line)) {
        if (!inList) { html += '<ul>'; inList = true; }
        html += '<li>' + esc(line.replace(/^[-*]\s+/, '')) + '</li>';
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        if (line.trim() === '') html += '<div style="height:6px"></div>';
        else html += '<p>' + esc(line) + '</p>';
      }
    }
    if (inList) html += '</ul>';
    return html;
  }

  function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onloadend = () => resolve(String(r.result || '').split(',')[1] || '');
      r.onerror = reject;
      r.readAsDataURL(blob);
    });
  }

  // ---------- toast --------------------------------------------------------
  function toast(msg, ms = 2200) {
    let el = document.getElementById('toast');
    if (!el) { el = document.createElement('div'); el.id = 'toast'; document.body.appendChild(el); }
    el.textContent = msg; el.classList.add('show');
    clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove('show'), ms);
  }

  // ---------- share --------------------------------------------------------
  async function shareLink(url, label) {
    if (navigator.share) {
      try { await navigator.share({ url, title: label, text: (label || '') + '\n' + url }); return true; }
      catch (e) { /* user cancelled, fall through */ }
    }
    try { await navigator.clipboard.writeText(url); toast('Link copied to clipboard'); return true; }
    catch { toast('Could not copy — long-press to copy manually'); return false; }
  }

  // ---------- PDF builder (shared between quote/PO/BOL) -------------------
  // opts: { kind: 'quote'|'po'|'bol', number, client: {company, contact, email, phone, city, region},
  //         lines: [{d, p}], terms: [['Label','Value']], notes, totals: { showTotal }, headerLabel }
  function buildPDF(opts) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'pt', format: 'letter' });
    const W = 612, x = 54;
    const CO = (brainCache && brainCache.company) || {
      name: 'Premier Equipment LLC', city: 'Beachwood', region: 'OH', postal: '44122',
      phone: '(216) 593-7000', email: 'sales@buypremier.com', tagline: 'Your Plastics Machinery Source'
    };
    const headerLabel = opts.headerLabel || ({ quote:'QUOTE', po:'PURCHASE ORDER', bol:'BILL OF LADING' }[opts.kind] || 'DOCUMENT');

    // letterhead
    doc.setFillColor(12, 42, 42); doc.rect(0, 0, W, 96, 'F');
    doc.setFillColor(242, 106, 33); doc.rect(0, 96, W, 5, 'F');
    doc.setTextColor(255, 255, 255); doc.setFont('helvetica', 'bold'); doc.setFontSize(20);
    doc.text(CO.name.toUpperCase(), x, 52);
    doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(159, 189, 183);
    doc.text((CO.tagline || '').toUpperCase() + '   ·   ' + (CO.city || '') + ', ' + (CO.region || '') + ' ' + (CO.postal || ''), x, 70);
    doc.text((CO.phone || '') + '   ·   ' + (CO.email || ''), x, 84);

    doc.setTextColor(20, 33, 43); doc.setFont('helvetica', 'bold'); doc.setFontSize(22);
    doc.text(headerLabel, W - x, 52, { align: 'right' });
    doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(120, 130, 138);
    if (opts.number) doc.text('#' + opts.number, W - x, 68, { align: 'right' });
    doc.text(new Date().toLocaleDateString(), W - x, 82, { align: 'right' });

    // prepared for
    let y = 140;
    doc.setTextColor(27, 138, 122); doc.setFont('helvetica', 'bold'); doc.setFontSize(10);
    doc.text(opts.kind === 'bol' ? 'CONSIGNEE / SHIP TO' : 'PREPARED FOR', x, y);
    const c = opts.client || {};
    doc.setTextColor(20, 33, 43); doc.setFont('helvetica', 'normal'); doc.setFontSize(11);
    y += 18; doc.text((c.contact || c.company || '—') + (c.contact && c.company ? '  ·  ' + c.company : ''), x, y);
    if (c.city || c.region) { y += 14; doc.setFontSize(9); doc.setTextColor(82, 96, 107); doc.text([c.city, c.region].filter(Boolean).join(', '), x, y); }
    if (c.email || c.phone) { y += 13; doc.text([c.email, c.phone].filter(Boolean).join('  ·  '), x, y); }

    // line items table
    y += 30;
    doc.setFillColor(246, 249, 249); doc.rect(x, y - 14, W - 2*x, 24, 'F');
    doc.setTextColor(82, 96, 107); doc.setFont('helvetica', 'bold'); doc.setFontSize(9);
    doc.text('DESCRIPTION', x + 10, y + 2);
    if (opts.kind !== 'bol') doc.text('AMOUNT', W - x - 10, y + 2, { align: 'right' });

    y += 24; doc.setFont('helvetica', 'normal'); doc.setTextColor(20, 33, 43); doc.setFontSize(11);
    let total = 0;
    (opts.lines || []).forEach(l => {
      if (!l.d && !l.p) return;
      const amt = (parseFloat(l.p) || 0);
      total += amt;
      const text = doc.splitTextToSize(l.d || 'Item', W - 2*x - 130);
      doc.text(text, x + 10, y);
      if (opts.kind !== 'bol') doc.text(money(amt), W - x - 10, y, { align: 'right' });
      const lineHeight = 14 * Math.max(1, text.length);
      y += lineHeight + 8;
      doc.setDrawColor(231, 233, 236); doc.line(x, y - 8, W - x, y - 8);
    });

    // total
    if (opts.kind !== 'bol') {
      y += 6;
      doc.setFont('helvetica', 'bold'); doc.setFontSize(14); doc.setTextColor(19, 96, 85);
      doc.text('TOTAL', W - x - 130, y);
      doc.text(money(total), W - x - 10, y, { align: 'right' });
    }

    // terms
    if (opts.terms && opts.terms.length) {
      y += 36; doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.setTextColor(27, 138, 122);
      doc.text(opts.kind === 'bol' ? 'SHIPMENT DETAILS' : 'TERMS', x, y);
      y += 16; doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(82, 96, 107);
      opts.terms.forEach(t => { doc.text(t[0] + ': ' + (t[1] || '—'), x, y); y += 15; });
    }
    if (opts.notes) {
      y += 6; doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(82, 96, 107);
      doc.text(doc.splitTextToSize(opts.notes, W - 2*x), x, y);
    }

    // footer
    doc.setFontSize(8); doc.setTextColor(150, 160, 165);
    doc.text('Cargo insured in transit. All machines sold subject to prior sale. ' + (CO.name || '') + ' · ' + (CO.phone || ''), x, 756);

    return { blob: doc.output('blob'), total };
  }

  function money(n) { return '$' + (parseFloat(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

  // ---------- nav highlighter ---------------------------------------------
  function highlightNav() {
    const cur = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.adm-tabs a').forEach(a => {
      if ((a.getAttribute('href') || '').endsWith(cur)) a.classList.add('active');
    });
  }

  // ---------- whoami in header --------------------------------------------
  async function renderWhoami() {
    const el = document.querySelector('.adm-bar .who');
    if (!el) return;
    const me = await whoami();
    if (me && me.email) {
      el.innerHTML = me.email + ' <button onclick="Premier.logout()">log out</button>';
    } else {
      el.innerHTML = '<a href="login.html" style="color:#2FB8A3">sign in</a>';
    }
  }
  function logout() { clearToken(); location.href = 'login.html'; }

  // expose
  global.Premier = {
    API_BASE, isLocal,
    getToken, setToken, clearToken,
    api, whoami,
    listClients, getClient, createClient, updateClient, deleteClient,
    listDocuments, getDocument, uploadDocument, rotateShare, deleteDocument,
    getDashboard, runBriefing, listBriefingHistory, mdToHTML,
    listBookings, updateBooking, listCalls, getCall,
    listUploads, generateUploadLink, rotateUploadLink, uploadFileUrl,
    loadBrain, shareLink, toast, buildPDF, money,
    highlightNav, renderWhoami, logout,
  };

  document.addEventListener('DOMContentLoaded', () => { highlightNav(); renderWhoami(); });
})(window);
