import { describe, it, expect } from "vitest";
import { presentJobsList } from "./presenter";
import type { JobWithScore } from "@/lib/types";

function makeJob(overrides: Partial<JobWithScore> = {}): JobWithScore {
  return {
    id: 1,
    company: "Acme Corp",
    title: "Software Engineer",
    location: "Remote, US",
    remote_type: "remote",
    description_clean: "<p>Build great software with TypeScript and React.</p>",
    apply_url_best: "https://example.com/apply",
    comp_min: 120000,
    comp_max: 180000,
    comp_currency: "USD",
    fingerprint: "abc123",
    first_seen: "2024-03-01T00:00:00Z",
    last_seen: "2024-03-06T00:00:00Z",
    is_active: true,
    score_total: 45.5,
    score_breakdown_json: {
      must_have_match: 1,
      title_match: 25,
      strong_plus_match: 5,
      penalty_avoid_tech: -10,
      recency_bonus: 8,
      total: 45.5,
    },
    status: "NEW",
    notes: null,
    tech_tags: ["typescript", "react", "node", "python", "kubernetes"],
    seniority: "senior",
    ...overrides,
  };
}

// ── renderAs states ─────────────────────────────────────────────

describe("presentJobsList renderAs", () => {
  it("returns loading when isLoading is true", () => {
    const result = presentJobsList(undefined, true, null);
    expect(result.renderAs).toBe("loading");
    expect(result.display.cards).toEqual([]);
  });

  it("returns error when error is truthy", () => {
    const result = presentJobsList(undefined, false, new Error("fail"));
    expect(result.renderAs).toBe("error");
    expect(result.instructions.showError).toBe(true);
  });

  it("returns error when jobs is undefined", () => {
    const result = presentJobsList(undefined, false, null);
    expect(result.renderAs).toBe("error");
  });

  it("returns empty when jobs array is empty", () => {
    const result = presentJobsList([], false, null);
    expect(result.renderAs).toBe("empty");
    expect(result.instructions.showEmptyState).toBe(true);
    expect(result.display.jobCount).toBe("0 jobs");
  });

  it("returns content when jobs exist", () => {
    const result = presentJobsList([makeJob()], false, null);
    expect(result.renderAs).toBe("content");
    expect(result.display.cards).toHaveLength(1);
  });
});

// ── Job count formatting ────────────────────────────────────────

describe("presentJobsList jobCount", () => {
  it("says '1 job' for single result", () => {
    const result = presentJobsList([makeJob()], false, null);
    expect(result.display.jobCount).toBe("1 job");
  });

  it("says '3 jobs' for multiple results", () => {
    const jobs = [makeJob({ id: 1 }), makeJob({ id: 2 }), makeJob({ id: 3 })];
    const result = presentJobsList(jobs, false, null);
    expect(result.display.jobCount).toBe("3 jobs");
  });
});

// ── Card field mapping ──────────────────────────────────────────

describe("presentJobsList card fields", () => {
  it("maps basic fields", () => {
    const result = presentJobsList([makeJob()], false, null);
    const card = result.display.cards[0];

    expect(card.title).toBe("Software Engineer");
    expect(card.company).toBe("Acme Corp");
    expect(card.companyInitial).toBe("A");
    expect(card.location).toBe("Remote, US");
  });

  it("maps badges", () => {
    const result = presentJobsList([makeJob()], false, null);
    const card = result.display.cards[0];

    expect(card.remoteBadge).toBe("remote");
    expect(card.seniorityBadge).toBe("senior");
  });

  it("formats score as string with one decimal", () => {
    const result = presentJobsList([makeJob({ score_total: 42.567 })], false, null);
    expect(result.display.cards[0].score).toBe("42.6");
  });

  it("handles null score", () => {
    const result = presentJobsList([makeJob({ score_total: null })], false, null);
    const card = result.display.cards[0];
    expect(card.score).toBeNull();
    expect(card.scored).toBe(false);
    expect(card.scoreColor).toBe("gray");
  });
});

// ── Score color mapping ─────────────────────────────────────────

describe("presentJobsList scoreColor", () => {
  it("green for score >= 30", () => {
    const result = presentJobsList([makeJob({ score_total: 30 })], false, null);
    expect(result.display.cards[0].scoreColor).toBe("green");
  });

  it("yellow for score 10-29", () => {
    const result = presentJobsList([makeJob({ score_total: 15 })], false, null);
    expect(result.display.cards[0].scoreColor).toBe("yellow");
  });

  it("gray for score 0-9", () => {
    const result = presentJobsList([makeJob({ score_total: 5 })], false, null);
    expect(result.display.cards[0].scoreColor).toBe("gray");
  });

  it("red for negative score", () => {
    const result = presentJobsList([makeJob({ score_total: -10 })], false, null);
    expect(result.display.cards[0].scoreColor).toBe("red");
  });
});

// ── Salary formatting ───────────────────────────────────────────

