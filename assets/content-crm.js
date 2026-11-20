/* CRM: community Q&A moderation + blog posts (Admins). Globals: supabaseClient, toolModal, esc, $, currentUser. */
(function () {
  var isAdmin = function () { return typeof currentUser !== 'undefined' && currentUser && ['admin', 'super_admin'].indexOf(currentUser.role) >= 0; };
  var dt = function (d) { return d ? new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }) : ''; };
  var tab = 'qa', editing = null;
  var slugify = function (t) { return String(t || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80); };

  window.openContent = async function (t) {
    if (!isAdmin()) return alert('Admins only.');
    tab = t || tab;
    toolModal('<h2 style="margin-top:0">Website content</h2><div style="display:flex;gap:6px;margin-bottom:10px">' +
      ['qa', 'blog'].map(function (k) { return '<button type="button" class="' + (k === tab ? '' : 'secondary') + '" onclick="openContent(\'' + k + '\')">' + (k === 'qa' ? 'Community Q&A' : 'Blog posts') + '</button>'; }).join('') + '</div><div id="ctBody">Loading…</div>');
    try { if (tab === 'qa') await drawQA(); else await drawBlog(); } catch (e) { $('ctBody').textContent = e.message || e; }
  };

  async function drawQA() {
    var q = await supabaseClient.from('community_questions').select('id,title,body,category,asker_name,status,answer_count,created_at').order('created_at', { ascending: false }).limit(100);
    if (q.error) throw q.error;
    var a = await supabaseClient.from('community_answers').select('id,question_id,body,answerer_name,is_staff_answer,status,created_at').eq('status', 'pending').order('created_at');
    var qs = q.data || [], pendQ = qs.filter(function (x) { return x.status === 'pending'; }), pendA = a.data || [];
    var title = {}; qs.forEach(function (x) { title[x.id] = x.title; });
    var row = function (x) {
      return '<div style="border-top:1px solid var(--line);padding:8px 0"><b>' + esc(x.title) + '</b> <span class="pill">' + esc(x.category) + '</span> <span class="pill ' + (x.status === 'approved' ? 'green' : x.status === 'rejected' ? 'red' : 'amber') + '">' + esc(x.status) + '</span>' +
        '<div class="small">' + esc(x.asker_name) + ' · ' + dt(x.created_at) + ' · ' + x.answer_count + ' answer(s)</div>' + (x.body ? '<div class="small">' + esc(x.body) + '</div>' : '') +
        '<div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap">' + (x.status !== 'approved' ? '<button type="button" onclick="ctQ(\'' + x.id + '\',\'approved\')">Approve</button>' : '') + (x.status !== 'rejected' ? '<button type="button" class="secondary" onclick="ctQ(\'' + x.id + '\',\'rejected\')">Reject</button>' : '') +
        (x.status === 'approved' ? '<button type="button" class="secondary" onclick="ctAnswer(\'' + x.id + '\')">Answer as expert</button>' : '') + '</div></div>';
    };
    $('ctBody').innerHTML = '<p class="small">Questions and user answers appear on <b>legalwegal.com/community</b> only after you approve them. Expert answers from staff publish immediately.</p>' +
      '<h3>Waiting for review: ' + pendQ.length + ' question(s), ' + pendA.length + ' answer(s)</h3>' + pendQ.map(row).join('') +
      pendA.map(function (x) { return '<div style="border-top:1px solid var(--line);padding:8px 0"><div class="small">Answer to: <b>' + esc(title[x.question_id] || '') + '</b> by ' + esc(x.answerer_name) + '</div><div>' + esc(x.body) + '</div><div style="display:flex;gap:6px;margin-top:6px"><button type="button" onclick="ctA(\'' + x.id + '\',\'approved\')">Approve</button><button type="button" class="secondary" onclick="ctA(\'' + x.id + '\',\'rejected\')">Reject</button></div></div>'; }).join('') +
      '<h3>All questions</h3>' + (qs.filter(function (x) { return x.status !== 'pending'; }).map(row).join('') || '<p class="small">None yet.</p>');
  }
  window.ctQ = async function (id, st) { var r = await supabaseClient.from('community_questions').update({ status: st }).eq('id', id); if (r.error) return alert(r.error.message); window.openContent('qa'); };
  window.ctA = async function (id, st) { var r = await supabaseClient.from('community_answers').update({ status: st }).eq('id', id); if (r.error) return alert(r.error.message); window.openContent('qa'); };
  window.ctAnswer = async function (qid) {
    var body = prompt('Your expert answer (shown publicly as "Legal Wegal Expert"):'); if (!body) return;
    var r = await supabaseClient.rpc('community_answer', { p_question: qid, p_body: body, p_name: '' });
    if (r.error) return alert(r.error.message); window.openContent('qa');
  };

  async function drawBlog() {
    var r = await supabaseClient.from('blog_posts').select('id,slug,title,category,status,published_at,updated_at').order('updated_at', { ascending: false });
    if (r.error) throw r.error;
    $('ctBody').innerHTML = '<p class="small">Posts published here appear on <b>legalwegal.com/blog</b> under the starter guides. Write in plain text; blank lines become paragraphs, and lines starting with "## " become headings.</p>' +
      '<div class="actions" style="justify-content:flex-start"><button type="button" onclick="ctEdit()">＋ New post</button></div>' +
      ((r.data || []).map(function (p) { return '<div style="border-top:1px solid var(--line);padding:8px 0;display:flex;gap:8px;align-items:center;flex-wrap:wrap"><b>' + esc(p.title) + '</b><span class="pill ' + (p.status === 'published' ? 'green' : '') + '">' + esc(p.status) + '</span><span class="small">' + esc(p.category) + ' · ' + dt(p.updated_at) + '</span><span style="margin-left:auto;display:flex;gap:6px">' + (p.status === 'published' ? '<a class="btn secondary" target="_blank" rel="noopener" href="https://www.legalwegal.com/blog/post/?s=' + encodeURIComponent(p.slug) + '">View</a>' : '') + '<button type="button" class="secondary" onclick="ctEdit(\'' + p.id + '\')">Edit</button></span></div>'; }).join('') || '<p class="small">No posts written in the CRM yet. The 10 starter guides are built into the website.</p>');
  }
  var toHtml = function (t) {
    return String(t || '').split(/\n\s*\n/).map(function (b) { b = b.trim(); if (!b) return ''; if (/^## /.test(b)) return '<h2>' + esc(b.slice(3)) + '</h2>'; if (/^- /m.test(b)) return '<ul>' + b.split('\n').map(function (l) { return '<li>' + esc(l.replace(/^- /, '')) + '</li>'; }).join('') + '</ul>'; return '<p>' + esc(b).replace(/\n/g, '<br>') + '</p>'; }).join('\n');
  };
  var fromHtml = function (h) {
    return String(h || '').replace(/<h2>(.*?)<\/h2>/g, '## $1\n\n').replace(/<li>(.*?)<\/li>/g, '- $1\n').replace(/<\/?ul>/g, '\n').replace(/<br>/g, '\n').replace(/<p>(.*?)<\/p>/gs, '$1\n\n').replace(/<[^>]+>/g, '')
      .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/\n{3,}/g, '\n\n').trim();
  };
  window.ctEdit = async function (id) {
    editing = { title: '', slug: '', excerpt: '', body_html: '', category: 'GST', status: 'draft' };
    if (id) { var r = await supabaseClient.from('blog_posts').select('*').eq('id', id).single(); if (r.error) return alert(r.error.message); editing = r.data; }
    toolModal('<h2 style="margin-top:0">' + (id ? 'Edit post' : 'New post') + '</h2><label>Title<input id="bTitle" value="' + esc(editing.title) + '"></label>' +
      '<label>Short summary (shown in lists and Google)<input id="bEx" value="' + esc(editing.excerpt) + '"></label>' +
      '<label>Category<select id="bCat">' + ['GST', 'Company', 'Trademark', 'Licences', 'Compliance', 'Tax', 'Legal', 'General'].map(function (c) { return '<option' + (c === editing.category ? ' selected' : '') + '>' + c + '</option>'; }).join('') + '</select></label>' +
      '<label>Article<textarea id="bBody" rows="16" style="width:100%">' + esc(fromHtml(editing.body_html)) + '</textarea></label>' +
      '<div class="actions"><button type="button" class="secondary" onclick="window.openContent(\'blog\')">Back</button><button type="button" class="secondary" onclick="ctSave(\'draft\')">Save draft</button><button type="button" onclick="ctSave(\'published\')">Publish</button></div><div id="bMsg" class="small"></div>');
  };
  window.ctSave = async function (st) {
    var t = $('bTitle').value.trim(); if (t.length < 10) return ($('bMsg').textContent = 'Title is too short.');
    var row = { title: t, excerpt: $('bEx').value.trim(), category: $('bCat').value, body_html: toHtml($('bBody').value), status: st, seo_title: t, seo_description: $('bEx').value.trim().slice(0, 158), author_name: 'Legal Wegal Team', updated_at: new Date().toISOString() };
    if (st === 'published' && !editing.published_at) row.published_at = new Date().toISOString();
    var r;
    if (editing.id) r = await supabaseClient.from('blog_posts').update(row).eq('id', editing.id).select('id').single();
    else { row.slug = slugify(t); r = await supabaseClient.from('blog_posts').insert(row).select('id').single(); }
    if (r.error) return ($('bMsg').textContent = /duplicate/.test(r.error.message) ? 'A post with a very similar title exists. Change the title.' : r.error.message);
    window.openContent('blog');
  };

  var tries = 0, t = setInterval(function () {
    if (typeof currentUser !== 'undefined' && currentUser && currentUser.id) {
      clearInterval(t);
      if (!isAdmin() || document.getElementById('contentBtn')) return;
      var s = [].slice.call(document.querySelectorAll('button')).find(function (b) { return /openSettings/.test(b.getAttribute('onclick') || ''); });
      if (!s) return;
      var b = document.createElement('button'); b.id = 'contentBtn'; b.type = 'button'; b.textContent = '📝 Content'; b.onclick = function () { window.openContent('qa'); };
      s.parentNode.insertBefore(b, s);
      supabaseClient.from('community_questions').select('id', { count: 'exact', head: true }).eq('status', 'pending').then(function (r) { if (r.count) b.textContent = '📝 Content (' + r.count + ' to review)'; });
    }
    if (++tries > 120) clearInterval(t);
  }, 1000);
})();
