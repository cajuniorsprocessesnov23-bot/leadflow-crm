# Service content: GST, Trademark & IP. Original text written for Legal Wegal (18 Nov 2026).
# Fields: n=name/H1, c=category, crm=CRM service name for live price, d=intro, who, docs, steps, time, faqs
S = {}

S["gst-registration"] = dict(n="GST Registration", c="gst", crm="GST",
 d="GST registration gives your business a 15-digit GSTIN so you can collect GST, claim input tax credit and sell across states and on marketplaces. We prepare the application, upload your documents on the GST portal, handle any clarification notice from the officer and send you the certificate.",
 who=["Businesses whose turnover crosses the GST threshold (₹40 lakh for most goods suppliers, ₹20 lakh for service providers; lower in special-category states)",
      "Anyone selling across state borders or through e-commerce marketplaces",
      "Exporters, importers and businesses that want to claim input tax credit",
      "Casual taxable persons and non-resident suppliers"],
 docs=["PAN of the business or proprietor","Aadhaar of the proprietor / partners / directors","Passport-size photograph","Address proof of the business (electricity bill, property tax receipt or rent agreement with owner's NOC)","Bank proof (cancelled cheque or bank statement)","Incorporation certificate or partnership deed, if applicable"],
 steps=["We check eligibility and the right registration type","You upload documents in your client portal","We file the application and complete Aadhaar authentication","We reply to any officer query","GSTIN and certificate delivered on WhatsApp and in your portal"],
 time="Usually 3–7 working days, depending on the GST officer",
 faqs=[("Is GST registration mandatory for a small business?","Only if your turnover crosses the threshold, you sell inter-state goods, or you sell through e-commerce operators. Many small businesses still register voluntarily to claim input tax credit."),
       ("Can I register GST at my home address?","Yes. A residential address can be the principal place of business if you have an address proof and, if rented, the owner's NOC."),
       ("What happens after I get GSTIN?","You must file GST returns every month or quarter, even if there are no sales. We can file them for you under a monthly plan.")])

S["gst-return-filing"] = dict(n="GST Return Filing", c="gst", crm="GST",
 d="Every GST-registered business must file returns such as GSTR-1 and GSTR-3B on time to avoid late fees and interest. Our team reconciles your sales and purchases, matches input tax credit with GSTR-2B and files your returns every month or quarter.",
 who=["Every regular GST-registered business","Businesses under the QRMP (quarterly) scheme","E-commerce sellers and exporters claiming refunds"],
 docs=["Sales invoices or sales register","Purchase invoices / expense bills","GST portal login (or OTP access)","Bank statement for the period, if needed"],
 steps=["You share sales and purchase data (Excel, Tally or photos)","We reconcile input tax credit with GSTR-2B","You approve the tax payable","We file GSTR-1 and GSTR-3B and send you the acknowledgement"],
 time="Filed before the due date every month or quarter",
 faqs=[("What if I miss the due date?","Late fees and 18% interest on unpaid tax apply. We file pending returns and calculate the exact late fee for you."),
       ("Do I need to file if there were no sales?","Yes. A nil return must still be filed; see our GST Nil Return service."),
       ("Can you file returns for past months?","Yes, we can file pending returns for previous periods and help you get back into compliance.")])

S["online-gst-nil-return-filing"] = dict(n="GST Nil Return Filing", c="gst", crm="GST",
 d="If your business had no sales, no purchases and no tax liability in a period, you still need to file a nil GST return. Missing it leads to late fees and can block your GSTIN. We file nil GSTR-1 and GSTR-3B on time so your registration stays active.",
 who=["Newly registered businesses with no activity yet","Seasonal businesses in off months","Businesses that have paused operations but keep GSTIN active"],
 docs=["GSTIN and portal access (or OTP)","Confirmation that there were no transactions in the period"],
 steps=["You confirm there were no transactions","We file nil GSTR-1 and GSTR-3B","Acknowledgement shared on WhatsApp"],
 time="Same day, before the due date",
 faqs=[("Is there a late fee for nil returns?","Yes, a reduced late fee applies per day of delay, so it is best to file on time."),
       ("Can nil returns be filed by SMS?","Yes, the GST portal allows nil filing by SMS for eligible taxpayers. We handle it for you either way."),
       ("When should I cancel GST instead?","If the business has stopped permanently, cancelling GSTIN avoids ongoing filings. See GST Cancellation.")])