describe("presentJobsList salary", () => {
  it("formats range as $Xk – $Yk", () => {
    const result = presentJobsList(
      [makeJob({ comp_min: 120000, comp_max: 180000 })],
      false,
      null,
    );
    expect(result.display.cards[0].salary).toBe("$120k – $180k");
  });

  it("formats single value when min equals max", () => {
    const result = presentJobsList(
      [makeJob({ comp_min: 150000, comp_max: 150000 })],
      false,
      null,
    );
    expect(result.display.cards[0].salary).toBe("$150k");
  });

  it("returns null when both are null", () => {
    const result = presentJobsList(
      [makeJob({ comp_min: null, comp_max: null })],
      false,
      null,
    );
    expect(result.display.cards[0].salary).toBeNull();
  });

  it("formats when only min is set", () => {
    const result = presentJobsList(
      [makeJob({ comp_min: 100000, comp_max: null })],
      false,
      null,
    );
    expect(result.display.cards[0].salary).toBe("$100k");
  });
});

// ── Tech tags truncation ────────────────────────────────────────

describe("presentJobsList techTags", () => {
  it("shows max 4 tags", () => {
    const result = presentJobsList([makeJob()], false, null);
    const card = result.display.cards[0];
    expect(card.techTags).toHaveLength(4);
    expect(card.extraTagCount).toBe(1);
  });

  it("no extra count when 4 or fewer tags", () => {
    const result = presentJobsList(
      [makeJob({ tech_tags: ["ts", "react"] })],
      false,
      null,
    );
    const card = result.display.cards[0];
    expect(card.techTags).toHaveLength(2);
    expect(card.extraTagCount).toBe(0);
  });

  it("handles null tech_tags", () => {
    const result = presentJobsList(
      [makeJob({ tech_tags: null })],
      false,
      null,
    );
    expect(result.display.cards[0].techTags).toEqual([]);
    expect(result.display.cards[0].extraTagCount).toBe(0);
  });
});

// ── Snippet generation ──────────────────────────────────────────

describe("presentJobsList snippet", () => {
  it("strips HTML from description", () => {
    const result = presentJobsList([makeJob()], false, null);
    const snippet = result.display.cards[0].snippet;
    expect(snippet).not.toContain("<p>");
    expect(snippet).toContain("Build great software");
  });

  it("truncates long descriptions", () => {
    const longDesc = "<p>" + "a".repeat(300) + "</p>";
    const result = presentJobsList(
      [makeJob({ description_clean: longDesc })],
      false,
      null,
    );
    const snippet = result.display.cards[0].snippet;
    expect(snippet.length).toBeLessThanOrEqual(145); // 140 + "..."
    expect(snippet).toMatch(/\.\.\.$/);
  });

  it("handles null description", () => {
    const result = presentJobsList(
      [makeJob({ description_clean: null })],
      false,
      null,
    );
    expect(result.display.cards[0].snippet).toBe("");
  });
});

// ── Status mapping ──────────────────────────────────────────────

describe("presentJobsList status", () => {
  it("defaults to NEW when null", () => {
    const result = presentJobsList(
      [makeJob({ status: null })],
      false,
      null,
    );
    expect(result.display.cards[0].status).toBe("NEW");
  });

  it("marks SAVED as isSaved", () => {
    const result = presentJobsList(
      [makeJob({ status: "SAVED" })],
      false,
      null,
    );
    expect(result.display.cards[0].isSaved).toBe(true);
  });

  it("marks APPLIED as isSaved", () => {
    const result = presentJobsList(
      [makeJob({ status: "APPLIED" })],
      false,
      null,
    );
    expect(result.display.cards[0].isSaved).toBe(true);
  });

  it("marks NEW as not isSaved", () => {
    const result = presentJobsList(
      [makeJob({ status: "NEW" })],
      false,
      null,
    );
    expect(result.display.cards[0].isSaved).toBe(false);
  });
});

// ── Score highlights ────────────────────────────────────────────

describe("presentJobsList scoreHighlights", () => {
  it("extracts up to 3 highlights", () => {
    const result = presentJobsList([makeJob()], false, null);
    const highlights = result.display.cards[0].scoreHighlights;
    expect(highlights.length).toBeLessThanOrEqual(3);
  });

  it("skips zero values and total", () => {
    const result = presentJobsList(
      [
        makeJob({
          score_breakdown_json: {
            must_have_match: 1,
            title_match: 0,
            strong_plus_match: 5,
            total: 35,
          },
        }),
      ],
      false,
      null,
    );
    const highlights = result.display.cards[0].scoreHighlights;
    const labels = highlights.map((h) => h.label);
    expect(labels).not.toContain("Total");
  });

  it("handles null breakdown", () => {
    const result = presentJobsList(
      [makeJob({ score_breakdown_json: null })],
      false,
      null,
    );
    expect(result.display.cards[0].scoreHighlights).toEqual([]);
  });

  it("positive values get + prefix", () => {
    const result = presentJobsList(
      [
        makeJob({
          score_breakdown_json: { must_have_match: 1, strong_plus_match: 5, total: 35 },
        }),
      ],
      false,
      null,
    );
    const plusItems = result.display.cards[0].scoreHighlights.filter(
      (h) => h.value.startsWith("+"),
    );
    expect(plusItems.length).toBeGreaterThan(0);
  });
});
