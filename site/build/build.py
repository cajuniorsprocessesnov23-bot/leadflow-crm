#!/usr/bin/env python3
"""Builds the new legalwegal.com as static pages into site/out/ (same URLs as the old site).
Run: python3 site/build/build.py   (from the repo root or anywhere)"""
import json, os, re, html, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from data_a import S as A
from data_b import S as B
from data_c import S as C

OUT = os.path.join(HERE, "..", "out")
SVC = {**A, **B, **C}
SVC.setdefault("llp-partnership", dict(n="LLP Registration", c="co", crm="LLP Registration",
 d="A Limited Liability Partnership (LLP) combines the flexibility of a partnership with limited liability for partners. It has lower compliance than a company and suits professional firms and small businesses. We handle DSC, name reservation, incorporation (FiLLiP) and the LLP agreement filing.",
 who=["Professional firms (CAs, consultants, architects)","Small businesses with two or more partners","Founders who want limited liability with simpler compliance"],
 docs=["PAN and Aadhaar of all partners","Photographs","Registered office address proof and owner's NOC","Bank statement or utility bill of each partner"],
 steps=["DSC for designated partners","Name reservation (RUN-LLP)","Incorporation filed (FiLLiP)","Certificate of Incorporation, LLPIN, PAN and TAN","LLP agreement filed (Form 3) within 30 days"],
 time="Usually 10–15 working days",
 faqs=[("How many partners are needed?","At least two designated partners, one of whom must be resident in India."),
       ("Is an audit required?","Only if turnover exceeds ₹40 lakh or contribution exceeds ₹25 lakh."),
       ("Can an LLP raise equity investment?","Not like a company; many convert to a Private Limited Company before fundraising.")]))
PRICES = json.load(open(os.path.join(HERE, "prices.json"), encoding="utf-8"))
CATS = {"co": "Company & Business Registration", "gst": "GST", "tm": "Trademark & IP", "lic": "Licences",
        "comp": "Compliance & Accounting", "tax": "Income Tax", "legal": "Legal & Disputes", "other": "More Services"}
HUB = {"co": "company-registration-all", "gst": "gst-online", "tm": "trademark-all", "lic": "licenses",
       "comp": "compliance", "tax": "tax", "legal": "legal", "other": "other-services"}
SITE = "https://www.legalwegal.com"
# Legal Wegal's own images (copied from the old site, compressed, SEO file names) in the public Supabase 'site' bucket
IMG = "https://smedmzwiddhmxaznqoen.supabase.co/storage/v1/object/public/site/"
# service slug -> (image, width, height, alt)
SVC_BANNER = {
    "gst-return-filing": ("gst-return-filing-compliance-legal-wegal.webp", 1400, 700, "Outsource GST return filing and compliance to Legal Wegal"),
    "gstr-9-annual-filing": ("gst-compliance-outsourcing-legal-wegal.webp", 1400, 560, "GST annual return and compliance by Legal Wegal"),
    "online-gst-nil-return-filing": ("gst-nil-return-filing.webp", 1400, 959, "GST nil return filing online"),
    "gst-modification": ("gst-registration-modification.webp", 1400, 933, "Modify your GST registration certificate"),
    "itr": ("income-tax-consultation-legal-wegal.webp", 1400, 788, "Income tax filing and consultation by Legal Wegal"),
    "online-tax-planning-consultancy": ("smart-tax-consultation-legal-wegal.webp", 1400, 788, "Smart tax consultation and strategic advisory"),
    "consumer-complaint": ("consumer-dispute-legal-help-legal-wegal.webp", 1400, 700, "Consumer dispute help with online dispute resolution"),
    "consumer-dispute-odr": ("consumer-dispute-legal-help-legal-wegal.webp", 1400, 700, "Consumer dispute help with online dispute resolution"),
    "fssai-modification": ("fssai-license-modification-legal-wegal.webp", 1400, 643, "FSSAI FoSCoS food licence modification at low cost"),
    "fssai-renewal": ("fssai-foscos-license-renewal.webp", 1400, 641, "FSSAI FoSCoS food licence renewal"),
    "trademark-registration": ("trademark-registration-certificate.webp", 1400, 934, "Get your trademark registration certificate"),
    "trademark-renewal": ("trademark-renewal-certificate.webp", 1400, 788, "Trademark renewal before the certificate expires"),
    "series-trademark": ("trademark-certificate-india.webp", 1351, 564, "Trademark certificate in India"),
    "trademark-all": ("trademark-renewal-india.webp", 1400, 934, "Trademark services in India"),
    "online-annual-compliance-filing": ("annual-compliance-company-llp.webp", 1400, 933, "Annual compliance and ROC filing for companies and LLPs"),
    "annual-compliance-bookkeeping": ("annual-compliance-filing-india.webp", 1400, 478, "Annual compliance and bookkeeping online"),
    "online-apeda-registration": ("apeda-registration-india.webp", 1400, 513, "APEDA registration for agricultural and food exporters"),
    "online-copyright-registration": ("copyright-registration-india.webp", 1400, 867, "Copyright registration in India"),
    "legal-notice": ("legal-services-scales-of-justice.webp", 1600, 1067, "Legal notice drafting by legal experts"),
}
FOUNDER = ("kunal-ahuja-founder-ceo-legal-wegal.webp", 393, 487, "Kunal Ahuja, Founder and CEO of Legal Wegal")

