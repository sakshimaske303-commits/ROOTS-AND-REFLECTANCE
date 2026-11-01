"""
ROOTS & REFLECTANCE: one Marathi page per field to hand to the farmer.

Each card has the walked boundary and area, the days the satellite could not see the field,
the season's figures, the insurance and a box for what the farmer says. Cards go in private/
because they hold one farmer's money figures.

Three versions of the money and insurance parts:
  --blank     empty boxes, for the farmer to tell me his own figures on the visit (default)
  --estimate  filled with my own estimate (private/estimate_whole_farm.py), marked as such
  --figures   the figures I worked out with the farmers in October (data/season_figures_2026.csv)

Out: private/field_cards/farmer_<code>.html  (estimate: private/field_cards/estimate/)
Usage: python src/field_card.py [YYYY-MM-DD] [--blank | --estimate | --figures]
"""
import datetime as dt
import html
import json
import math
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "private", "field_cards")
sys.path.insert(0, os.path.join(ROOT, "private"))

ACRE_PER_HA = 2.4711
GUNTHA_PER_ACRE = 40
SEASON_START = dt.date(2026, 6, 20)
SEASON_END = dt.date(2026, 10, 5)

VILLAGE = {"sawardoh": "सावरडोह", "karanja": "कारंजा घाडगे"}
CROP = {"cotton": "कापूस", "tur": "तूर", "soyabean": "सोयाबीन", "orange": "संत्रा"}
MONTH = ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै",
         "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]
DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def mr(x):
    """Numbers in Devanagari digits, the way the farmers read them on a 7/12."""
    return str(x).translate(DIGITS)


def mr_date(d):
    return f"{mr(d.day)} {MONTH[d.month - 1]}"


def rupees(x):
    """Indian grouping: 1,23,456."""
    neg = x < 0
    s = str(int(round(abs(x))))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("−" if neg else "") + "₹" + mr(s)


def load():
    with open(os.path.join(ROOT, "data", "field_boundaries.geojson"), encoding="utf-8") as f:
        fields = {(ft["properties"]["zone"], int(ft["properties"]["field_num"])): ft
                  for ft in json.load(f)["features"]}
    owners = pd.read_csv(os.path.join(ROOT, "data", "field_owners.csv"))
    money = pd.read_csv(os.path.join(ROOT, "data", "season_figures_2026.csv"))
    ins = pd.read_csv(os.path.join(ROOT, "data", "insurance_check.csv"))
    passes = pd.read_csv(os.path.join(ROOT, "output", "observability_passes.csv"))
    return fields, owners, money, ins, passes


def field_svg(geom, w=300, h=220):
    """The walked boundary, north up, with a 50 m scale bar. Lon/lat to metres locally."""
    ring = geom["coordinates"][0]
    lat0 = sum(p[1] for p in ring) / len(ring)
    kx = 111320 * math.cos(math.radians(lat0))
    ky = 110540
    xs = [p[0] * kx for p in ring]
    ys = [p[1] * ky for p in ring]
    minx, maxy = min(xs), max(ys)
    span = max(max(xs) - minx, maxy - min(ys))
    pad = 24
    s = (min(w, h) - 2 * pad) / span
    pts = " ".join(f"{pad + (x - minx) * s:.1f},{pad + (maxy - y) * s:.1f}" for x, y in zip(xs, ys))
    bar = 50 * s
    return (f'<svg viewBox="0 0 {w} {h}" class="map">'
            f'<polygon points="{pts}" fill="#e3efd9" stroke="#2f5d1e" stroke-width="2.5"/>'
            f'<g transform="translate({w - 34},28)"><path d="M0,14 L6,0 L12,14 L6,10 Z" fill="#333"/>'
            f'<text x="6" y="28" text-anchor="middle" font-size="12">उ</text></g>'
            f'<line x1="{pad}" y1="{h - 12}" x2="{pad + bar:.1f}" y2="{h - 12}" stroke="#333" stroke-width="3"/>'
            f'<text x="{pad + bar + 6:.1f}" y="{h - 8}" font-size="12">{mr(50)} मीटर</text></svg>')


def area_lines(ha):
    hectare = int(ha)
    are = round((ha - hectare) * 100)
    acre = ha * ACRE_PER_HA
    guntha = round(acre * GUNTHA_PER_ACRE)
    return (f"<b>{mr(f'{ha:.2f}')} हेक्टर</b> &nbsp;=&nbsp; {mr(hectare)} हे. {mr(are)} आर (हे.-आर मध्ये)"
            f"<br>= {mr(f'{acre:.2f}')} एकर &nbsp;=&nbsp; सुमारे {mr(guntha)} गुंठे")