S["gstr-9-annual-filing"] = dict(n="GSTR-9 Annual Return Filing", c="gst", crm="GST",
 d="GSTR-9 is the yearly GST return that summarises everything you reported in your monthly or quarterly returns. We reconcile your books with GSTR-1, GSTR-3B and GSTR-2B, fix differences and file the annual return (and GSTR-9C where required).",
 who=["Regular GST taxpayers above the annual-return exemption limit","Businesses that need GSTR-9C reconciliation"],
 docs=["Sales and purchase registers for the year","Filed GSTR-1 and GSTR-3B summaries","Books of accounts / trial balance","Details of any ITC reversals"],
 steps=["Year-end data collected","Reconciliation of books vs returns","Differences explained and corrected where possible","GSTR-9 (and 9C if applicable) filed"],
 time="5–10 working days after receiving data; due by 31 December for the previous year",
 faqs=[("Is GSTR-9 mandatory for everyone?","Small taxpayers below the notified turnover limit are exempt for some years. We check whether it applies to you."),
       ("Can GSTR-9 be revised?","No. Once filed it cannot be revised, which is why careful reconciliation matters."),
       ("What is GSTR-9C?","A reconciliation statement between audited accounts and GSTR-9, required above a higher turnover limit.")])

S["gst-lut-filing"] = dict(n="GST LUT Filing", c="gst", crm="GST",
 d="A Letter of Undertaking (LUT) lets exporters supply goods or services without paying IGST upfront, so cash is not blocked waiting for refunds. LUT must be filed every financial year. We prepare and file Form GST RFD-11 online for you.",
 who=["Exporters of goods and services","Suppliers to SEZ units","Freelancers and agencies billing foreign clients"],
 docs=["GSTIN and portal access","Details of two witnesses (name, address, occupation)","Authorised signatory details"],
 steps=["We prepare RFD-11","You approve via OTP","LUT filed and acknowledgement shared"],
 time="1–2 working days",
 faqs=[("How long is an LUT valid?","For one financial year. A new LUT must be filed each year."),
       ("Do service exporters need LUT?","Yes, if they want to export without paying IGST."),
       ("What if I exported without LUT?","You would have to pay IGST and claim a refund. File LUT before exporting to avoid this.")])

S["gst-eway-bill-generation"] = dict(n="GST E-Way Bill Generation", c="gst", crm="GST",
 d="An e-way bill is required to move goods worth more than ₹50,000 in a vehicle (state limits for intra-state movement can differ). We register you on the e-way bill portal, generate bills for your consignments and train your team to do it themselves.",
 who=["Manufacturers, traders and distributors moving goods","Transporters","E-commerce sellers shipping high-value consignments"],
 docs=["GSTIN","Invoice / bill of supply / delivery challan","Transporter ID or vehicle number"],
 steps=["E-way bill portal registration","Invoice and transport details entered","E-way bill generated and shared","Extension or cancellation when needed"],
 time="Same day",
 faqs=[("How long is an e-way bill valid?","It depends on the distance: generally one day per 200 km for normal cargo."),
       ("What is the penalty for moving goods without an e-way bill?","Goods and vehicles can be detained and penalties levied, so always generate it before dispatch."),
       ("Can an e-way bill be cancelled?","Yes, within 24 hours of generation if the goods have not moved.")])