PHONE, PHONE_TXT, WA = "+919370077727", "+91 93700 77727", "919370077727"
SB_URL, SB_KEY = "https://smedmzwiddhmxaznqoen.supabase.co", "sb_publishable_Y14BKYhQ7k7xSL8jhX6vFg_scknKxpe"
e = lambda s: html.escape(str(s or ""), quote=True)

def inr(n):
    n = int(round(float(n)))
    s = str(n)
    if len(s) <= 3: return "₹" + s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
    return "₹" + head + "," + tail

def price_of(slug):
    p = PRICES.get(slug)
    if not p: return None
    fee = p.get("fee")
    if fee in (None, ""): return None
    return p

def price_label(slug, short=False):
    p = price_of(slug)
    if not p: return "Get a free quote"
    if p["fee"] == 0: return e(p.get("note") or "Free")
    starting = "from " if "Starting" in (p.get("note") or "") else ""
    return f"{starting}{inr(p['fee'])}{e(p.get('unit',''))}"

CSS = """
:root{--ink:#14213d;--muted:#5b6478;--line:#e3e8f0;--soft:#f3f6fb;--brand:#0b2a5b;--brand2:#f26b21;--accent:#ffb703;--ok:#0f8a6b;--r:12px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);line-height:1.6;font-size:16px;background:#fff}
a{color:var(--brand2)}img,svg{display:block}.wrap{max-width:1160px;margin:0 auto;padding:0 20px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:12px;padding:12px 18px;font:600 15px/1.1 inherit;cursor:pointer;text-decoration:none}
.btn-p{background:var(--brand2);color:#fff}.btn-g{background:#fff;color:var(--brand);border:1.5px solid var(--line)}.btn-wa{background:#1fa855;color:#fff}
header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.nav{display:flex;align-items:center;gap:18px;height:66px}.logo{display:flex;align-items:center;gap:10px;white-space:nowrap;text-decoration:none;font-weight:800;font-size:19px;color:var(--brand)}
.logo b{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;background:var(--brand);color:var(--accent);font-size:16px}
.menu{display:flex;gap:4px;margin-left:auto}.dd{position:relative}.dd>a{display:block;white-space:nowrap;padding:10px 7px;text-decoration:none;color:var(--muted);font-weight:500;font-size:15px}
.dd .pan{display:none;position:absolute;top:100%;left:0;min-width:270px;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 18px 40px rgba(29,18,80,.12);padding:8px}
.dd:hover .pan,.dd:focus-within .pan{display:block}.pan a{display:block;padding:7px 10px;border-radius:8px;text-decoration:none;color:var(--ink);font-size:14px}.pan a:hover{background:var(--soft)}
@media(max-width:1100px){.nav .btn-g{display:none}}@media(max-width:960px){.menu{display:none}.nav .btn-g{display:none}}
.crumbs{font-size:13px;color:var(--muted);padding:14px 0 0}.crumbs a{color:var(--muted)}
.hero{background:linear-gradient(#faf9ff,#fff);padding:10px 0 40px;border-bottom:1px solid var(--line)}
.hgrid{display:grid;grid-template-columns:1.2fr .8fr;gap:36px;align-items:start;margin-top:10px}@media(max-width:900px){.hgrid{grid-template-columns:1fr}}
h1{font-size:clamp(30px,4vw,44px);line-height:1.12;letter-spacing:-.8px;color:var(--brand);margin:8px 0 14px}
.lead{font-size:17.5px;color:var(--muted)}.chips{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.chip{background:#fff;border:1px solid var(--line);border-radius:20px;padding:6px 12px;font-size:13px;color:var(--muted)}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 16px 40px rgba(29,18,80,.08)}
.price{font-size:30px;font-weight:800;color:var(--brand)}.price small{font-size:14px;color:var(--muted);font-weight:500}
.card label{display:block;font-size:13px;color:var(--muted);margin:10px 0 5px}.card input,.card textarea{width:100%;padding:12px;border:1.5px solid var(--line);border-radius:10px;font:inherit}
.card input:focus{outline:none;border-color:var(--brand2)}.msg{font-size:13px;min-height:18px;margin-top:8px}.small{font-size:12.5px;color:var(--muted)}
main section{padding:44px 0;border-bottom:1px solid var(--line)}main h2{font-size:clamp(23px,2.6vw,30px);color:var(--brand);letter-spacing:-.4px;margin:0 0 16px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:28px}@media(max-width:800px){.cols{grid-template-columns:1fr}}
ul.tick{list-style:none;padding:0;margin:0}ul.tick li{padding:8px 0 8px 30px;position:relative;border-bottom:1px dashed var(--line)}
ul.tick li:before{content:"✓";position:absolute;left:0;top:8px;width:20px;height:20px;border-radius:50%;background:#e6f6f1;color:var(--ok);font-size:12px;display:grid;place-items:center;font-weight:700}
ol.steps{counter-reset:s;list-style:none;padding:0;margin:0;display:grid;gap:12px}ol.steps li{counter-increment:s;padding:14px 16px 14px 58px;border:1px solid var(--line);border-radius:12px;position:relative;background:#fff}
ol.steps li:before{content:counter(s);position:absolute;left:14px;top:12px;width:30px;height:30px;border-radius:50%;background:var(--brand);color:var(--accent);display:grid;place-items:center;font-weight:700}
table.fees{width:100%;border-collapse:collapse;font-size:15px}table.fees td,table.fees th{padding:12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}table.fees th{background:var(--soft);color:var(--brand)}
details{border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px;background:#fff}summary{cursor:pointer;font-weight:600;color:var(--brand)}details p{color:var(--muted);margin:10px 0 0}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}}@media(max-width:560px){.grid{grid-template-columns:1fr}}
.svc{border:1px solid var(--line);border-radius:var(--r);padding:18px;text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:6px;background:#fff}.svc:hover{border-color:#cfc5ff;box-shadow:0 10px 26px rgba(29,18,80,.08)}
.svc h3{margin:0;font-size:16.5px;color:var(--brand)}.svc p{margin:0;font-size:14px;color:var(--muted);flex:1}.svc b{font-size:14px}
.incl{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}@media(max-width:800px){.incl{grid-template-columns:1fr 1fr}}.incl div{background:var(--soft);border-radius:12px;padding:14px;font-size:14px}
.disc{background:#fff8e6;border:1px solid #f3dfa6;border-radius:12px;padding:12px 14px;font-size:13px;color:#6b5200}
footer{background:#120b33;color:#c9c3e6;padding:46px 0 26px;font-size:14px}.fgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px}@media(max-width:800px){.fgrid{grid-template-columns:1fr 1fr}}
footer h4{color:#fff;margin:0 0 10px;font-size:14px}footer a{display:block;color:#c9c3e6;text-decoration:none;margin:5px 0}footer a:hover{color:#fff}.legal{border-top:1px solid #2a2155;margin-top:26px;padding-top:16px;font-size:12px;color:#8f88b5}
.mbar{display:none}@media(max-width:700px){.mbar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:30;background:#fff;border-top:1px solid var(--line);padding:8px;gap:8px}.mbar a{flex:1}body{padding-bottom:64px}.fab{display:none}}
.fab{position:fixed;right:18px;bottom:18px;z-index:30;width:54px;height:54px;border-radius:50%;background:#1fa855;display:grid;place-items:center;box-shadow:0 8px 20px rgba(0,0,0,.2)}
.preview{background:var(--accent);color:#3b2a00;text-align:center;font-size:13px;padding:5px}
.topbar{background:var(--brand);color:#dbe4f3;font-size:13px}.topbar .wrap{display:flex;gap:18px;align-items:center;height:36px}.topbar a{color:#fff;text-decoration:none}.topbar .r{margin-left:auto;display:flex;gap:16px}
@media(max-width:700px){.topbar .hide-m{display:none}}
.logo b{background:var(--brand2);color:#fff}.btn-p{background:var(--brand2)}.btn-p:hover{background:#d95a14}
h1{color:var(--brand)}.svc:hover{border-color:#f7b48c}.price{color:var(--brand)}
.hbanner{position:relative;color:#fff;background:#0b2a5b center/cover no-repeat;overflow:hidden}
.hbanner:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,26,58,.94) 0%,rgba(8,26,58,.82) 48%,rgba(8,26,58,.35) 100%)}
.hbanner .wrap{position:relative;display:grid;grid-template-columns:1.15fr .85fr;gap:34px;align-items:center;padding-top:44px;padding-bottom:44px}@media(max-width:900px){.hbanner .wrap{grid-template-columns:1fr}}
.hbanner h1{color:#fff;font-size:clamp(32px,4.4vw,50px)}.hbanner .lead{color:#dbe4f3}.hbanner .chip{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.25);color:#fff}
.hbanner .card{color:var(--ink)}
.tiles{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:-34px;position:relative;z-index:2}@media(max-width:900px){.tiles{grid-template-columns:repeat(3,1fr);margin-top:16px}}
.tile{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 10px;text-align:center;text-decoration:none;color:var(--brand);font-weight:600;font-size:14px;box-shadow:0 10px 24px rgba(11,42,91,.08)}
.tile i{font-style:normal;display:grid;place-items:center;width:46px;height:46px;margin:0 auto 8px;border-radius:50%;background:#fff1e8;font-size:22px}.tile:hover{border-color:var(--brand2)}
.feat{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}@media(max-width:800px){.feat{grid-template-columns:1fr}}
.feat div{display:flex;gap:14px;align-items:flex-start;background:var(--soft);border-radius:14px;padding:18px}.feat i{font-style:normal;font-size:26px}.feat b{display:block;color:var(--brand)}
.why{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}@media(max-width:800px){.why{grid-template-columns:1fr 1fr}}
.why div{text-align:center;border:1px solid var(--line);border-radius:14px;padding:18px 12px;background:#fff}.why i{font-style:normal;font-size:28px;display:block;margin-bottom:6px}.why b{color:var(--brand);font-size:14.5px}
.logo img{height:44px;width:auto}.sbanner{width:100%;height:auto;max-height:420px;object-fit:contain;border-radius:16px;background:#fff;box-shadow:0 12px 30px rgba(11,42,91,.12)}
.bstrip{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:8px}.bstrip a{flex:0 0 min(78%,420px);scroll-snap-align:start;border-radius:14px;overflow:hidden;box-shadow:0 8px 22px rgba(11,42,91,.12);background:#fff}.bstrip img{width:100%;height:210px;object-fit:cover;display:block}.bstrip span{display:block;padding:10px 12px;font-weight:700;color:var(--brand)}
.founder{margin:0;text-align:center}.founder img{width:100%;max-width:340px;height:auto;border-radius:18px;background:linear-gradient(180deg,#eef3fb,#dfe8f6);box-shadow:0 18px 40px rgba(11,42,91,.15)}.founder figcaption{margin-top:10px;font-weight:700;color:var(--brand)}.founder figcaption small{display:block;font-weight:500;color:var(--muted,#5b6475)}
.clients{display:flex;gap:26px;align-items:center;justify-content:center;flex-wrap:wrap}.clients img{height:90px;width:auto}
.about{display:grid;grid-template-columns:.9fr 1.1fr;gap:34px;align-items:center}@media(max-width:800px){.about{grid-template-columns:1fr}}
.about img,.ph{width:100%;border-radius:18px;object-fit:cover;box-shadow:0 18px 40px rgba(11,42,91,.15)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;background:var(--brand);color:#fff;border-radius:18px;padding:22px}@media(max-width:700px){.stats{grid-template-columns:1fr 1fr}}
.stats div{text-align:center}.stats b{display:block;font-size:28px;color:var(--accent)}.stats span{font-size:13px;color:#dbe4f3}
.svc .ic{font-size:24px}.cta{background:linear-gradient(90deg,#f26b21,#ff9a3c);color:#fff;border-radius:18px;padding:26px;display:flex;gap:16px;align-items:center;justify-content:space-between;flex-wrap:wrap}.cta h2{color:#fff;margin:0}
"""

def nav_html():
    out = []
    for c, label in CATS.items():
        items = [(s, d) for s, d in SVC.items() if d["c"] == c and not d.get("hub") and not d.get("special")]
        items.sort(key=lambda x: x[1]["n"])
        links = "".join(f'<a href="/services/{s}/">{e(d["n"])}</a>' for s, d in items[:14])
        out.append(f'<div class="dd"><a href="/services/{HUB[c]}/">{e(label.split(" &")[0])}</a><div class="pan">{links}<a href="/services/{HUB[c]}/"><b>All {e(label)} →</b></a></div></div>')
    return "".join(out)

def footer_html():
    cols = []
    for c, label in CATS.items():
        items = [(s, d) for s, d in SVC.items() if d["c"] == c and not d.get("hub") and not d.get("special")][:8]
        cols.append(f'<div><h4>{e(label)}</h4>' + "".join(f'<a href="/services/{s}/">{e(d["n"])}</a>' for s, d in items) + '</div>')
    return f"""<footer><div class="wrap"><div class="fgrid">{''.join(cols)}</div>
<div class="fgrid" style="margin-top:20px"><div><h4>Legal Wegal</h4><a href="tel:{PHONE}">{PHONE_TXT}</a><a href="mailto:legalwegal.com@gmail.com">legalwegal.com@gmail.com</a></div>
<div><h4>Company</h4><a href="/about/">About us</a><a href="/contact/">Contact</a><a href="/our-team/">Our team</a><a href="/services/feedback/">Client feedback</a></div>
<div><h4>For you</h4><a href="/Login/">Client login</a><a href="/partners/">Partner program</a><a href="/blog/">Blog</a><a href="/community/">Community Q&amp;A</a><a href="/services/tc/">Why Legal Wegal</a></div>
<div><h4>Legal</h4><a href="/policy/privacy-policy/">Privacy policy</a><a href="/policy/terms-and-conditions/">Terms & conditions</a><a href="https://g.page/r/CVpQ2RBis-UtEAE/review" rel="noopener">Review us on Google</a></div></div>
<div class="legal">© 2026 Legal Wegal. Legal Wegal is a private business registration and compliance facilitation provider and is not a government website. Registrations, licences and certificates are issued by the respective government authorities. Information on this website is general and is not legal advice. Stock photos: Unsplash.</div></div></footer>"""

LEAD_JS = """<script>
(function(){var SB='%s',KEY='%s';var q=new URLSearchParams(location.search);['utm_source','utm_campaign','gclid','fbclid','ref'].forEach(function(k){var v=q.get(k);if(v)try{localStorage.setItem('lw_'+k,v)}catch(e){}});
function g(k){try{return q.get(k)||localStorage.getItem('lw_'+k)||''}catch(e){return q.get(k)||''}}
document.querySelectorAll('form.lead').forEach(function(f){f.addEventListener('submit',function(ev){ev.preventDefault();var m=f.querySelector('.msg');var ph=(f.phone.value||'').replace(/\\D/g,'').slice(-10);
if(!/^[6-9]\\d{9}$/.test(ph)){m.style.color='#c0392b';m.textContent='Please enter a valid 10-digit mobile number.';return}
var b=f.querySelector('button');b.disabled=true;m.style.color='';m.textContent='Sending…';
fetch(SB+'/functions/v1/web-lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:(f.name.value||'').trim()||'Website visitor',phone:ph,service:f.dataset.service||'',message:((f.note&&f.note.value)||'')+' Page: '+location.pathname,ref:g('ref'),utm_source:g('utm_source'),utm_campaign:g('utm_campaign'),gclid:g('gclid'),hp:f.hp?f.hp.value:''})}).then(function(r){return r.json()}).then(function(j){if(j.ok){f.innerHTML='<div style="text-align:center;padding:18px 0"><div style="font-size:38px;color:#0f8a6b">✓</div><b>Thank you!</b><p class="small">Our expert will call you shortly from %s and send details on WhatsApp.</p></div>';try{window.gtag&&gtag('event','generate_lead')}catch(x){}}else{b.disabled=false;m.style.color='#c0392b';m.textContent=j.error||'Could not send. Please WhatsApp us.'}}).catch(function(){b.disabled=false;m.style.color='#c0392b';m.textContent='Could not send. Please WhatsApp us on %s.'})})});})();
</script>""" % (SB_URL, SB_KEY, PHONE_TXT, PHONE_TXT)

def lead_form(service_name, title="Get a free consultation"):
    return f"""<form class="lead" data-service="{e(service_name)}" novalidate>
<label>Your name</label><input name="name" autocomplete="name" required>
<label>Mobile number</label><input name="phone" type="tel" inputmode="numeric" maxlength="10" placeholder="10-digit mobile" required>
<input name="hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
<button class="btn btn-p" style="width:100%;margin-top:14px" type="submit">{e(title)}</button><div class="msg"></div>
<p class="small">By submitting you agree to be contacted by call / WhatsApp about your request.</p></form>"""

def page(path, title, desc, body, schema=None, preview=True):
    canon = SITE + (path if path.endswith("/") else path + "/")
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in (schema or []))
    return f"""<!DOCTYPE html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon)}">
{'<meta name="robots" content="noindex">' if preview else '<meta name="robots" content="index,follow">'}
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(canon)}"><meta property="og:type" content="website"><meta property="og:site_name" content="Legal Wegal">
<meta name="theme-color" content="#1d1250"><link rel="icon" href="/favicon.png">{ld}<style>{CSS}</style></head><body>
{'<div class="preview">Preview of the new Legal Wegal website – not live yet</div>' if preview else ''}
<div class="topbar"><div class="wrap"><a href="tel:{PHONE}">📞 {PHONE_TXT}</a><a class="hide-m" href="mailto:legalwegal.com@gmail.com">✉ legalwegal.com@gmail.com</a><span class="hide-m">Mon–Sat, 11 AM – 7 PM</span><span class="r"><a href="/partners/">Partner with us</a><a href="/Login/">Client login</a></span></div></div>
<header><div class="wrap nav"><a class="logo" href="/"><img src="{IMG}legal-wegal-logo.webp?v=2" alt="Legal Wegal logo" width="71" height="44">Legal Wegal</a><nav class="menu">{nav_html()}</nav>
<a class="btn btn-g" href="tel:{PHONE}">Call</a><a class="btn btn-p" href="#enquire">Free consultation</a></div></header>
{body}{footer_html()}
<a class="fab" href="https://wa.me/{WA}?text={e('Hi Legal Wegal, I need help')}" aria-label="WhatsApp"><svg width="26" height="26" viewBox="0 0 24 24" fill="#fff"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.1z"/></svg></a>
<div class="mbar"><a class="btn btn-g" href="tel:{PHONE}">Call</a><a class="btn btn-wa" href="https://wa.me/{WA}">WhatsApp</a><a class="btn btn-p" href="#enquire">Enquire</a></div>
{LEAD_JS}</body></html>"""

