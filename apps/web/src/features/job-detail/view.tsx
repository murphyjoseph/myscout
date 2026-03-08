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
import type { JobDetailContract } from "./types";
import type { CategorizedTag } from "@/lib/display-utils";

/* ─── Sidebar section ─────────────────────────────────── */

function SidebarSection({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <Box py={4} borderBottomWidth="1px" borderColor="border.subtle">
      {title && (
        <Text
          fontSize="10px"
          fontWeight="600"
          textTransform="uppercase"
          letterSpacing="0.08em"
          color="fg.dim"
          mb={2.5}
        >
          {title}
        </Text>
      )}
      {children}
    </Box>
  );
}

/* ─── Tech tag (uses presenter-provided styles) ──────── */

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

function DetailBadge({ label }: { label: string }) {
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

/* ─── Main view ───────────────────────────────────────── */

export function JobDetailView({ contract }: { contract: JobDetailContract }) {
  const { display, instructions, effects } = contract;

  if (contract.renderAs === "loading") {
    return (
      <Container maxW="6xl" py={8}>
        <Flex justify="center" py={20}>
          <Spinner size="md" color="fg.faint" />
        </Flex>
      </Container>
    );
  }

  if (instructions.showError) {
    return (
      <Container maxW="6xl" py={8}>
        <Flex justify="center" py={20}>
          <VStack gap={2}>
            <Text fontSize="md" color="fg.error">Job not found</Text>
            <ChakraLink asChild>
              <NextLink href="/jobs">
                <Text color="fg.subtle" fontSize="sm">&larr; Back to jobs</Text>
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
            color="fg.dim"
            fontSize="13px"
            mb={6}
            display="inline-block"
            _hover={{ color: "fg.muted" }}
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
          color="fg"
          letterSpacing="-0.02em"
          mb={1}
        >
          {display.title}
        </Text>
        <Text fontSize="16px" color="fg.subtle" fontWeight="500">
          {display.company}
        </Text>

        <HStack gap={2} mt={2} flexWrap="wrap">
          {display.location && (
            <Text fontSize="13px" color="fg.dim">{display.location}</Text>
          )}
          {display.salary && (
            <>
              <Text fontSize="13px" color="fg.faint">·</Text>
              <Text fontSize="13px" color="salary.fg">{display.salary}</Text>
            </>
          )}
          {display.remoteBadge && (
            <>
              <Text fontSize="13px" color="fg.faint">·</Text>
              <DetailBadge label={display.remoteBadge} />
            </>
          )}
          {display.seniorityBadge && (
            <>
              <Text fontSize="13px" color="fg.faint">·</Text>
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
                  color={display.scoreColor}
                  lineHeight="1"
                  fontVariantNumeric="tabular-nums"
                >
                  {display.score}
                </Text>
                <Text fontSize="12px" color="fg.faint">score</Text>
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
                  bg="accent.solid"
                  color="accent.contrast"
                  fontWeight="600"
                  fontSize="13px"
                  _hover={{ bg: "accent.emphasized" }}
                >
                  Apply &rarr;
                </Button>
              </ChakraLink>
            </SidebarSection>
          )}

          {/* Status */}
          <SidebarSection title="Status">
            <Flex gap={1.5} flexWrap="wrap">
              {display.statusButtons.map((btn) => {
                const isActive = display.status === btn.status;
                return (
                  <Box
                    key={btn.status}
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
                    onClick={() => !instructions.isMutating && effects.onStatusChange(btn.status)}
                    bg={isActive ? btn.color : "transparent"}
                    color={isActive ? "accent.contrast" : "fg.dim"}
                    border="1px solid"
                    borderColor={isActive ? btn.color : "border"}
                    _hover={{
                      borderColor: btn.color,
                      color: isActive ? "accent.contrast" : btn.color,
                    }}
                  >
                    {btn.status}
                  </Box>
                );
              })}
            </Flex>
          </SidebarSection>

          {/* Notes */}
          <SidebarSection title="Notes">
            <Textarea
              placeholder="Add notes..."
              value={display.notesValue}
              onChange={(e) => effects.onNotesChange(e.target.value)}
              mb={2}
              borderColor="border"
              bg="transparent"
              fontSize="13px"
              rows={3}
              color="fg.muted"
              _placeholder={{ color: "fg.faint" }}
              _focus={{ borderColor: "fg.faint" }}
            />
            <Button
              size="xs"
              variant="outline"
              borderColor="border"
              color="fg.subtle"
              fontSize="12px"
              onClick={effects.onSaveNotes}
              disabled={instructions.isMutating}
              _hover={{ borderColor: "fg.faint", color: "fg.muted" }}
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
                    <Text fontSize="12px" color="fg.dim">{row.label}</Text>
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
                      <Text fontSize="11px" color="fg.dim" flexShrink={0}>
                        {v.source}
                      </Text>
                      {v.url && (
                        <ChakraLink
                          href={v.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          color="fg.faint"
                          fontSize="11px"
                          _hover={{ color: "fg.subtle" }}
                          lineClamp={1}
                        >
                          {v.urlDisplay}
                        </ChakraLink>
                      )}
                    </HStack>
                    <Text fontSize="11px" color="fg.faint" flexShrink={0}>
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
              color="fg.muted"
              css={{
                "& h1": {
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "var(--chakra-colors-fg)",
                  marginTop: "2em",
                  marginBottom: "0.5em",
                  lineHeight: 1.3,
                },
                "& h2": {
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "var(--chakra-colors-fg-heading)",
                  marginTop: "1.75em",
                  marginBottom: "0.5em",
                  lineHeight: 1.3,
                },
                "& h3, & h4": {
                  fontSize: "14px",
                  fontWeight: 600,
                  color: "var(--chakra-colors-fg-heading)",
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
                  color: "var(--chakra-colors-fg-faint)",
                },
                "& a": {
                  color: "var(--chakra-colors-accent-solid)",
                  textDecoration: "none",
                  "&:hover": {
                    textDecoration: "underline",
                  },
                },
                "& strong, & b": {
                  color: "var(--chakra-colors-fg-heading)",
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
            <Text fontSize="14px" color="fg.faint" fontStyle="italic">
              No description available.
            </Text>
          )}
        </Box>
      </Box>
    </Container>
  );
}
