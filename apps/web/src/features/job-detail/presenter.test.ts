import { describe, it, expect, vi } from "vitest";

// Mock isomorphic-dompurify — the presenter calls DOMPurify.sanitize()
vi.mock("isomorphic-dompurify", () => ({
  default: {
    sanitize: (html: string) => html, // pass-through for tests
  },
}));

import { presentJobDetail } from "./presenter";
import type { JobDetail, JobStatus } from "@/lib/api/types";

function makeDetail(overrides: Partial<JobDetail> = {}): JobDetail {
  return {
    id: 1,
    company: "Acme Corp",
    title: "Software Engineer",
    location: "Remote, US",
    remote_type: "remote",
    description_clean: "<p>Build things.</p>",
    apply_url_best: "https://example.com/apply",
    comp_min: 120000,
    comp_max: 180000,
    comp_currency: "USD",
    fingerprint: "abc123",
    first_seen: "2024-03-01T00:00:00Z",
    last_seen: "2024-03-06T00:00:00Z",
    is_active: true,
    score_total: 42.5,
    score_breakdown_json: {
      must_have_match: 1,
      title_match: 25,
      strong_plus_match: 5,
      penalty_avoid_tech: -10,
      total: 42.5,
    },
    status: "SAVED",
    notes: "Looks interesting",
    tech_tags: ["typescript", "react"],
    seniority: "senior",
    variants: [
      {
        id: 10,
        source: "lever",
        external_id: "ext-001",
        url: "https://jobs.lever.co/acme/ext-001",
        date_seen: "2024-03-06T00:00:00Z",
      },
    ],
    ...overrides,
  };
}

// ── renderAs states ─────────────────────────────────────────────

describe("presentJobDetail renderAs", () => {
  it("returns loading when isLoading", () => {
    const result = presentJobDetail(undefined, true, null);
    expect(result.renderAs).toBe("loading");
  });

  it("returns loading when no job and no error", () => {
    const result = presentJobDetail(undefined, false, null);
    expect(result.renderAs).toBe("loading");
  });

  it("returns error when error is truthy", () => {
    const result = presentJobDetail(undefined, false, new Error("fail"));
    expect(result.renderAs).toBe("error");
    expect(result.instructions.showError).toBe(true);
  });

  it("returns content with valid job", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.renderAs).toBe("content");
  });
});

// ── Display fields ──────────────────────────────────────────────

describe("presentJobDetail display fields", () => {
  it("maps basic fields", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.display.title).toBe("Software Engineer");
    expect(result.display.company).toBe("Acme Corp");
    expect(result.display.location).toBe("Remote, US");
  });

  it("formats score as string with one decimal", () => {
    const result = presentJobDetail(makeDetail({ score_total: 42.567 }), false, null);
    expect(result.display.score).toBe("42.6");
  });

  it("handles null score", () => {
    const result = presentJobDetail(makeDetail({ score_total: null }), false, null);
    expect(result.display.score).toBeNull();
    expect(result.instructions.hasScore).toBe(false);
  });

  it("maps badges", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.display.remoteBadge).toBe("remote");
    expect(result.display.seniorityBadge).toBe("senior");
  });

  it("formats salary", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.display.salary).toBe("$120k – $180k");
  });

  it("null salary when both null", () => {
    const result = presentJobDetail(
      makeDetail({ comp_min: null, comp_max: null }),
      false,
      null,
    );
    expect(result.display.salary).toBeNull();
  });
});

// ── Score rows ──────────────────────────────────────────────────

describe("presentJobDetail scoreRows", () => {
  it("creates rows from breakdown excluding total", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    const labels = result.display.scoreRows.map((r) => r.label);
    expect(labels).not.toContain("Total");
    expect(labels.length).toBe(4); // must_have, title, strong_plus, penalty_avoid
  });

  it("formats positive values with +", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    const titleRow = result.display.scoreRows.find((r) =>
      r.label.toLowerCase().includes("title"),
    );
    expect(titleRow?.value).toMatch(/^\+/);
    expect(titleRow?.isPositive).toBe(true);
  });

  it("formats negative values without +", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    const penaltyRow = result.display.scoreRows.find((r) =>
      r.label.toLowerCase().includes("avoid"),
    );
    expect(penaltyRow?.value).toBe("-10");
    expect(penaltyRow?.isNegative).toBe(true);
  });

  it("handles null breakdown", () => {
    const result = presentJobDetail(
      makeDetail({ score_breakdown_json: null }),
      false,
      null,
    );
    expect(result.display.scoreRows).toEqual([]);
  });
});

// ── Variants ────────────────────────────────────────────────────

describe("presentJobDetail variants", () => {
  it("maps variant fields", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.display.variants).toHaveLength(1);
    const v = result.display.variants[0];
    expect(v.source).toBe("lever");
    expect(v.url).toContain("lever.co");
  });

  it("truncates long URLs in display", () => {
    const longUrl = "https://example.com/" + "a".repeat(60);
    const result = presentJobDetail(
      makeDetail({
        variants: [
          { id: 1, source: "test", external_id: "x", url: longUrl, date_seen: "2024-01-01" },
        ],
      }),
      false,
      null,
    );
    expect(result.display.variants[0].urlDisplay.length).toBeLessThanOrEqual(53); // 50 + "..."
  });

  it("handles empty variants", () => {
    const result = presentJobDetail(makeDetail({ variants: [] }), false, null);
    expect(result.instructions.hasVariants).toBe(false);
  });
});

// ── Status ──────────────────────────────────────────────────────

describe("presentJobDetail status", () => {
  it("maps status", () => {
    const result = presentJobDetail(makeDetail({ status: "APPLIED" }), false, null);
    expect(result.display.status).toBe("APPLIED");
  });

  it("defaults to NEW when null", () => {
    const result = presentJobDetail(makeDetail({ status: null }), false, null);
    expect(result.display.status).toBe("NEW");
  });
});

// ── Instructions flags ──────────────────────────────────────────

describe("presentJobDetail instructions", () => {
  it("sets hasTechTags when tags present", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.instructions.hasTechTags).toBe(true);
  });

  it("sets hasTechTags false when empty", () => {
    const result = presentJobDetail(makeDetail({ tech_tags: [] }), false, null);
    expect(result.instructions.hasTechTags).toBe(false);
  });

  it("sets hasDescription when present", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.instructions.hasDescription).toBe(true);
  });

  it("sets hasDescription false when empty", () => {
    const result = presentJobDetail(
      makeDetail({ description_clean: "" }),
      false,
      null,
    );
    expect(result.instructions.hasDescription).toBe(false);
  });
});

// ── Description sanitization ────────────────────────────────────

describe("presentJobDetail descriptionHtml", () => {
  it("passes description through sanitizer", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    // Our mock passes through, so the HTML should be present
    expect(result.display.descriptionHtml).toContain("<p>");
  });

  it("handles null description", () => {
    const result = presentJobDetail(
      makeDetail({ description_clean: null }),
      false,
      null,
    );
    expect(result.display.descriptionHtml).toBe("");
  });
});

// ── Apply URL ───────────────────────────────────────────────────

describe("presentJobDetail applyUrl", () => {
  it("passes through apply URL", () => {
    const result = presentJobDetail(makeDetail(), false, null);
    expect(result.display.applyUrl).toBe("https://example.com/apply");
  });

  it("null apply URL when missing", () => {
    const result = presentJobDetail(
      makeDetail({ apply_url_best: null }),
      false,
      null,
    );
    expect(result.display.applyUrl).toBeNull();
  });
});