def timeline_svg(dates, sown, w=640, h=70):
    """Season strip: every usable satellite look as a dot, the longest blind stretch shaded."""
    days = (SEASON_END - SEASON_START).days

    def x(d):
        return 10 + (d - SEASON_START).days / days * (w - 20)

    looks = sorted(d for d in dates if d >= sown)
    gap = max(zip(looks, looks[1:]), key=lambda p: (p[1] - p[0]).days)
    out = [f'<svg viewBox="0 0 {w} {h}" class="tl">',
           f'<rect x="{x(gap[0]):.1f}" y="14" width="{x(gap[1]) - x(gap[0]):.1f}" height="22" fill="#f3d9c4"/>',
           f'<text x="{(x(gap[0]) + x(gap[1])) / 2:.1f}" y="30" text-anchor="middle" font-size="13" fill="#8a3b0c">'
           f'{mr((gap[1] - gap[0]).days)} दिवस काहीच दिसले नाही</text>',
           f'<line x1="10" y1="25" x2="{w - 10}" y2="25" stroke="#999"/>']
    for m in (7, 8, 9, 10):
        d = dt.date(2026, m, 1)
        out.append(f'<line x1="{x(d):.1f}" y1="38" x2="{x(d):.1f}" y2="44" stroke="#666"/>'
                   f'<text x="{x(d):.1f}" y="58" text-anchor="middle" font-size="12">{MONTH[m - 1]}</text>')
    out.append(f'<path d="M{x(sown):.1f},4 l0,18" stroke="#2f5d1e" stroke-width="2"/>'
               f'<text x="{x(sown) + 4:.1f}" y="10" font-size="11" fill="#2f5d1e">पेरणी</text>')
    for d in looks:
        out.append(f'<circle cx="{x(d):.1f}" cy="25" r="6" fill="#1f5fa8"/>')
    out.append("</svg>")
    return "".join(out), gap


def money_block(row, ha):
    if row is None or pd.isna(row.get("margin_rs_per_ha")):
        return ("<p>या शेताचे उत्पादन अजून तपासून घेत आहे. आकडे नक्की झाल्यावर हा भाग भरून देईन.</p>")
    cost = row["cost_rs_per_ha"] * ha
    margin = row["margin_rs_per_ha"] * ha
    normal = row["margin_normal_year_rs_per_ha"] * ha
    harvest = str(row["harvest_this_season"])
    for en, m in CROP.items():
        harvest = harvest.replace(en, m)
    harvest = mr(harvest.replace(" q", " क्विंटल").replace(";", ","))
    return (f'<table class="money"><tr><td>एकूण खर्च (या शेतासाठी)</td><td>{rupees(cost)}</td></tr>'
            f'<tr><td>या हंगामातील उत्पादन</td><td>{harvest}</td></tr>'
            f'<tr class="hl"><td>या वर्षी हातात उरणारे (अंदाजे)</td><td>{rupees(margin)}</td></tr>'
            f'<tr><td>सर्वसाधारण पावसाच्या वर्षी उरले असते</td><td>{rupees(normal)}</td></tr></table>'
            f'<p class="small">हे आकडे तुमच्यासोबत बसून, विदर्भातील खर्च आणि २०२६-२७ च्या हमीभावावरून काढले. '
            f'कापूस अजून वेचायचा आहे, म्हणून त्याचे आकडे अपेक्षित उत्पादनाचे आहेत. '
            f'तुमच्या लिहून ठेवलेल्या नोंदी आल्या की हे आकडे बदलतील.</p>')


def qtl(prod):
    return "<br>".join(f"{CROP[c]} {mr(f'{q:.1f}')} क्वि." for c, q, _ in prod)


def price(prod):
    return "<br>".join(f"{CROP[c]} {rupees(p)}" for c, _, p in prod)


