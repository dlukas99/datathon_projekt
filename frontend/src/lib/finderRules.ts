// What each profile requires in "Predloži mjesto" (config/finder_rules.json, shared with
// the backend, which applies the rules).
import rules from '../../../config/finder_rules.json'

const PROFILES: Record<string, { summary: string; rationale: string }> = rules.profiles

export function finderSummary(profileId: string): string {
  return (PROFILES[profileId] ?? PROFILES.opci)?.summary ?? ''
}

export function finderRationale(profileId: string): string {
  return (PROFILES[profileId] ?? PROFILES.opci)?.rationale ?? ''
}
