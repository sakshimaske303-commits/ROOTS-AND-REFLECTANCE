"""
ROOTS & REFLECTANCE: a two-page Marathi survey form for each farmer.

I fill it in on a visit and copy the answers into data/farmer_survey_2026.csv under the
same question ids, and the cost table into data/farmer_costs_2026.csv. The last part is a
receipt the farmer signs.

  --blank     the form I carry to the farmer (default)
  --estimate  the same form filled with my own estimate (private/estimate_whole_farm.py),
              so I can put the farmer's answers next to it afterwards

Out: private/feedback_forms/farmer_<code>.html  (estimate: private/feedback_forms/estimate/)
Usage: python src/feedback_form.py [--blank | --estimate]
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "private", "feedback_forms")
sys.path.insert(0, os.path.join(ROOT, "private"))

VILLAGE = {"sawardoh": "सावरडोह", "karanja": "कारंजा घाडगे"}
CROP = {"cotton": "कापूस", "tur": "तूर", "soyabean": "सोयाबीन", "orange": "संत्रा"}
DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
BOX = '<span class="bx"></span>'


def mr(x):
    return str(x).translate(DIGITS)


def opts(*labels):
    return " ".join(f'<span class="opt">{BOX}{l}</span>' for l in labels)


def blank(w=30):
    return f'<span class="bl" style="width:{w}mm"></span>'


def rupees(x):
    """Indian grouping in Devanagari digits: ₹१,२३,४५६."""
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


def est(x):
    return f'<span class="est">{x}</span>'


def fq(q_):
    return mr(f"{q_:.1f}")


def q(qid, text, answer=""):
    return f'<div class="q"><span class="qid">{qid}</span><div class="qt">{text}</div><div class="qa">{answer}</div></div>'


def page_one(code, fields_txt, E=None):
    """E: my estimate per field, {(zone, field): (label, account)}; None for the blank form."""
    a4 = blank(14) + " पोती × " + blank(12) + " किलो = " + blank(14) + " क्विंटल"
    a5 = (opts("अजून नाही", "बाजार समिती", "व्यापारी", "CCI / नाफेड") + "<br>किती " + blank(16)
          + " क्विंटल &nbsp; भाव ₹" + blank(18) + " / क्विंटल &nbsp; पावती " + opts("आहे", "नाही"))
    a6 = blank(18) + " क्विंटल"
    a7 = ("पीक " + blank(26) + " क्षेत्र " + blank(18) + " हप्ता ₹" + blank(18)
          + "<br>कुठे भरला: " + opts("बँक", "सेतू / CSC", "स्वतः ॲपवर"))
    a9 = ("यंदा " + opts("नाही", "होय") + " ₹" + blank(18) + " &nbsp; मागच्या वर्षी "
          + opts("होय", "नाही", "विमा नव्हता"))
    if E:
        import estimate_whole_farm as M

        def prod(a):
            return ", ".join(f"{CROP[c]} {fq(x)}" for c, x, _ in a["prod"])
        a4 = "<br>".join(est(f"{lab}: {prod(a['now'])} क्विंटल (अपेक्षित; कापूस वेचणी जानेवारीत)") for lab, a in E.values())
        a5 = est("अजून विक्री नाही. अपेक्षित भाव: " + ", ".join(
            sorted({f"{CROP[c]} {rupees(p)}" for _, a in E.values() for c, _, p in a["now"]["prod"]})))
        a6 = "<br>".join(est(f"{lab}: {prod(a['good'])} क्विंटल") for lab, a in E.values())
        lines7, lines9 = [], []
        for (zone, num), (lab, a) in E.items():
            f = next(x for x in M.FIELDS if x[0] == zone and x[1] == num)
            prem = rupees(a["now"]["heads"].get("prem", 0))
            if (zone, num) == ("sawardoh", 2):
                lines7.append(est(f"{lab}: संत्रा, {mr(f'{f[3] * f[6]:.2f}')} हे., हप्ता {prem} (कापसाचा विमा नाही)"))
                lines9.append(est(f"{lab}: संत्र्याची भरपाई हवामानावर अवलंबून"))
            else:
                lines7.append(est(f"{lab}: {CROP[f[4]]}, {mr(f'{f[3] * (1 - f[6]):.2f}')} हे., हप्ता {prem}"))
                lines9.append(est(f"{lab}: {rupees(a['claim'])} (अंदाज, महसूल मंडळातील उत्पादनावर)"))
        a7 = "<br>".join(lines7)
        a9 = "<br>".join(lines9)
    return f"""
