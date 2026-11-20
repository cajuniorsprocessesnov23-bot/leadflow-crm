"""Core pages for the new legalwegal.com: home, about, contact, team, policies, partners."""
import json
from build import SVC, CATS, HUB, PRICES, e, inr, price_label, price_of, lead_form, page, write, PHONE, PHONE_TXT, WA, SB_URL, SB_KEY, SITE, IMG, FOUNDER

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
    org = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": "Legal Wegal", "url": SITE + "/", "telephone": PHONE, "email": "legalwegal.com@gmail.com", "areaServed": "IN", "priceRange": "₹₹"}
    write("index.html", page("/", "Legal Wegal – Company, GST, Trademark & FSSAI Registration Online in India",
          "Register your company, GST, trademark, FSSAI, IEC and more online with Legal Wegal. Clear prices, expert help on WhatsApp and live tracking in your client portal.", body, [org], preview), preview)

def simple(path, title, desc, h1, html_body, preview, form=True):
    side = f'<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Talk to an expert</h3>{lead_form("General enquiry")}</div>' if form else ""
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › {e(h1)}</div><div class="hgrid"><div><h1>{e(h1)}</h1>{html_body}</div>{side}</div></div></div>"""
    write(path.strip("/") + "/index.html", page(path, title, desc, body, None, preview), preview)

def core_pages(preview):
    home(preview)
    simple("/about/", "About Legal Wegal – Business Registration & Compliance Experts", "Legal Wegal helps Indian businesses register, license and stay compliant with clear prices and expert help on WhatsApp.", "About Legal Wegal",
        f"""<div class="about" style="margin-bottom:22px"><figure class="founder"><img src="{IMG}{FOUNDER[0]}" width="{FOUNDER[1]}" height="{FOUNDER[2]}" alt="{FOUNDER[3]}" loading="lazy"><figcaption>Kunal Ahuja<small>Founder &amp; CEO, Legal Wegal</small></figcaption></figure><div><p class="lead">Legal Wegal helps founders, small businesses and professionals across India get registered, licensed and compliant — without office visits or confusing fees.</p><p>Legal Wegal was founded by <b>Kunal Ahuja</b>, who leads the company as Founder &amp; CEO.</p></div></div>
<p>We handle company and LLP incorporation, GST, trademarks and copyright, food and trade licences, import-export codes, tax filings, payroll compliance and legal documentation. Every client gets a dedicated expert, updates on WhatsApp, and a personal client portal to upload documents, track progress and download certificates.</p>
<p>We believe legal and compliance work should be simple and transparent: our fee and every government fee are shown before you start, and you always know the next step.</p>
<p class="disc">Legal Wegal is a private facilitation provider and not a government website. Registrations and licences are issued by the respective government authorities.</p>""", preview)
    simple("/contact/", "Contact Legal Wegal – Call, WhatsApp or Email", "Contact Legal Wegal on +91 93700 77727 (call or WhatsApp) or legalwegal.com@gmail.com.", "Contact us",
        f"""<p class="lead">Call or WhatsApp us, or leave your number and an expert will call you back.</p>
<ul class="tick"><li>Phone & WhatsApp: <a href="tel:{PHONE}">{PHONE_TXT}</a></li><li>Email: <a href="mailto:legalwegal.com@gmail.com">legalwegal.com@gmail.com</a></li><li>Hours: Monday–Saturday, 11 AM – 7 PM</li><li>Service: online across India</li></ul>
<p><a class="btn btn-wa" href="https://wa.me/{WA}">Chat on WhatsApp</a></p>""", preview)
    team_cards = "".join((f'<div class="tm"><img src="{IMG}{f}" alt="{e(n)}, {e(r)} at Legal Wegal" loading="lazy" width="300" height="360">' if f else f'<div class="tm"><span class="av">{e("".join(w[0] for w in n.split()[:2]))}</span>') + f'<b>{e(n)}</b><small>{e(r)}</small></div>' for f, n, r in [("himanshu-pimpalkar-managing-director-legal-wegal.webp","Himanshu Pimpalkar","Manager"),
 ("riya-francis-customer-relationship-manager-legal-wegal.webp","Riya Francis","Customer Relationship Manager"),
 (None,"CA Krish","GST Advisor"),
 ("sanskar-kariya-legal-support-legal-wegal.webp","Sanskar Kariya","Legal Support"),
 ("pankaj-mete-legal-support-legal-wegal.webp","Pankaj Mete","Legal Support"),
 ("raj-meshram-legal-support-legal-wegal.webp","Raj Meshram","Legal Support"),
 ("simran-potphode-legal-support-legal-wegal.webp","Simran Potphode","Legal Support"),
 ("moksh-singh-legal-support-legal-wegal.webp","Moksh Singh","Legal Support")])
    simple("/our-team/", "Our Team – Legal Wegal", "Meet the Legal Wegal team: Kunal Ahuja (Founder), Himanshu Pimpalkar (Manager), Riya Francis (Customer Relationship Manager), CA Krish (GST Advisor) and our legal support team.", "Our team",
        f"""<p class="lead">Legal and compliance experts committed to helping Indian businesses get registered, licensed and compliant with integrity and care.</p>