S["gst-modification"] = dict(n="GST Registration Amendment", c="gst", crm="GST",
 d="Changed your business address, added a partner, opened a new branch or need to update contact details? GST rules require you to amend your registration within 15 days of the change. We file the right amendment (core or non-core) and follow up with the officer.",
 who=["Businesses that changed address, name, partners or directors","Businesses adding a branch or warehouse","Anyone updating mobile, email or bank details on GST"],
 docs=["GSTIN and portal access","Proof of the change (new address proof, partner KYC, board resolution etc.)","Authorised signatory details"],
 steps=["We identify core vs non-core amendment","Documents uploaded in your portal","Amendment filed","Approval tracked and shared"],
 time="Non-core changes: instant; core changes: usually 7–15 days for officer approval",
 faqs=[("Can I change my business name on GST?","Yes, if the legal or trade name changed. It is a core amendment and needs officer approval."),
       ("Can PAN be changed in GST?","No. A change of PAN needs a new GST registration."),
       ("Is there a fee for GST amendment?","There is no government fee; only our professional fee applies.")])

S["gst-cancellation"] = dict(n="GST Cancellation", c="gst", crm="GST",
 d="If your business has closed, been transferred, or no longer needs GST, you can surrender your GSTIN. Until it is cancelled you must keep filing returns. We file the cancellation application, the final return (GSTR-10) and help clear pending returns.",
 who=["Businesses that have closed or stopped trading","Businesses below the threshold that registered voluntarily","Firms converting to a company or merging"],
 docs=["GSTIN and portal access","Reason and date of cancellation","Details of closing stock and tax on it"],
 steps=["Pending returns checked and filed","Cancellation application (REG-16) filed","Officer order tracked","Final return GSTR-10 filed"],
 time="Usually 2–4 weeks for the order",
 faqs=[("Do I have to file returns after applying for cancellation?","Yes, until the cancellation order is issued, and then the final return GSTR-10."),
       ("Can a cancelled GSTIN be restored?","If cancelled by the officer, you can apply for revocation within the allowed time."),
       ("Is tax payable on closing stock?","Yes, input tax credit on closing stock generally has to be paid back.")])

S["gst-online"] = dict(n="GST Compliance Services", c="gst", crm="GST",
 d="One team for everything GST: registration, monthly returns, annual returns, notices and amendments. Choose a monthly plan and never miss a due date again — we send reminders, collect data on WhatsApp and file on time.",
 who=["Small and medium businesses that want GST handled end-to-end","E-commerce sellers","Businesses that received GST notices"],
 docs=["GSTIN or registration documents","Monthly sales and purchase data","Portal access"],
 steps=["We review your current GST status","Monthly calendar and reminders set up","Returns filed every period","Notices and annual return handled"],
 time="Ongoing monthly plan",
 faqs=[("Do you handle GST notices?","Yes. We draft and file replies to common notices such as mismatches and late filing."),
       ("Can I switch from my current accountant?","Yes. We take over from the next period and help fix any past gaps."),
       ("Is there a yearly plan?","Yes. Ask for a quote for monthly or yearly GST compliance.")])

S["trademark-registration"] = dict(n="Trademark Registration", c="tm", crm="Trademark",
 d="A registered trademark protects your brand name, logo or tagline across India and lets you take action against copycats. We run a search, pick the right class, file your application with the Trademark Registry and track it until registration. You can use the ™ symbol from the day we file.",
 who=["Startups and businesses launching a brand","Online sellers protecting their product names","Professionals and creators building a personal brand"],
 docs=["Brand name and/or logo (JPG)","Applicant name, address and nationality","Udyam/MSME or startup certificate for the lower government fee (optional)","Signed authorisation (Form TM-48) — we prepare it","Proof of earlier use, if claiming a user date"],
 steps=["Free trademark search and class selection","Application drafted and TM-48 signed","Filed online — ™ can be used immediately","Examination report tracked; objections replied if any","Publication in the journal and registration certificate"],
 time="Filing in 1–2 days; registration usually takes 8–18 months if there is no objection or opposition",
 faqs=[("How long is a trademark valid?","10 years from the application date, renewable every 10 years indefinitely."),
       ("Can I use ® after filing?","No. ® can be used only after registration. Use ™ while the application is pending."),
       ("What is a trademark class?","Goods and services are divided into 45 classes. You need protection in each class where you do business.")])