<section class="page">{BANNER if E else ""}
  <header><div><div class="kicker">रूट्स अँड रिफ्लेक्टन्स · खरीप २०२६</div>
    <h1>शेतकरी अभिप्राय</h1>
    <div class="sub">शेतकरी कोड {code} · {fields_txt}</div></div>
    <div class="meta">दिनांक {blank(32)}<br>भेट: प्रत्यक्ष</div></header>
  <p class="intro">ही माहिती माझ्या अभ्यासासाठी आहे. तुमचे नाव कुठेही लिहिले जाणार नाही. आधार, बँक, ७/१२ किंवा फोन नंबर विचारले जाणार नाहीत. कोणत्याही प्रश्नाचे उत्तर द्यायचे नसेल तर सोडून द्या.</p>

  <h2>अ. नकाशा आणि हिशोब</h2>
  {q("q1", "शेताचा नकाशा, क्षेत्र आणि हिशोब मिळाला का?", opts("होय", "नाही") + " &nbsp; कधी " + blank(25))}
  {q("q2", "७/१२ वरील क्षेत्र किती? नकाशातील क्षेत्राशी जुळते का?", blank(22) + " हे. आर &nbsp; " + opts("जुळते", "थोडा फरक", "जुळत नाही"))}
  {q("q3", "हिशोबातील आकडे बरोबर वाटले का?", opts("होय", "बदल हवा") + " &nbsp; काय " + blank(45))}

  <h2>ब. उत्पादन आणि विक्री</h2>
  {q("q4", "या हंगामात किती उत्पादन निघाले?", a4)}
  {q("q5", "विक्री कुठे केली?", a5)}
  {q("q6", "सर्वसाधारण पावसाच्या वर्षी किती उत्पादन निघते?", a6)}

  <h2>क. पीक विमा</h2>
  {q("q7", "यंदा कोणत्या पिकाचा विमा काढला? किती क्षेत्राचा? हप्ता किती भरला?", a7)}
  {q("q8", "नुकसानाची तक्रार केली का? पंचनामा झाला का?", opts("नाही", "होय") + " &nbsp; कशी: " + opts("ॲप", "टोल फ्री", "कृषी कार्यालय") + "<br>दिनांक " + blank(22) + " &nbsp; पंचनामा " + opts("झाला", "नाही"))}
  {q("q9", "भरपाई मिळाली का? मागच्या वर्षी मिळाली होती का?", a9)}
  {q("q10", "पुढच्या वर्षी विमा काढणार का? का?", opts("होय", "नाही", "ठरवले नाही") + " &nbsp; कारण " + blank(48))}
