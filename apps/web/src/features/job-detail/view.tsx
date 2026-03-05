"use client";

import {
  Box,
  Container,
  Text,
  Textarea,
  Button,
  Link as ChakraLink,
  Flex,
  HStack,
  Spinner,
  VStack,
} from "@chakra-ui/react";
import NextLink from "next/link";
import type { JobDetailContract, CategorizedTag, TechTagCategory } from "./presenter";
import type { JobStatus } from "@/lib/types";

interface JobDetailViewProps {
  contract: JobDetailContract;
  notesValue: string;
  onNotesChange: (value: string) => void;
  onStatusChange: (status: JobStatus) => void;
  onSaveNotes: () => void;
  isMutating: boolean;
}

const STATUSES: JobStatus[] = ["NEW", "SAVED", "APPLIED", "SKIPPED", "INTERVIEWING"];

const SCORE_COLOR = "#c8913a";
const MUST_HAVE_COLOR = "#c8913a";
const STRONG_PLUS_COLOR = "#6b8f71";
const AVOID_COLOR = "#8b5454";

const STATUS_COLORS: Record<string, string> = {
  NEW: "#3b82f6",
  SAVED: "#a855f7",
  APPLIED: "#22c55e",
  SKIPPED: "#52525b",
  INTERVIEWING: "#f59e0b",
};

function scoreColorHex(score: string | null): string {
  if (!score) return "#52525b";
  const n = parseFloat(score);
  if (n >= 50) return SCORE_COLOR;
  if (n >= 30) return "#a3a353";
  if (n >= 10) return "#71717a";
  if (n >= 0) return "#52525b";
  return "#b45454";
}

/* ─── Sidebar section ──────────────────────────────────── */

function SidebarSection({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <Box py={4} borderBottomWidth="1px" borderColor="#1a1a1f">
      {title && (
        <Text
          fontSize="10px"
          fontWeight="600"
          textTransform="uppercase"
          letterSpacing="0.08em"
          color="#52525b"
          mb={2.5}
        >
          {title}
        </Text>
      )}
      {children}
    </Box>
  );
}

/* ─── Tech tag (categorized) ──────────────────────────── */

