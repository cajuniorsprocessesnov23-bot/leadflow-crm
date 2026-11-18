"""Core pages for the new legalwegal.com: home, about, contact, team, policies, partners."""
import json
from build import SVC, CATS, HUB, PRICES, e, inr, price_label, price_of, lead_form, page, write, PHONE, PHONE_TXT, WA, SB_URL, SB_KEY, SITE

POPULAR = ["company-registration", "gst-registration", "trademark-registration", "fssai-registration", "llp-partnership",
           "one-person-company-registration", "online-iec-code-import-export-license", "itr", "gst-return-filing",
           "online-annual-compliance-filing", "online-copyright-registration", "legal-notice"]

def home(preview):
    cards = "".join(f'<a class="svc" href="/services/{s}/"><h3>{e(SVC[s]["n"])}</h3><p>{e(SVC[s]["d"][:110])}…</p><b>{price_label(s)}</b></a>' for s in POPULAR if s in SVC)
    cats = "".join(f'<a class="svc" href="/services/{HUB[c]}/"><h3>{e(l)}</h3><p>{sum(1 for x in SVC.values() if x["c"]==c and not x.get("hub") and not x.get("special"))} services</p><b>View all →</b></a>' for c, l in CATS.items())
    est = [(s, SVC[s]["n"], PRICES[s]) for s in POPULAR if s in SVC and s in PRICES and PRICES[s].get("fee")]
    est_items = "".join(f'<label class="qi"><input type="checkbox" data-fee="{p["fee"]}" data-n="{e(n)}" data-g="{e(p.get("govt",""))}"> <span><b>{e(n)}</b><br><small>{price_label(s)} + govt fees</small></span></label>' for s, n, p in est)
    finder = json.dumps([[r"restaurant|food|cafe|bakery|kitchen|sweet", ["fssai-registration", "gst-registration", "trade-license"]],
                         [r"brand|logo|name|trademark", ["trademark-registration", "logo-design"]],
                         [r"company|startup|pvt|private|fund", ["company-registration", "trademark-registration", "gst-registration"]],
                         [r"llp|partner", ["llp-partnership", "partnership-deed"]],
                         [r"export|import", ["online-iec-code-import-export-license", "gst-lut-filing", "online-apeda-registration"]],
                         [r"gst", ["gst-registration", "gst-return-filing"]],
                         [r"jewel|gold|hallmark", ["bis-certificate", "gst-registration"]],
                         [r"tax|itr|income", ["itr", "online-tax-planning-consultancy"]],
                         [r"employee|staff|pf|esi|payroll", ["online-pf-registration", "online-esic-registration", "hr-compliance"]],
                         [r"notice|dispute|consumer|refund", ["legal-notice", "consumer-complaint", "online-dispute-resolution"]],
                         [r"rent|lease|tenant", ["rent-agreement"]]])
    names = json.dumps({s: SVC[s]["n"] for s in SVC})
    body = f"""<div class="hero"><div class="wrap hgrid" style="padding-top:30px">
<div><span class="chip">Business registration & compliance, fully online</span>
<h1 style="font-size:clamp(34px,4.6vw,52px)">Register, license and protect your business — without the running around.</h1>
<p class="lead">Company, GST, trademark, FSSAI, IEC, tax and legal services across India. Clear prices before you start, documents uploaded online, and live status in your client portal.</p>
<form id="finder" style="display:flex;gap:8px;margin-top:20px;max-width:560px" onsubmit="return lwFind(event)"><input id="fq" style="flex:1;padding:13px;border:1.5px solid var(--line);border-radius:12px;font:inherit" placeholder="What do you need? e.g. start a restaurant"><button class="btn btn-p">Find</button></form>
<div id="fres" class="chips"></div>
<div class="chips"><span class="chip">✓ Fees shown upfront</span><span class="chip">✓ Expert on WhatsApp</span><span class="chip">✓ Track in your portal</span></div></div>
<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Get a free consultation</h3><p class="small">An expert calls you back, usually within working hours.</p>{lead_form('General enquiry','Request call back')}</div></div></div>
<main>
<section><div class="wrap"><h2>Popular services</h2><div class="grid">{cards}</div></div></section>
<section style="background:var(--soft)"><div class="wrap"><h2>All services</h2><div class="grid">{cats}</div></div></section>
<section><div class="wrap"><h2>How it works</h2><ol class="steps"><li><b>Tell us what you need</b> — enquire online or on WhatsApp; an expert confirms the exact price.</li><li><b>Upload documents</b> from your phone in the client portal.</li><li><b>We prepare and file</b> with the government and handle queries.</li><li><b>Done</b> — certificate on WhatsApp and in your portal, with renewal reminders later.</li></ol></div></section>
<section id="estimate" style="background:var(--soft)"><div class="wrap cols"><div><h2>Instant estimate</h2><p class="small" style="margin-top:-8px">Tick the services you need. Government fees are extra at actual cost and shown before you pay.</p><div class="grid" style="grid-template-columns:1fr 1fr">{est_items}</div></div>
<div class="card" style="align-self:start"><h3 style="margin:0;color:var(--brand)">Your estimate</h3><div id="erows" class="small" style="margin:10px 0">Select services to see the total.</div><div class="price" id="etot">₹0</div><p class="small">Our fees only · + government fees at actuals</p><a class="btn btn-p" style="width:100%" href="#enquire" onclick="lwEst()">Get this done</a></div></div></section>
<section><div class="wrap cols"><div class="card" style="background:linear-gradient(135deg,#1d1250,#3a1fa8);color:#fff"><h2 style="color:#fff">Partner with Legal Wegal</h2><p>For CAs, accountants, consultants and agents. Earn commission on every paid client, track their status live, and get paid monthly.</p><a class="btn" style="background:#fff;color:#1d1250" href="/partners/">Become a partner</a></div>
<div class="card" style="background:linear-gradient(135deg,#0f5e4c,#0f8a6b);color:#fff"><h2 style="color:#fff">Already a client?</h2><p>Log in with your mobile number — we send a code on WhatsApp. Track status, upload documents, pay and refer friends.</p><a class="btn" style="background:#fff;color:#0f5e4c" href="/Login/">Open client portal</a></div></div></section>
<section><div class="wrap" style="max-width:860px"><h2>Common questions</h2>
<details><summary>How much does it cost?</summary><p>Each service page shows our fee and lists the government fees separately. You get an exact quote before paying anything.</p></details>
<details><summary>Do I need to visit an office?</summary><p>No. Everything is online: upload documents from your phone and get updates on WhatsApp.</p></details>
<details><summary>How do I track my application?</summary><p>Log in to the client portal with your mobile number and the code we send on WhatsApp.</p></details>
<details><summary>Is Legal Wegal a government website?</summary><p>No. Legal Wegal is a private facilitation provider. Registrations are issued by the respective government authorities.</p></details></div></section>
</main>
<script>var LWF={finder},LWN={names};function lwFind(ev){{ev.preventDefault();var q=document.getElementById('fq').value,out=[];LWF.forEach(function(r){{if(new RegExp(r[0],'i').test(q))r[1].forEach(function(s){{if(out.indexOf(s)<0)out.push(s)}})}});document.getElementById('fres').innerHTML=out.length?out.map(function(s){{return '<a class="chip" style="text-decoration:none;color:var(--brand2);border-color:#cfc5ff" href="/services/'+s+'/">'+LWN[s]+' →</a>'}}).join(''):'<span class="small">Tell us below and an expert will suggest the right services.</span>';return false}}
function lwRows(){{var t=0,r=[];document.querySelectorAll('#estimate input:checked').forEach(function(c){{t+=+c.dataset.fee;r.push(c.dataset.n)}});document.getElementById('etot').textContent='₹'+t.toLocaleString('en-IN');document.getElementById('erows').textContent=r.length?r.join(' + '):'Select services to see the total.';return r}}
document.querySelectorAll('#estimate input').forEach(function(c){{c.addEventListener('change',lwRows)}});function lwEst(){{var r=lwRows(),f=document.querySelector('form.lead');if(f&&r.length){{f.dataset.service=r[0];var n=f.querySelector('[name=note]');if(!n){{n=document.createElement('input');n.type='hidden';n.name='note';f.appendChild(n)}}n.value='Estimate: '+r.join(', ')}}}}</script>
<style>.qi{{display:flex;gap:10px;align-items:flex-start;background:#fff;border:1.5px solid var(--line);border-radius:12px;padding:12px;cursor:pointer}}.qi small{{color:var(--muted)}}</style>"""
    org = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": "Legal Wegal", "url": SITE + "/", "telephone": PHONE, "email": "info@legalwegal.com", "areaServed": "IN", "priceRange": "₹₹"}
    write("index.html", page("/", "Legal Wegal – Company, GST, Trademark & FSSAI Registration Online in India",
          "Register your company, GST, trademark, FSSAI, IEC and more online with Legal Wegal. Clear prices, expert help on WhatsApp and live tracking in your client portal.", body, [org], preview), preview)

