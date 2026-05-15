/**
 * DentalFlow Agent - Mock EHR (Electronic Health Records) API
 * Node.js/Express server simulating a dental practice management system
 * For UiPath AgentHack 2026 - Track 1: Maestro Case
 */

const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');

const app = express();
app.use(express.json());
app.use(cors());

// ─── In-Memory Data Store ─────────────────────────────────────────────────────
let appointments = [
  {
    id: 'appt-001',
    patientId: 'pat-101',
    patientName: 'Maria Rodriguez',
    patientEmail: 'maria@example.com',
    patientPhone: '+1-713-555-0101',
    providerId: 'prov-01',
    providerName: 'Dr. James Chen',
    type: 'Cleaning',
    scheduledAt: new Date(Date.now() + 86400000).toISOString(),
    status: 'confirmed',
    insuranceId: 'ins-BCBS-001',
    insuranceVerified: true,
    notes: ''
  },
  {
    id: 'appt-002',
    patientId: 'pat-102',
    patientName: 'John Smith',
    patientEmail: 'john.smith@example.com',
    patientPhone: '+1-713-555-0202',
    providerId: 'prov-02',
    providerName: 'Dr. Sarah Patel',
    type: 'Root Canal',
    scheduledAt: new Date(Date.now() + 172800000).toISOString(),
    status: 'pending',
    insuranceId: 'ins-AETNA-002',
    insuranceVerified: false,
    notes: 'Requires insurance pre-authorization'
  },
  {
    id: 'appt-003',
    patientId: 'pat-103',
    patientName: 'Emily Johnson',
    patientEmail: 'emily.j@example.com',
    patientPhone: '+1-281-555-0303',
    providerId: 'prov-01',
    providerName: 'Dr. James Chen',
    type: 'Consultation',
    scheduledAt: new Date(Date.now() + 3600000).toISOString(),
    status: 'exception',
    insuranceId: 'ins-UHC-003',
    insuranceVerified: false,
    notes: 'Provider called in sick - needs rescheduling'
  }
];

let providers = [
  { id: 'prov-01', name: 'Dr. James Chen', specialty: 'General', availableSlots: [], status: 'unavailable' },
  { id: 'prov-02', name: 'Dr. Sarah Patel', specialty: 'Endodontics', availableSlots: [
    new Date(Date.now() + 86400000 + 3600000).toISOString(),
    new Date(Date.now() + 86400000 + 7200000).toISOString()
  ], status: 'available' },
  { id: 'prov-03', name: 'Dr. Marcus Williams', specialty: 'General', availableSlots: [
    new Date(Date.now() + 3600000 * 2).toISOString(),
    new Date(Date.now() + 3600000 * 4).toISOString(),
    new Date(Date.now() + 3600000 * 6).toISOString()
  ], status: 'available' }
];

let insuranceVerifications = {};

// ─── Health Check ─────────────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'DentalFlow EHR API', version: '1.0.0', timestamp: new Date().toISOString() });
});

// ─── Appointments ─────────────────────────────────────────────────────────────
app.get('/appointments', (req, res) => {
  const { status, providerId, patientId } = req.query;
  let result = [...appointments];
  if (status) result = result.filter(a => a.status === status);
  if (providerId) result = result.filter(a => a.providerId === providerId);
  if (patientId) result = result.filter(a => a.patientId === patientId);
  res.json({ appointments: result, total: result.length });
});

app.get('/appointments/:id', (req, res) => {
  const appt = appointments.find(a => a.id === req.params.id);
  if (!appt) return res.status(404).json({ error: 'Appointment not found' });
  res.json(appt);
});

app.post('/appointments', (req, res) => {
  const { patientId, patientName, patientEmail, patientPhone, providerId, type, scheduledAt, insuranceId } = req.body;
  if (!patientId || !providerId || !type || !scheduledAt) {
    return res.status(400).json({ error: 'Missing required fields: patientId, providerId, type, scheduledAt' });
  }
  const provider = providers.find(p => p.id === providerId);
  if (!provider) return res.status(404).json({ error: 'Provider not found' });

  const newAppt = {
    id: `appt-${uuidv4().slice(0, 8)}`,
    patientId,
    patientName: patientName || 'Unknown Patient',
    patientEmail: patientEmail || '',
    patientPhone: patientPhone || '',
    providerId,
    providerName: provider.name,
    type,
    scheduledAt,
    status: 'pending',
    insuranceId: insuranceId || null,
    insuranceVerified: false,
    notes: ''
  };
  appointments.push(newAppt);
  res.status(201).json(newAppt);
});