INCLUDED = ["Dedicated expert for your file", "Document check before filing", "Government filing and follow-up", "Status updates on WhatsApp", "Client portal: upload, track, pay", "Certificates stored in your portal", "Reminders for renewals and due dates", "No hidden charges – fees shown upfront"]

def service_page(slug, d, preview=True):
    name = d["n"]; cat = d["c"]; p = price_of(slug)
    related = [(s, x) for s, x in SVC.items() if x["c"] == cat and s != slug and not x.get("hub") and not x.get("special")][:6]
    if d.get("hub"):
        items = [(s, x) for s, x in SVC.items() if x["c"] == cat and not x.get("hub") and not x.get("special")]
        cards = "".join(f'<a class="svc" href="/services/{s}/"><h3>{e(x["n"])}</h3><p>{e(x["d"][:120])}…</p><b>{price_label(s)}</b></a>' for s, x in items)
        body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › {e(CATS[cat])}</div>
<div class="hgrid"><div><h1>{e(name)}</h1><p class="lead">{e(d['d'])}</p></div><div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Not sure what you need?</h3><p class="small">Tell us about your business; an expert will suggest the right services.</p>{lead_form(name)}</div></div></div></div>
<main><section><div class="wrap"><h2>{e(CATS[cat])} services</h2><div class="grid">{cards}</div></div></section></main>"""
        schema = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": CATS[cat], "item": f"{SITE}/services/{slug}/"}]}]
        title = f"{name} Online in India | Legal Wegal"
        return page(f"/services/{slug}/", title, d["d"][:155], body, schema, preview)

    if d.get("special") == "feedback":
        body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › Client feedback</div><div class="hgrid"><div><h1>{e(name)}</h1><p class="lead">{e(d['d'])}</p>
<p>Real reviews from our clients appear on our Google Business profile. If you've worked with us, we'd love to hear from you.</p></div>
<div class="card" id="enquire"><h3 style="margin:0 0 4px;color:var(--brand)">Share your feedback</h3><form class="lead" data-service="Feedback" novalidate><label>Your name</label><input name="name"><label>Mobile number</label><input name="phone" type="tel" maxlength="10"><label>Your feedback</label><textarea name="note" rows="4"></textarea><input name="hp" style="position:absolute;left:-9999px" tabindex="-1"><button class="btn btn-p" style="width:100%;margin-top:12px">Send feedback</button><div class="msg"></div></form></div></div></div></div>"""
        return page(f"/services/{slug}/", "Client Feedback | Legal Wegal", d["d"][:155], body, None, preview)
    if d.get("special") == "why":
        pts = [("Clear prices", "Our fee and every government fee are shown before you start."), ("One expert, on WhatsApp", "A named expert handles your file and updates you at each step."), ("Your own client portal", "Upload documents, track status, pay and download certificates."), ("All of India, fully online", "No office visits needed; everything is done online.")]
        body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › Why Legal Wegal</div><h1>{e(name)}</h1><p class="lead">{e(d['d'])}</p></div></div>
