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
if (process.env.SUPABASE_URL && process.env.SUPABASE_ANON_KEY) {
  const { createClient } = require('@supabase/supabase-js');
  supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);
  console.log('✅ Supabase client connected successfully.');
} else {
  console.log('ℹ️ Running with local JSON storage engine. Add SUPABASE_URL & SUPABASE_ANON_KEY to .env to connect Supabase.');
}

// ── LOCAL STORAGE FALLBACK ──
const SOURCE_DB_FILE = path.join(__dirname, 'data.json');
const DB_FILE = process.env.VERCEL ? path.join('/tmp', 'data.json') : SOURCE_DB_FILE;

const defaultData = {
  patients: [
    { id: '1', patient_id: 'PT-1001', first_name: 'Rajesh', last_name: 'Ahuja', age: 45, gender: 'M', phone: '+91 98765 43210', email: 'rajesh.ahuja@email.com', created_at: new Date().toISOString() },
    { id: '2', patient_id: 'PT-1002', first_name: 'Priya', last_name: 'Sinha', age: 32, gender: 'F', phone: '+91 87654 32109', email: 'priya.s@email.com', created_at: new Date().toISOString() },
    { id: '3', patient_id: 'PT-1003', first_name: 'Mohit', last_name: 'Kumar', age: 58, gender: 'M', phone: '+91 76543 21098', email: 'mohit.k@email.com', created_at: new Date().toISOString() },
    { id: '4', patient_id: 'PT-1004', first_name: 'Sunita', last_name: 'Gupta', age: 27, gender: 'F', phone: '+91 65432 10987', email: 'sunita.g@email.com', created_at: new Date().toISOString() },
    { id: '5', patient_id: 'PT-1005', first_name: 'Anil', last_name: 'Verma', age: 63, gender: 'M', phone: '+91 54321 09876', email: 'anil.v@email.com', created_at: new Date().toISOString() }
  ],
  cases: [
    {
      id: 'c1',
      case_number: 'CS-2026-0047',
      patient_id: '1',
      patient_name: 'Rajesh Ahuja',
      age: 45,
      gender: 'M',
      chief_complaint: 'Persistent cough & chest tightness',
      provisional_diagnosis: 'Acute bronchitis',
      status: 'active',
      created_at: '2026-09-10T08:30:00.000Z'
    },
    {
      id: 'c2',
      case_number: 'CS-2026-0046',
      patient_id: '2',
      patient_name: 'Priya Sinha',
      age: 32,
      gender: 'F',
      chief_complaint: 'Recurrent headaches, blurred vision',
      provisional_diagnosis: 'Migraine with aura',
      status: 'followup',
      created_at: '2026-09-09T10:15:00.000Z'
    },
    {
      id: 'c3',
      case_number: 'CS-2026-0045',
      patient_id: '3',
      patient_name: 'Mohit Kumar',
      age: 58,
      gender: 'M',
      chief_complaint: 'Joint pain, morning stiffness',
      provisional_diagnosis: 'Rheumatoid arthritis',
      status: 'active',
      created_at: '2026-09-09T14:45:00.000Z'
    },
    {
      id: 'c4',
      case_number: 'CS-2026-0044',
      patient_id: '4',
      patient_name: 'Sunita Gupta',
      age: 27,
      gender: 'F',
      chief_complaint: 'Fatigue, weight gain, cold intolerance',
      provisional_diagnosis: 'Hypothyroidism',
      status: 'closed',
      created_at: '2026-09-08T11:20:00.000Z'
    },
    {
      id: 'c5',
      case_number: 'CS-2026-0043',
      patient_id: '5',
      patient_name: 'Anil Verma',
      age: 63,
      gender: 'M',
      chief_complaint: 'Epigastric pain, acid reflux',
      provisional_diagnosis: 'GERD',
      status: 'followup',
      created_at: '2026-09-07T09:00:00.000Z'
    }
  ]
};

function readLocalDb() {
  if (!fs.existsSync(DB_FILE)) {
    if (fs.existsSync(SOURCE_DB_FILE)) {
      try {
        const sourceData = fs.readFileSync(SOURCE_DB_FILE, 'utf8');
        try { fs.writeFileSync(DB_FILE, sourceData); } catch (e) {}
        return JSON.parse(sourceData);
      } catch (e) {
        return defaultData;
      }
    }
    try { fs.writeFileSync(DB_FILE, JSON.stringify(defaultData, null, 2)); } catch (e) {}
    return defaultData;
  }
  try {
    const raw = fs.readFileSync(DB_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    return defaultData;
  }
}

function writeLocalDb(data) {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
  } catch (err) {
    console.warn('⚠️ File write ignored (read-only filesystem or serverless environment):', err.message);
  }
}

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
        thisMonth: totalCases || 0
      });
    } else {
      const db = readLocalDb();
      const pendingFollowups = db.cases.filter(c => c.status === 'followup').length;
      res.json({
        totalPatients: db.patients.length,
        casesToday: 12,
        pendingFollowups: pendingFollowups,
        thisMonth: db.cases.length
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
    res.json(db.patients);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/patients', async (req, res) => {
  try {
    const payload = req.body;
    if (!payload.first_name || !payload.last_name) {
      return res.status(400).json({ error: 'First name and Last name are required' });
    }

    if (payload.gender) {
      const g = payload.gender.toLowerCase();
      payload.gender = g.startsWith('m') ? 'male' : g.startsWith('f') ? 'female' : 'other';
    }

    if (supabase) {
      if (!payload.patient_id) {
        payload.patient_id = `PT-${Math.floor(1000 + Math.random() * 9000)}`;
      }
      const { data, error } = await supabase.from('patients').insert([payload]).select();
      if (error) throw error;
      return res.status(201).json(data[0]);
    }

    const db = readLocalDb();
    const newPt = {
      id: String(Date.now()),
      patient_id: `PT-${1000 + db.patients.length + 1}`,
      ...payload,
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