def simple(path, title, desc, h1, html_body, preview, form=True):
    side = f'<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Talk to an expert</h3>{lead_form("General enquiry")}</div>' if form else ""
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › {e(h1)}</div><div class="hgrid"><div><h1>{e(h1)}</h1>{html_body}</div>{side}</div></div></div>"""
    write(path.strip("/") + "/index.html", page(path, title, desc, body, None, preview), preview)

def core_pages(preview):
    home(preview)
    simple("/about/", "About Legal Wegal – Business Registration & Compliance Experts", "Legal Wegal helps Indian businesses register, license and stay compliant with clear prices and expert help on WhatsApp.", "About Legal Wegal",
        """<p class="lead">Legal Wegal helps founders, small businesses and professionals across India get registered, licensed and compliant — without office visits or confusing fees.</p>
<p>We handle company and LLP incorporation, GST, trademarks and copyright, food and trade licences, import-export codes, tax filings, payroll compliance and legal documentation. Every client gets a dedicated expert, updates on WhatsApp, and a personal client portal to upload documents, track progress and download certificates.</p>
<p>We believe legal and compliance work should be simple and transparent: our fee and every government fee are shown before you start, and you always know the next step.</p>
<p class="disc">Legal Wegal is a private facilitation provider and not a government website. Registrations and licences are issued by the respective government authorities.</p>""", preview)
    simple("/contact/", "Contact Legal Wegal – Call, WhatsApp or Email", "Contact Legal Wegal on +91 93700 77727 (call or WhatsApp) or info@legalwegal.com.", "Contact us",
        f"""<p class="lead">Call or WhatsApp us, or leave your number and an expert will call you back.</p>