</section>"""


def page_costs(fields, E=None):
    """Cost head by cost head for each of the farmer's fields, a good monsoon year next to
    this year. fields: [(zone, num, label, crops)]."""
    import estimate_whole_farm as M
    crops = {c for *_, cs in fields for c in cs}
    rows = [(k, lab) for k, lab in M.ROWS
            if not (k == "tur" and "tur" not in crops) and not (k == "orange" and "orange" not in crops)
            and not (k == "micro" and "cotton" not in crops)]
    accts = [E[(z, n)][1] if E else None for z, n, *_ in fields]

    def cell(a, yr, fn):
        return f'<td class="v est">{fn(a[yr])}</td>' if a else '<td class="v"></td>'
    head = "".join(f'<th colspan="2">{lab}</th>' for _, _, lab, _ in fields)
    sub = "".join('<th>चांगले वर्ष</th><th>यंदा</th>' for _ in fields)
    body = ""
    for k, lab in rows:
        body += f"<tr><td>{lab}</td>" + "".join(
            cell(a, yr, lambda x, k=k: rupees(x["heads"][k]) if x["heads"].get(k) else "—")
            for a in accts for yr in ("good", "now")) + "</tr>"
    summary = [("एकूण खर्च", lambda x: rupees(x["cost"])),
               ("उत्पादन (क्विंटल)", lambda x: "<br>".join(f"{CROP[c]} {fq(q_)}" for c, q_, _ in x["prod"])),
               ("भाव (₹ / क्विंटल)", lambda x: "<br>".join(f"{CROP[c]} {rupees(p)}" for c, _, p in x["prod"])),
               ("उत्पन्न (विक्रीचे पैसे)", lambda x: rupees(x["rev"])),
               ("हातात उरणारे (नफा / तोटा)", lambda x: rupees(x["net"]))]
    for i, (lab, fn) in enumerate(summary):
        body += f'<tr class="{"tot" if i in (0, 4) else "sum"}"><td>{lab}</td>' + "".join(
            cell(a, yr, fn) for a in accts for yr in ("good", "now")) + "</tr>"

    if E:
        g = sum(a["good"]["cost"] for a in accts); n = sum(a["now"]["cost"] for a in accts)
        gr = sum(a["good"]["rev"] for a in accts); nr = sum(a["now"]["rev"] for a in accts)
        h1 = est(f"फक्त या शेतांचा खरीप: चांगले वर्ष {rupees(g)}, यंदा {rupees(n)}") + "<br>संपूर्ण शेती: चांगले वर्ष ₹" + blank(22) + " यंदा ₹" + blank(22)
        h2 = est(f"फक्त या शेतांचा खरीप: चांगले वर्ष {rupees(gr)}, यंदा {rupees(nr)}") + "<br>संपूर्ण शेती: चांगले वर्ष ₹" + blank(22) + " यंदा ₹" + blank(22)
    else:
        h1 = "चांगल्या वर्षी ₹" + blank(26) + " &nbsp; यंदा ₹" + blank(26)
        h2 = "चांगल्या वर्षी ₹" + blank(26) + " &nbsp; यंदा ₹" + blank(26)
    return f"""
<section class="page costs">{BANNER if E else ""}
  <h2>फ. खर्च आणि उत्पन्नाचा हिशोब (प्रत्येक शेताचा)</h2>
  <p class="intro">एकूण रुपये, या शेतासाठी. घरच्या लोकांची मजुरी यात धरलेली नाही. आठवत नसेल तर अंदाजे सांगा, किंवा “—” लिहा.</p>
  <table class="ct"><tr><th class="lab">खर्च</th>{head}</tr><tr><th></th>{sub}</tr>{body}</table>

  <h2>ग. संपूर्ण शेती, वर्षभर</h2>
  {q("h1", "संपूर्ण शेतीचा वर्षभराचा खर्च किती होतो? (खरीप, रब्बी आणि इतर सगळे)", h1)}
  {q("h2", "संपूर्ण शेतीचे वर्षभराचे उत्पन्न किती होते?", h2)}
  {q("h3", "सालगडी / कायम मजूर आहे का? वर्षाला किती?", opts("आहे", "नाही") + " &nbsp; ₹" + blank(26) + " / वर्ष")}
  {q("h4", "शेतीपंपाचे वीज बिल, डिझेल, पाईप-मोटार दुरुस्ती वर्षाला किती?", "₹" + blank(26) + " / वर्ष")}
  {q("h5", "बैलजोडी / ट्रॅक्टर: स्वतःचा की भाड्याने? देखभाल, हप्ता वर्षाला किती?", opts("स्वतःचा", "भाड्याने") + " &nbsp; ₹" + blank(26) + " / वर्ष")}
  {q("h6", "रब्बीत कोणते पीक घेता? किती क्षेत्र, खर्च आणि उत्पन्न?", "पीक " + blank(24) + " क्षेत्र " + blank(16) + " खर्च ₹" + blank(20) + " उत्पन्न ₹" + blank(20))}
  {q("h7", "घरच्या लोकांनी किती दिवस काम केले? शेती बटाईने / भाड्याने दिली किंवा घेतली आहे का?", blank(16) + " दिवस &nbsp; " + opts("नाही", "दिली", "घेतली") + " खंड ₹" + blank(20))}
</section>"""


def page_two(code, E=None):
    return f"""
