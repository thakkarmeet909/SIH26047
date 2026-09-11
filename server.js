const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// ── SUPABASE CLIENT INITIALIZATION ──
let supabase = null;
const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (supabaseUrl && supabaseKey) {
  const { createClient } = require('@supabase/supabase-js');
  supabase = createClient(supabaseUrl, supabaseKey);
  console.log('✅ Supabase client connected successfully.');
} else {
  console.log('ℹ️ Running with local JSON storage engine. Add SUPABASE_URL & SUPABASE_ANON_KEY to .env to connect Supabase.');
}

// ── LOCAL STORAGE FALLBACK ──
const SOURCE_DB_FILE = path.join(__dirname, 'data.json');
const DB_FILE = process.env.VERCEL ? path.join('/tmp', 'data.json') : SOURCE_DB_FILE;

function readLocalDb() {
  if (!fs.existsSync(DB_FILE)) {
    if (fs.existsSync(SOURCE_DB_FILE)) {
      try {
        const sourceData = fs.readFileSync(SOURCE_DB_FILE, 'utf8');
        try { fs.writeFileSync(DB_FILE, sourceData); } catch (e) {}
        return JSON.parse(sourceData);
      } catch (e) {
        return getDefaultData();
      }
    }
    try { fs.writeFileSync(DB_FILE, JSON.stringify(getDefaultData(), null, 2)); } catch (e) {}
    return getDefaultData();
  }
  try {
    const raw = fs.readFileSync(DB_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    return getDefaultData();
  }
}

function writeLocalDb(data) {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
  } catch (err) {
    console.warn('⚠️ File write ignored (read-only filesystem or serverless environment):', err.message);
  }
}

function getDefaultData() {
  return { doctors: [], patients: [], cases: [], vitals_history: {}, visits: {} };
}

// ── AUTHENTICATION ROUTES ──

