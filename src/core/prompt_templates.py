# -*- coding: utf-8 -*-
"""
Prompt templates for 1917 Lai-goa-kho Tann-jin-siu OCR and Translation.
Optimized for Gemini 3.7 Flash / Gemini 2.5 Pro multi-modal vision models.
"""

PROMPT_ENGLISH_FRONT_MATTER = """
這是一頁 1917 年出版之醫學經典《內外科看護學》的前言、獻詞或版權頁（主要語言為英文 English）。
請為我進行極高精度的數位化轉錄與多語對照翻譯：

【工作任務】
1. 完整辨識（OCR）出影像中的英文內容，維持原始的段落、標題與格式結構。
2. 逐段提供「台文對照翻譯」（以台語漢字為主，並附帶括號內的白話字 Pe̍h-ōe-jī 羅馬字）以及「現代華語翻譯」。

【輸出格式規範】
請以 Markdown 格式輸出，每一段落依序呈現：

**[English Original]**
(英文段落內容)

> **[台文對照]** (台語漢字 + 白話字)
> (台文翻譯內容)
> 
> **[華語對照]**
> (現代標準中文翻譯內容)

---
請保持嚴謹與優雅，勿遺漏頁面中的任何題獻人名、年代或地名。
"""

PROMPT_POJ_MAIN = """
這是一頁 1917 年台灣長老教會出版之醫學典籍《內外科看護學》的台語白話字（Pe̍h-ōe-jī）內文影像。
請為我進行極高精度的 OCR 辨識與逐段「全漢字」對照：

【工作任務】
1. **高精度白話字 OCR**：
   - 精確還原所有白話字符號，包括右上方點號（如 `o͘`、`O͘`）、聲調符號（`á, à, â, ā, a̍, õ`）、鼻音標記（上標 `ⁿ` 或 `n`）、連字號（`-`）與雙連字符號（`--`）。
   - 保留原書的標題、小節數字、條列符號與分段結構。

2. **逐段全漢字對照**：
   - 在每一個白話字段落下方，提供對應的「台語全漢字」對照。
   - 漢字請採用符合文意與台語文法的正字（例如：`ê` -> 的/兮/ê, `chiū` -> 就, `tī-teh` -> 佇咧, `sio̍k tī` -> 屬佇, `khàn-hō͘` -> 看護, `chham-siông` -> 參詳）。
   - 對於專門醫學名詞，請保持原書意涵對譯。

【輸出格式規範】
請以 Markdown 格式輸出，格式範例：

### [小標題 / 節名（若該段有標題）]

(白話字段落內文...)

> **【全漢對照】**
> (全漢字段落內文...)

---
請直接輸出數位化內容，不需添加額外的問候語或解釋。
"""

PROMPT_GLOSSARY = """
這是一頁 1917 年《內外科看護學》書末的醫學辭彙表（GÚ-LŪI, Glossary）。
版面上通常包含「台語白話字 (POJ)」、「台語漢字 (Han-ji)」與「英文 (English)」之三語對照清單。

【工作任務】
1. 請以極高精度將圖像上的所有辭彙擷取為結構化的 Markdown 表格。
2. 準確保留白話字調號（包含 `o͘` 點號、`ó, ò, â, ā, a̍` 與上標鼻音 `ⁿ`）。
3. 勿隨意更動詞意或遺漏詞條。

【輸出格式規範】
請直接輸出 Markdown 表格：

| 白話字 (POJ) | 漢字 (Han-ji) | 英文 (English) | 說明 / 備註 |
| :--- | :--- | :--- | :--- |
| Chhùi-lāi-iām | 嘴內炎 | Stomatitis | |
| Huih-kńg | 血管 | Blood-vessel | |
| ... | ... | ... | ... |

請直接輸出表格內容，不需其他額外說明。
"""

PROMPT_INDEX = """
這是一頁 1917 年《內外科看護學》書末的索引（SEK-ÍN, Index）頁面。
通常以字母/部首或筆畫排列，包含詞條與原書頁碼。

【工作任務】
1. 請以高精度將所有索引條目擷取為乾淨清晰的 Markdown 表格或結構化清單。
2. 保留原書提及的對應頁碼數字。

【輸出格式規範】
| 索引詞條 (POJ) | 漢字 / 華語詞彙 | 原書對應頁碼 |
| :--- | :--- | :--- |
| ... | ... | ... |

請直接輸出數位化表格，不需多餘說明。
"""

def get_prompt_for_type(section_type: str) -> str:
    """Return the corresponding prompt template based on section type."""
    if section_type == "english_front_matter":
        return PROMPT_ENGLISH_FRONT_MATTER
    elif section_type == "glossary":
        return PROMPT_GLOSSARY
    elif section_type == "index":
        return PROMPT_INDEX
    else:
        return PROMPT_POJ_MAIN