<ul class="tick"><li>Phone & WhatsApp: <a href="tel:{PHONE}">{PHONE_TXT}</a></li><li>Email: <a href="mailto:info@legalwegal.com">info@legalwegal.com</a></li><li>Hours: Monday–Saturday, 9:30 AM – 7 PM</li><li>Service: online across India</li></ul>
<p><a class="btn btn-wa" href="https://wa.me/{WA}">Chat on WhatsApp</a></p>""", preview)
    simple("/our-team/", "Our Team – Legal Wegal", "Meet the Legal Wegal team of business registration, tax and compliance experts.", "Our team",
        """<p class="lead">Our team of company secretaries, accountants, tax and trademark specialists and client relationship managers works together on every file.</p>
<p>Each client is assigned a relationship manager who stays in touch on WhatsApp, and an expert who prepares and files the work.</p>""", preview)
    simple("/policy/privacy-policy/", "Privacy Policy – Legal Wegal", "How Legal Wegal collects, uses and protects your personal data.", "Privacy policy",
        """<p class="small">Last updated: 18 November 2026</p>
<p>Legal Wegal ("we") respects your privacy. This policy explains what personal data we collect and how we use it, in line with the Digital Personal Data Protection Act, 2023.</p>
<h3>What we collect</h3><p>Your name, mobile number, email, business details and the documents you share for the services you request; and basic website usage data such as pages visited and the advertisement that brought you to us.</p>
<h3>How we use it</h3><p>To contact you about your enquiry, provide and track the services you ask for, file applications with government authorities on your behalf, send updates and reminders on WhatsApp, call or email, issue receipts and invoices, and meet legal obligations.</p>
<h3>Sharing</h3><p>We share data only with government portals and authorities needed for your service, payment and communication providers that help us operate, and professionals working on your file. We do not sell your data.</p>
<h3>Storage and security</h3><p>Documents are stored in private, access-controlled storage. Only the team working on your file can open them. We keep data only as long as needed for the service and legal requirements.</p>
<h3>Your choices</h3><p>You can ask to access, correct or delete your data, or stop WhatsApp updates by replying STOP. Write to info@legalwegal.com.</p>
<h3>Grievance officer</h3><p>For privacy concerns, contact our grievance officer at info@legalwegal.com.</p>""", preview, form=False)
    simple("/policy/terms-and-conditions/", "Terms & Conditions – Legal Wegal", "Terms for using the Legal Wegal website and services.", "Terms & conditions",
        """<p class="small">Last updated: 18 November 2026</p>
