import { DocumentRecord, DetailedAnalysis } from '../types';

export const KPI_METRICS = {
  scanned: { value: '12,842', change: '+18.4%', isPositive: true },
  verified: { value: '11,124', change: '+14.2%', isPositive: true },
  suspicious: { value: '1,592', change: '+4.1%', isPositive: false },
  highRisk: { value: '126', change: '+8.2%', isPositive: false },
  avgRiskScore: { value: '28.4', change: '-2.1%', isPositive: true },
  accuracy: { value: '99.42%', change: '+0.12%', isPositive: true },
  processingTime: { value: '1.42s', change: '-180ms', isPositive: true },
};

export const RECENT_DOCUMENTS: DocumentRecord[] = [
  {
    id: 'DOC-2026-008421',
    docType: 'Aadhaar',
    subjectMaskedId: '[Aadhaar Redacted]',
    riskScore: 78,
    ocrConfidence: 93,
    tamperingDetected: true,
    qrStatus: 'FAILED',
    status: 'SUSPICIOUS',
    timestamp: '04 Sep 2026, 14:32',
    processedByNode: 'IN-WEST-AI-01'
  },
  {
    id: 'DOC-2026-008420',
    docType: 'PAN Card',
    subjectMaskedId: 'ABCDE****F',
    riskScore: 12,
    ocrConfidence: 99,
    tamperingDetected: false,
    qrStatus: 'VERIFIED',
    status: 'VERIFIED',
    timestamp: '04 Sep 2026, 14:28',
    processedByNode: 'IN-WEST-AI-02'
  },
  {
    id: 'DOC-2026-008419',
    docType: 'Passport',
    subjectMaskedId: 'P892****9',
    riskScore: 89,
    ocrConfidence: 71,
    tamperingDetected: true,
    qrStatus: 'MISMATCH',
    status: 'HIGH RISK',
    timestamp: '04 Sep 2026, 14:15',
    processedByNode: 'IN-NORTH-AI-01'
  },
  {
    id: 'DOC-2026-008418',
    docType: 'Driving License',
    subjectMaskedId: 'DL-04****892',
    riskScore: 94,
    ocrConfidence: 62,
    tamperingDetected: true,
    qrStatus: 'FAILED',
    status: 'CRITICAL',
    timestamp: '04 Sep 2026, 14:02',
    processedByNode: 'IN-SOUTH-AI-01'
  },
  {
    id: 'DOC-2026-008417',
    docType: 'Voter ID',
    subjectMaskedId: 'WZK****321',
    riskScore: 19,
    ocrConfidence: 96,
    tamperingDetected: false,
    qrStatus: 'VERIFIED',
    status: 'VERIFIED',
    timestamp: '04 Sep 2026, 13:50',
    processedByNode: 'IN-WEST-AI-01'
  }
];

export const CURRENT_INSPECTION: DetailedAnalysis = {
  id: 'DOC-2026-008421',
  docType: 'Aadhaar',
  subjectMaskedId: '[Aadhaar Redacted]',
  riskScore: 78,
  ocrConfidence: 93,
  tamperingDetected: true,
  qrStatus: 'FAILED',
  status: 'SUSPICIOUS',
  timestamp: '04 Sep 2026, 14:32:09 IST',
  processedByNode: 'IDSHIELD-INFERENCE-CLUSTER-04',
  layoutIntegrity: 81,
  imageIntegrity: 64,
  faceConsistency: 89,
  faceDetected: true,
  faceQuality: 91,
  qrDecodedData: 'RAW:ID_TOKEN_CORRUPTED_HEX_E29',
  qrExpectedData: 'ENCRYPTED_UIDAI_V3_SIGNATURE',
  aiExplanation: [
    'Cryptographic signature check failed on embedded Quick Response matrix.',
    'Local font weight mismatch detected within Father/Husband relationship field.',
    'Error Level Analysis (ELA) exhibits pixel frequency variance indicative of JPEG re-compression near DOB string.',
    'Microprint perimeter borders display structural displacement beyond 1.8mm threshold tolerance.'
  ],
  riskBreakdown: [
    { signal: 'Tampering / Pixel Splice', weight: 24, impact: 'negative', description: 'ELA anomaly in DOB field' },
    { signal: 'QR Signature Verification', weight: 20, impact: 'negative', description: 'Asymmetric key signature mismatch' },
    { signal: 'Image Integrity Score', weight: 18, impact: 'negative', description: 'Compression artifacts < 70% threshold' },
    { signal: 'Layout Displacement', weight: 15, impact: 'negative', description: 'Security border offset +2.1mm' },
    { signal: 'OCR Confidence Drop', weight: 5, impact: 'negative', description: 'Slight character blurring on header' },
    { signal: 'Biometric Face Geometry', weight: -4, impact: 'positive', description: 'Standard facial ratio aligns with schema' }
  ],
  evidenceRegions: [
    {
      id: 'EV-01',
      label: 'Altered Date Field',
      confidence: 91,
      x: 38,
      y: 45,
      width: 28,
      height: 9,
      type: 'pixel_splice',
      explanation: 'Discrete cosine transform (DCT) coefficient anomalies indicate post-render text insertion.'
    },
    {
      id: 'EV-02',
      label: 'Photograph Boundary Inconsistency',
      confidence: 84,
      x: 6,
      y: 35,
      width: 25,
      height: 42,
      type: 'layout_shift',
      explanation: 'Edge feathering detected without standard guilloche background continuation.'
    },
    {
      id: 'EV-03',
      label: 'Corrupted QR Matrix',
      confidence: 97,
      x: 72,
      y: 36,
      width: 22,
      height: 38,
      type: 'qr_forgery',
      explanation: 'Missing mandatory Reed-Solomon error correction parity bytes.'
    }
  ]
};