S["trademark-objection-reply"] = dict(n="Trademark Objection Reply", c="tm", crm="Trademark",
 d="If the examiner raises an objection in the examination report, a well-argued reply must be filed within the deadline or the application can be abandoned. Our team studies the objection (similarity, descriptiveness, etc.), drafts a legal reply with evidence and files it on time.",
 who=["Applicants who received a trademark examination report","Brands whose application status shows 'Objected'"],
 docs=["Trademark application number","Examination report","Evidence of use (invoices, website, ads), if available"],
 steps=["Examination report reviewed","Reply drafted with legal grounds and case law","Evidence affidavit prepared if needed","Reply filed and hearing tracked"],
 time="Reply filed within 3–5 working days of receiving documents",
 faqs=[("What is the deadline to reply?","Generally 30 days from receiving the examination report. Missing it can lead to abandonment."),
       ("What happens after the reply?","The examiner may accept it or call a hearing. We represent you at the hearing too."),
       ("Can an objection be overcome?","Many are, especially with good arguments and evidence of use.")])

S["trademark-hearing-india"] = dict(n="Trademark Hearing", c="tm", crm="Trademark",
 d="When the Registrar is not satisfied with the written reply, a show-cause hearing is fixed. Our attorneys prepare written submissions and represent you at the online hearing to argue for acceptance of your mark.",
 who=["Applicants with a hearing notice from the Trademark Registry"],
 docs=["Hearing notice","Application and examination report details","Evidence of use and earlier reply"],
 steps=["Case file reviewed","Written submissions prepared","Online hearing attended","Outcome tracked and shared"],
 time="Depends on the hearing date given by the Registry",
 faqs=[("Do I need to attend?","No, our attorney attends on your behalf."),
       ("Can a hearing be adjourned?","Adjournment can be requested in limited cases."),
       ("What if the mark is refused?","An appeal or a fresh strategy can be considered.")])

S["trademark-opposition-india"] = dict(n="Trademark Opposition", c="tm", crm="Trademark",
 d="After publication in the Trademark Journal, anyone can oppose a mark within four months — and you can oppose marks similar to yours. We file oppositions, counter-statements and evidence to protect your brand.",
 who=["Brand owners who spot a similar mark in the journal","Applicants whose mark has been opposed"],
 docs=["Details of your mark and registration","Details of the opposed mark","Evidence of use and reputation"],
 steps=["Case assessment","Notice of opposition or counter-statement filed","Evidence stage handled","Hearing representation"],
 time="Opposition proceedings can take several months to years",
 faqs=[("What is the deadline to oppose?","Four months from the date of publication in the Trademark Journal."),
       ("What if I don't file a counter-statement?","The application is treated as abandoned."),
       ("Can opposition be settled?","Yes, many are settled by agreement between the parties.")])

S["trademark-renewal"] = dict(n="Trademark Renewal", c="tm", crm="Trademark",
 d="A trademark registration lasts 10 years. Renewing it on time keeps your exclusive rights alive. We file the renewal (Form TM-R) before expiry — or within the grace period with a surcharge — and update the Registry.",
 who=["Owners of trademarks expiring in the next 12 months","Owners whose mark recently expired (grace period)"],
 docs=["Registration certificate or number","Owner details and any changes","Signed authorisation (TM-48)"],
 steps=["Expiry checked","TM-R prepared","Renewal filed","Renewal reflected on the Registry"],
 time="Filing in 1–2 days",
 faqs=[("When can I renew?","Up to one year before expiry."),
       ("Is there a grace period?","Yes, renewal is allowed within six months after expiry with a surcharge; later restoration is possible in some cases."),
       ("Can I change the logo while renewing?","No. A changed logo needs a new application.")])

