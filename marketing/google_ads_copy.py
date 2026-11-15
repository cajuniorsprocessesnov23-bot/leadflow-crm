import json
common_h=["Request a Call Back","Checklist on WhatsApp","Serving All of India","Legal Wegal Experts"]
common_d=["Share your details in 20 seconds. Our team calls you and sends a checklist on WhatsApp.",
          "Talk to our team 9 AM to 8 PM. Filing done for you, with updates at every step."]
G={
 "GST":{"s":"gst","path":["GST","Registration"],
  "h":["GST Registration Online","Get Your GST Number","GST Registration Experts","GST Return Filing Help","New GSTIN in Few Steps","GST Changes & Amendments"],
  "d":["New GST registration, returns and changes handled by our team. Request a call back.",
       "Not sure about regular or composition scheme? Our team guides you. Get a call back."],
  "k":["gst registration","gst registration online","new gst registration","apply for gst number","gst number apply","gst registration consultant","gst return filing","gst registration near me"]},
 "Trademark":{"s":"trademark","path":["Trademark","Registration"],
  "h":["Trademark Registration","Register Your Brand Name","Trademark Filing Online","Protect Your Brand Today","Logo & Name Registration","Trademark Objection Reply"],
  "d":["Trademark search, filing and objection replies handled by our team. Get a call back.",
       "Protect your brand name and logo. Our team checks the right class before you file."],
  "k":["trademark registration","trademark registration online","register brand name","brand name registration","logo registration","trademark filing","apply for trademark","trademark registration consultant"]},
 "IEC":{"s":"iec","path":["IEC","Import-Export"],
  "h":["IEC Registration Online","Get Import Export Code","Apply for IEC Today","IEC for Importers","IEC for Exporters","IEC Update & Changes"],
  "d":["Start importing or exporting with an IEC from DGFT. Our team files it for you.",
       "Import Export Code application handled by our team. Request a call back today."],
  "k":["iec registration","import export code","iec code apply","apply for iec","import export license","iec registration online","iec code registration"]},
 "FSSAI":{"s":"fssai","path":["FSSAI","Food-Licence"],
  "h":["FSSAI Registration Online","Get Your Food Licence","FSSAI Licence Experts","FSSAI State & Central","FSSAI Basic Registration","FSSAI Renewal Help"],
  "d":["Basic registration, state or central FSSAI licence handled by our team. Get a call back.",
       "Not sure which FSSAI licence you need? Our team guides you. Request a call back."],
  "k":["fssai registration","fssai license","fssai licence","food license apply","fssai registration online","food license registration","fssai license apply online","fssai renewal"]},
 "HUID":{"s":"huid","path":["HUID","Hallmarking"],
  "h":["BIS Hallmark Registration","HUID Hallmarking Help","Registration for Jewellers","BIS Jeweller Registration","Hallmark Licence Help","Get Ready for HUID"],
  "d":["BIS registration and HUID hallmarking help for jewellers. Request a call back today.",
       "Get your jewellery shop ready for mandatory hallmarking. Our team guides every step."],
  "k":["huid registration","bis hallmark registration","hallmark license","hallmark registration for jewellers","bis registration for jewellers","huid hallmarking","hallmark licence apply"]},
}
neg=["free","job","jobs","salary","course","pdf","syllabus","login","download","wikipedia","meaning","exam","internship","status","certificate download","portal","sample","format","template","vacancy","training"]
bad=[]
for g,v in G.items():
  v["h"]=v["h"]+common_h; v["d"]=v["d"]+common_d
  for h in v["h"]:
    if len(h)>30: bad.append((g,h,len(h)))
  for d in v["d"]:
    if len(d)>90: bad.append((g,d,len(d)))
  for p in v["path"]:
    if len(p)>15: bad.append((g,p))
print(bad)
json.dump({"groups":G,"neg":neg},open("ads.json","w"),indent=1)
