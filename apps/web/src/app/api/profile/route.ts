import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { join } from "path";
import yaml from "js-yaml";

// LOCAL-ONLY: No auth — reads user's local profile.yml
export async function GET() {
  try {
    const configDir = join(process.cwd(), "..", "..", "config");
    const profilePath = join(configDir, "profile.yml");

    const raw = await readFile(profilePath, "utf-8");
    const doc = yaml.load(raw) as Record<string, unknown>;

    const profile = (doc?.profile ?? {}) as Record<string, unknown>;
    const tech = (profile?.tech_preferences ?? {}) as Record<string, unknown>;

    return NextResponse.json({
      must_have: Array.isArray(tech.must_have) ? tech.must_have : [],
      strong_plus: Array.isArray(tech.strong_plus) ? tech.strong_plus : [],
      avoid: Array.isArray(tech.avoid) ? tech.avoid : [],
    });
  } catch {
    // No profile.yml or malformed — return empty prefs (graceful degradation)
    return NextResponse.json({
      must_have: [],
      strong_plus: [],
      avoid: [],
    });
  }
}