// Doctor Login
app.post('/api/auth/doctor-login', (req, res) => {
  try {
    const { doctor_id, pin } = req.body;
    if (!doctor_id || !pin) {
      return res.status(400).json({ error: 'Doctor ID and PIN are required' });
    }
    const db = readLocalDb();
    const doctor = db.doctors.find(
      d => (d.doctor_id.toLowerCase() === doctor_id.toLowerCase() || d.license_number.toLowerCase() === doctor_id.toLowerCase()) && d.pin === pin
    );
    if (!doctor) {
      return res.status(401).json({ error: 'Invalid credentials. Demo: DR-001 / casemed2026' });
    }
    const { pin: _, ...safeDoctor } = doctor;
    res.json({ success: true, role: 'doctor', user: safeDoctor });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Patient Login
app.post('/api/auth/patient-login', (req, res) => {
  try {
    const { phone, otp } = req.body;
    if (!phone) {
      return res.status(400).json({ error: 'Phone number is required' });
    }
    const db = readLocalDb();
    // Accept any 4-digit OTP as "1234" for demo
    if (otp !== '1234') {
      return res.status(401).json({ error: 'Invalid OTP. Demo OTP: 1234' });
    }
    const normalizedPhone = phone.replace(/[\s+\-]/g, '');
    const patient = db.patients.find(p => {
      const pPhone = p.phone.replace(/[\s+\-]/g, '');
      return pPhone === normalizedPhone || pPhone.endsWith(normalizedPhone) || normalizedPhone.endsWith(pPhone.slice(-10));
    });
    if (!patient) {
      return res.status(404).json({ error: 'No patient found with this phone. Demo: 9876543210' });
    }
    const { password: _, ...safePatient } = patient;
    res.json({ success: true, role: 'patient', user: safePatient });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── API ROUTES ──

// Healthcheck
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', engine: supabase ? 'supabase' : 'local-json', timestamp: new Date() });
});

// Dashboard Stats
app.get('/api/dashboard/stats', async (req, res) => {
  try {
    if (supabase) {
      const { count: totalPatients } = await supabase.from('patients').select('*', { count: 'exact', head: true });
      const { count: totalCases } = await supabase.from('cases').select('*', { count: 'exact', head: true });
      const { count: pendingFollowups } = await supabase.from('cases').select('*', { count: 'exact', head: true }).eq('status', 'followup');
      res.json({
        totalPatients: totalPatients || 0,
        casesToday: 12,
        pendingFollowups: pendingFollowups || 0,
        thisMonth: totalCases || 0,
        criticalAlerts: 1,
        revenue: 285000
      });
    } else {
      const db = readLocalDb();
      const pendingFollowups = db.cases.filter(c => c.status === 'followup').length;
      const criticalAlerts = db.cases.filter(c => c.status === 'critical').length;
      res.json({
        totalPatients: db.patients.length,
        casesToday: 12,
        pendingFollowups,
        thisMonth: db.cases.length,
        criticalAlerts,
        revenue: 285000
      });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Patients API
app.get('/api/patients', async (req, res) => {
  try {
    if (supabase) {
      const { data, error } = await supabase.from('patients').select('*').order('created_at', { ascending: false });
      if (error) throw error;
      return res.json(data);
    }
    const db = readLocalDb();
    // Strip passwords before sending
    const safePatients = db.patients.map(({ password, ...p }) => p);
    res.json(safePatients);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Single Patient Detail
app.get('/api/patients/:id', (req, res) => {
  try {
    const db = readLocalDb();
    const patient = db.patients.find(p => p.id === req.params.id);
    if (!patient) return res.status(404).json({ error: 'Patient not found' });
    const { password, ...safePatient } = patient;
    res.json(safePatient);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Patient Vitals History
app.get('/api/patients/:id/vitals', (req, res) => {
  try {
    const db = readLocalDb();
    const vitals = db.vitals_history[req.params.id] || [];
    res.json(vitals);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Patient Visit History
app.get('/api/patients/:id/visits', (req, res) => {
  try {
    const db = readLocalDb();
    const visits = db.visits[req.params.id] || [];
    res.json(visits);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update Patient Profile
app.put('/api/patients/:id', (req, res) => {
  try {
    const db = readLocalDb();
    const idx = db.patients.findIndex(p => p.id === req.params.id);
    if (idx === -1) return res.status(404).json({ error: 'Patient not found' });
    db.patients[idx] = { ...db.patients[idx], ...req.body };
    writeLocalDb(db);
    const { password, ...safePatient } = db.patients[idx];
    res.json(safePatient);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create Patient
app.post('/api/patients', async (req, res) => {
  try {
    const payload = req.body;
    if (!payload.first_name || !payload.last_name) {
      return res.status(400).json({ error: 'First name and Last name are required' });
    }
    if (supabase) {
      const { data, error } = await supabase.from('patients').insert([payload]).select();
      if (error) throw error;
      return res.status(201).json(data[0]);
    }
    const db = readLocalDb();
    const newPt = {
      id: String(Date.now()),
      patient_id: `PT-${1000 + db.patients.length + 1}`,
      ...payload,
      status: 'active',
      risk_level: 'low',
      created_at: new Date().toISOString()
    };
    db.patients.unshift(newPt);
    writeLocalDb(db);
    res.status(201).json(newPt);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Cases API
app.get('/api/cases', async (req, res) => {
  try {
    if (supabase) {
      const { data, error } = await supabase.from('cases').select('*, patients(first_name, last_name)').order('created_at', { ascending: false });
      if (error) throw error;
      return res.json(data);
    }
    const db = readLocalDb();
    res.json(db.cases);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Patient's Cases
app.get('/api/patients/:id/cases', (req, res) => {
  try {
    const db = readLocalDb();
    const patientCases = db.cases.filter(c => c.patient_id === req.params.id);
    res.json(patientCases);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/cases', async (req, res) => {
  try {
    const payload = req.body;
    if (supabase) {
      const { data, error } = await supabase.from('cases').insert([payload]).select();
      if (error) throw error;
      return res.status(201).json(data[0]);
    }
    const db = readLocalDb();
    const newCase = {
      id: `c${Date.now()}`,
      case_number: `CS-2026-00${db.cases.length + 48}`,
      status: 'active',
      created_at: new Date().toISOString(),
      prescriptions: [],
      ...payload
    };
    db.cases.unshift(newCase);
    writeLocalDb(db);
    res.status(201).json(newCase);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Serve index.html for all other GET routes
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Export app for Vercel Serverless Function support
module.exports = app;

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`🚀 CasePad Backend API server running at http://localhost:${PORT}`);
  });
}