const TAG_STYLES: Record<TechTagCategory, { bg: string; color: string; borderColor: string }> = {
  must_have: { bg: "rgba(200, 145, 58, 0.1)", color: MUST_HAVE_COLOR, borderColor: "rgba(200, 145, 58, 0.25)" },
  strong_plus: { bg: "rgba(107, 143, 113, 0.08)", color: STRONG_PLUS_COLOR, borderColor: "rgba(107, 143, 113, 0.2)" },
  avoid: { bg: "rgba(139, 84, 84, 0.08)", color: AVOID_COLOR, borderColor: "rgba(139, 84, 84, 0.2)" },
  neutral: { bg: "#1c1c24", color: "#a1a1aa", borderColor: "#27272a" },
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

function DetailBadge({ label }: { label: string }) {
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

/* ─── Main view ───────────────────────────────────────── */

export function JobDetailView({
  contract,
  notesValue,
  onNotesChange,
  onStatusChange,
  onSaveNotes,
  isMutating,
}: JobDetailViewProps) {
  const { display, instructions } = contract;

  if (contract.renderAs === "loading") {
    return (
      <Container maxW="6xl" py={8}>
        <Flex justify="center" py={20}>
          <Spinner size="md" color="#3f3f46" />
        </Flex>
      </Container>
    );
  }

  if (instructions.showError) {
    return (
      <Container maxW="6xl" py={8}>
        <Flex justify="center" py={20}>
          <VStack gap={2}>
            <Text fontSize="md" color="#ef4444">Job not found</Text>
            <ChakraLink asChild>
              <NextLink href="/jobs">
                <Text color="#71717a" fontSize="sm">&larr; Back to jobs</Text>
              </NextLink>
            </ChakraLink>
          </VStack>
        </Flex>
      </Container>
    );
  }

  return (
    <Container maxW="6xl" py={6} px={5}>
      {/* Back link */}
      <ChakraLink asChild _hover={{ textDecoration: "none" }}>
        <NextLink href="/jobs">
          <Text
            color="#52525b"
            fontSize="13px"
            mb={6}
            display="inline-block"
            _hover={{ color: "#a1a1aa" }}
            transition="color 0.1s"
          >
            &larr; Jobs
          </Text>
        </NextLink>
      </ChakraLink>

      {/* Header */}
      <Box mb={6}>
        <Text
          as="h1"
          fontSize="24px"
          fontWeight="700"
          lineHeight="1.3"
          color="#ededef"
          letterSpacing="-0.02em"
          mb={1}
        >
          {display.title}
        </Text>
        <Text fontSize="16px" color="#71717a" fontWeight="500">
          {display.company}
        </Text>

        <HStack gap={2} mt={2} flexWrap="wrap">
          {display.location && (
            <Text fontSize="13px" color="#52525b">{display.location}</Text>
          )}
          {display.salary && (
            <>
              <Text fontSize="13px" color="#3f3f46">·</Text>
              <Text fontSize="13px" color="#8b9a6b">{display.salary}</Text>
            </>
          )}
          {display.remoteBadge && (
            <>
              <Text fontSize="13px" color="#3f3f46">·</Text>
              <DetailBadge label={display.remoteBadge} />
            </>
          )}
          {display.seniorityBadge && (
            <>
              <Text fontSize="13px" color="#3f3f46">·</Text>
              <DetailBadge label={display.seniorityBadge} />
            </>
          )}
        </HStack>
      </Box>

      {/* Two-column layout */}
      <Box
        display={{ base: "flex", lg: "grid" }}
        flexDirection="column"
        gridTemplateColumns={{ lg: "1fr 300px" }}
        gap={{ base: 6, lg: 10 }}
        alignItems="start"
      >
        {/* ─── Sidebar (shows first on mobile, right column on desktop) ─── */}
        <Box
          order={{ base: 0, lg: 1 }}
          position={{ lg: "sticky" }}
          top={{ lg: "24px" }}
          width="100%"
        >
          {/* Score */}
          {instructions.hasScore && (
            <SidebarSection>
              <Flex align="baseline" gap={2}>
                <Text
                  fontSize="36px"
                  fontWeight="700"
                  color={scoreColorHex(display.score)}
                  lineHeight="1"
                  fontVariantNumeric="tabular-nums"
                >
                  {display.score}
                </Text>
                <Text fontSize="12px" color="#3f3f46">score</Text>
              </Flex>
            </SidebarSection>
          )}

          {/* Apply */}
          {display.applyUrl && (
            <SidebarSection>
              <ChakraLink
                href={display.applyUrl}
                target="_blank"
                rel="noopener noreferrer"
                _hover={{ textDecoration: "none" }}
              >
                <Button
                  width="full"
                  size="sm"
                  bg={SCORE_COLOR}
                  color="#0a0a0c"
                  fontWeight="600"
                  fontSize="13px"
                  _hover={{ bg: "#d9a04a" }}
                >
                  Apply &rarr;
                </Button>
              </ChakraLink>
            </SidebarSection>
          )}

          {/* Status */}
          <SidebarSection title="Status">
            <Flex gap={1.5} flexWrap="wrap">
              {STATUSES.map((s) => {
                const isActive = display.status === s;
                const statusColor = STATUS_COLORS[s];
                return (
                  <Box
                    key={s}
                    as="button"
                    px={2.5}
                    py={1}
                    borderRadius="5px"
                    fontSize="11px"
                    fontWeight="600"
                    letterSpacing="0.02em"
                    transition="all 0.1s"
                    cursor="pointer"
                    _disabled={{ opacity: 0.5, cursor: "not-allowed" }}
                    onClick={() => !isMutating && onStatusChange(s)}
                    bg={isActive ? statusColor : "transparent"}
                    color={isActive ? "#0a0a0c" : "#52525b"}
                    border="1px solid"
                    borderColor={isActive ? statusColor : "#27272a"}
                    _hover={{
                      borderColor: statusColor,
                      color: isActive ? "#0a0a0c" : statusColor,
                    }}
                  >
                    {s}
                  </Box>
                );
              })}
            </Flex>
          </SidebarSection>

          {/* Notes */}
          <SidebarSection title="Notes">
            <Textarea
              placeholder="Add notes..."
              value={notesValue}
              onChange={(e) => onNotesChange(e.target.value)}
              mb={2}
              borderColor="#27272a"
              bg="transparent"
              fontSize="13px"
              rows={3}
              color="#a1a1aa"
              _placeholder={{ color: "#3f3f46" }}
              _focus={{ borderColor: "#3f3f46" }}
            />
            <Button
              size="xs"
              variant="outline"
              borderColor="#27272a"
              color="#71717a"
              fontSize="12px"
              onClick={onSaveNotes}
              disabled={isMutating}
              _hover={{ borderColor: "#3f3f46", color: "#a1a1aa" }}
            >
              Save
            </Button>
          </SidebarSection>

          {/* Score Breakdown */}
          {instructions.hasScore && display.scoreRows.length > 0 && (
            <SidebarSection title="Score Breakdown">
              <Flex direction="column" gap={1}>
                {display.scoreRows.map((row) => (
                  <Flex key={row.label} justify="space-between" align="center">
                    <Text fontSize="12px" color="#52525b">{row.label}</Text>
                    <Text
                      fontSize="12px"
                      fontWeight="600"
                      color={row.color}
                      fontVariantNumeric="tabular-nums"
                    >
                      {row.value}
                    </Text>
                  </Flex>
                ))}
              </Flex>
            </SidebarSection>
          )}

          {/* Tech */}
          {instructions.hasTechTags && (
            <SidebarSection title="Technologies">
              <Flex gap={1.5} flexWrap="wrap">
                {display.techTags.map((tag) => (
                  <TechTag key={tag.label} tag={tag} />
                ))}
              </Flex>
            </SidebarSection>
          )}

          {/* Sources */}
          {instructions.hasVariants && (
            <SidebarSection title={`Sources (${display.variants.length})`}>
              <Flex direction="column" gap={2}>
                {display.variants.map((v) => (
                  <Flex key={v.id} justify="space-between" align="center" gap={2}>
                    <HStack gap={1.5} minW={0}>
                      <Text fontSize="11px" color="#52525b" flexShrink={0}>
                        {v.source}
                      </Text>
                      {v.url && (
                        <ChakraLink
                          href={v.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          color="#3f3f46"
                          fontSize="11px"
                          _hover={{ color: "#71717a" }}
                          lineClamp={1}
                        >
                          {v.urlDisplay}
                        </ChakraLink>
                      )}
                    </HStack>
                    <Text fontSize="11px" color="#3f3f46" flexShrink={0}>
                      {v.dateSeen}
                    </Text>
                  </Flex>
                ))}
              </Flex>
            </SidebarSection>
          )}
        </Box>

        {/* ─── Main content: Description ─── */}
        <Box order={{ base: 1, lg: 0 }} minW={0}>
          {instructions.hasDescription && (
            <Box
              fontSize="14px"
              lineHeight="1.75"
              color="#a1a1aa"
              css={{
                "& h1": {
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "#ededef",
                  marginTop: "2em",
                  marginBottom: "0.5em",
                  lineHeight: 1.3,
                },
                "& h2": {
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "#d4d4d8",
                  marginTop: "1.75em",
                  marginBottom: "0.5em",
                  lineHeight: 1.3,
                },
                "& h3, & h4": {
                  fontSize: "14px",
                  fontWeight: 600,
                  color: "#d4d4d8",
                  marginTop: "1.5em",
                  marginBottom: "0.4em",
                },
                "& p": {
                  marginBottom: "1em",
                },
                "& ul, & ol": {
                  paddingLeft: "1.5em",
                  marginBottom: "1em",
                },
                "& li": {
                  marginBottom: "0.35em",
                },
                "& li::marker": {
                  color: "#3f3f46",
                },
                "& a": {
                  color: SCORE_COLOR,
                  textDecoration: "none",
                  "&:hover": {
                    textDecoration: "underline",
                  },
                },
                "& strong, & b": {
                  color: "#d4d4d8",
                  fontWeight: 600,
                },
                "& > *:first-child": {
                  marginTop: 0,
                },
              }}
              dangerouslySetInnerHTML={{ __html: display.descriptionHtml }}
            />
          )}

          {!instructions.hasDescription && (
            <Text fontSize="14px" color="#3f3f46" fontStyle="italic">
              No description available.
            </Text>
          )}
        </Box>
      </Box>
    </Container>
  );
}