<main><section><div class="wrap"><div class="grid">{''.join(f'<div class="svc"><h3>{e(a)}</h3><p>{e(b)}</p></div>' for a, b in pts)}</div></div></section>
<section><div class="wrap cols"><div><h2>Talk to an expert</h2><p>Tell us what you need and we'll call you back.</p></div><div class="card" id="enquire">{lead_form('General enquiry')}</div></div></section></main>"""
        return page(f"/services/{slug}/", "Why Legal Wegal – Business Registration & Compliance Experts", d["d"][:155], body, None, preview)

    # ---- regular service page ----
    if p:
        if p["fee"] == 0:
            fee_line = f'<div class="price">{e(p.get("note") or "Free")}</div>'
        else:
            starting = "Starting from " if "Starting" in (p.get("note") or "") else ""
            fee_line = f'<div class="price">{starting}{inr(p["fee"])}<small>{e(p.get("unit",""))} our fee</small></div>'
        note = p.get("note") if p.get("note") and "Starting" not in p.get("note") else ""
        govt = p.get("govt") or "Government fees, if any, at actuals"
    else:
        fee_line, note, govt = '<div class="price" style="font-size:22px">Get a free quote</div>', "", "Government fees, if any, at actuals"
    chips = "".join(f'<span class="chip">{e(x)}</span>' for x in ([d["time"]] if d.get("time") else []) + ["100% online", "Expert on WhatsApp"])
    who = "".join(f"<li>{e(x)}</li>" for x in d["who"])
    docs = "".join(f"<li>{e(x)}</li>" for x in d["docs"])
    steps = "".join(f"<li>{e(x)}</li>" for x in d["steps"])
    faqs = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in d["faqs"])
    rel = "".join(f'<a class="svc" href="/services/{s}/"><h3>{e(x["n"])}</h3><p>{e(x["d"][:100])}…</p><b>{price_label(s)}</b></a>' for s, x in related)
    fee_rows = (f'<tr><td><b>Our professional fee</b></td><td>{price_label(slug)}{(" — " + e(note)) if note else ""}</td></tr>'
                f'<tr><td><b>Government fees</b></td><td>{e(govt)}. Paid to the government at actual cost; we show you the exact amount before filing.</td></tr>'
                f'<tr><td><b>Timeline</b></td><td>{e(d.get("time",""))}</td></tr>')
    bn = SVC_BANNER.get(slug)
    banner = (f'<section style="padding-bottom:0;border:0"><div class="wrap"><img class="sbanner" src="{IMG}{bn[0]}" width="{bn[1]}" height="{bn[2]}" alt="{e(bn[3])}" loading="lazy"></div></section>') if bn else ""
    body = f"""<div class="hero"><div class="wrap"><div class="crumbs"><a href="/">Home</a> › <a href="/services/{HUB[cat]}/">{e(CATS[cat])}</a> › {e(name)}</div>
<div class="hgrid"><div><h1>{e(name)} Online in India</h1><p class="lead">{e(d['d'])}</p><div class="chips">{chips}</div>
<a class="btn btn-wa" href="https://wa.me/{WA}?text={e('Hi, I need help with ' + name)}">Ask on WhatsApp</a></div>
<div class="card" id="enquire">{fee_line}<p class="small" style="margin:4px 0 10px">+ government fees at actuals · exact quote before payment</p>{lead_form(name, 'Get started')}</div></div></div></div>
<main>{banner}
<section><div class="wrap cols"><div><h2>Who needs {e(name)}?</h2><ul class="tick">{who}</ul></div><div><h2>Documents required</h2><ul class="tick">{docs}</ul></div></div></section>
<section><div class="wrap"><h2>How it works</h2><ol class="steps">{steps}</ol></div></section>
<section><div class="wrap"><h2>Fees and government charges</h2><table class="fees"><tr><th style="width:32%">Item</th><th>Details</th></tr>{fee_rows}</table>
<p class="disc" style="margin-top:14px">Legal Wegal is a private facilitation provider. Our fee is for professional and administrative services; government fees are paid to the respective authority at actual cost.</p></div></section>
<section><div class="wrap"><h2>What's included</h2><div class="incl">{''.join(f'<div>✓ {e(x)}</div>' for x in INCLUDED)}</div></div></section>
<section><div class="wrap"><h2>{e(name)} – frequently asked questions</h2>{faqs}</div></section>
<section><div class="wrap"><h2>Related services</h2><div class="grid">{rel}</div></div></section>
</main>"""
    offer = {"@type": "Offer", "priceCurrency": "INR", "price": str(p["fee"])} if p and p["fee"] else None
    svc_ld = {"@context": "https://schema.org", "@type": "Service", "name": name, "description": d["d"], "areaServed": "IN",
              "provider": {"@type": "ProfessionalService", "name": "Legal Wegal", "url": SITE + "/", "telephone": PHONE}}
    if offer: svc_ld["offers"] = offer
    schema = [svc_ld,
              {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faqs"]]},
              {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                  {"@type": "ListItem", "position": 2, "name": CATS[cat], "item": f"{SITE}/services/{HUB[cat]}/"},
                  {"@type": "ListItem", "position": 3, "name": name, "item": f"{SITE}/services/{slug}/"}]}]
    title = f"{name} Online in India – Fees, Documents & Process | Legal Wegal"
    if len(title) > 65: title = f"{name} Online – Fees & Process | Legal Wegal"
    desc = (f"{name} online with Legal Wegal: {price_label(slug)} + govt fees. Documents, process and timeline explained. Expert help on WhatsApp.")
    return page(f"/services/{slug}/", title, desc[:158], body, schema, preview)

PREVIEW_BASE = "/site/out"
def write(rel, content, preview=True):
    if preview:  # preview is served under /site/out on the CRM host
        content = re.sub(r'href="/(?!/)', 'href="' + PREVIEW_BASE + '/', content)
    path = os.path.join(OUT, rel.lstrip("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)

def main(preview=True):
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    for slug, d in SVC.items():
        write(f"services/{slug}/index.html", service_page(slug, d, preview), preview)
    print("service pages:", len(SVC))
    import core; core.core_pages(preview); print("core pages done")

if __name__ == "__main__":
    main(preview="--live" not in sys.argv)
