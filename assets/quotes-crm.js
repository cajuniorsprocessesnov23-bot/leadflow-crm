/* CRM quotes (18–19 Nov 2026). Staff build a quote from a lead and submit it; only the Super Admin
   approves. Approval makes the PDF, uploads it to the "quotes" bucket and calls approve_quote(), which
   queues WhatsApp template lw_c_quote to the client. Uses globals from index.html:
   supabaseClient, leads, leadTypeOptions, currentUser, toolModal, esc, $. */
(function () {
  var SITE = 'https://www.legalwegal.com';
  var ST = { draft: ['Draft', ''], pending_approval: ['Waiting for approval', 'amber'], rejected: ['Sent back', 'red'], approved: ['Approved', 'green'],
    sent: ['Sent to client', 'green'], accepted: ['Accepted by client', 'green'], cancelled: ['Cancelled', ''] };
  var isSA = function () { return typeof currentUser !== 'undefined' && currentUser && currentUser.role === 'super_admin'; };
  var rs = function (n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); };
  var pill = function (s) { var x = ST[s] || [s, '']; return '<span class="pill ' + x[1] + '">' + x[0] + '</span>'; };
  var lines = function (t) { return String(t || '').split('\n').map(function (x) { return x.trim(); }).filter(Boolean); };
  var masked = function (p) { var d = String(p || '').replace(/\D/g, '').slice(-10); return d ? '+91 ' + d.slice(0, 2) + 'XXX XX' + d.slice(-3) : ''; };
  var draft = null;

  window.renderHistQuotes = async function (l) {
    var box = $('histQuotes'); if (!box) return;
    box.innerHTML = '<div class="small">Loading quotes…</div>';
    var r = await supabaseClient.from('quotes').select('id,quote_no,service,total,status,created_at,review_note,viewed_at,public_token').eq('lead_id', String(l.id)).order('created_at', { ascending: false });
    var rows = r.data || [];
    box.innerHTML = '<div style="display:flex;align-items:center;gap:8px;margin:14px 0 6px"><h3 style="margin:0">Quotes (' + rows.length + ')</h3>' +
      '<button type="button" style="margin-left:auto" onclick="openQuoteEditor(\'' + esc(l.id) + '\')">＋ New quote</button></div>' +
      (rows.length ? rows.map(function (q) {
        var edit = ['draft', 'rejected', 'pending_approval'].indexOf(q.status) >= 0;
        return '<div class="small" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 0;border-top:1px solid var(--line)"><b>' + esc(q.quote_no) + '</b> ' + esc(q.service) + ' · ' + rs(q.total) + ' ' + pill(q.status) +
          (q.viewed_at ? ' <span>Opened by client</span>' : '') + (q.review_note && q.status === 'rejected' ? ' <i>' + esc(q.review_note) + '</i>' : '') +
          '<span style="margin-left:auto;display:flex;gap:6px">' + (edit ? '<button type="button" class="secondary" onclick="openQuoteEditor(\'' + esc(l.id) + '\',\'' + q.id + '\')">Open</button>' : '<a class="btn secondary" target="_blank" rel="noopener" href="' + SITE + '/quote/?t=' + q.public_token + '">View</a>') +
          (isSA() && q.status === 'pending_approval' ? '<button type="button" onclick="openQuoteReview(\'' + q.id + '\')">Review</button>' : '') + '</span></div>';
      }).join('') : '<div class="small">No quotes yet.</div>');
  };

  function opt(name) { return (leadTypeOptions || []).find(function (o) { return o.name === name; }) || {}; }
  function prefill(svc) {
    var o = opt(svc), it = [];
    if (o.professional_fee != null) it.push({ section: 'fee', desc: svc, amount: Number(o.professional_fee) });
    if (Number(o.govt_fee) > 0) it.push({ section: 'govt', desc: 'Government fees for ' + svc + (o.price_note ? ' (' + o.price_note + ')' : ''), amount: Number(o.govt_fee) });
    if (!it.length) it.push({ section: 'fee', desc: svc, amount: 0 });
    return { items: it, timeline: o.timeline ? [o.timeline] : [] };
  }

  window.openQuoteEditor = async function (leadId, quoteId) {
    var l = leads.find(function (x) { return String(x.id) === String(leadId); }); if (!l) return;
    if (quoteId) {
      var r = await supabaseClient.from('quotes').select('*').eq('id', quoteId).single();
      if (r.error) return alert(r.error.message); draft = r.data;
    } else {
      var svc = (l.leadTypes || [])[0] || ((leadTypeOptions || [])[0] || {}).name || '';
      var p = prefill(svc);
      draft = { lead_id: String(l.id), client_name: l.name || '', client_phone: l.phone || '', client_place: '', service: svc, service_details: '',
        items: p.items, gst_rate: 0, advance_pct: 50, timeline: p.timeline, documents: [], notes: '', expert_name: currentUser.name || '',
        valid_till: new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10), status: 'draft' };
    }
    draft._lead = l; drawEditor();
  };

  function drawEditor() {
    var q = draft, svcOpts = (leadTypeOptions || []).map(function (o) { return '<option' + (o.name === q.service ? ' selected' : '') + '>' + esc(o.name) + '</option>'; }).join('');
    var rows = (q.items || []).map(function (i, k) {
      return '<tr><td><select data-k="section" data-i="' + k + '"><option value="fee"' + (i.section === 'fee' ? ' selected' : '') + '>Our fee</option><option value="govt"' + (i.section === 'govt' ? ' selected' : '') + '>Govt / third-party</option></select></td>' +
        '<td><input data-k="desc" data-i="' + k + '" value="' + esc(i.desc) + '" style="width:100%"></td><td><input type="number" min="0" data-k="amount" data-i="' + k + '" value="' + Number(i.amount || 0) + '" style="width:100px"></td>' +
        '<td><button type="button" class="secondary" onclick="qRemoveRow(' + k + ')">✕</button></td></tr>';
    }).join('');
    var back = q.status === 'rejected' && q.review_note ? '<div class="small" style="background:#fdecea;padding:8px;border-radius:8px">Sent back by Super Admin: <b>' + esc(q.review_note) + '</b></div>' : '';
    toolModal('<h2 style="margin-top:0">' + (q.quote_no ? 'Quote ' + esc(q.quote_no) : 'New quote') + ' – ' + esc(q._lead.name) + ' ' + (q.status ? pill(q.status) : '') + '</h2>' + back +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><label>Service<select id="qSvc" onchange="qService(this.value)">' + svcOpts + '</select></label>' +
      '<label>Details (shown after service name)<input id="qDet" value="' + esc(q.service_details) + '" placeholder="2 directors, ₹1 lakh capital, Maharashtra"></label>' +
      '<label>Client name<input id="qName" value="' + esc(q.client_name) + '"></label><label>City / state<input id="qPlace" value="' + esc(q.client_place) + '"></label>' +
      '<label>Advance %<input id="qAdv" type="number" min="0" max="100" value="' + Number(q.advance_pct) + '"></label><label>Valid till<input id="qValid" type="date" value="' + esc(q.valid_till) + '"></label>' +
      '<label>Expert name on quote<input id="qExp" value="' + esc(q.expert_name) + '"></label><label>GST % on our fee (0 = not registered)<input id="qGst" type="number" min="0" value="' + Number(q.gst_rate || 0) + '"></label></div>' +
      '<h3>Line items</h3><table style="width:100%"><thead><tr><th>Type</th><th>Description</th><th>₹</th><th></th></tr></thead><tbody id="qRows">' + rows + '</tbody></table>' +
      '<div class="actions" style="justify-content:flex-start"><button type="button" class="secondary" onclick="qAddRow(\'fee\')">＋ Our fee line</button><button type="button" class="secondary" onclick="qAddRow(\'govt\')">＋ Govt fee line</button></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><label>Timeline (one per line)<textarea id="qTl" rows="4">' + esc((q.timeline || []).join('\n')) + '</textarea></label>' +
      '<label>Documents needed (one per line)<textarea id="qDocs" rows="4">' + esc((q.documents || []).join('\n')) + '</textarea></label></div>' +
      '<label>Note for client (optional)<input id="qNotes" value="' + esc(q.notes) + '"></label>' +
      '<div class="actions"><button type="button" class="secondary" onclick="qPreview()">Preview</button><button type="button" class="secondary" onclick="qSave(\'draft\')">Save draft</button>' +
      '<button type="button" onclick="qSave(\'pending_approval\')">Submit for approval</button></div><div id="qMsg" class="small"></div><div id="qPrev" style="border:1px solid var(--line);border-radius:12px;margin-top:10px;display:none;overflow:auto"></div>');
    $('qRows').addEventListener('input', function (e) {
      var t = e.target, i = +t.dataset.i; if (isNaN(i)) return;
      draft.items[i][t.dataset.k] = t.dataset.k === 'amount' ? Number(t.value || 0) : t.value;
    });
    $('qRows').addEventListener('change', function (e) { var t = e.target; if (t.dataset.k === 'section') draft.items[+t.dataset.i].section = t.value; });
  }
  function read() {
    var q = draft;
    q.service = $('qSvc').value; q.service_details = $('qDet').value.trim(); q.client_name = $('qName').value.trim(); q.client_place = $('qPlace').value.trim();
    q.advance_pct = Number($('qAdv').value || 0); q.valid_till = $('qValid').value; q.expert_name = $('qExp').value.trim(); q.gst_rate = Number($('qGst').value || 0);
    q.timeline = lines($('qTl').value); q.documents = lines($('qDocs').value); q.notes = $('qNotes').value.trim();
    q.items = (q.items || []).filter(function (i) { return String(i.desc || '').trim(); }).map(function (i) { return { section: i.section, desc: String(i.desc).trim(), amount: Number(i.amount || 0) }; });
    return q;
  }
  function totals(q) {
    var f = 0, g = 0; (q.items || []).forEach(function (i) { if (i.section === 'fee') f += Number(i.amount || 0); else g += Number(i.amount || 0); });
    var gst = Math.round(f * Number(q.gst_rate || 0)) / 100; return { fee_total: f, govt_total: g, gst_amount: gst, total: f + g + gst };
  }
  window.qService = function (svc) { read(); var p = prefill(svc); draft.service = svc; draft.items = p.items; if (p.timeline.length) draft.timeline = p.timeline; drawEditor(); };
  window.qAddRow = function (s) { read(); draft.items.push({ section: s, desc: '', amount: 0 }); drawEditor(); };
  window.qRemoveRow = function (k) { read(); draft.items.splice(k, 1); drawEditor(); };
  window.qPreview = function () {
    var q = read(), t = totals(q), box = $('qPrev');
    box.style.display = ''; box.innerHTML = lwQuoteHtml(Object.assign({}, q, t, { client_phone_masked: masked(q.client_phone), lead_code: q._lead.leadCode, date: new Date() }));
  };
  window.qSave = async function (status) {
    var q = read();
    if (!q.items.length) return ($('qMsg').textContent = 'Add at least one line item.');
    if (!q.valid_till) return ($('qMsg').textContent = 'Choose a valid-till date.');
    var row = { lead_id: q.lead_id, client_name: q.client_name, client_phone: q.client_phone, client_place: q.client_place, service: q.service, service_details: q.service_details,
      items: q.items, gst_rate: q.gst_rate, advance_pct: q.advance_pct, timeline: q.timeline, documents: q.documents, notes: q.notes, expert_name: q.expert_name,
      valid_till: q.valid_till, status: status };
    $('qMsg').textContent = 'Saving…';
    var r = q.id ? await supabaseClient.from('quotes').update(row).eq('id', q.id).select('id,quote_no').single()
                 : await supabaseClient.from('quotes').insert(row).select('id,quote_no').single();
    if (r.error) return ($('qMsg').textContent = r.error.message);
    draft.id = r.data.id; draft.quote_no = r.data.quote_no; draft.status = status;
    $('qMsg').textContent = status === 'pending_approval' ? 'Submitted. The Super Admin will review it before anything is sent.' : 'Draft saved.';
    window.renderHistQuotes(q._lead); refreshBadge();
    if (status === 'pending_approval') setTimeout(function () { var m = $('toolModal'); if (m) m.classList.remove('show'); }, 900);
  };

  // Super Admin: review list, approve (PDF + WhatsApp) or send back.
  window.openQuoteApprovals = async function () {
    var r = await supabaseClient.from('quotes').select('id,quote_no,client_name,service,total,status,created_at,submitted_at,lead_id').in('status', isSA() ? ['pending_approval'] : ['pending_approval', 'rejected']).order('submitted_at', { ascending: true });
    var rows = r.data || [];
    toolModal('<h2 style="margin-top:0">Quotes ' + (isSA() ? 'waiting for your approval' : 'waiting / sent back') + ' (' + rows.length + ')</h2>' +
      (rows.length ? rows.map(function (q) {
        return '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 0;border-top:1px solid var(--line)"><b>' + esc(q.quote_no) + '</b> ' + esc(q.client_name) + ' · ' + esc(q.service) + ' · ' + rs(q.total) + ' ' + pill(q.status) +
          '<span style="margin-left:auto">' + (isSA() ? '<button type="button" onclick="openQuoteReview(\'' + q.id + '\')">Review</button>' : '<button type="button" class="secondary" onclick="openQuoteEditor(\'' + esc(q.lead_id) + '\',\'' + q.id + '\')">Open</button>') + '</span></div>';
      }).join('') : '<p class="small">Nothing waiting.</p>'));
  };
  window.openQuoteReview = async function (id) {
    var r = await supabaseClient.from('quotes').select('*').eq('id', id).single(); if (r.error) return alert(r.error.message);
    var q = r.data, l = leads.find(function (x) { return String(x.id) === String(q.lead_id); }) || {};
    window._qReview = q;
    toolModal('<h2 style="margin-top:0">Review ' + esc(q.quote_no) + ' ' + pill(q.status) + '</h2><p class="small">Approving creates the PDF and sends it to ' + esc(q.client_name) + ' on WhatsApp (' + esc(q.client_phone) + ')' +
      (l.whatsappOptIn === false ? ' — <b>this client has WhatsApp updates OFF, so nothing will be sent automatically</b>' : '') + '.</p>' +
      '<div id="qRevBody" style="border:1px solid var(--line);border-radius:12px;overflow:auto">' + lwQuoteHtml(Object.assign({}, q, { client_phone_masked: masked(q.client_phone), lead_code: l.leadCode, date: new Date() })) + '</div>' +
      '<label>Note if sending back<input id="qRevNote" placeholder="e.g. add stamp duty for Karnataka"></label>' +
      '<div class="actions"><button type="button" class="secondary" onclick="qReturn()">Send back to staff</button><button type="button" onclick="qApprove()">Approve &amp; send to client</button></div><div id="qRevMsg" class="small"></div>');
  };
  window.qReturn = async function () {
    var note = $('qRevNote').value.trim(); if (!note) return ($('qRevMsg').textContent = 'Write what to change.');
    var r = await supabaseClient.rpc('return_quote', { p_id: window._qReview.id, p_note: note });
    $('qRevMsg').textContent = r.error ? r.error.message : 'Sent back.'; refreshBadge();
  };
  function loadPdfLib() {
    return window.html2pdf ? Promise.resolve() : new Promise(function (ok, bad) {
      var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/html2pdf.js@0.10.2/dist/html2pdf.bundle.min.js'; s.onload = ok; s.onerror = bad; document.head.appendChild(s);
    });
  }
  window.qApprove = async function () {
    var q = window._qReview, msg = $('qRevMsg'), url = '';
    if (!confirm('Approve ' + q.quote_no + ' and send it to ' + q.client_name + '?')) return;
    msg.textContent = 'Creating PDF…';
    try {
      await loadPdfLib();
      var holder = document.createElement('div'); holder.style.cssText = 'position:fixed;left:-10000px;top:0;width:800px;background:#fff';
      holder.innerHTML = $('qRevBody').innerHTML; document.body.appendChild(holder);
      var blob = await html2pdf().set({ margin: [8, 8, 8, 8], filename: q.quote_no + '.pdf', image: { type: 'jpeg', quality: 0.95 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4' } }).from(holder.firstElementChild.nextElementSibling || holder).outputPdf('blob');
      holder.remove();
      var path = q.public_token + '/' + q.quote_no + '.pdf';
      var up = await supabaseClient.storage.from('quotes').upload(path, blob, { contentType: 'application/pdf', upsert: true });
      if (up.error) throw up.error;
      url = supabaseClient.storage.from('quotes').getPublicUrl(path).data.publicUrl;
    } catch (e) { msg.textContent = 'PDF could not be created (' + (e.message || e) + '). Approving without PDF; the client still gets the quote link.'; }
    var r = await supabaseClient.rpc('approve_quote', { p_id: q.id, p_pdf_url: url });
    if (r.error) return (msg.textContent = r.error.message);
    msg.innerHTML = 'Approved. ' + (r.data && r.data.whatsapp ? 'WhatsApp queued to the client.' : 'Client has WhatsApp off — share the link yourself: ') +
      ' <a target="_blank" rel="noopener" href="' + SITE + '/quote/?t=' + q.public_token + '">' + SITE + '/quote/?t=' + q.public_token + '</a>';
    refreshBadge(); var l = leads.find(function (x) { return String(x.id) === String(q.lead_id); }); if (l && typeof histLeadId !== 'undefined' && histLeadId === String(l.id)) window.renderHistQuotes(l);
  };

  // Header button with a count of quotes waiting for the Super Admin.
  async function refreshBadge() {
    var b = document.getElementById('quotesBtn'); if (!b || typeof supabaseClient === 'undefined') return;
    var r = await supabaseClient.from('quotes').select('id', { count: 'exact', head: true }).eq('status', isSA() ? 'pending_approval' : 'rejected');
    var n = r.count || 0; b.textContent = '🧾 Quotes' + (n ? ' (' + n + (isSA() ? ' to approve' : ' sent back') + ')' : '');
  }
  window.refreshQuotesBadge = refreshBadge;
  function addButton() {
    if (document.getElementById('quotesBtn')) return;
    var settings = [].slice.call(document.querySelectorAll('button')).find(function (b) { return /Settings/.test(b.textContent) && /openSettings/.test(b.getAttribute('onclick') || ''); });
    if (!settings) return;
    var b = document.createElement('button'); b.id = 'quotesBtn'; b.type = 'button'; b.textContent = '🧾 Quotes'; b.onclick = window.openQuoteApprovals;
    settings.parentNode.insertBefore(b, settings); refreshBadge();
  }
  var tries = 0, t = setInterval(function () { if (typeof currentUser !== 'undefined' && currentUser && currentUser.id) { addButton(); clearInterval(t); setInterval(refreshBadge, 60000); } if (++tries > 120) clearInterval(t); }, 1000);
})();