<div class="about" style="margin:22px 0"><figure class="founder"><img src="{IMG}{FOUNDER[0]}" width="{FOUNDER[1]}" height="{FOUNDER[2]}" alt="{FOUNDER[3]}" loading="lazy"><figcaption>Kunal Ahuja<small>Founder &amp; CEO</small></figcaption></figure><div><h2>Kunal Ahuja – Founder &amp; CEO</h2><p>With 5+ years of experience in corporate law and legal strategy, Kunal founded Legal Wegal to make legal services accessible for Indian startups and businesses. He has personally advised 500+ businesses on legal structuring, fundraising, governance and compliance, and leads the firm with a client-first approach that combines legal expertise with modern technology.</p></div></div>
<style>.team{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:18px;margin-top:14px}}.tm{{background:#fff;border-radius:16px;box-shadow:0 10px 26px rgba(11,42,91,.1);overflow:hidden;text-align:center;padding-bottom:14px}}.tm img,.tm .av{{display:block;width:100%;aspect-ratio:5/6;height:auto;object-fit:cover;object-position:top;background:linear-gradient(180deg,#eef3fb,#dfe8f6)}}.tm .av{{display:grid;place-items:center;font-size:54px;font-weight:800;color:var(--brand)}}.tm b{{display:block;margin-top:12px;color:var(--brand)}}.tm small{{color:#5b6475}}</style><h2>Meet the team</h2><div class="team">{team_cards}</div>
<h2 style="margin-top:28px">What makes our team different</h2><ul class="tick"><li><b>Client first:</b> transparent communication and ethical solutions</li><li><b>Legal excellence:</b> up to date with the latest amendments and tools</li><li><b>One expert per file:</b> a relationship manager on WhatsApp at every step</li></ul>""", preview)
    simple("/policy/privacy-policy/", "Privacy Policy – Legal Wegal", "How Legal Wegal collects, uses and protects your personal data.", "Privacy policy",
        """<p class="small">Last updated: 18 November 2026</p>
<p>Legal Wegal ("we") respects your privacy. This policy explains what personal data we collect and how we use it, in line with the Digital Personal Data Protection Act, 2023.</p>
<h3>What we collect</h3><p>Your name, mobile number, email, business details and the documents you share for the services you request; and basic website usage data such as pages visited and the advertisement that brought you to us.</p>
<h3>How we use it</h3><p>To contact you about your enquiry, provide and track the services you ask for, file applications with government authorities on your behalf, send updates and reminders on WhatsApp, call or email, issue receipts and invoices, and meet legal obligations.</p>
<h3>Sharing</h3><p>We share data only with government portals and authorities needed for your service, payment and communication providers that help us operate, and professionals working on your file. We do not sell your data.</p>
<h3>Storage and security</h3><p>Documents are stored in private, access-controlled storage. Only the team working on your file can open them. We keep data only as long as needed for the service and legal requirements.</p>
<h3>Your choices</h3><p>You can ask to access, correct or delete your data, or stop WhatsApp updates by replying STOP. Write to legalwegal.com@gmail.com.</p>
<h3>Grievance officer</h3><p>For privacy concerns, contact our grievance officer at legalwegal.com@gmail.com.</p>""", preview, form=False)
    simple("/policy/terms-and-conditions/", "Terms & Conditions – Legal Wegal", "Terms for using the Legal Wegal website and services.", "Terms & conditions",
        """<p class="small">Last updated: 18 November 2026</p>
<p>By using this website or our services you agree to these terms.</p>
<h3>Our role</h3><p>Legal Wegal is a private facilitation provider. We prepare and file applications and documents on your behalf. Approvals, registrations and certificates are issued by government authorities, and their timelines and decisions are outside our control.</p>
<h3>Fees</h3><p>Our professional fee is shown on each service page or in your quote. Government fees, stamp duty and other statutory charges are extra and payable at actual cost. Prices may change; the price in your accepted quote applies.</p>
<h3>Your responsibilities</h3><p>You must provide true, complete documents and information. We are not responsible for delays or rejections caused by incorrect or missing information.</p>
<h3>Refunds</h3><p>If we have not started work, our professional fee is refundable. Once filing has started, fees for work done and government fees already paid are not refundable.</p>
<h3>Not legal advice</h3><p>Information on this website is general and not legal advice for your specific situation.</p>
<h3>Contact</h3><p>legalwegal.com@gmail.com · +91 93700 77727</p>""", preview, form=False)

    # old URL had a space: keep it working and point search engines to /our-team/
    write("our team/index.html", '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Our team – Legal Wegal</title><link rel="canonical" href="'+SITE+'/our-team/"><meta http-equiv="refresh" content="0; url=/our-team/"><meta name="robots" content="noindex"></head><body><a href="/our-team/">Our team</a></body></html>', preview)
    partners(preview)
    quote_page(preview)
    blog_pages(preview)
    community_page(preview)

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
if(d.rules.length)h+='<h4>Commission rates</h4><table><tr><th>Service</th><th>Commission</th></tr>'+d.rules.map(function(x){return '<tr><td>'+(x.service&&x.service!=='*'?esc(x.service):'All services')+'</td><td>'+(x.kind==='percent'?x.value+'% of our fee':rs(x.value))+'</td></tr>'}).join('')+'</table>';
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

def quote_page(preview):
    import os
    render = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "quote-render.js"), encoding="utf-8").read()
    html = """<!DOCTYPE html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your quotation – Legal Wegal</title><meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#1d1250">
<style>body{margin:0;background:#f4f2fb;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1c1830}
.wrapq{max-width:840px;margin:18px auto;background:#fff;border-radius:14px;box-shadow:0 4px 24px #1d125014;overflow:hidden}
.bar{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;padding:16px;border-top:1px solid #e6e3f2;background:#faf9ff}
.b{display:inline-block;border:0;cursor:pointer;text-decoration:none;font:inherit;font-weight:700;padding:11px 16px;border-radius:10px;background:#3a1fa8;color:#fff}
.b.g{background:#fff;color:#1d1250;border:1.5px solid #cfc5ff}.b.wa{background:#25d366}.msg{text-align:center;padding:40px 20px}
@media print{body{background:#fff}.wrapq{box-shadow:none;margin:0}.bar,.noprint{display:none}}</style></head><body>
<div class="wrapq"><div id="qBody" class="msg">Loading your quotation…</div><div class="bar" id="qBar" style="display:none"></div></div>
<script>__RENDER__</script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(async function(){var t=new URLSearchParams(location.search).get('t')||'',B=document.getElementById('qBody'),bar=document.getElementById('qBar');
if(!/^[0-9a-f-]{36}$/i.test(t)){B.innerHTML='This quotation link is not valid. Please WhatsApp us on +91 93700 77727.';return}
var sb=supabase.createClient('__SB__','__KEY__',{auth:{persistSession:false}});
var r=await sb.rpc('quote_public',{p_token:t});if(r.error||!r.data){B.innerHTML='We could not find this quotation. Please WhatsApp us on +91 93700 77727.';return}
var q=r.data;B.className='';B.innerHTML=lwQuoteHtml(q);document.title='Quotation '+q.quote_no+' – Legal Wegal';
var wa='https://wa.me/919370077727?text='+encodeURIComponent('Hi Legal Wegal, about quotation '+q.quote_no+': ');
var adv=Math.round(Number(q.total)*Number(q.advance_pct)/100);
var upi='upi://pay?pa='+encodeURIComponent(lwQuoteUpi)+'&pn=Legal%20Wegal&am='+adv+'&cu=INR&tn='+encodeURIComponent(q.quote_no+' advance');
var h='';if(q.expired)h+='<div style="width:100%;text-align:center;color:#c0392b"><b>This quotation has expired.</b> Ask us for an updated one.</div>';
else if(q.status==='accepted')h+='<div style="width:100%;text-align:center;color:#0f8a6b"><b>✓ You accepted this quotation.</b> Pay the advance to start.</div>';
else h+='<button class="b" id="acc">Accept quotation</button>';
h+='<a class="b" href="'+upi+'">Pay ₹'+adv.toLocaleString('en-IN')+' by UPI</a>';
h+=q.pdf_url?'<a class="b g" href="'+q.pdf_url+'" target="_blank" rel="noopener">Download PDF</a>':'<button class="b g" onclick="print()">Download PDF</button>';
h+='<a class="b wa" href="'+wa+'">Ask a question</a>';bar.innerHTML=h;bar.style.display='';
var a=document.getElementById('acc');if(a)a.onclick=async function(){a.disabled=true;a.textContent='Saving…';var x=await sb.rpc('accept_quote',{p_token:t});
a.outerHTML=(x.data?'<div style="width:100%;text-align:center;color:#0f8a6b"><b>✓ Thank you! Quotation accepted.</b> Pay the advance by UPI and send the screenshot on WhatsApp.</div>':'<div style="width:100%;text-align:center">Could not save. Please WhatsApp us.</div>')}})();
</script></body></html>""".replace("__RENDER__", render).replace("__SB__", SB_URL).replace("__KEY__", SB_KEY)
    write("quote/index.html", html, preview)

# ---------------- Blog & community (20 Nov) ----------------
import blog_posts, qa_seed
from datetime import date as _date

def _dt(s):
    d = _date.fromisoformat(s); return d.strftime("%-d %b %Y")

BLOG_CSS = """<style>.post{max-width:780px}.post h2{margin:26px 0 8px}.post table{width:100%;border-collapse:collapse;margin:12px 0}.post th,.post td{border:1px solid var(--line);padding:8px;text-align:left}.post th{background:var(--soft)}
.qa{border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0;background:#fff}.qa h3{margin:0 0 6px;font-size:17px}.qa .ans{border-left:3px solid var(--brand2);padding-left:12px;margin-top:8px}.tagc{display:inline-block;font-size:12px;background:var(--soft);border-radius:20px;padding:2px 10px;margin-right:6px}</style>"""

def blog_pages(preview):
    cards = "".join(f'<a class="svc" href="/blog/{p["slug"]}/"><span class="tagc">{e(p["cat"])}</span><h3>{e(p["title"])}</h3><p>{e(p["desc"][:120])}…</p><b>Read →</b></a>' for p in blog_posts.POSTS)
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › Blog</div><h1>Guides on business registration, tax and compliance</h1>
<p class="lead">Clear, practical answers from the Legal Wegal team, written for founders and small business owners.</p></div></div>
<main><section><div class="wrap"><div class="grid">{cards}</div><div id="dbPosts" class="grid" style="margin-top:16px"></div></div></section></main>{BLOG_CSS}
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script><script>(async function(){{try{{var sb=supabase.createClient('{SB_URL}','{SB_KEY}',{{auth:{{persistSession:false}}}});var r=await sb.from('blog_posts').select('slug,title,excerpt,category').eq('status','published').order('published_at',{{ascending:false}}).limit(50);var esc=function(t){{return String(t||'').replace(/[&<>"]/g,function(c){{return{{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]}})}};document.getElementById('dbPosts').innerHTML=(r.data||[]).map(function(p){{return '<a class="svc" href="/blog/post/?s='+encodeURIComponent(p.slug)+'"><span class="tagc">'+esc(p.category)+'</span><h3>'+esc(p.title)+'</h3><p>'+esc(p.excerpt)+'</p><b>Read →</b></a>'}}).join('')}}catch(x){{}}}})();</script>"""
    write("blog/index.html", page("/blog/", "Blog – Company, GST, Trademark & Compliance Guides | Legal Wegal",
          "Practical guides on company registration, GST, trademarks, FSSAI, import-export and compliance in India from the Legal Wegal team.", body, None, preview), preview)
    for p in blog_posts.POSTS:
        rel = "".join(f'<a class="svc" href="/services/{s}/"><h3>{e(SVC[s]["n"])}</h3><b>{price_label(s)}</b></a>' for s in p["related"] if s in SVC)
        body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › <a href="/blog/">Blog</a> › {e(p["cat"])}</div><div class="hgrid"><div>
<span class="chip">{e(p["cat"])} · {_dt(p["date"])} · Legal Wegal Team</span><h1>{e(p["title"])}</h1><p class="lead">{e(p["desc"])}</p></div>
<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Need help with this?</h3>{lead_form(SVC[p["related"][0]]["n"] if p["related"] else "General enquiry")}</div></div></div></div>
<main><section><div class="wrap post">{p["html"]}<p class="disc">This article is general information, not legal advice. Rules and fees change; we confirm the latest position before filing.</p></div></section>
<section style="background:var(--soft)"><div class="wrap"><h2>Related services</h2><div class="grid">{rel}</div></div></section></main>{BLOG_CSS}"""
        art = {"@context": "https://schema.org", "@type": "Article", "headline": p["title"], "description": p["desc"], "datePublished": p["date"], "dateModified": p["date"],
               "author": {"@type": "Organization", "name": "Legal Wegal"}, "publisher": {"@type": "Organization", "name": "Legal Wegal", "url": SITE + "/"},
               "mainEntityOfPage": f'{SITE}/blog/{p["slug"]}/'}
        write(f'blog/{p["slug"]}/index.html', page(f'/blog/{p["slug"]}/', f'{p["title"]} | Legal Wegal', p["desc"][:158], body, [art], preview), preview)
    # Posts written later in the CRM
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › <a href="/blog/">Blog</a></div><h1 id="pt">Loading…</h1><p class="lead" id="pe"></p></div></div>
<main><section><div class="wrap post" id="pb"></div></section></main>{BLOG_CSS}
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script><script>(async function(){{var s=new URLSearchParams(location.search).get('s')||'';var sb=supabase.createClient('{SB_URL}','{SB_KEY}',{{auth:{{persistSession:false}}}});var r=await sb.from('blog_posts').select('title,excerpt,body_html,seo_title,seo_description').eq('slug',s).eq('status','published').maybeSingle();if(!r.data){{document.getElementById('pt').textContent='Article not found';return}}var p=r.data;document.title=(p.seo_title||p.title)+' | Legal Wegal';document.getElementById('pt').textContent=p.title;document.getElementById('pe').textContent=p.excerpt||'';document.getElementById('pb').innerHTML=p.body_html}})();</script>"""
    write("blog/post/index.html", page("/blog/post/", "Blog | Legal Wegal", "Legal Wegal blog article.", body, None, True if preview else False).replace('<meta name="robots" content="index,follow">', '<meta name="robots" content="noindex,follow">'), preview)

COMMUNITY_APP = r"""<div class="card" id="askBox" style="max-width:760px"><h3 style="margin:0 0 6px;color:var(--brand)">Ask a question</h3>
<div id="cLogin"><p class="small">Log in with your mobile number. We send a code on WhatsApp. Your number is never shown publicly.</p><label>Mobile number</label><input id="cPhone" maxlength="10" inputmode="numeric"><button class="btn btn-p" style="margin-top:10px" onclick="cSend()">Send code</button><div id="cOtpBox" style="display:none"><label>Code</label><input id="cOtp" maxlength="6" inputmode="numeric"><button class="btn btn-p" style="margin-top:10px" onclick="cVerify()">Verify</button></div></div>
<div id="cAsk" style="display:none"><label>Your name (shown with the question)</label><input id="cName"><label>Topic</label><select id="cCat"><option>GST</option><option>Company</option><option>Trademark</option><option>FSSAI</option><option>Licences</option><option>Tax</option><option>Legal</option><option>General</option></select>
<label>Question</label><input id="cTitle" placeholder="e.g. Do I need GST for selling on Instagram?"><label>Details (optional)</label><textarea id="cBody" rows="3" style="width:100%"></textarea><button class="btn btn-p" style="margin-top:10px" onclick="cAskQ()">Post question</button></div><div class="msg" id="cMsg"></div></div>
<div id="dbQ"></div>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script><script>
var csb=supabase.createClient('__SB__','__KEY__',{auth:{storageKey:'lw-community',persistSession:true}}),cPh='';function $c(i){return document.getElementById(i)}function cm(t,b){var m=$c('cMsg');m.style.color=b?'#c0392b':'';m.textContent=t}
function cesc(t){return String(t||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
async function cSend(){cPh=($c('cPhone').value||'').replace(/\D/g,'').slice(-10);if(!/^[6-9]\d{9}$/.test(cPh))return cm('Enter a valid 10-digit mobile number.',1);cm('Sending…');var r=await csb.auth.signInWithOtp({phone:'+91'+cPh,options:{channel:'sms'}});if(r.error)return cm(r.error.message,1);$c('cOtpBox').style.display='';cm('Code sent on WhatsApp.')}
async function cVerify(){var r=await csb.auth.verifyOtp({phone:'+91'+cPh,token:($c('cOtp').value||'').trim(),type:'sms'});if(r.error)return cm(r.error.message,1);cm('');cInit()}
async function cAskQ(){cm('Posting…');var r=await csb.rpc('community_ask',{p_title:$c('cTitle').value,p_body:$c('cBody').value,p_category:$c('cCat').value,p_name:$c('cName').value});if(r.error)return cm(r.error.message,1);$c('cTitle').value='';$c('cBody').value='';cm('Thank you! Your question will appear after a quick review, usually within a working day.')}
async function cInit(){var s=(await csb.auth.getSession()).data.session;$c('cLogin').style.display=s?'none':'';$c('cAsk').style.display=s?'':'none'}
(async function(){cInit();var q=await csb.from('community_questions').select('id,slug,title,body,category,asker_name,created_at').eq('status','approved').order('created_at',{ascending:false}).limit(50);var qs=q.data||[];if(!qs.length)return;var a=await csb.from('community_answers').select('question_id,body,answerer_name,is_staff_answer,upvotes').in('question_id',qs.map(function(x){return x.id})).eq('status','approved');var by={};(a.data||[]).forEach(function(x){(by[x.question_id]=by[x.question_id]||[]).push(x)});
$c('dbQ').innerHTML='<h2>Latest questions</h2>'+qs.filter(function(x){return !window.LW_SEEDED||window.LW_SEEDED.indexOf(x.title)<0}).map(function(x){return '<div class="qa"><span class="tagc">'+cesc(x.category)+'</span><h3>'+cesc(x.title)+'</h3>'+(x.body?'<p class="small">'+cesc(x.body)+'</p>':'')+'<div class="small">Asked by '+cesc(x.asker_name)+'</div>'+(by[x.id]||[]).map(function(y){return '<div class="ans"><b>'+cesc(y.answerer_name)+(y.is_staff_answer?' ✓':'')+'</b><p>'+cesc(y.body)+'</p></div>'}).join('')+'</div>'}).join('')})();
</script>"""

def community_page(preview):
    seeded = json.dumps([q for _, q, _ in qa_seed.QA])
    cats = []
    for c in dict.fromkeys(c for c, _, _ in qa_seed.QA):
        items = "".join(f'<div class="qa"><span class="tagc">{e(c)}</span><h3>{e(q)}</h3><div class="ans"><b>Legal Wegal Expert ✓</b><p>{e(a)}</p></div></div>' for cc, q, a in qa_seed.QA if cc == c)
        cats.append(f'<h2 id="{e(c.lower())}">{e(c)}</h2>{items}')
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › Community Q&amp;A</div><h1>Ask the community: business, tax and legal questions answered</h1>
<p class="lead">Get answers from Legal Wegal experts and other business owners. Free to ask; questions are reviewed before they appear.</p>
<div class="chips">{''.join(f'<a class="chip" style="text-decoration:none" href="#{e(c.lower())}">{e(c)}</a>' for c in dict.fromkeys(c for c, _, _ in qa_seed.QA))}</div></div></div>
<main><section><div class="wrap" style="max-width:860px"><script>window.LW_SEEDED={seeded};</script>{COMMUNITY_APP.replace('__SB__', SB_URL).replace('__KEY__', SB_KEY)}{''.join(cats)}
<p class="disc">Answers are general information, not legal advice for your specific situation.</p></div></section></main>{BLOG_CSS}"""
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for _, q, a in qa_seed.QA]}
    write("community/index.html", page("/community/", "Community Q&A – GST, Company, Trademark & Legal Questions | Legal Wegal",
          "Free answers to common questions on GST, company registration, trademarks, FSSAI, tax and legal matters in India from Legal Wegal experts.", body, [faq], preview), preview)

# ---------- Home page v2 (20 Nov): photo banner + icon tiles, in the style Kunal asked for ----------
U = "https://images.unsplash.com/"
PH = {"hero": U + "photo-1771244688590-1e481dba1b5a?w=1600&q=70&auto=format&fit=crop",
      "about": U + "photo-1656236577401-6c60e0baeed5?w=900&q=70&auto=format&fit=crop",
      "docs": U + "photo-1562564055-71e051d33c19?w=900&q=70&auto=format&fit=crop",
      "meet": U + "photo-1656221008533-ebae2be98b48?w=900&q=70&auto=format&fit=crop"}
TILES = [("🏢", "Company", "company-registration"), ("🧾", "GST", "gst-registration"), ("™️", "Trademark", "trademark-registration"),
         ("🍽️", "FSSAI", "fssai-registration"), ("🌐", "Import-Export", "online-iec-code-import-export-license"), ("📊", "Income Tax", "itr")]
ICON = {"co": "🏢", "gst": "🧾", "tm": "™️", "lic": "📜", "comp": "📅", "tax": "📊", "legal": "⚖️", "other": "🧩"}

CLIENTS = [("client-unacademy.webp", 434, 116, "Unacademy"), ("client-swiggy-zomato-logo.webp", 700, 394, "Swiggy and Zomato"), ("client-the-shakes-company.webp", 600, 222, "The Shakes Company"),
           ("client-bizleap.webp", 800, 232, "BizLeap"), ("client-branditude.webp", 408, 363, "Branditude"), ("client-aswaad-by-vijaya.webp", 500, 500, "Aswaad by Vijaya"), ("client-hi-tech-pathshala.webp", 455, 455, "Hi-Tech Pathshala")]

def home(preview):
    tiles = "".join(f'<a class="tile" href="/services/{s}/"><i>{i}</i>{e(n)}</a>' for i, n, s in TILES if s in SVC)
    cards = "".join(f'<a class="svc" href="/services/{s}/"><span class="ic">{ICON.get(SVC[s]["c"], "📄")}</span><h3>{e(SVC[s]["n"])}</h3><p>{e(SVC[s]["d"][:105])}…</p><b>{price_label(s)}</b></a>' for s in POPULAR if s in SVC)
    cats = "".join(f'<details><summary>{ICON.get(c, "📄")} {e(l)}</summary><p>' + " · ".join(f'<a href="/services/{s}/">{e(d["n"])}</a>' for s, d in sorted(SVC.items(), key=lambda x: x[1]["n"]) if d["c"] == c and not d.get("hub") and not d.get("special")) + f'</p><p><a href="/services/{HUB[c]}/"><b>All {e(l)} →</b></a></p></details>' for c, l in CATS.items())
    finder = json.dumps([[r"restaurant|food|cafe|bakery|kitchen|sweet", ["fssai-registration", "gst-registration", "trade-license"]],
                         [r"brand|logo|name|trademark", ["trademark-registration"]], [r"company|startup|pvt|private|fund", ["company-registration", "trademark-registration", "gst-registration"]],
                         [r"llp|partner", ["llp-partnership"]], [r"export|import", ["online-iec-code-import-export-license", "gst-lut-filing"]], [r"gst", ["gst-registration", "gst-return-filing"]],
                         [r"jewel|gold|hallmark", ["bis-certificate", "gst-registration"]], [r"tax|itr|income", ["itr"]], [r"notice|dispute|consumer|refund", ["legal-notice"]], [r"rent|lease|tenant", ["rent-agreement"]]])
    names = json.dumps({s: SVC[s]["n"] for s in SVC})
    clients = "".join(f'<img src="{IMG}{f}" width="{w}" height="{h}" alt="{e(n)} logo" loading="lazy">' for f, w, h, n in CLIENTS)
    strip = "".join(f'<a href="/services/{s}/"><img src="{IMG}{f}" alt="{e(t)} – Legal Wegal" loading="lazy" width="420" height="210"><span>{e(t)} →</span></a>' for f, t, s in [("gst-compliance-outsourcing-legal-wegal.webp","Outsource your GST compliance","gst-return-filing"),("trademark-registration-certificate.webp","Get your trademark certificate","trademark-registration"),("fssai-license-modification-legal-wegal.webp","FSSAI food licence at low cost","fssai-modification"),("smart-tax-consultation-legal-wegal.webp","Smart tax consultation","online-tax-planning-consultancy"),("annual-compliance-company-llp.webp","Annual compliance & filing","online-annual-compliance-filing"),("consumer-dispute-legal-help-legal-wegal.webp","Got a consumer dispute?","consumer-complaint"),("gst-nil-return-filing.webp","GST nil return filing","online-gst-nil-return-filing")] if s in SVC)
    body = f"""<div class="hbanner" style="background-image:url('{PH["hero"]}')"><div class="wrap">
<div><span class="chip">India's online business registration & compliance partner</span>
<h1>Register, license and protect your business — fully online</h1>
<p class="lead">Company, GST, trademark, FSSAI, import-export, tax and legal services across India. Clear fees before you start, documents uploaded from your phone and live status in your client portal.</p>
<form style="display:flex;gap:8px;margin-top:18px;max-width:560px" onsubmit="return lwFind(event)"><input id="fq" style="flex:1;padding:13px;border:0;border-radius:10px;font:inherit" placeholder="What do you need? e.g. start a restaurant"><button class="btn btn-p">Find</button></form>
<div id="fres" class="chips"></div><div class="chips"><span class="chip">✓ Fees shown upfront</span><span class="chip">✓ Expert on WhatsApp</span><span class="chip">✓ Track in your portal</span></div></div>
<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Get a free consultation</h3><p class="small">An expert calls you back within working hours.</p>{lead_form('General enquiry','Request call back')}</div></div></div>
<div class="wrap"><div class="tiles">{tiles}</div></div>
<main>
<section style="border:0"><div class="wrap"><div class="feat"><div><i>💬</i><span><b>Expert on WhatsApp</b>A dedicated expert answers your questions and guides every step.</span></div><div><i>💰</i><span><b>Clear, fixed fees</b>Our fee and every government fee are shown before you pay.</span></div><div><i>📱</i><span><b>100% online</b>Upload documents from your phone and track progress in your portal.</span></div></div></div></section>
<section style="background:var(--soft)"><div class="wrap"><h2>Popular services</h2><div class="grid">{cards}</div></div></section>
<section><div class="wrap"><h2>Offers & services in focus</h2><div class="bstrip">{strip}</div></div></section>
<section style="padding:30px 0"><div class="wrap"><p class="small" style="text-align:center;margin:0 0 10px;text-transform:uppercase;letter-spacing:.08em">We are associated with</p><div class="clients">{clients}</div></div></section>
<section><div class="wrap about"><figure class="founder"><img src="{IMG}{FOUNDER[0]}" width="{FOUNDER[1]}" height="{FOUNDER[2]}" alt="{FOUNDER[3]}" loading="lazy"><figcaption>Kunal Ahuja<small>Founder &amp; CEO, Legal Wegal</small></figcaption></figure>
<div><h2>About Legal Wegal</h2><p class="lead">We help founders, small businesses and professionals across India get registered, licensed and compliant without office visits or confusing fees.</p>
<ul class="tick"><li>Company, LLP, GST, trademark, FSSAI, IEC, BIS and more under one roof</li><li>Every client gets a relationship manager on WhatsApp</li><li>Government fees charged at actual cost, with receipts</li><li>Client portal to upload, track, pay and download certificates</li></ul>
<p style="margin-top:16px"><a class="btn btn-p" href="/about/">Know more</a> <a class="btn btn-g" href="https://wa.me/{WA}">Chat on WhatsApp</a></p></div></div></section>
<section style="background:var(--soft)"><div class="wrap"><h2>Why choose Legal Wegal</h2><div class="why">
<div><i>🧑‍💼</i><b>Dedicated expert</b></div><div><i>🏷️</i><b>Transparent pricing</b></div><div><i>⚡</i><b>Fast filing</b></div><div><i>🔒</i><b>Secure documents</b></div><div><i>🔔</i><b>Renewal reminders</b></div><div><i>📲</i><b>Updates on WhatsApp</b></div><div><i>🧾</i><b>Receipts for every fee</b></div><div><i>🤝</i><b>Partner program for CAs</b></div><div><i>🇮🇳</i><b>Service across India</b></div></div></div></section>
<section><div class="wrap"><div class="stats"><div><b>{len([s for s, d in SVC.items() if not d.get("hub") and not d.get("special")])}+</b><span>services</span></div><div><b>100%</b><span>online process</span></div><div><b>11–7</b><span>Mon–Sat support</span></div><div><b>₹0</b><span>first consultation</span></div></div></div></section>
<section><div class="wrap cols"><div><h2>How it works</h2><ol class="steps"><li><b>Tell us what you need</b>: enquire online or on WhatsApp; an expert confirms the exact price.</li><li><b>Upload documents</b> from your phone in the client portal.</li><li><b>We prepare and file</b> with the government and handle any queries.</li><li><b>Done</b>: certificate on WhatsApp and in your portal, with renewal reminders later.</li></ol></div>
<img class="ph" loading="lazy" src="{PH["docs"]}" alt="Client signing registration documents with an adviser" style="height:100%;max-height:420px"></div></section>
<section style="background:var(--soft)"><div class="wrap"><h2>All services</h2>{cats}</div></section>
<section><div class="wrap cols"><img class="ph" loading="lazy" src="{PH["meet"]}" alt="Consultant meeting a business owner" style="max-height:380px">
<div><h2>Partner with Legal Wegal</h2><p class="lead">For CAs, accountants, consultants and agents: earn 20% of our fee on every client you refer, track their status live and get paid on time.</p><p><a class="btn btn-p" href="/partners/">Become a partner</a> <a class="btn btn-g" href="/Login/">Client login</a></p>
<h3 style="color:var(--brand);margin-top:22px">Happy with our service?</h3><p class="small">Read or leave a review on Google.</p><a class="btn btn-g" href="https://g.page/r/CVpQ2RBis-UtEAE/review" rel="noopener">⭐ Google reviews</a></div></div></section>
<section><div class="wrap" style="max-width:860px"><h2>Common questions</h2>
<details><summary>How much does it cost?</summary><p>Each service page shows our fee and lists the government fees separately. You get an exact quote before paying anything.</p></details>
<details><summary>Do I need to visit an office?</summary><p>No. Everything is online: upload documents from your phone and get updates on WhatsApp.</p></details>
<details><summary>How do I track my application?</summary><p>Log in to the client portal with your mobile number and the code we send on WhatsApp.</p></details>
<details><summary>Is Legal Wegal a government website?</summary><p>No. Legal Wegal is a private facilitation provider. Registrations are issued by the respective government authorities.</p></details></div></section>
<section style="border:0"><div class="wrap"><div class="cta"><h2>Talk to an expert today, free</h2><span><a class="btn" style="background:#fff;color:var(--brand)" href="tel:{PHONE}">Call {PHONE_TXT}</a> <a class="btn btn-wa" href="https://wa.me/{WA}">WhatsApp</a></span></div></div></section>
</main>
<script>var LWF={finder},LWN={names};function lwFind(ev){{ev.preventDefault();var q=document.getElementById('fq').value,out=[];LWF.forEach(function(r){{if(new RegExp(r[0],'i').test(q))r[1].forEach(function(s){{if(out.indexOf(s)<0&&LWN[s])out.push(s)}})}});document.getElementById('fres').innerHTML=out.length?out.map(function(s){{return '<a class="chip" style="text-decoration:none" href="/services/'+s+'/">'+LWN[s]+' →</a>'}}).join(''):'<span class="chip">Tell us in the form and an expert will suggest the right services.</span>';return false}}</script>"""
    org = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": "Legal Wegal", "url": SITE + "/", "telephone": PHONE, "email": "legalwegal.com@gmail.com", "areaServed": "IN", "priceRange": "₹₹", "image": PH["hero"], "logo": IMG + "legal-wegal-logo.webp", "founder": {"@type": "Person", "name": "Kunal Ahuja", "jobTitle": "Founder & CEO", "image": IMG + FOUNDER[0]}}
    write("index.html", page("/", "Legal Wegal – Company, GST, Trademark & FSSAI Registration Online in India",
          "Register your company, GST, trademark, FSSAI, IEC and more online with Legal Wegal. Clear prices, expert help on WhatsApp and live tracking in your client portal.", body, [org], preview), preview)
