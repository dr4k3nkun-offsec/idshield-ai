export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type VerificationStatus = 'VERIFIED' | 'SUSPICIOUS' | 'HIGH RISK' | 'CRITICAL';

export interface DocumentRecord {
  id: string;
  docType: 'Aadhaar' | 'PAN Card' | 'Passport' | 'Voter ID' | 'Driving Licence' | 'Driving License' | string;
  subjectMaskedId: string;
  riskScore: number;
  ocrConfidence: number;
  tamperingDetected: boolean;
  qrStatus: 'VERIFIED' | 'FAILED' | 'MISSING' | 'MISMATCH' | 'UNVERIFIED' | string;
  status: VerificationStatus;
  timestamp: string;
  processedByNode: string;
}

export interface RiskFactor {
  signal: string;
  weight: number;
  impact: 'positive' | 'negative';
  description: string;
}

export interface EvidenceRegion {
  id: string;
  label: string;
  confidence: number;
  x: number; // percentage
  y: number; // percentage
  width: number; // percentage
  height: number; // percentage
  type: 'font_anomaly' | 'qr_forgery' | 'pixel_splice' | 'layout_shift' | string;
  explanation: string;
}

export interface ValidationCheckItem {
  code: string;
  label: string;
  status: 'pass' | 'warn' | 'fail';
  message: string;
}

export interface ValidationOutcome {
  checks: ValidationCheckItem[];
  passed: number;
  warnings: number;
  failed: number;
  isValid: boolean;
  extractedFields?: {
    name?: string;
    dob?: string;
    gender?: string;
    expiry?: string;
  };
}

export interface EngineIntelligence {
  screened_count: number;
  stage: string;
  clusters_identified: number;
  intelligence_multiplier?: number;
}

export interface DetailedAnalysis extends DocumentRecord {
  processingTimeSeconds?: number;
  layoutIntegrity: number;
  imageIntegrity: number;
  faceConsistency: number;
  faceDetected: boolean;
  faceQuality: number;
  qrDecodedData: string | null;
  qrExpectedData: string | null;
  aiExplanation: string[];
  riskBreakdown: RiskFactor[];
  evidenceRegions: EvidenceRegion[];
  imageUrl?: string;
  engineIntelligence?: EngineIntelligence;
  validationOutcome?: ValidationOutcome;
}

export type PipelineStage = 
  | 'upload'
  | 'preprocessing'
  | 'ocr'
  | 'classification'
  | 'tampering'
  | 'layout'
  | 'qr'
  | 'biometric'
  | 'risk'
  | 'decision';

export interface StageStatus {
  id: PipelineStage;
  label: string;
  state: 'pending' | 'processing' | 'completed' | 'failed';
  details?: string;
}

export interface OfficerSession {
  badgeId: string;
  name: string;
  clearance: string;
}

export interface DashboardMetric {
  value: string;
  change: string;
  isPositive: boolean;
}

export interface DashboardStats {
  scanned: DashboardMetric;
  verified: DashboardMetric;
  suspicious: DashboardMetric;
  highRisk: DashboardMetric;
  avgRiskScore: DashboardMetric;
  accuracy: DashboardMetric;
  processingTime: DashboardMetric;
  recentDocuments: DetailedAnalysis[];
  learningMetrics?: EngineIntelligence;
}
