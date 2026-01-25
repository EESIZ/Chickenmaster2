# External Skill Generation Review Checklist

> Use this checklist before moving any externally-generated content to production.

## Pre-Scraping Verification

- [ ] **robots.txt**: Verified crawling is allowed for target URL
- [ ] **Terms of Service**: No prohibition on automated access
- [ ] **License**: Content license permits derivative works
- [ ] **Output Path**: Configured to `temp/skill_seekers/` only

## Security Scan

- [ ] **No injection patterns**: Searched for `ignore.*instruction`, `system.*prompt`
- [ ] **No script tags**: Searched for `<script>`, `javascript:`, `onclick`
- [ ] **No external calls**: No unexpected URLs or API endpoints
- [ ] **Valid JSON**: File parses correctly with `jq` or similar

### Security Scan Commands

```bash
# Pattern search
grep -iE "(ignore|forget|disregard).*(instruction|previous|above)" FILE.json
grep -iE "<script|javascript:|onclick|onerror" FILE.json
grep -iE "http[s]?://(?!docs\.example\.com)" FILE.json  # Unexpected URLs

# JSON validation
jq . FILE.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

## Content Review

- [ ] **Minimal verbatim copying**: Content is summarized, not copied
- [ ] **Links preferred**: Detailed information links to original source
- [ ] **Attribution present**: Source URL and license clearly stated
- [ ] **Version recorded**: Library version and scrape date documented

### Content Quality Check

| Aspect | Good ✅ | Bad ❌ |
| :--- | :--- | :--- |
| API Reference | "See [Trainer docs](url) for full options" | [500 lines of copied text] |
| Code Example | 5-10 line minimal example | Entire tutorial copied |
| Explanation | Summary with key points | Verbatim documentation |

## Schema Validation

- [ ] **Required fields present**: `metadata`, `sections` exist
- [ ] **Metadata complete**: `source_url`, `scraped_at`, `license`
- [ ] **Sections structured**: Each section has `title`, `url`, `summary`

### Expected Schema Structure

```json
{
  "metadata": {
    "source_url": "required",
    "scraped_at": "required",
    "license": "required",
    "library_version": "recommended"
  },
  "sections": [
    {
      "title": "required",
      "url": "required", 
      "summary": "required",
      "key_points": "optional",
      "code_examples": "optional"
    }
  ]
}
```

## Post-Processing

- [ ] **Extracted only needed content**: Removed unnecessary sections
- [ ] **Restructured for clarity**: Organized for agent consumption
- [ ] **Tested functionality**: Generated skill works as expected

## Final Gate

- [ ] **Ready for `.github/skills/`**: Content meets all criteria above
- [ ] **temp/ cleanup planned**: Will delete source files after extraction
- [ ] **No sensitive data**: No API keys, credentials, or PII included

---

## Reviewer Sign-off

| Item | Reviewer | Date |
| :--- | :--- | :--- |
| Security Scan | | |
| Content Review | | |
| Schema Check | | |

**Final Decision**: [ ] APPROVED / [ ] REJECTED

**Notes**:
