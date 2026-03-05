"use client";

import {
  Box,
  Container,
  Text,
  Flex,
  Input,
  HStack,
  Link as ChakraLink,
  Spinner,
  VStack,
} from "@chakra-ui/react";
import NextLink from "next/link";
import type { JobsListContract, JobCard, CategorizedTag, TechTagCategory } from "./presenter";
import type { JobStatus } from "@/lib/types";

interface JobsListViewProps {
  contract: JobsListContract;
  filters: {
    status: string;
    minScore: string;
    remote: string;
  };
  onFilterChange: (key: string, value: string) => void;
  onQuickSave: (jobId: number, currentStatus: JobStatus) => void;
}

const STATUSES: JobStatus[] = ["NEW", "SAVED", "APPLIED", "SKIPPED", "INTERVIEWING"];

/* ─── Accent colors ────────────────────────────────────── */

const SCORE_COLOR = "#c8913a";
const MUST_HAVE_COLOR = "#c8913a";
const STRONG_PLUS_COLOR = "#6b8f71";
const AVOID_COLOR = "#8b5454";

function scoreColorHex(score: string | null): string {
  if (!score) return "#52525b";
  const n = parseFloat(score);
  if (n >= 50) return SCORE_COLOR;
  if (n >= 30) return "#a3a353";
  if (n >= 10) return "#71717a";
  if (n >= 0) return "#52525b";
  return "#b45454";
}

/* ─── Logo ─────────────────────────────────────────────── */

function Logo() {
  return (
    <Flex align="center" gap={2.5}>
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8.5" stroke={SCORE_COLOR} strokeWidth="1.5" />
        <circle cx="10" cy="10" r="2" fill={SCORE_COLOR} />
        <line x1="10" y1="1.5" x2="10" y2="5.5" stroke={SCORE_COLOR} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="10" y1="14.5" x2="10" y2="18.5" stroke={SCORE_COLOR} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="1.5" y1="10" x2="5.5" y2="10" stroke={SCORE_COLOR} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="14.5" y1="10" x2="18.5" y2="10" stroke={SCORE_COLOR} strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <Text
        fontSize="lg"
        fontWeight="normal"
        letterSpacing="-0.01em"
        css={{ fontFamily: "var(--font-display), Georgia, serif" }}
      >
        MyScout
      </Text>
    </Flex>
  );
}

/* ─── Filter bar ───────────────────────────────────────── */

function FilterBar({
  filters,
  onFilterChange,
}: Pick<JobsListViewProps, "filters" | "onFilterChange">) {
  const selectStyle: React.CSSProperties = {
    padding: "5px 10px",
    borderRadius: "6px",
    border: "1px solid #27272a",
    background: "transparent",
    fontSize: "13px",
    color: "#a1a1aa",
  };

  return (
    <Flex gap={3} align="center" flexWrap="wrap">
      <select
        value={filters.status}
        onChange={(e) => onFilterChange("status", e.target.value)}
        style={selectStyle}
        aria-label="Status filter"
      >
        <option value="">All statuses</option>
        {STATUSES.map((s) => (
          <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>
        ))}
      </select>
      <Input
        placeholder="Min score"
        type="number"
        size="sm"
        width="100px"
        value={filters.minScore}
        onChange={(e) => onFilterChange("minScore", e.target.value)}
        borderColor="#27272a"
        bg="transparent"
        color="#a1a1aa"
        fontSize="13px"
        _placeholder={{ color: "#52525b" }}
      />
      <select
        value={filters.remote}
        onChange={(e) => onFilterChange("remote", e.target.value)}
        style={selectStyle}
        aria-label="Remote filter"
      >
        <option value="">All locations</option>
        <option value="remote">Remote</option>
        <option value="hybrid">Hybrid</option>
        <option value="onsite">Onsite</option>
      </select>
    </Flex>
  );
}

/* ─── Bookmark ─────────────────────────────────────────── */

