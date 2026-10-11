# Local FAQ demo v0.1

Delivered at human request for a shareable demo, 2026-10-11. Source: app/config/routiq_faq.json v0.1 REVIEW. Output: demo/Routiq-Coach-Demo.html, one self-contained HTML file with 255 prepared answers. No application backend or source configuration changed.

The demo uses exact normalized matching; alternative wording offers related FAQ choices rather than generating an answer. It includes search, category filtering, suggested questions, clear chat and safe unmatched-question handling. It has no external assets, network calls, persisted chat, credentials or personal habit data. The FAQ review status and unresolved product rules remain unchanged.

## Executed verification

Browser checks via localhost: sample chip returned the curated small-habit answer; cricket query returned the prepared out-of-scope response; search for reading showed 11 of 255 entries; alternative reading wording offered three choices and selecting one returned the correct answer; New chat cleared prior messages. No browser error logs or horizontal overflow at 1280px. Screenshot: demo/demo-preview.png.

Direct file URL testing was blocked by the verification browser's protocol policy; no workaround attempted. The standalone file embeds its data and requires no fetch/server, but opening by double-click in the recipient's browser was not directly verified. These are demo UI checks, not live-provider, mobile, accessibility conformance or participant usability validation.