def money_two_years(zone, num, crops, est):
    """Good monsoon year next to this year. Empty cells when est is None."""
    def cell(v):
        return f'<td class="est">{v}</td>' if est else '<td class="blank"></td>'
    g, n = (est["good"], est["now"]) if est else ({}, {})
    rows = [("एकूण खर्च", lambda a: rupees(a["cost"])),
            ("उत्पादन", lambda a: qtl(a["prod"])),
            ("भाव (₹ / क्विंटल)", lambda a: price(a["prod"])),
            ("उत्पन्न (विक्रीचे पैसे)", lambda a: rupees(a["rev"])),
            ("हातात उरणारे (नफा / तोटा)", lambda a: rupees(a["net"]))]
    body = "".join(f'<tr{" class=hl" if i == 4 else ""}><td>{lab}</td>'
                   + (cell(fn(g)) + cell(fn(n)) if est else cell(0) + cell(0)) + "</tr>"
                   for i, (lab, fn) in enumerate(rows))
    if not est:
        now = '<td class="blank"></td>'
    elif (zone, num) == ("sawardoh", 2):
        now = '<td class="est">कापसाचा विमा नाही</td>'
    else:
        now = f'<td class="est">{rupees(est["claim"])}</td>'
    claim = '<td class="na">—</td>' + now
    body += f"<tr><td>विमा भरपाई (मिळाली / मिळेल)</td>{claim}</tr>"
    note = ("हे आकडे <b>माझा अंदाज</b> आहेत: बाजारभाव, हमीभाव २०२६-२७, मजुरी आणि विदर्भातील एकरी खर्चावरून. "
            "हे शेतकऱ्याचे उत्तर नाही. "
            + ("कापूस अजून वेचायचा आहे, म्हणून यंदाचे उत्पादन अपेक्षित आहे." if "कापूस" in crops
               else "सोयाबीन काढून झाले; " + ("तूर अजून उभी आहे, तिचे उत्पादन अपेक्षित आहे." if "तूर" in crops
                                               else "उत्पादन माझ्या अंदाजाने धरले आहे."))
            if est else
            "चांगल्या पावसाच्या वर्षी किती खर्च आणि उत्पन्न होते, आणि यंदा किती झाले, ते तुमच्या अंदाजाने सांगा. "
            "खर्चाचा तपशील अभिप्राय फॉर्ममध्ये आहे.")
    return (f'<table class="money two"><tr class="th"><td></td><td>चांगल्या पावसाचे वर्ष</td><td>यंदा (दुष्काळ)</td></tr>'
            f'{body}</table><p class="small">{note}</p>')


def insurance_lines(zone, num, ha, est):
    """The insurance facts I still need from each field, filled with my estimate or left empty."""
    def v(x, w="22mm"):
        return f'<span class="est">{x}</span>' if est else f'<span class="bl" style="width:{w}"></span>'
    if est is None:
        return (f'<p class="fill">पीक {v(0)} &nbsp; क्षेत्र {v(0, "18mm")} हे.<br>'
                f'संरक्षित रक्कम ₹{v(0)} &nbsp; हप्ता ₹{v(0, "18mm")}<br>'
                f'नुकसानाची तक्रार केली: होय / नाही &nbsp; भरपाई ₹{v(0, "18mm")}</p>')
    import estimate_whole_farm as E
    f = next(x for x in E.FIELDS if x[0] == zone and x[1] == num)
    orng = f[6]
    prem = est["now"]["heads"].get("prem", 0)
    if (zone, num) == ("sawardoh", 2):
        crop, area, si = CROP["orange"], ha * orng, "सुमारे १ लाख / हे."
        claim = "हवामानावर अवलंबून"
    else:
        crop, area, si = CROP[f[4]], ha * (1 - orng), rupees(E.SI[f[4]]) + " / हे."
        claim = rupees(est["claim"])
    return (f'<p class="fill">पीक {v(crop)} &nbsp; क्षेत्र {v(mr(f"{area:.2f}"))} हे.<br>'
            f'संरक्षित रक्कम {v(si)} &nbsp; हप्ता {v(rupees(prem))}<br>'
            f'नुकसानाची तक्रार केली: होय / नाही &nbsp; भरपाई {v(claim)}</p>')


def insurance_block(ins, code, zone, num):
    for _, r in ins.iterrows():
        if r["farmer_code"] != code or r["zone"] != zone:
            continue
        if str(num) in str(r["field"]).split(";"):
            crop = str(r.get("crop_insured", ""))
            if "orange only" in crop:
                return ("या शेतात फक्त <b>संत्र्याचा</b> विमा आहे (हवामान आधारित फळपीक विमा). "
                        "याच शेतातील <b>कापसाचा विमा नाही</b>.")
            if str(r.get("enrolled", "")).strip().lower().startswith("no"):
                return "या हंगामात या शेतावर <b>पीक विमा नाही</b>."
            if str(r.get("enrolled", "")).strip().lower().startswith("yes"):
                return "या शेताचा पीक विमा आहे, असे तुम्ही सांगितले."
            return html.escape(crop)
    return "माहिती नाही. तुम्हाला सांगायचे असेल तर खाली लिहा."