function BookmarkButton({
  isSaved,
  onClick,
}: {
  isSaved: boolean;
  onClick: (e: React.MouseEvent) => void;
}) {
  return (
    <Box
      as="button"
      onClick={onClick}
      p={1}
      borderRadius="md"
      transition="all 0.15s"
      color={isSaved ? SCORE_COLOR : "#3f3f46"}
      _hover={{ color: isSaved ? SCORE_COLOR : "#71717a" }}
      title={isSaved ? "Unsave" : "Save"}
      flexShrink={0}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
      </svg>
    </Box>
  );
}

/* ─── Status pill ──────────────────────────────────────── */

const STATUS_PILL_COLORS: Record<string, string> = {
  NEW: "#3b82f6",
  SAVED: "#a855f7",
  APPLIED: "#22c55e",
  SKIPPED: "#52525b",
  INTERVIEWING: "#f59e0b",
};

function StatusPill({ status }: { status: string }) {
  const color = STATUS_PILL_COLORS[status] || "#52525b";
  return (
    <Text
      fontSize="10px"
      fontWeight="semibold"
      letterSpacing="0.05em"
      textTransform="uppercase"
      color={color}
    >
      {status}
    </Text>
  );
}

/* ─── Tag chip ─────────────────────────────────────────── */

const TAG_STYLES: Record<TechTagCategory, { bg: string; color: string; borderColor: string }> = {
  must_have: { bg: "rgba(200, 145, 58, 0.1)", color: MUST_HAVE_COLOR, borderColor: "rgba(200, 145, 58, 0.25)" },
  strong_plus: { bg: "rgba(107, 143, 113, 0.08)", color: STRONG_PLUS_COLOR, borderColor: "rgba(107, 143, 113, 0.2)" },
  avoid: { bg: "rgba(139, 84, 84, 0.08)", color: AVOID_COLOR, borderColor: "rgba(139, 84, 84, 0.2)" },
  neutral: { bg: "transparent", color: "#52525b", borderColor: "#1f1f24" },
};

function TechTag({ tag }: { tag: CategorizedTag }) {
  const style = TAG_STYLES[tag.category];
  return (
    <Text
      fontSize="11px"
      px="6px"
      py="1px"
      borderRadius="4px"
      bg={style.bg}
      color={style.color}
      border="1px solid"
      borderColor={style.borderColor}
      whiteSpace="nowrap"
      fontWeight={tag.category === "must_have" ? "600" : "normal"}
    >
      {tag.label}
    </Text>
  );
}

function BadgeTag({ label }: { label: string }) {
  return (
    <Text
      fontSize="11px"
      px="6px"
      py="1px"
      borderRadius="4px"
      bg="#1c1c24"
      color="#a1a1aa"
      border="1px solid"
      borderColor="#27272a"
      whiteSpace="nowrap"
    >
      {label}
    </Text>
  );
}

/* ─── Job card ─────────────────────────────────────────── */

