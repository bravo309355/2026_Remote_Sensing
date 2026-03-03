# AI Prompts Log

This file documents each user prompt in this session and a concise summary of the AI response.

## Prompt 1
- User prompt: `告訴我你目前連接的github repository`
- AI response summary: Checked local Git remotes and reported `origin` as `https://github.com/bravo309355/2026_Remote_Sensing.git`.

## Prompt 2
- User prompt: `ok 我在本機L:\2026_RS\data內新增了 新增了一個csv，你讀的到?`
- AI response summary: Located and read `L:\2026_RS\data\避難收容處所點位檔案v9.csv`; previewed the first rows successfully.

## Prompt 3
- User prompt: `針對這個檔案，請你1.瀏覽資料檢查哪裡有錯 2.根據錯誤進行修復 3.Write an audit report documenting every issue and correction`
- AI response summary:
  - Audited all 5,973 records.
  - Found and fixed 383 issues total:
    - `Phone normalization`: 348
    - `Leading/trailing whitespace`: 24
    - `Invalid/unrecoverable phone content`: 8
    - `Longitude out of Taiwan range (0)`: 3
  - Rewrote cleaned CSV and generated a full line-by-line audit report.
  - Created a pre-fix backup CSV for traceability.

## Prompt 4
- User prompt: `最後請你做這三個檔案，在output裡面創一個資料夾"exercise1"，把檔案放進去 ...`
- AI response summary: Created `output/exercise1` and prepared all three requested deliverables: `audit_report.md`, `ai_prompts.md`, `reflection.md`.