S["trademark-assignment"] = dict(n="Trademark Assignment", c="tm", crm="Trademark",
 d="Selling or transferring a brand? A trademark assignment transfers ownership from one person or company to another. We draft the assignment deed and record the change with the Trademark Registry.",
 who=["Businesses buying or selling a brand","Founders moving a brand into their new company"],
 docs=["Trademark registration details","Assignor and assignee KYC","Consideration and terms","Signed assignment deed (we draft it)"],
 steps=["Assignment deed drafted","Deed signed and stamped","Form TM-P filed","Registry records the new owner"],
 time="Deed in 2–3 days; Registry update can take a few months",
 faqs=[("Can a pending application be assigned?","Yes, applications can also be assigned."),
       ("Is stamp duty payable?","Yes, as per the state stamp laws on the deed."),
       ("Can only part of the goods be assigned?","Yes, partial assignment is possible.")])

S["series-trademark"] = dict(n="Series Trademark Registration", c="tm", crm="Trademark",
 d="A series trademark protects several similar versions of the same mark (for example different colours or small variations) in one application. We assess whether your marks qualify as a series and file them together.",
 who=["Brands using the same mark in different colours or variants","Product lines with a common brand name"],
 docs=["All versions of the mark","Applicant details","Signed TM-48"],
 steps=["Series check","Application drafted","Filed with the Registry","Tracked to registration"],
 time="Filing in 2–3 days",
 faqs=[("What is a series mark?","Marks that resemble each other in material particulars but differ in non-distinctive details."),
       ("Is it cheaper than separate filings?","Usually yes, but a fee applies for each mark in the series."),
       ("Can any marks be filed as a series?","Only if they meet the series test; we check before filing.")])

S["trademark-all"] = dict(n="Trademark Services", c="tm", crm="Trademark", hub=True,
 d="Protect your brand from search to registration and beyond: filing, objections, hearings, oppositions, renewals and transfers — handled by trademark experts with updates on WhatsApp.",
 who=[],docs=[],steps=[],time="",faqs=[])

S["online-copyright-registration"] = dict(n="Copyright Registration", c="tm", crm="",
 d="Copyright protects original creative work such as software, books, music, artwork, films and website content. Registration gives you strong proof of ownership in a dispute. We prepare and file your application with the Copyright Office and follow it up.",
 who=["Authors, artists and musicians","Software developers and app makers","Businesses protecting original designs, content and photos"],
 docs=["Copy of the work","Author and owner details","No-objection from the author if the owner is different","Signed power of attorney (we draft it)"],
 steps=["Work and category reviewed","Application filed","Diary number issued","Objection period and examination tracked","Registration certificate"],
 time="Filing in 2–3 days; registration commonly takes several months",
 faqs=[("Is registration mandatory?","No, copyright exists from creation, but registration is strong evidence of ownership."),
       ("How long does copyright last?","For literary and artistic works, generally the author's lifetime plus 60 years."),
       ("Can a logo get copyright?","Yes, as an artistic work — but also register it as a trademark for brand protection.")])

S["logo-design"] = dict(n="Logo Design", c="tm", crm="",
 d="A distinctive logo is the start of a strong brand — and a strong trademark. Our designers create original logo options for your business, ready to file for trademark registration.",
 who=["New businesses and startups","Businesses refreshing their brand"],
 docs=["Business name and industry","Colour and style preferences","Examples you like (optional)"],
 steps=["Brief collected","Initial concepts shared","Revisions","Final files (PNG, SVG, PDF) delivered"],
 time="5–7 working days",
 faqs=[("Will the logo be original?","Yes, designed from scratch for you."),
       ("Can you register it as a trademark?","Yes, we can file it right after design."),
       ("Which file formats do I get?","High-resolution PNG, vector SVG/PDF for print.")])