<p>By using this website or our services you agree to these terms.</p>
<h3>Our role</h3><p>Legal Wegal is a private facilitation provider. We prepare and file applications and documents on your behalf. Approvals, registrations and certificates are issued by government authorities, and their timelines and decisions are outside our control.</p>
<h3>Fees</h3><p>Our professional fee is shown on each service page or in your quote. Government fees, stamp duty and other statutory charges are extra and payable at actual cost. Prices may change; the price in your accepted quote applies.</p>
<h3>Your responsibilities</h3><p>You must provide true, complete documents and information. We are not responsible for delays or rejections caused by incorrect or missing information.</p>
<h3>Refunds</h3><p>If we have not started work, our professional fee is refundable. Once filing has started, fees for work done and government fees already paid are not refundable.</p>
<h3>Not legal advice</h3><p>Information on this website is general and not legal advice for your specific situation.</p>
<h3>Contact</h3><p>info@legalwegal.com · +91 93700 77727</p>""", preview, form=False)

    # old URL had a space: keep it working and point search engines to /our-team/
    write("our team/index.html", '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Our team – Legal Wegal</title><link rel="canonical" href="'+SITE+'/our-team/"><meta http-equiv="refresh" content="0; url=/our-team/"><meta name="robots" content="noindex"></head><body><a href="/our-team/">Our team</a></body></html>', preview)
    partners(preview)

PARTNER_APP = r"""<div id="pp" class="card" style="max-width:760px;margin:0 auto">
<div id="pLogin"><h3 style="margin:0 0 4px;color:var(--brand)">Partner login / sign up</h3><p class="small">We send a 6-digit code to your WhatsApp.</p>
<label>Mobile number</label><input id="pPhone" type="tel" inputmode="numeric" maxlength="10" placeholder="10-digit mobile"><button class="btn btn-p" style="width:100%;margin-top:12px" onclick="pSend()">Send code on WhatsApp</button>
<div id="pOtpBox" style="display:none"><label>Code</label><input id="pOtp" inputmode="numeric" maxlength="6"><button class="btn btn-p" style="width:100%;margin-top:12px" onclick="pVerify()">Verify &amp; continue</button></div><div class="msg" id="pMsg"></div></div>
<div id="pSign" style="display:none"><h3 style="margin:0;color:var(--brand)">Register as a partner</h3><p class="small">An admin reviews your details, usually within one working day, and gives you a partner code.</p>
<label>Firm / practice name *</label><input id="sFirm"><label>Your name *</label><input id="sName"><label>Email</label><input id="sEmail" type="email"><label>City</label><input id="sCity">
<label>PAN (needed for payouts; without PAN, TDS is 20%)</label><input id="sPan" maxlength="10" style="text-transform:uppercase"><label>GSTIN (optional)</label><input id="sGst" maxlength="15" style="text-transform:uppercase"><label>UPI ID for payouts</label><input id="sUpi" placeholder="name@okicici">
<label>Partnership type</label><select id="sModel"><option value="referral">Referral – we serve your client, you earn commission</option><option value="reseller">Reseller – you buy at partner price and bill your client</option></select>
<label style="display:flex;gap:8px;align-items:flex-start;margin-top:12px"><input type="checkbox" id="sTerms" style="width:auto;margin-top:4px"> I agree to the partner terms below.</label>
<button class="btn btn-p" style="width:100%;margin-top:12px" onclick="pSignup()">Submit application</button><div class="msg" id="sMsg"></div></div>
<div id="pDash" style="display:none"></div></div>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
var psb=supabase.createClient('__SB__','__KEY__',{auth:{storageKey:'lw-partner-portal',persistSession:true}}),pPh='';
function $(i){return document.getElementById(i)}function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function rs(n){return '₹'+Number(n||0).toLocaleString('en-IN')}function dt(d){return d?new Date(d).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):''}
function pm(id,t,bad){var m=$(id);m.style.color=bad?'#c0392b':'';m.textContent=t}
async function pSend(){pPh=($('pPhone').value||'').replace(/\D/g,'').slice(-10);if(!/^[6-9]\d{9}$/.test(pPh))return pm('pMsg','Enter a valid 10-digit mobile number.',1);pm('pMsg','Sending…');var r=await psb.auth.signInWithOtp({phone:'+91'+pPh,options:{channel:'sms'}});if(r.error)return pm('pMsg',r.error.message,1);$('pOtpBox').style.display='';pm('pMsg','Code sent on WhatsApp to '+pPh+'.')}
async function pVerify(){var r=await psb.auth.verifyOtp({phone:'+91'+pPh,token:($('pOtp').value||'').trim(),type:'sms'});if(r.error)return pm('pMsg',r.error.message,1);pLoad()}
async function pSignup(){if(!$('sTerms').checked)return pm('sMsg','Please accept the partner terms.',1);pm('sMsg','Submitting…');var r=await psb.rpc('partner_signup',{p_firm:$('sFirm').value,p_name:$('sName').value,p_email:$('sEmail').value,p_city:$('sCity').value,p_pan:$('sPan').value,p_gstin:$('sGst').value,p_upi:$('sUpi').value,p_model:$('sModel').value});if(r.error)return pm('sMsg',r.error.message,1);pLoad()}
async function pAdd(){var sv=[].slice.call(document.querySelectorAll('#aSvc option:checked')).map(function(o){return o.value});pm('aMsg','Adding…');var r=await psb.rpc('partner_add_client',{p_name:$('aName').value,p_phone:$('aPhone').value,p_services:sv,p_note:$('aNote').value});if(r.error)return pm('aMsg',r.error.message,1);pm('aMsg','Client added. Our team will contact them shortly.');setTimeout(pLoad,1200)}
async function pOut(){await psb.auth.signOut({scope:'local'});location.reload()}
function copyLink(t){try{navigator.clipboard.writeText(t)}catch(e){}pm('lMsg','Link copied.')}
async function pLoad(){var s=(await psb.auth.getSession()).data.session;if(!s){$('pLogin').style.display='';return}$('pLogin').style.display='none';
var r=await psb.rpc('partner_dashboard');if(r.error){$('pDash').style.display='';$('pDash').innerHTML='<p>'+esc(r.error.message)+'</p>';return}var d=r.data;
if(!d.registered){$('pSign').style.display='';return}$('pSign').style.display='none';var p=d.partner,t=d.totals||{},h='';
h+='<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><div><h3 style="margin:0;color:var(--brand)">'+esc(p.firm)+'</h3><span class="small">'+esc(p.name)+' · '+(p.model==='reseller'?'Reseller':'Referral partner')+'</span></div><button class="btn btn-g" onclick="pOut()">Log out</button></div>';
if(p.status!=='active'){h+='<div class="disc" style="margin-top:14px"><b>Application received.</b> Status: '+esc(p.status)+'. An admin will review it and you will get your partner code on WhatsApp.</div>';$('pDash').innerHTML=h;$('pDash').style.display='';return}
var link='https://www.legalwegal.com/?ref='+p.code;
h+='<div class="grid" style="grid-template-columns:repeat(3,1fr);margin-top:14px"><div class="card"><span class="small">Earned</span><div class="price">'+rs(t.earned)+'</div></div><div class="card"><span class="small">Payable</span><div class="price">'+rs(t.payable)+'</div></div><div class="card"><span class="small">Paid</span><div class="price">'+rs(t.paid)+'</div></div></div>';
h+='<h4>Your partner code: '+esc(p.code)+'</h4><p class="small">Share your link. Every enquiry through it is tagged to you.</p><div style="display:flex;gap:8px"><input readonly value="'+esc(link)+'"><button class="btn btn-p" onclick="copyLink(\''+link+'\')">Copy</button><a class="btn btn-wa" href="https://wa.me/?text='+encodeURIComponent('Get your business registration done with Legal Wegal: '+link)+'">Share</a></div><div class="msg" id="lMsg"></div>';
h+='<h4>Add a client</h4><label>Client name</label><input id="aName"><label>Client mobile</label><input id="aPhone" maxlength="10" inputmode="numeric"><label>Services (hold Ctrl to pick several)</label><select id="aSvc" multiple size="5">'+(d.service_options||[]).map(function(o){return '<option>'+esc(o)+'</option>'}).join('')+'</select><label>Note</label><input id="aNote"><button class="btn btn-p" style="margin-top:12px" onclick="pAdd()">Add client</button><div class="msg" id="aMsg"></div>';
h+='<h4>Your clients ('+d.clients.length+')</h4>'+(d.clients.length?'<div style="overflow:auto"><table><tr><th>Client</th><th>Services</th><th>Status</th><th>Paid</th></tr>'+d.clients.map(function(c){return '<tr><td>'+esc(c.name)+'<br><small>'+esc(c.code||'')+' · '+dt(c.created_at)+'</small></td><td>'+esc((c.services||[]).join(', '))+'</td><td>'+esc(c.status)+'</td><td>'+rs(c.paid)+'</td></tr>'}).join('')+'</table></div>':'<p class="small">No clients yet.</p>');
if(p.model==='reseller'&&d.wholesale.length)h+='<h4>Your partner prices</h4><table><tr><th>Service</th><th>Price</th></tr>'+d.wholesale.map(function(w){return '<tr><td>'+esc(w.service)+'</td><td>'+rs(w.price)+'</td></tr>'}).join('')+'</table>';
if(d.rules.length)h+='<h4>Commission rates</h4><table><tr><th>Service</th><th>Commission</th></tr>'+d.rules.map(function(x){return '<tr><td>'+esc(x.service||'All services')+'</td><td>'+(x.kind==='percent'?x.value+'% of our fee':rs(x.value))+'</td></tr>'}).join('')+'</table>';
h+='<h4>Commissions</h4>'+(d.commissions.length?'<div style="overflow:auto"><table><tr><th>Date</th><th>Service</th><th>Gross</th><th>TDS</th><th>Net</th><th>Status</th></tr>'+d.commissions.map(function(c){return '<tr><td>'+dt(c.date)+'</td><td>'+esc(c.service)+'</td><td>'+rs(c.gross)+'</td><td>'+rs(c.tds)+'</td><td>'+rs(c.net)+'</td><td>'+esc(c.status)+(c.ref?'<br><small>UTR '+esc(c.ref)+'</small>':'')+'</td></tr>'}).join('')+'</table></div>':'<p class="small">Commission appears here as soon as your client pays.</p>');
$('pDash').innerHTML=h;$('pDash').style.display=''}
pLoad();
</script>""".replace("__SB__", SB_URL).replace("__KEY__", SB_KEY)

def partners(preview):
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › Partner program</div><div class="hgrid"><div>
<span class="chip">For CAs, accountants, consultants & agents</span><h1>Partner with Legal Wegal and earn on every client you refer</h1>
<p class="lead">Refer clients or resell our services under your own billing. We do the filing; you keep the relationship and get paid automatically.</p>
<ul class="tick"><li>Commission is calculated on our professional fee and becomes payable as soon as your client pays</li><li>Live status of every client in your partner portal</li><li>Your own referral link and code</li><li>Monthly payouts to UPI or bank with TDS certificate (2% u/s 194H above ₹20,000 a year)</li><li>Reseller option with partner prices</li></ul></div>
<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Questions first?</h3>{lead_form('Partner program','Call me back')}</div></div></div></div>
<main><section><div class="wrap"><h2>How it works</h2><ol class="steps"><li><b>Sign up</b> with your mobile number below. We verify your details.</li><li><b>Get your code</b> (e.g. LWP-0001) and referral link.</li><li><b>Refer or add clients</b> — share your link or add them in the portal.</li><li><b>Earn</b> — commission is created automatically when the client pays, and paid out monthly.</li></ol></div></section>
<section id="portal" style="background:var(--soft)"><div class="wrap"><h2 style="text-align:center">Partner portal</h2>{PARTNER_APP}</div></section>
<section><div class="wrap" style="max-width:860px"><h2>Partner terms (summary)</h2>
<details><summary>When is commission earned?</summary><p>When a client tagged to you pays. It is calculated on our professional fee only, not on government fees, and reversed if the payment is refunded.</p></details>
<details><summary>Who can be tagged to me?</summary><p>New clients who enquire through your link or code, or whom you add in the portal. Existing Legal Wegal clients cannot be re-tagged.</p></details>
<details><summary>Tax deduction</summary><p>TDS under section 194H is deducted at 2% once your commission passes ₹20,000 in a financial year, or 20% if PAN is not provided.</p></details>
<details><summary>Conduct</summary><p>Do not promise government outcomes or timelines, and do not use Legal Wegal's name in paid ads without written approval. Accounts can be suspended for misuse.</p></details></div></section></main>"""
    write("partners/index.html", page("/partners/", "Partner Program for CAs & Consultants – Earn Commission | Legal Wegal",
          "Join the Legal Wegal partner program. Refer or resell company, GST, trademark and licence services and earn commission paid monthly.", body, None, preview), preview)