def card(ft, code, money_row, ins, passes, mode="blank"):
    p = ft["properties"]
    zone, num, ha = p["zone"], int(p["field_num"]), float(p["area_ha"])
    sown = dt.date.fromisoformat(p["sown"])
    crops = ", ".join(CROP.get(c, c) for c in p["crops"])
    sel = passes[(passes.zone == zone) & (passes.field_num == num) & (passes.usable_look == True)]
    dates = sorted({dt.date.fromisoformat(d) for d in sel.date})
    after = [d for d in dates if d >= sown]
    tl, gap = timeline_svg(dates, sown)
    est = None
    if mode == "estimate":
        import estimate_whole_farm as E
        est = E.account(zone, num)
    if mode == "figures":
        money, ins_extra = money_block(money_row, ha), ""
    else:
        money, ins_extra = money_two_years(zone, num, crops, est), insurance_lines(zone, num, ha, est)
    banner = ('<div class="banner">अंदाज · हे आकडे माझे अंदाजे आकडे आहेत, शेतकऱ्याचे उत्तर नाही</div>'
              '<div class="wm">अंदाज</div>' if est else "")

    return f"""
<section class="page">{banner}
  <header>
    <div><div class="kicker">रूट्स अँड रिफ्लेक्टन्स · खरीप २०२६</div>
      <h1>शेत कार्ड: {VILLAGE[zone]}, शेत {mr(num)}</h1>
      <div class="sub">पीक: {crops} · पेरणी {mr_date(sown)} · शेतकरी कोड {code}</div></div>
    <div class="namebox">शेतकऱ्याचे नाव<br><span></span></div>
  </header>

  <div class="row">
    <div class="box half"><h2>१. तुमचे शेत</h2>{field_svg(ft["geometry"])}
      <p>{area_lines(ha)}</p>
      <p class="small">ही हद्द मी स्वतः शेताच्या कडेने GPS घेऊन चालून मोजली आहे.</p>
      <p class="fill">७/१२ वरील क्षेत्र: ____________ &nbsp; विम्यात दाखवलेले क्षेत्र: ____________</p></div>
    <div class="box half"><h2>३. या हंगामाचा हिशोब</h2>{money}</div>
  </div>

  <div class="box"><h2>२. उपग्रहाने तुमचे शेत कधी पाहिले?</h2>{tl}
    <p>पेरणीपासून {mr_date(dates[-1])} पर्यंत उपग्रह अनेक वेळा वरून गेला, पण तुमचे शेत फक्त
    <b>{mr(len(after))} वेळा</b> स्वच्छ दिसले (निळे ठिपके). <b>{mr_date(gap[0])} ते {mr_date(gap[1])}</b>,
    म्हणजे <b>{mr((gap[1] - gap[0]).days)} दिवस</b>, ढगांमुळे शेत दिसलेच नाही. याच आठवड्यांत पीक वाढले.
    पीक विम्यात उपग्रहावर आधारित उत्पादन अंदाज वापरला जाऊ लागला आहे, आणि त्याला हा काळ दिसत नाही.</p></div>

  <div class="row">
    <div class="box half"><h2>४. विमा</h2><p>{insurance_block(ins, code, zone, num)}</p>{ins_extra}</div>
    <div class="box half"><h2>५. तुम्ही काय करू शकता</h2><ol>
      <li>पिकाचे नुकसान झाले तर <b>तारीख असलेले फोटो</b> स्वतः काढून ठेवा. उपग्रहाकडे त्या दिवसांचा पुरावा नसू शकतो.</li>
      <li><b>ई-पीक पाहणीत</b> तुमचे पीक आणि क्षेत्र बरोबर नोंदले आहे का, ते तपासा.</li>
      <li>खर्च, मजुरी, उत्पादन आणि विक्री <b>त्याच दिवशी लिहून ठेवा</b>. पुढच्या वर्षीचा हिशोब तुमच्याच नोंदींतून होईल.</li>
    </ol></div>
  </div>

  <div class="box"><h2>तुमचे मत आणि तुम्ही काय ठरवले</h2>
    <div class="lines"><span></span><span></span><span></span></div>
    <p class="fill">दिनांक: __________ &nbsp; माहिती वापरायला संमती: होय / नाही &nbsp; सही / अंगठा: __________</p></div>

  <footer>रूट्स अँड रिफ्लेक्टन्स · तयार केले: साक्षी मस्के · {mr_date(PRINT_DATE)} {mr(PRINT_DATE.year)}</footer>
</section>"""


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');
@page { size: A4; margin: 10mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Noto Sans Devanagari', 'Nirmala UI', 'Mangal', sans-serif;
       color: #1d1d1d; background: #fff; font-size: 13px; line-height: 1.45; }
.page { width: 190mm; min-height: 275mm; margin: 0 auto; padding: 4mm 0; page-break-after: always; }
header { display: flex; justify-content: space-between; align-items: flex-start;
         border-bottom: 3px solid #2f5d1e; padding-bottom: 6px; margin-bottom: 8px; }
.kicker { font-size: 11px; letter-spacing: .04em; color: #2f5d1e; font-weight: 600; }
h1 { font-size: 22px; margin: 2px 0; }
.sub { color: #444; }
.namebox { border: 1px solid #999; padding: 4px 8px; width: 62mm; font-size: 11px; color: #555; }
.namebox span { display: block; height: 22px; }
h2 { font-size: 15px; margin: 0 0 4px; color: #2f5d1e; }
.box { border: 1px solid #cfcfcf; border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; }
.row { display: flex; gap: 8px; }
.half { flex: 1; }
.map { width: 100%; height: 150px; }
.tl { width: 100%; height: 70px; }
.money { width: 100%; border-collapse: collapse; }
.money td { padding: 4px 2px; border-bottom: 1px solid #e6e6e6; }
.money td:last-child { text-align: right; white-space: nowrap; font-weight: 600; }
.money .hl td { background: #eef5e8; }
.small { font-size: 11px; color: #555; margin: 4px 0; }
.fill { font-size: 12px; margin: 6px 0 0; }
ol { margin: 0; padding-left: 18px; }
li { margin-bottom: 4px; }
.lines span { display: block; border-bottom: 1px solid #999; height: 24px; }
.page { position: relative; }
.money.two td { font-size: 12px; vertical-align: top; }
.money.two td:not(:first-child) { text-align: right; width: 30%; }
.money.two .th td { font-size: 11px; color: #2f5d1e; font-weight: 600; border-bottom: 1.5px solid #2f5d1e; }
.money td.blank { height: 26px; border-bottom: 1px solid #999; }
.money td.na { color: #aaa; text-align: center !important; font-weight: 400; }
.est { color: #1a4fa0; font-weight: 600; }
span.est { border-bottom: 1px dotted #1a4fa0; padding: 0 2px; }
.bl { display: inline-block; border-bottom: 1px solid #666; height: 15px; vertical-align: bottom; }
.banner { background: #e7eefb; color: #1a4fa0; border: 1px solid #1a4fa0; border-radius: 4px; font-size: 12px;
          font-weight: 600; text-align: center; padding: 2px 6px; margin-bottom: 4px; }
.wm { position: absolute; top: 42%; left: 0; right: 0; text-align: center; font-size: 150px; font-weight: 700;
      color: rgba(26, 79, 160, .06); transform: rotate(-28deg); pointer-events: none; z-index: 0; }
footer { font-size: 10.5px; color: #666; border-top: 1px solid #ddd; padding-top: 4px; }
"""


def main(mode):
    fields, owners, money, ins, passes = load()
    out = os.path.join(OUT, "estimate") if mode == "estimate" else OUT
    os.makedirs(out, exist_ok=True)
    for code, grp in owners.groupby("farmer_code"):
        pages = []
        for _, o in grp.sort_values(["zone", "field"]).iterrows():
            key = (o["zone"], int(o["field"]))
            m = money[(money.zone == key[0]) & (money.field == key[1])]
            row = m.iloc[0].to_dict() if len(m) else None
            pages.append(card(fields[key], code, row, ins, passes, mode))
        doc = (f'<!doctype html><html lang="mr"><head><meta charset="utf-8">'
               f'<meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>शेत कार्ड · {code}</title><style>{CSS}</style></head><body>'
               + "".join(pages) + "</body></html>")
        path = os.path.join(out, f"farmer_{code}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"{path}  ({len(pages)} page{'s' if len(pages) > 1 else ''})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a[2:] for a in sys.argv[1:] if a.startswith("--")]
    PRINT_DATE = dt.date.fromisoformat(args[0]) if args else dt.date.today()
    main(flags[0] if flags else "blank")
