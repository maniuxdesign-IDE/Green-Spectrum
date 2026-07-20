#!/usr/bin/env python3
"""Green Spectrum local full-stack server.

This deliberately uses only the Python standard library so the current static
prototype can gain backend foundations without introducing a framework install.
"""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "green_spectrum.sqlite3"
METHODOLOGY_VERSION = "0.1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dumps(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_columns(db: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, definition in columns.items():
        if name not in existing:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def as_list(value: object) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def first_value(data: dict, key: str, fallback: str = "") -> str:
    value = data.get(key)
    if isinstance(value, list):
        return str(value[0]) if value else fallback
    return str(value) if value not in (None, "") else fallback


def question_number(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def slugify(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or f"organisation-{secrets.token_hex(4)}"


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT,
  email TEXT UNIQUE,
  image TEXT,
  role TEXT,
  locale TEXT DEFAULT 'en-GB',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_active_at TEXT,
  consent_version TEXT,
  terms_version TEXT
);

CREATE TABLE IF NOT EXISTS organisations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE,
  organisation_type TEXT,
  industry TEXT,
  subsector TEXT,
  size_band TEXT,
  headquarters_country TEXT,
  operating_regions TEXT,
  website TEXT,
  created_by_user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  FOREIGN KEY(created_by_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS organisation_memberships (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  organisation_id TEXT NOT NULL,
  membership_role TEXT NOT NULL,
  permission_level TEXT NOT NULL,
  joined_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS methodology_versions (
  id TEXT PRIMARY KEY,
  version TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  published_at TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 0,
  changelog TEXT NOT NULL,
  content_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journeys (
  id TEXT PRIMARY KEY,
  organisation_id TEXT,
  title TEXT NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  current_stage TEXT NOT NULL,
  methodology_version_id TEXT NOT NULL,
  started_by_user_id TEXT,
  started_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  archived_at TEXT,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id),
  FOREIGN KEY(methodology_version_id) REFERENCES methodology_versions(id),
  FOREIGN KEY(started_by_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS journey_progress (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  stage_key TEXT NOT NULL,
  status TEXT NOT NULL,
  completion_percentage INTEGER NOT NULL DEFAULT 0,
  started_at TEXT,
  completed_at TEXT,
  last_visited_at TEXT,
  needs_review INTEGER NOT NULL DEFAULT 0,
  output_summary TEXT,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS public_content_blocks (
  id TEXT PRIMARY KEY,
  page_key TEXT NOT NULL,
  section_key TEXT NOT NULL,
  locale TEXT NOT NULL DEFAULT 'en-GB',
  heading TEXT,
  body TEXT,
  structured_content TEXT NOT NULL,
  display_order INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'published',
  published_at TEXT,
  version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resources (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  stage TEXT,
  use_mode TEXT,
  file_type TEXT NOT NULL,
  file_size TEXT,
  storage_key TEXT,
  preview_image_key TEXT,
  methodology_version_id TEXT NOT NULL,
  licence TEXT,
  version TEXT NOT NULL,
  published_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY(methodology_version_id) REFERENCES methodology_versions(id)
);

CREATE TABLE IF NOT EXISTS resource_bundles (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  resource_ids TEXT NOT NULL,
  storage_key TEXT,
  version TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS analytics_events (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT,
  user_id TEXT,
  event_name TEXT NOT NULL,
  route TEXT,
  section_key TEXT,
  metadata TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  consent_state TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS consent_records (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  anonymous_session_id TEXT,
  consent_type TEXT NOT NULL,
  granted INTEGER NOT NULL,
  version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS feature_flags (
  id TEXT PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 0,
  rules TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS onboarding_states (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  organisation_id TEXT,
  form_data TEXT NOT NULL,
  section_states TEXT NOT NULL,
  context_profile TEXT NOT NULL,
  recommended_route TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_contexts (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  anonymous_session_id TEXT,
  professional_role TEXT,
  department TEXT,
  influence_level TEXT,
  personal_objective TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organisation_profile_versions (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  snapshot TEXT NOT NULL,
  changed_by_user_id TEXT,
  change_reason TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS industry_classifications (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  taxonomy_version TEXT NOT NULL,
  primary_industry_name TEXT,
  subsector_name TEXT,
  value_chain_positions TEXT,
  operating_characteristics TEXT,
  confirmed_by_user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS journey_participant_plans (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  expected_participant_count TEXT,
  functions TEXT,
  planned_workshop_date TEXT,
  planned_session_length TEXT,
  location_type TEXT,
  notes TEXT,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS stakeholders (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  name TEXT NOT NULL,
  stakeholder_type TEXT,
  internal_external TEXT,
  description TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS journey_stakeholders (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  stakeholder_id TEXT NOT NULL,
  role_in_journey TEXT,
  influence_level TEXT,
  interest_level TEXT,
  knowledge_contribution TEXT,
  decision_authority TEXT,
  participation_required INTEGER NOT NULL DEFAULT 0,
  source_type TEXT,
  confidence TEXT,
  confirmed_by_user INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  FOREIGN KEY(journey_id) REFERENCES journeys(id),
  FOREIGN KEY(stakeholder_id) REFERENCES stakeholders(id)
);

CREATE TABLE IF NOT EXISTS evidence_documents (
  id TEXT PRIMARY KEY,
  organisation_id TEXT,
  journey_id TEXT,
  title TEXT NOT NULL,
  document_type TEXT,
  original_file_name TEXT,
  mime_type TEXT,
  file_size INTEGER,
  storage_key TEXT,
  checksum TEXT,
  source_owner TEXT,
  confidentiality TEXT,
  analysis_permission INTEGER NOT NULL DEFAULT 0,
  recommendation_permission INTEGER NOT NULL DEFAULT 0,
  upload_status TEXT NOT NULL,
  processing_status TEXT NOT NULL,
  uploaded_by_user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id),
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS document_processing_jobs (
  id TEXT PRIMARY KEY,
  evidence_document_id TEXT NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  progress INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  started_at TEXT,
  completed_at TEXT,
  error_code TEXT,
  error_message TEXT,
  processor_version TEXT,
  FOREIGN KEY(evidence_document_id) REFERENCES evidence_documents(id)
);

CREATE TABLE IF NOT EXISTS extracted_evidence_items (
  id TEXT PRIMARY KEY,
  evidence_document_id TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  statement TEXT NOT NULL,
  source_location TEXT,
  source_page TEXT,
  source_section TEXT,
  confidence TEXT,
  extraction_method TEXT,
  review_status TEXT,
  reviewed_by_user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(evidence_document_id) REFERENCES evidence_documents(id)
);

CREATE TABLE IF NOT EXISTS data_sources (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT,
  owner TEXT,
  availability TEXT,
  quality TEXT,
  format TEXT,
  permission_status TEXT,
  source_type TEXT,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS external_research_preferences (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  allowed INTEGER NOT NULL DEFAULT 0,
  categories TEXT NOT NULL,
  allowed_domains TEXT,
  prohibited_domains TEXT,
  require_user_review INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS research_tasks (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  category TEXT NOT NULL,
  query_definition TEXT NOT NULL,
  jurisdiction TEXT,
  status TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  started_at TEXT,
  completed_at TEXT,
  expires_at TEXT,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS initial_signals (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  empathy_type TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  confidence TEXT,
  source_type TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS journey_constraints (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  severity TEXT,
  owner TEXT,
  evidence TEXT,
  confidence TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS readiness_profiles (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  leadership_readiness TEXT,
  resource_readiness TEXT,
  data_readiness TEXT,
  cultural_readiness TEXT,
  change_speed TEXT,
  notes TEXT,
  confidence TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS provisional_maturity_orientations (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  level TEXT,
  strongest_area TEXT,
  weakest_area TEXT,
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS output_preferences (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  output_types TEXT,
  primary_audience TEXT,
  detail_level TEXT,
  preferred_formats TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS context_facts (
  id TEXT PRIMARY KEY,
  organisation_id TEXT,
  journey_id TEXT,
  fact_type TEXT NOT NULL,
  subject_type TEXT,
  subject_id TEXT,
  predicate TEXT NOT NULL,
  value TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT,
  confidence TEXT NOT NULL,
  verification_status TEXT NOT NULL,
  valid_from TEXT,
  valid_until TEXT,
  created_by_user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(organisation_id) REFERENCES organisations(id),
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS context_insights (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  insight_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  supporting_fact_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  generated_by TEXT NOT NULL,
  generator_version TEXT NOT NULL,
  status TEXT NOT NULL,
  user_edited INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS recommended_routes (
  id TEXT PRIMARY KEY,
  journey_id TEXT NOT NULL,
  stage_key TEXT NOT NULL,
  recommended_sequence TEXT NOT NULL,
  priority_themes TEXT NOT NULL,
  evidence_tasks TEXT NOT NULL,
  stakeholder_tasks TEXT NOT NULL,
  rationale TEXT NOT NULL,
  supporting_fact_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  user_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  actor_type TEXT NOT NULL,
  actor_id TEXT,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  metadata TEXT NOT NULL,
  occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS explore_states (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  active_empathy TEXT NOT NULL DEFAULT 'business',
  form_data TEXT NOT NULL,
  scores TEXT NOT NULL,
  outputs TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS business_empathy_responses (
  id TEXT PRIMARY KEY,
  explore_state_id TEXT NOT NULL,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  question_id TEXT NOT NULL,
  question_number INTEGER NOT NULL,
  category TEXT NOT NULL,
  maturity_level TEXT,
  maturity_score REAL,
  confidence TEXT,
  confidence_score REAL,
  scope TEXT,
  evidence_reference TEXT,
  notes TEXT,
  strategic_flags TEXT NOT NULL,
  discovery_domains TEXT NOT NULL DEFAULT '[]',
  selected_tools TEXT NOT NULL DEFAULT '[]',
  stakeholder_suggestions TEXT NOT NULL DEFAULT '[]',
  reflection TEXT NOT NULL DEFAULT '{}',
  systems_connections TEXT NOT NULL DEFAULT '[]',
  carry_forward_actions TEXT NOT NULL DEFAULT '[]',
  evidence_tasks TEXT NOT NULL DEFAULT '[]',
  tool_recommendations TEXT NOT NULL DEFAULT '[]',
  skipped_reason TEXT,
  needs_review INTEGER NOT NULL DEFAULT 0,
  interpretation TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(explore_state_id) REFERENCES explore_states(id)
);

CREATE TABLE IF NOT EXISTS business_empathy_outputs (
  id TEXT PRIMARY KEY,
  explore_state_id TEXT NOT NULL,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  score REAL,
  evidence_weighted_confidence REAL,
  strengths TEXT NOT NULL,
  weak_areas TEXT NOT NULL,
  evidence_gaps TEXT NOT NULL,
  contradictions TEXT NOT NULL,
  problem_signals TEXT NOT NULL,
  impact_journey_questions TEXT NOT NULL,
  human_empathy_recommendations TEXT NOT NULL,
  discovery_domain_readings TEXT NOT NULL DEFAULT '[]',
  tool_recommendations TEXT NOT NULL DEFAULT '[]',
  carry_forward_items TEXT NOT NULL DEFAULT '[]',
  systems_connections TEXT NOT NULL DEFAULT '[]',
  updated_at TEXT NOT NULL,
  FOREIGN KEY(explore_state_id) REFERENCES explore_states(id)
);

CREATE TABLE IF NOT EXISTS organisation_nodes (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  node_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  source TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  version TEXT NOT NULL,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organisation_relationships (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  source_node_id TEXT NOT NULL,
  target_node_id TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  evidence TEXT NOT NULL,
  confidence TEXT NOT NULL,
  direction TEXT NOT NULL,
  version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capability_profiles (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  capability TEXT NOT NULL,
  current_maturity TEXT,
  maturity_score REAL,
  confidence TEXT NOT NULL,
  supporting_evidence TEXT NOT NULL,
  strengths TEXT NOT NULL,
  weaknesses TEXT NOT NULL,
  unknowns TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_themes (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  theme_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  supporting_questions TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_patterns (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  title TEXT NOT NULL,
  explanation TEXT NOT NULL,
  supporting_questions TEXT NOT NULL,
  confidence TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_insights (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  title TEXT NOT NULL,
  explanation TEXT NOT NULL,
  supporting_evidence TEXT NOT NULL,
  supporting_questions TEXT NOT NULL,
  supporting_themes TEXT NOT NULL,
  supporting_relationships TEXT NOT NULL,
  confidence TEXT NOT NULL,
  editable INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_memory (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  memory_type TEXT NOT NULL,
  title TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_empathy_responses (
  id TEXT PRIMARY KEY,
  explore_state_id TEXT NOT NULL,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  question_id TEXT NOT NULL,
  question_number INTEGER NOT NULL,
  category TEXT NOT NULL,
  maturity_level TEXT,
  maturity_score REAL,
  confidence TEXT,
  confidence_score REAL,
  scope TEXT,
  represented_groups TEXT NOT NULL,
  underrepresented_groups TEXT,
  behavioural_barriers TEXT,
  capability_gaps TEXT,
  power_concern TEXT,
  research_task TEXT,
  stakeholder_representation TEXT NOT NULL DEFAULT '[]',
  discovery_domains TEXT NOT NULL DEFAULT '[]',
  selected_tools TEXT NOT NULL DEFAULT '[]',
  evidence_tasks TEXT NOT NULL DEFAULT '[]',
  systems_connections TEXT NOT NULL DEFAULT '[]',
  carry_forward_actions TEXT NOT NULL DEFAULT '[]',
  human_risk_flags TEXT NOT NULL DEFAULT '[]',
  reflection TEXT NOT NULL DEFAULT '{}',
  evidence_reference TEXT,
  notes TEXT,
  strategic_flags TEXT NOT NULL,
  skipped_reason TEXT,
  needs_review INTEGER NOT NULL DEFAULT 0,
  interpretation TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(explore_state_id) REFERENCES explore_states(id)
);

CREATE TABLE IF NOT EXISTS response_stakeholder_representations (
  id TEXT PRIMARY KEY,
  response_id TEXT NOT NULL,
  stakeholder_id TEXT NOT NULL,
  representation_status TEXT NOT NULL,
  influence_level TEXT,
  impact_exposure TEXT,
  decision_authority TEXT,
  evidence_type TEXT,
  confidentiality_level TEXT,
  notes TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS behavioural_barriers (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  barrier_type TEXT NOT NULL,
  description TEXT NOT NULL,
  stakeholder_ids TEXT NOT NULL,
  evidence_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_impact_signals (
  id TEXT PRIMARY KEY,
  response_id TEXT NOT NULL,
  impact_type TEXT NOT NULL,
  affected_stakeholders TEXT NOT NULL,
  severity TEXT NOT NULL,
  duration TEXT,
  distribution TEXT,
  evidence_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stakeholder_research_tasks (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  stakeholder_id TEXT NOT NULL,
  research_purpose TEXT NOT NULL,
  suggested_method TEXT NOT NULL,
  questions TEXT NOT NULL,
  consent_requirements TEXT NOT NULL,
  owner TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS facilitation_recommendations (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  recommendation_type TEXT NOT NULL,
  rationale TEXT NOT NULL,
  stakeholder_ids TEXT NOT NULL,
  suggested_format TEXT NOT NULL,
  suggested_tools TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_risk_flags (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  urgency TEXT NOT NULL,
  restricted INTEGER NOT NULL DEFAULT 1,
  escalation_required INTEGER NOT NULL DEFAULT 1,
  owner TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_empathy_outputs (
  id TEXT PRIMARY KEY,
  explore_state_id TEXT NOT NULL,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  score REAL,
  evidence_weighted_confidence REAL,
  represented_groups TEXT NOT NULL,
  underrepresented_groups TEXT NOT NULL,
  strengths TEXT NOT NULL,
  weak_areas TEXT NOT NULL,
  evidence_gaps TEXT NOT NULL,
  contradictions TEXT NOT NULL,
  problem_signals TEXT NOT NULL,
  participation_tasks TEXT NOT NULL,
  impact_journey_questions TEXT NOT NULL,
  planetary_empathy_recommendations TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(explore_state_id) REFERENCES explore_states(id)
);

CREATE TABLE IF NOT EXISTS planetary_empathy_responses (
  id TEXT PRIMARY KEY,
  explore_state_id TEXT NOT NULL,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  question_id TEXT NOT NULL,
  question_number INTEGER NOT NULL,
  category TEXT NOT NULL,
  maturity_level TEXT,
  maturity_score REAL,
  confidence TEXT,
  confidence_score REAL,
  scope TEXT,
  ecological_boundary TEXT NOT NULL DEFAULT '{}',
  dependencies TEXT,
  impact_signal TEXT,
  material_flow TEXT,
  environmental_task TEXT,
  discovery_domains TEXT NOT NULL DEFAULT '[]',
  selected_tools TEXT NOT NULL DEFAULT '[]',
  evidence_tasks TEXT NOT NULL DEFAULT '[]',
  systems_connections TEXT NOT NULL DEFAULT '[]',
  carry_forward_actions TEXT NOT NULL DEFAULT '[]',
  planetary_risk_flags TEXT NOT NULL DEFAULT '[]',
  reflection TEXT NOT NULL DEFAULT '{}',
  evidence_reference TEXT,
  notes TEXT,
  strategic_flags TEXT NOT NULL,
  skipped_reason TEXT,
  needs_review INTEGER NOT NULL DEFAULT 0,
  interpretation TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(explore_state_id) REFERENCES explore_states(id)
);

CREATE TABLE IF NOT EXISTS planetary_empathy_outputs (
  id TEXT PRIMARY KEY,
  explore_state_id TEXT NOT NULL,
  anonymous_session_id TEXT NOT NULL,
  journey_id TEXT,
  score REAL,
  evidence_weighted_confidence REAL,
  strengths TEXT NOT NULL,
  weak_areas TEXT NOT NULL,
  evidence_gaps TEXT NOT NULL,
  boundary_coverage TEXT NOT NULL,
  ecological_dependencies TEXT NOT NULL,
  impact_signals TEXT NOT NULL,
  material_flows TEXT NOT NULL,
  hotspot_candidates TEXT NOT NULL,
  contradictions TEXT NOT NULL,
  problem_signals TEXT NOT NULL,
  environmental_evidence_tasks TEXT NOT NULL,
  impact_journey_questions TEXT NOT NULL,
  synthesis_handover TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(explore_state_id) REFERENCES explore_states(id)
);

CREATE TABLE IF NOT EXISTS ecological_boundaries (
  id TEXT PRIMARY KEY,
  journey_id TEXT,
  response_id TEXT NOT NULL,
  organisational_scope TEXT,
  lifecycle_stages TEXT,
  geographic_scope TEXT,
  ecosystem_types TEXT,
  reporting_period_start TEXT,
  reporting_period_end TEXT,
  exclusions TEXT,
  limitations TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ecological_dependencies (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  dependency_type TEXT NOT NULL,
  resource_or_service TEXT,
  location TEXT,
  criticality TEXT,
  substitutability TEXT,
  evidence_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS environmental_impact_signals (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  impact_type TEXT NOT NULL,
  lifecycle_stage TEXT,
  location TEXT,
  direction TEXT,
  magnitude TEXT,
  duration TEXT,
  reversibility TEXT,
  affected_ecosystems TEXT,
  affected_stakeholders TEXT,
  evidence_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS material_flow_signals (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  material_name TEXT,
  material_category TEXT,
  source_region TEXT,
  quantity TEXT,
  unit TEXT,
  destination TEXT,
  circularity_status TEXT,
  toxicity_risk TEXT,
  criticality TEXT,
  evidence_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ecological_hotspot_candidates (
  id TEXT PRIMARY KEY,
  journey_id TEXT,
  assessment_id TEXT NOT NULL,
  source_object_ids TEXT NOT NULL,
  hotspot_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  lifecycle_stage TEXT,
  geography TEXT,
  severity TEXT,
  leverage_potential TEXT,
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS environmental_evidence_tasks (
  id TEXT PRIMARY KEY,
  journey_id TEXT,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  evidence_needed TEXT NOT NULL,
  suggested_source TEXT,
  suggested_owner TEXT,
  specialist_required INTEGER NOT NULL DEFAULT 0,
  priority TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS planetary_risk_flags (
  id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  response_id TEXT NOT NULL,
  risk_type TEXT NOT NULL,
  description TEXT,
  affected_systems TEXT NOT NULL,
  urgency TEXT,
  severity TEXT,
  cascading_risk INTEGER NOT NULL DEFAULT 0,
  restricted INTEGER NOT NULL DEFAULT 0,
  owner TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_journey_states (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  organisation_id TEXT,
  journey_id TEXT,
  methodology_version_id TEXT,
  version_number INTEGER NOT NULL DEFAULT 1,
  title TEXT,
  description TEXT,
  scope_statement TEXT,
  scope_type TEXT,
  boundary_description TEXT,
  boundary_type TEXT,
  geographical_scope TEXT,
  time_horizon TEXT,
  upstream_boundary TEXT,
  downstream_boundary TEXT,
  includes_enabling_functions INTEGER NOT NULL DEFAULT 0,
  includes_external_partners INTEGER NOT NULL DEFAULT 0,
  source_page3_version_id TEXT,
  status TEXT NOT NULL,
  completion_percentage INTEGER NOT NULL DEFAULT 0,
  current_section TEXT,
  autosave_revision INTEGER NOT NULL DEFAULT 0,
  form_snapshot TEXT NOT NULL DEFAULT '{}',
  analysis_snapshot TEXT NOT NULL DEFAULT '{}',
  last_saved_at TEXT,
  completed_at TEXT,
  completed_by TEXT,
  reopened_at TEXT,
  reopened_by TEXT,
  revision_reason TEXT,
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS journey_boundaries (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  boundary_name TEXT,
  boundary_description TEXT,
  organisational_scope TEXT,
  geographical_scope TEXT,
  temporal_scope TEXT,
  upstream_extent TEXT,
  downstream_extent TEXT,
  included_entities TEXT NOT NULL DEFAULT '[]',
  excluded_entities TEXT NOT NULL DEFAULT '[]',
  included_business_units TEXT NOT NULL DEFAULT '[]',
  excluded_business_units TEXT NOT NULL DEFAULT '[]',
  scope_1_included INTEGER NOT NULL DEFAULT 0,
  scope_2_included INTEGER NOT NULL DEFAULT 0,
  scope_3_categories_included TEXT NOT NULL DEFAULT '[]',
  known_limitations TEXT,
  confidence TEXT,
  evidence_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_journey_stages (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  stage_type TEXT,
  sequence INTEGER NOT NULL,
  geography TEXT,
  business_unit TEXT,
  internal_or_external TEXT,
  owner_stakeholder_id TEXT,
  starts_when TEXT,
  ends_when TEXT,
  is_enabling_function INTEGER NOT NULL DEFAULT 0,
  is_optional INTEGER NOT NULL DEFAULT 0,
  is_system_generated INTEGER NOT NULL DEFAULT 0,
  source_type TEXT,
  source_id TEXT,
  confidence TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS stage_activities (
  id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  activity_type TEXT,
  frequency TEXT,
  duration TEXT,
  criticality TEXT,
  internal_or_external TEXT,
  owner_stakeholder_id TEXT,
  performing_stakeholder_id TEXT,
  authorising_stakeholder_id TEXT,
  technology_used TEXT,
  policy_or_rule_reference TEXT,
  operational_constraints TEXT,
  source_type TEXT,
  source_id TEXT,
  confidence TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS stage_decisions (
  id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  activity_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  decision_type TEXT,
  decision_owner_stakeholder_id TEXT,
  decision_authority_level TEXT,
  decision_frequency TEXT,
  decision_trigger TEXT,
  decision_criteria TEXT,
  information_inputs TEXT,
  constraints TEXT,
  known_biases TEXT,
  incentives TEXT,
  escalation_route TEXT,
  delay_effect TEXT,
  influence_level TEXT,
  policy_reference TEXT,
  confidence TEXT,
  evidence_status TEXT,
  source_type TEXT,
  source_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stage_stakeholders (
  id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  stakeholder_id TEXT,
  stakeholder_name TEXT,
  relationship_type TEXT,
  role TEXT,
  influence_level TEXT,
  decision_authority TEXT,
  dependency_level TEXT,
  impact_received TEXT,
  impact_created TEXT,
  engagement_level TEXT,
  trust_level TEXT,
  conflict_level TEXT,
  participation_level TEXT,
  is_vulnerable_group INTEGER NOT NULL DEFAULT 0,
  is_non_human_stakeholder INTEGER NOT NULL DEFAULT 0,
  is_future_generation_proxy INTEGER NOT NULL DEFAULT 0,
  confidence TEXT,
  evidence_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_inputs (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  source_stage_id TEXT,
  destination_stage_id TEXT,
  activity_id TEXT,
  input_type TEXT,
  name TEXT NOT NULL,
  description TEXT,
  source_organisation_or_location TEXT,
  quantity TEXT,
  unit TEXT,
  measurement_period TEXT,
  renewable_status TEXT,
  criticality TEXT,
  substitutability TEXT,
  scarcity_risk TEXT,
  supply_risk TEXT,
  ethical_risk TEXT,
  environmental_risk TEXT,
  social_risk TEXT,
  geography TEXT,
  supplier_stakeholder_id TEXT,
  data_quality TEXT,
  confidence TEXT,
  evidence_id TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_outputs (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT NOT NULL,
  activity_id TEXT,
  output_type TEXT,
  name TEXT NOT NULL,
  description TEXT,
  destination_stage_id TEXT,
  destination_stakeholder_id TEXT,
  quantity TEXT,
  unit TEXT,
  measurement_period TEXT,
  value_created TEXT,
  waste_classification TEXT,
  hazardous_status TEXT,
  recovery_potential TEXT,
  reusability TEXT,
  recyclability TEXT,
  data_quality TEXT,
  confidence TEXT,
  evidence_id TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_human_experiences (
  id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  activity_id TEXT,
  stakeholder_id TEXT,
  stakeholder_name TEXT,
  experience_type TEXT,
  need TEXT,
  emotion TEXT,
  frustration TEXT,
  motivation TEXT,
  behaviour TEXT,
  barrier TEXT,
  trust_condition TEXT,
  workload_effect TEXT,
  wellbeing_effect TEXT,
  perceived_fairness TEXT,
  participation_level TEXT,
  adoption_readiness TEXT,
  power_dynamic TEXT,
  equity_or_justice_issue TEXT,
  description TEXT,
  source_type TEXT,
  source_id TEXT,
  evidence_id TEXT,
  confidence TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_category_definitions (
  id TEXT PRIMARY KEY,
  methodology_version_id TEXT,
  empathy_type TEXT NOT NULL,
  category_key TEXT NOT NULL,
  label TEXT NOT NULL,
  description TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_impacts (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT NOT NULL,
  activity_id TEXT,
  decision_id TEXT,
  source_input_id TEXT,
  source_output_id TEXT,
  empathy_type TEXT NOT NULL,
  impact_category TEXT,
  impact_subcategory TEXT,
  title TEXT NOT NULL,
  description TEXT,
  direction TEXT,
  directness TEXT,
  scope_classification TEXT,
  magnitude TEXT,
  severity TEXT,
  likelihood TEXT,
  frequency TEXT,
  duration TEXT,
  reversibility TEXT,
  time_horizon TEXT,
  geography TEXT,
  affected_stakeholder_id TEXT,
  affected_ecosystem TEXT,
  affected_business_area TEXT,
  benefit_or_harm TEXT,
  transferred_impact INTEGER NOT NULL DEFAULT 0,
  externalised_impact INTEGER NOT NULL DEFAULT 0,
  cumulative_effect INTEGER NOT NULL DEFAULT 0,
  trade_off_present INTEGER NOT NULL DEFAULT 0,
  rebound_risk INTEGER NOT NULL DEFAULT 0,
  confidence TEXT,
  evidence_status TEXT,
  verification_status TEXT,
  source_problem_signal_id TEXT,
  source_type TEXT,
  source_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS journey_assumptions (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  activity_id TEXT,
  decision_id TEXT,
  impact_id TEXT,
  statement TEXT NOT NULL,
  assumption_type TEXT,
  criticality TEXT,
  uncertainty_level TEXT,
  consequence_if_wrong TEXT,
  evidence_required TEXT,
  validation_method TEXT,
  owner_stakeholder_id TEXT,
  status TEXT NOT NULL DEFAULT 'unverified',
  source_type TEXT,
  source_id TEXT,
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_unknowns (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  question TEXT NOT NULL,
  unknown_type TEXT,
  importance TEXT,
  urgency TEXT,
  blocking_status TEXT,
  recommended_research_method TEXT,
  data_source_needed TEXT,
  owner_stakeholder_id TEXT,
  due_date TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  source_type TEXT,
  source_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_evidence_links (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  activity_id TEXT,
  decision_id TEXT,
  input_id TEXT,
  output_id TEXT,
  impact_id TEXT,
  relationship_id TEXT,
  hotspot_id TEXT,
  evidence_id TEXT,
  relationship_type TEXT,
  supports_or_challenges TEXT,
  relevance_notes TEXT,
  strength TEXT,
  confidence TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_relationships (
  id TEXT PRIMARY KEY,
  organisation_id TEXT,
  journey_id TEXT,
  impact_journey_state_id TEXT,
  source_object_type TEXT NOT NULL,
  source_object_id TEXT NOT NULL,
  target_object_type TEXT NOT NULL,
  target_object_id TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  direction TEXT,
  strength TEXT,
  delay_description TEXT,
  polarity TEXT,
  confidence TEXT,
  rationale TEXT,
  evidence_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  generator_version TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_feedback_loops (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  loop_type TEXT,
  polarity TEXT,
  delay_description TEXT,
  system_behaviour TEXT,
  confidence TEXT,
  evidence_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_feedback_loop_members (
  id TEXT PRIMARY KEY,
  feedback_loop_id TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  relationship_id TEXT,
  role_in_loop TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_bottlenecks (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  activity_id TEXT,
  decision_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  bottleneck_type TEXT,
  capacity_constraint TEXT,
  delay_created TEXT,
  stakeholders_affected TEXT,
  business_effect TEXT,
  human_effect TEXT,
  planetary_effect TEXT,
  governance_effect TEXT,
  severity TEXT,
  persistence TEXT,
  confidence TEXT,
  evidence_id TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_dependencies (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  source_object_type TEXT NOT NULL,
  source_object_id TEXT NOT NULL,
  target_object_type TEXT NOT NULL,
  target_object_id TEXT NOT NULL,
  dependency_type TEXT,
  criticality TEXT,
  substitutability TEXT,
  failure_consequence TEXT,
  dependency_owner_id TEXT,
  geography TEXT,
  time_horizon TEXT,
  confidence TEXT,
  evidence_id TEXT,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_strengths (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  activity_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  strength_type TEXT,
  existing_capability TEXT,
  positive_impact TEXT,
  transferability TEXT,
  scalability TEXT,
  stakeholders_involved TEXT NOT NULL DEFAULT '[]',
  evidence_id TEXT,
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_opportunity_signals (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  activity_id TEXT,
  impact_id TEXT,
  relationship_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  opportunity_type TEXT,
  expected_value TEXT,
  potential_leverage TEXT,
  required_capability TEXT,
  known_dependencies TEXT,
  confidence TEXT,
  evidence_status TEXT,
  source_type TEXT,
  source_id TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hotspot_candidates (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  hotspot_type TEXT,
  impact_dimensions TEXT NOT NULL DEFAULT '[]',
  evidence_basis TEXT NOT NULL DEFAULT '[]',
  rationale TEXT,
  severity TEXT,
  uncertainty TEXT,
  leverage_potential TEXT,
  confidence TEXT,
  generator_version TEXT,
  user_decision TEXT,
  status TEXT NOT NULL DEFAULT 'suggested',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leverage_points (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  relationship_id TEXT,
  hotspot_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  leverage_type TEXT,
  intervention_level TEXT,
  rationale TEXT,
  expected_influence TEXT,
  uncertainty TEXT,
  confidence TEXT,
  generator_version TEXT,
  user_decision TEXT,
  status TEXT NOT NULL DEFAULT 'suggested',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_journey_problem_signals (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  stage_id TEXT,
  hotspot_id TEXT,
  leverage_point_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  signal_type TEXT,
  source_type TEXT,
  source_id TEXT,
  evidence_basis TEXT NOT NULL DEFAULT '[]',
  rationale TEXT,
  confidence TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stage_handover_manifests (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  target_stage_key TEXT NOT NULL,
  manifest TEXT NOT NULL,
  stale INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_journey_import_records (
  id TEXT PRIMARY KEY,
  impact_journey_state_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT,
  imported_payload TEXT NOT NULL,
  imported_count INTEGER NOT NULL DEFAULT 0,
  conflict_count INTEGER NOT NULL DEFAULT 0,
  stale_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_states (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  organisation_id TEXT,
  journey_id TEXT,
  methodology_version_id TEXT,
  version_number INTEGER NOT NULL DEFAULT 1,
  title TEXT,
  description TEXT,
  source_page3_version_id TEXT,
  source_impact_journey_version_id TEXT,
  status TEXT NOT NULL,
  completion_percentage INTEGER NOT NULL DEFAULT 0,
  current_section TEXT,
  selected_problem_minimum INTEGER NOT NULL DEFAULT 3,
  selected_problem_maximum INTEGER NOT NULL DEFAULT 5,
  autosave_revision INTEGER NOT NULL DEFAULT 0,
  form_snapshot TEXT NOT NULL DEFAULT '{}',
  analysis_snapshot TEXT NOT NULL DEFAULT '{}',
  last_saved_at TEXT,
  completed_at TEXT,
  completed_by TEXT,
  reopened_at TEXT,
  reopened_by TEXT,
  revision_reason TEXT,
  is_stale INTEGER NOT NULL DEFAULT 0,
  stale_reason TEXT,
  review_required INTEGER NOT NULL DEFAULT 0,
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS problem_signals (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  organisation_id TEXT,
  journey_id TEXT,
  source_page TEXT NOT NULL,
  source_object_type TEXT,
  source_object_id TEXT,
  source_version TEXT,
  title TEXT NOT NULL,
  description TEXT,
  evidence_summary TEXT,
  source_confidence TEXT,
  status TEXT NOT NULL DEFAULT 'imported',
  imported_at TEXT NOT NULL,
  reviewed_at TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS problems (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  organisation_id TEXT,
  journey_id TEXT,
  title TEXT NOT NULL,
  short_title TEXT,
  description TEXT,
  problem_statement TEXT,
  problem_type TEXT,
  origin_stage TEXT,
  primary_stage_id TEXT,
  primary_activity_id TEXT,
  primary_decision_id TEXT,
  primary_hotspot_id TEXT,
  primary_leverage_point_id TEXT,
  affected_business_area TEXT,
  affected_geography TEXT,
  time_horizon TEXT,
  severity_summary TEXT,
  uncertainty_summary TEXT,
  status TEXT NOT NULL,
  confidence TEXT,
  confidence_score INTEGER,
  verification_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  owner_stakeholder_id TEXT,
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS problem_statements (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  stakeholder_or_system TEXT,
  experienced_problem TEXT,
  stage_or_context TEXT,
  known_cause TEXT,
  suspected_cause TEXT,
  business_consequence TEXT,
  human_consequence TEXT,
  planetary_consequence TEXT,
  governance_consequence TEXT,
  evidence_summary TEXT,
  remaining_uncertainty TEXT,
  scope_boundary TEXT,
  statement_version INTEGER NOT NULL DEFAULT 1,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_signal_links (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  problem_signal_id TEXT NOT NULL,
  source_stage TEXT,
  relationship_type TEXT,
  contribution_strength TEXT,
  notes TEXT,
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_evidence_links (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  evidence_id TEXT,
  relationship_type TEXT,
  supports_or_challenges TEXT,
  strength TEXT,
  relevance TEXT,
  confidence TEXT,
  verification_status TEXT,
  source_excerpt_reference TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_stakeholders (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  stakeholder_id TEXT,
  stakeholder_name TEXT,
  relationship_type TEXT,
  impact_level TEXT,
  influence_level TEXT,
  decision_authority TEXT,
  dependency_level TEXT,
  vulnerability TEXT,
  participation_level TEXT,
  conflict_level TEXT,
  support_level TEXT,
  confidence TEXT,
  evidence_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_ecosystems (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  ecosystem_name TEXT,
  ecosystem_type TEXT,
  geography TEXT,
  relationship_type TEXT,
  impact_level TEXT,
  dependency_level TEXT,
  reversibility TEXT,
  time_horizon TEXT,
  confidence TEXT,
  evidence_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_relationships (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  source_problem_id TEXT NOT NULL,
  target_problem_id TEXT NOT NULL,
  relationship_type TEXT,
  direction TEXT,
  strength TEXT,
  confidence TEXT,
  rationale TEXT,
  evidence_status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_merge_candidates (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  problem_a_id TEXT NOT NULL,
  problem_b_id TEXT NOT NULL,
  similarity_score REAL,
  shared_evidence_ids TEXT NOT NULL DEFAULT '[]',
  shared_hotspot_ids TEXT NOT NULL DEFAULT '[]',
  shared_stakeholder_ids TEXT NOT NULL DEFAULT '[]',
  shared_stage_ids TEXT NOT NULL DEFAULT '[]',
  rationale TEXT,
  confidence TEXT,
  status TEXT NOT NULL,
  user_decision TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS root_cause_assessments (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  candidate_cause_problem_id TEXT,
  candidate_cause_statement TEXT,
  cause_type TEXT,
  evidence_strength TEXT,
  causal_confidence TEXT,
  time_delay TEXT,
  interdependency_level TEXT,
  alternative_explanations TEXT,
  status TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  rationale TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS maturity_positioning (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  green_spectrum_level TEXT,
  current_position TEXT,
  desired_position TEXT,
  primary_maturity_dimension TEXT,
  secondary_maturity_dimensions TEXT NOT NULL DEFAULT '[]',
  classification_answers TEXT NOT NULL DEFAULT '{}',
  confidence TEXT,
  rationale TEXT,
  supporting_evidence_ids TEXT NOT NULL DEFAULT '[]',
  source_assessment_ids TEXT NOT NULL DEFAULT '[]',
  rule_version TEXT,
  generation_method TEXT,
  user_status TEXT,
  user_notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS maturity_classification_responses (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  question_key TEXT NOT NULL,
  question_text TEXT,
  selected_option TEXT,
  mapped_level TEXT,
  rationale TEXT,
  confidence TEXT,
  evidence_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_maturity_dimensions (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  maturity_dimension_key TEXT,
  relevance_level TEXT,
  current_maturity_level TEXT,
  desired_maturity_level TEXT,
  evidence_ids TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS complexity_assessments (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  cynefin_domain TEXT,
  cause_effect_clarity TEXT,
  predictability TEXT,
  solution_known TEXT,
  expertise_required TEXT,
  stakeholder_agreement TEXT,
  interdependency_level TEXT,
  system_volatility TEXT,
  evidence_quality TEXT,
  urgency TEXT,
  experimentation_need TEXT,
  risk_of_standard_solution TEXT,
  confidence TEXT,
  rationale TEXT,
  rule_version TEXT,
  generation_method TEXT,
  user_status TEXT,
  user_notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS complexity_classification_responses (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  question_key TEXT NOT NULL,
  question_text TEXT,
  selected_option TEXT,
  mapped_domain TEXT,
  rationale TEXT,
  confidence TEXT,
  evidence_id TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS response_archetypes (
  id TEXT PRIMARY KEY,
  maturity_level TEXT NOT NULL,
  cynefin_domain TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  recommended_response TEXT,
  typical_methods TEXT NOT NULL DEFAULT '[]',
  prerequisites TEXT NOT NULL DEFAULT '[]',
  warnings TEXT NOT NULL DEFAULT '[]',
  default_decision_route TEXT,
  rule_version TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_assessments (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  dimension TEXT NOT NULL,
  score INTEGER,
  scale_min INTEGER NOT NULL DEFAULT 1,
  scale_max INTEGER NOT NULL DEFAULT 5,
  qualitative_label TEXT,
  rationale TEXT,
  confidence TEXT,
  evidence_ids TEXT NOT NULL DEFAULT '[]',
  assessed_by TEXT,
  assessment_method TEXT,
  rule_version TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_weighting_profiles (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  profile_type TEXT,
  is_default INTEGER NOT NULL DEFAULT 0,
  created_by TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_weighting_profile_dimensions (
  id TEXT PRIMARY KEY,
  weighting_profile_id TEXT NOT NULL,
  dimension TEXT NOT NULL,
  weight REAL NOT NULL,
  rationale TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_scores (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  weighting_profile_id TEXT NOT NULL,
  calculated_score REAL,
  normalised_score REAL,
  calculation_trace TEXT NOT NULL,
  formula_version TEXT,
  calculated_at TEXT NOT NULL,
  user_confirmed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS priority_recommendations (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  recommendation_category TEXT,
  recommended_response_archetype_id TEXT,
  recommended_action TEXT,
  rationale TEXT,
  trigger_inputs TEXT NOT NULL DEFAULT '{}',
  confidence TEXT,
  uncertainty TEXT,
  generator_version TEXT,
  status TEXT NOT NULL,
  user_decision TEXT,
  user_notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_clusters (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  cluster_type TEXT,
  generation_method TEXT,
  rationale TEXT,
  confidence TEXT,
  status TEXT NOT NULL,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_cluster_members (
  id TEXT PRIMARY KEY,
  cluster_id TEXT NOT NULL,
  problem_id TEXT NOT NULL,
  membership_strength TEXT,
  membership_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_opportunity_branches (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  branch_type TEXT,
  title TEXT NOT NULL,
  description TEXT,
  source_leverage_point_id TEXT,
  source_strength_id TEXT,
  source_opportunity_signal_id TEXT,
  time_horizon TEXT,
  potential_value TEXT,
  required_capability TEXT,
  confidence TEXT,
  status TEXT NOT NULL,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_portfolios (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  title TEXT,
  description TEXT,
  status TEXT NOT NULL,
  selection_limit INTEGER NOT NULL DEFAULT 5,
  portfolio_rationale TEXT,
  portfolio_risks TEXT NOT NULL DEFAULT '[]',
  shared_dependencies TEXT NOT NULL DEFAULT '[]',
  shared_capabilities TEXT NOT NULL DEFAULT '[]',
  shared_owners TEXT NOT NULL DEFAULT '[]',
  completed_at TEXT,
  completed_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priority_portfolio_items (
  id TEXT PRIMARY KEY,
  priority_portfolio_id TEXT NOT NULL,
  problem_id TEXT NOT NULL,
  portfolio_status TEXT,
  rank INTEGER,
  selection_rationale TEXT,
  decision_rationale TEXT,
  selected_by TEXT,
  selected_at TEXT,
  review_date TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_rationales (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  problem_id TEXT,
  portfolio_id TEXT,
  decision_type TEXT,
  decision TEXT,
  rationale TEXT,
  supporting_evidence_ids TEXT NOT NULL DEFAULT '[]',
  contradictory_evidence_ids TEXT NOT NULL DEFAULT '[]',
  assumptions TEXT NOT NULL DEFAULT '[]',
  uncertainty TEXT,
  alternative_options TEXT NOT NULL DEFAULT '[]',
  trade_offs TEXT NOT NULL DEFAULT '[]',
  risks TEXT NOT NULL DEFAULT '[]',
  user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prioritisation_import_records (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT,
  source_version TEXT,
  imported_payload TEXT NOT NULL,
  imported_count INTEGER NOT NULL DEFAULT 0,
  conflict_count INTEGER NOT NULL DEFAULT 0,
  stale_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS page6_handover_manifests (
  id TEXT PRIMARY KEY,
  priority_state_id TEXT NOT NULL,
  manifest TEXT NOT NULL,
  confirmed INTEGER NOT NULL DEFAULT 0,
  stale INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_states (
  id TEXT PRIMARY KEY,
  anonymous_session_id TEXT NOT NULL,
  organisation_id TEXT,
  journey_id TEXT,
  methodology_version_id TEXT,
  version_number INTEGER NOT NULL DEFAULT 1,
  source_priority_state_id TEXT,
  source_priority_portfolio_id TEXT,
  title TEXT,
  description TEXT,
  status TEXT NOT NULL,
  completion_percentage INTEGER NOT NULL DEFAULT 0,
  current_section TEXT,
  autosave_revision INTEGER NOT NULL DEFAULT 0,
  form_snapshot TEXT NOT NULL DEFAULT '{}',
  analysis_snapshot TEXT NOT NULL DEFAULT '{}',
  last_saved_at TEXT,
  completed_at TEXT,
  completed_by TEXT,
  reopened_at TEXT,
  reopened_by TEXT,
  revision_reason TEXT,
  is_stale INTEGER NOT NULL DEFAULT 0,
  stale_reason TEXT,
  review_required INTEGER NOT NULL DEFAULT 0,
  created_by TEXT,
  updated_by TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS selected_problem_focus (
  id TEXT PRIMARY KEY,
  intervention_state_id TEXT NOT NULL,
  problem_id TEXT,
  source_problem_id TEXT,
  focus_statement TEXT,
  scope TEXT,
  desired_change TEXT,
  reason_for_selection TEXT,
  portfolio_rationale TEXT,
  decision_conditions TEXT NOT NULL DEFAULT '[]',
  constraints TEXT NOT NULL DEFAULT '[]',
  dependencies TEXT NOT NULL DEFAULT '[]',
  capability_gaps TEXT NOT NULL DEFAULT '[]',
  known_risks TEXT NOT NULL DEFAULT '[]',
  known_assumptions TEXT NOT NULL DEFAULT '[]',
  known_unknowns TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS desired_outcomes (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  title TEXT,
  description TEXT,
  outcome_type TEXT,
  business_outcome TEXT,
  human_outcome TEXT,
  planetary_outcome TEXT,
  governance_outcome TEXT,
  target_stakeholders TEXT NOT NULL DEFAULT '[]',
  target_ecosystems TEXT NOT NULL DEFAULT '[]',
  target_date TEXT,
  success_conditions TEXT NOT NULL DEFAULT '[]',
  failure_conditions TEXT NOT NULL DEFAULT '[]',
  ethical_constraints TEXT,
  acceptable_trade_offs TEXT,
  unacceptable_trade_offs TEXT,
  baseline_status TEXT,
  evidence_required TEXT,
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backcast_steps (
  id TEXT PRIMARY KEY,
  desired_outcome_id TEXT NOT NULL,
  title TEXT,
  description TEXT,
  sequence INTEGER NOT NULL,
  target_date TEXT,
  preceding_condition TEXT,
  required_capability TEXT,
  required_evidence TEXT,
  required_partner TEXT,
  decision_gate TEXT,
  dependency_step_id TEXT,
  owner_id TEXT,
  risk TEXT,
  confidence TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_assessments (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  question_key TEXT NOT NULL,
  question_text TEXT,
  answer TEXT,
  rationale TEXT,
  evidence_ids TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  rule_version TEXT,
  recommended_outcome TEXT,
  user_decision TEXT,
  user_notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_results (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  system_recommendation TEXT,
  final_decision TEXT,
  rationale TEXT,
  blocking_conditions TEXT NOT NULL DEFAULT '[]',
  enabling_conditions TEXT NOT NULL DEFAULT '[]',
  required_next_actions TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_definitions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  purpose TEXT,
  applicable_maturity_levels TEXT NOT NULL DEFAULT '[]',
  applicable_complexity_domains TEXT NOT NULL DEFAULT '[]',
  applicable_problem_types TEXT NOT NULL DEFAULT '[]',
  required_inputs TEXT NOT NULL DEFAULT '[]',
  evidence_prerequisites TEXT NOT NULL DEFAULT '[]',
  expected_outputs TEXT NOT NULL DEFAULT '[]',
  time TEXT,
  effort TEXT,
  expertise TEXT,
  delivery_modes TEXT NOT NULL DEFAULT '[]',
  limitations TEXT NOT NULL DEFAULT '[]',
  risks TEXT NOT NULL DEFAULT '[]',
  alternative_tools TEXT NOT NULL DEFAULT '[]',
  next_steps TEXT NOT NULL DEFAULT '[]',
  download_asset TEXT,
  methodology_version TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_recommendations (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  tool_definition_id TEXT,
  reason TEXT,
  trigger_inputs TEXT NOT NULL DEFAULT '{}',
  prerequisites_met INTEGER NOT NULL DEFAULT 0,
  missing_prerequisites TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  limitations TEXT NOT NULL DEFAULT '[]',
  alternative_tool_ids TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  user_decision TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_pathways (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  desired_outcome_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  pathway_type TEXT,
  theory_of_change TEXT,
  response_archetype TEXT,
  related_leverage_point_id TEXT,
  current_maturity TEXT,
  target_maturity TEXT,
  complexity_fit TEXT,
  system_level TEXT,
  primary_driver TEXT,
  required_capabilities TEXT NOT NULL DEFAULT '[]',
  required_partners TEXT NOT NULL DEFAULT '[]',
  resource_estimate TEXT,
  cost_range TEXT,
  time_horizon TEXT,
  expected_benefits TEXT NOT NULL DEFAULT '[]',
  potential_harms TEXT NOT NULL DEFAULT '[]',
  trade_offs TEXT NOT NULL DEFAULT '[]',
  rebound_risks TEXT NOT NULL DEFAULT '[]',
  dependencies TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  generation_method TEXT,
  rationale TEXT,
  status TEXT NOT NULL,
  user_decision TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_options (
  id TEXT PRIMARY KEY,
  intervention_pathway_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  intervention_type TEXT,
  expected_outcome TEXT,
  effort INTEGER,
  cost_range TEXT,
  time_to_learn TEXT,
  time_to_impact TEXT,
  reversibility TEXT,
  implementation_risk INTEGER,
  evidence_strength TEXT,
  stakeholder_acceptability TEXT,
  ecological_alignment TEXT,
  strategic_alignment TEXT,
  capability_fit TEXT,
  dependency_risk TEXT,
  confidence TEXT,
  case_study_reference TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_comparisons (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  option_a_id TEXT,
  option_b_id TEXT,
  comparison_dimensions TEXT NOT NULL DEFAULT '[]',
  advantages TEXT NOT NULL DEFAULT '[]',
  limitations TEXT NOT NULL DEFAULT '[]',
  trade_offs TEXT NOT NULL DEFAULT '[]',
  preferred_option_id TEXT,
  decision_rationale TEXT,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS horizons (
  id TEXT PRIMARY KEY,
  intervention_pathway_id TEXT NOT NULL,
  horizon TEXT NOT NULL,
  title TEXT,
  description TEXT,
  objective TEXT,
  start_date TEXT,
  target_date TEXT,
  required_capabilities TEXT NOT NULL DEFAULT '[]',
  required_evidence TEXT NOT NULL DEFAULT '[]',
  required_partners TEXT NOT NULL DEFAULT '[]',
  owner_id TEXT,
  status TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  confidence TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS horizon_dependencies (
  id TEXT PRIMARY KEY,
  source_horizon_item_id TEXT NOT NULL,
  target_horizon_item_id TEXT NOT NULL,
  relationship_type TEXT,
  rationale TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prototype_plans (
  id TEXT PRIMARY KEY,
  intervention_pathway_id TEXT NOT NULL,
  prototype_type TEXT,
  title TEXT,
  description TEXT,
  purpose TEXT,
  assumption_tested TEXT,
  learning_objective TEXT,
  fidelity TEXT,
  audience TEXT,
  setting TEXT,
  duration TEXT,
  resources_required TEXT NOT NULL DEFAULT '[]',
  ethical_considerations TEXT,
  accessibility_considerations TEXT,
  risk_level TEXT,
  status TEXT NOT NULL,
  user_selected INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_assumptions (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  source_assumption_id TEXT,
  statement TEXT NOT NULL,
  assumption_type TEXT,
  criticality TEXT,
  uncertainty TEXT,
  consequence_if_wrong TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY,
  prototype_plan_id TEXT NOT NULL,
  selected_problem_focus_id TEXT NOT NULL,
  title TEXT,
  hypothesis TEXT,
  learning_objective TEXT,
  method TEXT,
  decision_threshold TEXT,
  start_date TEXT,
  end_date TEXT,
  status TEXT NOT NULL,
  owner TEXT,
  review_date TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_hypotheses (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  assumption_id TEXT,
  hypothesis_statement TEXT,
  expected_observation TEXT,
  falsification_condition TEXT,
  confidence_before TEXT,
  confidence_after TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_metrics (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_category TEXT,
  baseline_value TEXT,
  target_value TEXT,
  measurement_method TEXT,
  data_owner TEXT,
  frequency TEXT,
  confidence TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_risks (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  intervention_pathway_id TEXT,
  experiment_id TEXT,
  risk_category TEXT,
  description TEXT,
  likelihood INTEGER,
  severity INTEGER,
  mitigation TEXT,
  owner TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pathway_ownership (
  id TEXT PRIMARY KEY,
  selected_problem_focus_id TEXT NOT NULL,
  executive_sponsor TEXT,
  pathway_owner TEXT,
  experiment_owner TEXT,
  decision_maker TEXT,
  data_owner TEXT,
  risk_owner TEXT,
  governance_cadence TEXT,
  review_date TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_reviews (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  review_date TEXT,
  result_status TEXT,
  result_summary TEXT,
  evidence_collected TEXT NOT NULL DEFAULT '[]',
  decision TEXT,
  decision_rationale TEXT,
  next_actions TEXT NOT NULL DEFAULT '[]',
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_records (
  id TEXT PRIMARY KEY,
  intervention_state_id TEXT NOT NULL,
  experiment_id TEXT,
  selected_problem_focus_id TEXT,
  learning_type TEXT,
  title TEXT,
  summary TEXT,
  evidence_ids TEXT NOT NULL DEFAULT '[]',
  confidence TEXT,
  affects_stage TEXT,
  recommended_revisit TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_outputs (
  id TEXT PRIMARY KEY,
  intervention_state_id TEXT NOT NULL,
  output_type TEXT,
  title TEXT,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS complete_journey_records (
  id TEXT PRIMARY KEY,
  intervention_state_id TEXT NOT NULL,
  organisation_id TEXT,
  journey_id TEXT,
  journey_summary TEXT NOT NULL,
  learning_loop_status TEXT,
  next_review_date TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intervention_import_records (
  id TEXT PRIMARY KEY,
  intervention_state_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT,
  source_version TEXT,
  imported_payload TEXT NOT NULL,
  imported_count INTEGER NOT NULL DEFAULT 0,
  conflict_count INTEGER NOT NULL DEFAULT 0,
  stale_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


LANDING_CONTENT = {
    "hero": {
        "eyebrow": "Operating System for Sustainability Transformation",
        "heading": "Green Spectrum makes complex sustainability challenges navigable.",
        "body": "A guided platform that helps sustainability leaders understand interconnected challenges, choose appropriate methods, prioritise where change matters and turn decisions into practical experiments.",
    },
    "problemCards": [
        {"title": "Too many competing priorities", "body": "Climate, nature, people, governance, operations, regulation and commercial pressures compete for attention."},
        {"title": "Disconnected evidence", "body": "Reports, operational data, expert knowledge and stakeholder experience are often stored separately."},
        {"title": "Too many tools, too little navigation", "body": "Organisations may know about ESG, LCA, materiality, systems thinking and circular design without knowing how to sequence them."},
        {"title": "Pressure to decide under uncertainty", "body": "Leaders must act before every relationship, impact or consequence can be fully understood."},
    ],
    "processStages": [
        {"key": "explore", "title": "Explore", "subtitle": "Three Empathies", "purpose": "Understand Business, Human and Planetary realities.", "output": "Maturity profile, tensions, evidence gaps and initial problem signals."},
        {"key": "map", "title": "Map", "subtitle": "Impact Journey", "purpose": "Make relationships, impacts and behaviour visible.", "output": "Impact journey, system map, hotspots and opportunity areas."},
        {"key": "structure", "title": "Structure", "subtitle": "Spectrum and Complexity", "purpose": "Classify what kind of challenges the organisation faces.", "output": "Structured challenge portfolio, maturity distribution and complexity profile."},
        {"key": "prioritise", "title": "Prioritise", "subtitle": "Select Focus", "purpose": "Determine which problems deserve attention first.", "output": "Priority portfolio, selection rationale and decision routes."},
        {"key": "decide", "title": "Decide and Experiment", "subtitle": "Intervention Pathways", "purpose": "Choose a response and reduce uncertainty through action.", "output": "Intervention pathways, experiment cards, owners, KPIs and roadmap."},
        {"key": "evolve", "title": "Reflect and Evolve", "subtitle": "Continuous Learning", "purpose": "Use results to improve future decisions.", "output": "Learning record, updated organisational knowledge and next cycle."},
    ],
    "faqs": [
        {"question": "Is Green Spectrum another sustainability framework?", "answer": "No. It connects and sequences existing sustainability, systems, design and strategy methods. Its role is navigation and orchestration."},
        {"question": "Does the platform make decisions for me?", "answer": "No. It organises evidence, highlights uncertainty and suggests routes. The user confirms priorities, decisions and interventions."},
        {"question": "How does Green Spectrum avoid generic advice?", "answer": "Later stages should use the organisation’s context, evidence, maturity, system relationships and previous learning. Generic suggestions must be labelled as examples rather than organisation-specific findings."},
    ],
}


FEATURED_RESOURCES = [
    ("Green Spectrum Playbook", "green-spectrum-playbook", "Complete methodology handbook for the MVP user-testing process.", "Core methodology", "All", "solo,team,facilitation", "PDF", "718 KB", "downloads/green-spectrum-playbook.pdf", "0.1.0"),
    ("Three Empathies Questions 1", "three-empathies-questions-1", "Question set for exploring business, human and planetary realities.", "Three Empathies", "Explore", "solo,team,facilitation", "PDF", "3.7 MB", "downloads/three-empathies-questions-1.pdf", "0.1.0"),
    ("Three Empathies Questions 2", "three-empathies-questions-2", "Additional Three Empathies question set for deeper user-testing sessions.", "Three Empathies", "Explore", "solo,team,facilitation", "PDF", "3.5 MB", "downloads/three-empathies-questions-2.pdf", "0.1.0"),
    ("Impact Journey Mapping Canvas", "impact-journey-mapping-canvas", "Canvas for mapping stages, activities, stakeholders, decisions, impacts and evidence gaps.", "Impact Journey Mapping", "Map", "team,facilitation", "PDF", "237 KB", "downloads/impact-journey-mapping-canvas.pdf", "0.1.0"),
    ("Green Spectrum Canvas", "green-spectrum-canvas", "Canvas for classifying challenges across the Green Spectrum.", "Structure and Prioritise", "Structure", "solo,team,facilitation", "PDF", "1.5 MB", "downloads/green-spectrum-canvas.pdf", "0.1.0"),
    ("Opportunity Mapping Tree", "opportunity-mapping-tree", "Tool for opening up opportunity branches before selecting an intervention route.", "Structure and Prioritise", "Prioritise", "solo,team,facilitation", "PDF", "1.4 MB", "downloads/opportunity-mapping-tree.pdf", "0.1.0"),
    ("Prototype Experiment Card", "prototype-experiment-card", "Template for hypothesis, prototype, measures, owner and review date.", "Experiment and Review Tools", "Decide and Experiment", "solo,team,facilitation", "PDF", "1.7 MB", "downloads/prototype-experiment-card.pdf", "0.1.0"),
    ("Prototyping Wheel", "prototyping-wheel", "Tool for choosing a prototype type for the uncertainty being tested.", "Experiment and Review Tools", "Decide and Experiment", "solo,team,facilitation", "PDF", "1.3 MB", "downloads/prototyping-wheel.pdf", "0.1.0"),
]


def sync_resource_library(db: sqlite3.Connection, methodology_id: str) -> None:
    timestamp = now_iso()
    resource_ids = []
    for title, slug, description, category, stage, use_mode, file_type, file_size, storage_key, version in FEATURED_RESOURCES:
        resource_id = f"resource-{slug}"
        resource_ids.append(resource_id)
        db.execute(
            """
            INSERT INTO resources
            (id, title, slug, description, category, stage, use_mode, file_type, file_size,
             storage_key, preview_image_key, methodology_version_id, licence, version, published_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 'Green Spectrum MVP resource', ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
              title = excluded.title,
              slug = excluded.slug,
              description = excluded.description,
              category = excluded.category,
              stage = excluded.stage,
              use_mode = excluded.use_mode,
              file_type = excluded.file_type,
              file_size = excluded.file_size,
              storage_key = excluded.storage_key,
              methodology_version_id = excluded.methodology_version_id,
              licence = excluded.licence,
              version = excluded.version,
              updated_at = excluded.updated_at,
              active = 1
            """,
            (resource_id, title, slug, description, category, stage, use_mode, file_type, file_size, storage_key, methodology_id, version, timestamp, timestamp),
        )
    db.execute(
        """
        INSERT INTO resource_bundles
        (id, title, description, resource_ids, storage_key, version, generated_at, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(id) DO UPDATE SET
          title = excluded.title,
          description = excluded.description,
          resource_ids = excluded.resource_ids,
          storage_key = excluded.storage_key,
          version = excluded.version,
          generated_at = excluded.generated_at,
          active = 1
        """,
        (
            "bundle-complete-0-1-0",
            "Complete Green Spectrum MVP Resources",
            "All current Green Spectrum playbook, canvas and experiment PDFs for user testing.",
            json.dumps(resource_ids),
            "downloads/green-spectrum-mvp-resources.zip",
            METHODOLOGY_VERSION,
            timestamp,
        ),
    )


def seed_database() -> None:
    with connect() as db:
        db.executescript(SCHEMA)
        ensure_columns(db, "organisations", {
            "confidential_alias": "TEXT",
            "is_confidential": "INTEGER NOT NULL DEFAULT 0",
            "ownership_model": "TEXT",
            "age_band": "TEXT",
            "products_services": "TEXT",
            "business_model": "TEXT",
            "notes": "TEXT",
            "current_profile_version_id": "TEXT",
        })
        ensure_columns(db, "journeys", {
            "purpose_category": "TEXT",
            "purpose_description": "TEXT",
            "urgency_driver": "TEXT",
            "challenge_clarity": "TEXT",
            "scope_type": "TEXT",
            "scope_description": "TEXT",
            "exclusions": "TEXT",
            "timeframe": "TEXT",
        })
        ensure_columns(db, "business_empathy_responses", {
            "discovery_domains": "TEXT NOT NULL DEFAULT '[]'",
            "selected_tools": "TEXT NOT NULL DEFAULT '[]'",
            "stakeholder_suggestions": "TEXT NOT NULL DEFAULT '[]'",
            "reflection": "TEXT NOT NULL DEFAULT '{}'",
            "systems_connections": "TEXT NOT NULL DEFAULT '[]'",
            "carry_forward_actions": "TEXT NOT NULL DEFAULT '[]'",
            "evidence_tasks": "TEXT NOT NULL DEFAULT '[]'",
            "tool_recommendations": "TEXT NOT NULL DEFAULT '[]'",
        })
        ensure_columns(db, "business_empathy_outputs", {
            "discovery_domain_readings": "TEXT NOT NULL DEFAULT '[]'",
            "tool_recommendations": "TEXT NOT NULL DEFAULT '[]'",
            "carry_forward_items": "TEXT NOT NULL DEFAULT '[]'",
            "systems_connections": "TEXT NOT NULL DEFAULT '[]'",
        })
        ensure_columns(db, "human_empathy_responses", {
            "capability_gaps": "TEXT",
            "power_concern": "TEXT",
            "research_task": "TEXT",
            "stakeholder_representation": "TEXT NOT NULL DEFAULT '[]'",
            "discovery_domains": "TEXT NOT NULL DEFAULT '[]'",
            "selected_tools": "TEXT NOT NULL DEFAULT '[]'",
            "evidence_tasks": "TEXT NOT NULL DEFAULT '[]'",
            "systems_connections": "TEXT NOT NULL DEFAULT '[]'",
            "carry_forward_actions": "TEXT NOT NULL DEFAULT '[]'",
            "human_risk_flags": "TEXT NOT NULL DEFAULT '[]'",
            "reflection": "TEXT NOT NULL DEFAULT '{}'",
        })
        existing = db.execute("SELECT id FROM methodology_versions WHERE active = 1").fetchone()
        method_id = existing["id"] if existing else "methodology-green-spectrum-0-1-0"
        if not existing:
            db.execute(
                """
                INSERT INTO methodology_versions
                (id, version, title, description, published_at, active, changelog, content_hash)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    method_id,
                    METHODOLOGY_VERSION,
                    "Green Spectrum Methodology",
                    "Initial digital-platform methodology foundation for the six-stage decision-navigation journey.",
                    now_iso(),
                    "Foundation release for Page 1 backend objects and public content.",
                    "green-spectrum-methodology-0.1.0",
                ),
            )
            db.execute(
                """
                INSERT INTO public_content_blocks
                (id, page_key, section_key, heading, body, structured_content, display_order, status, published_at, version)
                VALUES (?, 'landing', 'page', ?, ?, ?, 1, 'published', ?, ?)
                """,
                (
                    "content-landing-0-1-0",
                    LANDING_CONTENT["hero"]["heading"],
                    LANDING_CONTENT["hero"]["body"],
                    json.dumps(LANDING_CONTENT),
                    now_iso(),
                    METHODOLOGY_VERSION,
                ),
            )
            for title, slug, description, category, stage, use_mode, file_type, file_size, storage_key, version in FEATURED_RESOURCES:
                db.execute(
                    """
                    INSERT INTO resources
                    (id, title, slug, description, category, stage, use_mode, file_type, file_size,
                     storage_key, preview_image_key, methodology_version_id, licence, version, published_at, updated_at, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 'Green Spectrum MVP resource', ?, ?, ?, 1)
                    """,
                    (
                        f"resource-{slug}",
                        title,
                        slug,
                        description,
                        category,
                        stage,
                        use_mode,
                        file_type,
                        file_size,
                        storage_key,
                        method_id,
                        version,
                        now_iso(),
                        now_iso(),
                    ),
                )
            db.execute(
                """
                INSERT INTO resource_bundles
                (id, title, description, resource_ids, storage_key, version, generated_at, active)
                VALUES (?, ?, ?, ?, NULL, ?, ?, 0)
                """,
                (
                    "bundle-complete-0-1-0",
                    "Complete Green Spectrum Components",
                    "Bundle placeholder until downloadable assets are attached.",
                    json.dumps([f"resource-{item[1]}" for item in FEATURED_RESOURCES]),
                    METHODOLOGY_VERSION,
                    now_iso(),
                ),
            )
            for key, enabled in {
                "guest_onboarding": True,
                "resource_bundle_download": False,
                "ai_recommendations": False,
                "external_research": False,
            }.items():
                db.execute(
                    "INSERT INTO feature_flags (id, key, enabled, rules, updated_at) VALUES (?, ?, ?, '{}', ?)",
                    (f"flag-{key}", key, 1 if enabled else 0, now_iso()),
                )
        sync_resource_library(db, method_id)
        seed_impact_categories(db)
        seed_response_archetypes(db)
        seed_tool_definitions(db)


def public_landing() -> dict:
    with connect() as db:
        methodology = db.execute(
            "SELECT version, title, description, published_at FROM methodology_versions WHERE active = 1 LIMIT 1"
        ).fetchone()
        block = db.execute(
            """
            SELECT structured_content, version FROM public_content_blocks
            WHERE page_key = 'landing' AND status = 'published'
            ORDER BY display_order LIMIT 1
            """
        ).fetchone()
    content = json.loads(block["structured_content"]) if block else LANDING_CONTENT
    return {
        "content": content,
        "methodologyVersion": dict(methodology) if methodology else None,
        "privacy": {
            "analyticsRequiresConsent": True,
            "collectsOrganisationDataOnLanding": False,
            "externalResearchOnLanding": False,
        },
    }


def featured_resources() -> dict:
    with connect() as db:
        rows = db.execute(
            """
            SELECT title, slug, description, category, stage, use_mode AS useMode, file_type AS fileType,
                   file_size AS fileSize, storage_key AS storageKey, version
            FROM resources
            WHERE active = 1
            ORDER BY published_at DESC
            LIMIT 8
            """
        ).fetchall()
        bundle = db.execute(
            "SELECT title, description, version, active FROM resource_bundles ORDER BY generated_at DESC LIMIT 1"
        ).fetchone()
    return {
        "resources": [dict(row) for row in rows],
        "bundle": {
            "available": bool(bundle and bundle["active"]),
            "title": bundle["title"] if bundle else "Complete Green Spectrum Components",
            "description": bundle["description"] if bundle else "Bundle not configured yet.",
            "downloadUrl": f"/{bundle['storage_key']}" if bundle and bundle["storage_key"] else "",
            "version": bundle["version"] if bundle else METHODOLOGY_VERSION,
        },
    }


def external_source_catalogue(query: dict[str, list[str]] | None = None) -> dict:
    catalogue_path = DATA_DIR / "external_source_catalogue.json"
    if not catalogue_path.exists():
        return {
            "ok": False,
            "message": "External source catalogue has not been generated yet.",
            "stages": [],
            "sources": [],
            "summary": {"totalSources": 0, "stageCount": 0},
        }
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    sources = list(catalogue.get("sources", []))
    query = query or {}
    stage = (query.get("stage", [""])[0] or "").strip()
    access = (query.get("accessType", [""])[0] or "").strip()
    topic = (query.get("topic", [""])[0] or "").strip()
    search = (query.get("q", [""])[0] or "").strip().lower()
    try:
        limit = max(1, min(250, int(query.get("limit", ["80"])[0] or 80)))
    except ValueError:
        limit = 80
    if stage:
        sources = [item for item in sources if item.get("stageKey") == stage or item.get("appStage") == stage]
    if access:
        sources = [item for item in sources if item.get("accessType") == access]
    if topic:
        sources = [item for item in sources if topic in item.get("topics", [])]
    if search:
        sources = [item for item in sources if search in item.get("name", "").lower() or search in " ".join(item.get("topics", [])).lower()]
    source_counts = {stage_info.get("key"): 0 for stage_info in catalogue.get("stages", [])}
    for item in catalogue.get("sources", []):
        key = item.get("stageKey")
        source_counts[key] = source_counts.get(key, 0) + 1
    stages = []
    for stage_info in catalogue.get("stages", []):
        enriched = dict(stage_info)
        enriched["sourceCount"] = source_counts.get(stage_info.get("key"), enriched.get("sourceCount", 0))
        stages.append(enriched)
    return {
        "ok": True,
        "catalogueVersion": catalogue.get("catalogueVersion"),
        "methodologyVersion": catalogue.get("methodologyVersion"),
        "implementationStatus": catalogue.get("implementationStatus"),
        "purpose": catalogue.get("purpose"),
        "integrationNotes": catalogue.get("integrationNotes", {}),
        "stages": stages,
        "sources": sources[:limit],
        "summary": {
            "totalSources": len(catalogue.get("sources", [])),
            "stageCount": len(stages),
            "returnedSources": min(len(sources), limit),
            "filteredSources": len(sources),
        },
    }


def journey_entry(query: dict[str, list[str]]) -> dict:
    demo_state = query.get("state", ["guest"])[0]
    progress_preview = [
        {"label": "Welcome", "status": "current"},
        {"label": "Onboarding", "status": "next"},
        {"label": "Explore", "status": "future"},
        {"label": "Map", "status": "future"},
        {"label": "Structure and Prioritise", "status": "future"},
        {"label": "Decide and Experiment", "status": "future"},
        {"label": "Reflect and Evolve", "status": "future"},
    ]
    if demo_state == "active":
        return {
            "authenticated": True,
            "activeJourney": True,
            "ctaLabel": "Continue Your Journey",
            "ctaRoute": "/dashboard/",
            "progressPreview": progress_preview,
        }
    if demo_state == "completed":
        return {
            "authenticated": True,
            "activeJourney": False,
            "ctaLabel": "Open Dashboard",
            "ctaRoute": "/dashboard/",
            "progressPreview": progress_preview,
        }
    return {
        "authenticated": False,
        "activeJourney": False,
        "ctaLabel": "Start Your Journey",
        "ctaRoute": "/onboarding/",
        "progressPreview": progress_preview,
    }


SAFE_METADATA_KEYS = {"sectionKey", "ctaLocation", "authenticated", "activeJourney", "resourceCategory", "deviceBreakpoint", "stage", "label", "mode"}


def record_analytics(payload: dict) -> dict:
    event_name = str(payload.get("eventName", ""))[:120]
    if not event_name:
        return {"ok": False, "error": "eventName is required"}
    consent_state = payload.get("consentState") or {}
    analytics_allowed = bool(consent_state.get("analytics"))
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    safe_metadata = {key: metadata[key] for key in SAFE_METADATA_KEYS if key in metadata}
    if not analytics_allowed:
        return {"ok": True, "stored": False, "reason": "analytics_consent_not_granted"}
    with connect() as db:
        db.execute(
            """
            INSERT INTO analytics_events
            (id, anonymous_session_id, user_id, event_name, route, section_key, metadata, occurred_at, consent_state)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)
            """,
            (
                "event-" + secrets.token_hex(12),
                str(payload.get("anonymousSessionId", ""))[:80] or None,
                event_name,
                str(payload.get("route", ""))[:240] or None,
                str(payload.get("sectionKey", ""))[:120] or None,
                json.dumps(safe_metadata),
                now_iso(),
                json.dumps(consent_state),
            ),
        )
    return {"ok": True, "stored": True}


ONBOARDING_SECTION_KEYS = [
    "role",
    "mode",
    "organisation",
    "sector",
    "reason",
    "maturity",
    "stakeholders",
    "evidence",
    "data",
    "constraints",
    "outputs",
]


def section_statuses(form_data: dict) -> dict:
    checks = {
        "role": bool(first_value(form_data, "role")),
        "mode": bool(first_value(form_data, "mode")),
        "organisation": bool(first_value(form_data, "organisationName") and first_value(form_data, "headquarters")),
        "sector": bool(first_value(form_data, "industry")),
        "reason": bool(as_list(form_data.get("reasons"))),
        "maturity": bool(first_value(form_data, "maturity")),
        "stakeholders": bool(as_list(form_data.get("stakeholders")) or first_value(form_data, "decisionOwner")),
        "evidence": bool(as_list(form_data.get("evidence")) or as_list(form_data.get("fileNames"))),
        "data": bool(as_list(form_data.get("dataSources"))),
        "constraints": bool(as_list(form_data.get("priorityDrivers")) or as_list(form_data.get("constraints")) or first_value(form_data, "timeHorizon")),
        "outputs": bool(as_list(form_data.get("outputs"))),
    }
    optional = {"evidence", "data"}
    return {
        key: {
            "status": "Complete" if checks[key] else "Optional" if key in optional else "Not started",
            "completionPercentage": 100 if checks[key] else 0,
            "required": key not in optional,
        }
        for key in ONBOARDING_SECTION_KEYS
    }


def build_context_profile(form_data: dict) -> dict:
    file_names = as_list(form_data.get("fileNames"))
    missing = []
    for label, key in [
        ("organisation name", "organisationName"),
        ("headquarters country", "headquarters"),
        ("primary industry", "industry"),
        ("decision owner", "decisionOwner"),
        ("data quality", "dataQuality"),
    ]:
        if not first_value(form_data, key):
            missing.append(label)
    return {
        "userContext": {
            "role": first_value(form_data, "role", "Not specified"),
            "influence": first_value(form_data, "influence", "Not specified"),
            "department": first_value(form_data, "representing", "Not specified"),
        },
        "organisation": {
            "name": first_value(form_data, "organisationName", "Confidential organisation"),
            "profileType": first_value(form_data, "organisationProfileType", "Create new organisation"),
            "confidentialAlias": first_value(form_data, "confidentialAlias", ""),
            "type": first_value(form_data, "organisationType", "Not specified"),
            "size": first_value(form_data, "size", "Not specified"),
            "ownershipModel": first_value(form_data, "ownershipModel", "Not specified"),
            "ageBand": first_value(form_data, "ageBand", "Not specified"),
            "headquarters": first_value(form_data, "headquarters", "Not specified"),
            "regions": first_value(form_data, "regions", "Not specified"),
            "businessModel": first_value(form_data, "businessModel", "Not specified"),
            "publicContextConsent": bool(first_value(form_data, "publicContextConsent")),
        },
        "journey": {
            "mode": first_value(form_data, "mode", "solo"),
            "reasons": as_list(form_data.get("reasons")),
            "clarity": first_value(form_data, "challengeClarity", "Not sure"),
            "scope": first_value(form_data, "scopeType", "Not specified"),
            "timeframe": first_value(form_data, "timeHorizon", "Multiple horizons"),
        },
        "stakeholders": {
            "groups": as_list(form_data.get("stakeholders")) or as_list(form_data.get("participants")),
            "decisionOwner": first_value(form_data, "decisionOwner", "Not specified"),
            "blocker": first_value(form_data, "progressBlocker", "Not specified"),
            "underrepresented": first_value(form_data, "underrepresented", "Not specified"),
        },
        "evidence": {
            "types": as_list(form_data.get("evidence")),
            "uploadedFileNames": file_names,
            "analysisStatus": "Metadata only. Content has not been analysed.",
        },
        "data": {
            "sources": as_list(form_data.get("dataSources")),
            "access": first_value(form_data, "dataAccess", "Unknown"),
            "quality": first_value(form_data, "dataQuality", "Unknown"),
            "externalResearchAllowed": bool(first_value(form_data, "externalResearchAllowed") or first_value(form_data, "publicContextConsent")),
            "externalResearchCategories": as_list(form_data.get("externalResearchCategories")),
        },
        "initialSignals": {
            "business": as_list(form_data.get("businessSignals")),
            "human": as_list(form_data.get("humanSignals")),
            "planetary": as_list(form_data.get("planetarySignals")),
            "confidence": first_value(form_data, "signalConfidence", "Unknown"),
        },
        "constraints": as_list(form_data.get("constraints")),
        "outputs": as_list(form_data.get("outputs")),
        "missingInformation": missing,
        "sourceStatus": "User supplied",
        "confidence": "Medium" if len(missing) <= 2 else "Low",
    }


def build_recommended_route(form_data: dict) -> dict:
    clarity = first_value(form_data, "challengeClarity", "Not sure")
    mode = first_value(form_data, "mode", "solo")
    industry = first_value(form_data, "industry", "")
    constraints = as_list(form_data.get("constraints"))
    reasons = as_list(form_data.get("reasons"))
    data_sources = as_list(form_data.get("dataSources"))
    begin = "Business Empathy"
    priority_themes = ["governance", "evidence quality", "decision ownership"]
    rationale = ["The organisation context is still forming, so Explore should keep assumptions visible."]
    if "Manufacturing" in industry or first_value(form_data, "valueChain") in {"Manufacturing", "Multiple stages"}:
        priority_themes.extend(["materials", "energy", "supply chain"])
        rationale.append("Manufacturing or value-chain signals suggest material, energy and supply-chain questions should appear early.")
    if any("workforce" in item.lower() or "social" in item.lower() for item in reasons):
        begin = "Human Empathy"
        priority_themes.extend(["skills", "culture", "incentives"])
        rationale.append("The stated purpose includes human or workforce outcomes.")
    if any("Weak data" == item for item in constraints) or not data_sources:
        priority_themes.append("data gaps")
        rationale.append("Data availability is weak or not yet mapped.")
    if mode in {"team", "facilitation"}:
        priority_themes.append("stakeholder alignment")
        rationale.append("The selected journey mode depends on shared interpretation.")
    return {
        "stageKey": "explore",
        "startWith": begin,
        "recommendedSequence": [begin, "Business Empathy", "Human Empathy", "Planetary Empathy"] if begin != "Business Empathy" else ["Business Empathy", "Human Empathy", "Planetary Empathy"],
        "priorityThemes": list(dict.fromkeys(priority_themes)),
        "evidenceTasks": ["Review uploaded document metadata", "Confirm which reports can be used for recommendations", "Carry missing information into Explore"],
        "stakeholderTasks": ["Confirm decision owner", "Identify evidence contributors", "Check underrepresented stakeholders"],
        "estimatedTime": "25-60 minutes",
        "rationale": rationale,
        "confidence": "Medium",
        "userStatus": "suggested",
    }


def save_onboarding_state(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    states = section_statuses(form_data)
    profile = build_context_profile(form_data)
    route = build_recommended_route(form_data)
    with connect() as db:
        row = db.execute("SELECT id, journey_id, organisation_id, created_at FROM onboarding_states WHERE anonymous_session_id = ?", (session_id,)).fetchone()
        state_id = row["id"] if row else "onboarding-" + secrets.token_hex(12)
        created_at = row["created_at"] if row else now_iso()
        if row:
            db.execute(
                """
                UPDATE onboarding_states
                SET form_data = ?, section_states = ?, context_profile = ?, recommended_route = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(form_data), json.dumps(states), json.dumps(profile), json.dumps(route), status, now_iso(), state_id),
            )
        else:
            db.execute(
                """
                INSERT INTO onboarding_states
                (id, anonymous_session_id, form_data, section_states, context_profile, recommended_route, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (state_id, session_id, json.dumps(form_data), json.dumps(states), json.dumps(profile), json.dumps(route), status, created_at, now_iso()),
            )
    return {"ok": True, "stateId": state_id, "sectionStates": states, "contextProfile": profile, "recommendedRoute": route}


def get_onboarding_state(session_id: str) -> dict:
    with connect() as db:
        row = db.execute(
            "SELECT id, form_data, section_states, context_profile, recommended_route, status, updated_at FROM onboarding_states WHERE anonymous_session_id = ?",
            (session_id[:80],),
        ).fetchone()
    if not row:
        return {"ok": True, "found": False}
    return {
        "ok": True,
        "found": True,
        "stateId": row["id"],
        "formData": json.loads(row["form_data"]),
        "sectionStates": json.loads(row["section_states"]),
        "contextProfile": json.loads(row["context_profile"]),
        "recommendedRoute": json.loads(row["recommended_route"]),
        "status": row["status"],
        "updatedAt": row["updated_at"],
    }


def insert_context_fact(db: sqlite3.Connection, organisation_id: str, journey_id: str, fact_type: str, predicate: str, value: object, confidence: str = "Medium") -> str:
    fact_id = "fact-" + secrets.token_hex(12)
    db.execute(
        """
        INSERT INTO context_facts
        (id, organisation_id, journey_id, fact_type, subject_type, subject_id, predicate, value,
         source_type, source_id, confidence, verification_status, valid_from, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'journey', ?, ?, ?, 'user_supplied', NULL, ?, 'user_confirmed', ?, ?, ?)
        """,
        (fact_id, organisation_id, journey_id, fact_type, journey_id, predicate, json.dumps(value), confidence, now_iso(), now_iso(), now_iso()),
    )
    return fact_id


def complete_onboarding(payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    save_result = save_onboarding_state({"anonymousSessionId": session_id, "formData": form_data}, status="completed")
    profile = save_result["contextProfile"]
    route = save_result["recommendedRoute"]
    with connect() as db:
        methodology = db.execute("SELECT id FROM methodology_versions WHERE active = 1 LIMIT 1").fetchone()
        method_id = methodology["id"] if methodology else "methodology-green-spectrum-0-1-0"
        org_name = first_value(form_data, "organisationName", "Confidential organisation")
        organisation_id = "org-" + secrets.token_hex(12)
        journey_id = "journey-" + secrets.token_hex(12)
        profile_version_id = "org-profile-" + secrets.token_hex(12)
        db.execute(
            """
            INSERT INTO organisations
            (id, name, slug, confidential_alias, is_confidential, organisation_type, industry, subsector,
             size_band, headquarters_country, operating_regions, website, products_services, business_model,
             ownership_model, age_band, notes, current_profile_version_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                organisation_id,
                org_name,
                slugify(org_name) + "-" + secrets.token_hex(3),
                first_value(form_data, "confidentialAlias"),
                1 if first_value(form_data, "organisationProfileType") == "Confidential or unnamed organisation" else 0,
                first_value(form_data, "organisationType"),
                first_value(form_data, "industry"),
                first_value(form_data, "subsector"),
                first_value(form_data, "size"),
                first_value(form_data, "headquarters"),
                first_value(form_data, "regions"),
                first_value(form_data, "website"),
                first_value(form_data, "products"),
                first_value(form_data, "businessModel"),
                first_value(form_data, "ownershipModel"),
                first_value(form_data, "ageBand"),
                first_value(form_data, "organisationNotes"),
                profile_version_id,
                now_iso(),
                now_iso(),
            ),
        )
        db.execute(
            "INSERT INTO organisation_profile_versions (id, organisation_id, version, snapshot, change_reason, created_at) VALUES (?, ?, 1, ?, 'Initial onboarding profile', ?)",
            (profile_version_id, organisation_id, json.dumps(profile), now_iso()),
        )
        db.execute(
            """
            INSERT INTO journeys
            (id, organisation_id, title, mode, purpose_category, purpose_description, urgency_driver,
             challenge_clarity, scope_type, scope_description, exclusions, timeframe, status, current_stage,
             methodology_version_id, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 'explore', ?, ?, ?)
            """,
            (
                journey_id,
                organisation_id,
                f"{org_name} Green Spectrum Journey",
                first_value(form_data, "mode", "solo"),
                ", ".join(as_list(form_data.get("reasons"))),
                first_value(form_data, "desiredOutcome"),
                ", ".join(as_list(form_data.get("priorityDrivers"))),
                first_value(form_data, "challengeClarity"),
                first_value(form_data, "scopeType"),
                first_value(form_data, "scopeDescription"),
                first_value(form_data, "scopeExclusions"),
                first_value(form_data, "timeHorizon"),
                method_id,
                now_iso(),
                now_iso(),
            ),
        )
        progress = [
            ("welcome", "complete", 100),
            ("onboarding", "complete", 100),
            ("explore", "next", 0),
            ("map", "future", 0),
            ("structure-prioritise", "future", 0),
            ("decide-experiment", "future", 0),
            ("reflect-evolve", "future", 0),
        ]
        for stage, stage_status, completion in progress:
            db.execute(
                """
                INSERT INTO journey_progress
                (id, journey_id, stage_key, status, completion_percentage, completed_at, last_visited_at, output_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("progress-" + secrets.token_hex(12), journey_id, stage, stage_status, completion, now_iso() if completion == 100 else None, now_iso(), json.dumps(profile if stage == "onboarding" else {})),
            )
        db.execute(
            "INSERT INTO user_contexts (id, anonymous_session_id, professional_role, department, influence_level, personal_objective, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("user-context-" + secrets.token_hex(12), session_id, first_value(form_data, "role"), first_value(form_data, "representing"), first_value(form_data, "influence"), first_value(form_data, "personalObjective"), now_iso(), now_iso()),
        )
        db.execute(
            "INSERT INTO industry_classifications (id, organisation_id, taxonomy_version, primary_industry_name, subsector_name, value_chain_positions, operating_characteristics, created_at, updated_at) VALUES (?, ?, 'green-spectrum-industry-v1', ?, ?, ?, ?, ?, ?)",
            ("industry-" + secrets.token_hex(12), organisation_id, first_value(form_data, "industry"), first_value(form_data, "subsector"), first_value(form_data, "valueChain"), json.dumps(as_list(form_data.get("sectorCharacteristics"))), now_iso(), now_iso()),
        )
        db.execute(
            "INSERT INTO journey_participant_plans (id, journey_id, expected_participant_count, functions, planned_workshop_date, planned_session_length, location_type, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("participant-plan-" + secrets.token_hex(12), journey_id, first_value(form_data, "participantCount"), json.dumps(as_list(form_data.get("participants"))), first_value(form_data, "workshopDate"), first_value(form_data, "sessionLength"), first_value(form_data, "locationType"), first_value(form_data, "workshopNotes")),
        )
        for group in as_list(form_data.get("stakeholders")) + as_list(form_data.get("participants")):
            stakeholder_id = "stakeholder-" + secrets.token_hex(12)
            db.execute(
                "INSERT INTO stakeholders (id, organisation_id, name, stakeholder_type, internal_external, description, created_at, updated_at) VALUES (?, ?, ?, 'group', ?, '', ?, ?)",
                (stakeholder_id, organisation_id, group, "external" if group in {"Suppliers", "Customers", "Investors", "Regulators", "Communities", "NGOs", "External experts"} else "internal", now_iso(), now_iso()),
            )
            db.execute(
                "INSERT INTO journey_stakeholders (id, journey_id, stakeholder_id, role_in_journey, influence_level, source_type, confidence, confirmed_by_user, notes) VALUES (?, ?, ?, 'context contributor', 'Unknown', 'user_supplied', 'Medium', 1, ?)",
                ("journey-stakeholder-" + secrets.token_hex(12), journey_id, stakeholder_id, first_value(form_data, "stakeholderNotes")),
            )
        for file_name in as_list(form_data.get("fileNames")):
            evidence_id = "evidence-" + secrets.token_hex(12)
            db.execute(
                """
                INSERT INTO evidence_documents
                (id, organisation_id, journey_id, title, original_file_name, upload_status, processing_status,
                 analysis_permission, recommendation_permission, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'metadata_only', 'not_analysed', ?, ?, ?, ?)
                """,
                (evidence_id, organisation_id, journey_id, file_name, file_name, 1 if first_value(form_data, "analysisPermission") else 0, 1 if first_value(form_data, "recommendationPermission") else 0, now_iso(), now_iso()),
            )
            if first_value(form_data, "analysisPermission"):
                db.execute(
                    "INSERT INTO document_processing_jobs (id, evidence_document_id, job_type, status, progress, processor_version) VALUES (?, ?, 'metadata_review', 'queued', 0, 'prototype-metadata-only-v1')",
                    ("doc-job-" + secrets.token_hex(12), evidence_id),
                )
        for source in as_list(form_data.get("dataSources")):
            db.execute(
                "INSERT INTO data_sources (id, organisation_id, name, category, availability, quality, format, source_type, notes, created_at, updated_at) VALUES (?, ?, ?, 'onboarding', ?, ?, ?, 'user_supplied', ?, ?, ?)",
                ("data-source-" + secrets.token_hex(12), organisation_id, source, first_value(form_data, "dataAccess"), first_value(form_data, "dataQuality"), first_value(form_data, "dataFormat"), first_value(form_data, "dataNotes"), now_iso(), now_iso()),
            )
        for empathy in ("business", "human", "planetary"):
            for signal in as_list(form_data.get(f"{empathy}Signals")):
                db.execute(
                    "INSERT INTO initial_signals (id, journey_id, empathy_type, signal_type, title, confidence, source_type, created_at, updated_at) VALUES (?, ?, ?, 'concern', ?, ?, 'user_supplied', ?, ?)",
                    ("signal-" + secrets.token_hex(12), journey_id, empathy, signal, first_value(form_data, "signalConfidence", "Unknown"), now_iso(), now_iso()),
                )
        external_categories = as_list(form_data.get("externalResearchCategories"))
        external_allowed = bool(first_value(form_data, "externalResearchAllowed") or first_value(form_data, "publicContextConsent"))
        db.execute(
            """
            INSERT INTO external_research_preferences
            (id, journey_id, allowed, categories, allowed_domains, require_user_review, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            ("external-pref-" + secrets.token_hex(12), journey_id, 1 if external_allowed else 0, json.dumps(external_categories), first_value(form_data, "allowedDomains"), now_iso(), now_iso()),
        )
        if external_allowed:
            for category in external_categories or ["Public organisation context"]:
                db.execute(
                    """
                    INSERT INTO research_tasks
                    (id, journey_id, category, query_definition, jurisdiction, status, created_by, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, 'queued_for_later', 'onboarding', ?, ?)
                    """,
                    (
                        "research-task-" + secrets.token_hex(12),
                        journey_id,
                        category,
                        json.dumps({"organisation": org_name, "industry": first_value(form_data, "industry"), "allowedDomains": first_value(form_data, "allowedDomains")}),
                        first_value(form_data, "headquarters"),
                        now_iso(),
                        (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                    ),
                )
        for constraint in as_list(form_data.get("constraints")):
            db.execute(
                "INSERT INTO journey_constraints (id, journey_id, category, description, severity, owner, evidence, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("constraint-" + secrets.token_hex(12), journey_id, constraint, first_value(form_data, "nonNegotiables"), first_value(form_data, "constraintSeverity"), first_value(form_data, "constraintOwner"), first_value(form_data, "constraintEvidence"), "Medium", now_iso(), now_iso()),
            )
        db.execute(
            "INSERT INTO readiness_profiles (id, journey_id, leadership_readiness, resource_readiness, data_readiness, cultural_readiness, change_speed, notes, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'User estimate', ?, ?)",
            ("readiness-" + secrets.token_hex(12), journey_id, first_value(form_data, "leadershipReadiness"), first_value(form_data, "resourceReadiness"), first_value(form_data, "dataReadiness"), first_value(form_data, "culturalReadiness"), first_value(form_data, "changeSpeed"), first_value(form_data, "readinessNotes"), now_iso(), now_iso()),
        )
        db.execute(
            "INSERT INTO provisional_maturity_orientations (id, journey_id, level, strongest_area, weakest_area, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'User estimate', 1, ?, ?)",
            ("maturity-" + secrets.token_hex(12), journey_id, first_value(form_data, "maturity"), first_value(form_data, "strongestArea"), first_value(form_data, "difficultArea"), now_iso(), now_iso()),
        )
        db.execute(
            "INSERT INTO output_preferences (id, journey_id, output_types, primary_audience, detail_level, preferred_formats, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("output-pref-" + secrets.token_hex(12), journey_id, json.dumps(as_list(form_data.get("outputs"))), first_value(form_data, "audience"), first_value(form_data, "detailLevel"), json.dumps(as_list(form_data.get("preferredFormats"))), now_iso(), now_iso()),
        )
        fact_ids = [
            insert_context_fact(db, organisation_id, journey_id, "organisation_attribute", "organisation_profile", profile["organisation"]),
            insert_context_fact(db, organisation_id, journey_id, "journey_attribute", "journey_purpose", profile["journey"]),
            insert_context_fact(db, organisation_id, journey_id, "evidence_inventory", "available_evidence", profile["evidence"]),
            insert_context_fact(db, organisation_id, journey_id, "stakeholder_context", "stakeholders", profile["stakeholders"]),
        ]
        db.execute(
            "INSERT INTO context_insights (id, journey_id, insight_type, title, description, supporting_fact_ids, confidence, generated_by, generator_version, status, created_at, updated_at) VALUES (?, ?, 'starting_insight', ?, ?, ?, ?, 'rules', 'onboarding-route-v1', 'active', ?, ?)",
            ("insight-" + secrets.token_hex(12), journey_id, "Recommended Explore starting point", "Green Spectrum has created a starting context profile and route. The recommendation is based only on user-supplied onboarding answers.", json.dumps(fact_ids), route["confidence"], now_iso(), now_iso()),
        )
        db.execute(
            "INSERT INTO recommended_routes (id, journey_id, stage_key, recommended_sequence, priority_themes, evidence_tasks, stakeholder_tasks, rationale, supporting_fact_ids, confidence, user_status, created_at, updated_at) VALUES (?, ?, 'explore', ?, ?, ?, ?, ?, ?, ?, 'suggested', ?, ?)",
            ("route-" + secrets.token_hex(12), journey_id, json.dumps(route["recommendedSequence"]), json.dumps(route["priorityThemes"]), json.dumps(route["evidenceTasks"]), json.dumps(route["stakeholderTasks"]), json.dumps(route["rationale"]), json.dumps(fact_ids), route["confidence"], now_iso(), now_iso()),
        )
        db.execute(
            "UPDATE onboarding_states SET journey_id = ?, organisation_id = ?, status = 'completed', updated_at = ? WHERE anonymous_session_id = ?",
            (journey_id, organisation_id, now_iso(), session_id),
        )
        db.execute(
            "INSERT INTO audit_logs (id, actor_type, actor_id, action, entity_type, entity_id, metadata, occurred_at) VALUES (?, 'anonymous_session', ?, 'complete_onboarding', 'journey', ?, ?, ?)",
            ("audit-" + secrets.token_hex(12), session_id, journey_id, json.dumps({"organisationId": organisation_id}), now_iso()),
        )
    return {"ok": True, "organisationId": organisation_id, "journeyId": journey_id, "contextProfile": profile, "recommendedRoute": route, "nextRoute": "/explore/"}


MATURITY_SCORES = {"white": 0, "light": 1, "mid": 2, "dark": 3}
CONFIDENCE_SCORES = {"high": 1.0, "medium": 0.72, "low": 0.42, "assumption": 0.2, "not_assessed": 0.0, "": 0.0}

CAPABILITY_MAP = {
    "Strategy and Purpose": ["Strategy", "Purpose"],
    "Governance and Leadership": ["Governance", "Leadership"],
    "Culture and Engagement": ["Culture", "People", "Skills"],
    "Materiality and Risk": ["Risk", "Strategy"],
    "Transparency and Accountability": ["Reporting", "Governance"],
    "Metrics and Impact": ["Reporting", "Data"],
    "Product and Service Innovation": ["Innovation", "Customer"],
    "Operations and Circularity": ["Operations", "Supply Chain", "Circularity"],
    "Finance and Investment": ["Finance"],
    "Data and Digital": ["Data", "Technology"],
    "Policy and Regulation": ["Policy"],
    "Collaboration and Partnerships": ["Collaboration"],
    "Innovation and R&D Alignment": ["Innovation"],
    "Learning and Adaptation": ["Learning", "Skills"],
    "Crisis Readiness and Resilience": ["Resilience", "Risk"],
    "Regenerative Business Identity": ["Purpose", "Strategy"],
    "Stakeholder Engagement": ["Stakeholder Engagement", "Governance", "Collaboration"],
    "Behavioural Change and Incentives": ["People", "Skills", "Leadership"],
    "Customer Engagement": ["Customer", "Innovation", "Trust"],
    "Human and Community Wellbeing": ["People", "Community", "Resilience"],
    "Equity, Justice and Inclusion": ["Justice", "Inclusion", "Governance"],
    "Ecosystem Stewardship": ["Ecosystems", "Nature", "Resilience"],
    "Value Chain and Traceability": ["Supply Chain", "Traceability", "Risk"],
    "Circular Design and Materials": ["Circularity", "Materials", "Innovation"],
    "Climate and Biodiversity Integration": ["Climate", "Biodiversity", "Resilience"],
}


def maturity_label(value: str) -> str:
    return {"white": "White", "light": "Light Green", "mid": "Mid Green", "dark": "Dark Green", "unknown": "Not Known"}.get(value or "", "Unanswered")


def evidence_weight(evidence: str, confidence: str) -> str:
    text = (evidence or "").lower()
    if any(term in text for term in ["audit", "assurance", "board approved", "external"]):
        return "high"
    if any(term in text for term in ["policy", "workshop", "interview", "report", "dashboard", "website"]):
        return "medium"
    if confidence in {"assumption", "low"}:
        return "low"
    if confidence in {"not_assessed", ""}:
        return "zero"
    return "medium"


def intelligence_model(form_data: dict, outputs: dict | None = None, session_id: str = "anonymous-local", journey_id: str | None = None) -> dict:
    responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
    business = []
    for key, value in responses.items():
        if isinstance(value, dict) and value.get("empathy") in {"business", "human", "planetary"}:
            maturity = value.get("maturity", "")
            confidence = value.get("confidence", "")
            business.append({**value, "key": key, "score": MATURITY_SCORES.get(maturity), "confidenceScore": CONFIDENCE_SCORES.get(confidence, 0.0)})

    organisation_title = form_data.get("organisationName") or "Organisation"
    nodes = [{
        "id": f"node-{session_id}-organisation",
        "type": "Organisation",
        "title": organisation_title,
        "description": "Root organisation node for the Explore and Map knowledge graph.",
        "source": "Business Empathy",
        "confidence": "medium",
        "status": "active",
        "version": "intelligence-v1",
    }]
    relationships = []
    capability_buckets: dict[str, list[dict]] = {}
    uncertainty = {"unknownInformation": [], "assumptions": [], "missingEvidence": [], "lowConfidence": [], "conflictingEvidence": []}

    for item in business:
        qid = item.get("id")
        area = str(item.get("area") or f"Question {qid}")
        node_id = f"node-{session_id}-q{qid}"
        evidence = str(item.get("evidence") or "")
        confidence = str(item.get("confidence") or "not_assessed")
        nodes.append({
            "id": node_id,
            "type": "Answer",
            "title": area,
            "description": f"{area} is marked {maturity_label(item.get('maturity', ''))} with {confidence or 'unknown'} confidence.",
            "source": f"{str(item.get('empathy') or 'business').title()} question {qid}",
            "confidence": confidence or "not_assessed",
            "status": "active",
            "version": "intelligence-v1",
        })
        relationships.append({
            "id": f"rel-{session_id}-org-q{qid}",
            "sourceNodeId": f"node-{session_id}-organisation",
            "targetNodeId": node_id,
            "type": "contains",
            "evidence": evidence or "User assessment response",
            "confidence": confidence or "not_assessed",
            "direction": "organisation_to_answer",
        })
        if evidence:
            evidence_node_id = f"node-{session_id}-evidence-q{qid}"
            nodes.append({
                "id": evidence_node_id,
                "type": "Evidence",
                "title": evidence[:80],
                "description": f"Evidence reference for {area}. Weight: {evidence_weight(evidence, confidence)}.",
                "source": f"{str(item.get('empathy') or 'business').title()} question {qid}",
                "confidence": evidence_weight(evidence, confidence),
                "status": "active",
                "version": "intelligence-v1",
            })
            relationships.append({
                "id": f"rel-{session_id}-q{qid}-evidence",
                "sourceNodeId": node_id,
                "targetNodeId": evidence_node_id,
                "type": "supported by",
                "evidence": evidence,
                "confidence": evidence_weight(evidence, confidence),
                "direction": "answer_to_evidence",
            })
        for capability in CAPABILITY_MAP.get(area, [area]):
            capability_buckets.setdefault(capability, []).append(item)
            cap_node_id = f"node-{session_id}-capability-{slugify(capability)}"
            relationships.append({
                "id": f"rel-{session_id}-q{qid}-capability-{slugify(capability)}",
                "sourceNodeId": node_id,
                "targetNodeId": cap_node_id,
                "type": "influences",
                "evidence": area,
                "confidence": confidence or "not_assessed",
                "direction": "answer_to_capability",
            })
        for connection in as_list(item.get("systemsConnections")):
            rel_id = f"rel-{session_id}-q{qid}-system-{slugify(connection)}"
            relationships.append({
                "id": rel_id,
                "sourceNodeId": node_id,
                "targetNodeId": f"node-{session_id}-system-{slugify(connection)}",
                "type": "connects to",
                "evidence": area,
                "confidence": confidence or "not_assessed",
                "direction": "answer_to_system",
            })
        if item.get("maturity") == "unknown":
            uncertainty["unknownInformation"].append(area)
        if confidence == "assumption":
            uncertainty["assumptions"].append(area)
        if not evidence:
            uncertainty["missingEvidence"].append(area)
        if confidence in {"low", "assumption", "not_assessed", ""}:
            uncertainty["lowConfidence"].append(area)

    capabilities = []
    for capability, items in capability_buckets.items():
        scores = [item.get("score") for item in items if item.get("score") is not None]
        avg = round(sum(scores) / len(scores), 2) if scores else None
        current = "unknown" if avg is None else "white" if avg < 0.75 else "light" if avg < 1.5 else "mid" if avg < 2.4 else "dark"
        capabilities.append({
            "capability": capability,
            "currentMaturity": current,
            "maturityScore": avg,
            "confidence": "high" if all(item.get("confidence") == "high" for item in items) and items else "medium" if any(item.get("confidence") in {"high", "medium"} for item in items) else "low",
            "supportingEvidence": [item.get("evidence") for item in items if item.get("evidence")],
            "knownStrengths": [item.get("area") for item in items if item.get("maturity") in {"mid", "dark"}],
            "knownWeaknesses": [item.get("area") for item in items if item.get("maturity") in {"white", "light"}],
            "unknowns": [item.get("area") for item in items if item.get("maturity") == "unknown" or not item.get("evidence")],
        })

    themes = detect_themes(business)
    patterns = detect_patterns(business)
    insights = build_insights(business, themes, patterns)
    later_pages = {
        "impactJourneyMapping": {
            "journeyNodes": [item.get("area") for item in business if item.get("maturity") in {"white", "light", "unknown"}][:8],
            "likelyHotspots": (outputs or {}).get("weakAreas", [])[:6],
            "likelyStakeholders": sorted({stakeholder for item in business for stakeholder in as_list(item.get("stakeholderSuggestions"))})[:10],
            "likelyLeveragePoints": [item.get("area") for item in business if "impact_journey" in as_list(item.get("carryForwardActions"))][:6],
        },
        "sortAndPrioritise": {
            "problemSignals": (outputs or {}).get("problemSignals", [])[:8],
            "confidence": (outputs or {}).get("evidenceWeightedConfidence", 0),
            "strategicImportance": [item.get("area") for item in business if "Strategically important" in as_list(item.get("flags"))],
        },
        "prototypeInterventions": {
            "potentialChallengeStatements": [f"How might we improve {item.get('area', '').lower()} with better evidence and ownership?" for item in business if item.get("maturity") in {"white", "light", "unknown"}][:6],
        },
    }
    return {
        "graph": {"nodes": nodes, "relationships": relationships},
        "capabilities": capabilities,
        "themes": themes,
        "patterns": patterns,
        "insights": insights,
        "uncertainty": uncertainty,
        "latestInsight": insights[0] if insights else None,
        "latestContradiction": ((outputs or {}).get("contradictions") or [None])[0],
        "latestRelationship": relationships[-1] if relationships else None,
        "laterPages": later_pages,
        "updatedAt": now_iso(),
    }


def detect_themes(business: list[dict]) -> list[dict]:
    theme_rules = [
        ("Governance", "Ownership Gap", ["Governance and Leadership", "Culture and Engagement", "Collaboration and Partnerships"]),
        ("Data", "Data Capability Gap", ["Metrics and Impact", "Data and Digital", "Transparency and Accountability"]),
        ("Finance", "Financial Alignment Gap", ["Finance and Investment", "Strategy and Purpose", "Innovation and R&D Alignment"]),
        ("Operations", "Operational Implementation Gap", ["Operations and Circularity", "Materiality and Risk", "Product and Service Innovation"]),
        ("Resilience", "Resilience Readiness Gap", ["Crisis Readiness and Resilience", "Policy and Regulation", "Materiality and Risk"]),
    ]
    by_area = {item.get("area"): item for item in business}
    themes = []
    for theme_type, title, areas in theme_rules:
        supporting = [by_area[area] for area in areas if by_area.get(area) and (by_area[area].get("maturity") in {"white", "light", "unknown"} or by_area[area].get("confidence") in {"low", "assumption", "not_assessed", ""})]
        if len(supporting) >= 2:
            themes.append({
                "type": theme_type,
                "title": title,
                "description": f"{len(supporting)} related Business answers suggest a repeated {theme_type.lower()} pattern.",
                "supportingQuestions": [item.get("id") for item in supporting],
                "confidence": "medium" if len(supporting) > 2 else "low",
                "status": "suggested",
            })
    return themes


def detect_patterns(business: list[dict]) -> list[dict]:
    by_area = {item.get("area"): item.get("maturity") for item in business}
    patterns = []
    def add_if(title: str, explanation: str, areas: list[str], condition: bool) -> None:
        if condition:
            patterns.append({"title": title, "explanation": explanation, "supportingQuestions": [item.get("id") for item in business if item.get("area") in areas], "confidence": "medium"})
    add_if("Strong strategy, weak finance", "Strategic ambition appears stronger than the financial mechanisms needed for implementation.", ["Strategy and Purpose", "Finance and Investment"], by_area.get("Strategy and Purpose") in {"mid", "dark"} and by_area.get("Finance and Investment") in {"white", "light", "unknown"})
    add_if("Good reporting, weak implementation", "Transparency or metrics appear more mature than operational sustainability.", ["Transparency and Accountability", "Metrics and Impact", "Operations and Circularity"], (by_area.get("Transparency and Accountability") in {"mid", "dark"} or by_area.get("Metrics and Impact") in {"mid", "dark"}) and by_area.get("Operations and Circularity") in {"white", "light", "unknown"})
    add_if("High confidence, little evidence", "Some answers are confident but lack explicit evidence references.", [item.get("area") for item in business if item.get("confidence") in {"high", "medium"} and not item.get("evidence")], any(item.get("confidence") in {"high", "medium"} and not item.get("evidence") for item in business))
    return patterns


def build_insights(business: list[dict], themes: list[dict], patterns: list[dict]) -> list[dict]:
    insights = []
    if patterns:
        first = patterns[0]
        insights.append({
            "title": first["title"],
            "explanation": first["explanation"],
            "supportingQuestions": first["supportingQuestions"],
            "supportingThemes": [theme["title"] for theme in themes[:3]],
            "supportingRelationships": [],
            "supportingEvidence": [item.get("evidence") for item in business if item.get("id") in first["supportingQuestions"] and item.get("evidence")],
            "confidence": first["confidence"],
            "editable": True,
        })
    weak = [item for item in business if item.get("maturity") in {"white", "light", "unknown"}]
    if weak:
        insights.append({
            "title": "Emerging Business hotspot",
            "explanation": f"{weak[0].get('area')} is an early hotspot that may need journey mapping before solutions are selected.",
            "supportingQuestions": [weak[0].get("id")],
            "supportingThemes": [theme["title"] for theme in themes[:2]],
            "supportingRelationships": [],
            "supportingEvidence": [weak[0].get("evidence")] if weak[0].get("evidence") else [],
            "confidence": weak[0].get("confidence") or "low",
            "editable": True,
        })
    return insights


def persist_intelligence(db: sqlite3.Connection, session_id: str, journey_id: str | None, model: dict) -> None:
    timestamp = now_iso()
    graph = model.get("graph", {})
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        db.execute(
            """
            INSERT OR REPLACE INTO organisation_nodes
            (id, anonymous_session_id, journey_id, node_type, title, description, source, confidence, status,
             version, created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'rules', 'rules', COALESCE((SELECT created_at FROM organisation_nodes WHERE id = ?), ?), ?)
            """,
            (
                str(node.get("id")),
                session_id,
                journey_id,
                str(node.get("type") or "Unknown"),
                str(node.get("title") or "Untitled"),
                str(node.get("description") or ""),
                str(node.get("source") or "Business Empathy"),
                str(node.get("confidence") or "low"),
                str(node.get("status") or "active"),
                str(node.get("version") or "intelligence-v1"),
                str(node.get("id")),
                timestamp,
                timestamp,
            ),
        )
    for relationship in graph.get("relationships", []):
        if not isinstance(relationship, dict):
            continue
        db.execute(
            """
            INSERT OR REPLACE INTO organisation_relationships
            (id, anonymous_session_id, journey_id, source_node_id, target_node_id, relationship_type,
             evidence, confidence, direction, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'intelligence-v1',
                    COALESCE((SELECT created_at FROM organisation_relationships WHERE id = ?), ?), ?)
            """,
            (
                str(relationship.get("id")),
                session_id,
                journey_id,
                str(relationship.get("sourceNodeId") or ""),
                str(relationship.get("targetNodeId") or ""),
                str(relationship.get("type") or "relates to"),
                str(relationship.get("evidence") or ""),
                str(relationship.get("confidence") or "low"),
                str(relationship.get("direction") or "directed"),
                str(relationship.get("id")),
                timestamp,
                timestamp,
            ),
        )
    for capability in model.get("capabilities", []):
        if not isinstance(capability, dict):
            continue
        cap_id = f"capability-{session_id}-{slugify(str(capability.get('capability') or 'unknown'))}"
        db.execute(
            """
            INSERT OR REPLACE INTO capability_profiles
            (id, anonymous_session_id, journey_id, capability, current_maturity, maturity_score, confidence,
             supporting_evidence, strengths, weaknesses, unknowns, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cap_id,
                session_id,
                journey_id,
                str(capability.get("capability") or ""),
                str(capability.get("currentMaturity") or ""),
                capability.get("maturityScore"),
                str(capability.get("confidence") or "low"),
                json.dumps(as_list(capability.get("supportingEvidence"))),
                json.dumps(as_list(capability.get("knownStrengths"))),
                json.dumps(as_list(capability.get("knownWeaknesses"))),
                json.dumps(as_list(capability.get("unknowns"))),
                timestamp,
            ),
        )
    for theme in model.get("themes", []):
        if not isinstance(theme, dict):
            continue
        theme_id = f"theme-{session_id}-{slugify(str(theme.get('title') or 'theme'))}"
        db.execute(
            """
            INSERT OR REPLACE INTO intelligence_themes
            (id, anonymous_session_id, journey_id, theme_type, title, description, supporting_questions, confidence, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (theme_id, session_id, journey_id, str(theme.get("type") or ""), str(theme.get("title") or ""), str(theme.get("description") or ""), json.dumps(as_list(theme.get("supportingQuestions"))), str(theme.get("confidence") or "low"), str(theme.get("status") or "suggested"), timestamp),
        )
    for pattern in model.get("patterns", []):
        if not isinstance(pattern, dict):
            continue
        pattern_id = f"pattern-{session_id}-{slugify(str(pattern.get('title') or 'pattern'))}"
        db.execute(
            """
            INSERT OR REPLACE INTO intelligence_patterns
            (id, anonymous_session_id, journey_id, title, explanation, supporting_questions, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pattern_id, session_id, journey_id, str(pattern.get("title") or ""), str(pattern.get("explanation") or ""), json.dumps(as_list(pattern.get("supportingQuestions"))), str(pattern.get("confidence") or "low"), timestamp),
        )
    for insight in model.get("insights", []):
        if not isinstance(insight, dict):
            continue
        insight_id = f"insight-{session_id}-{slugify(str(insight.get('title') or 'insight'))}"
        db.execute(
            """
            INSERT OR REPLACE INTO intelligence_insights
            (id, anonymous_session_id, journey_id, title, explanation, supporting_evidence, supporting_questions,
             supporting_themes, supporting_relationships, confidence, editable, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', ?)
            """,
            (
                insight_id,
                session_id,
                journey_id,
                str(insight.get("title") or ""),
                str(insight.get("explanation") or ""),
                json.dumps(as_list(insight.get("supportingEvidence"))),
                json.dumps(as_list(insight.get("supportingQuestions"))),
                json.dumps(as_list(insight.get("supportingThemes"))),
                json.dumps(as_list(insight.get("supportingRelationships"))),
                str(insight.get("confidence") or "low"),
                timestamp,
            ),
        )
    db.execute(
        """
        INSERT OR REPLACE INTO journey_memory
        (id, anonymous_session_id, journey_id, memory_type, title, payload, updated_at)
        VALUES (?, ?, ?, 'organisational_intelligence', 'Latest Business Empathy intelligence model', ?, ?)
        """,
        (f"memory-{session_id}-business-intelligence", session_id, journey_id, json.dumps(model), timestamp),
    )


def update_intelligence(payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    journey_id = str(payload.get("journeyId", "")) or None
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    outputs = business_outputs(form_data)
    model = intelligence_model(form_data, outputs, session_id, journey_id)
    with connect() as db:
        persist_intelligence(db, session_id, journey_id, model)
    return {"ok": True, "intelligence": model}


def get_intelligence(session_id: str) -> dict:
    session_id = session_id[:80] or "anonymous-local"
    with connect() as db:
        row = db.execute(
            "SELECT payload, updated_at FROM journey_memory WHERE id = ?",
            (f"memory-{session_id}-business-intelligence",),
        ).fetchone()
    if not row:
        return {"ok": True, "found": False}
    return {"ok": True, "found": True, "intelligence": json.loads(row["payload"]), "updatedAt": row["updated_at"]}


def business_outputs(form_data: dict) -> dict:
    responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
    business = []
    for key, value in responses.items():
        if not isinstance(value, dict) or value.get("empathy") not in {"business", "human"}:
            continue
        maturity = value.get("maturity", "")
        confidence = value.get("confidence", "")
        score = MATURITY_SCORES.get(maturity)
        confidence_score = CONFIDENCE_SCORES.get(confidence, 0.0)
        business.append({**value, "key": key, "score": score, "confidenceScore": confidence_score})
    scored = [item for item in business if item["score"] is not None]
    score = round(sum(item["score"] for item in scored) / len(scored), 2) if scored else None
    weighted = round(sum(item["confidenceScore"] for item in business) / len(business), 2) if business else 0
    strengths = [item["area"] for item in business if item.get("maturity") in {"mid", "dark"}]
    weak = [item["area"] for item in business if item.get("maturity") in {"white", "light"}]
    gaps = [item["area"] for item in business if item.get("maturity") == "unknown" or item.get("confidence") in {"low", "assumption", "not_assessed", ""}]
    discovery_domains: dict[str, list[dict]] = {}
    tool_recommendations = []
    carry_forward_items = []
    systems_connections: dict[str, int] = {}
    for item in business:
        for domain in as_list(item.get("discoveryDomains")):
            discovery_domains.setdefault(domain, []).append(item)
        selected_tools = set(as_list(item.get("selectedTools")))
        for tool in item.get("toolRecommendations") if isinstance(item.get("toolRecommendations"), list) else []:
            if isinstance(tool, dict):
                tool_recommendations.append({**tool, "status": "saved" if tool.get("tool") in selected_tools else "recommended"})
        for action in as_list(item.get("carryForwardActions")):
            carry_forward_items.append({
                "action": action,
                "questionId": item.get("id"),
                "area": item.get("area"),
                "maturity": item.get("maturity"),
                "confidence": item.get("confidence"),
                "note": item.get("reflection", {}).get("later", "") if isinstance(item.get("reflection"), dict) else "",
            })
        for connection in as_list(item.get("systemsConnections")):
            systems_connections[connection] = systems_connections.get(connection, 0) + 1
    domain_readings = []
    for domain, items in discovery_domains.items():
        domain_scores = [entry.get("score") for entry in items if entry.get("score") is not None]
        domain_readings.append({
            "domain": domain,
            "questions": [entry.get("id") for entry in items],
            "averageScore": round(sum(domain_scores) / len(domain_scores), 2) if domain_scores else None,
            "evidenceGaps": [entry.get("area") for entry in items if entry.get("maturity") == "unknown" or entry.get("confidence") in {"low", "assumption", "not_assessed", ""}],
        })
    contradictions = []
    by_area = {item.get("area"): item.get("maturity") for item in business}
    if by_area.get("Governance and Leadership") in {"mid", "dark"} and by_area.get("Operations and Circularity") in {"white", "light"}:
        contradictions.append("Governance appears more mature than operational implementation.")
    if by_area.get("Strategy and Purpose") in {"mid", "dark"} and by_area.get("Finance and Investment") in {"white", "light"}:
        contradictions.append("Strategic ambition may not yet be matched by financial alignment.")
    problem_signals = [
        {
            "title": f"{item['area']} may need deeper mapping",
            "description": f"{item['area']} is marked as {item.get('maturity', 'unknown')} with {item.get('confidence') or 'unknown'} confidence.",
            "source": f"Business question {item.get('id')}",
            "confidence": item.get("confidence") or "low",
        }
        for item in business
        if item.get("maturity") in {"white", "light", "unknown"} or item.get("confidence") in {"low", "assumption"}
    ][:8]
    impact_questions = [f"Where does {area.lower()} show up across the value chain, process or service journey?" for area in (weak[:4] or gaps[:4])]
    human_recommendations = []
    if "Culture and Engagement" in weak or "Governance and Leadership" in weak:
        human_recommendations.append("Prioritise ownership, incentives and behavioural barriers in Human Empathy.")
    if "Transparency and Accountability" in gaps:
        human_recommendations.append("Check stakeholder trust and representation before treating disclosures as settled evidence.")
    if not human_recommendations:
        human_recommendations.append("Use Human Empathy to test whether business maturity is experienced consistently by staff and stakeholders.")
    return {
        "score": score,
        "evidenceWeightedConfidence": weighted,
        "answered": len([item for item in business if item.get("maturity") and item.get("confidence")]),
        "total": 16,
        "evidenceSupported": len([item for item in business if item.get("evidence")]),
        "needsReview": len(gaps),
        "strengths": strengths,
        "weakAreas": weak,
        "evidenceGaps": gaps,
        "contradictions": contradictions,
        "problemSignals": problem_signals,
        "impactJourneyQuestions": impact_questions,
        "humanEmpathyRecommendations": human_recommendations,
        "discoveryDomainReadings": domain_readings,
        "toolRecommendations": tool_recommendations[:40],
        "carryForwardItems": carry_forward_items[:60],
        "systemsConnections": [{"connection": key, "count": value} for key, value in sorted(systems_connections.items())],
    }


def save_explore_business(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    outputs = business_outputs(form_data)
    journey_id = str(payload.get("journeyId", "")) or None
    intelligence = intelligence_model(form_data, outputs, session_id, journey_id)
    with connect() as db:
        row = db.execute("SELECT id, created_at FROM explore_states WHERE anonymous_session_id = ?", (session_id,)).fetchone()
        state_id = row["id"] if row else "explore-" + secrets.token_hex(12)
        created_at = row["created_at"] if row else now_iso()
        if row:
            db.execute(
                "UPDATE explore_states SET form_data = ?, scores = ?, outputs = ?, status = ?, updated_at = ? WHERE id = ?",
                (json.dumps(form_data), json.dumps({"business": outputs}), json.dumps(outputs), status, now_iso(), state_id),
            )
        else:
            db.execute(
                "INSERT INTO explore_states (id, anonymous_session_id, active_empathy, form_data, scores, outputs, status, created_at, updated_at) VALUES (?, ?, 'business', ?, ?, ?, ?, ?, ?)",
                (state_id, session_id, json.dumps(form_data), json.dumps({"business": outputs}), json.dumps(outputs), status, created_at, now_iso()),
            )
        responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
        for key, response in responses.items():
            if not isinstance(response, dict) or response.get("empathy") != "business":
                continue
            maturity = response.get("maturity", "")
            confidence = response.get("confidence", "")
            db.execute(
                """
                INSERT OR REPLACE INTO business_empathy_responses
                (id, explore_state_id, anonymous_session_id, journey_id, question_id, question_number, category,
                 maturity_level, maturity_score, confidence, confidence_score, scope, evidence_reference, notes,
                 strategic_flags, discovery_domains, selected_tools, stakeholder_suggestions, reflection,
                 systems_connections, carry_forward_actions, evidence_tasks, tool_recommendations,
                 skipped_reason, needs_review, interpretation, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"business-response-{state_id}-{key}",
                    state_id,
                    session_id,
                    journey_id,
                    str(response.get("slug") or key),
                    question_number(response.get("id")),
                    str(response.get("area") or ""),
                    maturity,
                    MATURITY_SCORES.get(maturity),
                    confidence,
                    CONFIDENCE_SCORES.get(confidence, 0.0),
                    str(response.get("scope") or ""),
                    str(response.get("evidence") or ""),
                    str(response.get("notes") or ""),
                    json.dumps(as_list(response.get("flags"))),
                    json.dumps(as_list(response.get("discoveryDomains"))),
                    json.dumps(as_list(response.get("selectedTools"))),
                    json.dumps(as_list(response.get("stakeholderSuggestions"))),
                    json.dumps(response.get("reflection") if isinstance(response.get("reflection"), dict) else {}),
                    json.dumps(as_list(response.get("systemsConnections"))),
                    json.dumps(as_list(response.get("carryForwardActions"))),
                    json.dumps(as_list(response.get("evidenceTasks"))),
                    json.dumps(response.get("toolRecommendations") if isinstance(response.get("toolRecommendations"), list) else []),
                    str(response.get("skippedReason") or ""),
                    1 if response.get("needsReview") else 0,
                    str(response.get("interpretation") or ""),
                    now_iso(),
                ),
            )
        db.execute(
            """
            INSERT OR REPLACE INTO business_empathy_outputs
            (id, explore_state_id, anonymous_session_id, journey_id, score, evidence_weighted_confidence,
             strengths, weak_areas, evidence_gaps, contradictions, problem_signals, impact_journey_questions,
             human_empathy_recommendations, discovery_domain_readings, tool_recommendations, carry_forward_items,
             systems_connections, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"business-output-{state_id}",
                state_id,
                session_id,
                journey_id,
                outputs["score"],
                outputs["evidenceWeightedConfidence"],
                json.dumps(outputs["strengths"]),
                json.dumps(outputs["weakAreas"]),
                json.dumps(outputs["evidenceGaps"]),
                json.dumps(outputs["contradictions"]),
                json.dumps(outputs["problemSignals"]),
                json.dumps(outputs["impactJourneyQuestions"]),
                json.dumps(outputs["humanEmpathyRecommendations"]),
                json.dumps(outputs["discoveryDomainReadings"]),
                json.dumps(outputs["toolRecommendations"]),
                json.dumps(outputs["carryForwardItems"]),
                json.dumps(outputs["systemsConnections"]),
                now_iso(),
            ),
        )
        persist_intelligence(db, session_id, journey_id, intelligence)
    return {"ok": True, "stateId": state_id, "outputs": outputs, "intelligence": intelligence}


def get_explore_business(session_id: str) -> dict:
    with connect() as db:
        row = db.execute(
            "SELECT id, form_data, outputs, status, updated_at FROM explore_states WHERE anonymous_session_id = ?",
            (session_id[:80],),
        ).fetchone()
        memory = db.execute(
            "SELECT payload FROM journey_memory WHERE id = ?",
            (f"memory-{session_id[:80]}-business-intelligence",),
        ).fetchone()
    if not row:
        return {"ok": True, "found": False}
    return {
        "ok": True,
        "found": True,
        "stateId": row["id"],
        "formData": json.loads(row["form_data"]),
        "outputs": json.loads(row["outputs"]),
        "intelligence": json.loads(memory["payload"]) if memory else None,
        "status": row["status"],
        "updatedAt": row["updated_at"],
    }


def human_outputs(form_data: dict) -> dict:
    responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
    human = []
    for key, value in responses.items():
        if not isinstance(value, dict) or value.get("empathy") != "human":
            continue
        maturity = value.get("maturity", "")
        confidence = value.get("confidence", "")
        score = MATURITY_SCORES.get(maturity)
        confidence_score = CONFIDENCE_SCORES.get(confidence, 0.0)
        human.append({**value, "key": key, "score": score, "confidenceScore": confidence_score})
    scored = [item for item in human if item["score"] is not None]
    score = round(sum(item["score"] for item in scored) / len(scored), 2) if scored else None
    weighted = round(sum(item["confidenceScore"] for item in human) / len(human), 2) if human else 0
    represented = sorted({group for item in human for group in as_list(item.get("representedGroups"))})
    underrepresented = sorted({group for item in human for group in as_list(item.get("underrepresentedGroups"))})
    representation_entries = [entry for item in human for entry in (item.get("stakeholderRepresentation") if isinstance(item.get("stakeholderRepresentation"), list) else []) if isinstance(entry, dict)]
    direct_evidence = [entry for entry in representation_entries if entry.get("representationStatus") == "Direct evidence"]
    indirect_evidence = [entry for entry in representation_entries if entry.get("representationStatus") == "Indirect evidence"]
    high_exposure_low_influence = [
        entry for entry in representation_entries
        if entry.get("impactExposure") == "High exposure" and entry.get("influenceLevel") in {"Low influence", "No influence", "Unclear"}
    ]
    strengths = [item["area"] for item in human if item.get("maturity") in {"mid", "dark"}]
    weak = [item["area"] for item in human if item.get("maturity") in {"white", "light"}]
    gaps = [item["area"] for item in human if item.get("maturity") == "unknown" or item.get("confidence") in {"low", "assumption", "not_assessed", ""}]
    contradictions = []
    business = [value for value in responses.values() if isinstance(value, dict) and value.get("empathy") == "business"]
    business_by_area = {item.get("area"): item.get("maturity") for item in business}
    human_by_area = {item.get("area"): item.get("maturity") for item in human}
    if business_by_area.get("Governance and Leadership") in {"mid", "dark"} and human_by_area.get("Stakeholder Engagement") in {"white", "light"}:
        contradictions.append("Governance appears formalised, but stakeholder participation may remain weak.")
    if business_by_area.get("Culture and Engagement") in {"mid", "dark"} and human_by_area.get("Behavioural Change and Incentives") in {"white", "light"}:
        contradictions.append("Business culture may be described as engaged, but incentives may not yet support behaviour change.")
    if business_by_area.get("Regenerative Business Identity") in {"mid", "dark"} and human_by_area.get("Equity, Justice and Inclusion") in {"white", "light"}:
        contradictions.append("Regenerative ambition may not yet be matched by justice and inclusion practice.")
    if any(item.get("maturity") == "dark" and not any(entry.get("representationStatus") == "Direct evidence" for entry in (item.get("stakeholderRepresentation") or [])) for item in human):
        contradictions.append("At least one high Human maturity claim lacks direct stakeholder evidence.")
    problem_signals = [
        {
            "title": f"{item['area']} may need deeper human enquiry",
            "description": f"{item['area']} is marked as {item.get('maturity', 'unknown')} with {item.get('confidence') or 'unknown'} confidence.",
            "source": f"Human question {item.get('id')}",
            "confidence": item.get("confidence") or "low",
        }
        for item in human
        if item.get("maturity") in {"white", "light", "unknown"} or item.get("confidence") in {"low", "assumption"}
    ][:8]
    behavioural_barriers = [item.get("barriers") for item in human if item.get("barriers")]
    capability_gaps = [item.get("capabilityGaps") for item in human if item.get("capabilityGaps")]
    power_insights = [f"{entry.get('stakeholder')} has {entry.get('impactExposure')} and {entry.get('influenceLevel')}." for entry in high_exposure_low_influence]
    participation_tasks = []
    if underrepresented:
        participation_tasks.append(f"Seek input from underrepresented groups: {', '.join(underrepresented[:5])}.")
    participation_tasks.extend([item.get("researchTask") for item in human if item.get("researchTask")])
    participation_tasks.extend([f"Create stakeholder research task for {item.get('area')}." for item in human if item.get("maturity") == "unknown"])
    if weak:
        participation_tasks.append("Review who has authority, influence and lived experience for weak Human Empathy areas.")
    if not participation_tasks:
        participation_tasks.append("Confirm that represented stakeholder groups are broad enough for the journey scope.")
    facilitation_recommendations = []
    if len(underrepresented) > 3:
        facilitation_recommendations.append({"type": "Stakeholder research planning", "rationale": "Several relevant stakeholder groups are not represented or unclear.", "format": "Facilitated stakeholder mapping session", "confidence": "medium"})
    if high_exposure_low_influence:
        facilitation_recommendations.append({"type": "Power and influence mapping", "rationale": "At least one high-exposure stakeholder appears to have low influence.", "format": "Facilitated power mapping", "confidence": "medium"})
    if behavioural_barriers:
        facilitation_recommendations.append({"type": "Behavioural barrier workshop", "rationale": "Behavioural or incentive barriers have been recorded.", "format": "Team workshop", "confidence": "medium"})
    human_risk_flags = [
        {"area": item.get("area"), "category": flag, "urgency": "restricted review", "restricted": True, "escalationRequired": True}
        for item in human for flag in as_list(item.get("humanRiskFlags"))
    ]
    impact_questions = [f"Where do people experience the effects of {area.lower()} across the journey or value chain?" for area in (weak[:4] or gaps[:4])]
    planetary_recommendations = []
    if "Human and Community Wellbeing" in weak or "Equity, Justice and Inclusion" in weak:
        planetary_recommendations.append("Check whether environmental impacts and ecological dependencies affect communities unevenly.")
    if "Customer Engagement" in weak:
        planetary_recommendations.append("Explore product, material and use-phase impacts alongside customer agency.")
    if not planetary_recommendations:
        planetary_recommendations.append("Use Planetary Empathy to test whether human concerns connect to climate, nature, materials or place-based impacts.")
    return {
        "score": score,
        "evidenceWeightedConfidence": weighted,
        "answered": len([item for item in human if item.get("maturity") and item.get("confidence")]),
        "total": 5,
        "evidenceSupported": len([item for item in human if item.get("evidence")]),
        "needsReview": len(gaps),
        "representedGroups": represented,
        "underrepresentedGroups": underrepresented,
        "representationCoverage": len(representation_entries),
        "directEvidenceCoverage": len(direct_evidence),
        "indirectEvidenceCoverage": len(indirect_evidence),
        "strengths": strengths,
        "weakAreas": weak,
        "evidenceGaps": gaps,
        "contradictions": contradictions,
        "problemSignals": problem_signals,
        "behaviouralBarriers": behavioural_barriers,
        "capabilityGaps": capability_gaps,
        "powerInfluenceInsights": power_insights,
        "participationTasks": participation_tasks,
        "facilitationRecommendations": facilitation_recommendations,
        "humanRiskFlags": human_risk_flags,
        "impactJourneyQuestions": impact_questions,
        "planetaryEmpathyRecommendations": planetary_recommendations,
    }


def save_explore_human(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    outputs = human_outputs(form_data)
    journey_id = str(payload.get("journeyId", "")) or None
    intelligence = intelligence_model(form_data, outputs, session_id, journey_id)
    with connect() as db:
        row = db.execute("SELECT id, created_at FROM explore_states WHERE anonymous_session_id = ?", (session_id,)).fetchone()
        state_id = row["id"] if row else "explore-" + secrets.token_hex(12)
        created_at = row["created_at"] if row else now_iso()
        existing_scores = {}
        existing_outputs = {}
        if row:
            existing = db.execute("SELECT scores, outputs FROM explore_states WHERE id = ?", (state_id,)).fetchone()
            existing_scores = json.loads(existing["scores"]) if existing and existing["scores"] else {}
            existing_outputs = json.loads(existing["outputs"]) if existing and existing["outputs"] else {}
        existing_scores["human"] = outputs
        existing_outputs["human"] = outputs
        if row:
            db.execute(
                "UPDATE explore_states SET active_empathy = 'human', form_data = ?, scores = ?, outputs = ?, status = ?, updated_at = ? WHERE id = ?",
                (json.dumps(form_data), json.dumps(existing_scores), json.dumps(existing_outputs), status, now_iso(), state_id),
            )
        else:
            db.execute(
                "INSERT INTO explore_states (id, anonymous_session_id, active_empathy, form_data, scores, outputs, status, created_at, updated_at) VALUES (?, ?, 'human', ?, ?, ?, ?, ?, ?)",
                (state_id, session_id, json.dumps(form_data), json.dumps(existing_scores), json.dumps(existing_outputs), status, created_at, now_iso()),
            )
        responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
        for key, response in responses.items():
            if not isinstance(response, dict) or response.get("empathy") != "human":
                continue
            maturity = response.get("maturity", "")
            confidence = response.get("confidence", "")
            db.execute(
                """
                INSERT OR REPLACE INTO human_empathy_responses
                (id, explore_state_id, anonymous_session_id, journey_id, question_id, question_number, category,
                 maturity_level, maturity_score, confidence, confidence_score, scope, represented_groups,
                 underrepresented_groups, behavioural_barriers, capability_gaps, power_concern, research_task,
                 stakeholder_representation, discovery_domains, selected_tools, evidence_tasks, systems_connections,
                 carry_forward_actions, human_risk_flags, reflection, evidence_reference, notes, strategic_flags,
                 skipped_reason, needs_review, interpretation, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"human-response-{state_id}-{key}",
                    state_id,
                    session_id,
                    journey_id,
                    str(response.get("slug") or key),
                    question_number(response.get("id")),
                    str(response.get("area") or ""),
                    maturity,
                    MATURITY_SCORES.get(maturity),
                    confidence,
                    CONFIDENCE_SCORES.get(confidence, 0.0),
                    str(response.get("scope") or ""),
                    json.dumps(as_list(response.get("representedGroups"))),
                    json.dumps(as_list(response.get("underrepresentedGroups"))),
                    str(response.get("barriers") or ""),
                    str(response.get("capabilityGaps") or ""),
                    str(response.get("powerConcern") or ""),
                    str(response.get("researchTask") or ""),
                    json.dumps(response.get("stakeholderRepresentation") if isinstance(response.get("stakeholderRepresentation"), list) else []),
                    json.dumps(as_list(response.get("discoveryDomains"))),
                    json.dumps(as_list(response.get("selectedTools"))),
                    json.dumps(as_list(response.get("evidenceTasks"))),
                    json.dumps(as_list(response.get("systemsConnections"))),
                    json.dumps(as_list(response.get("carryForwardActions"))),
                    json.dumps(as_list(response.get("humanRiskFlags"))),
                    json.dumps(response.get("reflection") if isinstance(response.get("reflection"), dict) else {}),
                    str(response.get("evidence") or ""),
                    str(response.get("notes") or ""),
                    json.dumps(as_list(response.get("flags"))),
                    str(response.get("skippedReason") or ""),
                    1 if response.get("needsReview") else 0,
                    str(response.get("interpretation") or ""),
                    now_iso(),
                ),
            )
            response_id = f"human-response-{state_id}-{key}"
            for entry in response.get("stakeholderRepresentation") if isinstance(response.get("stakeholderRepresentation"), list) else []:
                if not isinstance(entry, dict):
                    continue
                stakeholder = str(entry.get("stakeholder") or "Unknown stakeholder")
                db.execute(
                    """
                    INSERT OR REPLACE INTO response_stakeholder_representations
                    (id, response_id, stakeholder_id, representation_status, influence_level, impact_exposure,
                     decision_authority, evidence_type, confidentiality_level, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"representation-{response_id}-{slugify(stakeholder)}",
                        response_id,
                        slugify(stakeholder),
                        str(entry.get("representationStatus") or "Unclear"),
                        str(entry.get("influenceLevel") or "Unclear"),
                        str(entry.get("impactExposure") or "Unclear"),
                        str(entry.get("decisionAuthority") or "Unclear"),
                        str(entry.get("evidenceType") or "Unclear"),
                        str(entry.get("confidentialityLevel") or "Group-level"),
                        "",
                        now_iso(),
                    ),
                )
            if response.get("barriers"):
                db.execute(
                    "INSERT OR REPLACE INTO behavioural_barriers (id, assessment_id, response_id, barrier_type, description, stakeholder_ids, evidence_ids, confidence, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)",
                    (f"barrier-{response_id}", state_id, response_id, "behavioural", str(response.get("barriers")), json.dumps(as_list(response.get("representedGroups"))), json.dumps(as_list(response.get("evidenceTasks"))), confidence or "low", now_iso()),
                )
            if response.get("researchTask") or maturity == "unknown":
                db.execute(
                    "INSERT OR REPLACE INTO stakeholder_research_tasks (id, assessment_id, stakeholder_id, research_purpose, suggested_method, questions, consent_requirements, owner, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'suggested', ?)",
                    (f"research-{response_id}", state_id, slugify(str(response.get("area") or key)), str(response.get("researchTask") or f"Gather direct evidence for {response.get('area')}"), "Stakeholder interview or facilitated mapping", json.dumps(as_list(response.get("discoveryDomains"))), "Purpose, consent, feedback route and minimised personal data", "", now_iso()),
                )
            for flag in as_list(response.get("humanRiskFlags")):
                db.execute(
                    "INSERT OR REPLACE INTO human_risk_flags (id, assessment_id, response_id, category, description, urgency, restricted, escalation_required, owner, status, updated_at) VALUES (?, ?, ?, ?, ?, 'restricted review', 1, 1, '', 'open', ?)",
                    (f"human-risk-{response_id}-{slugify(flag)}", state_id, response_id, flag, "Sensitive human-risk flag recorded separately from maturity scoring.", now_iso()),
                )
        db.execute(
            """
            INSERT OR REPLACE INTO human_empathy_outputs
            (id, explore_state_id, anonymous_session_id, journey_id, score, evidence_weighted_confidence,
             represented_groups, underrepresented_groups, strengths, weak_areas, evidence_gaps, contradictions,
             problem_signals, participation_tasks, impact_journey_questions, planetary_empathy_recommendations, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"human-output-{state_id}",
                state_id,
                session_id,
                journey_id,
                outputs["score"],
                outputs["evidenceWeightedConfidence"],
                json.dumps(outputs["representedGroups"]),
                json.dumps(outputs["underrepresentedGroups"]),
                json.dumps(outputs["strengths"]),
                json.dumps(outputs["weakAreas"]),
                json.dumps(outputs["evidenceGaps"]),
                json.dumps(outputs["contradictions"]),
                json.dumps(outputs["problemSignals"]),
                json.dumps(outputs["participationTasks"]),
                json.dumps(outputs["impactJourneyQuestions"]),
                json.dumps(outputs["planetaryEmpathyRecommendations"]),
                now_iso(),
            ),
        )
        for recommendation in outputs.get("facilitationRecommendations", []):
            db.execute(
                "INSERT OR REPLACE INTO facilitation_recommendations (id, assessment_id, recommendation_type, rationale, stakeholder_ids, suggested_format, suggested_tools, confidence, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'suggested', ?)",
                (f"facilitation-{state_id}-{slugify(recommendation.get('type', 'recommendation'))}", state_id, recommendation.get("type", ""), recommendation.get("rationale", ""), json.dumps(outputs.get("representedGroups", [])), recommendation.get("format", ""), json.dumps([]), recommendation.get("confidence", "low"), now_iso()),
            )
        persist_intelligence(db, session_id, journey_id, intelligence)
    return {"ok": True, "stateId": state_id, "outputs": outputs, "intelligence": intelligence}


def planetary_outputs(form_data: dict) -> dict:
    responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
    planetary = []
    for key, value in responses.items():
        if not isinstance(value, dict) or value.get("empathy") != "planetary":
            continue
        maturity = value.get("maturity", "")
        confidence = value.get("confidence", "")
        planetary.append({**value, "key": key, "score": MATURITY_SCORES.get(maturity), "confidenceScore": CONFIDENCE_SCORES.get(confidence, 0.0)})
    scored = [item for item in planetary if item["score"] is not None]
    score = round(sum(item["score"] for item in scored) / len(scored), 2) if scored else None
    weighted = round(sum(item["confidenceScore"] for item in planetary) / len(planetary), 2) if planetary else 0
    strengths = [item["area"] for item in planetary if item.get("maturity") in {"mid", "dark"}]
    weak = [item["area"] for item in planetary if item.get("maturity") in {"white", "light"}]
    gaps = [item["area"] for item in planetary if item.get("maturity") == "unknown" or item.get("confidence") in {"low", "assumption", "not_assessed", ""}]
    boundary_coverage = [
        {"area": item.get("area"), **(item.get("ecologicalBoundary") if isinstance(item.get("ecologicalBoundary"), dict) else {})}
        for item in planetary
        if item.get("ecologicalBoundary")
    ]
    dependencies = [item.get("dependencies") for item in planetary if item.get("dependencies")]
    impact_signals = [item.get("impactSignal") for item in planetary if item.get("impactSignal")]
    material_flows = [item.get("materialFlow") for item in planetary if item.get("materialFlow")]
    environmental_tasks = [item.get("environmentalTask") for item in planetary if item.get("environmentalTask")]
    environmental_tasks.extend([f"Gather environmental evidence for {item.get('area')}." for item in planetary if item.get("maturity") == "unknown"])
    risk_flags = [
        {"area": item.get("area"), "riskType": flag, "severity": "review", "confidence": item.get("confidence") or "low"}
        for item in planetary for flag in as_list(item.get("planetaryRiskFlags"))
    ]
    business = [value for value in responses.values() if isinstance(value, dict) and value.get("empathy") == "business"]
    human = [value for value in responses.values() if isinstance(value, dict) and value.get("empathy") == "human"]
    business_by_area = {item.get("area"): item.get("maturity") for item in business}
    human_by_area = {item.get("area"): item.get("maturity") for item in human}
    planetary_by_area = {item.get("area"): item.get("maturity") for item in planetary}
    contradictions = []
    if planetary_by_area.get("Circular Design and Materials") in {"mid", "dark"} and planetary_by_area.get("Value Chain and Traceability") in {"white", "light", "unknown"}:
        contradictions.append("Circularity maturity may be ahead of traceability evidence.")
    if planetary_by_area.get("Climate and Biodiversity Integration") in {"mid", "dark"} and planetary_by_area.get("Ecosystem Stewardship") in {"white", "light", "unknown"}:
        contradictions.append("Climate maturity may not yet be matched by ecosystem stewardship.")
    if business_by_area.get("Operations and Circularity") in {"mid", "dark"} and gaps:
        contradictions.append("Operational maturity appears stronger than the available Planetary evidence.")
    if human_by_area.get("Human and Community Wellbeing") in {"white", "light", "unknown"} and (impact_signals or dependencies):
        contradictions.append("Human wellbeing concerns may connect to ecological impacts or dependencies.")
    hotspot_candidates = [
        {
            "title": f"{item.get('area')} hotspot candidate",
            "description": item.get("impactSignal") or item.get("dependencies") or f"{item.get('area')} needs ecological mapping.",
            "source": f"Planetary question {item.get('id')}",
            "confidence": item.get("confidence") or "low",
        }
        for item in planetary
        if item.get("maturity") in {"white", "light", "unknown"} or item.get("impactSignal") or item.get("dependencies")
    ][:8]
    problem_signals = [
        {
            "title": f"{item['area']} may need ecological systems mapping",
            "description": f"{item['area']} is marked as {item.get('maturity', 'unknown')} with {item.get('confidence') or 'unknown'} confidence.",
            "source": f"Planetary question {item.get('id')}",
            "confidence": item.get("confidence") or "low",
        }
        for item in planetary
        if item.get("maturity") in {"white", "light", "unknown"} or item.get("confidence") in {"low", "assumption"}
    ][:8]
    impact_questions = [f"Where does {area.lower()} appear across lifecycle stages, places, suppliers or material flows?" for area in (weak[:4] or gaps[:4])]
    synthesis_handover = [
        "Connect Business, Human and Planetary findings before selecting interventions.",
        "Review whether ecological hotspots also create human or strategic consequences.",
    ]
    if contradictions:
        synthesis_handover.append("Carry cross-empathy contradictions into Three Empathies Synthesis.")
    return {
        "score": score,
        "evidenceWeightedConfidence": weighted,
        "answered": len([item for item in planetary if item.get("maturity") and item.get("confidence")]),
        "total": 4,
        "evidenceSupported": len([item for item in planetary if item.get("evidence")]),
        "needsReview": len(gaps) + len(risk_flags),
        "strengths": strengths,
        "weakAreas": weak,
        "evidenceGaps": gaps,
        "boundaryCoverage": boundary_coverage,
        "ecologicalDependencies": dependencies,
        "impactSignals": impact_signals,
        "materialFlows": material_flows,
        "hotspotCandidates": hotspot_candidates,
        "contradictions": contradictions,
        "problemSignals": problem_signals,
        "environmentalEvidenceTasks": environmental_tasks,
        "planetaryRiskFlags": risk_flags,
        "impactJourneyQuestions": impact_questions,
        "synthesisHandover": synthesis_handover,
    }


def save_explore_planetary(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    outputs = planetary_outputs(form_data)
    journey_id = str(payload.get("journeyId", "")) or None
    intelligence = intelligence_model(form_data, outputs, session_id, journey_id)
    with connect() as db:
        row = db.execute("SELECT id, created_at FROM explore_states WHERE anonymous_session_id = ?", (session_id,)).fetchone()
        state_id = row["id"] if row else "explore-" + secrets.token_hex(12)
        created_at = row["created_at"] if row else now_iso()
        existing_scores = {}
        existing_outputs = {}
        if row:
            existing = db.execute("SELECT scores, outputs FROM explore_states WHERE id = ?", (state_id,)).fetchone()
            existing_scores = json.loads(existing["scores"]) if existing and existing["scores"] else {}
            existing_outputs = json.loads(existing["outputs"]) if existing and existing["outputs"] else {}
        existing_scores["planetary"] = outputs
        existing_outputs["planetary"] = outputs
        if row:
            db.execute("UPDATE explore_states SET active_empathy = 'planetary', form_data = ?, scores = ?, outputs = ?, status = ?, updated_at = ? WHERE id = ?", (json.dumps(form_data), json.dumps(existing_scores), json.dumps(existing_outputs), status, now_iso(), state_id))
        else:
            db.execute("INSERT INTO explore_states (id, anonymous_session_id, active_empathy, form_data, scores, outputs, status, created_at, updated_at) VALUES (?, ?, 'planetary', ?, ?, ?, ?, ?, ?)", (state_id, session_id, json.dumps(form_data), json.dumps(existing_scores), json.dumps(existing_outputs), status, created_at, now_iso()))
        responses = form_data.get("responses") if isinstance(form_data.get("responses"), dict) else {}
        for key, response in responses.items():
            if not isinstance(response, dict) or response.get("empathy") != "planetary":
                continue
            maturity = response.get("maturity", "")
            confidence = response.get("confidence", "")
            response_id = f"planetary-response-{state_id}-{key}"
            boundary = response.get("ecologicalBoundary") if isinstance(response.get("ecologicalBoundary"), dict) else {}
            db.execute(
                """
                INSERT OR REPLACE INTO planetary_empathy_responses
                (id, explore_state_id, anonymous_session_id, journey_id, question_id, question_number, category,
                 maturity_level, maturity_score, confidence, confidence_score, scope, ecological_boundary, dependencies,
                 impact_signal, material_flow, environmental_task, discovery_domains, selected_tools, evidence_tasks,
                 systems_connections, carry_forward_actions, planetary_risk_flags, reflection, evidence_reference, notes,
                 strategic_flags, skipped_reason, needs_review, interpretation, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response_id, state_id, session_id, journey_id, str(response.get("slug") or key), question_number(response.get("id")), str(response.get("area") or ""),
                    maturity, MATURITY_SCORES.get(maturity), confidence, CONFIDENCE_SCORES.get(confidence, 0.0), str(response.get("scope") or ""),
                    json.dumps(boundary), str(response.get("dependencies") or ""), str(response.get("impactSignal") or ""), str(response.get("materialFlow") or ""),
                    str(response.get("environmentalTask") or ""), json.dumps(as_list(response.get("discoveryDomains"))), json.dumps(as_list(response.get("selectedTools"))),
                    json.dumps(as_list(response.get("evidenceTasks"))), json.dumps(as_list(response.get("systemsConnections"))), json.dumps(as_list(response.get("carryForwardActions"))),
                    json.dumps(as_list(response.get("planetaryRiskFlags"))), json.dumps(response.get("reflection") if isinstance(response.get("reflection"), dict) else {}),
                    str(response.get("evidence") or ""), str(response.get("notes") or ""), json.dumps(as_list(response.get("flags"))), str(response.get("skippedReason") or ""),
                    1 if response.get("needsReview") else 0, str(response.get("interpretation") or ""), now_iso(),
                ),
            )
            db.execute("INSERT OR REPLACE INTO ecological_boundaries (id, journey_id, response_id, organisational_scope, lifecycle_stages, geographic_scope, ecosystem_types, reporting_period_start, reporting_period_end, exclusions, limitations, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"boundary-{response_id}", journey_id, response_id, str(boundary.get("organisationalScope") or boundary.get("operationalBoundary") or ""), str(boundary.get("lifecycleStages") or ""), str(boundary.get("geographicScope") or boundary.get("geography") or ""), "", str(boundary.get("reportingPeriod") or ""), "", str(boundary.get("includedSuppliers") or ""), str(boundary.get("limitations") or ""), now_iso()))
            if response.get("dependencies"):
                db.execute("INSERT OR REPLACE INTO ecological_dependencies (id, assessment_id, response_id, dependency_type, resource_or_service, location, criticality, substitutability, evidence_ids, confidence, status, updated_at) VALUES (?, ?, ?, 'ecological_dependency', ?, ?, 'review', 'unknown', ?, ?, 'active', ?)", (f"dependency-{response_id}", state_id, response_id, str(response.get("dependencies")), str(boundary.get("geography") or ""), json.dumps(as_list(response.get("evidenceTasks"))), confidence or "low", now_iso()))
            if response.get("impactSignal"):
                db.execute("INSERT OR REPLACE INTO environmental_impact_signals (id, assessment_id, response_id, impact_type, lifecycle_stage, location, direction, magnitude, duration, reversibility, affected_ecosystems, affected_stakeholders, evidence_ids, confidence, status, updated_at) VALUES (?, ?, ?, 'environmental_impact', ?, ?, 'pressure', 'review', '', '', '', '', ?, ?, 'active', ?)", (f"impact-{response_id}", state_id, response_id, str(boundary.get("lifecycleStages") or ""), str(boundary.get("geography") or ""), json.dumps(as_list(response.get("evidenceTasks"))), confidence or "low", now_iso()))
            if response.get("materialFlow"):
                db.execute("INSERT OR REPLACE INTO material_flow_signals (id, assessment_id, response_id, material_name, material_category, source_region, quantity, unit, destination, circularity_status, toxicity_risk, criticality, evidence_ids, confidence, updated_at) VALUES (?, ?, ?, ?, '', ?, '', '', '', 'review', 'review', 'review', ?, ?, ?)", (f"material-{response_id}", state_id, response_id, str(response.get("materialFlow")), str(boundary.get("geography") or ""), json.dumps(as_list(response.get("evidenceTasks"))), confidence or "low", now_iso()))
            if response.get("environmentalTask") or maturity == "unknown":
                db.execute("INSERT OR REPLACE INTO environmental_evidence_tasks (id, journey_id, assessment_id, response_id, evidence_needed, suggested_source, suggested_owner, specialist_required, priority, status, updated_at) VALUES (?, ?, ?, ?, ?, 'Environmental evidence source', 'Sustainability or operations owner', ?, 'medium', 'suggested', ?)", (f"env-task-{response_id}", journey_id, state_id, response_id, str(response.get("environmentalTask") or f"Gather environmental evidence for {response.get('area')}"), 1 if response.get("confidence") in {"low", "assumption", "not_assessed"} else 0, now_iso()))
            for flag in as_list(response.get("planetaryRiskFlags")):
                db.execute("INSERT OR REPLACE INTO planetary_risk_flags (id, assessment_id, response_id, risk_type, description, affected_systems, urgency, severity, cascading_risk, restricted, owner, status, updated_at) VALUES (?, ?, ?, ?, 'Planetary risk flag recorded separately from maturity scoring.', ?, 'review', 'review', ?, 0, '', 'open', ?)", (f"planetary-risk-{response_id}-{slugify(flag)}", state_id, response_id, flag, json.dumps(as_list(response.get("systemsConnections"))), 1 if "Cascading" in flag else 0, now_iso()))
        db.execute(
            """
            INSERT OR REPLACE INTO planetary_empathy_outputs
            (id, explore_state_id, anonymous_session_id, journey_id, score, evidence_weighted_confidence, strengths,
             weak_areas, evidence_gaps, boundary_coverage, ecological_dependencies, impact_signals, material_flows,
             hotspot_candidates, contradictions, problem_signals, environmental_evidence_tasks, impact_journey_questions,
             synthesis_handover, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (f"planetary-output-{state_id}", state_id, session_id, journey_id, outputs["score"], outputs["evidenceWeightedConfidence"], json.dumps(outputs["strengths"]), json.dumps(outputs["weakAreas"]), json.dumps(outputs["evidenceGaps"]), json.dumps(outputs["boundaryCoverage"]), json.dumps(outputs["ecologicalDependencies"]), json.dumps(outputs["impactSignals"]), json.dumps(outputs["materialFlows"]), json.dumps(outputs["hotspotCandidates"]), json.dumps(outputs["contradictions"]), json.dumps(outputs["problemSignals"]), json.dumps(outputs["environmentalEvidenceTasks"]), json.dumps(outputs["impactJourneyQuestions"]), json.dumps(outputs["synthesisHandover"]), now_iso()),
        )
        persist_intelligence(db, session_id, journey_id, intelligence)
    return {"ok": True, "stateId": state_id, "outputs": outputs, "intelligence": intelligence}


IMPACT_LAYER_TO_EMPATHY = {
    "business": "business",
    "social": "human",
    "environmental": "planetary",
    "governance": "governance",
}

PAGE4_CHILD_TABLES = [
    "journey_boundaries",
    "stage_activities",
    "stage_decisions",
    "stage_stakeholders",
    "journey_inputs",
    "journey_outputs",
    "journey_human_experiences",
    "journey_impacts",
    "journey_assumptions",
    "journey_unknowns",
    "journey_evidence_links",
    "system_relationships",
    "journey_feedback_loop_members",
    "journey_feedback_loops",
    "journey_bottlenecks",
    "journey_dependencies",
    "journey_strengths",
    "journey_opportunity_signals",
    "hotspot_candidates",
    "leverage_points",
    "impact_journey_problem_signals",
    "stage_handover_manifests",
]

IMPACT_CATEGORIES = {
    "business": ["cost", "revenue", "operational efficiency", "resilience", "risk", "reputation", "compliance", "innovation", "supply continuity", "data quality", "capability", "strategic alignment"],
    "human": ["health", "safety", "wellbeing", "workload", "equality", "inclusion", "accessibility", "trust", "participation", "behaviour", "community", "human rights", "justice", "agency"],
    "planetary": ["climate", "energy", "materials", "water", "waste", "pollution", "biodiversity", "land", "circularity", "toxicity", "ecosystem health", "resource depletion", "restoration"],
    "governance": ["ownership", "accountability", "transparency", "incentives", "decision rights", "oversight", "reporting", "policy", "data governance", "procurement", "legal exposure", "escalation", "stakeholder representation"],
}


def json_loads_safe(value: object, fallback: object) -> object:
    if not value:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return fallback


def seed_impact_categories(db: sqlite3.Connection) -> None:
    method = db.execute("SELECT id FROM methodology_versions WHERE active = 1 LIMIT 1").fetchone()
    method_id = method["id"] if method else "methodology-green-spectrum-0-1-0"
    timestamp = now_iso()
    for empathy, categories in IMPACT_CATEGORIES.items():
        for category in categories:
            category_id = f"impact-category-{empathy}-{slugify(category)}"
            db.execute(
                """
                INSERT OR IGNORE INTO impact_category_definitions
                (id, methodology_version_id, empathy_type, category_key, label, description, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (category_id, method_id, empathy, slugify(category), category.title(), f"Green Spectrum {empathy} impact category: {category}.", timestamp, timestamp),
            )


def resolve_impact_context(db: sqlite3.Connection, session_id: str, journey_id: str | None = None) -> dict:
    onboarding = db.execute(
        """
        SELECT journey_id, organisation_id, form_data
        FROM onboarding_states
        WHERE anonymous_session_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    organisation_id = onboarding["organisation_id"] if onboarding else None
    resolved_journey_id = journey_id or (onboarding["journey_id"] if onboarding else None)
    form_data = json_loads_safe(onboarding["form_data"], {}) if onboarding else {}
    method = db.execute("SELECT id FROM methodology_versions WHERE active = 1 LIMIT 1").fetchone()
    return {
        "anonymousSessionId": session_id,
        "organisationId": organisation_id,
        "journeyId": resolved_journey_id,
        "methodologyVersionId": method["id"] if method else "methodology-green-spectrum-0-1-0",
        "onboarding": form_data if isinstance(form_data, dict) else {},
    }


def page3_source_bundle(db: sqlite3.Connection, session_id: str, journey_id: str | None = None) -> dict:
    explore = db.execute(
        """
        SELECT id, journey_id, form_data, scores, outputs, status, updated_at
        FROM explore_states
        WHERE anonymous_session_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    memory = db.execute(
        """
        SELECT id, payload, updated_at
        FROM journey_memory
        WHERE anonymous_session_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    bundle = {"found": bool(explore or memory), "explore": None, "intelligence": None, "signals": [], "questions": [], "evidenceGaps": []}
    if explore:
        outputs = json_loads_safe(explore["outputs"], {})
        form_data = json_loads_safe(explore["form_data"], {})
        bundle["explore"] = {
            "id": explore["id"],
            "journeyId": explore["journey_id"],
            "status": explore["status"],
            "updatedAt": explore["updated_at"],
            "formData": form_data,
            "outputs": outputs,
        }
        if isinstance(outputs, dict):
            for empathy_output in outputs.values():
                if not isinstance(empathy_output, dict):
                    continue
                bundle["signals"].extend([item for item in empathy_output.get("problemSignals", []) if isinstance(item, dict)])
                bundle["questions"].extend(as_list(empathy_output.get("impactJourneyQuestions")))
                bundle["evidenceGaps"].extend(as_list(empathy_output.get("evidenceGaps")))
                bundle["evidenceGaps"].extend(as_list(empathy_output.get("environmentalEvidenceTasks")))
    if memory:
        intelligence = json_loads_safe(memory["payload"], {})
        bundle["intelligence"] = intelligence
        if isinstance(intelligence, dict):
            mapping = intelligence.get("impactJourneyMapping") if isinstance(intelligence.get("impactJourneyMapping"), dict) else {}
            bundle["signals"].extend([{"title": item, "description": "Imported from organisational intelligence mapping hints.", "confidence": "low", "source": "Page 3 intelligence"} for item in as_list(mapping.get("journeyNodes"))])
    return bundle


def impact_scope(form_data: dict) -> dict:
    scope = form_data.get("scope") if isinstance(form_data.get("scope"), dict) else {}
    return scope


def derive_stage_type(title: str) -> str:
    lower = title.lower()
    for key, words in {
        "procurement": ["procurement", "sourcing", "supplier"],
        "manufacturing": ["production", "manufacturing", "processing"],
        "logistics": ["distribution", "transport", "logistics"],
        "use": ["use", "participation", "service delivery"],
        "recovery": ["return", "recovery", "reuse", "recycling", "end of life"],
        "governance": ["approval", "review", "decision", "governance"],
    }.items():
        if any(word in lower for word in words):
            return key
    return "custom"


def impact_completion(form_data: dict) -> int:
    scope = impact_scope(form_data)
    stages = form_data.get("stages") if isinstance(form_data.get("stages"), list) else []
    layer_items = form_data.get("layerItems") if isinstance(form_data.get("layerItems"), dict) else {}
    relationships = form_data.get("relationships") if isinstance(form_data.get("relationships"), list) else []
    signals = form_data.get("problemSignals") if isinstance(form_data.get("problemSignals"), list) else []
    impact_keys = ["environmental", "social", "governance", "business", "businessEffects", "humanEffects", "planetaryEffects"]
    decision_keys = ["decisions", "decisionPoints"]
    sections = 0
    sections += 1 if scope.get("journeyType") and scope.get("startPoint") and scope.get("endPoint") else 0
    sections += 1 if len(stages) >= 3 else 0
    sections += 1 if stages and all(layer_items.get(stage.get("id"), {}).get("activities") for stage in stages if isinstance(stage, dict)) else 0
    sections += 1 if relationships else 0
    sections += 1 if signals or form_data.get("opportunities") else 0
    sections += 1 if any(layer_items.get(stage.get("id"), {}).get(key) for stage in stages if isinstance(stage, dict) for key in impact_keys + ["unknowns"]) else 0
    sections += 1 if str(scope.get("mapReviewed", "")).lower() in {"on", "true", "yes"} or any(layer_items.get(stage.get("id"), {}).get(key) for stage in stages if isinstance(stage, dict) for key in decision_keys) else 0
    return round((sections / 7) * 100)


def classify_relationship(rel: dict, source_name: str, target_name: str) -> dict:
    text = f"{rel.get('type', '')} {rel.get('description', '')} {source_name} {target_name}".lower()
    relationship_type = str(rel.get("type") or "")
    if not relationship_type or relationship_type.lower() == "dependency":
        if any(word in text for word in ["return", "rework", "review", "feedback", "learn"]):
            relationship_type = "Feedback loop"
        elif any(word in text for word in ["delay", "waiting", "lead time", "approval", "procurement"]):
            relationship_type = "Delay"
        elif any(word in text for word in ["trade", "compromise", "cost pressure", "quality", "safety"]):
            relationship_type = "Trade-off"
        elif any(word in text for word in ["capacity", "bottleneck", "constraint", "capability"]):
            relationship_type = "Bottleneck"
        elif any(word in text for word in ["risk", "failure", "exposure", "scrutiny"]):
            relationship_type = "Risk transfer"
        elif any(word in text for word in ["reinforce", "growth", "rebound", "lock-in"]):
            relationship_type = "Reinforcing loop"
        else:
            relationship_type = "Dependency"
    confidence = str(rel.get("confidence") or "medium").lower()
    if confidence not in {"high", "medium", "low", "assumption"}:
        confidence = "medium"
    return {
        "type": relationship_type,
        "confidence": confidence,
        "nonAdjacent": source_name != "Source stage" and target_name != "target stage" and abs(int(rel.get("sourceSequence", 0) or 0) - int(rel.get("targetSequence", 0) or 0)) > 1,
    }


def impact_stage_suggestions(context: dict) -> list[str]:
    onboarding = context.get("onboarding") if isinstance(context.get("onboarding"), dict) else {}
    industry = " ".join(as_list(onboarding.get("industry"))).lower()
    if any(word in industry for word in ["manufacturing", "food", "product"]):
        return ["Raw materials", "Procurement", "Production", "Distribution", "Use", "End of life"]
    if any(word in industry for word in ["public", "professional", "service", "health", "education"]):
        return ["Need identified", "Access", "Service delivery", "Use or participation", "Follow-up", "Long-term outcome"]
    return ["Issue identified", "Evidence gathered", "Proposal developed", "Approval", "Implementation", "Review"]


def analyse_impact_journey(form_data: dict, page3: dict) -> dict:
    stages = [stage for stage in form_data.get("stages", []) if isinstance(stage, dict)]
    layer_items = form_data.get("layerItems") if isinstance(form_data.get("layerItems"), dict) else {}
    relationships = [item for item in form_data.get("relationships", []) if isinstance(item, dict)]
    stage_by_id = {stage.get("id"): stage for stage in stages}
    stage_sequence = {stage.get("id"): index + 1 for index, stage in enumerate(stages)}
    hotspots = []
    leverage = []
    problem_signals = []
    for stage in stages:
        stage_id = stage.get("id")
        items = layer_items.get(stage_id, {}) if isinstance(layer_items.get(stage_id), dict) else {}
        impact_count = sum(len(items.get(key, [])) for key in ["business", "social", "environmental", "governance", "businessEffects", "humanEffects", "planetaryEffects"] if isinstance(items.get(key), list))
        unknown_count = len(items.get("unknowns", [])) if isinstance(items.get("unknowns"), list) else 0
        stakeholder_count = len(items.get("stakeholders", [])) if isinstance(items.get("stakeholders"), list) else 0
        if impact_count or unknown_count:
            title = f"{stage.get('name') or 'Stage'} hotspot candidate"
            rationale = f"Suggested because this stage has {impact_count} mapped impact items, {unknown_count} uncertainty items and {stakeholder_count} stakeholder entries."
            hotspots.append({
                "id": f"hotspot-{slugify(str(stage_id or title))}",
                "stageId": stage_id,
                "title": title,
                "description": "Review this stage before prioritising problems on Page 5.",
                "type": "multi-impact" if impact_count > 1 else "uncertainty" if unknown_count else "impact",
                "impactDimensions": [key for key in ["business", "social", "environmental", "governance"] if isinstance(items.get(key), list) and items.get(key)],
                "rationale": rationale,
                "severity": "high" if impact_count >= 4 else "medium" if impact_count >= 2 else "review",
                "uncertainty": "high" if unknown_count else "medium",
                "confidence": "medium" if impact_count else "low",
            })
            problem_signals.append({
                "id": f"impact-problem-{slugify(str(stage_id or title))}",
                "stageId": stage_id,
                "title": f"{stage.get('name') or 'Stage'} may need prioritisation",
                "description": f"This signal is generated from mapped impacts and uncertainties at {stage.get('name') or 'this stage'}.",
                "type": "journey_hotspot",
                "rationale": rationale,
                "confidence": "medium" if impact_count else "low",
            })
    for rel in relationships:
        source = stage_by_id.get(rel.get("source"), {}).get("name", "Source stage")
        target = stage_by_id.get(rel.get("target"), {}).get("name", "target stage")
        rel_for_classification = {**rel, "sourceSequence": stage_sequence.get(rel.get("source"), 0), "targetSequence": stage_sequence.get(rel.get("target"), 0)}
        classified = classify_relationship(rel_for_classification, source, target)
        rel_type = classified["type"]
        leverage.append({
            "id": f"leverage-{slugify(str(rel.get('id') or source + target + rel_type))}",
            "relationshipId": rel.get("id"),
            "title": f"{source} to {target}",
            "description": f"{source} affects {target} through {rel_type.lower()}.",
            "leverageType": rel_type.lower().replace(" ", "_"),
            "rationale": f"Suggested because the map shows a {rel_type.lower()} that may change downstream outcomes or reveal where a safe-to-fail intervention belongs.",
            "expectedInfluence": "high" if rel_type.lower() in {"feedback loop", "reinforcing loop", "bottleneck"} else "review",
            "uncertainty": "medium" if classified["confidence"] == "medium" else "high" if classified["confidence"] in {"low", "assumption"} else "low",
            "confidence": classified["confidence"],
            "relationshipType": rel_type,
            "nonAdjacent": classified["nonAdjacent"],
        })
    for signal in page3.get("signals", [])[:8]:
        if isinstance(signal, dict) and signal.get("title"):
            problem_signals.append({
                "id": f"impact-problem-page3-{slugify(str(signal.get('title')))}",
                "stageId": None,
                "title": str(signal.get("title")),
                "description": str(signal.get("description") or "Imported from Page 3 as a candidate problem signal for mapping."),
                "type": "page3_import",
                "rationale": f"Imported from {signal.get('source') or 'Page 3'} and must be checked against the journey map.",
                "confidence": str(signal.get("confidence") or "low"),
            })
    return {
        "hotspots": hotspots[:12],
        "leveragePoints": leverage[:12],
        "problemSignals": list({item["title"]: item for item in problem_signals}.values())[:16],
        "evidenceGaps": page3.get("evidenceGaps", [])[:16],
        "priorityQuestions": page3.get("questions", [])[:10],
        "completionPercentage": impact_completion(form_data),
        "readiness": "ready_to_proceed" if impact_completion(form_data) >= 85 and relationships else "structurally_complete" if impact_completion(form_data) >= 70 else "incomplete",
    }


def normalise_impact_form(payload: dict) -> dict:
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    if "stages" not in form_data and "state" in payload and isinstance(payload["state"], dict):
        form_data = payload["state"]
    return {
        "scope": form_data.get("scope") if isinstance(form_data.get("scope"), dict) else {},
        "stages": form_data.get("stages") if isinstance(form_data.get("stages"), list) else [],
        "layerItems": form_data.get("layerItems") if isinstance(form_data.get("layerItems"), dict) else {},
        "relationships": form_data.get("relationships") if isinstance(form_data.get("relationships"), list) else [],
        "problemSignals": form_data.get("problemSignals") if isinstance(form_data.get("problemSignals"), list) else [],
        "opportunities": form_data.get("opportunities") if isinstance(form_data.get("opportunities"), list) else [],
        "activeLayer": form_data.get("activeLayer"),
        "activeStage": form_data.get("activeStage"),
    }


def get_or_create_impact_state(db: sqlite3.Connection, session_id: str, journey_id: str | None, payload: dict, status: str) -> tuple[str, dict, int]:
    context = resolve_impact_context(db, session_id, journey_id)
    explicit_id = str(payload.get("impactJourneyStateId") or payload.get("id") or "")
    row = None
    if explicit_id:
        row = db.execute("SELECT * FROM impact_journey_states WHERE id = ? AND anonymous_session_id = ?", (explicit_id, session_id)).fetchone()
    if not row:
        row = db.execute(
            """
            SELECT * FROM impact_journey_states
            WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '') AND status IN ('draft', 'active')
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (session_id, context.get("journeyId")),
        ).fetchone()
    if row and row["status"] == "completed" and status != "completed":
        return row["id"], context, int(row["version_number"])
    if row:
        return row["id"], context, int(row["version_number"])
    version = 1
    latest = db.execute(
        "SELECT MAX(version_number) AS version FROM impact_journey_states WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '')",
        (session_id, context.get("journeyId")),
    ).fetchone()
    if latest and latest["version"]:
        version = int(latest["version"]) + 1
    return "impact-journey-" + secrets.token_hex(12), context, version


def clear_impact_children(db: sqlite3.Connection, state_id: str) -> None:
    stage_ids = [row["id"] for row in db.execute("SELECT id FROM impact_journey_stages WHERE impact_journey_state_id = ?", (state_id,)).fetchall()]
    loop_ids = [row["id"] for row in db.execute("SELECT id FROM journey_feedback_loops WHERE impact_journey_state_id = ?", (state_id,)).fetchall()]
    if stage_ids:
        placeholders = ",".join("?" for _ in stage_ids)
        for table in ["stage_activities", "stage_decisions", "stage_stakeholders", "journey_human_experiences"]:
            db.execute(f"DELETE FROM {table} WHERE stage_id IN ({placeholders})", stage_ids)
    if loop_ids:
        placeholders = ",".join("?" for _ in loop_ids)
        db.execute(f"DELETE FROM journey_feedback_loop_members WHERE feedback_loop_id IN ({placeholders})", loop_ids)
    for table in PAGE4_CHILD_TABLES:
        if table in {"stage_activities", "stage_decisions", "stage_stakeholders", "journey_human_experiences", "journey_feedback_loop_members"}:
            continue
        key = "impact_journey_state_id"
        db.execute(f"DELETE FROM {table} WHERE {key} = ?", (state_id,))
    db.execute("DELETE FROM impact_journey_stages WHERE impact_journey_state_id = ?", (state_id,))


def insert_impact_children(db: sqlite3.Connection, state_id: str, context: dict, form_data: dict, analysis: dict) -> dict:
    timestamp = now_iso()
    scope = impact_scope(form_data)
    stages = [stage for stage in form_data.get("stages", []) if isinstance(stage, dict)]
    layer_items = form_data.get("layerItems") if isinstance(form_data.get("layerItems"), dict) else {}
    stage_id_map: dict[str, str] = {}
    db.execute(
        """
        INSERT INTO journey_boundaries
        (id, impact_journey_state_id, boundary_name, boundary_description, organisational_scope, geographical_scope, temporal_scope,
         upstream_extent, downstream_extent, included_entities, excluded_entities, known_limitations, confidence, evidence_status,
         user_confirmed, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"boundary-{state_id}",
            state_id,
            str(scope.get("journeyType") or "Impact Journey boundary"),
            str(scope.get("insideBoundary") or ""),
            str(scope.get("primaryFocus") or ""),
            str(scope.get("geographicalScope") or ""),
            str(scope.get("timeframe") or ""),
            str(scope.get("startPoint") or ""),
            str(scope.get("endPoint") or ""),
            json.dumps(as_list(scope.get("insideBoundary"))),
            json.dumps(as_list(scope.get("outsideBoundary"))),
            str(scope.get("outsideBoundary") or ""),
            "medium",
            "user_supplied",
            1 if scope.get("startPoint") and scope.get("endPoint") else 0,
            timestamp,
            timestamp,
        ),
    )
    for index, stage in enumerate(stages, start=1):
        frontend_id = str(stage.get("id") or f"stage-{index}")
        stage_id = f"{state_id}-{slugify(frontend_id)}"
        stage_id_map[frontend_id] = stage_id
        db.execute(
            """
            INSERT INTO impact_journey_stages
            (id, impact_journey_state_id, title, description, stage_type, sequence, owner_stakeholder_id,
             is_system_generated, source_type, source_id, confidence, verification_status, user_confirmed, status,
             created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """,
            (
                stage_id,
                state_id,
                str(stage.get("name") or f"Stage {index}"),
                str(stage.get("description") or ""),
                derive_stage_type(str(stage.get("name") or "")),
                index,
                str(stage.get("owner") or ""),
                1 if stage.get("source") == "system-suggested" else 0,
                str(stage.get("source") or "user-entered"),
                frontend_id,
                str(stage.get("confidence") or "medium"),
                "unverified" if stage.get("source") == "system-suggested" else "user_confirmed",
                0 if stage.get("source") == "system-suggested" else 1,
                context["anonymousSessionId"],
                context["anonymousSessionId"],
                timestamp,
                timestamp,
                json.dumps({"frontendId": frontend_id}),
            ),
        )
        items = layer_items.get(frontend_id, {}) if isinstance(layer_items.get(frontend_id), dict) else {}
        for layer_key, entries in items.items():
            if not isinstance(entries, list):
                continue
            for item_index, item in enumerate([entry for entry in entries if isinstance(entry, dict)], start=1):
                item_id = f"{stage_id}-{slugify(layer_key)}-{slugify(str(item.get('id') or item_index))}"
                title = str(item.get("title") or f"{layer_key.title()} item")
                notes = str(item.get("notes") or "")
                confidence = str(item.get("confidence") or "medium")
                source = str(item.get("source") or "user-entered")
                user_confirmed = 0 if "system" in source.lower() else 1
                if layer_key == "activities":
                    db.execute("INSERT INTO stage_activities (id, stage_id, title, description, activity_type, source_type, source_id, confidence, verification_status, user_confirmed, status, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, 'custom', ?, ?, ?, 'unverified', ?, 'active', ?, ?, ?)", (item_id, stage_id, title, notes, source, str(item.get("id") or ""), confidence, user_confirmed, timestamp, timestamp, json.dumps(item)))
                elif layer_key == "decisions":
                    db.execute("INSERT INTO stage_decisions (id, stage_id, title, description, decision_type, confidence, evidence_status, source_type, source_id, user_confirmed, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'custom', ?, 'unverified', ?, ?, ?, 'active', ?, ?)", (item_id, stage_id, title, notes, confidence, source, str(item.get("id") or ""), user_confirmed, timestamp, timestamp))
                elif layer_key == "stakeholders":
                    db.execute("INSERT INTO stage_stakeholders (id, stage_id, stakeholder_id, stakeholder_name, relationship_type, role, influence_level, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, NULL, ?, 'is affected by', ?, 'unknown', ?, ?, ?, ?)", (item_id, stage_id, title, notes, confidence, user_confirmed, timestamp, timestamp))
                elif layer_key == "data":
                    db.execute("INSERT INTO journey_inputs (id, impact_journey_state_id, source_stage_id, destination_stage_id, input_type, name, description, data_quality, confidence, verification_status, user_confirmed, created_at, updated_at) VALUES (?, ?, NULL, ?, 'data', ?, ?, 'review', ?, 'unverified', ?, ?, ?)", (item_id, state_id, stage_id, title, notes, confidence, user_confirmed, timestamp, timestamp))
                    db.execute("INSERT INTO journey_evidence_links (id, impact_journey_state_id, stage_id, evidence_id, relationship_type, supports_or_challenges, relevance_notes, strength, confidence, verification_status, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, 'source_note', 'supports', ?, 'review', ?, 'unverified', ?, ?, ?)", (f"evidence-link-{item_id}", state_id, stage_id, item_id, notes, confidence, user_confirmed, timestamp, timestamp))
                elif layer_key == "experience":
                    db.execute("INSERT INTO journey_human_experiences (id, stage_id, stakeholder_name, experience_type, description, source_type, source_id, confidence, verification_status, user_confirmed, created_at, updated_at) VALUES (?, ?, '', 'mixed', ?, ?, ?, ?, 'unverified', ?, ?, ?)", (item_id, stage_id, f"{title}. {notes}".strip(), source, str(item.get("id") or ""), confidence, user_confirmed, timestamp, timestamp))
                elif layer_key in IMPACT_LAYER_TO_EMPATHY:
                    db.execute("INSERT INTO journey_impacts (id, impact_journey_state_id, stage_id, empathy_type, impact_category, title, description, direction, directness, confidence, evidence_status, verification_status, source_type, source_id, user_confirmed, status, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, 'custom', ?, ?, 'uncertain', 'unknown', ?, 'unverified', 'unverified', ?, ?, ?, 'active', ?, ?, ?)", (item_id, state_id, stage_id, IMPACT_LAYER_TO_EMPATHY[layer_key], title, notes, confidence, source, str(item.get("id") or ""), user_confirmed, timestamp, timestamp, json.dumps(item)))
                elif layer_key == "unknowns":
                    db.execute("INSERT INTO journey_unknowns (id, impact_journey_state_id, stage_id, question, unknown_type, importance, urgency, blocking_status, status, source_type, source_id, created_at, updated_at) VALUES (?, ?, ?, ?, 'missing data', 'review', 'review', 'not_blocking', 'open', ?, ?, ?, ?)", (item_id, state_id, stage_id, title if title.endswith("?") else f"What is not yet known about {title}?", source, str(item.get("id") or ""), timestamp, timestamp))
                    db.execute("INSERT INTO journey_assumptions (id, impact_journey_state_id, stage_id, statement, assumption_type, criticality, uncertainty_level, evidence_required, status, source_type, source_id, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, 'custom', 'review', 'medium', ?, 'unverified', ?, ?, ?, ?, ?, ?)", (f"assumption-{item_id}", state_id, stage_id, title, notes or "Evidence required before relying on this assumption.", source, str(item.get("id") or ""), confidence, user_confirmed, timestamp, timestamp))
                elif layer_key == "strengths":
                    db.execute("INSERT INTO journey_strengths (id, impact_journey_state_id, stage_id, title, description, strength_type, existing_capability, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'custom', ?, ?, ?, ?, ?)", (item_id, state_id, stage_id, title, notes, title, confidence, user_confirmed, timestamp, timestamp))
    for rel in [item for item in form_data.get("relationships", []) if isinstance(item, dict)]:
        source_stage_id = stage_id_map.get(str(rel.get("source") or ""))
        target_stage_id = stage_id_map.get(str(rel.get("target") or ""))
        if not source_stage_id or not target_stage_id or source_stage_id == target_stage_id:
            continue
        rel_id = f"relationship-{state_id}-{slugify(str(rel.get('id') or source_stage_id + target_stage_id + str(rel.get('type'))))}"
        rel_type = str(rel.get("type") or "depends_on").lower().replace(" ", "_")
        db.execute("INSERT INTO system_relationships (id, organisation_id, journey_id, impact_journey_state_id, source_object_type, source_object_id, target_object_type, target_object_id, relationship_type, direction, strength, confidence, rationale, evidence_status, user_confirmed, generator_version, created_at, updated_at) VALUES (?, ?, ?, ?, 'journey_stage', ?, 'journey_stage', ?, ?, 'forward', 'review', ?, ?, 'unverified', 1, NULL, ?, ?)", (rel_id, context.get("organisationId"), context.get("journeyId"), state_id, source_stage_id, target_stage_id, rel_type, str(rel.get("confidence") or "medium"), str(rel.get("description") or ""), timestamp, timestamp))
        if "bottleneck" in rel_type or "delay" in rel_type:
            db.execute("INSERT INTO journey_bottlenecks (id, impact_journey_state_id, stage_id, title, description, bottleneck_type, delay_created, severity, persistence, confidence, status, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'review', 'review', ?, 'draft', 1, ?, ?)", (f"bottleneck-{rel_id}", state_id, source_stage_id, rel.get("type") or "Bottleneck", str(rel.get("description") or ""), rel_type, str(rel.get("description") or ""), str(rel.get("confidence") or "medium"), timestamp, timestamp))
        if "dependency" in rel_type:
            db.execute("INSERT INTO journey_dependencies (id, impact_journey_state_id, source_object_type, source_object_id, target_object_type, target_object_id, dependency_type, criticality, substitutability, failure_consequence, confidence, verification_status, user_confirmed, created_at, updated_at) VALUES (?, ?, 'journey_stage', ?, 'journey_stage', ?, 'custom', 'review', 'unknown', ?, ?, 'unverified', 1, ?, ?)", (f"dependency-{rel_id}", state_id, source_stage_id, target_stage_id, str(rel.get("description") or ""), str(rel.get("confidence") or "medium"), timestamp, timestamp))
    for hotspot in analysis.get("hotspots", []):
        stage_id = stage_id_map.get(str(hotspot.get("stageId") or ""))
        db.execute("INSERT INTO hotspot_candidates (id, impact_journey_state_id, stage_id, title, description, hotspot_type, impact_dimensions, evidence_basis, rationale, severity, uncertainty, leverage_potential, confidence, generator_version, user_decision, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'review', ?, 'rules-page4-v1', 'pending_review', 'suggested', ?, ?)", (f"{state_id}-{hotspot['id']}", state_id, stage_id, hotspot["title"], hotspot["description"], hotspot["type"], json.dumps(hotspot.get("impactDimensions", [])), json.dumps(["mapped_layer_counts"]), hotspot["rationale"], hotspot["severity"], hotspot["uncertainty"], hotspot["confidence"], timestamp, timestamp))
    for point in analysis.get("leveragePoints", []):
        db.execute("INSERT INTO leverage_points (id, impact_journey_state_id, relationship_id, title, description, leverage_type, intervention_level, rationale, expected_influence, uncertainty, confidence, generator_version, user_decision, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'system_relationship', ?, ?, ?, ?, 'rules-page4-v1', 'pending_review', 'suggested', ?, ?)", (f"{state_id}-{point['id']}", state_id, point.get("relationshipId"), point["title"], point["description"], point["leverageType"], point["rationale"], point["expectedInfluence"], point["uncertainty"], point["confidence"], timestamp, timestamp))
    for signal in analysis.get("problemSignals", []):
        stage_id = stage_id_map.get(str(signal.get("stageId") or ""))
        db.execute("INSERT INTO impact_journey_problem_signals (id, impact_journey_state_id, stage_id, title, description, signal_type, source_type, source_id, evidence_basis, rationale, confidence, status, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'rules_page4', ?, ?, ?, ?, 'draft', 0, ?, ?)", (f"{state_id}-{signal['id']}", state_id, stage_id, signal["title"], signal["description"], signal["type"], signal.get("id"), json.dumps(["Page 3 import" if signal["type"] == "page3_import" else "mapped journey layers"]), signal["rationale"], signal["confidence"], timestamp, timestamp))
    for opp in [item for item in form_data.get("opportunities", []) if isinstance(item, dict)]:
        db.execute("INSERT INTO journey_opportunity_signals (id, impact_journey_state_id, title, description, opportunity_type, expected_value, potential_leverage, confidence, evidence_status, source_type, source_id, status, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, 'custom', 'review', 'review', ?, 'unverified', 'user_entered', ?, 'draft', 1, ?, ?)", (f"opportunity-{state_id}-{slugify(str(opp.get('id') or opp.get('title')))}", state_id, str(opp.get("title") or "Opportunity area"), str(opp.get("description") or ""), str(opp.get("confidence") or "low"), str(opp.get("id") or ""), timestamp, timestamp))
    return stage_id_map


def build_page5_handover(state_id: str, form_data: dict, analysis: dict, status: str) -> dict:
    scope = impact_scope(form_data)
    return {
        "source": {"page": "impact-journey", "impactJourneyStateId": state_id, "status": status, "generatedAt": now_iso()},
        "scope": scope,
        "stages": [{"id": stage.get("id"), "name": stage.get("name"), "confidence": stage.get("confidence")} for stage in form_data.get("stages", []) if isinstance(stage, dict)],
        "candidateProblems": analysis.get("problemSignals", []),
        "hotspots": analysis.get("hotspots", []),
        "leveragePoints": analysis.get("leveragePoints", []),
        "evidenceGaps": analysis.get("evidenceGaps", []),
        "priorityQuestions": analysis.get("priorityQuestions", []),
        "traceability": "Page 3 source bundle -> journey map rows -> hotspots -> problem signals for Sort and Prioritise.",
    }


def validate_impact_completion(form_data: dict, context: dict) -> dict:
    scope = impact_scope(form_data)
    stages = [stage for stage in form_data.get("stages", []) if isinstance(stage, dict)]
    layer_items = form_data.get("layerItems") if isinstance(form_data.get("layerItems"), dict) else {}
    errors = []
    warnings = []
    if not scope.get("journeyType"):
        errors.append("Journey type is required.")
    if not scope.get("startPoint") or not scope.get("endPoint"):
        errors.append("Journey boundary needs a start point and end point.")
    if not stages:
        errors.append("At least one journey stage is required.")
    if len(stages) < 3:
        errors.append("At least three journey stages are required for a usable map.")
    if stages and not any(layer_items.get(stage.get("id"), {}).get("activities") for stage in stages if isinstance(layer_items.get(stage.get("id")), dict)):
        errors.append("At least one activity must be mapped before completion.")
    if impact_completion(form_data) < 85:
        errors.append("Impact Journey is not ready to complete; scope, stages, activities, relationships, impacts/signals and review evidence are required.")
    if not context.get("journeyId"):
        warnings.append("No completed onboarding journey was found, so this remains an anonymous local Page 4 draft.")
    if not form_data.get("relationships"):
        warnings.append("No system relationships have been recorded yet.")
    if not form_data.get("problemSignals"):
        warnings.append("No user-reviewed Page 4 problem signals are present yet; generated signals will be marked as draft.")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def save_impact_journey(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    journey_id = str(payload.get("journeyId", "")) or None
    form_data = normalise_impact_form(payload)
    with connect() as db:
        seed_impact_categories(db)
        state_id, context, version = get_or_create_impact_state(db, session_id, journey_id, payload, status)
        existing = db.execute("SELECT status FROM impact_journey_states WHERE id = ?", (state_id,)).fetchone()
        if existing and existing["status"] == "completed" and status != "completed":
            return {"ok": False, "error": "Completed impact journeys must be reopened before editing.", "stateId": state_id}
        page3 = page3_source_bundle(db, session_id, context.get("journeyId"))
        analysis = analyse_impact_journey(form_data, page3)
        validation = validate_impact_completion(form_data, context) if status == "completed" else {"valid": True, "errors": [], "warnings": []}
        if status == "completed" and not validation["valid"]:
            return {"ok": False, "stateId": state_id, "validation": validation}
        timestamp = now_iso()
        scope = impact_scope(form_data)
        row = db.execute("SELECT autosave_revision, created_at FROM impact_journey_states WHERE id = ?", (state_id,)).fetchone()
        revision = int(row["autosave_revision"]) + 1 if row else 1
        created_at = row["created_at"] if row else timestamp
        final_status = "completed" if status == "completed" else "draft"
        db.execute(
            """
            INSERT OR REPLACE INTO impact_journey_states
            (id, anonymous_session_id, organisation_id, journey_id, methodology_version_id, version_number, title, description,
             scope_statement, scope_type, boundary_description, boundary_type, geographical_scope, time_horizon, upstream_boundary,
             downstream_boundary, source_page3_version_id, status, completion_percentage, current_section, autosave_revision,
             form_snapshot, analysis_snapshot, last_saved_at, completed_at, completed_by, created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id,
                session_id,
                context.get("organisationId"),
                context.get("journeyId"),
                context.get("methodologyVersionId"),
                version,
                str(scope.get("journeyType") or "Impact Journey Map"),
                str(scope.get("primaryFocus") or ""),
                f"{scope.get('startPoint', '')} to {scope.get('endPoint', '')}".strip(" to"),
                str(scope.get("primaryFocus") or scope.get("journeyType") or ""),
                str(scope.get("insideBoundary") or ""),
                str(scope.get("journeyType") or ""),
                str(scope.get("geographicalScope") or ""),
                str(scope.get("timeframe") or ""),
                str(scope.get("startPoint") or ""),
                str(scope.get("endPoint") or ""),
                page3.get("explore", {}).get("id") if isinstance(page3.get("explore"), dict) else None,
                final_status,
                impact_completion(form_data) if final_status != "completed" else 100,
                str(payload.get("currentSection") or form_data.get("activeLayer") or "scope"),
                revision,
                json.dumps(form_data),
                json.dumps(analysis),
                timestamp,
                timestamp if final_status == "completed" else None,
                session_id if final_status == "completed" else None,
                session_id,
                session_id,
                created_at,
                timestamp,
                json.dumps({"authMode": "anonymous-local", "warnings": validation.get("warnings", [])}),
            ),
        )
        clear_impact_children(db, state_id)
        insert_impact_children(db, state_id, context, form_data, analysis)
        handover = build_page5_handover(state_id, form_data, analysis, final_status)
        db.execute("INSERT OR REPLACE INTO stage_handover_manifests (id, impact_journey_state_id, target_stage_key, manifest, stale, created_at, updated_at) VALUES (?, ?, 'sort-prioritise', ?, 0, ?, ?)", (f"handover-page5-{state_id}", state_id, json.dumps(handover), timestamp, timestamp))
        if page3.get("found"):
            db.execute("INSERT INTO impact_journey_import_records (id, impact_journey_state_id, source_type, source_id, imported_payload, imported_count, conflict_count, stale_count, status, created_at) VALUES (?, ?, 'page3', ?, ?, ?, 0, 0, 'imported', ?)", ("import-" + secrets.token_hex(12), state_id, page3.get("explore", {}).get("id") if isinstance(page3.get("explore"), dict) else None, json.dumps(page3), len(page3.get("signals", [])) + len(page3.get("questions", [])), timestamp))
        if final_status == "completed":
            db.execute("UPDATE journey_progress SET status = 'completed', completion_percentage = 100, completed_at = ?, last_visited_at = ?, output_summary = ? WHERE journey_id = ? AND stage_key = 'map'", (timestamp, timestamp, json.dumps({"impactJourneyStateId": state_id, "hotspots": len(analysis.get("hotspots", [])), "problemSignals": len(analysis.get("problemSignals", []))}), context.get("journeyId")))
        db.execute("INSERT INTO audit_logs (id, actor_type, actor_id, action, entity_type, entity_id, metadata, occurred_at) VALUES (?, 'anonymous_session', ?, ?, 'impact_journey_state', ?, ?, ?)", ("audit-" + secrets.token_hex(12), session_id, "complete_impact_journey" if final_status == "completed" else "autosave_impact_journey", state_id, json.dumps({"status": final_status, "revision": revision}), timestamp))
    return {"ok": True, "stateId": state_id, "status": final_status, "versionNumber": version, "autosaveRevision": revision, "analysis": analysis, "handover": handover, "validation": validation}


def get_impact_journey(session_id: str, journey_id: str | None = None, state_id: str | None = None) -> dict:
    session_id = session_id[:80] or "anonymous-local"
    with connect() as db:
        row = None
        if state_id:
            row = db.execute("SELECT * FROM impact_journey_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            row = db.execute(
                """
                SELECT * FROM impact_journey_states
                WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '')
                ORDER BY CASE status WHEN 'draft' THEN 0 WHEN 'active' THEN 1 WHEN 'completed' THEN 2 ELSE 3 END, updated_at DESC
                LIMIT 1
                """,
                (session_id, journey_id),
            ).fetchone()
        context = resolve_impact_context(db, session_id, journey_id)
        page3 = page3_source_bundle(db, session_id, journey_id)
    if not row:
        suggested = impact_stage_suggestions(context)
        return {"ok": True, "found": False, "suggestedStages": suggested, "page3": page3, "context": context}
    return {
        "ok": True,
        "found": True,
        "stateId": row["id"],
        "status": row["status"],
        "versionNumber": row["version_number"],
        "formData": json_loads_safe(row["form_snapshot"], {}),
        "analysis": json_loads_safe(row["analysis_snapshot"], {}),
        "updatedAt": row["updated_at"],
        "suggestedStages": impact_stage_suggestions(context),
        "page3": page3,
        "context": context,
    }


def import_page3_to_impact(state_id: str, payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    with connect() as db:
        state = db.execute("SELECT id, journey_id FROM impact_journey_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not state:
            return {"ok": False, "error": "Impact journey state not found."}
        page3 = page3_source_bundle(db, session_id, state["journey_id"])
        timestamp = now_iso()
        db.execute("INSERT INTO impact_journey_import_records (id, impact_journey_state_id, source_type, source_id, imported_payload, imported_count, conflict_count, stale_count, status, created_at) VALUES (?, ?, 'page3', ?, ?, ?, 0, 0, 'imported', ?)", ("import-" + secrets.token_hex(12), state_id, page3.get("explore", {}).get("id") if isinstance(page3.get("explore"), dict) else None, json.dumps(page3), len(page3.get("signals", [])) + len(page3.get("questions", [])), timestamp))
    return {"ok": True, "stateId": state_id, "page3": page3}


def reopen_impact_journey(state_id: str, payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    reason = str(payload.get("revisionReason") or "Reopened for editing")
    with connect() as db:
        row = db.execute("SELECT * FROM impact_journey_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            return {"ok": False, "error": "Impact journey state not found."}
        new_id = "impact-journey-" + secrets.token_hex(12)
        version = int(row["version_number"]) + 1
        timestamp = now_iso()
        db.execute(
            """
            INSERT INTO impact_journey_states
            (id, anonymous_session_id, organisation_id, journey_id, methodology_version_id, version_number, title, description,
             scope_statement, scope_type, boundary_description, boundary_type, geographical_scope, time_horizon, upstream_boundary,
             downstream_boundary, includes_enabling_functions, includes_external_partners, source_page3_version_id, status,
             completion_percentage, current_section, autosave_revision, form_snapshot, analysis_snapshot, last_saved_at,
             reopened_at, reopened_by, revision_reason, created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id, row["anonymous_session_id"], row["organisation_id"], row["journey_id"], row["methodology_version_id"], version, row["title"], row["description"], row["scope_statement"], row["scope_type"], row["boundary_description"], row["boundary_type"], row["geographical_scope"], row["time_horizon"], row["upstream_boundary"], row["downstream_boundary"], row["includes_enabling_functions"], row["includes_external_partners"], row["source_page3_version_id"], row["completion_percentage"], row["current_section"], row["form_snapshot"], row["analysis_snapshot"], timestamp, timestamp, session_id, reason, session_id, session_id, timestamp, timestamp, row["metadata"]),
        )
        db.execute("UPDATE stage_handover_manifests SET stale = 1, updated_at = ? WHERE impact_journey_state_id = ?", (timestamp, state_id))
    return {"ok": True, "stateId": new_id, "versionNumber": version, "status": "draft"}


def export_impact_journey(state_id: str, session_id: str) -> dict:
    data = get_impact_journey(session_id, state_id=state_id)
    if not data.get("found"):
        return {"ok": False, "error": "Impact journey state not found."}
    with connect() as db:
        counts = {}
        for table in ["impact_journey_stages", "stage_activities", "stage_decisions", "stage_stakeholders", "journey_impacts", "system_relationships", "hotspot_candidates", "leverage_points", "impact_journey_problem_signals"]:
            key = "impact_journey_state_id"
            if table in {"stage_activities", "stage_decisions", "stage_stakeholders"}:
                count = db.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE stage_id IN (SELECT id FROM impact_journey_stages WHERE impact_journey_state_id = ?)", (state_id,)).fetchone()["count"]
            else:
                count = db.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE {key} = ?", (state_id,)).fetchone()["count"]
            counts[table] = count
    return {"ok": True, "exportedAt": now_iso(), "format": "green-spectrum-impact-journey-json-v1", "counts": counts, **data}


def page5_handover(state_id: str, session_id: str) -> dict:
    session_id = session_id[:80] or "anonymous-local"
    with connect() as db:
        row = db.execute(
            """
            SELECT m.manifest, m.stale, m.updated_at
            FROM stage_handover_manifests m
            JOIN impact_journey_states s ON s.id = m.impact_journey_state_id
            WHERE m.impact_journey_state_id = ? AND s.anonymous_session_id = ? AND m.target_stage_key = 'sort-prioritise'
            ORDER BY m.updated_at DESC
            LIMIT 1
            """,
            (state_id, session_id),
        ).fetchone()
    if not row:
        return {"ok": False, "error": "Page 5 handover not found."}
    return {"ok": True, "handover": json_loads_safe(row["manifest"], {}), "stale": bool(row["stale"]), "updatedAt": row["updated_at"]}


PAGE5_CHILD_TABLES = [
    "problem_signal_links",
    "problem_evidence_links",
    "problem_stakeholders",
    "problem_ecosystems",
    "problem_statements",
    "root_cause_assessments",
    "maturity_positioning",
    "maturity_classification_responses",
    "problem_maturity_dimensions",
    "complexity_assessments",
    "complexity_classification_responses",
    "priority_assessments",
    "priority_scores",
    "priority_recommendations",
    "problem_opportunity_branches",
]

PRIORITY_DIMENSION_MAP = {
    "impact": "impact",
    "urgency": "urgency",
    "effort": "effort",
    "readiness": "readiness",
    "influence": "influence",
    "strategic": "strategic_alignment",
    "stakeholder": "stakeholder_concern",
    "leverage": "systems_leverage",
    "confidence": "evidence_confidence",
    "learning": "learning_value",
}

DEFAULT_PRIORITY_WEIGHTS = {
    "impact": 20,
    "strategic": 15,
    "leverage": 15,
    "urgency": 10,
    "influence": 10,
    "readiness": 10,
    "confidence": 10,
    "stakeholder": 5,
    "learning": 5,
    "effort": 10,
}

SPECTRUM_LEVELS = {"white", "light", "mid", "dark", "unsure", "light_green", "mid_green", "dark_green", "uncertain"}
CYNEFIN_DOMAINS = {"clear", "complicated", "complex", "chaotic", "confused", "mixed"}


def seed_response_archetypes(db: sqlite3.Connection) -> None:
    timestamp = now_iso()
    titles = {
        "clear": ("Standard control", "Use repeatable practice with a named owner."),
        "complicated": ("Expert analysis", "Use specialist analysis and compare valid options."),
        "complex": ("Adaptive experiment", "Probe safely, learn, and adjust through feedback."),
        "chaotic": ("Stabilise first", "Contain harm before attempting detailed optimisation."),
        "confused": ("Clarify first", "Gather evidence, clarify ownership, and reclassify."),
        "mixed": ("Mixed route", "Separate the parts before choosing a response route."),
    }
    for level in ["white", "light", "mid", "dark"]:
        for domain, (title, description) in titles.items():
            archetype_id = f"archetype-{level}-{domain}"
            methods = {
                "clear": ["process mapping", "owner assignment", "routine monitoring"],
                "complicated": ["expert analysis", "scenario comparison", "technical assessment"],
                "complex": ["systems mapping", "stakeholder engagement", "safe-to-fail experiment"],
                "chaotic": ["rapid control", "escalation", "short decision cycle"],
                "confused": ["discovery sprint", "evidence review", "problem reframing"],
                "mixed": ["decompose problem", "route sub-problems", "review assumptions"],
            }[domain]
            db.execute(
                """
                INSERT OR IGNORE INTO response_archetypes
                (id, maturity_level, cynefin_domain, title, description, recommended_response, typical_methods,
                 prerequisites, warnings, default_decision_route, rule_version, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'rules-page5-v1', 1, ?, ?)
                """,
                (
                    archetype_id,
                    level,
                    domain,
                    f"{level.title()} + {title}",
                    description,
                    title,
                    json.dumps(methods),
                    json.dumps(["review evidence", "confirm user judgement"]),
                    json.dumps(["suggested route only", "not a final intervention"]),
                    title,
                    timestamp,
                    timestamp,
                ),
            )


def confidence_number(value: object) -> int:
    if isinstance(value, (int, float)):
        return max(1, min(5, int(value)))
    lower = str(value or "").lower()
    if lower in {"high", "very high"}:
        return 4
    if lower == "medium":
        return 3
    if lower == "low":
        return 2
    if lower in {"assumption", "not_assessed", "unknown"}:
        return 1
    return 2


def score_label(score: int | float | None) -> str:
    labels = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
    return labels.get(max(1, min(5, int(score or 3))), "Moderate")


def cluster_from_text(text: str) -> str:
    lower = text.lower()
    if "supplier" in lower or "supply" in lower:
        return "Operations and value chain"
    if "data" in lower or "evidence" in lower or "report" in lower:
        return "Data and measurement"
    if "governance" in lower or "ownership" in lower:
        return "Strategy and governance"
    if "employee" in lower or "culture" in lower or "behaviour" in lower:
        return "People and culture"
    if any(word in lower for word in ["climate", "waste", "nature", "material", "ecosystem"]):
        return "Climate and nature"
    return "Strategy and governance"


def suggest_priority_spectrum(text: str) -> tuple[str, str]:
    lower = text.lower()
    if "regenerative" in lower or "ecosystem" in lower or "justice" in lower or "nature" in lower:
        return "dark", "Suggested as Dark Green because the problem appears to involve system-level, justice, nature or regenerative change."
    if "redesign" in lower or "supplier" in lower or "traceability" in lower or "culture" in lower or "business model" in lower:
        return "mid", "Suggested as Mid Green because the problem appears to require organisational redesign or cross-system coordination."
    if "report" in lower or "data" in lower or "waste" in lower or "energy" in lower or "compliance" in lower:
        return "light", "Suggested as Light Green because the problem appears to involve compliance, evidence, transparency or harm reduction."
    return "white", "Suggested as White because the problem appears to need foundational ownership, evidence or recognition first."


def suggest_priority_cynefin(text: str, confidence: int) -> tuple[str, str]:
    lower = text.lower()
    if "crisis" in lower or "disruption" in lower or "immediate harm" in lower:
        return "chaotic", "Suggested as Chaotic because the problem language implies instability or immediate containment needs."
    if any(word in lower for word in ["culture", "behaviour", "stakeholder", "supplier", "system"]):
        return "complex", "Suggested as Complex because it involves interacting actors, behaviours or relationships where outcomes may emerge over time."
    if any(word in lower for word in ["material", "product", "analysis", "technical", "lca"]):
        return "complicated", "Suggested as Complicated because expert analysis could reduce uncertainty."
    if confidence <= 2:
        return "confused", "Suggested as Confused because evidence confidence is low and the problem needs clarification."
    return "clear", "Suggested as Clear because cause and effect appear visible enough for structured response."


def suggest_priority_scores(text: str, confidence: int) -> dict:
    lower = text.lower()
    return {
        "impact": 4 if any(word in lower for word in ["supplier", "climate", "waste", "risk", "harm"]) else 3,
        "effort": 4 if any(word in lower for word in ["system", "supplier", "culture", "redesign"]) else 2,
        "strategic": 5 if any(word in lower for word in ["strategy", "supplier", "governance", "regulation"]) else 3,
        "urgency": 4 if any(word in lower for word in ["regulation", "risk", "incomplete", "deadline"]) else 3,
        "confidence": confidence,
        "readiness": 2 if any(word in lower for word in ["capability", "ownership", "fragmented"]) else 3,
        "influence": 3 if any(word in lower for word in ["external", "supplier", "market"]) else 4,
        "leverage": 5 if any(word in lower for word in ["data", "governance", "supplier", "ownership"]) else 3,
        "stakeholder": 4 if any(word in lower for word in ["employee", "community", "customer", "justice"]) else 3,
        "learning": 5 if any(word in lower for word in ["uncertain", "culture", "experiment", "unknown"]) else 3,
    }


def calculate_priority_score(problem: dict, weights: dict) -> int:
    scores = problem.get("scores") if isinstance(problem.get("scores"), dict) else {}
    w = {**DEFAULT_PRIORITY_WEIGHTS, **{key: int(value) for key, value in weights.items() if str(value).isdigit()}} if isinstance(weights, dict) else DEFAULT_PRIORITY_WEIGHTS
    positive = sum((int(scores.get(key) or 3) * int(w.get(key, 0))) for key in ["impact", "strategic", "leverage", "urgency", "influence", "readiness", "confidence", "stakeholder", "learning"])
    penalty = int(scores.get("effort") or 3) * int(w.get("effort", 10))
    return max(0, round((positive - penalty) / 5))


def score_contributions(problem: dict, weights: dict) -> dict:
    scores = problem.get("scores") if isinstance(problem.get("scores"), dict) else {}
    w = {**DEFAULT_PRIORITY_WEIGHTS, **{key: int(value) for key, value in weights.items() if str(value).isdigit()}} if isinstance(weights, dict) else DEFAULT_PRIORITY_WEIGHTS
    positive_keys = ["impact", "strategic", "leverage", "urgency", "influence", "readiness", "confidence", "stakeholder", "learning"]
    contributions = []
    for key in positive_keys:
        score = int(scores.get(key) or 3)
        weight = int(w.get(key, 0))
        contributions.append({
            "factor": key,
            "score": score,
            "weight": weight,
            "contribution": score * weight,
            "direction": "raises" if score >= 4 else "limits" if score <= 2 else "neutral",
            "explanation": f"{key.replace('_', ' ').title()} is {score_label(score).lower()} and carries weight {weight}.",
        })
    effort_score = int(scores.get("effort") or 3)
    effort_weight = int(w.get("effort", 10))
    contributions.append({
        "factor": "effort",
        "score": effort_score,
        "weight": effort_weight,
        "contribution": -(effort_score * effort_weight),
        "direction": "lowers" if effort_score >= 4 else "supports feasibility" if effort_score <= 2 else "neutral",
        "explanation": f"Effort is {score_label(effort_score).lower()} and is treated as a delivery penalty.",
    })
    return {
        "formula": "weighted positive factors minus effort penalty, divided by five",
        "overall": problem.get("overall", calculate_priority_score(problem, weights)),
        "contributions": contributions,
        "topPositiveFactors": [item["factor"] for item in sorted([c for c in contributions if c["contribution"] > 0], key=lambda c: c["contribution"], reverse=True)[:3]],
        "mainConstraints": [item["factor"] for item in contributions if item["direction"] in {"limits", "lowers"}],
    }


def evidence_trace_for_problem(problem: dict) -> dict:
    title = str(problem.get("title") or "")
    description = str(problem.get("description") or "")
    cluster = str(problem.get("cluster") or "")
    text = f"{title} {description} {cluster}".lower()
    business_terms = ["cost", "strategy", "customer", "procurement", "supplier", "risk", "regulation", "operations", "finance", "quality"]
    human_terms = ["employee", "worker", "customer", "community", "patient", "fair", "access", "safety", "wellbeing", "stakeholder", "labour"]
    planetary_terms = ["carbon", "emissions", "waste", "water", "nature", "biodiversity", "energy", "material", "soil", "climate"]
    trace = {
        "business": [term for term in business_terms if term in text][:4],
        "human": [term for term in human_terms if term in text][:4],
        "planetary": [term for term in planetary_terms if term in text][:4],
        "source": str(problem.get("source") or "unknown"),
        "sourceObjectId": str(problem.get("sourceObjectId") or problem.get("id") or ""),
        "sourceStages": as_list(problem.get("relatedStages")),
        "evidenceSummary": str(problem.get("evidence") or "No explicit evidence summary supplied."),
        "confidence": confidence_number(problem.get("confidence")),
    }
    trace["missingPerspectives"] = [key for key in ["business", "human", "planetary"] if not trace[key]]
    trace["integrationStatus"] = "balanced" if not trace["missingPerspectives"] else "needs explicit review"
    return trace


def priority_category(problem: dict) -> str:
    scores = problem.get("scores", {})
    if problem.get("cynefin") == "chaotic":
        return "stabilise"
    if scores.get("confidence", 3) <= 2 and scores.get("impact", 3) >= 4:
        return "investigate"
    if problem.get("cynefin") == "complex":
        return "experiment"
    if scores.get("impact", 3) >= 4 and scores.get("readiness", 3) >= 3 and scores.get("effort", 3) <= 2:
        return "act_now"
    if scores.get("readiness", 3) <= 2:
        return "build_capability"
    return "monitor" if scores.get("urgency", 3) <= 2 else "collaborate" if scores.get("influence", 3) <= 3 else "act_now"


def recommendation_explanation(problem: dict, weights: dict) -> dict:
    trace = evidence_trace_for_problem(problem)
    score_trace = score_contributions(problem, weights)
    category = priority_category(problem)
    factors = ", ".join(score_trace["topPositiveFactors"]) or "the balanced score"
    missing = ", ".join(trace["missingPerspectives"]) if trace["missingPerspectives"] else "none"
    why = (
        f"{category.replace('_', ' ').title()} is suggested because {factors} are the strongest score drivers, "
        f"while the problem is classified as {problem.get('cynefin')} and {problem.get('spectrum')} green."
    )
    if score_trace["mainConstraints"]:
        why += f" The main constraint is {', '.join(score_trace['mainConstraints'])}."
    if trace["missingPerspectives"]:
        why += f" Missing perspective evidence: {missing}."
    return {
        "category": category,
        "whyThis": why,
        "sourceEvidence": trace,
        "scoreTrace": score_trace,
        "uncertainty": "Low-confidence or missing perspective evidence should be tested before scaling." if trace["missingPerspectives"] or trace["confidence"] <= 2 else "Residual assumptions should be reviewed before acting.",
        "excludedBecause": "Not excluded; included in ranked portfolio for user review.",
    }


def assign_priority_archetypes(problem: dict) -> list[str]:
    scores = problem.get("scores") if isinstance(problem.get("scores"), dict) else {}
    types = []
    if scores.get("impact", 3) >= 4 and scores.get("effort", 3) <= 2 and scores.get("confidence", 3) >= 3 and scores.get("readiness", 3) >= 3:
        types.append("quick-win")
    if scores.get("impact", 3) >= 4 and scores.get("strategic", 3) >= 4 and scores.get("effort", 3) >= 3:
        types.append("strategic-programme")
    if scores.get("confidence", 3) <= 2:
        types.append("research-needed")
    if problem.get("cynefin") == "complex":
        types.append("experiment-first")
    if scores.get("strategic", 3) >= 4 and scores.get("readiness", 3) <= 2:
        types.append("build-capability")
    if scores.get("leverage", 3) >= 4:
        types.append("system-leverage-point")
    if problem.get("cynefin") == "chaotic":
        types.append("crisis-response")
    if scores.get("urgency", 3) <= 2 and scores.get("impact", 3) <= 2:
        types.append("pause-monitor")
    return types or ["strategic-programme"]


def next_priority_move(problem: dict) -> str:
    if problem.get("cynefin") == "complex":
        return "Design experiment"
    if problem.get("cynefin") == "confused" or confidence_number(problem.get("confidence")) <= 2:
        return "Gather evidence first"
    if problem.get("scores", {}).get("readiness", 3) <= 2:
        return "Build capability first"
    if problem.get("cynefin") == "chaotic":
        return "Stabilise immediately"
    return "Proceed to structured decision"


def normalise_priority_form(payload: dict) -> dict:
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    if not form_data and isinstance(payload.get("state"), dict):
        form_data = payload["state"]
    return {
        "id": form_data.get("id") or form_data.get("stateId") or "",
        "problems": form_data.get("problems") if isinstance(form_data.get("problems"), list) else [],
        "weights": form_data.get("weights") if isinstance(form_data.get("weights"), dict) else DEFAULT_PRIORITY_WEIGHTS,
        "selectedIds": form_data.get("selectedIds") if isinstance(form_data.get("selectedIds"), list) else [],
        "reviewed": bool(form_data.get("reviewed") or form_data.get("priorityReviewed")),
        "sourceImpactJourneyStateId": form_data.get("sourceImpactJourneyStateId") or payload.get("sourceImpactJourneyStateId"),
    }


def latest_page4_handover(db: sqlite3.Connection, session_id: str, journey_id: str | None = None) -> dict:
    row = None
    source_state_id = ""
    if journey_id:
        row = db.execute(
            """
            SELECT m.manifest, m.stale, m.updated_at, s.id AS state_id, s.version_number
            FROM stage_handover_manifests m
            JOIN impact_journey_states s ON s.id = m.impact_journey_state_id
            WHERE s.anonymous_session_id = ? AND COALESCE(s.journey_id, '') = COALESCE(?, '') AND m.target_stage_key = 'sort-prioritise'
            ORDER BY s.updated_at DESC
            LIMIT 1
            """,
            (session_id, journey_id),
        ).fetchone()
    if not row:
        row = db.execute(
            """
            SELECT m.manifest, m.stale, m.updated_at, s.id AS state_id, s.version_number
            FROM stage_handover_manifests m
            JOIN impact_journey_states s ON s.id = m.impact_journey_state_id
            WHERE s.anonymous_session_id = ? AND m.target_stage_key = 'sort-prioritise'
            ORDER BY s.updated_at DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    if row:
        source_state_id = row["state_id"]
        return {"found": True, "sourceImpactJourneyStateId": source_state_id, "versionNumber": row["version_number"], "handover": json_loads_safe(row["manifest"], {}), "stale": bool(row["stale"]), "updatedAt": row["updated_at"]}
    return {"found": False, "sourceImpactJourneyStateId": "", "handover": {}, "stale": False}


def import_priority_problems_from_sources(db: sqlite3.Connection, session_id: str, journey_id: str | None, source_impact_id: str | None = None) -> tuple[list[dict], dict]:
    page4 = latest_page4_handover(db, session_id, journey_id)
    problems: list[dict] = []
    if page4.get("found"):
        handover = page4.get("handover", {}) if isinstance(page4.get("handover"), dict) else {}
        for index, signal in enumerate(handover.get("candidateProblems", []) if isinstance(handover.get("candidateProblems"), list) else []):
            if not isinstance(signal, dict):
                continue
            problems.append({
                "id": f"impact-{signal.get('id') or index}",
                "title": str(signal.get("title") or "Impact Journey problem signal"),
                "description": str(signal.get("description") or "Mapped issue requiring prioritisation."),
                "source": "Impact Journey",
                "sourceObjectId": str(signal.get("id") or ""),
                "confidence": confidence_number(signal.get("confidence")),
                "status": "unreviewed",
                "cluster": cluster_from_text(f"{signal.get('title', '')} {signal.get('description', '')}"),
                "evidence": str(signal.get("rationale") or "Impact Journey handover"),
                "relatedStages": as_list(signal.get("stageId")),
                "sourceImpactJourneyStateId": page4.get("sourceImpactJourneyStateId"),
            })
        for index, hotspot in enumerate(handover.get("hotspots", []) if isinstance(handover.get("hotspots"), list) else []):
            if not isinstance(hotspot, dict) or any(problem["title"] == hotspot.get("title") for problem in problems):
                continue
            problems.append({
                "id": f"hotspot-{hotspot.get('id') or index}",
                "title": str(hotspot.get("title") or "Journey hotspot"),
                "description": str(hotspot.get("description") or "Hotspot requires review before selecting interventions."),
                "source": "Impact Journey",
                "sourceObjectId": str(hotspot.get("id") or ""),
                "confidence": confidence_number(hotspot.get("confidence")),
                "status": "unreviewed",
                "cluster": cluster_from_text(f"{hotspot.get('title', '')} {' '.join(as_list(hotspot.get('impactDimensions')))}"),
                "evidence": str(hotspot.get("rationale") or "Impact hotspot"),
                "relatedStages": as_list(hotspot.get("stageId")),
                "sourceImpactJourneyStateId": page4.get("sourceImpactJourneyStateId"),
            })
    page3 = page3_source_bundle(db, session_id, journey_id)
    for index, signal in enumerate(page3.get("signals", [])[:10]):
        if not isinstance(signal, dict):
            continue
        title = str(signal.get("title") or "")
        if not title or any(problem["title"] == title for problem in problems):
            continue
        problems.append({
            "id": f"explore-{slugify(title)}-{index}",
            "title": title,
            "description": str(signal.get("description") or "Explore finding requiring prioritisation."),
            "source": "Explore and Map",
            "sourceObjectId": str(signal.get("source") or ""),
            "confidence": confidence_number(signal.get("confidence")),
            "status": "unreviewed",
            "cluster": cluster_from_text(title),
            "evidence": str(signal.get("source") or "Explore output"),
            "relatedStages": [],
        })
    if not problems:
        for index, description in enumerate([
            "Supplier sustainability expectations exist because traceability and evidence remain incomplete, leading to weak Scope 3 confidence and delayed decisions.",
            "Packaging waste remains high because product design and end-of-life ownership are disconnected, leading to avoidable material loss.",
            "Sustainability governance exists because accountability is not linked to operational decision points, leading to inconsistent delivery.",
            "Employee engagement is uneven because sustainability responsibilities are unclear, leading to low participation and missed learning.",
            "Data ownership is fragmented because systems are managed across separate teams, leading to slow reporting and weak prioritisation.",
        ], start=1):
            problems.append({"id": f"demo-{index}", "title": description.split(" because ")[0], "description": description, "source": "System-generated demo", "confidence": 2 if index > 1 else 3, "status": "unreviewed", "cluster": cluster_from_text(description), "evidence": "Development fallback; replace with Page 4 handover", "relatedStages": []})
    return [enrich_priority_problem(problem, DEFAULT_PRIORITY_WEIGHTS) for problem in problems], page4


def enrich_priority_problem(problem: dict, weights: dict) -> dict:
    text = f"{problem.get('title', '')} {problem.get('description', '')} {problem.get('cluster', '')}"
    confidence = confidence_number(problem.get("confidence"))
    spectrum, spectrum_rationale = suggest_priority_spectrum(text)
    cynefin, cynefin_rationale = suggest_priority_cynefin(text, confidence)
    enriched = {
        **problem,
        "confidence": confidence,
        "cluster": problem.get("cluster") or cluster_from_text(text),
        "spectrum": problem.get("spectrum") or spectrum,
        "spectrumRationale": problem.get("spectrumRationale") or spectrum_rationale,
        "cynefin": problem.get("cynefin") or cynefin,
        "cynefinRationale": problem.get("cynefinRationale") or cynefin_rationale,
        "scores": problem.get("scores") if isinstance(problem.get("scores"), dict) else suggest_priority_scores(text, confidence),
    }
    enriched["overall"] = calculate_priority_score(enriched, weights)
    enriched["archetypes"] = assign_priority_archetypes(enriched)
    return enriched


def analyse_priority_state(form_data: dict) -> dict:
    weights = form_data.get("weights") if isinstance(form_data.get("weights"), dict) else DEFAULT_PRIORITY_WEIGHTS
    problems = [enrich_priority_problem(problem, weights) for problem in form_data.get("problems", []) if isinstance(problem, dict)]
    for problem in problems:
        problem["evidenceTrace"] = evidence_trace_for_problem(problem)
        problem["scoreTrace"] = score_contributions(problem, weights)
    selected_ids = set(as_list(form_data.get("selectedIds")))
    ranked = sorted([problem for problem in problems if problem.get("status") != "archived"], key=lambda item: item.get("overall", 0), reverse=True)
    duplicate_pairs = []
    for i, first in enumerate(problems):
        for second in problems[i + 1:]:
            shared_cluster = first.get("cluster") and first.get("cluster") == second.get("cluster")
            shared_word = set(str(first.get("title", "")).lower().split()) & set(str(second.get("title", "")).lower().split())
            if shared_cluster or len(shared_word) >= 3:
                duplicate_pairs.append({"a": first.get("id"), "b": second.get("id"), "similarity": 0.78 if shared_cluster else 0.62, "rationale": "Suggested because the problems share cluster, wording or source context."})
    selected = [problem for problem in problems if problem.get("id") in selected_ids]
    warnings = []
    if len(selected) > 5:
        warnings.append("More than five problems are selected. Reduce the list to create focus.")
    if selected and all(problem.get("scores", {}).get("effort", 3) >= 4 for problem in selected):
        warnings.append("All selected problems are high-effort, which may create delivery capacity risk.")
    if selected and not any("people" in f"{problem.get('cluster')} {problem.get('title')}".lower() or "culture" in f"{problem.get('cluster')} {problem.get('title')}".lower() for problem in selected):
        warnings.append("No selected problem clearly addresses Human Empathy findings.")
    if len([problem for problem in selected if confidence_number(problem.get("confidence")) <= 2]) >= 3:
        warnings.append("Several selected problems depend on weak evidence.")
    recommendations = []
    for problem in ranked:
        explanation = recommendation_explanation(problem, weights)
        recommendations.append({
            "problemId": problem.get("id"),
            "category": explanation["category"],
            "action": next_priority_move(problem),
            "rationale": explanation["whyThis"],
            "confidence": "high" if confidence_number(problem.get("confidence")) >= 4 else "medium" if confidence_number(problem.get("confidence")) == 3 else "low",
            "whyThis": explanation["whyThis"],
            "sourceEvidence": explanation["sourceEvidence"],
            "scoreTrace": explanation["scoreTrace"],
            "uncertainty": explanation["uncertainty"],
            "excludedBecause": explanation["excludedBecause"],
        })
    clusters: dict[str, list[dict]] = {}
    for problem in problems:
        clusters.setdefault(str(problem.get("cluster") or "Unclustered"), []).append(problem)
    integration = []
    for problem in ranked:
        trace = problem.get("evidenceTrace", {})
        integration.append({
            "problemId": problem.get("id"),
            "title": problem.get("title"),
            "businessEvidence": trace.get("business", []),
            "humanEvidence": trace.get("human", []),
            "planetaryEvidence": trace.get("planetary", []),
            "missingPerspectives": trace.get("missingPerspectives", []),
            "status": trace.get("integrationStatus", "needs explicit review"),
        })
    return {
        "problems": problems,
        "rankedProblemIds": [problem.get("id") for problem in ranked],
        "duplicatePairs": duplicate_pairs[:12],
        "portfolioWarnings": warnings,
        "recommendations": recommendations,
        "clusters": [{"title": title, "problemIds": [problem.get("id") for problem in members], "rationale": "Grouped by shared topic, stage or capability language.", "confidence": "medium"} for title, members in clusters.items()],
        "threeEmpathiesIntegration": integration,
        "scoringModel": {"formula": "weighted positive factors minus effort penalty, divided by five", "weights": weights, "scale": "1 low to 5 high; effort lowers the final priority score"},
        "selectedProblems": selected,
        "completionPercentage": priority_completion(form_data),
    }


def priority_completion(form_data: dict) -> int:
    problems = form_data.get("problems") if isinstance(form_data.get("problems"), list) else []
    selected = as_list(form_data.get("selectedIds"))
    complete = [
        bool(problems),
        any(problem.get("status") in {"confirmed", "selected"} for problem in problems if isinstance(problem, dict)),
        all(problem.get("spectrum") for problem in problems if isinstance(problem, dict)),
        all(problem.get("cynefin") for problem in problems if isinstance(problem, dict)),
        bool(form_data.get("weights")),
        1 <= len(selected) <= 5,
        bool(selected),
        bool(form_data.get("reviewed")),
    ]
    return round((len([item for item in complete if item]) / 8) * 100)


def resolve_priority_context(db: sqlite3.Connection, session_id: str, journey_id: str | None = None) -> dict:
    context = resolve_impact_context(db, session_id, journey_id)
    return context


def get_or_create_priority_state(db: sqlite3.Connection, session_id: str, journey_id: str | None, payload: dict) -> tuple[str, dict, int]:
    context = resolve_priority_context(db, session_id, journey_id)
    explicit_id = str(payload.get("priorityStateId") or payload.get("id") or "")
    row = None
    if explicit_id:
        row = db.execute("SELECT * FROM priority_states WHERE id = ? AND anonymous_session_id = ?", (explicit_id, session_id)).fetchone()
    if not row:
        row = db.execute(
            """
            SELECT * FROM priority_states
            WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '') AND status IN ('draft', 'active')
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (session_id, context.get("journeyId")),
        ).fetchone()
    if row:
        return row["id"], context, int(row["version_number"])
    latest = db.execute("SELECT MAX(version_number) AS version FROM priority_states WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '')", (session_id, context.get("journeyId"))).fetchone()
    version = int(latest["version"] or 0) + 1 if latest else 1
    return "priority-" + secrets.token_hex(12), context, version


def clear_priority_children(db: sqlite3.Connection, state_id: str) -> None:
    problem_ids = [row["id"] for row in db.execute("SELECT id FROM problems WHERE priority_state_id = ?", (state_id,)).fetchall()]
    portfolio_ids = [row["id"] for row in db.execute("SELECT id FROM priority_portfolios WHERE priority_state_id = ?", (state_id,)).fetchall()]
    cluster_ids = [row["id"] for row in db.execute("SELECT id FROM priority_clusters WHERE priority_state_id = ?", (state_id,)).fetchall()]
    if problem_ids:
        placeholders = ",".join("?" for _ in problem_ids)
        for table in PAGE5_CHILD_TABLES:
            db.execute(f"DELETE FROM {table} WHERE problem_id IN ({placeholders})", problem_ids)
    if portfolio_ids:
        placeholders = ",".join("?" for _ in portfolio_ids)
        db.execute(f"DELETE FROM priority_portfolio_items WHERE priority_portfolio_id IN ({placeholders})", portfolio_ids)
    if cluster_ids:
        placeholders = ",".join("?" for _ in cluster_ids)
        db.execute(f"DELETE FROM priority_cluster_members WHERE cluster_id IN ({placeholders})", cluster_ids)
    for table in ["problem_relationships", "problem_merge_candidates", "priority_weighting_profile_dimensions", "priority_weighting_profiles", "priority_recommendations", "priority_clusters", "priority_portfolios", "decision_rationales", "prioritisation_import_records", "page6_handover_manifests", "problem_signals"]:
        key = "priority_state_id"
        if table == "priority_weighting_profile_dimensions":
            db.execute("DELETE FROM priority_weighting_profile_dimensions WHERE weighting_profile_id IN (SELECT id FROM priority_weighting_profiles WHERE priority_state_id = ?)", (state_id,))
            continue
        if table == "priority_recommendations":
            continue
        db.execute(f"DELETE FROM {table} WHERE {key} = ?", (state_id,))
    db.execute("DELETE FROM problems WHERE priority_state_id = ?", (state_id,))


def structured_statement_parts(problem: dict) -> dict:
    description = str(problem.get("description") or "")
    cause = ""
    consequence = ""
    if " because " in description:
        cause = description.split(" because ", 1)[1].split(" leading to ", 1)[0]
    if " leading to " in description:
        consequence = description.split(" leading to ", 1)[1]
    return {
        "stakeholder_or_system": str(problem.get("cluster") or "Organisation/system"),
        "experienced_problem": str(problem.get("title") or ""),
        "stage_or_context": ", ".join(as_list(problem.get("relatedStages"))) or str(problem.get("source") or ""),
        "known_cause": cause,
        "suspected_cause": "" if cause else "Unknown or not yet evidenced",
        "business_consequence": consequence,
        "evidence_summary": str(problem.get("evidence") or ""),
        "remaining_uncertainty": "Confidence and source evidence require review." if confidence_number(problem.get("confidence")) <= 2 else "Residual assumptions should be checked before intervention.",
    }


def insert_priority_children(db: sqlite3.Connection, state_id: str, context: dict, form_data: dict, analysis: dict, page4: dict) -> str:
    timestamp = now_iso()
    seed_response_archetypes(db)
    problem_id_map: dict[str, str] = {}
    for problem in analysis["problems"]:
        frontend_id = str(problem.get("id") or slugify(problem.get("title", "problem")))
        problem_id = f"{state_id}-{slugify(frontend_id)}"
        problem_id_map[frontend_id] = problem_id
        signal_id = f"signal-{problem_id}"
        db.execute(
            """
            INSERT INTO problem_signals
            (id, priority_state_id, organisation_id, journey_id, source_page, source_object_type, source_object_id, source_version,
             title, description, evidence_summary, source_confidence, status, imported_at, user_confirmed, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'imported', ?, ?, ?)
            """,
            (signal_id, state_id, context.get("organisationId"), context.get("journeyId"), str(problem.get("source") or "unknown"), "problem_signal", str(problem.get("sourceObjectId") or frontend_id), str(page4.get("versionNumber") or ""), str(problem.get("title") or ""), str(problem.get("description") or ""), str(problem.get("evidence") or ""), str(problem.get("confidence") or ""), timestamp, 1 if problem.get("status") in {"confirmed", "selected"} else 0, json.dumps({"frontendId": frontend_id})),
        )
        statement = structured_statement_parts(problem)
        db.execute(
            """
            INSERT INTO problems
            (id, priority_state_id, organisation_id, journey_id, title, short_title, description, problem_statement, problem_type,
             origin_stage, primary_stage_id, primary_hotspot_id, primary_leverage_point_id, severity_summary, uncertainty_summary,
             status, confidence, confidence_score, verification_status, user_confirmed, created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                problem_id, state_id, context.get("organisationId"), context.get("journeyId"), str(problem.get("title") or ""), str(problem.get("title") or "")[:80],
                str(problem.get("description") or ""), str(problem.get("description") or ""), str(problem.get("problemType") or slugify(str(problem.get("cluster") or "custom"))),
                str(problem.get("source") or ""), ",".join(as_list(problem.get("relatedStages")))[:120], str(problem.get("primaryHotspotId") or ""), str(problem.get("primaryLeveragePointId") or ""),
                f"Impact {problem.get('scores', {}).get('impact', 3)}/5", statement["remaining_uncertainty"], str(problem.get("status") or "under_review"),
                str(problem.get("confidence") or "medium"), confidence_number(problem.get("confidence")), "unverified", 1 if problem.get("status") in {"confirmed", "selected"} else 0,
                context["anonymousSessionId"], context["anonymousSessionId"], timestamp, timestamp, json.dumps({**problem, "frontendId": frontend_id}),
            ),
        )
        db.execute("INSERT INTO problem_signal_links (id, problem_id, problem_signal_id, source_stage, relationship_type, contribution_strength, notes, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, 'primary_source', 'medium', ?, ?, ?, ?, ?)", (f"link-{signal_id}", problem_id, signal_id, str(problem.get("source") or ""), str(problem.get("evidence") or ""), str(problem.get("confidence") or "medium"), 1 if problem.get("status") in {"confirmed", "selected"} else 0, timestamp, timestamp))
        db.execute("INSERT INTO problem_evidence_links (id, problem_id, evidence_id, relationship_type, supports_or_challenges, strength, relevance, confidence, verification_status, source_excerpt_reference, user_confirmed, notes, created_at, updated_at) VALUES (?, ?, ?, 'source_summary', 'supports', 'review', 'contextual', ?, 'unverified', ?, ?, ?, ?, ?)", (f"evidence-{problem_id}", problem_id, f"evidence-{frontend_id}", str(problem.get("confidence") or "medium"), str(problem.get("evidence") or ""), 1 if problem.get("status") in {"confirmed", "selected"} else 0, str(problem.get("evidence") or ""), timestamp, timestamp))
        db.execute("INSERT INTO problem_statements (id, problem_id, stakeholder_or_system, experienced_problem, stage_or_context, known_cause, suspected_cause, business_consequence, evidence_summary, remaining_uncertainty, scope_boundary, statement_version, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)", (f"statement-{problem_id}", problem_id, statement["stakeholder_or_system"], statement["experienced_problem"], statement["stage_or_context"], statement["known_cause"], statement["suspected_cause"], statement["business_consequence"], statement["evidence_summary"], statement["remaining_uncertainty"], str(problem.get("source") or ""), 1 if problem.get("status") in {"confirmed", "selected"} else 0, timestamp, timestamp))
        db.execute("INSERT INTO root_cause_assessments (id, problem_id, candidate_cause_statement, cause_type, evidence_strength, causal_confidence, interdependency_level, alternative_explanations, status, user_confirmed, rationale, created_at, updated_at) VALUES (?, ?, ?, 'unknown', 'review', ?, 'review', 'Other causes may exist.', 'suggested', 0, ?, ?, ?)", (f"root-{problem_id}", problem_id, statement["known_cause"] or statement["suspected_cause"], str(problem.get("confidence") or "low"), "Created from structured problem statement; requires user review.", timestamp, timestamp))
        spectrum = str(problem.get("spectrum") or "unsure")
        cynefin = str(problem.get("cynefin") or "confused")
        archetype_id = f"archetype-{spectrum if spectrum in {'white','light','mid','dark'} else 'white'}-{cynefin if cynefin in {'clear','complicated','complex','chaotic','confused','mixed'} else 'confused'}"
        db.execute("INSERT INTO maturity_positioning (id, problem_id, green_spectrum_level, current_position, desired_position, primary_maturity_dimension, secondary_maturity_dimensions, classification_answers, confidence, rationale, rule_version, generation_method, user_status, user_notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'rules-page5-v1', 'rules', ?, '', ?, ?)", (f"maturity-{problem_id}", problem_id, spectrum, spectrum, "review", str(problem.get("cluster") or ""), json.dumps([]), json.dumps({}), str(problem.get("confidence") or "medium"), str(problem.get("spectrumRationale") or ""), "edited" if problem.get("userEdited") else "suggested", timestamp, timestamp))
        db.execute("INSERT INTO problem_maturity_dimensions (id, problem_id, maturity_dimension_key, relevance_level, current_maturity_level, desired_maturity_level, evidence_ids, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, 'medium', ?, 'review', ?, ?, ?, ?, ?)", (f"dimension-{problem_id}", problem_id, slugify(str(problem.get("cluster") or "custom")), spectrum, json.dumps([f"evidence-{frontend_id}"]), str(problem.get("confidence") or "medium"), 0, timestamp, timestamp))
        db.execute("INSERT INTO complexity_assessments (id, problem_id, cynefin_domain, cause_effect_clarity, predictability, solution_known, expertise_required, stakeholder_agreement, interdependency_level, evidence_quality, urgency, experimentation_need, confidence, rationale, rule_version, generation_method, user_status, created_at, updated_at) VALUES (?, ?, ?, 'review', 'review', 'review', 'review', 'review', 'review', ?, ?, ?, ?, ?, 'rules-page5-v1', 'rules', ?, ?, ?)", (f"complexity-{problem_id}", problem_id, cynefin, score_label(problem.get("scores", {}).get("confidence")), score_label(problem.get("scores", {}).get("urgency")), "high" if cynefin == "complex" else "medium", str(problem.get("confidence") or "medium"), str(problem.get("cynefinRationale") or ""), "edited" if problem.get("userEdited") else "suggested", timestamp, timestamp))
        for key, value in (problem.get("scores") if isinstance(problem.get("scores"), dict) else {}).items():
            dimension = PRIORITY_DIMENSION_MAP.get(key, key)
            db.execute("INSERT INTO priority_assessments (id, problem_id, dimension, score, qualitative_label, rationale, confidence, evidence_ids, assessed_by, assessment_method, rule_version, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'rules', 'rules_and_user_editable', 'rules-page5-v1', ?, ?, ?)", (f"assessment-{problem_id}-{dimension}", problem_id, dimension, int(value or 3), score_label(value), f"{dimension} scored {value}/5 as a decision-support estimate.", str(problem.get("confidence") or "medium"), json.dumps([f"evidence-{frontend_id}"]), 1 if problem.get("userEdited") else 0, timestamp, timestamp))
        db.execute("INSERT INTO priority_recommendations (id, problem_id, recommendation_category, recommended_response_archetype_id, recommended_action, rationale, trigger_inputs, confidence, uncertainty, generator_version, status, user_decision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'medium', 'review', 'rules-page5-v1', 'suggested', 'pending_review', ?, ?)", (f"recommendation-{problem_id}", problem_id, next_priority_move(problem).lower().replace(" ", "_"), archetype_id, next_priority_move(problem), f"Suggested from {spectrum} spectrum and {cynefin} complexity.", json.dumps({"spectrum": spectrum, "cynefin": cynefin, "scores": problem.get("scores", {})}), timestamp, timestamp))
        db.execute("INSERT INTO problem_opportunity_branches (id, problem_id, branch_type, title, description, time_horizon, potential_value, required_capability, confidence, status, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'review', 'review', 'review', ?, 'suggested', 0, ?, ?)", (f"branch-{problem_id}", problem_id, "leverage_point" if problem.get("scores", {}).get("leverage", 3) >= 4 else "capability", f"Opportunity branch for {problem.get('title')}", f"Prepare options for Page 6 without choosing interventions yet. Suggested next move: {next_priority_move(problem)}.", str(problem.get("confidence") or "medium"), timestamp, timestamp))
    profile_id = f"weighting-{state_id}-balanced"
    db.execute("INSERT INTO priority_weighting_profiles (id, priority_state_id, name, description, profile_type, is_default, created_by, status, created_at, updated_at) VALUES (?, ?, 'Balanced decision lens', 'Default Page 5 weighting profile from the frontend controls.', 'balanced', 1, ?, 'active', ?, ?)", (profile_id, state_id, context["anonymousSessionId"], timestamp, timestamp))
    for key, weight in (form_data.get("weights") if isinstance(form_data.get("weights"), dict) else DEFAULT_PRIORITY_WEIGHTS).items():
        db.execute("INSERT INTO priority_weighting_profile_dimensions (id, weighting_profile_id, dimension, weight, rationale, created_at, updated_at) VALUES (?, ?, ?, ?, 'Frontend weighting control.', ?, ?)", (f"{profile_id}-{slugify(key)}", profile_id, PRIORITY_DIMENSION_MAP.get(key, key), float(weight), timestamp, timestamp))
    for problem in analysis["problems"]:
        problem_id = problem_id_map.get(str(problem.get("id")))
        if problem_id:
            trace = {"scores": problem.get("scores", {}), "weights": form_data.get("weights", DEFAULT_PRIORITY_WEIGHTS), "formula": "weighted positives minus effort penalty divided by five"}
            db.execute("INSERT INTO priority_scores (id, problem_id, weighting_profile_id, calculated_score, normalised_score, calculation_trace, formula_version, calculated_at, user_confirmed) VALUES (?, ?, ?, ?, ?, ?, 'priority-formula-v1', ?, 0)", (f"score-{problem_id}", problem_id, profile_id, problem.get("overall", 0), min(100, problem.get("overall", 0)), json.dumps(trace), timestamp))
    for pair in analysis.get("duplicatePairs", []):
        a = problem_id_map.get(str(pair.get("a")))
        b = problem_id_map.get(str(pair.get("b")))
        if a and b and a != b:
            db.execute("INSERT INTO problem_merge_candidates (id, priority_state_id, problem_a_id, problem_b_id, similarity_score, rationale, confidence, status, user_decision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'medium', 'suggested', 'pending_review', ?, ?)", (f"merge-{state_id}-{slugify(pair['a'])}-{slugify(pair['b'])}", state_id, a, b, pair.get("similarity", 0.5), pair.get("rationale", ""), timestamp, timestamp))
    for cluster in analysis.get("clusters", []):
        cluster_id = f"cluster-{state_id}-{slugify(cluster.get('title', 'cluster'))}"
        db.execute("INSERT INTO priority_clusters (id, priority_state_id, title, description, cluster_type, generation_method, rationale, confidence, status, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, 'shared_capability', 'rules', ?, ?, 'suggested', 0, ?, ?)", (cluster_id, state_id, cluster.get("title"), f"{len(cluster.get('problemIds', []))} related problems.", cluster.get("rationale", ""), cluster.get("confidence", "medium"), timestamp, timestamp))
        for pid in cluster.get("problemIds", []):
            problem_id = problem_id_map.get(str(pid))
            if problem_id:
                db.execute("INSERT INTO priority_cluster_members (id, cluster_id, problem_id, membership_strength, membership_reason, created_at, updated_at) VALUES (?, ?, ?, 'medium', 'Shared cluster language.', ?, ?)", (f"member-{cluster_id}-{slugify(pid)}", cluster_id, problem_id, timestamp, timestamp))
    portfolio_id = f"portfolio-{state_id}"
    selected_ids = set(as_list(form_data.get("selectedIds")))
    db.execute("INSERT INTO priority_portfolios (id, priority_state_id, title, description, status, selection_limit, portfolio_rationale, portfolio_risks, created_at, updated_at) VALUES (?, ?, 'Selected priority portfolio', 'Current Page 5 focus portfolio.', 'draft', 5, ?, ?, ?, ?)", (portfolio_id, state_id, "Selected by user through the Page 5 focus controls.", json.dumps(analysis.get("portfolioWarnings", [])), timestamp, timestamp))
    ranked_lookup = {pid: index + 1 for index, pid in enumerate(analysis.get("rankedProblemIds", []))}
    for problem in analysis["problems"]:
        problem_id = problem_id_map.get(str(problem.get("id")))
        if not problem_id:
            continue
        selected = str(problem.get("id")) in selected_ids
        status = "primary" if selected else "monitor" if problem.get("status") not in {"archived", "rejected"} else "rejected"
        rationale = f"Score {problem.get('overall', 0)}; {problem.get('spectrum')} spectrum; {problem.get('cynefin')} complexity; route {next_priority_move(problem)}."
        db.execute("INSERT INTO priority_portfolio_items (id, priority_portfolio_id, problem_id, portfolio_status, rank, selection_rationale, decision_rationale, selected_by, selected_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"portfolio-item-{problem_id}", portfolio_id, problem_id, status, ranked_lookup.get(problem.get("id")), rationale, rationale, context["anonymousSessionId"] if selected else None, timestamp if selected else None, timestamp, timestamp))
        db.execute("INSERT INTO decision_rationales (id, priority_state_id, problem_id, portfolio_id, decision_type, decision, rationale, assumptions, uncertainty, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, 'selection', ?, ?, ?, ?, ?, ?, ?)", (f"rationale-{problem_id}", state_id, problem_id, portfolio_id, status, rationale, json.dumps(["Scores are decision-support estimates, not objective truth."]), "Review evidence and trade-offs before intervention design.", context["anonymousSessionId"], timestamp, timestamp))
    if page4.get("found"):
        db.execute("INSERT INTO prioritisation_import_records (id, priority_state_id, source_type, source_id, source_version, imported_payload, imported_count, conflict_count, stale_count, status, created_at) VALUES (?, ?, 'page4', ?, ?, ?, ?, 0, ?, 'imported', ?)", ("priority-import-" + secrets.token_hex(12), state_id, page4.get("sourceImpactJourneyStateId"), str(page4.get("versionNumber") or ""), json.dumps(page4), len(analysis.get("problems", [])), 1 if page4.get("stale") else 0, timestamp))
    return portfolio_id


def validate_priority_completion(form_data: dict, page4: dict) -> dict:
    problems = [problem for problem in form_data.get("problems", []) if isinstance(problem, dict)]
    selected = as_list(form_data.get("selectedIds"))
    blocking = []
    warnings = []
    if not page4.get("found"):
        blocking.append("No Page 4 handover source was found.")
    source_status = ((page4.get("handover") or {}).get("source") or {}).get("status") if isinstance(page4.get("handover"), dict) else ""
    if page4.get("found") and source_status not in {"completed", "ready_to_proceed"}:
        blocking.append("Page 4 handover is not marked as completed.")
    if not problems:
        blocking.append("At least one canonical problem is required.")
    if not selected:
        blocking.append("At least one priority problem must be selected.")
    if not any(problem.get("status") in {"confirmed", "selected"} for problem in problems):
        blocking.append("At least one problem must be confirmed or selected.")
    if len(selected) < 3:
        warnings.append("Fewer than three problems are selected. This may be acceptable for a narrow journey, but the usual range is three to five.")
    if len(selected) > 5:
        blocking.append("No more than five primary problems can be selected.")
    if not form_data.get("reviewed"):
        blocking.append("The priority review confirmation is required.")
    if priority_completion(form_data) < 85:
        blocking.append("Prioritisation is not complete enough to continue; classifications, weighting, selected focus and review are required.")
    for problem in [item for item in problems if item.get("id") in selected]:
        trace = evidence_trace_for_problem(problem)
        if len(trace.get("missingPerspectives", [])) >= 2:
            warnings.append(f"{problem.get('title', 'A selected problem')} has weak Three Empathies integration.")
    return {"valid": not blocking, "blockingIssues": blocking, "warnings": warnings}


def build_page6_handover(priority_state_id: str, form_data: dict, analysis: dict, portfolio_id: str, status: str) -> dict:
    selected_ids = set(as_list(form_data.get("selectedIds")))
    selected = [problem for problem in analysis.get("problems", []) if str(problem.get("id")) in selected_ids]
    return {
        "source": {"page": "sort-prioritise", "priorityStateId": priority_state_id, "portfolioId": portfolio_id, "status": status, "generatedAt": now_iso()},
        "selectedProblems": [
            {
                "id": problem.get("id"),
                "title": problem.get("title"),
                "description": problem.get("description"),
                "problemStatement": problem.get("description"),
                "source": problem.get("source"),
                "sourceObjectId": problem.get("sourceObjectId"),
                "sourceStages": as_list(problem.get("relatedStages")),
                "evidence": problem.get("evidence"),
                "confidence": problem.get("confidence"),
                "uncertainty": "Review required before intervention design." if confidence_number(problem.get("confidence")) <= 2 else "Residual assumptions remain.",
                "greenSpectrumLevel": problem.get("spectrum"),
                "complexityDomain": problem.get("cynefin"),
                "responseArchetypes": problem.get("archetypes", []),
                "priorityAssessments": problem.get("scores", {}),
                "scoreTrace": problem.get("scoreTrace", score_contributions(problem, form_data.get("weights", DEFAULT_PRIORITY_WEIGHTS))),
                "evidenceTrace": problem.get("evidenceTrace", evidence_trace_for_problem(problem)),
                "priorityScore": problem.get("overall"),
                "recommendedNextMove": next_priority_move(problem),
                "selectionRationale": f"Selected with score {problem.get('overall')}, {problem.get('spectrum')} spectrum and {problem.get('cynefin')} complexity.",
            }
            for problem in selected
        ],
        "portfolioWarnings": analysis.get("portfolioWarnings", []),
        "clusters": analysis.get("clusters", []),
        "threeEmpathiesIntegration": analysis.get("threeEmpathiesIntegration", []),
        "scoringModel": analysis.get("scoringModel", {}),
        "decisionLenses": {"balanced": form_data.get("weights", DEFAULT_PRIORITY_WEIGHTS)},
        "traceability": "Page 4 handover -> Page 5 canonical problems -> classifications -> priority portfolio -> Page 6 handover.",
    }


def save_priority_state(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    journey_id = str(payload.get("journeyId", "")) or None
    form_data = normalise_priority_form(payload)
    with connect() as db:
        state_id, context, version = get_or_create_priority_state(db, session_id, journey_id, payload)
        existing = db.execute("SELECT status FROM priority_states WHERE id = ?", (state_id,)).fetchone()
        if existing and existing["status"] == "completed" and status != "completed":
            return {"ok": False, "error": "Completed prioritisation must be reopened before editing.", "stateId": state_id}
        page4 = latest_page4_handover(db, session_id, context.get("journeyId"))
        if not form_data["problems"]:
            imported, page4 = import_priority_problems_from_sources(db, session_id, context.get("journeyId"), form_data.get("sourceImpactJourneyStateId"))
            form_data["problems"] = imported
        analysis = analyse_priority_state(form_data)
        form_data["problems"] = analysis["problems"]
        validation = validate_priority_completion(form_data, page4) if status == "completed" else {"valid": True, "blockingIssues": [], "warnings": []}
        if status == "completed" and not validation["valid"]:
            return {"ok": False, "stateId": state_id, "validation": validation, "analysis": analysis}
        timestamp = now_iso()
        row = db.execute("SELECT autosave_revision, created_at FROM priority_states WHERE id = ?", (state_id,)).fetchone()
        revision = int(row["autosave_revision"]) + 1 if row else 1
        created_at = row["created_at"] if row else timestamp
        final_status = "completed" if status == "completed" else "draft"
        clear_priority_children(db, state_id)
        source_page3 = ""
        source_page4 = page4.get("sourceImpactJourneyStateId") or form_data.get("sourceImpactJourneyStateId") or ""
        db.execute(
            """
            INSERT OR REPLACE INTO priority_states
            (id, anonymous_session_id, organisation_id, journey_id, methodology_version_id, version_number, title, description,
             source_page3_version_id, source_impact_journey_version_id, status, completion_percentage, current_section,
             selected_problem_minimum, selected_problem_maximum, autosave_revision, form_snapshot, analysis_snapshot, last_saved_at,
             completed_at, completed_by, is_stale, stale_reason, review_required, created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, 'Sort and Prioritise Problems', ?, ?, ?, ?, ?, ?, 3, 5, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id, session_id, context.get("organisationId"), context.get("journeyId"), context.get("methodologyVersionId"), version,
                "Page 5 decision-structuring and priority portfolio.", source_page3, source_page4, final_status,
                100 if final_status == "completed" else analysis.get("completionPercentage", 0), str(payload.get("section") or "portfolio"), revision,
                json.dumps(form_data), json.dumps(analysis), timestamp, timestamp if final_status == "completed" else None,
                session_id if final_status == "completed" else None, 1 if page4.get("stale") else 0,
                "Upstream Page 4 handover is stale." if page4.get("stale") else "", 1 if page4.get("stale") else 0,
                session_id, session_id, created_at, timestamp, json.dumps({"authMode": "anonymous-local", "warnings": validation.get("warnings", [])}),
            ),
        )
        portfolio_id = insert_priority_children(db, state_id, context, form_data, analysis, page4)
        handover = build_page6_handover(state_id, form_data, analysis, portfolio_id, final_status)
        db.execute("INSERT OR REPLACE INTO page6_handover_manifests (id, priority_state_id, manifest, confirmed, stale, created_at, updated_at) VALUES (?, ?, ?, ?, 0, ?, ?)", (f"handover-page6-{state_id}", state_id, json.dumps(handover), 1 if final_status == "completed" else 0, timestamp, timestamp))
        if final_status == "completed":
            db.execute("UPDATE journey_progress SET status = 'completed', completion_percentage = 100, completed_at = ?, last_visited_at = ?, output_summary = ? WHERE journey_id = ? AND stage_key = 'structure-prioritise'", (timestamp, timestamp, json.dumps({"priorityStateId": state_id, "selectedProblems": len(handover.get("selectedProblems", []))}), context.get("journeyId")))
        db.execute("INSERT INTO audit_logs (id, actor_type, actor_id, action, entity_type, entity_id, metadata, occurred_at) VALUES (?, 'anonymous_session', ?, ?, 'priority_state', ?, ?, ?)", ("audit-" + secrets.token_hex(12), session_id, "complete_prioritisation" if final_status == "completed" else "autosave_prioritisation", state_id, json.dumps({"status": final_status, "revision": revision}), timestamp))
    return {"ok": True, "stateId": state_id, "status": final_status, "versionNumber": version, "autosaveRevision": revision, "formData": form_data, "analysis": analysis, "handover": handover, "validation": validation}


def get_priority_state(session_id: str, journey_id: str | None = None, state_id: str | None = None) -> dict:
    session_id = session_id[:80] or "anonymous-local"
    with connect() as db:
        row = None
        if state_id:
            row = db.execute("SELECT * FROM priority_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            row = db.execute(
                """
                SELECT * FROM priority_states
                WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '')
                ORDER BY CASE status WHEN 'draft' THEN 0 WHEN 'active' THEN 1 WHEN 'completed' THEN 2 ELSE 3 END, updated_at DESC
                LIMIT 1
                """,
                (session_id, journey_id),
            ).fetchone()
        context = resolve_priority_context(db, session_id, journey_id)
        imported, page4 = import_priority_problems_from_sources(db, session_id, context.get("journeyId"))
    if not row:
        form_data = {"problems": imported, "weights": DEFAULT_PRIORITY_WEIGHTS, "selectedIds": [], "reviewed": False, "sourceImpactJourneyStateId": page4.get("sourceImpactJourneyStateId")}
        analysis = analyse_priority_state(form_data)
        return {"ok": True, "found": False, "formData": form_data, "analysis": analysis, "page4": page4, "context": context}
    return {
        "ok": True,
        "found": True,
        "stateId": row["id"],
        "status": row["status"],
        "versionNumber": row["version_number"],
        "autosaveRevision": row["autosave_revision"],
        "formData": json_loads_safe(row["form_snapshot"], {}),
        "analysis": json_loads_safe(row["analysis_snapshot"], {}),
        "page4": page4,
        "context": context,
        "updatedAt": row["updated_at"],
    }


def import_page4_to_priority(state_id: str, payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    with connect() as db:
        row = db.execute("SELECT id, journey_id FROM priority_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            return {"ok": False, "error": "Prioritisation state not found."}
        problems, page4 = import_priority_problems_from_sources(db, session_id, row["journey_id"])
        timestamp = now_iso()
        db.execute("INSERT INTO prioritisation_import_records (id, priority_state_id, source_type, source_id, source_version, imported_payload, imported_count, conflict_count, stale_count, status, created_at) VALUES (?, ?, 'page4', ?, ?, ?, ?, 0, ?, 'imported', ?)", ("priority-import-" + secrets.token_hex(12), state_id, page4.get("sourceImpactJourneyStateId"), str(page4.get("versionNumber") or ""), json.dumps(page4), len(problems), 1 if page4.get("stale") else 0, timestamp))
    return {"ok": True, "stateId": state_id, "problems": problems, "page4": page4}


def reopen_priority_state(state_id: str, payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    reason = str(payload.get("revisionReason") or "Reopened for editing")
    with connect() as db:
        row = db.execute("SELECT * FROM priority_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            return {"ok": False, "error": "Prioritisation state not found."}
        new_id = "priority-" + secrets.token_hex(12)
        timestamp = now_iso()
        db.execute(
            """
            INSERT INTO priority_states
            (id, anonymous_session_id, organisation_id, journey_id, methodology_version_id, version_number, title, description,
             source_page3_version_id, source_impact_journey_version_id, status, completion_percentage, current_section,
             selected_problem_minimum, selected_problem_maximum, autosave_revision, form_snapshot, analysis_snapshot, last_saved_at,
             reopened_at, reopened_by, revision_reason, is_stale, stale_reason, review_required, created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, 0, '', 0, ?, ?, ?, ?, ?)
            """,
            (new_id, row["anonymous_session_id"], row["organisation_id"], row["journey_id"], row["methodology_version_id"], int(row["version_number"]) + 1, row["title"], row["description"], row["source_page3_version_id"], row["source_impact_journey_version_id"], row["completion_percentage"], row["current_section"], row["selected_problem_minimum"], row["selected_problem_maximum"], row["form_snapshot"], row["analysis_snapshot"], timestamp, timestamp, session_id, reason, session_id, session_id, timestamp, timestamp, row["metadata"]),
        )
        db.execute("UPDATE page6_handover_manifests SET stale = 1, updated_at = ? WHERE priority_state_id = ?", (timestamp, state_id))
    return {"ok": True, "stateId": new_id, "status": "draft"}


def export_priority_state(state_id: str, session_id: str) -> dict:
    data = get_priority_state(session_id, state_id=state_id)
    if not data.get("found"):
        return {"ok": False, "error": "Prioritisation state not found."}
    with connect() as db:
        counts = {}
        for table in ["problems", "problem_signals", "priority_assessments", "priority_scores", "priority_clusters", "priority_portfolios", "priority_portfolio_items", "decision_rationales"]:
            if table == "priority_portfolio_items":
                count = db.execute("SELECT COUNT(*) AS count FROM priority_portfolio_items WHERE priority_portfolio_id IN (SELECT id FROM priority_portfolios WHERE priority_state_id = ?)", (state_id,)).fetchone()["count"]
            else:
                count = db.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE priority_state_id = ?", (state_id,)).fetchone()["count"] if table not in {"priority_assessments", "priority_scores"} else db.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE problem_id IN (SELECT id FROM problems WHERE priority_state_id = ?)", (state_id,)).fetchone()["count"]
            counts[table] = count
    return {"ok": True, "exportedAt": now_iso(), "format": "green-spectrum-prioritisation-json-v1", "counts": counts, **data}


def page6_handover(state_id: str, session_id: str) -> dict:
    session_id = session_id[:80] or "anonymous-local"
    with connect() as db:
        row = db.execute(
            """
            SELECT h.manifest, h.confirmed, h.stale, h.updated_at
            FROM page6_handover_manifests h
            JOIN priority_states s ON s.id = h.priority_state_id
            WHERE h.priority_state_id = ? AND s.anonymous_session_id = ?
            ORDER BY h.updated_at DESC
            LIMIT 1
            """,
            (state_id, session_id),
        ).fetchone()
    if not row:
        return {"ok": False, "error": "Page 6 handover not found."}
    return {"ok": True, "handover": json_loads_safe(row["manifest"], {}), "confirmed": bool(row["confirmed"]), "stale": bool(row["stale"]), "updatedAt": row["updated_at"]}


INTERVENTION_CHILD_TABLES = [
    "decision_assessments",
    "decision_results",
    "tool_recommendations",
    "intervention_assumptions",
    "desired_outcomes",
    "backcast_steps",
    "intervention_pathways",
    "intervention_options",
    "intervention_comparisons",
    "horizons",
    "horizon_dependencies",
    "prototype_plans",
    "experiments",
    "experiment_hypotheses",
    "experiment_metrics",
    "intervention_risks",
    "pathway_ownership",
    "experiment_reviews",
    "learning_records",
    "intervention_outputs",
    "complete_journey_records",
    "intervention_import_records",
]

TOOL_FIXTURES = [
    ("tool-systems-mapping", "Systems Mapping", "systems", "Reveal relationships, dependencies and feedback loops.", ["complex", "confused"], ["system map", "leverage questions"]),
    ("tool-stakeholder-interviews", "Stakeholder Interviews", "stakeholder engagement", "Understand experience, incentives and resistance.", ["complex", "complicated"], ["interview guide", "insight summary"]),
    ("tool-experiment-card", "Experiment Card", "experimentation", "Define a hypothesis, method, measures and review decision.", ["complex", "clear", "complicated"], ["experiment plan", "decision threshold"]),
    ("tool-three-horizons", "Three Horizons", "strategic foresight", "Plan near-term, transitional and long-term change together.", ["complex", "complicated"], ["roadmap", "horizon dependencies"]),
    ("tool-lca", "Life Cycle Assessment", "technical testing", "Assess product or material environmental impacts.", ["complicated"], ["impact baseline", "hotspot evidence"]),
    ("tool-raci", "Decision Rights and RACI", "governance design", "Clarify ownership, roles and escalation.", ["clear", "complicated", "confused"], ["owner map", "governance actions"]),
    ("tool-data-dictionary", "Data Dictionary", "data", "Clarify data owners, definitions and minimum evidence requirements.", ["clear", "confused"], ["data inventory", "quality criteria"]),
]


def seed_tool_definitions(db: sqlite3.Connection) -> None:
    timestamp = now_iso()
    for tool_id, name, category, purpose, domains, outputs in TOOL_FIXTURES:
        db.execute(
            """
            INSERT OR IGNORE INTO tool_definitions
            (id, name, category, purpose, applicable_maturity_levels, applicable_complexity_domains,
             applicable_problem_types, required_inputs, evidence_prerequisites, expected_outputs, time, effort,
             expertise, delivery_modes, limitations, risks, alternative_tools, next_steps, download_asset,
             methodology_version, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'short workshop to multi-week sprint', 'moderate', 'facilitator or specialist where needed',
                    ?, ?, ?, ?, ?, NULL, ?, 1, ?, ?)
            """,
            (
                tool_id,
                name,
                category,
                purpose,
                json.dumps(["white", "light", "mid", "dark"]),
                json.dumps(domains),
                json.dumps(["custom"]),
                json.dumps(["problem statement", "source evidence", "decision context"]),
                json.dumps(["source evidence reviewed"]),
                json.dumps(outputs),
                json.dumps(["solo", "team", "facilitation"]),
                json.dumps(["does not replace user judgement", "requires evidence review"]),
                json.dumps(["wrong tool fit may create false confidence"]),
                json.dumps([]),
                json.dumps(["review output", "decide next action"]),
                METHODOLOGY_VERSION,
                timestamp,
                timestamp,
            ),
        )


def latest_priority_handover(db: sqlite3.Connection, session_id: str, journey_id: str | None = None) -> dict:
    row = None
    if journey_id:
        row = db.execute(
            """
            SELECT h.manifest, h.confirmed, h.stale, h.updated_at, s.id AS state_id, s.version_number
            FROM page6_handover_manifests h
            JOIN priority_states s ON s.id = h.priority_state_id
            WHERE s.anonymous_session_id = ? AND COALESCE(s.journey_id, '') = COALESCE(?, '')
            ORDER BY s.updated_at DESC
            LIMIT 1
            """,
            (session_id, journey_id),
        ).fetchone()
    if not row:
        row = db.execute(
            """
            SELECT h.manifest, h.confirmed, h.stale, h.updated_at, s.id AS state_id, s.version_number
            FROM page6_handover_manifests h
            JOIN priority_states s ON s.id = h.priority_state_id
            WHERE s.anonymous_session_id = ?
            ORDER BY s.updated_at DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    if not row:
        return {"found": False, "sourcePriorityStateId": "", "sourcePriorityPortfolioId": "", "handover": {}, "stale": False}
    manifest = json_loads_safe(row["manifest"], {})
    return {
        "found": True,
        "sourcePriorityStateId": row["state_id"],
        "sourcePriorityPortfolioId": manifest.get("source", {}).get("portfolioId", "") if isinstance(manifest, dict) else "",
        "versionNumber": row["version_number"],
        "handover": manifest,
        "confirmed": bool(row["confirmed"]),
        "stale": bool(row["stale"]),
        "updatedAt": row["updated_at"],
    }


def recommended_intervention_family(problem: dict) -> str:
    text = f"{problem.get('title', '')} {problem.get('description', '')}".lower()
    if "data" in text or "evidence" in text:
        return "data"
    if "supplier" in text or "supply" in text:
        return "supply-chain"
    if "governance" in text or "ownership" in text:
        return "governance"
    if "culture" in text or "employee" in text or "behaviour" in text:
        return "behaviour"
    if "product" in text or "packaging" in text:
        return "product"
    return "process"


def recommended_prototype_type(problem: dict, family: str) -> str:
    if problem.get("complexityDomain") == "complex" or problem.get("cynefin") == "complex":
        return "behaviour"
    if family == "data":
        return "digital"
    if family == "supply-chain":
        return "supply-chain"
    if family == "governance":
        return "organisational"
    if family == "product":
        return "product"
    return "process"


def decision_route(problem: dict) -> str:
    domain = problem.get("complexityDomain") or problem.get("cynefin")
    confidence = confidence_number(problem.get("confidence"))
    assessments = problem.get("priorityAssessments") if isinstance(problem.get("priorityAssessments"), dict) else problem.get("scores", {})
    if domain == "chaotic":
        return "stabilise"
    if domain == "complex" or "experiment-first" in as_list(problem.get("responseArchetypes")):
        return "experiment"
    if domain == "confused" or confidence <= 2:
        return "return-to-discovery"
    if isinstance(assessments, dict) and int(assessments.get("readiness", assessments.get("readiness", 3)) or 3) <= 2:
        return "build-capability"
    return "proceed"


def intervention_option_from_problem(problem: dict, family: str, index: int = 1) -> dict:
    return {
        "id": f"option-{slugify(str(problem.get('id') or problem.get('title') or index))}-{index}",
        "family": family,
        "title": f"{family.replace('-', ' ').title()} pilot",
        "description": f"Test a focused {family.replace('-', ' ')} intervention linked to the selected problem.",
        "mechanism": "Reduce uncertainty through a contained learning activity.",
        "impact": 4,
        "effort": 3,
        "risk": 2,
        "status": "suggested",
        "tools": tool_suggestions_for_family(family),
    }


def tool_suggestions_for_family(family: str) -> list[str]:
    return {
        "data": ["Data Dictionary", "Decision Rights and RACI", "Experiment Card"],
        "supply-chain": ["Stakeholder Interviews", "Systems Mapping", "Experiment Card"],
        "governance": ["Decision Rights and RACI", "Three Horizons", "Experiment Card"],
        "behaviour": ["Stakeholder Interviews", "Systems Mapping", "Experiment Card"],
        "product": ["Life Cycle Assessment", "Experiment Card", "Three Horizons"],
    }.get(family, ["Three Horizons", "Experiment Card", "Systems Mapping"])


def create_pathway_from_problem(problem: dict, index: int) -> dict:
    family = recommended_intervention_family(problem)
    route = decision_route(problem)
    title = str(problem.get("title") or f"Pathway {index + 1}")
    assessments = problem.get("priorityAssessments") if isinstance(problem.get("priorityAssessments"), dict) else {}
    return {
        "id": f"pathway-{slugify(str(problem.get('id') or title or index))}",
        "problemId": problem.get("id"),
        "rank": index + 1,
        "title": title,
        "problemDefinition": str(problem.get("description") or problem.get("problemStatement") or title),
        "evidenceSummary": str(problem.get("evidence") or problem.get("selectionRationale") or "Priority handover evidence."),
        "unknowns": ["Evidence confidence remains low"] if confidence_number(problem.get("confidence")) <= 2 else [],
        "spectrum": str(problem.get("greenSpectrumLevel") or problem.get("spectrum") or "light"),
        "cynefin": str(problem.get("complexityDomain") or problem.get("cynefin") or "complex"),
        "archetypes": as_list(problem.get("responseArchetypes")),
        "readiness": int(assessments.get("readiness", 3) or 3),
        "influence": int(assessments.get("influence", 3) or 3),
        "leverage": int(assessments.get("leverage", assessments.get("systems_leverage", 3)) or 3),
        "desiredOutcome": "",
        "beneficiaries": [],
        "changes": [],
        "nonNegotiables": "",
        "timeframe": "3-12 months",
        "backcastSteps": ["Define evidence need", "Confirm owner", "Test the riskiest assumption", "Review decision threshold"],
        "decisionAnswers": {},
        "decisionOutcome": route,
        "decisionRationale": f"{route.replace('-', ' ').title()} is suggested from Page 5 complexity, confidence, readiness and response archetype.",
        "interventionOptions": [
            intervention_option_from_problem(problem, family, 1),
            {"id": f"option-governance-{index}", "family": "governance", "title": "Ownership and decision-rights redesign", "description": "Clarify who owns decisions, evidence and escalation.", "mechanism": "Improve accountability and decision speed.", "impact": 3, "effort": 2, "risk": 2, "status": "suggested", "tools": tool_suggestions_for_family("governance")},
            {"id": f"option-data-{index}", "family": "data", "title": "Evidence visibility sprint", "description": "Improve the minimum data needed to make a responsible decision.", "mechanism": "Increase confidence before scaling.", "impact": 3, "effort": 2, "risk": 1, "status": "suggested", "tools": tool_suggestions_for_family("data")},
        ],
        "selectedInterventionId": "",
        "horizons": [
            {"type": "h1", "title": "Horizon 1", "timeframe": "0-3 months", "objective": "Test or improve the current system", "actions": ["Clarify owner", "Run a small prototype"], "owner": "", "participants": [], "resources": [], "dependencies": [], "measures": [], "decisionDate": ""},
            {"type": "h2", "title": "Horizon 2", "timeframe": "3-12 months", "objective": "Develop and integrate the emerging pathway", "actions": ["Expand pilot", "Build capability"], "owner": "", "participants": [], "resources": [], "dependencies": [], "measures": [], "decisionDate": ""},
            {"type": "h3", "title": "Horizon 3", "timeframe": "12+ months", "objective": "Create wider strategic or transformational change", "actions": ["Scale learning", "Build long-term partnerships"], "owner": "", "participants": [], "resources": [], "dependencies": [], "measures": [], "decisionDate": ""},
        ],
        "prototypeType": recommended_prototype_type(problem, family),
        "experiment": {
            "title": f"{family.replace('-', ' ').title()} prototype for {title}",
            "hypothesis": f"If we test a {family.replace('-', ' ')} intervention, then decision confidence will improve because the riskiest assumption can be observed before scaling.",
            "learningObjective": "Reduce uncertainty about feasibility, stakeholder response and evidence quality.",
            "method": "Run a contained pilot, collect evidence, and review results against decision thresholds.",
            "decisionThreshold": "Proceed if evidence improves and risks remain acceptable; iterate if assumptions are partly supported; pause or return to discovery if contradicted.",
            "startDate": "",
            "endDate": "",
            "status": "draft",
        },
        "owners": {"executiveSponsor": "", "pathwayOwner": "", "experimentOwner": "", "decisionMaker": "", "dataOwner": "", "riskOwner": "", "cadence": "monthly"},
        "metrics": [
            {"name": "Evidence confidence improved", "category": "learning", "unit": "confidence level", "baseline": str(problem.get("confidence") or "unknown"), "target": "Confidence increases by one level", "owner": "", "frequency": "review gate", "dataSource": "prototype evidence log"},
            {"name": "Prototype completed", "category": "activity", "unit": "test", "baseline": "0", "target": "One contained test completed", "owner": "", "frequency": "end of pilot", "dataSource": "experiment record"},
            {"name": "Stakeholder response understood", "category": "outcome", "unit": "evidence summary", "baseline": "not yet tested", "target": "Key feedback captured", "owner": "", "frequency": "midpoint and final review", "dataSource": "stakeholder feedback"},
        ],
        "risks": [
            {"category": "operational", "description": "Prototype disrupts normal work", "likelihood": 2, "severity": 3, "mitigation": "Limit scope, keep the test reversible and agree a review point before launch.", "owner": "", "watchSignal": "delivery delays or staff pushback", "stopCondition": "pause if service quality, safety or workload crosses the agreed threshold"},
            {"category": "data", "description": "Evidence remains incomplete", "likelihood": 3, "severity": 3, "mitigation": "Define minimum evidence threshold, data owner and fallback decision rule.", "owner": "", "watchSignal": "missing baseline or unverifiable result", "stopCondition": "return to discovery if the minimum evidence cannot be collected"},
        ],
        "reviewDate": "",
        "completed": False,
    }


def import_intervention_pathways_from_priority(db: sqlite3.Connection, session_id: str, journey_id: str | None) -> tuple[list[dict], dict]:
    source = latest_priority_handover(db, session_id, journey_id)
    problems = []
    if source.get("found"):
        handover = source.get("handover") if isinstance(source.get("handover"), dict) else {}
        problems = [item for item in handover.get("selectedProblems", []) if isinstance(item, dict)]
    if not problems:
        problems = [
            {"id": "demo-1", "title": "Supplier emissions data pathway", "description": "Supplier emissions data is incomplete because reporting expectations and verification processes are inconsistent, leading to weak Scope 3 confidence.", "greenSpectrumLevel": "light", "complexityDomain": "complex", "priorityAssessments": {"readiness": 3, "influence": 3, "leverage": 5}, "confidence": 3, "responseArchetypes": ["experiment-first", "system-leverage-point"], "evidence": "Development fallback; replace with Page 5 handover"},
            {"id": "demo-2", "title": "Packaging waste reduction pathway", "description": "Packaging waste remains high because product design and end-of-life ownership are disconnected, leading to avoidable material loss.", "greenSpectrumLevel": "mid", "complexityDomain": "complicated", "priorityAssessments": {"readiness": 3, "influence": 4, "leverage": 4}, "confidence": 3, "responseArchetypes": ["strategic-programme"], "evidence": "Development fallback; replace with Page 5 handover"},
            {"id": "demo-3", "title": "Sustainability governance pathway", "description": "Sustainability governance exists but accountability is not linked to operational decision points, leading to inconsistent delivery.", "greenSpectrumLevel": "light", "complexityDomain": "clear", "priorityAssessments": {"readiness": 4, "influence": 4, "leverage": 5}, "confidence": 3, "responseArchetypes": ["quick-win"], "evidence": "Development fallback; replace with Page 5 handover"},
        ]
    return [create_pathway_from_problem(problem, index) for index, problem in enumerate(problems[:5])], source


def normalise_intervention_form(payload: dict) -> dict:
    form_data = payload.get("formData") if isinstance(payload.get("formData"), dict) else {}
    if not form_data and isinstance(payload.get("state"), dict):
        form_data = payload["state"]
    return {
        "stateId": form_data.get("stateId") or form_data.get("id") or "",
        "sourcePriorityStateId": form_data.get("sourcePriorityStateId") or payload.get("sourcePriorityStateId") or "",
        "sourcePriorityPortfolioId": form_data.get("sourcePriorityPortfolioId") or payload.get("sourcePriorityPortfolioId") or "",
        "pathways": form_data.get("pathways") if isinstance(form_data.get("pathways"), list) else [],
        "activeId": form_data.get("activeId") or "",
        "primaryIds": form_data.get("primaryIds") if isinstance(form_data.get("primaryIds"), list) else [],
        "reviewed": bool(form_data.get("reviewed") or form_data.get("prototypeReviewed")),
    }


def intervention_completion(form_data: dict) -> int:
    pathways = [p for p in form_data.get("pathways", []) if isinstance(p, dict)]
    if not pathways:
        return 0
    checks = [
        any(p.get("problemDefinition") for p in pathways),
        any(p.get("desiredOutcome") for p in pathways),
        all(len(as_list(p.get("backcastSteps"))) >= 3 for p in pathways),
        all(p.get("decisionOutcome") for p in pathways),
        any(p.get("selectedInterventionId") for p in pathways),
        all(p.get("horizons") for p in pathways),
        any((p.get("experiment") or {}).get("hypothesis") for p in pathways if isinstance(p.get("experiment"), dict)),
        any((p.get("owners") or {}).get("pathwayOwner") and (p.get("owners") or {}).get("experimentOwner") for p in pathways if isinstance(p.get("owners"), dict)),
        any(p.get("completed") for p in pathways) or bool(form_data.get("reviewed")),
    ]
    return round((len([item for item in checks if item]) / 9) * 100)


def analyse_intervention_state(form_data: dict, source: dict) -> dict:
    pathways = [p for p in form_data.get("pathways", []) if isinstance(p, dict)]
    primary_ids = set(as_list(form_data.get("primaryIds")))
    primary = [p for p in pathways if p.get("id") in primary_ids] or pathways[:3]
    warnings = []
    missing_owner = len([p for p in primary if not (p.get("owners") or {}).get("pathwayOwner")])
    if missing_owner:
        warnings.append(f"{missing_owner} primary pathway{'s' if missing_owner != 1 else ''} still need a pathway owner.")
    if primary and all(p.get("prototypeType") not in {"behaviour", "community"} for p in primary):
        warnings.append("The portfolio contains no explicit Human Empathy or participation prototype.")
    if primary and not any(p.get("decisionOutcome") == "experiment" for p in primary):
        warnings.append("The portfolio contains no low-risk learning experiment.")
    if primary and len([p for p in primary if (p.get("owners") or {}).get("dataOwner")]) > 1:
        warnings.append("Several pathways may depend on the same data capacity.")
    outputs = {
        "strategySummary": {"pathways": len(pathways), "primaryPathways": len(primary), "decisions": [p.get("decisionOutcome") for p in pathways]},
        "experimentPack": [{
            "pathwayId": p.get("id"),
            "title": (p.get("experiment") or {}).get("title"),
            "hypothesis": (p.get("experiment") or {}).get("hypothesis"),
            "owner": (p.get("owners") or {}).get("experimentOwner"),
            "reviewDate": p.get("reviewDate"),
            "decisionThreshold": (p.get("experiment") or {}).get("decisionThreshold"),
            "safeToFail": as_list(p.get("nonNegotiables")) or ["Do not compromise safety, fairness or evidence quality."],
        } for p in pathways],
        "threeHorizonsRoadmap": [{"pathwayId": p.get("id"), "horizons": p.get("horizons", [])} for p in pathways],
        "learningPlan": [{"pathwayId": p.get("id"), "learningObjective": (p.get("experiment") or {}).get("learningObjective"), "decisionThreshold": (p.get("experiment") or {}).get("decisionThreshold")} for p in pathways],
        "metricPlan": [{"pathwayId": p.get("id"), "metrics": p.get("metrics", [])} for p in pathways],
        "riskRegister": [{"pathwayId": p.get("id"), "risks": p.get("risks", [])} for p in pathways],
    }
    return {
        "pathwayCount": len(pathways),
        "primaryPathwayIds": list(primary_ids),
        "experimentReadyCount": len([p for p in pathways if (p.get("experiment") or {}).get("hypothesis") and (p.get("owners") or {}).get("experimentOwner")]),
        "completedPathwayCount": len([p for p in pathways if p.get("completed")]),
        "portfolioWarnings": warnings,
        "outputs": outputs,
        "source": source,
        "completionPercentage": intervention_completion(form_data),
    }


def get_or_create_intervention_state(db: sqlite3.Connection, session_id: str, journey_id: str | None, payload: dict) -> tuple[str, dict, int]:
    context = resolve_priority_context(db, session_id, journey_id)
    explicit_id = str(payload.get("interventionStateId") or payload.get("id") or "")
    row = None
    if explicit_id:
        row = db.execute("SELECT * FROM intervention_states WHERE id = ? AND anonymous_session_id = ?", (explicit_id, session_id)).fetchone()
    if not row:
        row = db.execute(
            """
            SELECT * FROM intervention_states
            WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '') AND status IN ('draft', 'active')
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (session_id, context.get("journeyId")),
        ).fetchone()
    if row:
        return row["id"], context, int(row["version_number"])
    latest = db.execute("SELECT MAX(version_number) AS version FROM intervention_states WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '')", (session_id, context.get("journeyId"))).fetchone()
    version = int(latest["version"] or 0) + 1 if latest else 1
    return "intervention-" + secrets.token_hex(12), context, version


def clear_intervention_children(db: sqlite3.Connection, state_id: str) -> None:
    focus_ids = [row["id"] for row in db.execute("SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?", (state_id,)).fetchall()]
    if focus_ids:
        placeholders = ",".join("?" for _ in focus_ids)
        outcome_ids = [row["id"] for row in db.execute(f"SELECT id FROM desired_outcomes WHERE selected_problem_focus_id IN ({placeholders})", focus_ids).fetchall()]
        pathway_ids = [row["id"] for row in db.execute(f"SELECT id FROM intervention_pathways WHERE selected_problem_focus_id IN ({placeholders})", focus_ids).fetchall()]
        experiment_ids = [row["id"] for row in db.execute(f"SELECT id FROM experiments WHERE selected_problem_focus_id IN ({placeholders})", focus_ids).fetchall()]
        db.execute(f"DELETE FROM decision_assessments WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM decision_results WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM tool_recommendations WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM intervention_assumptions WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM intervention_comparisons WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM intervention_risks WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM pathway_ownership WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM learning_records WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        if outcome_ids:
            out_ph = ",".join("?" for _ in outcome_ids)
            db.execute(f"DELETE FROM backcast_steps WHERE desired_outcome_id IN ({out_ph})", outcome_ids)
        if pathway_ids:
            path_ph = ",".join("?" for _ in pathway_ids)
            option_ids = [row["id"] for row in db.execute(f"SELECT id FROM intervention_options WHERE intervention_pathway_id IN ({path_ph})", pathway_ids).fetchall()]
            horizon_ids = [row["id"] for row in db.execute(f"SELECT id FROM horizons WHERE intervention_pathway_id IN ({path_ph})", pathway_ids).fetchall()]
            prototype_ids = [row["id"] for row in db.execute(f"SELECT id FROM prototype_plans WHERE intervention_pathway_id IN ({path_ph})", pathway_ids).fetchall()]
            db.execute(f"DELETE FROM intervention_options WHERE intervention_pathway_id IN ({path_ph})", pathway_ids)
            db.execute(f"DELETE FROM horizons WHERE intervention_pathway_id IN ({path_ph})", pathway_ids)
            db.execute(f"DELETE FROM prototype_plans WHERE intervention_pathway_id IN ({path_ph})", pathway_ids)
            if horizon_ids:
                hor_ph = ",".join("?" for _ in horizon_ids)
                db.execute(f"DELETE FROM horizon_dependencies WHERE source_horizon_item_id IN ({hor_ph}) OR target_horizon_item_id IN ({hor_ph})", horizon_ids + horizon_ids)
            if option_ids:
                opt_ph = ",".join("?" for _ in option_ids)
                db.execute(f"DELETE FROM intervention_comparisons WHERE option_a_id IN ({opt_ph}) OR option_b_id IN ({opt_ph})", option_ids + option_ids)
            if prototype_ids:
                proto_ph = ",".join("?" for _ in prototype_ids)
                db.execute(f"DELETE FROM experiments WHERE prototype_plan_id IN ({proto_ph})", prototype_ids)
        if experiment_ids:
            exp_ph = ",".join("?" for _ in experiment_ids)
            db.execute(f"DELETE FROM experiment_hypotheses WHERE experiment_id IN ({exp_ph})", experiment_ids)
            db.execute(f"DELETE FROM experiment_metrics WHERE experiment_id IN ({exp_ph})", experiment_ids)
            db.execute(f"DELETE FROM experiment_reviews WHERE experiment_id IN ({exp_ph})", experiment_ids)
        db.execute(f"DELETE FROM desired_outcomes WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM intervention_pathways WHERE selected_problem_focus_id IN ({placeholders})", focus_ids)
        db.execute(f"DELETE FROM selected_problem_focus WHERE id IN ({placeholders})", focus_ids)
    for table in ["intervention_outputs", "complete_journey_records", "intervention_import_records"]:
        db.execute(f"DELETE FROM {table} WHERE intervention_state_id = ?", (state_id,))


def insert_intervention_children(db: sqlite3.Connection, state_id: str, context: dict, form_data: dict, analysis: dict, source: dict) -> None:
    timestamp = now_iso()
    seed_tool_definitions(db)
    for index, pathway in enumerate([p for p in form_data.get("pathways", []) if isinstance(p, dict)], start=1):
        frontend_id = str(pathway.get("id") or f"pathway-{index}")
        focus_id = f"focus-{state_id}-{slugify(frontend_id)}"
        outcome_id = f"outcome-{focus_id}"
        pathway_id = f"intervention-pathway-{state_id}-{slugify(frontend_id)}"
        db.execute(
            """
            INSERT INTO selected_problem_focus
            (id, intervention_state_id, problem_id, source_problem_id, focus_statement, scope, desired_change, reason_for_selection,
             portfolio_rationale, decision_conditions, constraints, dependencies, capability_gaps, known_risks, known_assumptions,
             known_unknowns, confidence, user_confirmed, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                focus_id, state_id, str(pathway.get("problemId") or ""), str(pathway.get("problemId") or ""), str(pathway.get("problemDefinition") or ""),
                str(pathway.get("boundary") or ""), str(pathway.get("desiredOutcome") or ""), str(pathway.get("decisionRationale") or ""),
                str(pathway.get("evidenceSummary") or ""), json.dumps(as_list(pathway.get("backcastSteps"))), json.dumps(as_list(pathway.get("nonNegotiables"))),
                json.dumps([]), json.dumps([]), json.dumps([risk.get("description") for risk in pathway.get("risks", []) if isinstance(risk, dict)]),
                json.dumps(["Prototype assumptions require testing."]), json.dumps(as_list(pathway.get("unknowns"))), "medium",
                1 if pathway.get("completed") else 0, "confirmed" if pathway.get("completed") else "draft", timestamp, timestamp,
            ),
        )
        db.execute(
            """
            INSERT INTO desired_outcomes
            (id, selected_problem_focus_id, title, description, outcome_type, business_outcome, human_outcome, planetary_outcome,
             governance_outcome, target_stakeholders, target_ecosystems, target_date, success_conditions, failure_conditions,
             ethical_constraints, acceptable_trade_offs, unacceptable_trade_offs, baseline_status, evidence_required, confidence,
             user_confirmed, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'strategic_outcome', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'medium', ?, ?, ?, ?)
            """,
            (
                outcome_id, focus_id, str(pathway.get("title") or ""), str(pathway.get("desiredOutcome") or ""),
                str(pathway.get("desiredOutcome") or ""), "", "", "", json.dumps(as_list(pathway.get("beneficiaries"))), json.dumps([]),
                str(pathway.get("reviewDate") or ""), json.dumps(as_list(pathway.get("goodEnough"))), json.dumps(["Decision threshold not met"]),
                str(pathway.get("nonNegotiables") or ""), "", str(pathway.get("nonNegotiables") or ""), str(pathway.get("problemDefinition") or ""),
                "Evidence collected through experiment and metrics.", 1 if pathway.get("desiredOutcome") else 0, "draft", timestamp, timestamp,
            ),
        )
        for step_index, step in enumerate(as_list(pathway.get("backcastSteps")), start=1):
            db.execute("INSERT INTO backcast_steps (id, desired_outcome_id, title, description, sequence, preceding_condition, required_capability, required_evidence, decision_gate, risk, confidence, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'review', 'review', 'review', 'review', 'medium', 'draft', ?, ?)", (f"backcast-{focus_id}-{step_index}", outcome_id, step, step, step_index, step, timestamp, timestamp))
        decision_answers = pathway.get("decisionAnswers") if isinstance(pathway.get("decisionAnswers"), dict) else {}
        questions = {
            "clarity": "Is the problem sufficiently understood?",
            "evidence": "Is the evidence adequate?",
            "agreement": "Do relevant stakeholders agree on the framing?",
            "alignment": "Does it align with organisational strategy?",
            "influence": "Can the organisation influence it?",
            "capability": "Does the organisation have the required capability?",
            "risk": "Is the risk acceptable?",
            "testable": "Can the proposed response be tested?",
        }
        for key, text in questions.items():
            db.execute("INSERT INTO decision_assessments (id, selected_problem_focus_id, question_key, question_text, answer, rationale, evidence_ids, confidence, rule_version, recommended_outcome, user_decision, user_notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'medium', 'rules-page6-v1', ?, ?, '', ?, ?)", (f"decision-assessment-{focus_id}-{key}", focus_id, key, text, str(decision_answers.get(key) or decision_answers.get(f"decision-{key}") or ""), "Captured through Page 6 decision tree.", json.dumps([]), str(pathway.get("decisionOutcome") or ""), str(pathway.get("decisionOutcome") or ""), timestamp, timestamp))
        db.execute("INSERT INTO decision_results (id, selected_problem_focus_id, system_recommendation, final_decision, rationale, blocking_conditions, enabling_conditions, required_next_actions, confidence, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'medium', ?, ?, ?)", (f"decision-result-{focus_id}", focus_id, str(pathway.get("decisionOutcome") or ""), str(pathway.get("decisionOutcome") or ""), str(pathway.get("decisionRationale") or ""), json.dumps([]), json.dumps(["Owner, evidence and review cadence required"]), json.dumps(as_list(pathway.get("backcastSteps"))), 1 if pathway.get("decisionOutcome") else 0, timestamp, timestamp))
        db.execute(
            """
            INSERT INTO intervention_pathways
            (id, selected_problem_focus_id, desired_outcome_id, title, description, pathway_type, theory_of_change, response_archetype,
             current_maturity, target_maturity, complexity_fit, system_level, primary_driver, required_capabilities, required_partners,
             resource_estimate, cost_range, time_horizon, expected_benefits, potential_harms, trade_offs, rebound_risks, dependencies,
             confidence, generation_method, rationale, status, user_decision, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'review', ?, 'pathway', ?, ?, ?, 'review', 'review', ?, ?, ?, ?, ?, ?, 'medium', 'rules_and_user', ?, ?, ?, ?, ?)
            """,
            (
                pathway_id, focus_id, outcome_id, str(pathway.get("title") or ""), str(pathway.get("problemDefinition") or ""),
                str(pathway.get("prototypeType") or recommended_intervention_family(pathway)), str(pathway.get("experiment", {}).get("hypothesis", "") if isinstance(pathway.get("experiment"), dict) else ""),
                ",".join(as_list(pathway.get("archetypes"))), str(pathway.get("spectrum") or ""), str(pathway.get("cynefin") or ""),
                str(pathway.get("decisionOutcome") or ""), json.dumps(as_list(pathway.get("changes"))), json.dumps(as_list(pathway.get("beneficiaries"))),
                str(pathway.get("timeframe") or ""), json.dumps(as_list(pathway.get("desiredOutcome"))), json.dumps([]), json.dumps([]), json.dumps([]),
                json.dumps([]), str(pathway.get("decisionRationale") or ""), "selected" if pathway.get("selectedInterventionId") else "draft",
                str(pathway.get("selectedInterventionId") or ""), timestamp, timestamp,
            ),
        )
        option_ids = []
        for option_index, option in enumerate([o for o in pathway.get("interventionOptions", []) if isinstance(o, dict)], start=1):
            option_id = f"intervention-option-{pathway_id}-{slugify(str(option.get('id') or option_index))}"
            option_ids.append(option_id)
            db.execute("INSERT INTO intervention_options (id, intervention_pathway_id, title, description, intervention_type, expected_outcome, effort, cost_range, time_to_learn, time_to_impact, reversibility, implementation_risk, evidence_strength, stakeholder_acceptability, ecological_alignment, strategic_alignment, capability_fit, dependency_risk, confidence, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'review', 'short', 'review', 'medium', ?, 'review', 'review', 'review', 'review', 'review', 'review', 'medium', ?, ?, ?)", (option_id, pathway_id, str(option.get("title") or ""), str(option.get("description") or ""), str(option.get("family") or ""), str(option.get("mechanism") or ""), int(option.get("effort") or 3), int(option.get("risk") or 2), str(option.get("status") or "suggested"), timestamp, timestamp))
            for tool_name in as_list(option.get("tools")):
                tool_row = db.execute("SELECT id FROM tool_definitions WHERE name = ? LIMIT 1", (tool_name,)).fetchone()
                db.execute("INSERT OR REPLACE INTO tool_recommendations (id, selected_problem_focus_id, tool_definition_id, reason, trigger_inputs, prerequisites_met, missing_prerequisites, confidence, limitations, alternative_tool_ids, status, user_decision, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, 'medium', ?, ?, 'suggested', 'pending_review', ?, ?)", (f"tool-rec-{focus_id}-{slugify(tool_name)}", focus_id, tool_row["id"] if tool_row else None, f"{tool_name} supports this pathway's selected intervention family.", json.dumps({"tool": tool_name, "pathway": pathway.get("id")}), json.dumps(["confirm evidence and owner"]), json.dumps(["Tool guidance is not a final intervention decision."]), json.dumps([]), timestamp, timestamp))
        if len(option_ids) >= 2:
            db.execute("INSERT INTO intervention_comparisons (id, selected_problem_focus_id, option_a_id, option_b_id, comparison_dimensions, advantages, limitations, trade_offs, preferred_option_id, decision_rationale, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"comparison-{focus_id}", focus_id, option_ids[0], option_ids[1], json.dumps(["impact", "effort", "risk", "learning"]), json.dumps(["Compare visible pathway options before committing."]), json.dumps(["Scores are qualitative."]), json.dumps(["Review trade-offs before implementation."]), option_ids[0] if pathway.get("selectedInterventionId") else None, "Preferred option follows current user selection if present.", 1 if pathway.get("selectedInterventionId") else 0, timestamp, timestamp))
        horizon_id_map = {}
        for h_index, horizon in enumerate([h for h in pathway.get("horizons", []) if isinstance(h, dict)], start=1):
            horizon_id = f"horizon-{pathway_id}-{slugify(str(horizon.get('type') or h_index))}"
            horizon_id_map[str(horizon.get("type") or h_index)] = horizon_id
            db.execute("INSERT INTO horizons (id, intervention_pathway_id, horizon, title, description, objective, start_date, target_date, required_capabilities, required_evidence, required_partners, owner_id, status, sequence, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, 'draft', ?, 'medium', ?, ?)", (horizon_id, pathway_id, str(horizon.get("type") or h_index), str(horizon.get("title") or ""), "; ".join(as_list(horizon.get("actions"))), str(horizon.get("objective") or ""), str(horizon.get("decisionDate") or ""), json.dumps(as_list(horizon.get("resources"))), json.dumps(as_list(horizon.get("measures"))), json.dumps(as_list(horizon.get("participants"))), str(horizon.get("owner") or ""), h_index, timestamp, timestamp))
        horizon_values = list(horizon_id_map.values())
        for dep_index in range(len(horizon_values) - 1):
            db.execute("INSERT INTO horizon_dependencies (id, source_horizon_item_id, target_horizon_item_id, relationship_type, rationale, created_at, updated_at) VALUES (?, ?, ?, 'precedes', 'Later horizon depends on evidence and capability from earlier horizon.', ?, ?)", (f"horizon-dependency-{pathway_id}-{dep_index}", horizon_values[dep_index], horizon_values[dep_index + 1], timestamp, timestamp))
        experiment = pathway.get("experiment") if isinstance(pathway.get("experiment"), dict) else {}
        prototype_id = f"prototype-plan-{pathway_id}"
        experiment_id = f"experiment-{pathway_id}"
        db.execute("INSERT INTO prototype_plans (id, intervention_pathway_id, prototype_type, title, description, purpose, assumption_tested, learning_objective, fidelity, audience, setting, duration, resources_required, ethical_considerations, accessibility_considerations, risk_level, status, user_selected, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'Reduce uncertainty through a contained test.', ?, ?, 'low-to-medium', 'affected stakeholders', 'controlled setting', 'short experiment', ?, 'Review consent, fairness and unintended consequences.', 'Use accessible participation formats.', 'review', ?, ?, ?, ?)", (prototype_id, pathway_id, str(pathway.get("prototypeType") or ""), str(experiment.get("title") or ""), str(experiment.get("method") or ""), str(experiment.get("hypothesis") or ""), str(experiment.get("learningObjective") or ""), json.dumps([]), str(experiment.get("status") or "draft"), 1 if pathway.get("prototypeType") else 0, timestamp, timestamp))
        assumption_id = f"assumption-{focus_id}"
        db.execute("INSERT INTO intervention_assumptions (id, selected_problem_focus_id, statement, assumption_type, criticality, uncertainty, consequence_if_wrong, status, created_at, updated_at) VALUES (?, ?, ?, 'prototype', 'high', 'review', ?, 'untested', ?, ?)", (assumption_id, focus_id, str(experiment.get("hypothesis") or "The proposed intervention can improve decision confidence."), "The pathway may not create the desired outcome or may create unintended consequences.", timestamp, timestamp))
        db.execute("INSERT INTO experiments (id, prototype_plan_id, selected_problem_focus_id, title, hypothesis, learning_objective, method, decision_threshold, start_date, end_date, status, owner, review_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (experiment_id, prototype_id, focus_id, str(experiment.get("title") or ""), str(experiment.get("hypothesis") or ""), str(experiment.get("learningObjective") or ""), str(experiment.get("method") or ""), str(experiment.get("decisionThreshold") or ""), str(experiment.get("startDate") or ""), str(experiment.get("endDate") or ""), str(experiment.get("status") or "draft"), str(pathway.get("owners", {}).get("experimentOwner", "") if isinstance(pathway.get("owners"), dict) else ""), str(pathway.get("reviewDate") or ""), timestamp, timestamp))
        db.execute("INSERT INTO experiment_hypotheses (id, experiment_id, assumption_id, hypothesis_statement, expected_observation, falsification_condition, confidence_before, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'Evidence improves and stakeholders can observe a useful change.', 'Decision threshold is not met or risks become unacceptable.', 'medium', 'draft', ?, ?)", (f"hypothesis-{experiment_id}", experiment_id, assumption_id, str(experiment.get("hypothesis") or ""), timestamp, timestamp))
        for metric_index, metric in enumerate([m for m in pathway.get("metrics", []) if isinstance(m, dict)], start=1):
            db.execute("INSERT INTO experiment_metrics (id, experiment_id, metric_name, metric_category, target_value, measurement_method, data_owner, frequency, confidence, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'manual review', ?, 'review cadence', 'medium', 'draft', ?, ?)", (f"metric-{experiment_id}-{metric_index}", experiment_id, str(metric.get("name") or ""), str(metric.get("category") or ""), str(metric.get("target") or ""), str(metric.get("owner") or ""), timestamp, timestamp))
        for risk_index, risk in enumerate([r for r in pathway.get("risks", []) if isinstance(r, dict)], start=1):
            db.execute("INSERT INTO intervention_risks (id, selected_problem_focus_id, intervention_pathway_id, experiment_id, risk_category, description, likelihood, severity, mitigation, owner, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)", (f"risk-{focus_id}-{risk_index}", focus_id, pathway_id, experiment_id, str(risk.get("category") or "risk"), str(risk.get("description") or ""), int(risk.get("likelihood") or 2), int(risk.get("severity") or 2), str(risk.get("mitigation") or ""), str(risk.get("owner") or ""), timestamp, timestamp))
        owners = pathway.get("owners") if isinstance(pathway.get("owners"), dict) else {}
        db.execute("INSERT INTO pathway_ownership (id, selected_problem_focus_id, executive_sponsor, pathway_owner, experiment_owner, decision_maker, data_owner, risk_owner, governance_cadence, review_date, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)", (f"ownership-{focus_id}", focus_id, str(owners.get("executiveSponsor") or ""), str(owners.get("pathwayOwner") or ""), str(owners.get("experimentOwner") or ""), str(owners.get("decisionMaker") or ""), str(owners.get("dataOwner") or ""), str(owners.get("riskOwner") or ""), str(owners.get("cadence") or ""), str(pathway.get("reviewDate") or ""), timestamp, timestamp))
        db.execute("INSERT INTO experiment_reviews (id, experiment_id, review_date, result_status, result_summary, evidence_collected, decision, decision_rationale, next_actions, user_confirmed, created_at, updated_at) VALUES (?, ?, ?, 'planned', 'Review pending.', ?, 'review', ?, ?, 0, ?, ?)", (f"review-{experiment_id}", experiment_id, str(pathway.get("reviewDate") or ""), json.dumps([]), str(experiment.get("decisionThreshold") or ""), json.dumps(as_list(pathway.get("backcastSteps"))), timestamp, timestamp))
        db.execute("INSERT INTO learning_records (id, intervention_state_id, experiment_id, selected_problem_focus_id, learning_type, title, summary, evidence_ids, confidence, affects_stage, recommended_revisit, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'planned_learning', ?, ?, ?, 'medium', 'reflect-evolve', 'Review after experiment result.', 'planned', ?, ?)", (f"learning-{experiment_id}", state_id, experiment_id, focus_id, f"Learning plan for {pathway.get('title')}", str(experiment.get("learningObjective") or ""), json.dumps([]), timestamp, timestamp))
    for output_type, payload in analysis.get("outputs", {}).items():
        db.execute("INSERT INTO intervention_outputs (id, intervention_state_id, output_type, title, payload, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?)", (f"output-{state_id}-{slugify(output_type)}", state_id, output_type, output_type.replace("_", " ").title(), json.dumps(payload), timestamp, timestamp))
    db.execute("INSERT OR REPLACE INTO complete_journey_records (id, intervention_state_id, organisation_id, journey_id, journey_summary, learning_loop_status, next_review_date, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'ongoing', '', 'draft', ?, ?)", (f"complete-journey-{state_id}", state_id, context.get("organisationId"), context.get("journeyId"), json.dumps({"summary": "Green Spectrum pathway portfolio created.", "outputs": analysis.get("outputs", {})}), timestamp, timestamp))
    if source.get("found"):
        db.execute("INSERT INTO intervention_import_records (id, intervention_state_id, source_type, source_id, source_version, imported_payload, imported_count, conflict_count, stale_count, status, created_at) VALUES (?, ?, 'page5', ?, ?, ?, ?, 0, ?, 'imported', ?)", ("intervention-import-" + secrets.token_hex(12), state_id, source.get("sourcePriorityStateId"), str(source.get("versionNumber") or ""), json.dumps(source), len(form_data.get("pathways", [])), 1 if source.get("stale") else 0, timestamp))


def validate_intervention_completion(form_data: dict, source: dict) -> dict:
    pathways = [p for p in form_data.get("pathways", []) if isinstance(p, dict)]
    blocking = []
    warnings = []
    if not source.get("found"):
        blocking.append("No completed Page 5 handover source was found.")
    if source.get("found") and not source.get("confirmed"):
        blocking.append("Page 5 handover is not confirmed.")
    if not pathways:
        blocking.append("At least one intervention pathway is required.")
    if not any(p.get("completed") for p in pathways):
        blocking.append("At least one pathway must be confirmed.")
    for pathway in pathways:
        owners = pathway.get("owners") if isinstance(pathway.get("owners"), dict) else {}
        experiment = pathway.get("experiment") if isinstance(pathway.get("experiment"), dict) else {}
        if pathway.get("completed") and not owners.get("pathwayOwner"):
            blocking.append(f"{pathway.get('title', 'A pathway')} needs a pathway owner.")
        if pathway.get("completed") and not owners.get("experimentOwner"):
            blocking.append(f"{pathway.get('title', 'A pathway')} needs an experiment owner.")
        if pathway.get("completed") and not experiment.get("hypothesis"):
            blocking.append(f"{pathway.get('title', 'A pathway')} needs an experiment hypothesis.")
        if pathway.get("completed") and not experiment.get("decisionThreshold"):
            blocking.append(f"{pathway.get('title', 'A pathway')} needs a decision threshold.")
        if pathway.get("completed") and len([m for m in pathway.get("metrics", []) if isinstance(m, dict) and m.get("name") and m.get("target")]) < 1:
            blocking.append(f"{pathway.get('title', 'A pathway')} needs at least one measurable metric with a target.")
        if pathway.get("completed") and len([r for r in pathway.get("risks", []) if isinstance(r, dict) and r.get("description") and r.get("mitigation")]) < 1:
            blocking.append(f"{pathway.get('title', 'A pathway')} needs at least one risk with a mitigation.")
        if pathway.get("completed") and not pathway.get("reviewDate"):
            warnings.append(f"{pathway.get('title', 'A pathway')} has no review date.")
    if not form_data.get("reviewed"):
        blocking.append("The final intervention review confirmation is required.")
    if intervention_completion(form_data) < 85:
        blocking.append("Prototype plan is not complete enough to finish; outcome, selected intervention, owners, metrics, risks and review are required.")
    return {"valid": not blocking, "blockingIssues": blocking, "warnings": warnings}


def final_journey_manifest(state_id: str, form_data: dict, analysis: dict, status: str) -> dict:
    return {
        "source": {"page": "prototype", "interventionStateId": state_id, "status": status, "generatedAt": now_iso()},
        "pathways": form_data.get("pathways", []),
        "primaryPathwayIds": form_data.get("primaryIds", []),
        "strategySummary": analysis.get("outputs", {}).get("strategySummary", {}),
        "experimentPack": analysis.get("outputs", {}).get("experimentPack", []),
        "threeHorizonsRoadmap": analysis.get("outputs", {}).get("threeHorizonsRoadmap", []),
        "learningPlan": analysis.get("outputs", {}).get("learningPlan", []),
        "metricPlan": analysis.get("outputs", {}).get("metricPlan", []),
        "riskRegister": analysis.get("outputs", {}).get("riskRegister", []),
        "portfolioWarnings": analysis.get("portfolioWarnings", []),
        "reflectLearnEvolve": {
            "status": "ongoing",
            "principle": "Begin experiments, collect evidence, update organisational knowledge, and revisit earlier Green Spectrum stages when learning changes the system.",
        },
    }


def save_intervention_state(payload: dict, status: str = "draft") -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    journey_id = str(payload.get("journeyId", "")) or None
    form_data = normalise_intervention_form(payload)
    with connect() as db:
        state_id, context, version = get_or_create_intervention_state(db, session_id, journey_id, payload)
        existing = db.execute("SELECT status FROM intervention_states WHERE id = ?", (state_id,)).fetchone()
        if existing and existing["status"] == "completed" and status != "completed":
            return {"ok": False, "error": "Completed intervention state must be reopened before editing.", "stateId": state_id}
        source = latest_priority_handover(db, session_id, context.get("journeyId"))
        if not form_data["pathways"]:
            pathways, source = import_intervention_pathways_from_priority(db, session_id, context.get("journeyId"))
            form_data["pathways"] = pathways
            form_data["primaryIds"] = [p["id"] for p in pathways[:3]]
            form_data["activeId"] = pathways[0]["id"] if pathways else ""
        analysis = analyse_intervention_state(form_data, source)
        validation = validate_intervention_completion(form_data, source) if status == "completed" else {"valid": True, "blockingIssues": [], "warnings": []}
        if status == "completed" and not validation["valid"]:
            return {"ok": False, "stateId": state_id, "validation": validation, "analysis": analysis}
        timestamp = now_iso()
        row = db.execute("SELECT autosave_revision, created_at FROM intervention_states WHERE id = ?", (state_id,)).fetchone()
        revision = int(row["autosave_revision"]) + 1 if row else 1
        created_at = row["created_at"] if row else timestamp
        final_status = "completed" if status == "completed" else "draft"
        clear_intervention_children(db, state_id)
        db.execute(
            """
            INSERT OR REPLACE INTO intervention_states
            (id, anonymous_session_id, organisation_id, journey_id, methodology_version_id, version_number, source_priority_state_id,
             source_priority_portfolio_id, title, description, status, completion_percentage, current_section, autosave_revision,
             form_snapshot, analysis_snapshot, last_saved_at, completed_at, completed_by, is_stale, stale_reason, review_required,
             created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Decide, Prototype and Experiment', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id, session_id, context.get("organisationId"), context.get("journeyId"), context.get("methodologyVersionId"), version,
                source.get("sourcePriorityStateId") or form_data.get("sourcePriorityStateId"), source.get("sourcePriorityPortfolioId") or form_data.get("sourcePriorityPortfolioId"),
                "Page 6 final pathway, experiment and learning portfolio.", final_status, 100 if final_status == "completed" else analysis.get("completionPercentage", 0),
                str(payload.get("section") or "review"), revision, json.dumps(form_data), json.dumps(analysis), timestamp,
                timestamp if final_status == "completed" else None, session_id if final_status == "completed" else None, 1 if source.get("stale") else 0,
                "Upstream Page 5 handover is stale." if source.get("stale") else "", 1 if source.get("stale") else 0,
                session_id, session_id, created_at, timestamp, json.dumps({"authMode": "anonymous-local", "warnings": validation.get("warnings", [])}),
            ),
        )
        insert_intervention_children(db, state_id, context, form_data, analysis, source)
        manifest = final_journey_manifest(state_id, form_data, analysis, final_status)
        db.execute("INSERT OR REPLACE INTO intervention_outputs (id, intervention_state_id, output_type, title, payload, status, created_at, updated_at) VALUES (?, ?, 'complete_journey', 'Complete Journey Report', ?, ?, ?, ?)", (f"output-{state_id}-complete-journey", state_id, json.dumps(manifest), final_status, timestamp, timestamp))
        if final_status == "completed":
            db.execute("UPDATE journey_progress SET status = 'completed', completion_percentage = 100, completed_at = ?, last_visited_at = ?, output_summary = ? WHERE journey_id = ? AND stage_key = 'decide-experiment'", (timestamp, timestamp, json.dumps({"interventionStateId": state_id, "pathways": len(form_data.get("pathways", []))}), context.get("journeyId")))
        db.execute("INSERT INTO audit_logs (id, actor_type, actor_id, action, entity_type, entity_id, metadata, occurred_at) VALUES (?, 'anonymous_session', ?, ?, 'intervention_state', ?, ?, ?)", ("audit-" + secrets.token_hex(12), session_id, "complete_intervention_state" if final_status == "completed" else "autosave_intervention_state", state_id, json.dumps({"status": final_status, "revision": revision}), timestamp))
    return {"ok": True, "stateId": state_id, "status": final_status, "versionNumber": version, "autosaveRevision": revision, "formData": form_data, "analysis": analysis, "manifest": manifest, "validation": validation}


def get_intervention_state(session_id: str, journey_id: str | None = None, state_id: str | None = None) -> dict:
    session_id = session_id[:80] or "anonymous-local"
    with connect() as db:
        row = None
        if state_id:
            row = db.execute("SELECT * FROM intervention_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            row = db.execute(
                """
                SELECT * FROM intervention_states
                WHERE anonymous_session_id = ? AND COALESCE(journey_id, '') = COALESCE(?, '')
                ORDER BY CASE status WHEN 'draft' THEN 0 WHEN 'active' THEN 1 WHEN 'completed' THEN 2 ELSE 3 END, updated_at DESC
                LIMIT 1
                """,
                (session_id, journey_id),
            ).fetchone()
        context = resolve_priority_context(db, session_id, journey_id)
        pathways, source = import_intervention_pathways_from_priority(db, session_id, context.get("journeyId"))
    if not row:
        form_data = {"pathways": pathways, "activeId": pathways[0]["id"] if pathways else "", "primaryIds": [p["id"] for p in pathways[:3]], "reviewed": False, "sourcePriorityStateId": source.get("sourcePriorityStateId"), "sourcePriorityPortfolioId": source.get("sourcePriorityPortfolioId")}
        return {"ok": True, "found": False, "formData": form_data, "analysis": analyse_intervention_state(form_data, source), "source": source, "context": context}
    return {
        "ok": True,
        "found": True,
        "stateId": row["id"],
        "status": row["status"],
        "versionNumber": row["version_number"],
        "autosaveRevision": row["autosave_revision"],
        "formData": json_loads_safe(row["form_snapshot"], {}),
        "analysis": json_loads_safe(row["analysis_snapshot"], {}),
        "source": source,
        "context": context,
        "updatedAt": row["updated_at"],
    }


def import_page5_to_intervention(state_id: str, payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    with connect() as db:
        row = db.execute("SELECT id, journey_id FROM intervention_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            return {"ok": False, "error": "Intervention state not found."}
        pathways, source = import_intervention_pathways_from_priority(db, session_id, row["journey_id"])
        timestamp = now_iso()
        db.execute("INSERT INTO intervention_import_records (id, intervention_state_id, source_type, source_id, source_version, imported_payload, imported_count, conflict_count, stale_count, status, created_at) VALUES (?, ?, 'page5', ?, ?, ?, ?, 0, ?, 'imported', ?)", ("intervention-import-" + secrets.token_hex(12), state_id, source.get("sourcePriorityStateId"), str(source.get("versionNumber") or ""), json.dumps(source), len(pathways), 1 if source.get("stale") else 0, timestamp))
    return {"ok": True, "stateId": state_id, "pathways": pathways, "source": source}


def reopen_intervention_state(state_id: str, payload: dict) -> dict:
    session_id = str(payload.get("anonymousSessionId", ""))[:80] or "anonymous-local"
    reason = str(payload.get("revisionReason") or "Reopened for editing")
    with connect() as db:
        row = db.execute("SELECT * FROM intervention_states WHERE id = ? AND anonymous_session_id = ?", (state_id, session_id)).fetchone()
        if not row:
            return {"ok": False, "error": "Intervention state not found."}
        new_id = "intervention-" + secrets.token_hex(12)
        timestamp = now_iso()
        db.execute(
            """
            INSERT INTO intervention_states
            (id, anonymous_session_id, organisation_id, journey_id, methodology_version_id, version_number, source_priority_state_id,
             source_priority_portfolio_id, title, description, status, completion_percentage, current_section, autosave_revision,
             form_snapshot, analysis_snapshot, last_saved_at, reopened_at, reopened_by, revision_reason, is_stale, stale_reason,
             review_required, created_by, updated_by, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, 1, ?, ?, ?, ?, ?, ?, 0, '', 0, ?, ?, ?, ?, ?)
            """,
            (new_id, row["anonymous_session_id"], row["organisation_id"], row["journey_id"], row["methodology_version_id"], int(row["version_number"]) + 1, row["source_priority_state_id"], row["source_priority_portfolio_id"], row["title"], row["description"], row["completion_percentage"], row["current_section"], row["form_snapshot"], row["analysis_snapshot"], timestamp, timestamp, session_id, reason, session_id, session_id, timestamp, timestamp, row["metadata"]),
        )
    return {"ok": True, "stateId": new_id, "status": "draft"}


def export_intervention_state(state_id: str, session_id: str) -> dict:
    data = get_intervention_state(session_id, state_id=state_id)
    if not data.get("found"):
        return {"ok": False, "error": "Intervention state not found."}
    with connect() as db:
        counts = {}
        for table in ["selected_problem_focus", "desired_outcomes", "intervention_pathways", "intervention_options", "prototype_plans", "experiments", "experiment_metrics", "intervention_risks", "learning_records", "intervention_outputs"]:
            if table in {"selected_problem_focus", "learning_records", "intervention_outputs"}:
                count = db.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE intervention_state_id = ?", (state_id,)).fetchone()["count"]
            elif table == "desired_outcomes":
                count = db.execute("SELECT COUNT(*) AS count FROM desired_outcomes WHERE selected_problem_focus_id IN (SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?)", (state_id,)).fetchone()["count"]
            elif table == "intervention_pathways":
                count = db.execute("SELECT COUNT(*) AS count FROM intervention_pathways WHERE selected_problem_focus_id IN (SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?)", (state_id,)).fetchone()["count"]
            elif table == "intervention_options":
                count = db.execute("SELECT COUNT(*) AS count FROM intervention_options WHERE intervention_pathway_id IN (SELECT id FROM intervention_pathways WHERE selected_problem_focus_id IN (SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?))", (state_id,)).fetchone()["count"]
            elif table == "prototype_plans":
                count = db.execute("SELECT COUNT(*) AS count FROM prototype_plans WHERE intervention_pathway_id IN (SELECT id FROM intervention_pathways WHERE selected_problem_focus_id IN (SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?))", (state_id,)).fetchone()["count"]
            elif table in {"experiments", "intervention_risks"}:
                count = db.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE selected_problem_focus_id IN (SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?)", (state_id,)).fetchone()["count"]
            else:
                count = db.execute("SELECT COUNT(*) AS count FROM experiment_metrics WHERE experiment_id IN (SELECT id FROM experiments WHERE selected_problem_focus_id IN (SELECT id FROM selected_problem_focus WHERE intervention_state_id = ?))", (state_id,)).fetchone()["count"]
            counts[table] = count
    return {"ok": True, "exportedAt": now_iso(), "format": "green-spectrum-intervention-json-v1", "counts": counts, **data}


class GreenSpectrumHandler(BaseHTTPRequestHandler):
    server_version = "GreenSpectrumLocal/0.1"

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def send_json(self, status: int, data: object) -> None:
        body = json_dumps(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, path: Path, head_only: bool = False) -> None:
        if path.is_dir():
            path = path / "index.html"
        if not path.exists() or not path.is_file() or ROOT not in path.resolve().parents and path.resolve() != ROOT:
            self.send_error(404, "Not found")
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if route == "/api/health":
            try:
                with connect() as db:
                    db.execute("SELECT 1").fetchone()
                self.send_json(200, {"ok": True, "database": "available", "storage": "local", "contentService": "available"})
            except sqlite3.Error as exc:
                self.send_json(503, {"ok": False, "database": "unavailable", "error": str(exc)})
            return
        if route == "/api/public/landing":
            self.send_json(200, public_landing())
            return
        if route == "/api/public/resources/featured":
            self.send_json(200, featured_resources())
            return
        if route == "/api/public/data-sources/catalogue":
            self.send_json(200, external_source_catalogue(query))
            return
        if route == "/api/public/resources/bundle/download":
            data = featured_resources()
            if data["bundle"]["available"]:
                expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                self.send_json(200, {"available": True, "downloadUrl": data["bundle"].get("downloadUrl") or "/downloads/green-spectrum-mvp-resources.zip", "expiresAt": expires})
            else:
                self.send_json(200, {"available": False, "route": "/resources", "message": "Downloads are temporarily unavailable. Please browse the Resources library."})
            return
        if route.startswith("/api/public/resources/") and route.endswith("/download"):
            slug = route.removeprefix("/api/public/resources/").removesuffix("/download").strip("/")
            with connect() as db:
                resource = db.execute(
                    "SELECT title, slug, category, file_type AS fileType, file_size AS fileSize, storage_key AS storageKey FROM resources WHERE slug = ? AND active = 1",
                    (slug,),
                ).fetchone()
            if not resource:
                self.send_json(404, {"available": False, "message": "Resource not found."})
            else:
                resource_data = dict(resource)
                self.send_json(200, {"available": bool(resource_data.get("storageKey")), "resource": resource_data, "downloadUrl": f"/{resource_data.get('storageKey')}" if resource_data.get("storageKey") else "", "message": "" if resource_data.get("storageKey") else "This resource has metadata, but no downloadable asset is attached yet."})
            return
        if route == "/api/session/journey-entry":
            self.send_json(200, journey_entry(query))
            return
        if route == "/api/onboarding/state":
            session_id = query.get("anonymousSessionId", [""])[0]
            self.send_json(200, get_onboarding_state(session_id))
            return
        if route == "/api/explore/business/state":
            session_id = query.get("anonymousSessionId", [""])[0]
            self.send_json(200, get_explore_business(session_id))
            return
        if route.endswith("/explore/human/bootstrap") or route.endswith("/human/summary") or route.endswith("/human/export"):
            session_id = query.get("anonymousSessionId", [""])[0]
            self.send_json(200, get_explore_business(session_id))
            return
        if "/human/questions" in route:
            self.send_json(200, {"ok": True, "questions": [{"id": item, "empathy": "human"} for item in range(17, 22)]})
            return
        if route in {"/api/intelligence/graph", "/intelligence/graph"}:
            session_id = query.get("anonymousSessionId", [""])[0]
            result = get_intelligence(session_id)
            graph = result.get("intelligence", {}).get("graph", {}) if result.get("found") else {}
            self.send_json(200, {"ok": True, "found": result.get("found", False), "graph": graph})
            return
        if route in {"/api/intelligence/themes", "/intelligence/themes"}:
            session_id = query.get("anonymousSessionId", [""])[0]
            result = get_intelligence(session_id)
            self.send_json(200, {"ok": True, "found": result.get("found", False), "themes": result.get("intelligence", {}).get("themes", []) if result.get("found") else []})
            return
        if route in {"/api/intelligence/patterns", "/intelligence/patterns"}:
            session_id = query.get("anonymousSessionId", [""])[0]
            result = get_intelligence(session_id)
            self.send_json(200, {"ok": True, "found": result.get("found", False), "patterns": result.get("intelligence", {}).get("patterns", []) if result.get("found") else []})
            return
        if route in {"/api/intelligence/capabilities", "/intelligence/capabilities"}:
            session_id = query.get("anonymousSessionId", [""])[0]
            result = get_intelligence(session_id)
            self.send_json(200, {"ok": True, "found": result.get("found", False), "capabilities": result.get("intelligence", {}).get("capabilities", []) if result.get("found") else []})
            return
        if route in {"/api/intelligence/relationships", "/intelligence/relationships"}:
            session_id = query.get("anonymousSessionId", [""])[0]
            result = get_intelligence(session_id)
            relationships = result.get("intelligence", {}).get("graph", {}).get("relationships", []) if result.get("found") else []
            self.send_json(200, {"ok": True, "found": result.get("found", False), "relationships": relationships})
            return
        if route in {"/api/intelligence/history", "/intelligence/history"}:
            session_id = query.get("anonymousSessionId", [""])[0]
            result = get_intelligence(session_id)
            self.send_json(200, {"ok": True, "found": result.get("found", False), "history": [result] if result.get("found") else []})
            return
        parts = route.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "journeys"] and parts[3] == "impact-journey":
            session_id = query.get("anonymousSessionId", [""])[0]
            self.send_json(200, get_impact_journey(session_id, journey_id=parts[2]))
            return
        if len(parts) >= 3 and parts[:2] == ["api", "impact-journeys"]:
            state_id = parts[2]
            session_id = query.get("anonymousSessionId", [""])[0]
            if len(parts) == 3:
                self.send_json(200, get_impact_journey(session_id, state_id=state_id))
                return
            if len(parts) == 4 and parts[3] == "export":
                self.send_json(200, export_impact_journey(state_id, session_id))
                return
            if len(parts) == 4 and parts[3] == "page-5-handover":
                self.send_json(200, page5_handover(state_id, session_id))
                return
        if len(parts) == 4 and parts[:2] == ["api", "journeys"] and parts[3] == "prioritisation":
            session_id = query.get("anonymousSessionId", [""])[0]
            self.send_json(200, get_priority_state(session_id, journey_id=parts[2]))
            return
        if len(parts) >= 3 and parts[:2] == ["api", "prioritisation"]:
            priority_state_id = parts[2]
            session_id = query.get("anonymousSessionId", [""])[0]
            if len(parts) == 3:
                self.send_json(200, get_priority_state(session_id, state_id=priority_state_id))
                return
            if len(parts) == 4 and parts[3] == "export":
                self.send_json(200, export_priority_state(priority_state_id, session_id))
                return
            if len(parts) == 4 and parts[3] == "page-6-handover":
                self.send_json(200, page6_handover(priority_state_id, session_id))
                return
            if len(parts) == 4 and parts[3] in {"merge-candidates", "priority-views"}:
                data = get_priority_state(session_id, state_id=priority_state_id)
                analysis = data.get("analysis", {}) if data.get("found") or "analysis" in data else {}
                key = "duplicatePairs" if parts[3] == "merge-candidates" else "recommendations"
                self.send_json(200, {"ok": True, key: analysis.get(key, []) if isinstance(analysis, dict) else []})
                return
        if len(parts) == 4 and parts[:2] == ["api", "journeys"] and parts[3] == "interventions":
            session_id = query.get("anonymousSessionId", [""])[0]
            self.send_json(200, get_intervention_state(session_id, journey_id=parts[2]))
            return
        if len(parts) >= 3 and parts[:2] == ["api", "interventions"]:
            intervention_state_id = parts[2]
            session_id = query.get("anonymousSessionId", [""])[0]
            if len(parts) == 3:
                self.send_json(200, get_intervention_state(session_id, state_id=intervention_state_id))
                return
            if len(parts) == 4 and parts[3] == "export":
                self.send_json(200, export_intervention_state(intervention_state_id, session_id))
                return

        raw_path = unquote(parsed.path.lstrip("/"))
        static_path = ROOT / raw_path if raw_path else ROOT / "index.html"
        self.send_static(static_path)

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        raw_path = unquote(parsed.path.lstrip("/"))
        static_path = ROOT / raw_path if raw_path else ROOT / "index.html"
        self.send_static(static_path, head_only=True)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_json(400, {"ok": False, "error": "Invalid JSON"})
            return
        if route == "/api/analytics/events":
            self.send_json(200, record_analytics(payload))
            return
        if route == "/api/consent":
            anonymous_session_id = str(payload.get("anonymousSessionId", ""))[:80]
            consent = payload.get("consent") if isinstance(payload.get("consent"), dict) else {}
            with connect() as db:
                for consent_type, granted in consent.items():
                    db.execute(
                        """
                        INSERT INTO consent_records
                        (id, user_id, anonymous_session_id, consent_type, granted, version, created_at, updated_at)
                        VALUES (?, NULL, ?, ?, ?, '2026-07-landing-v1', ?, ?)
                        """,
                        ("consent-" + secrets.token_hex(12), anonymous_session_id, str(consent_type), 1 if granted else 0, now_iso(), now_iso()),
                    )
            self.send_json(200, {"ok": True})
            return
        if route == "/api/onboarding/autosave":
            self.send_json(200, save_onboarding_state(payload, status="draft"))
            return
        if route == "/api/onboarding/complete":
            self.send_json(200, complete_onboarding(payload))
            return
        if route == "/api/explore/business/autosave":
            self.send_json(200, save_explore_business(payload, status="draft"))
            return
        if route == "/api/explore/business/complete":
            self.send_json(200, save_explore_business(payload, status="business_complete"))
            return
        if route in {"/api/intelligence/update", "/intelligence/update"}:
            self.send_json(200, update_intelligence(payload))
            return
        if route == "/api/explore/human/autosave":
            self.send_json(200, save_explore_human(payload, status="draft"))
            return
        if route == "/api/explore/human/complete":
            self.send_json(200, save_explore_human(payload, status="human_complete"))
            return
        if route == "/api/explore/planetary/autosave":
            self.send_json(200, save_explore_planetary(payload, status="draft"))
            return
        if route == "/api/explore/planetary/complete":
            self.send_json(200, save_explore_planetary(payload, status="planetary_complete"))
            return
        if "/assessments/" in route and "/planetary" in route:
            self.send_json(200, save_explore_planetary(payload, status="draft"))
            return
        if "/assessments/" in route and "/human" in route:
            self.send_json(200, save_explore_human(payload, status="draft"))
            return
        if "/responses/" in route and any(suffix in route for suffix in ["/stakeholders", "/discovery", "/evidence", "/tools/recommend"]):
            self.send_json(200, save_explore_human(payload, status="draft"))
            return
        if route.startswith("/api/human-risk-flags/"):
            self.send_json(200, {"ok": True, "status": "updated"})
            return
        if route == "/api/impact-journey/autosave":
            self.send_json(200, save_impact_journey(payload, status="draft"))
            return
        if route == "/api/impact-journey/complete":
            self.send_json(200, save_impact_journey(payload, status="completed"))
            return
        parts = route.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "journeys"] and parts[3] == "impact-journey":
            payload["journeyId"] = parts[2]
            self.send_json(200, save_impact_journey(payload, status=str(payload.get("status") or "draft")))
            return
        if len(parts) >= 3 and parts[:2] == ["api", "impact-journeys"]:
            state_id = parts[2]
            payload["impactJourneyStateId"] = state_id
            if len(parts) == 3:
                self.send_json(200, save_impact_journey(payload, status=str(payload.get("status") or "draft")))
                return
            action = parts[3]
            if action == "autosave":
                self.send_json(200, save_impact_journey(payload, status="draft"))
                return
            if action == "complete":
                self.send_json(200, save_impact_journey(payload, status="completed"))
                return
            if action == "reopen":
                self.send_json(200, reopen_impact_journey(state_id, payload))
                return
            if action == "import-page-3":
                self.send_json(200, import_page3_to_impact(state_id, payload))
                return
            if action in {"stages", "activities", "decisions", "stakeholders", "inputs", "outputs", "impacts", "assumptions", "unknowns", "relationships", "feedback-loops", "hotspots", "leverage-points", "problem-signals"}:
                self.send_json(200, save_impact_journey(payload, status="draft"))
                return
            if action in {"generate-hotspots", "generate-leverage", "accept-hotspot", "edit-hotspot", "dismiss-hotspot", "confirm-leverage", "dismiss-leverage"}:
                self.send_json(200, save_impact_journey(payload, status="draft"))
                return
        if route == "/api/prioritisation/autosave":
            self.send_json(200, save_priority_state(payload, status="draft"))
            return
        if route == "/api/prioritisation/complete":
            self.send_json(200, save_priority_state(payload, status="completed"))
            return
        if len(parts) == 4 and parts[:2] == ["api", "journeys"] and parts[3] == "prioritisation":
            payload["journeyId"] = parts[2]
            self.send_json(200, save_priority_state(payload, status=str(payload.get("status") or "draft")))
            return
        if len(parts) >= 3 and parts[:2] == ["api", "prioritisation"]:
            priority_state_id = parts[2]
            payload["priorityStateId"] = priority_state_id
            if len(parts) == 3:
                self.send_json(200, save_priority_state(payload, status=str(payload.get("status") or "draft")))
                return
            action = parts[3]
            if action == "autosave":
                self.send_json(200, save_priority_state(payload, status="draft"))
                return
            if action == "complete":
                self.send_json(200, save_priority_state(payload, status="completed"))
                return
            if action == "reopen":
                self.send_json(200, reopen_priority_state(priority_state_id, payload))
                return
            if action == "import-page-4":
                self.send_json(200, import_page4_to_priority(priority_state_id, payload))
                return
            if action in {"problems", "generate-clusters", "clusters", "generate-recommendations", "portfolio", "confirm-page-6-handover", "autosave-section"}:
                self.send_json(200, save_priority_state(payload, status="draft"))
                return
        if len(parts) >= 3 and parts[0] == "api" and parts[1] in {"problems", "problem-evidence-links", "problem-relationships", "problem-merge-candidates", "problem-merges", "maturity-positioning", "complexity-assessments", "priority-assessments", "priority-weighting-profiles", "priority-clusters", "priority-recommendations", "priority-portfolios", "priority-portfolio-items"}:
            self.send_json(200, {"ok": True, "status": "accepted", "note": "Use prioritisation autosave to persist the current Page 5 frontend state."})
            return
        if route == "/api/interventions/autosave":
            self.send_json(200, save_intervention_state(payload, status="draft"))
            return
        if route == "/api/interventions/complete":
            self.send_json(200, save_intervention_state(payload, status="completed"))
            return
        if len(parts) == 4 and parts[:2] == ["api", "journeys"] and parts[3] == "interventions":
            payload["journeyId"] = parts[2]
            self.send_json(200, save_intervention_state(payload, status=str(payload.get("status") or "draft")))
            return
        if len(parts) >= 3 and parts[:2] == ["api", "interventions"]:
            intervention_state_id = parts[2]
            payload["interventionStateId"] = intervention_state_id
            if len(parts) == 3:
                self.send_json(200, save_intervention_state(payload, status=str(payload.get("status") or "draft")))
                return
            action = parts[3]
            if action == "autosave":
                self.send_json(200, save_intervention_state(payload, status="draft"))
                return
            if action == "complete":
                self.send_json(200, save_intervention_state(payload, status="completed"))
                return
            if action == "reopen":
                self.send_json(200, reopen_intervention_state(intervention_state_id, payload))
                return
            if action == "import-page-5":
                self.send_json(200, import_page5_to_intervention(intervention_state_id, payload))
                return
            if action in {"focus", "desired-outcomes", "backcast", "decision", "tools", "pathways", "options", "horizons", "prototypes", "assumptions", "experiments", "metrics", "risks", "ownership", "reviews", "learning-records", "outputs", "autosave-section"}:
                self.send_json(200, save_intervention_state(payload, status="draft"))
                return
        self.send_json(404, {"ok": False, "error": "Not found"})

    def do_PATCH(self) -> None:
        self.do_POST()


def main() -> None:
    seed_database()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), GreenSpectrumHandler)
    print(f"Green Spectrum server running at http://localhost:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