app.patch('/appointments/:id', (req, res) => {
  const idx = appointments.findIndex(a => a.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Appointment not found' });
  appointments[idx] = { ...appointments[idx], ...req.body, id: appointments[idx].id };
  res.json(appointments[idx]);
});

app.delete('/appointments/:id', (req, res) => {
  const idx = appointments.findIndex(a => a.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Appointment not found' });
  appointments[idx].status = 'cancelled';
  res.json({ message: 'Appointment cancelled', appointment: appointments[idx] });
});

// ─── Exceptions (appointments needing agent attention) ────────────────────────
app.get('/exceptions', (req, res) => {
  const exceptions = appointments.filter(a => a.status === 'exception' || a.status === 'pending');
  const enriched = exceptions.map(appt => ({
    ...appt,
    exceptionType: resolveExceptionType(appt),
    priority: resolvePriority(appt),
    suggestedAction: resolveSuggestedAction(appt)
  }));
  res.json({ exceptions: enriched, total: enriched.length });
});

function resolveExceptionType(appt) {
  if (!appt.insuranceVerified) return 'insurance_unverified';
  if (appt.status === 'exception') return 'provider_unavailable';
  return 'pending_confirmation';
}

function resolvePriority(appt) {
  const hoursUntil = (new Date(appt.scheduledAt) - Date.now()) / 3600000;
  if (hoursUntil < 4) return 'critical';
  if (hoursUntil < 24) return 'high';
  return 'normal';
}

function resolveSuggestedAction(appt) {
  if (!appt.insuranceVerified) return 'verify_insurance';
  if (appt.status === 'exception') return 'reschedule_with_available_provider';
  return 'confirm_appointment';
}

// ─── Providers ────────────────────────────────────────────────────────────────
app.get('/providers', (req, res) => {
  const { status, specialty } = req.query;
  let result = [...providers];
  if (status) result = result.filter(p => p.status === status);
  if (specialty) result = result.filter(p => p.specialty.toLowerCase() === specialty.toLowerCase());
  res.json({ providers: result });
});

app.get('/providers/:id/slots', (req, res) => {
  const provider = providers.find(p => p.id === req.params.id);
  if (!provider) return res.status(404).json({ error: 'Provider not found' });
  res.json({ providerId: provider.id, providerName: provider.name, availableSlots: provider.availableSlots });
});

// ─── Insurance Verification ───────────────────────────────────────────────────
app.post('/insurance/verify', (req, res) => {
  const { insuranceId, patientId, appointmentType } = req.body;
  if (!insuranceId || !patientId) {
    return res.status(400).json({ error: 'insuranceId and patientId are required' });
  }
  // Simulate async verification - BCBS and UHC auto-approve, AETNA needs pre-auth
  const approved = !insuranceId.includes('AETNA');
  const result = {
    insuranceId,
    patientId,
    verified: approved,
    coveragePercent: approved ? 80 : 0,
    requiresPreAuth: !approved,
    preAuthCode: approved ? `AUTH-${Math.random().toString(36).slice(2,8).toUpperCase()}` : null,
    message: approved ? 'Coverage verified successfully' : 'Pre-authorization required. Contact AETNA at 1-800-555-2368.'
  };
  insuranceVerifications[`${insuranceId}-${patientId}`] = result;

  // Update appointment if linked
  if (approved) {
    const appt = appointments.find(a => a.insuranceId === insuranceId && a.patientId === patientId);
    if (appt) {
      appt.insuranceVerified = true;
      if (appt.status === 'pending') appt.status = 'confirmed';
    }
  }
  res.json(result);
});

// ─── Patients ─────────────────────────────────────────────────────────────────
app.get('/patients/:id', (req, res) => {
  const appt = appointments.find(a => a.patientId === req.params.id);
  if (!appt) return res.status(404).json({ error: 'Patient not found' });
  res.json({
    patientId: appt.patientId,
    name: appt.patientName,
    email: appt.patientEmail,
    phone: appt.patientPhone,
    appointments: appointments.filter(a => a.patientId === req.params.id)
  });
});

// ─── Agent Actions Log ────────────────────────────────────────────────────────
let agentActions = [];

app.post('/agent/action', (req, res) => {
  const action = {
    id: uuidv4(),
    timestamp: new Date().toISOString(),
    ...req.body
  };
  agentActions.push(action);
  console.log(`[AGENT ACTION] ${action.actionType}: ${JSON.stringify(action.details)}`);
  res.status(201).json(action);
});

app.get('/agent/actions', (req, res) => {
  res.json({ actions: agentActions, total: agentActions.length });
});

// ─── Start ────────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`DentalFlow EHR API running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});

module.exports = app;
