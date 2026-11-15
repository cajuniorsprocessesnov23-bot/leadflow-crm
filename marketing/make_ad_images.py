import asyncio, base64, pathlib
from playwright.async_api import async_playwright

LOGO = base64.b64encode(pathlib.Path('assets/legalwegal-app-icon-1024.png').read_bytes()).decode()
OUT = pathlib.Path('marketing/out'); OUT.mkdir(exist_ok=True)

# Simple line icons (own drawings)
ICON = {
 'gst': '<rect x="22" y="10" width="76" height="100" rx="8"/><path d="M38 36h44M38 54h44M38 72h26"/><circle cx="86" cy="88" r="20" fill="#f2b705" stroke="#f2b705"/><path d="M77 88l6 6 12-13" stroke="#180858"/>',
 'trademark': '<path d="M60 8l42 16v30c0 28-18 48-42 58C36 102 18 82 18 54V24z"/><text x="60" y="72" text-anchor="middle" font-family="Inter" font-weight="800" font-size="34" fill="#f2b705" stroke="none">TM</text>',
 'iec': '<circle cx="60" cy="60" r="46"/><path d="M14 60h92M60 14c-18 18-18 74 0 92M60 14c18 18 18 74 0 92"/><path d="M78 96l16-6-6 16" stroke="#f2b705"/>',
 'fssai': '<path d="M16 62h88c0 26-20 42-44 42S16 88 16 62z"/><path d="M44 50c0-12 8-12 8-24M62 50c0-12 8-12 8-24" stroke="#f2b705"/><path d="M30 104h60"/>',
 'huid': '<path d="M60 18l16 16-16 16-16-16z" fill="#f2b705" stroke="#f2b705"/><circle cx="60" cy="78" r="30"/><circle cx="60" cy="78" r="20"/>',
}
S = {
 'gst': ('GST Registration', 'New GSTIN, returns & changes', ['Help choosing the right scheme', 'Checklist shared on WhatsApp', 'Returns & notices handled']),
 'trademark': ('Trademark Registration', 'Protect your brand name & logo', ['Name & class search first', 'Filing with the Registry', 'Objection replies handled']),
 'iec': ('IEC Code', 'Import Export Code from DGFT', ['Start importing or exporting', 'Application filed by our team', 'Updates & changes handled']),
 'fssai': ('FSSAI Food Licence', 'Basic, State & Central licence', ['Right licence for your business', 'Checklist shared on WhatsApp', 'Renewals handled by our team']),
 'huid': ('BIS Hallmark & HUID', 'Registration for jewellers', ['BIS jeweller registration', 'HUID process explained', 'Updates at every step']),
}
SIZES = {'landscape': (1200, 628), 'square': (1200, 1200), 'portrait': (960, 1200)}

def html(key, w, h):
    title, sub, pts = S[key]
    land = w / h > 1.5
    scale = 1 if land else (1.5 if h/w<1.1 else 1.4)
    icon = f'<svg viewBox="0 0 120 120" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">{ICON[key]}</svg>'
    bullets = ''.join(f'<li><span></span>{p}</li>' for p in pts)
    layout = 'row' if land else 'column'
    return f'''<!doctype html><html><head><style>
@font-face{{font-family:Inter;src:local('Inter')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{w}px;height:{h}px;overflow:hidden;font-family:Inter,sans-serif;background:#180858;color:#fff;position:relative}}
.bg1{{position:absolute;right:-{int(w*.18)}px;top:-{int(h*.25)}px;width:{int(max(w,h)*.75)}px;height:{int(max(w,h)*.75)}px;border-radius:50%;background:radial-gradient(circle,#2a1a8a 0%,#180858 70%)}}
.bg2{{position:absolute;left:0;bottom:0;width:100%;height:{int(h*.012)+6}px;background:#f2b705}}
.wrap{{position:relative;height:100%;display:flex;flex-direction:{layout};padding:{int(56*scale)}px {int(64*scale)}px;gap:{int(40*scale)}px}}
.main{{flex:1;display:flex;flex-direction:column;justify-content:center}}
.brand{{display:flex;align-items:center;gap:14px;font-family:Georgia,serif;font-size:{int(28*scale)}px;letter-spacing:.04em;margin-bottom:{int(28*scale)}px}}
.brand img{{width:{int(56*scale)}px;height:{int(56*scale)}px;border-radius:10px;border:2px solid rgba(255,255,255,.25)}}
.tag{{display:inline-block;align-self:flex-start;background:rgba(242,183,5,.16);color:#ffd84d;font-weight:700;font-size:{int(20*scale)}px;letter-spacing:.12em;text-transform:uppercase;padding:8px 14px;border-radius:8px;margin-bottom:{int(18*scale)}px}}
h1{{font-size:{int(62 if land else 104)}px;line-height:1.05;font-weight:800;letter-spacing:-.01em}}
.sub{{font-size:{int(28*scale)}px;opacity:.85;margin-top:{int(14*scale)}px}}
ul{{list-style:none;margin-top:{int(30*scale)}px;display:grid;gap:{int(14*scale)}px}}
li{{font-size:{int(26*scale)}px;display:flex;align-items:center;gap:14px}}
li span{{width:{int(14*scale)}px;height:{int(14*scale)}px;border-radius:50%;background:#f2b705;flex:none}}
.side{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{int(26*scale)}px;{'width:330px' if land else ''}}}
.icon{{width:{int(200*scale) if land else 260}px;height:{int(200*scale) if land else 260}px;border-radius:50%;background:rgba(255,255,255,.07);display:grid;place-items:center}}
.icon svg{{width:62%;height:62%}}
.cta{{background:#f2b705;color:#180858;font-weight:800;font-size:{int(26*scale)}px;padding:{int(16*scale)}px {int(26*scale)}px;border-radius:999px;white-space:nowrap}}
.ph{{font-size:{int(22*scale)}px;opacity:.85}}
{'' if land else '.wrap{justify-content:space-between}.main{flex:none}.side{flex-direction:row;justify-content:space-between;align-items:center}.icon{width:230px;height:230px}'}
</style></head><body><div class="bg1"></div><div class="bg2"></div>
<div class="wrap"><div class="main">
<div class="brand"><img src="data:image/png;base64,{LOGO}">LEGAL WEGAL</div>
<div class="tag">All India · Expert help</div>
<h1>{title}</h1><div class="sub">{sub}</div><ul>{bullets}</ul></div>
<div class="side"><div class="icon">{icon}</div><div style="display:flex;flex-direction:column;align-items:center;gap:10px"><div class="cta">Request a call back</div><div class="ph">WhatsApp +91 93700 77727</div></div></div>
</div></body></html>'''

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for key in S:
            for name, (w, h) in SIZES.items():
                pg = await b.new_page(viewport={'width': w, 'height': h})
                await pg.set_content(html(key, w, h))
                await pg.wait_for_timeout(150)
                await pg.screenshot(path=str(OUT / f'lw_{key}_{name}.png'), type='png')
                await pg.close()
        await b.close()
asyncio.run(main())
print(sorted(x.name for x in OUT.iterdir()))
