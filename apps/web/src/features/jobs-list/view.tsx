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
import type { JobsListContract, JobCard } from "./types";
import type { CategorizedTag } from "@/lib/display-utils";
import type { JobStatus } from "@/lib/types";

/* ─── Logo ─────────────────────────────────────────────── */

function Logo() {
  return (
    <Flex align="center" gap={2.5}>
      <Box color="accent.solid">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="8.5" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="10" cy="10" r="2" fill="currentColor" />
          <line x1="10" y1="1.5" x2="10" y2="5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="10" y1="14.5" x2="10" y2="18.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="1.5" y1="10" x2="5.5" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="14.5" y1="10" x2="18.5" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </Box>
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

const STATUSES: JobStatus[] = ["NEW", "SAVED", "APPLIED", "SKIPPED", "INTERVIEWING"];

function FilterBar({ contract }: { contract: JobsListContract }) {
  const { filters } = contract.display;
  const { onFilterChange } = contract.effects;

  const selectStyle: React.CSSProperties = {
    padding: "5px 10px",
    borderRadius: "6px",
    border: "1px solid var(--chakra-colors-border)",
    background: "transparent",
    fontSize: "13px",
    color: "var(--chakra-colors-fg-muted)",
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
        borderColor="border"
        bg="transparent"
        color="fg.muted"
        fontSize="13px"
        _placeholder={{ color: "fg.dim" }}
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
      color={isSaved ? "accent.solid" : "fg.faint"}
      _hover={{ color: isSaved ? "accent.solid" : "fg.subtle" }}
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

function StatusPill({ status, color }: { status: string; color: string }) {
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

function TechTag({ tag }: { tag: CategorizedTag }) {
  return (
    <Text
      fontSize="11px"
      px="6px"
      py="1px"
      borderRadius="4px"
      bg={tag.style.bg}
      color={tag.style.color}
      border="1px solid"
      borderColor={tag.style.borderColor}
      whiteSpace="nowrap"
      fontWeight={tag.style.fontWeight}
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
      bg="bg.muted"
      color="fg.muted"
      border="1px solid"
      borderColor="border"
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
      borderColor="border.subtle"
      _hover={{ bg: "bg.subtle" }}
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
              color="fg"
              _hover={{ color: "accent.solid" }}
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
              color={card.scoreColor}
              fontVariantNumeric="tabular-nums"
            >
              {card.score}
            </Text>
          ) : (
            <Text fontSize="12px" color="fg.faint">&mdash;</Text>
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
        <Text fontSize="13px" color="fg.subtle">
          {card.company}
        </Text>
        {card.location && (
          <Text fontSize="13px" color="fg.dim">
            <Text as="span" mx={1.5}>·</Text>
            <Text as="span" color="fg.dim">{card.location}</Text>
          </Text>
        )}
        {card.salary && (
          <Text fontSize="13px" color="fg.dim">
            <Text as="span" mx={1.5}>·</Text>
            <Text as="span" color="salary.fg">{card.salary}</Text>
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
            <Text fontSize="11px" color="fg.faint">
              +{card.extraTagCount}
            </Text>
          )}
        </HStack>

        <HStack gap={2.5} flexShrink={0} align="center">
          <StatusPill status={card.status} color={card.statusColor} />
          {card.lastSeen && (
            <Text fontSize="11px" color="fg.faint">
              {card.lastSeen}
            </Text>
          )}
        </HStack>
      </Flex>
    </Box>
  );
}

/* ─── Main view ────────────────────────────────────────── */

export function JobsListView({ contract }: { contract: JobsListContract }) {
  return (
    <Container maxW="3xl" py={6} px={5}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={8}>
        <Logo />
        {contract.display.jobCount && (
          <Text fontSize="12px" color="fg.faint" fontVariantNumeric="tabular-nums">
            {contract.display.jobCount}
          </Text>
        )}
      </Flex>

      {/* Filters */}
      <Box mb={6} pb={5} borderBottomWidth="1px" borderColor="border.subtle">
        <FilterBar contract={contract} />
      </Box>

      {/* States */}
      {contract.renderAs === "loading" && (
        <Flex justify="center" py={20}>
          <Spinner size="md" color="fg.faint" />
        </Flex>
      )}

      {contract.instructions.showError && (
        <Flex justify="center" py={20}>
          <VStack gap={2}>
            <Text fontSize="md" color="fg.error">Failed to load jobs</Text>
            <Text fontSize="sm" color="fg.dim">Check that Postgres is running and tables are created.</Text>
          </VStack>
        </Flex>
      )}

      {contract.instructions.showEmptyState && (
        <Flex justify="center" py={20}>
          <VStack gap={3}>
            <Text fontSize="md" color="fg.subtle">No jobs found</Text>
            <Text fontSize="sm" color="fg.dim" textAlign="center" maxW="sm">
              Run <code>make ingest</code> then <code>make score</code> to populate jobs.
            </Text>
          </VStack>
        </Flex>
      )}

      {/* Job list */}
      {contract.renderAs === "content" && (
        <Box>
          {contract.display.cards.map((card) => (
            <JobCardItem key={card.id} card={card} onQuickSave={contract.effects.onQuickSave} />
          ))}
        </Box>
      )}
    </Container>
  );
}