<section class="page">{BANNER if E else ""}
  <h2>ड. शासकीय मदत</h2>
  {q("q11", "ई-पीक पाहणी केली का? पीक बरोबर नोंदले आहे का?", opts("स्वतः केली", "सहाय्यकाकडून", "नाही") + " &nbsp; नोंद " + opts("बरोबर", "चूक", "माहिती नाही"))}
  {q("q12", "कारंजा तालुका दुष्काळ यादीत आला, हे माहीत आहे का? काही सवलत किंवा मदत मिळाली का?", opts("माहीत आहे", "माहीत नाही") + " &nbsp; मदत " + blank(50))}
  {q("q13", "कर्जमाफी: पीक कर्ज आहे का? यादीत नाव आले का?", "कर्ज " + opts("आहे", "नाही") + " &nbsp; यादीत " + opts("आले", "नाही आले", "माहिती नाही"))}
  {q("q14", "यंदा इतर कोणती शासकीय मदत मिळाली?", blank(110))}

  <h2>इ. कार्डचा उपयोग</h2>
  {q("q15", "शेत कार्ड उपयोगी वाटले का? कशासाठी?", opts("खूप", "थोडे", "नाही") + " &nbsp; " + blank(60))}
  {q("q16", "कार्ड पाहिल्यानंतर काय केले किंवा ठरवले?", opts("विमा तपासला", "ई-पीक पाहणी दुरुस्त केली", "क्षेत्र तपासले", "खर्च लिहायला सुरुवात") + "<br>" + opts("काही नाही") + " इतर " + blank(60))}
  {q("q17", "पुढे नुकसान झाले तर दिनांकासह फोटो काढून ठेवणार का?", opts("होय", "नाही"))}
  {q("q18", "रब्बीत काय पेरणार? पाण्याची सोय कोणती?", opts("हरभरा", "गहू", "काही नाही") + " इतर " + blank(22) + " &nbsp; पाणी " + opts("विहीर", "कालवा", "नाही"))}
  {q("q19", "यंदाची सगळ्यात मोठी अडचण कोणती होती?", blank(110))}
  {q("q20", "सरकारला एक गोष्ट सांगायची असेल तर काय सांगाल?", blank(110) + "<br>" + blank(110))}

  <div class="consent"><h2>संमती</h2>
    <p>माझे नाव न देता ही माहिती अभ्यासात वापरायला संमती: {opts("होय", "नाही")} &nbsp; चेहरा नसलेले शेताचे फोटो वापरायला: {opts("होय", "नाही")}</p>
    <p>सही / अंगठा {blank(50)} &nbsp; दिनांक {blank(30)}</p></div>

  <div class="mine"><b>For my records</b> · Visit time {blank(18)} · Proof collected:
    {opts("sale receipt photo", "insurance slip photo", "7/12 area seen", "card-in-hand photo", "GPS track")}
    · Follow up on {blank(24)}</div>

  <div class="receipt"><div class="cut">✂ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -</div>
    <h2>पोच पावती</h2>
    <p>मला माझ्या शेताचा नकाशा, मोजलेले क्षेत्र आणि या हंगामाचा हिशोब मिळाला. (शेतकरी कोड {code})</p>
    <p>सही / अंगठा {blank(50)} &nbsp; दिनांक {blank(30)}</p></div>
