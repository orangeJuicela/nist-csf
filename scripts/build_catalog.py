#!/usr/bin/env python3
"""Build data/nist-cswp-29.json from the NIST CSWP 29 Appendix A text extract.

English outcomes are parsed from the publication text. The only editorial change
is joining the PDF line-break hyphenation in RC.RP-06 ("incident-" / "related")
into "incident-related". Traditional Chinese fields are unofficial explanations
for this guide, not a NIST translation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPENDIX = Path("/tmp/csf/appendix.txt")
OUT = ROOT / "data" / "nist-cswp-29.json"

NAV = {
    "GV": "治理",
    "ID": "識別",
    "PR": "保護",
    "DE": "偵測",
    "RS": "應變",
    "RC": "復原",
    "GV.OC": "組織情境",
    "GV.RM": "風險管理策略",
    "GV.RR": "角色、責任與權限",
    "GV.PO": "政策",
    "GV.OV": "監督",
    "GV.SC": "資安供應鏈風險管理",
    "ID.AM": "資產管理",
    "ID.RA": "風險評估",
    "ID.IM": "改善",
    "PR.AA": "身分、鑑別與存取控制",
    "PR.AT": "意識與訓練",
    "PR.DS": "資料安全",
    "PR.PS": "平台安全",
    "PR.IR": "技術基礎設施韌性",
    "DE.CM": "持續監控",
    "DE.AE": "不利事件分析",
    "RS.MA": "資安事件管理",
    "RS.AN": "資安事件分析",
    "RS.CO": "通報與溝通",
    "RS.MI": "遏制與清除",
    "RC.RP": "復原計畫執行",
    "RC.CO": "復原溝通",
}

# Unofficial plain-language explanations (zh-Hant-TW). Keyed by official ID.
ZH = {
    "GV": "治理是先把資安風險要怎麼管、組織期待什麼、政策是什麼定下來，讓相關的人知道，並持續看著這些決定有沒有被執行。CSF 2.0 把治理放在其他功能的中央，因為角色、風險胃納、政策與監督會影響識別、保護、偵測、應變與復原的每一項決定。",
    "ID": "識別是把組織目前的資安風險看清楚：有哪些資產、風險從哪裡來、哪些做法該改。看清楚之後，後面的保護與資源才放得準。",
    "PR": "保護是實際使用防護措施來管理資安風險，範圍涵蓋身分與存取控制、人員的意識與訓練、資料、平台，以及技術基礎設施的韌性。重點是這些防護有被用上。",
    "DE": "偵測是找出可能的資安攻擊與入侵，並加以分析。目標是發現不利事件，並在符合已訂條件時把它認定為資安事件。",
    "RS": "應變是在偵測到資安事件之後採取行動，包含啟動計畫、調查、通報，以及遏制與清除。重點是事件發生當下怎麼處置。",
    "RC": "復原是把受資安事件影響的資產與營運恢復到可用狀態，並讓該知道的人了解進度。復原要依條件宣告結束，也要完成與事件相關的文件。",
    "GV.OC": "做資安決策之前，先掌握組織的任務、利害關係人的期待、彼此的依賴，以及法令、監管與契約上的要求。這些是決策時的情境，不是附錄。",
    "GV.RM": "把優先順序、限制條件、風險胃納與風險容忍度，以及背後的假設定下來、講清楚，並用來支持日常的風險決定。",
    "GV.RR": "把資安的角色、責任與權限定下來並讓人知道，這樣才能究責、看表現，也才能持續改善。",
    "GV.PO": "訂出組織的資安政策，傳達給該知道的人，並且確實執行。",
    "GV.OV": "用全組織資安風險管理做下來的結果與表現，回頭通知、改善並調整風險管理策略。",
    "GV.SC": "由組織的利害關係人辨識、建立、管理、監控並改進資安供應鏈風險管理的做法。",
    "ID.AM": "把讓組織達成業務目的的資產找出來並管理。資產包含資料、硬體、軟體、系統、設施、服務與人員，管理方式要對齊它們對組織目標與風險策略的相對重要性。",
    "ID.RA": "組織要理解資安風險對組織本身、資產與個人的意義，而不是只收集一份弱點清單。",
    "ID.IM": "在所有 CSF 功能裡，找出資安風險管理的流程、程序與活動可以改進的地方。",
    "PR.AA": "實體與邏輯資產只讓經過授權的使用者、服務與硬體存取，並依未授權存取的風險來管理這件事。",
    "PR.AT": "讓組織人員得到資安意識與訓練，使他們做得到與資安有關的工作。",
    "PR.DS": "依組織的風險策略管理資料，以保護資訊的機密性、完整性與可用性。",
    "PR.PS": "依組織的風險策略管理實體與虛擬平台上的硬體、軟體（包含韌體、作業系統、應用程式）與服務，以保護它們的機密性、完整性與可用性。",
    "PR.IR": "依組織的風險策略管理安全架構，以保護資產的機密性、完整性與可用性，以及組織的韌性。",
    "DE.CM": "監控資產，以便找出異常、入侵跡象，以及其他可能的不利事件。",
    "DE.AE": "分析異常、入侵跡象與其他可能的不利事件，用來描述這些事件，並判斷是否為資安事件。",
    "RS.MA": "管理對已偵測到的資安事件所做的應變。",
    "RS.AN": "進行調查，讓應變做得到，並支援數位鑑識與復原。",
    "RS.CO": "依法律、監管要求或政策，與內部及外部利害關係人協調應變活動。",
    "RS.MI": "採取行動，避免事件擴大並減輕其影響。",
    "RC.RP": "執行復原活動，讓受資安事件影響的系統與服務恢復到可營運的狀態。",
    "RC.CO": "與內部及外部相關單位協調復原活動。",
    "GV.OC-01": "組織的任務要被理解，並用來引導資安風險管理。資安在管什麼，要跟組織為什麼存在對得起來。",
    "GV.OC-02": "內部與外部利害關係人是誰，以及他們對資安風險管理的需求與期待，都要弄清楚並納入考量。",
    "GV.OC-03": "與資安有關的法令、監管與契約要求，包含隱私與公民自由方面的義務，都要被理解並加以管理。",
    "GV.OC-04": "外部利害關係人依賴或期待組織提供的關鍵目標、能力與服務，要被理解，並向他們說明。",
    "GV.OC-05": "組織自己所依賴的成果、能力與服務，要被理解，並向相關的人說明。",
    "GV.RM-01": "風險管理目標要訂出來，並取得組織利害關係人的同意。",
    "GV.RM-02": "風險胃納與風險容忍度要寫成聲明、傳達出去，並持續維護。",
    "GV.RM-03": "資安風險管理的活動與成果要納入企業風險管理流程。",
    "GV.RM-04": "要建立並傳達策略方向，說明哪些風險回應選項是適當的。",
    "GV.RM-05": "組織裡要建立資安風險的溝通管道，包含來自供應商與其他第三方的風險。",
    "GV.RM-06": "要建立並傳達一套一致的方法，用來計算、記錄、分類與排定資安風險的優先順序。",
    "GV.RM-07": "策略機會（也就是正向風險）要被描述，並納入組織的資安風險討論。",
    "GV.RR-01": "組織領導層對資安風險負責並可被究責，同時培養有風險意識、合乎倫理且持續改善的文化。",
    "GV.RR-02": "與資安風險管理有關的角色、責任與權限要訂定、傳達、讓人理解，並且確實執行。",
    "GV.RR-03": "配置的資源要與資安風險策略、角色、責任及政策相稱。",
    "GV.RR-04": "資安要被納入人力資源的做法。",
    "GV.PO-01": "管理資安風險的政策要依組織情境、資安策略與優先順序來訂定，並加以傳達與執行。",
    "GV.PO-02": "資安風險政策要檢討並更新，以反映要求、威脅、技術與組織任務的變化，並重新傳達與執行。",
    "GV.OV-01": "檢視資安風險管理策略的成果，用來告知並調整策略與方向。",
    "GV.OV-02": "檢討並調整資安風險管理策略，確認它涵蓋組織的要求與風險。",
    "GV.OV-03": "評估並檢視組織資安風險管理的表現，看哪些地方需要調整。",
    "GV.SC-01": "資安供應鏈風險管理的計畫、策略、目標、政策與流程要建立，並取得組織利害關係人同意。",
    "GV.SC-02": "供應商、客戶與夥伴在資安上的角色與責任要訂定、傳達，並在組織內外協調。",
    "GV.SC-03": "資安供應鏈風險管理要整合進資安與企業風險管理、風險評估與改善流程。",
    "GV.SC-04": "供應商要被掌握，並依關鍵程度排定優先順序。",
    "GV.SC-05": "處理供應鏈資安風險的要求要訂出、排定優先順序，並寫進與供應商及其他相關第三方的契約或其他協議。",
    "GV.SC-06": "在正式建立供應商或其他第三方關係之前，先做規劃與盡職調查，以降低風險。",
    "GV.SC-07": "供應商、其產品與服務，以及其他第三方帶來的風險，要在關係存續期間被理解、記錄、排定優先順序、評估、回應並持續監控。",
    "GV.SC-08": "相關供應商與其他第三方要被納入資安事件的規劃、應變與復原活動。",
    "GV.SC-09": "供應鏈安全做法要整合進資安與企業風險管理計畫，並在技術產品與服務的生命週期中監控其表現。",
    "GV.SC-10": "資安供應鏈風險管理計畫要包含夥伴關係或服務協議結束之後仍須進行的活動。",
    "ID.AM-01": "組織所管理的硬體要有清冊，並持續維護。",
    "ID.AM-02": "組織所管理的軟體、服務與系統要有清冊，並持續維護。",
    "ID.AM-03": "要維護組織所授權的網路通訊，以及內部與外部網路資料流向的表示。",
    "ID.AM-04": "供應商所提供的服務要有清冊，並持續維護。",
    "ID.AM-05": "資產要依分類、關鍵程度、資源，以及對任務的影響來排定優先順序。",
    "ID.AM-07": "指定資料類型的資料清冊，以及對應的詮釋資料，要持續維護。",
    "ID.AM-08": "系統、硬體、軟體、服務與資料要在整個生命週期中被管理。",
    "ID.RA-01": "資產上的弱點要被找出、確認並記錄。",
    "ID.RA-02": "要從情資分享管道與其他來源接收網路威脅情資。",
    "ID.RA-03": "對組織的內部與外部威脅要被辨識並記錄。",
    "ID.RA-04": "威脅利用弱點時可能造成的影響與可能性，要被辨識並記錄。",
    "ID.RA-05": "用威脅、弱點、可能性與影響來理解固有風險，並據此排定風險回應的優先順序。",
    "ID.RA-06": "風險回應要被選定、排定優先順序、規劃、追蹤並傳達。",
    "ID.RA-07": "變更與例外要被管理、評估其風險影響、記錄並追蹤。",
    "ID.RA-08": "要建立接收、分析與回應弱點揭露的流程。",
    "ID.RA-09": "硬體與軟體在取得與使用之前，要評估其真實性與完整性。",
    "ID.RA-10": "關鍵供應商在採購之前要先被評估。",
    "ID.IM-01": "從評鑑中找出可改善之處。",
    "ID.IM-02": "從安全測試與演練找出可改善之處，包含與供應商及相關第三方一起進行的測試與演練。",
    "ID.IM-03": "從日常流程、程序與活動的執行中找出可改善之處。",
    "ID.IM-04": "資安事件應變計畫，以及其他會影響營運的資安計畫，要建立、傳達、維護並改進。",
    "PR.AA-01": "經授權的使用者、服務與硬體，其身分與憑證要由組織管理。",
    "PR.AA-02": "依互動的情境查核身分，並把身分與憑證綁在一起。",
    "PR.AA-03": "使用者、服務與硬體都要經過鑑別。",
    "PR.AA-04": "身分主張要被保護、傳遞並驗證。",
    "PR.AA-05": "存取權限、被賦予的資格與授權要寫進政策，加以管理、執行與檢視，並納入最小權限與職務區隔。",
    "PR.AA-06": "對資產的實體存取要依風險加以管理、監控與執行。",
    "PR.AT-01": "提供人員意識與訓練，使他們具備知識與技能，在做一般工作時把資安風險納入考量。",
    "PR.AT-02": "對擔任專門角色的人提供意識與訓練，使他們具備知識與技能，在做相關工作時把資安風險納入考量。",
    "PR.DS-01": "保護靜態資料的機密性、完整性與可用性。",
    "PR.DS-02": "保護傳輸中資料的機密性、完整性與可用性。",
    "PR.DS-10": "保護使用中資料的機密性、完整性與可用性。",
    "PR.DS-11": "建立資料備份，並加以保護、維護與測試。",
    "PR.PS-01": "建立並落實組態管理做法。",
    "PR.PS-02": "依風險維護、更換與移除軟體。",
    "PR.PS-03": "依風險維護、更換與移除硬體。",
    "PR.PS-04": "產生日誌紀錄，並提供給持續監控使用。",
    "PR.PS-05": "防止未經授權的軟體被安裝與執行。",
    "PR.PS-06": "納入安全的軟體開發做法，並在整個軟體開發生命週期監控這些做法的表現。",
    "PR.IR-01": "保護網路與環境，使其免於未經授權的邏輯存取與使用。",
    "PR.IR-02": "保護組織的技術資產，使其免於環境威脅。",
    "PR.IR-03": "落實機制，使韌性要求在平常與不利狀況下都能達成。",
    "PR.IR-04": "維持足夠的資源容量，以確保可用性。",
    "DE.CM-01": "監控網路與網路服務，以發現可能的不利事件。",
    "DE.CM-02": "監控實體環境，以發現可能的不利事件。",
    "DE.CM-03": "監控人員活動與技術使用情形，以發現可能的不利事件。",
    "DE.CM-06": "監控外部服務提供者的活動與服務，以發現可能的不利事件。",
    "DE.CM-09": "監控運算硬體與軟體、執行環境及其資料，以發現可能的不利事件。",
    "DE.AE-02": "分析可能的不利事件，以便更了解與之相關的活動。",
    "DE.AE-03": "把來自多個來源的資訊關聯起來。",
    "DE.AE-04": "掌握不利事件的預估影響與範圍。",
    "DE.AE-06": "把不利事件的資訊提供給經授權的人員與工具。",
    "DE.AE-07": "把網路威脅情資與其他情境資訊納入分析。",
    "DE.AE-08": "當不利事件符合已定義的資安事件條件時，宣告為資安事件。",
    "RS.MA-01": "資安事件一旦宣告，就與相關第三方協調，執行資安事件應變計畫。",
    "RS.MA-02": "資安事件通報要先分級檢傷，並確認是否成立。",
    "RS.MA-03": "資安事件要分類並排定優先順序。",
    "RS.MA-04": "必要時把資安事件向上呈報或提升處理層級。",
    "RS.MA-05": "套用已訂的條件，決定何時啟動資安事件復原。",
    "RS.AN-03": "分析資安事件中發生了什麼，以及事件的根本原因。",
    "RS.AN-06": "調查過程中採取的行動要留下紀錄，並保存這些紀錄的完整性，以及它們從何而來。",
    "RS.AN-07": "蒐集資安事件的資料與詮釋資料，並保存其完整性，以及它們從何而來。",
    "RS.AN-08": "估計資安事件的規模，並加以確認。",
    "RS.CO-02": "將資安事件通知內部與外部利害關係人。",
    "RS.CO-03": "與指定的內部及外部利害關係人分享資訊。",
    "RS.MI-01": "遏制資安事件，使它不再擴大。",
    "RS.MI-02": "清除資安事件，把造成事件的因素從環境中移除。",
    "RC.RP-01": "一旦從應變流程啟動復原，就執行資安事件應變計畫中的復原部分。",
    "RC.RP-02": "選擇復原行動、界定範圍、排定優先順序，並加以執行。",
    "RC.RP-03": "在使用備份與其他復原用資產進行還原之前，先驗證它們的完整性。",
    "RC.RP-04": "把關鍵任務功能與資安風險管理納入考量，以建立事件後的營運常態。",
    "RC.RP-05": "驗證已還原資產的完整性，恢復系統與服務，並確認已回到正常運作狀態。",
    "RC.RP-06": "依條件宣告資安事件復原結束，並完成與該資安事件相關的文件。",
    "RC.CO-03": "向指定的內部與外部利害關係人說明復原活動，以及營運能力恢復的進度。",
    "RC.CO-04": "以經過核准的方式與訊息，對外分享資安事件復原的公開更新。",
}


def parse_appendix(text: str) -> list[dict]:
    start = text.find("GOVERN (GV):")
    end = text.find("Appendix B.")
    if start < 0 or end < 0:
        raise SystemExit("Appendix A span not found")
    body = text[start:end].replace("\f", "\n")
    body = re.sub(r"NIST CSWP 29.*?February 26, 2024\n", "", body, flags=re.S)
    body = re.sub(r"\n\s*\d+\s*\n", "\n", body)
    items: list[str] = []
    buf: str | None = None

    def flush() -> None:
        nonlocal buf
        if buf:
            items.append(re.sub(r"\s+", " ", buf).strip())
            buf = None

    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if (
            re.match(r"^(GOVERN|IDENTIFY|PROTECT|DETECT|RESPOND|RECOVER) \(", s)
            or s.startswith("•")
            or s.startswith("o ")
        ):
            flush()
            buf = s
        elif buf is not None:
            # Keep a trailing hyphen when the PDF broke a compound word.
            if buf.endswith("-") and s[:1].islower():
                buf += s
            else:
                buf += " " + s
    flush()

    parsed: list[dict] = []
    fn_re = re.compile(
        r"^(GOVERN|IDENTIFY|PROTECT|DETECT|RESPOND|RECOVER) \(([A-Z]{2})\): (.+)$"
    )
    cat_re = re.compile(r"^• (.+) \(([A-Z]{2}\.[A-Z]{2})\): (.+)$")
    sub_re = re.compile(r"^o ([A-Z]{2}\.[A-Z]{2}-\d{2}): (.+)$")
    current_fn = None
    current_cat = None
    for raw in items:
        mf = fn_re.match(raw)
        mc = cat_re.match(raw)
        ms = sub_re.match(raw)
        if mf:
            current_fn = mf.group(2)
            current_cat = None
            parsed.append(
                {
                    "id": current_fn,
                    "elementType": "function",
                    "parentId": None,
                    "name": mf.group(1).title() if mf.group(1) != "GOVERN" else "Govern",
                    "outcome": mf.group(3),
                }
            )
            # title() would make Identify etc. GOVERN special-cased; fix names explicitly below.
        elif mc:
            current_cat = mc.group(2)
            parsed.append(
                {
                    "id": current_cat,
                    "elementType": "category",
                    "parentId": current_fn,
                    "name": mc.group(1),
                    "outcome": mc.group(3),
                }
            )
        elif ms:
            parsed.append(
                {
                    "id": ms.group(1),
                    "elementType": "subcategory",
                    "parentId": current_cat,
                    "name": None,
                    "outcome": ms.group(2),
                }
            )
        else:
            raise SystemExit(f"Unparsed line: {raw}")
    names = {
        "GV": "Govern",
        "ID": "Identify",
        "PR": "Protect",
        "DE": "Detect",
        "RS": "Respond",
        "RC": "Recover",
    }
    for el in parsed:
        if el["elementType"] == "function":
            el["name"] = names[el["id"]]
    return parsed


def main() -> None:
    elements = parse_appendix(APPENDIX.read_text(encoding="utf-8"))
    missing = [el["id"] for el in elements if el["id"] not in ZH]
    extra = sorted(set(ZH) - {el["id"] for el in elements})
    if missing or extra:
        raise SystemExit(f"explanation mismatch missing={missing} extra={extra}")
    for i, el in enumerate(elements, start=1):
        el["sort"] = i
        el["navLabelZhTW"] = NAV.get(el["id"])
        el["explanationZhTW"] = ZH[el["id"]]
        if el["id"] == "RC.RP-06" and "incident-related" not in el["outcome"]:
            raise SystemExit(f"RC.RP-06 text not repaired: {el['outcome']}")
        if "incidentrelated" in el["outcome"] or "incident- related" in el["outcome"]:
            raise SystemExit("hyphenation artifact remains")

    counts = {k: sum(1 for el in elements if el["elementType"] == k) for k in ("function", "category", "subcategory")}
    if counts != {"function": 6, "category": 22, "subcategory": 106}:
        raise SystemExit(f"unexpected counts {counts}")

    catalog = {
        "schemaVersion": "1.0",
        "schema": (
            "Catalog of NIST publications expressed as trees of elements. "
            "Each document is independent. CSF 2.0 uses elementType function, category, and subcategory. "
            "Other publications (for example SP 800-53, SP 800-61, SP 800-63, SP 800-207) can be added "
            "as further documents, with their own elementType values, or as relationship files keyed by element id. "
            "Informative references are intentionally not embedded; add them beside this file when needed."
        ),
        "sourceChecked": "2026-11-13",
        "documents": [
            {
                "id": "NIST.CSWP.29",
                "shortTitle": "CSF 2.0",
                "title": "The NIST Cybersecurity Framework (CSF) 2.0",
                "publisher": "National Institute of Standards and Technology",
                "series": "NIST Cybersecurity White Paper",
                "publicationId": "NIST CSWP 29",
                "version": "2.0",
                "published": "2024-02-26",
                "doi": "https://doi.org/10.6028/NIST.CSWP.29",
                "urls": {
                    "pdf": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
                    "pdfZhHant": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.chi.pdf",
                    "home": "https://www.nist.gov/cyberframework",
                    "cprt": "https://csrc.nist.gov/projects/cprt",
                    "referenceTool": "https://csrc.nist.gov/Projects/cybersecurity-framework/Filters#/csf/filters",
                    "faq": "https://www.nist.gov/cyberframework/faqs",
                },
                "publicDomain": {
                    "statement": (
                        "NIST publications created by NIST employees are works of the United States Government. "
                        "They are not subject to copyright protection in the United States and are in the public domain there. "
                        "NIST notes that its publications may be subject to copyright protection outside the United States. "
                        "English outcome text on this site is reproduced from NIST CSWP 29."
                    ),
                    "credit": "Reprinted courtesy of the National Institute of Standards and Technology, U.S. Department of Commerce.",
                },
                "localization": {
                    "explanationLocale": "zh-Hant-TW",
                    "explanationStatus": "unofficial",
                    "explanationNote": (
                        "navLabelZhTW and explanationZhTW are unofficial plain-language Traditional Chinese "
                        "(Taiwan usage) written for this guide. They are not the NIST translation. "
                        "The official Traditional Chinese translation is the PDF linked in urls.pdfZhHant."
                    ),
                },
                "transcriptionNotes": [
                    "English name and outcome fields are taken from NIST CSWP 29 Appendix A.",
                    "RC.RP-06 is hyphenated across a line break in the PDF as 'incident-' / 'related'. This catalog joins that artifact as 'incident-related'. The same wording appears in the CSF 2.0 Reference Tool export.",
                    "Subcategory identifier gaps are intentional. Appendix A states that gaps indicate CSF 1.1 subcategories that were relocated in CSF 2.0. Withdrawn identifiers are not included as current elements.",
                ],
                "presentation": {
                    "source": "NIST Cybersecurity Framework FAQ, CSF Six Functions Graphic hex codes",
                    "sourceUrl": "https://www.nist.gov/cyberframework/faqs",
                    "colors": {
                        "GV": "#f9f49d",
                        "ID": "#4bb2e0",
                        "PR": "#9292ea",
                        "DE": "#fab746",
                        "RS": "#f97367",
                        "RC": "#7df49f",
                    },
                },
                "counts": counts,
                "elements": elements,
            }
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} counts={counts} elements={len(elements)}")


if __name__ == "__main__":
    main()
