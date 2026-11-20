/* CRM: B2B partners, commission rules, payouts and client referral payouts (Admins / Super Admin).
   Uses globals from index.html: supabaseClient, toolModal, esc, $, currentUser, leadTypeOptions. */
(function () {
  var rs = function (n) { return '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }); };
  var dt = function (d) { return d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''; };
  var isAdmin = function () { return typeof currentUser !== 'undefined' && currentUser && ['admin', 'super_admin'].indexOf(currentUser.role) >= 0; };
  var PILL = { pending: 'amber', active: 'green', paused: '', rejected: 'red', joined: '', payable: 'amber', paid: 'green', cancelled: 'red', approved: 'amber', reversed: 'red' };
  var pill = function (s) { return '<span class="pill ' + (PILL[s] || '') + '">' + esc(s) + '</span>'; };
  var tab = 'partners';

  window.openPartners = async function (t) {
    if (!isAdmin()) return alert('Admins only.');
    tab = t || tab;
    var head = '<h2 style="margin-top:0">Partners & referrals</h2><div style="display:flex;gap:6px;margin-bottom:10px">' +
      ['partners', 'rules', 'referrals'].map(function (k) { return '<button type="button" class="' + (k === tab ? '' : 'secondary') + '" onclick="openPartners(\'' + k + '\')">' + { partners: 'Partners & payouts', rules: 'Commission rules', referrals: 'Client referrals' }[k] + '</button>'; }).join('') + '</div><div id="ptBody">Loading…</div>';
    toolModal(head);
    try { await ({ partners: drawPartners, rules: drawRules, referrals: drawReferrals })[tab](); }
    catch (e) { $('ptBody').innerHTML = '<p class="small">' + esc(e.message || e) + '</p>'; }
  };

  async function drawPartners() {
    var p = await supabaseClient.from('partners').select('id,code,firm_name,contact_name,phone,email,city,pan,upi_id,model,status,created_at').order('created_at', { ascending: false });
    if (p.error) throw p.error;
    var c = await supabaseClient.from('partner_commissions').select('partner_id,net,status');
    var l = await supabaseClient.from('leads').select('partner_id').not('partner_id', 'is', null);
    var tot = {}; (c.data || []).forEach(function (x) { var t = tot[x.partner_id] = tot[x.partner_id] || { payable: 0, paid: 0 }; if (x.status === 'approved') t.payable += Number(x.net); if (x.status === 'paid') t.paid += Number(x.net); });
    var cnt = {}; (l.data || []).forEach(function (x) { cnt[x.partner_id] = (cnt[x.partner_id] || 0) + 1; });
    var rows = p.data || [];
    $('ptBody').innerHTML = '<p class="small">Partners sign up at <b>legalwegal.com/partners</b>. Approve to give them a code (LWP-0001) and referral link. Commission is created automatically when their client pays, on our fee only.</p>' +
      (rows.length ? '<div style="overflow:auto"><table style="width:100%;font-size:13px"><tr><th>Partner</th><th>Contact</th><th>Status</th><th>Clients</th><th>Payable</th><th>Paid</th><th></th></tr>' + rows.map(function (r) {
        var t = tot[r.id] || { payable: 0, paid: 0 };
        var act = r.status === 'active' ? '<button type="button" class="secondary" onclick="ptStatus(\'' + r.id + '\',\'paused\')">Pause</button>'
          : '<button type="button" onclick="ptStatus(\'' + r.id + '\',\'active\')">Approve</button>' + (r.status === 'pending' ? ' <button type="button" class="secondary" onclick="ptStatus(\'' + r.id + '\',\'rejected\')">Reject</button>' : '');
        return '<tr><td><b>' + esc(r.firm_name) + '</b><br><small>' + esc(r.code || 'no code yet') + ' · ' + (r.model === 'reseller' ? 'Reseller' : 'Referral') + ' · ' + esc(r.city || '') + '</small></td>' +
          '<td>' + esc(r.contact_name) + '<br><small>' + esc(r.phone) + (r.email ? ' · ' + esc(r.email) : '') + '<br>PAN ' + (r.pan ? esc(r.pan) : '<b>missing (20% TDS)</b>') + ' · UPI ' + esc(r.upi_id || '-') + '</small></td>' +
          '<td>' + pill(r.status) + '<br><small>since ' + dt(r.created_at) + '</small></td><td>' + (cnt[r.id] || 0) + '</td><td><b>' + rs(t.payable) + '</b></td><td>' + rs(t.paid) + '</td>' +
          '<td style="white-space:nowrap">' + act + (t.payable > 0 ? ' <button type="button" onclick="ptPay(\'' + r.id + '\',' + t.payable + ',\'' + esc(r.upi_id || '') + '\')">Mark paid</button>' : '') + '</td></tr>';
      }).join('') + '</table></div>' : '<p class="small">No partner sign-ups yet.</p>') + '<div id="ptMsg" class="small"></div>';
  }
  window.ptStatus = async function (id, st) {
    if (st !== 'active' && !confirm('Set this partner to ' + st + '?')) return;
    var r = await supabaseClient.rpc('admin_set_partner_status', { p_id: id, p_status: st });
    if (r.error) return alert(r.error.message);
    if (st === 'active') alert('Approved. Partner code: ' + r.data + '\nTheir link: https://www.legalwegal.com/?ref=' + r.data);
    window.openPartners('partners');
  };
  window.ptPay = async function (id, amt, upi) {
    var ref = prompt('Pay ' + rs(amt) + (upi ? ' to UPI ' + upi : '') + ', then enter the UPI / bank reference (UTR):');
    if (!ref) return;
    var r = await supabaseClient.rpc('admin_mark_commissions_paid', { p_partner: id, p_ref: ref });
    if (r.error) return alert(r.error.message);
    alert(r.data + ' commission(s) marked paid.'); window.openPartners('partners');
  };

  async function drawRules() {
    var r = await supabaseClient.from('partner_commission_rules').select('id,partner_id,service,kind,value,active').order('created_at');
    if (r.error) throw r.error;
    var p = await supabaseClient.from('partners').select('id,firm_name,code').order('firm_name');
    var pn = {}; (p.data || []).forEach(function (x) { pn[x.id] = x.firm_name + (x.code ? ' (' + x.code + ')' : ''); });
    var svc = (typeof leadTypeOptions !== 'undefined' ? leadTypeOptions : []).filter(function (o) { return o.active !== false; }).map(function (o) { return o.name; });
    $('ptBody').innerHTML = '<p class="small">The most specific rule wins: a partner + service rule beats a partner rule, which beats the default for everyone. Commission is on our professional fee only.</p>' +
      '<table style="width:100%;font-size:13px"><tr><th>Who</th><th>Service</th><th>Commission</th><th>Active</th><th></th></tr>' + (r.data || []).map(function (x) {
        return '<tr><td>' + (x.partner_id ? esc(pn[x.partner_id] || 'partner') : '<b>All partners (default)</b>') + '</td><td>' + (x.service === '*' ? 'All services' : esc(x.service)) + '</td><td>' + (x.kind === 'percent' ? Number(x.value) + '% of our fee' : rs(x.value) + ' flat') + '</td><td>' + (x.active ? 'Yes' : 'No') +
          '</td><td><button type="button" class="secondary" onclick="ptRuleToggle(\'' + x.id + '\',' + !x.active + ')">' + (x.active ? 'Turn off' : 'Turn on') + '</button></td></tr>';
      }).join('') + '</table><h3>Add a rule</h3><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">' +
      '<label>Who<select id="rWho"><option value="">All partners</option>' + (p.data || []).map(function (x) { return '<option value="' + x.id + '">' + esc(pn[x.id]) + '</option>'; }).join('') + '</select></label>' +
      '<label>Service<select id="rSvc"><option value="*">All services</option>' + svc.map(function (s) { return '<option>' + esc(s) + '</option>'; }).join('') + '</select></label>' +
      '<label>Type<select id="rKind"><option value="percent">% of our fee</option><option value="flat">Flat ₹</option></select></label><label>Value<input id="rVal" type="number" min="0" value="20"></label></div>' +
      '<div class="actions"><button type="button" onclick="ptRuleAdd()">Save rule</button></div><div id="ptMsg" class="small"></div>';
  }
  window.ptRuleAdd = async function () {
    var row = { partner_id: $('rWho').value || null, service: $('rSvc').value, kind: $('rKind').value, value: Number($('rVal').value || 0), active: true };
    var ex = supabaseClient.from('partner_commission_rules').select('id').eq('service', row.service);
    ex = row.partner_id ? ex.eq('partner_id', row.partner_id) : ex.is('partner_id', null);
    var e = await ex.maybeSingle();
    var r = e.data ? await supabaseClient.from('partner_commission_rules').update({ kind: row.kind, value: row.value, active: true }).eq('id', e.data.id)
                   : await supabaseClient.from('partner_commission_rules').insert(row);
    if (r.error) return ($('ptMsg').textContent = r.error.message);
    window.openPartners('rules');
  };
  window.ptRuleToggle = async function (id, on) {
    var r = await supabaseClient.from('partner_commission_rules').update({ active: on }).eq('id', id);
    if (r.error) return alert(r.error.message); window.openPartners('rules');
  };

  async function drawReferrals() {
    var r = await supabaseClient.from('referrals').select('id,code,referrer_phone10,referred_lead_id,status,reward_amount,referrer_upi,payout_ref,paid_at,created_at').order('created_at', { ascending: false });
    if (r.error) throw r.error;
    var ids = (r.data || []).map(function (x) { return x.referred_lead_id; });
    var names = {};
    if (ids.length) { var l = await supabaseClient.from('leads').select('id,name,lead_code').in('id', ids); (l.data || []).forEach(function (x) { names[x.id] = x.name + (x.lead_code ? ' (' + x.lead_code + ')' : ''); }); }
    $('ptBody').innerHTML = '<p class="small">Clients share their code (LWR-last 6 digits of mobile) from the client portal. When the friend makes their first payment, the reward (10% of our fee) becomes payable to the client\'s UPI.</p>' +
      ((r.data || []).length ? '<table style="width:100%;font-size:13px"><tr><th>Referrer</th><th>Friend</th><th>Status</th><th>Reward</th><th>UPI</th><th></th></tr>' + r.data.map(function (x) {
        return '<tr><td>' + esc(x.code) + '<br><small>' + esc(x.referrer_phone10) + '</small></td><td>' + esc(names[x.referred_lead_id] || x.referred_lead_id) + '<br><small>' + dt(x.created_at) + '</small></td><td>' + pill(x.status) + (x.payout_ref ? '<br><small>UTR ' + esc(x.payout_ref) + '</small>' : '') + '</td><td>' + (x.reward_amount ? rs(x.reward_amount) : '-') + '</td><td>' + esc(x.referrer_upi || 'not given yet') + '</td>' +
          '<td>' + (x.status === 'payable' ? '<button type="button" onclick="ptRefPay(\'' + x.id + '\',' + Number(x.reward_amount || 0) + ',\'' + esc(x.referrer_upi || '') + '\')">Mark paid</button>' : '') + '</td></tr>';
      }).join('') + '</table>' : '<p class="small">No client referrals yet.</p>');
  }
  window.ptRefPay = async function (id, amt, upi) {
    if (!upi) return alert('The client has not added a UPI ID yet. Ask them to add it in the client portal (Refer & earn).');
    var ref = prompt('Pay ' + rs(amt) + ' to UPI ' + upi + ', then enter the UPI reference (UTR):'); if (!ref) return;
    var r = await supabaseClient.rpc('admin_mark_referral_paid', { p_id: id, p_ref: ref });
    if (r.error) return alert(r.error.message); window.openPartners('referrals');
  };

  // Header button (Admins / Super Admin only), next to Settings.
  var tries = 0, t = setInterval(function () {
    if (typeof currentUser !== 'undefined' && currentUser && currentUser.id) {
      clearInterval(t);
      if (!isAdmin() || document.getElementById('partnersBtn')) return;
      var s = [].slice.call(document.querySelectorAll('button')).find(function (b) { return /openSettings/.test(b.getAttribute('onclick') || ''); });
      if (!s) return;
      var b = document.createElement('button'); b.id = 'partnersBtn'; b.type = 'button'; b.textContent = '🤝 Partners'; b.onclick = function () { window.openPartners('partners'); };
      s.parentNode.insertBefore(b, s);
    }
    if (++tries > 120) clearInterval(t);
  }, 1000);
})();
