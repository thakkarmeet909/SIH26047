-- ═══════════════════════════════════════════════════════════
-- Supabase PostgreSQL Database Schema for CasePad (SIH26047)
-- ═══════════════════════════════════════════════════════════

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. PATIENTS TABLE
create table if not exists patients (
  id uuid primary key default uuid_generate_v4(),
  patient_id text unique not null,
  first_name text not null,
  last_name text not null,
  dob date,
  age integer,
  gender text check (gender in ('male', 'female', 'other')),
  blood_group text,
  phone text not null,
  email text,
  occupation text,
  address text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. CASES TABLE
create table if not exists cases (
  id uuid primary key default uuid_generate_v4(),
  case_number text unique not null,
  patient_id uuid references patients(id) on delete cascade,
  doctor_name text default 'Dr. Sharma',
  status text default 'active' check (status in ('active', 'followup', 'closed')),
  
  -- Step 1: Chief Complaint
  chief_complaint text not null,
  duration text,
  duration_unit text,
  severity integer,
  onset text,
  cc_notes text,

  -- Step 2: HPI
  hpi_narrative text,
  opqrst jsonb default '{}'::jsonb,
  treatment_so_far text,

  -- Step 3: Past History
  pmh_conditions jsonb default '[]'::jsonb,
  pmh_other text,
  surgeries text,
  hospitalizations text,
  allergies text,
  current_medications text,

  -- Step 4: Family History
  family_hx jsonb default '{}'::jsonb,
  family_notes text,

  -- Step 5: Personal History
  personal_hx jsonb default '{}'::jsonb,

  -- Step 6: Review of Systems
  ros jsonb default '{}'::jsonb,
  ros_notes text,

  -- Step 7: Examination
  vitals jsonb default '{}'::jsonb,
  general_exam text,
  systemic_exam jsonb default '{}'::jsonb,

  -- Step 8: Diagnosis
  provisional_diagnosis text not null,
  differential_diagnosis text,
  icd_code text,
  investigations text,
  clinical_notes text,

  -- Step 9: Treatment Plan
  prescriptions jsonb default '[]'::jsonb,
  general_advice text,
  followup_date date,
  followup_notes text,
  referral text,
  prognosis text,

  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Row Level Security (RLS) policies for Supabase
alter table patients enable row level security;
alter table cases enable row level security;

-- Allow public read/write access for demonstration (or customize with Supabase Auth)
create policy "Public read patients" on patients for select using (true);
create policy "Public insert patients" on patients for insert with check (true);
create policy "Public update patients" on patients for update using (true);

create policy "Public read cases" on cases for select using (true);
create policy "Public insert cases" on cases for insert with check (true);
create policy "Public update cases" on cases for update using (true);