</section>"""


BANNER = ('<div class="banner">अंदाज · निळे आकडे माझे अंदाजे आकडे आहेत, शेतकऱ्याचे उत्तर नाही</div>'
          '<div class="wm">अंदाज</div>')

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');
@page { size: A4; margin: 10mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Noto Sans Devanagari', 'Nirmala UI', 'Mangal', sans-serif;
       color: #1d1d1d; background: #fff; font-size: 12.5px; line-height: 1.5; }
.page { width: 190mm; min-height: 275mm; margin: 0 auto; padding: 3mm 0; page-break-after: always; }
header { display: flex; justify-content: space-between; border-bottom: 3px solid #2f5d1e;
         padding-bottom: 5px; margin-bottom: 6px; }
.kicker { font-size: 11px; color: #2f5d1e; font-weight: 600; }
h1 { font-size: 22px; margin: 0; }
.sub { color: #444; }
.meta { text-align: right; font-size: 12px; }
.intro { font-size: 11.5px; background: #f4f7f1; padding: 6px 8px; border-radius: 4px; margin: 4px 0 8px; }
h2 { font-size: 14.5px; color: #2f5d1e; margin: 10px 0 4px; border-bottom: 1px solid #d8e4cf; }
.q { display: grid; grid-template-columns: 9mm 1fr; padding: 4px 0 6px; border-bottom: 1px dotted #ccc; }
.qid { font-size: 10px; color: #999; padding-top: 2px; }
.qt { font-weight: 600; }
.qa { grid-column: 2; margin-top: 3px; }
.opt { margin-right: 10px; white-space: nowrap; }
.bx { display: inline-block; width: 11px; height: 11px; border: 1.2px solid #333; margin-right: 4px; vertical-align: -1px; }
.bl { display: inline-block; border-bottom: 1px solid #666; height: 16px; vertical-align: bottom; }
.consent { border: 1.5px solid #2f5d1e; border-radius: 6px; padding: 4px 10px; margin-top: 10px; }
.consent h2 { border: 0; margin-top: 4px; }
.consent p { margin: 6px 0; }
.mine { font-size: 10.5px; color: #555; margin-top: 8px; padding: 5px 8px; background: #f6f6f6; border-radius: 4px; }
.receipt { margin-top: 12px; }
.cut { color: #999; font-size: 11px; overflow: hidden; white-space: nowrap; }
.receipt p { margin: 6px 0; }
.page { position: relative; }
.est { color: #1a4fa0; font-weight: 600; }
.banner { background: #e7eefb; color: #1a4fa0; border: 1px solid #1a4fa0; border-radius: 4px; font-size: 12px;
          font-weight: 600; text-align: center; padding: 2px 6px; margin-bottom: 4px; }
.wm { position: absolute; top: 40%; left: 0; right: 0; text-align: center; font-size: 150px; font-weight: 700;
      color: rgba(26, 79, 160, .06); transform: rotate(-28deg); pointer-events: none; z-index: 0; }
table.ct { width: 100%; border-collapse: collapse; font-size: 11.5px; }
.ct th { font-size: 11px; color: #2f5d1e; border-bottom: 1.5px solid #2f5d1e; padding: 2px 4px; text-align: center; }
.ct th.lab { text-align: left; }
.ct td { border-bottom: 1px solid #ccc; padding: 1px 4px; height: 19px; vertical-align: top; }
.costs .q { padding: 3px 0 4px; }
.ct td.v { border-left: 1px solid #e3e3e3; text-align: right; width: 19%; white-space: nowrap; }
.ct tr.tot td { font-weight: 700; background: #f2f6ee; }
.ct tr.sum td { background: #fafafa; }
"""


def main(mode="blank"):
    owners = pd.read_csv(os.path.join(ROOT, "data", "field_owners.csv"))
    with open(os.path.join(ROOT, "data", "field_boundaries.geojson"), encoding="utf-8") as f:
        props = {(ft["properties"]["zone"], int(ft["properties"]["field_num"])): ft["properties"]
                 for ft in json.load(f)["features"]}
    out = os.path.join(OUT, "estimate") if mode == "estimate" else OUT
    os.makedirs(out, exist_ok=True)
    if mode == "estimate":
        import estimate_whole_farm as M
    for code, grp in owners.groupby("farmer_code"):
        parts, fields, E = [], [], {}
        for _, o in grp.sort_values(["zone", "field"]).iterrows():
            z, n = o["zone"], int(o["field"])
            p = props[(z, n)]
            crops = ", ".join(CROP.get(c, c) for c in p["crops"])
            parts.append(f'{VILLAGE[z]} शेत {mr(n)} ({crops})')
            label = f"शेत {mr(n)}" if z == "sawardoh" else f"कारंजा शेत {mr(n)}"
            fields.append((z, n, label, p["crops"]))
            if mode == "estimate":
                E[(z, n)] = (label, M.account(z, n))
        E = E or None
        doc = (f'<!doctype html><html lang="mr"><head><meta charset="utf-8">'
               f'<meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>शेतकरी अभिप्राय · {code}</title><style>{CSS}</style></head><body>'
               + page_one(code, " · ".join(parts), E) + page_costs(fields, E) + page_two(code, E)
               + "</body></html>")
        path = os.path.join(out, f"farmer_{code}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)
        print(path)


if __name__ == "__main__":
    flags = [a[2:] for a in sys.argv[1:] if a.startswith("--")]
    main(flags[0] if flags else "blank")
