// ── Score breakdown returned by the GEO audit engine ─────────────────────────
export interface ScoreBreakdown {
  ai_citability: number
  brand_authority: number
  content_eeat: number
  technical: number
  schema: number
  platform_optimization: number
}

// ── A single finding inside an audit ─────────────────────────────────────────
export interface Finding {
  severity: 'critical' | 'high' | 'medium'
  title: string
  description: string
}

// ── Full audit data shape (stored as rawData JSON in the Audit model) ─────────
export interface AuditData {
  url: string
  brand_name: string
  date: string
  geo_score: number
  scores: ScoreBreakdown
  platforms: {
    'Google AI Overviews': number
    ChatGPT: number
    Perplexity: number
    'Bing Copilot': number
  }
  executive_summary: string
  findings: Finding[]
  quick_wins: string[]
  medium_term: string[]
  strategic: string[]
  crawler_access: Record<string, string>
}

// ── Client with computed stats for the admin overview table ──────────────────
export interface ClientWithStats {
  id: string
  name: string
  websiteUrl: string
  createdAt: Date
  latestScore: number | null
  previousScore: number | null
  scoreDelta: number | null
  lastAuditAt: Date | null
  auditCount: number
}

// ── Recommendation shape (mirrors Prisma model) ───────────────────────────────
export interface RecommendationRecord {
  id: string
  auditId: string
  clientId: string
  category: string
  priority: number
  title: string
  description: string
  effort: 'low' | 'medium' | 'high'
  impact: 'low' | 'medium' | 'high'
  status: 'pending' | 'in_progress' | 'done'
}

// ── Alert shape (mirrors Prisma model) ───────────────────────────────────────
export interface AlertRecord {
  id: string
  clientId: string
  type: 'score_drop' | 'overdue_audit' | 'milestone'
  message: string
  isRead: boolean
  createdAt: Date
}

// ── Audit record with parsed JSON fields ──────────────────────────────────────
export interface AuditRecord {
  id: string
  clientId: string
  timestamp: Date
  isBaseline: boolean
  geoScore: number
  scores: ScoreBreakdown
  rawData: AuditData
  competitors: CompetitorSnapshot[] | null
  recommendations: RecommendationRecord[]
}

// ── Competitor snapshot stored inside Audit.competitors JSON ─────────────────
export interface CompetitorSnapshot {
  url: string
  name: string
  geoScore: number
  scores: Partial<ScoreBreakdown>
  capturedAt: string
}

// ── API response wrappers ─────────────────────────────────────────────────────
export interface ApiSuccessResponse<T> {
  data: T
  ok: true
}

export interface ApiErrorResponse {
  error: string
  ok: false
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse
