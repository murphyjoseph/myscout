# Saved Jobs

Drop job postings you like into this directory. These serve as training examples for teaching the scoring engine what a good job looks like for you.

## How to use

Save jobs as markdown files with a simple frontmatter format:

```markdown
---
company: Acme Corp
title: Senior Frontend Engineer
url: https://example.com/jobs/12345
outcome: got_interview  # good_shot | got_interview | aspirational
---

Paste the full job description here...
```

## Outcome labels

- **good_shot** — jobs you'd be a strong match for
- **got_interview** — jobs where you actually got an interview (strongest signal)
- **aspirational** — dream roles you're working toward

## File naming

Name files however you want. Suggested: `company-title.md`

```
saved_jobs/
  acme-senior-frontend.md
  stripe-staff-engineer.md
  cloudflare-systems-engineer.md
```

## Privacy

This directory is gitignored. Your saved jobs stay on your machine and are never committed to the repo.

## Future use

These files can be used to:
- Generate embeddings that represent your ideal job profile
- Auto-tune the scoring weights in `config/profile.yml`
- Extract patterns (tech stacks, seniority levels, company types) to refine search targets