function JobCardItem({
  card,
  onQuickSave,
}: {
  card: JobCard;
  onQuickSave: (jobId: number, currentStatus: JobStatus) => void;
}) {
  return (
    <Box
      py={4}
      borderBottomWidth="1px"
      borderColor="#1a1a1f"
      _hover={{ bg: "#0c0c10" }}
      transition="background 0.15s"
    >
      {/* Row 1: Title + Score */}
      <Flex justify="space-between" align="start" gap={4}>
        <ChakraLink asChild _hover={{ textDecoration: "none" }}>
          <NextLink href={`/jobs/${card.id}`}>
            <Text
              fontWeight="600"
              fontSize="15px"
              lineHeight="1.4"
              color="#ededef"
              _hover={{ color: SCORE_COLOR }}
              transition="color 0.1s"
              lineClamp={1}
            >
              {card.title}
            </Text>
          </NextLink>
        </ChakraLink>

        <HStack gap={2} flexShrink={0} align="center">
          {card.scored ? (
            <Text
              fontSize="15px"
              fontWeight="700"
              color={scoreColorHex(card.score)}
              fontVariantNumeric="tabular-nums"
            >
              {card.score}
            </Text>
          ) : (
            <Text fontSize="12px" color="#3f3f46">&mdash;</Text>
          )}
          <BookmarkButton
            isSaved={card.isSaved}
            onClick={(e) => {
              e.preventDefault();
              onQuickSave(card.id, card.status);
            }}
          />
        </HStack>
      </Flex>

      {/* Row 2: Company · Location · Salary */}
      <Flex align="center" gap={0} mt={0.5} flexWrap="wrap">
        <Text fontSize="13px" color="#71717a">
          {card.company}
        </Text>
        {card.location && (
          <Text fontSize="13px" color="#52525b">
            <Text as="span" mx={1.5}>·</Text>
            <Text as="span" color="#52525b">{card.location}</Text>
          </Text>
        )}
        {card.salary && (
          <Text fontSize="13px" color="#52525b">
            <Text as="span" mx={1.5}>·</Text>
            <Text as="span" color="#8b9a6b">{card.salary}</Text>
          </Text>
        )}
      </Flex>

      {/* Row 3: Tags + Status + Date */}
      <Flex justify="space-between" align="center" mt={2}>
        <HStack gap={1} flexWrap="wrap">
          {card.seniorityBadge && (
            <BadgeTag label={card.seniorityBadge} />
          )}
          {card.remoteBadge && (
            <BadgeTag label={card.remoteBadge} />
          )}
          {card.techTags.map((tag) => (
            <TechTag key={tag.label} tag={tag} />
          ))}
          {card.extraTagCount > 0 && (
            <Text fontSize="11px" color="#3f3f46">
              +{card.extraTagCount}
            </Text>
          )}
        </HStack>

        <HStack gap={2.5} flexShrink={0} align="center">
          <StatusPill status={card.status} />
          {card.lastSeen && (
            <Text fontSize="11px" color="#3f3f46">
              {card.lastSeen}
            </Text>
          )}
        </HStack>
      </Flex>
    </Box>
  );
}

/* ─── Main view ────────────────────────────────────────── */

export function JobsListView({
  contract,
  filters,
  onFilterChange,
  onQuickSave,
}: JobsListViewProps) {
  return (
    <Container maxW="3xl" py={6} px={5}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={8}>
        <Logo />
        {contract.display.jobCount && (
          <Text fontSize="12px" color="#3f3f46" fontVariantNumeric="tabular-nums">
            {contract.display.jobCount}
          </Text>
        )}
      </Flex>

      {/* Filters */}
      <Box mb={6} pb={5} borderBottomWidth="1px" borderColor="#1a1a1f">
        <FilterBar filters={filters} onFilterChange={onFilterChange} />
      </Box>

      {/* States */}
      {contract.renderAs === "loading" && (
        <Flex justify="center" py={20}>
          <Spinner size="md" color="#3f3f46" />
        </Flex>
      )}

      {contract.instructions.showError && (
        <Flex justify="center" py={20}>
          <VStack gap={2}>
            <Text fontSize="md" color="#ef4444">Failed to load jobs</Text>
            <Text fontSize="sm" color="#52525b">Check that Postgres is running and tables are created.</Text>
          </VStack>
        </Flex>
      )}

      {contract.instructions.showEmptyState && (
        <Flex justify="center" py={20}>
          <VStack gap={3}>
            <Text fontSize="md" color="#71717a">No jobs found</Text>
            <Text fontSize="sm" color="#52525b" textAlign="center" maxW="sm">
              Run <code>make ingest</code> then <code>make score</code> to populate jobs.
            </Text>
          </VStack>
        </Flex>
      )}

      {/* Job list */}
      {contract.renderAs === "content" && (
        <Box>
          {contract.display.cards.map((card) => (
            <JobCardItem key={card.id} card={card} onQuickSave={onQuickSave} />
          ))}
        </Box>
      )}
    </Container>
  );
}
