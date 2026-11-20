/* Legal Wegal quotation layout (approved by Kunal 18 Nov 2026). Shared by the CRM (preview + PDF)
   and the public quote page. lwQuoteHtml(q) returns HTML; q uses the quote_public() field names. */
(function (w) {
  var UPI = 'cajuniorsknn@okaxis', PHONE = '+91 93700 77727';
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function rs(n) { return Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }); }
  function dt(d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''; }
  var CSS = '.lwq{font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1c1830;background:#fff;max-width:800px;margin:0 auto;padding:30px}' +
    '.lwq *{box-sizing:border-box}.lwq .top{display:flex;justify-content:space-between;gap:20px;border-bottom:3px solid #1d1250;padding-bottom:14px}' +
    '.lwq .logo{font-weight:800;font-size:22px;color:#1d1250}.lwq .logo b{background:#1d1250;color:#fff;border-radius:8px;padding:2px 7px;margin-right:6px}' +
    '.lwq .sm{color:#6b6880;font-size:12.5px}.lwq h1{font-size:20px;margin:0;color:#1d1250;text-align:right}.lwq .meta{text-align:right}' +
    '.lwq .two{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:16px 0}.lwq .box{background:#f7f5ff;border-radius:10px;padding:12px 14px}' +
    '.lwq .box h4{margin:0 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#6b6880}' +
    '.lwq table{width:100%;border-collapse:collapse;margin:8px 0}.lwq th,.lwq td{padding:9px 8px;border-bottom:1px solid #e6e3f2;text-align:left;vertical-align:top}' +
    '.lwq th{background:#1d1250;color:#fff;font-weight:600;font-size:12.5px}.lwq .r{text-align:right;white-space:nowrap}' +
    '.lwq .sec td{background:#f7f5ff;font-weight:700;color:#1d1250}.lwq .tot td{font-weight:800;font-size:16px;border-top:2px solid #1d1250;border-bottom:none}' +
    '.lwq .pay{border:1.5px dashed #3a1fa8;border-radius:12px;padding:14px;margin-top:14px}.lwq ul{margin:6px 0;padding-left:18px}' +
    '.lwq h3{margin:12px 0 4px;color:#1d1250;font-size:15px}.lwq .foot{margin-top:18px;border-top:1px solid #e6e3f2;padding-top:12px}' +
    '@media(max-width:600px){.lwq{padding:16px}.lwq .two,.lwq .top{display:block}.lwq .meta,.lwq h1{text-align:left;margin-top:10px}}';
  function lwQuoteHtml(q) {
    var items = q.items || [], fee = items.filter(function (i) { return i.section === 'fee'; }), govt = items.filter(function (i) { return i.section === 'govt'; });
    var n = 0, row = function (i) { n++; return '<tr><td>' + n + '</td><td>' + esc(i.desc) + '</td><td class="r">' + rs(i.amount) + '</td></tr>'; };
    var adv = Math.round(Number(q.total || 0) * Number(q.advance_pct == null ? 50 : q.advance_pct) / 100), bal = Number(q.total || 0) - adv;
    var h = '<style>' + CSS + '</style><div class="lwq">';
    h += '<div class="top"><div><div class="logo"><b>LW</b>Legal Wegal</div><div class="sm">' + PHONE + ' · legalwegal.com@gmail.com · www.legalwegal.com</div></div>' +
      '<div class="meta"><h1>QUOTATION</h1><div class="sm">No. <b>' + esc(q.quote_no || 'Draft') + '</b><br>Date: ' + dt(q.date || new Date()) + '<br>Valid till: <b>' + dt(q.valid_till) + '</b></div></div></div>';
    h += '<div class="two"><div class="box"><h4>Prepared for</h4><b>' + esc(q.client_name) + '</b><br>' + esc(q.client_phone_masked || '') +
      (q.lead_code || q.client_place ? '<br>' + esc([q.lead_code ? 'Lead ' + q.lead_code : '', q.client_place].filter(Boolean).join(' · ')) : '') + '</div>' +
      '<div class="box"><h4>Your expert</h4><b>' + esc(q.expert_name || 'Legal Wegal team') + '</b><br>WhatsApp ' + PHONE + '<br>Mon–Sat, 11 AM – 7 PM</div></div>';
    h += '<p><b>Service:</b> ' + esc(q.service) + (q.service_details ? ' (' + esc(q.service_details) + ')' : '') + '</p>';
    h += '<table><tr><th>#</th><th>Description</th><th class="r">Amount (₹)</th></tr>';
    if (fee.length) h += '<tr class="sec"><td colspan="3">A. Our professional fee</td></tr>' + fee.map(row).join('');
    if (Number(q.gst_amount) > 0) h += '<tr><td></td><td>GST @ ' + rs(q.gst_rate) + '% on professional fee</td><td class="r">' + rs(q.gst_amount) + '</td></tr>';
    if (govt.length) h += '<tr class="sec"><td colspan="3">B. Government &amp; third-party fees (at actuals, paid to the authority / vendor)</td></tr>' + govt.map(row).join('');
    h += '<tr class="tot"><td></td><td>Total payable</td><td class="r">₹' + rs(q.total) + '</td></tr></table>';
    if (govt.length) h += '<p class="sm">Section B is charged at actual cost with no mark-up. If an authority\'s fee changes before filing, we charge the actual amount and show you the receipt.</p>';
    h += '<div class="pay"><b>Pay ' + rs(q.advance_pct == null ? 50 : q.advance_pct) + '% advance (₹' + rs(adv) + ') to start' + (bal > 0 ? ' · balance ₹' + rs(bal) + ' before filing' : '') + '</b>' +
      '<div class="sm">UPI: <b>' + UPI + '</b> · Share the payment screenshot on WhatsApp · Receipt sent on WhatsApp</div></div>';
    var tl = q.timeline || [], dc = q.documents || [];
    if (tl.length || dc.length) h += '<div class="two">' + (tl.length ? '<div><h3>Timeline</h3><ul>' + tl.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>' : '<div></div>') +
      (dc.length ? '<div><h3>Documents needed</h3><ul>' + dc.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>' : '') + '</div>';
    if (q.notes) h += '<p><b>Note:</b> ' + esc(q.notes) + '</p>';
    h += '<div class="foot sm"><b>Terms.</b> Prices valid till the date above. Legal Wegal is a private facilitation provider and not a government body; approvals are issued by the respective authority and timelines depend on it. If work has not started, the professional fee is refundable; government fees once paid are not. Upload documents and track progress in your client portal: www.legalwegal.com/Login.</div></div>';
    return h;
  }
  w.lwQuoteHtml = lwQuoteHtml; w.lwQuoteUpi = UPI;
})(window);
