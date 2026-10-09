PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS owner_profile (
  id INTEGER PRIMARY KEY,
  full_name TEXT,
  preferred_name TEXT,
  public_name TEXT,
  country TEXT,
  city TEXT,
  timezone TEXT,
  primary_email TEXT,
  phone TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  browser_profile TEXT,
  purpose TEXT,
  status TEXT NOT NULL DEFAULT 'unknown',
  permission_level TEXT DEFAULT 'unknown',
  last_verified_at TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY,
  name TEXT,
  phone TEXT,
  email TEXT,
  relationship TEXT NOT NULL DEFAULT 'unknown',
  identity_confidence REAL,
  consent_status TEXT NOT NULL DEFAULT 'unknown',
  source TEXT,
  first_seen_at TEXT,
  last_seen_at TEXT,
  style_profile TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY,
  contact_id INTEGER,
  channel TEXT NOT NULL,
  account_id INTEGER,
  external_chat_id TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  first_message_at TEXT,
  last_message_at TEXT,
  summary TEXT,
  next_action TEXT,
  FOREIGN KEY(contact_id) REFERENCES contacts(id),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL,
  direction TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  message TEXT NOT NULL,
  source TEXT,
  importance INTEGER DEFAULT 0,
  embedding_ref TEXT,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS opportunities (
  id INTEGER PRIMARY KEY,
  source_id TEXT,
  external_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  client_name TEXT,
  budget REAL,
  currency TEXT,
  deadline TEXT,
  estimated_hours REAL,
  estimated_cost REAL,
  estimated_profit REAL,
  profit_per_hour REAL,
  execution_confidence REAL,
  recurrence_probability REAL,
  risk REAL,
  score REAL,
  status TEXT NOT NULL DEFAULT 'discovered',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY,
  opportunity_id INTEGER NOT NULL,
  account_id INTEGER,
  message TEXT,
  submitted_at TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  reply_at TEXT,
  result TEXT,
  FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  opportunity_id INTEGER,
  client_id INTEGER,
  agreed_value REAL,
  currency TEXT,
  deadline TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  estimated_hours REAL,
  actual_hours REAL,
  deliverable_path TEXT,
  revenue REAL DEFAULT 0,
  cost REAL DEFAULT 0,
  profit REAL DEFAULT 0,
  FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
  FOREIGN KEY(client_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS session_runs (
  id INTEGER PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  primary_goal TEXT NOT NULL,
  minimum_real_outcome TEXT,
  result_level TEXT,
  actions_count INTEGER DEFAULT 0,
  economic_result REAL DEFAULT 0,
  operational_leap INTEGER DEFAULT 0,
  blocked INTEGER DEFAULT 0,
  next_action TEXT
);

CREATE TABLE IF NOT EXISTS human_interventions (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  platform TEXT,
  account_id INTEGER,
  blocker TEXT NOT NULL,
  reason TEXT,
  requested_action TEXT NOT NULL,
  priority INTEGER DEFAULT 2,
  status TEXT NOT NULL DEFAULT 'queued',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS learning_events (
  id INTEGER PRIMARY KEY,
  category TEXT NOT NULL,
  observation TEXT NOT NULL,
  evidence_count INTEGER DEFAULT 1,
  confidence REAL,
  effect TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS historical_evidence (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  event_date TEXT,
  event TEXT NOT NULL,
  result TEXT,
  lesson TEXT,
  confidence REAL,
  superseded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY,
  timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  agent TEXT NOT NULL,
  account_id INTEGER,
  platform TEXT,
  action TEXT NOT NULL,
  target TEXT,
  reason TEXT,
  result TEXT,
  cost REAL DEFAULT 0,
  reversible INTEGER DEFAULT 1,
  evidence_ref TEXT,
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

-- Autonomous operation layer (same project version 2.0)

CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY,
  parent_goal_id INTEGER,
  title TEXT NOT NULL,
  description TEXT,
  context_type TEXT,
  context_id TEXT,
  priority INTEGER DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'active',
  success_condition TEXT,
  minimum_real_outcome TEXT,
  deadline TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  FOREIGN KEY(parent_goal_id) REFERENCES goals(id)
);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY,
  goal_id INTEGER,
  title TEXT NOT NULL,
  description TEXT,
  context_type TEXT,
  context_id TEXT,
  priority INTEGER DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'queued',
  estimated_minutes REAL,
  estimated_value REAL,
  actual_minutes REAL,
  actual_value REAL,
  next_action TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  goal_id INTEGER,
  task_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  actor TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target TEXT,
  authorization_basis TEXT,
  risk_level TEXT DEFAULT 'low',
  reversible INTEGER DEFAULT 1,
  expected_impact REAL,
  status TEXT NOT NULL DEFAULT 'planned',
  started_at TEXT,
  completed_at TEXT,
  result TEXT,
  evidence_ref TEXT,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(goal_id) REFERENCES goals(id),
  FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  objective TEXT NOT NULL,
  options_considered TEXT,
  chosen_option TEXT NOT NULL,
  reason_summary TEXT,
  confidence REAL,
  expected_impact REAL,
  risk_level TEXT,
  authorization_basis TEXT,
  evidence_refs TEXT,
  actual_result TEXT,
  actual_impact REAL,
  impact_verified_at TEXT,
  lesson TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(session_id) REFERENCES session_runs(id)
);

CREATE TABLE IF NOT EXISTS work_diary (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  goal_id INTEGER,
  task_id INTEGER,
  action_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  step TEXT NOT NULL,
  reason TEXT,
  result TEXT,
  evidence_ref TEXT,
  next_step TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(goal_id) REFERENCES goals(id),
  FOREIGN KEY(task_id) REFERENCES tasks(id),
  FOREIGN KEY(action_id) REFERENCES actions(id)
);

CREATE TABLE IF NOT EXISTS facts (
  id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  scope TEXT DEFAULT 'general',
  fact TEXT NOT NULL,
  source TEXT,
  confidence REAL,
  first_seen_at TEXT,
  last_confirmed_at TEXT,
  superseded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY,
  evidence_type TEXT NOT NULL,
  source TEXT NOT NULL,
  external_id TEXT,
  entity_type TEXT,
  entity_id TEXT,
  content_ref TEXT,
  observed_at TEXT,
  confidence REAL,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS relationship_edges (
  id INTEGER PRIMARY KEY,
  person_a_id INTEGER NOT NULL,
  person_b_id INTEGER NOT NULL,
  relationship_type TEXT NOT NULL,
  strength REAL,
  confidence REAL,
  context_scope TEXT,
  first_seen_at TEXT,
  last_seen_at TEXT,
  evidence_ref TEXT,
  notes TEXT,
  UNIQUE(person_a_id, person_b_id, relationship_type, context_scope),
  FOREIGN KEY(person_a_id) REFERENCES contacts(id),
  FOREIGN KEY(person_b_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS conversation_states (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL UNIQUE,
  relationship_context TEXT,
  intent TEXT,
  urgency TEXT DEFAULT 'normal',
  response_required TEXT DEFAULT 'UNKNOWN',
  commercial_value REAL DEFAULT 0,
  social_value REAL DEFAULT 0,
  risk REAL DEFAULT 0,
  identity_confidence REAL,
  last_meaningful_event TEXT,
  pending_question TEXT,
  pending_commitment TEXT,
  recommended_next_action TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS social_actions (
  id INTEGER PRIMARY KEY,
  account_id INTEGER,
  contact_id INTEGER,
  platform TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target_ref TEXT,
  context_type TEXT DEFAULT 'social',
  reason TEXT,
  risk_level TEXT DEFAULT 'low',
  status TEXT NOT NULL DEFAULT 'planned',
  result TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(account_id) REFERENCES accounts(id),
  FOREIGN KEY(contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS tools_registry (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  purpose TEXT NOT NULL,
  tool_type TEXT,
  inputs TEXT,
  outputs TEXT,
  path TEXT,
  version TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  success_rate REAL,
  avg_time_saved_minutes REAL,
  known_failures TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at TEXT
);

CREATE TABLE IF NOT EXISTS tool_runs (
  id INTEGER PRIMARY KEY,
  tool_id INTEGER NOT NULL,
  session_id INTEGER,
  task_id INTEGER,
  input_ref TEXT,
  output_ref TEXT,
  duration_seconds REAL,
  status TEXT NOT NULL,
  result TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(tool_id) REFERENCES tools_registry(id),
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS account_observations (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL,
  observation_type TEXT NOT NULL,
  value TEXT,
  evidence_ref TEXT,
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS session_checkpoints (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  current_goal_id INTEGER,
  current_task_id INTEGER,
  current_context_type TEXT,
  current_context_id TEXT,
  current_account_id INTEGER,
  last_action_id INTEGER,
  last_result TEXT,
  next_action TEXT,
  pending_blocker_count INTEGER DEFAULT 0,
  snapshot_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(current_goal_id) REFERENCES goals(id),
  FOREIGN KEY(current_task_id) REFERENCES tasks(id),
  FOREIGN KEY(current_account_id) REFERENCES accounts(id),
  FOREIGN KEY(last_action_id) REFERENCES actions(id)
);

CREATE TABLE IF NOT EXISTS strategies (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  problem TEXT,
  approach TEXT,
  status TEXT NOT NULL DEFAULT 'experimental',
  attempt_count INTEGER DEFAULT 0,
  success_count INTEGER DEFAULT 0,
  failure_count INTEGER DEFAULT 0,
  avg_time_minutes REAL,
  avg_gain REAL,
  risk REAL,
  last_result TEXT,
  last_used_at TEXT
);

CREATE TABLE IF NOT EXISTS strategy_runs (
  id INTEGER PRIMARY KEY,
  strategy_id INTEGER NOT NULL,
  session_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  changed_variables TEXT,
  expected_result TEXT,
  actual_result TEXT,
  outcome TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(strategy_id) REFERENCES strategies(id),
  FOREIGN KEY(session_id) REFERENCES session_runs(id)
);

CREATE TABLE IF NOT EXISTS human_intervention_batches (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  priority INTEGER DEFAULT 2,
  summary TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,
  FOREIGN KEY(session_id) REFERENCES session_runs(id)
);

CREATE TABLE IF NOT EXISTS financial_events (
  id INTEGER PRIMARY KEY,
  job_id INTEGER,
  account_id INTEGER,
  event_type TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT NOT NULL DEFAULT 'BRL',
  category TEXT,
  reference TEXT,
  status TEXT,
  occurred_at TEXT,
  notes TEXT,
  FOREIGN KEY(job_id) REFERENCES jobs(id),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS state_snapshots (
  id INTEGER PRIMARY KEY,
  scope TEXT NOT NULL,
  scope_id TEXT,
  snapshot_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retrieval_events (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  query TEXT NOT NULL,
  result_refs TEXT,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(session_id) REFERENCES session_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_contact ON conversations(contact_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority_status ON tasks(status, priority);
CREATE INDEX IF NOT EXISTS idx_actions_context ON actions(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_context ON decisions(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_facts_entity ON facts(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_work_diary_session ON work_diary(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_interventions_status ON human_interventions(status, priority);
CREATE INDEX IF NOT EXISTS idx_account_observations_account ON account_observations(account_id, observed_at);


-- Adaptive execution layer (same project version 2.0)
CREATE TABLE IF NOT EXISTS opportunity_routes (
  id INTEGER PRIMARY KEY,
  opportunity_id INTEGER NOT NULL,
  route_type TEXT NOT NULL,
  rationale TEXT,
  expected_value REAL,
  estimated_minutes REAL,
  estimated_cost REAL,
  risk REAL,
  status TEXT NOT NULL DEFAULT 'candidate',
  selected INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS execution_plans (
  id INTEGER PRIMARY KEY,
  opportunity_id INTEGER,
  job_id INTEGER,
  objective TEXT NOT NULL,
  accepted_scope TEXT,
  acceptance_criteria TEXT,
  required_accounts TEXT,
  required_apps TEXT,
  required_tools TEXT,
  environment_dependencies TEXT,
  existing_assets TEXT,
  simplest_valid_route TEXT,
  build_required INTEGER DEFAULT 0,
  build_reason TEXT,
  estimated_minutes REAL,
  estimated_tokens REAL,
  estimated_cost REAL,
  test_strategy TEXT,
  fallback_strategy TEXT,
  rollback_strategy TEXT,
  communication_requirements TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  next_action TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
  FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS environment_discoveries (
  id INTEGER PRIMARY KEY,
  execution_plan_id INTEGER NOT NULL,
  target_system TEXT NOT NULL,
  finding_type TEXT NOT NULL,
  target_ref TEXT,
  account_state TEXT,
  logged_in INTEGER,
  usable INTEGER,
  permissions_state TEXT,
  finding TEXT,
  evidence_ref TEXT,
  next_action TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(execution_plan_id) REFERENCES execution_plans(id)
);

CREATE TABLE IF NOT EXISTS capability_evidence (
  id INTEGER PRIMARY KEY,
  capability TEXT NOT NULL,
  confidence REAL,
  proof_level TEXT,
  tool_support TEXT,
  speed_score REAL,
  quality_score REAL,
  cost_score REAL,
  reuse_value REAL,
  learning_cost REAL,
  evidence_ref TEXT,
  last_success_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS context_locks (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  job_id INTEGER,
  account_id INTEGER,
  contact_id INTEGER,
  conversation_id INTEGER,
  platform TEXT,
  context_type TEXT NOT NULL,
  context_id TEXT NOT NULL,
  lock_reason TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  released_at TEXT,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(job_id) REFERENCES jobs(id),
  FOREIGN KEY(account_id) REFERENCES accounts(id),
  FOREIGN KEY(contact_id) REFERENCES contacts(id),
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS action_expectations (
  id INTEGER PRIMARY KEY,
  action_id INTEGER NOT NULL,
  expected_result TEXT NOT NULL,
  validation_method TEXT,
  actual_result TEXT,
  outcome TEXT,
  impact REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  verified_at TEXT,
  FOREIGN KEY(action_id) REFERENCES actions(id)
);

CREATE INDEX IF NOT EXISTS idx_opportunity_routes_opportunity ON opportunity_routes(opportunity_id, selected);
CREATE INDEX IF NOT EXISTS idx_execution_plans_job ON execution_plans(job_id, status);
CREATE INDEX IF NOT EXISTS idx_environment_discoveries_plan ON environment_discoveries(execution_plan_id, created_at);
CREATE INDEX IF NOT EXISTS idx_context_locks_active ON context_locks(active, context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_action_expectations_action ON action_expectations(action_id);

-- Generalized problem-solving and consequence-tracing layer (same project version 2.0)
-- These tables describe relationships and expected destinations without hard-coding one platform.
CREATE TABLE IF NOT EXISTS system_relations (
  id INTEGER PRIMARY KEY,
  source_system TEXT NOT NULL,
  target_system TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  signal_type TEXT,
  confidence REAL,
  evidence_ref TEXT,
  status TEXT NOT NULL DEFAULT 'observed',
  last_verified_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_system, target_system, relation_type)
);

CREATE TABLE IF NOT EXISTS event_destinations (
  id INTEGER PRIMARY KEY,
  event_type TEXT NOT NULL,
  origin_system TEXT,
  destination_system TEXT NOT NULL,
  destination_signal TEXT,
  expected_latency TEXT,
  detection_method TEXT,
  probability REAL,
  priority INTEGER DEFAULT 2,
  enabled INTEGER NOT NULL DEFAULT 1,
  source_evidence TEXT,
  last_verified_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS solver_probes (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  goal_id INTEGER,
  task_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  question TEXT NOT NULL,
  systems_considered TEXT,
  probes_attempted TEXT,
  chosen_probe TEXT,
  result TEXT,
  uncertainty_before REAL,
  uncertainty_after REAL,
  impact REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(goal_id) REFERENCES goals(id),
  FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS outcome_checks (
  id INTEGER PRIMARY KEY,
  action_id INTEGER,
  expectation_id INTEGER,
  event_type TEXT,
  expected_destination TEXT,
  checked_systems TEXT,
  observation TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  evidence_ref TEXT,
  checked_at TEXT,
  next_action TEXT,
  FOREIGN KEY(action_id) REFERENCES actions(id),
  FOREIGN KEY(expectation_id) REFERENCES action_expectations(id)
);

CREATE TABLE IF NOT EXISTS capability_market_matches (
  id INTEGER PRIMARY KEY,
  opportunity_id INTEGER,
  capability TEXT NOT NULL,
  fit_score REAL,
  economic_score REAL,
  route_score REAL,
  reuse_score REAL,
  friction_score REAL,
  total_score REAL,
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
);

CREATE INDEX IF NOT EXISTS idx_system_relations_source ON system_relations(source_system, status);
CREATE INDEX IF NOT EXISTS idx_system_relations_target ON system_relations(target_system, status);
CREATE INDEX IF NOT EXISTS idx_event_destinations_event ON event_destinations(event_type, enabled, priority);
CREATE INDEX IF NOT EXISTS idx_solver_probes_context ON solver_probes(context_type, context_id, created_at);
CREATE INDEX IF NOT EXISTS idx_outcome_checks_action ON outcome_checks(action_id, status);

CREATE TABLE IF NOT EXISTS worker_profile (
  id INTEGER PRIMARY KEY,
  role_identity TEXT NOT NULL DEFAULT 'autonomous_digital_worker',
  status TEXT NOT NULL DEFAULT 'discovering',
  summary TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS capability_tests (
  id INTEGER PRIMARY KEY,
  capability TEXT NOT NULL,
  objective TEXT NOT NULL,
  toolchain TEXT,
  input_ref TEXT,
  output_ref TEXT,
  quality_score REAL,
  time_seconds REAL,
  estimated_cost REAL,
  rework_required INTEGER DEFAULT 0,
  result TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_capability_tests_status ON capability_tests(status, created_at);
CREATE INDEX IF NOT EXISTS idx_capability_evidence_capability ON capability_evidence(capability, proof_level, confidence DESC);

CREATE INDEX IF NOT EXISTS idx_capability_market_match ON capability_market_matches(opportunity_id, total_score DESC);



-- Communication state layer (behavioral reinforcement, same project version 2.0)
CREATE TABLE IF NOT EXISTS conversation_plans (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL UNIQUE,
  stage TEXT NOT NULL DEFAULT 'OPEN',
  conversation_goal TEXT,
  customer_problem_or_goal TEXT,
  known_facts TEXT,
  unknown_that_matters TEXT,
  value_hypothesis TEXT,
  desired_next_customer_state TEXT,
  next_action TEXT,
  objection_focus TEXT,
  follow_up_state TEXT,
  stop_condition TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS conversation_followups (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL,
  reason TEXT NOT NULL,
  value_added TEXT,
  due_at TEXT,
  attempt_number INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'queued',
  completed_at TEXT,
  result TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS session_wait_states (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  state TEXT NOT NULL DEFAULT 'WAITING_FOR_EVENT',
  next_wake_at TEXT,
  pending_outcomes TEXT,
  pending_followups TEXT,
  pending_blockers TEXT,
  next_action TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resumed_at TEXT,
  FOREIGN KEY(session_id) REFERENCES session_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_conversation_plans_stage ON conversation_plans(stage, updated_at);
CREATE INDEX IF NOT EXISTS idx_conversation_followups_due ON conversation_followups(status, due_at);
CREATE INDEX IF NOT EXISTS idx_session_wait_states_wake ON session_wait_states(state, next_wake_at);

-- Behavioral autonomy 2.1: media, customer lifecycle, scoring, payments, feedback
CREATE TABLE IF NOT EXISTS platform_capabilities (
  id INTEGER PRIMARY KEY,
  platform TEXT NOT NULL,
  account_id INTEGER,
  capability TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unknown',
  evidence_ref TEXT,
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT,
  notes TEXT,
  UNIQUE(platform, account_id, capability),
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS media_items (
  id INTEGER PRIMARY KEY,
  message_id INTEGER NOT NULL,
  media_type TEXT NOT NULL,
  view_once INTEGER NOT NULL DEFAULT 0,
  external_ref TEXT,
  mime_type TEXT,
  size_bytes INTEGER,
  access_status TEXT NOT NULL DEFAULT 'unknown',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(message_id) REFERENCES messages(id)
);

CREATE TABLE IF NOT EXISTS media_observations (
  id INTEGER PRIMARY KEY,
  media_id INTEGER NOT NULL,
  operation TEXT NOT NULL,
  status TEXT NOT NULL,
  result_ref TEXT,
  error_class TEXT,
  capability_evidence_ref TEXT,
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(media_id) REFERENCES media_items(id)
);

CREATE TABLE IF NOT EXISTS customer_scores (
  id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  score_type TEXT NOT NULL DEFAULT 'commercial_priority',
  score REAL NOT NULL,
  confidence REAL,
  priority_band TEXT,
  factors_json TEXT,
  reasons_json TEXT,
  next_action TEXT,
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(entity_type, entity_id, score_type)
);

CREATE TABLE IF NOT EXISTS customer_lifecycle (
  id INTEGER PRIMARY KEY,
  contact_id INTEGER,
  organization_ref TEXT,
  stage TEXT NOT NULL DEFAULT 'unknown',
  trial_status TEXT,
  payment_state TEXT,
  satisfaction_state TEXT,
  repeat_potential REAL,
  last_material_event TEXT,
  last_material_event_at TEXT,
  next_best_action TEXT,
  confidence REAL,
  evidence_ref TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS trials (
  id INTEGER PRIMARY KEY,
  contact_id INTEGER,
  conversation_id INTEGER,
  opportunity_id INTEGER,
  trial_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unknown',
  requested_at TEXT,
  started_at TEXT,
  completed_at TEXT,
  result TEXT,
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(contact_id) REFERENCES contacts(id),
  FOREIGN KEY(conversation_id) REFERENCES conversations(id),
  FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS payment_destinations (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL,
  account_id INTEGER,
  method_type TEXT NOT NULL,
  identifier_ref TEXT,
  masked_identifier TEXT,
  verification_status TEXT NOT NULL DEFAULT 'unverified',
  capability_level TEXT NOT NULL DEFAULT 'NONE',
  last_verified_at TEXT,
  verification_evidence_ref TEXT,
  notes TEXT,
  FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS payment_checks (
  id INTEGER PRIMARY KEY,
  job_id INTEGER,
  conversation_id INTEGER,
  payment_destination_id INTEGER,
  expected_amount REAL,
  currency TEXT NOT NULL DEFAULT 'BRL',
  status TEXT NOT NULL DEFAULT 'pending',
  provider_reference TEXT,
  checked_at TEXT,
  evidence_ref TEXT,
  next_action TEXT,
  FOREIGN KEY(job_id) REFERENCES jobs(id),
  FOREIGN KEY(conversation_id) REFERENCES conversations(id),
  FOREIGN KEY(payment_destination_id) REFERENCES payment_destinations(id)
);

CREATE TABLE IF NOT EXISTS feedback_requests (
  id INTEGER PRIMARY KEY,
  job_id INTEGER,
  contact_id INTEGER,
  conversation_id INTEGER,
  trigger TEXT NOT NULL,
  satisfaction_confirmed INTEGER NOT NULL DEFAULT 0,
  request_message TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  response TEXT,
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  responded_at TEXT,
  FOREIGN KEY(job_id) REFERENCES jobs(id),
  FOREIGN KEY(contact_id) REFERENCES contacts(id),
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_platform_capabilities_platform ON platform_capabilities(platform, capability, status);
CREATE INDEX IF NOT EXISTS idx_media_items_message ON media_items(message_id, access_status);
CREATE INDEX IF NOT EXISTS idx_media_observations_media ON media_observations(media_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_customer_scores_priority ON customer_scores(score DESC, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_customer_lifecycle_stage ON customer_lifecycle(stage, updated_at);
CREATE INDEX IF NOT EXISTS idx_trials_contact_status ON trials(contact_id, status, completed_at);
CREATE INDEX IF NOT EXISTS idx_payment_destinations_status ON payment_destinations(verification_status, capability_level);
CREATE INDEX IF NOT EXISTS idx_payment_checks_status ON payment_checks(status, checked_at);
CREATE INDEX IF NOT EXISTS idx_feedback_requests_status ON feedback_requests(status, created_at);



-- Behavioral autonomy 2.2: mandate-scoped authorization, generalized error recovery, durable agenda/reminders
CREATE TABLE IF NOT EXISTS authorization_grants (
  id INTEGER PRIMARY KEY,
  scope_type TEXT NOT NULL,
  scope_key TEXT NOT NULL,
  capability TEXT NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  risk_ceiling TEXT NOT NULL DEFAULT 'low',
  parameters_json TEXT,
  evidence_ref TEXT,
  granted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT,
  revoked_at TEXT,
  UNIQUE(scope_type, scope_key, capability)
);

CREATE TABLE IF NOT EXISTS authorization_checks (
  id INTEGER PRIMARY KEY,
  action_id INTEGER,
  session_id INTEGER,
  capability TEXT NOT NULL,
  scope_type TEXT,
  scope_key TEXT,
  decision TEXT NOT NULL,
  authorization_basis TEXT,
  risk_level TEXT,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(action_id) REFERENCES actions(id),
  FOREIGN KEY(session_id) REFERENCES session_runs(id)
);

CREATE TABLE IF NOT EXISTS error_events (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  action_id INTEGER,
  tool_id INTEGER,
  provider TEXT,
  operation TEXT NOT NULL,
  error_class TEXT NOT NULL,
  error_code TEXT,
  message TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0,
  recovery_strategy TEXT,
  recovery_result TEXT,
  evidence_ref TEXT,
  idempotency_key TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(action_id) REFERENCES actions(id),
  FOREIGN KEY(tool_id) REFERENCES tools_registry(id)
);

CREATE TABLE IF NOT EXISTS retry_circuit_state (
  provider TEXT NOT NULL,
  operation TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'closed',
  failure_count INTEGER NOT NULL DEFAULT 0,
  opened_at TEXT,
  cooldown_until TEXT,
  last_error_class TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(provider, operation)
);

CREATE TABLE IF NOT EXISTS idempotency_records (
  id INTEGER PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  action_fingerprint TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'in_flight',
  result_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS calendars (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL,
  account_id INTEGER,
  external_calendar_id TEXT,
  name TEXT,
  timezone TEXT,
  access_mode TEXT NOT NULL DEFAULT 'read',
  status TEXT NOT NULL DEFAULT 'unknown',
  evidence_ref TEXT,
  last_synced_at TEXT,
  FOREIGN KEY(account_id) REFERENCES accounts(id),
  UNIQUE(provider, account_id, external_calendar_id)
);

CREATE TABLE IF NOT EXISTS calendar_events (
  id INTEGER PRIMARY KEY,
  calendar_id INTEGER,
  external_event_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  start_at TEXT NOT NULL,
  end_at TEXT,
  timezone TEXT,
  status TEXT NOT NULL DEFAULT 'scheduled',
  source TEXT NOT NULL DEFAULT 'local',
  context_type TEXT,
  context_id TEXT,
  recurrence_rule TEXT,
  sync_state TEXT NOT NULL DEFAULT 'local_only',
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(calendar_id) REFERENCES calendars(id),
  UNIQUE(calendar_id, external_event_id)
);

CREATE TABLE IF NOT EXISTS reminders (
  id INTEGER PRIMARY KEY,
  event_id INTEGER,
  context_type TEXT,
  context_id TEXT,
  title TEXT NOT NULL,
  message TEXT,
  due_at TEXT NOT NULL,
  delivery TEXT NOT NULL DEFAULT 'runtime_wake',
  status TEXT NOT NULL DEFAULT 'scheduled',
  priority INTEGER NOT NULL DEFAULT 3,
  repeat_rule TEXT,
  last_fired_at TEXT,
  next_fire_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(event_id) REFERENCES calendar_events(id)
);

CREATE TABLE IF NOT EXISTS wake_queue (
  id INTEGER PRIMARY KEY,
  wake_type TEXT NOT NULL,
  due_at TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 3,
  context_type TEXT,
  context_id TEXT,
  source_ref TEXT,
  status TEXT NOT NULL DEFAULT 'queued',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  claimed_at TEXT,
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_authorization_grants_active ON authorization_grants(status, capability, expires_at);
CREATE INDEX IF NOT EXISTS idx_authorization_checks_action ON authorization_checks(action_id, created_at);
CREATE INDEX IF NOT EXISTS idx_error_events_provider_operation ON error_events(provider, operation, created_at);
CREATE INDEX IF NOT EXISTS idx_error_events_unresolved ON error_events(resolved_at, created_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_time ON calendar_events(start_at, status);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, next_fire_at, due_at);
CREATE INDEX IF NOT EXISTS idx_wake_queue_due ON wake_queue(status, due_at, priority);


-- Behavioral autonomy 2.3: durable action commitments and progress supervision
CREATE TABLE IF NOT EXISTS execution_commitments (
  id INTEGER PRIMARY KEY,
  session_id INTEGER,
  goal_id INTEGER,
  task_id INTEGER,
  action_id INTEGER,
  action_key TEXT NOT NULL UNIQUE,
  action_type TEXT NOT NULL,
  scope TEXT,
  target TEXT,
  expected_result TEXT,
  status TEXT NOT NULL DEFAULT 'READY',
  authorization_basis TEXT,
  capability_snapshot TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  confirmation_requests INTEGER NOT NULL DEFAULT 0,
  no_progress_cycles INTEGER NOT NULL DEFAULT 0,
  blocker_class TEXT,
  next_action TEXT,
  evidence_ref TEXT,
  last_progress_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(session_id) REFERENCES session_runs(id),
  FOREIGN KEY(goal_id) REFERENCES goals(id),
  FOREIGN KEY(task_id) REFERENCES tasks(id),
  FOREIGN KEY(action_id) REFERENCES actions(id)
);

CREATE INDEX IF NOT EXISTS idx_execution_commitments_status ON execution_commitments(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_execution_commitments_progress ON execution_commitments(no_progress_cycles, updated_at);

-- Autonomia 2.5: worker-owned missions, behavioral communication memory, runtime supervision
CREATE TABLE IF NOT EXISTS missions (
  id INTEGER PRIMARY KEY,
  goal_id INTEGER,
  title TEXT NOT NULL,
  objective TEXT NOT NULL,
  economic_value REAL NOT NULL DEFAULT 0,
  probability_of_success REAL NOT NULL DEFAULT 0.5,
  strategic_value REAL NOT NULL DEFAULT 0.5,
  recurrence_potential REAL NOT NULL DEFAULT 0,
  expected_minutes REAL NOT NULL DEFAULT 30,
  expected_cost REAL NOT NULL DEFAULT 0,
  risk REAL NOT NULL DEFAULT 0,
  uncertainty REAL NOT NULL DEFAULT 0,
  context_switch_cost REAL NOT NULL DEFAULT 0,
  human_dependency REAL NOT NULL DEFAULT 0,
  deadline_at TEXT,
  success_condition TEXT,
  owner_dependency TEXT,
  current_state TEXT NOT NULL DEFAULT 'candidate',
  next_action TEXT,
  priority REAL NOT NULL DEFAULT 0,
  metadata_json TEXT,
  status TEXT NOT NULL DEFAULT 'candidate',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE TABLE IF NOT EXISTS runtime_journal (
  id INTEGER PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runtime_receipts (
  id INTEGER PRIMARY KEY,
  mission_fingerprint TEXT,
  action_type TEXT NOT NULL,
  status TEXT NOT NULL,
  result_json TEXT,
  evidence_ref TEXT,
  blocker TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS browser_workspaces (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  profile_dir TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ready',
  last_reconciled_at TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS runtime_leases (
  id INTEGER PRIMARY KEY,
  worker_id TEXT NOT NULL UNIQUE,
  acquired_at TEXT NOT NULL,
  heartbeat_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_missions_priority ON missions(status, priority DESC, updated_at);
CREATE INDEX IF NOT EXISTS idx_runtime_journal_created ON runtime_journal(created_at);
CREATE INDEX IF NOT EXISTS idx_runtime_receipts_mission ON runtime_receipts(mission_fingerprint, created_at);
CREATE INDEX IF NOT EXISTS idx_runtime_leases_status ON runtime_leases(status, heartbeat_at);
