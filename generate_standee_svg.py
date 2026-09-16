import os

def build_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 3600" width="1440" height="3600">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;display=swap');
      text { font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
      .bg { fill: #FFFFFF; }
      .title-navy { fill: #0F172A; font-weight: 800; }
      .text-navy { fill: #0F172A; font-weight: 700; }
      .text-blue { fill: #2563EB; font-weight: 700; }
      .text-slate { fill: #475569; font-weight: 500; }
      .text-muted { fill: #64748B; font-weight: 400; }
      .card-bg { fill: #FFFFFF; stroke: #E2E8F0; stroke-width: 1.5; }
      .card-subtle { fill: #F8FAFC; stroke: #E2E8F0; stroke-width: 1.5; }
      .pill-bg { fill: #FFFFFF; stroke: #CBD5E1; stroke-width: 1.5; }
      .header-line { stroke: #CBD5E1; stroke-width: 2; stroke-linecap: round; }
    </style>

    <linearGradient id="azureGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284C7"/>
      <stop offset="100%" stop-color="#0369A1"/>
    </linearGradient>

    <!-- Icons -->
    <g id="icon-snowflake">
      <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" stroke="#0EA5E9" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="12" cy="12" r="3" fill="#0EA5E9"/>
    </g>
    
    <g id="icon-database">
      <ellipse cx="16" cy="8" rx="12" ry="4" fill="#3B82F6" opacity="0.8"/>
      <path d="M4 8v6c0 2.21 5.37 4 12 4s12-1.79 12-4V8" fill="none" stroke="#2563EB" stroke-width="2.5"/>
      <path d="M4 14v6c0 2.21 5.37 4 12 4s12-1.79 12-4v-6" fill="none" stroke="#1D4ED8" stroke-width="2.5"/>
    </g>

    <g id="icon-gauge">
      <path d="M5 19a12 12 0 1 1 22 0" fill="none" stroke="#2563EB" stroke-width="3" stroke-linecap="round"/>
      <path d="M16 16l6-8" stroke="#1D4ED8" stroke-width="3" stroke-linecap="round"/>
      <circle cx="16" cy="16" r="3" fill="#1D4ED8"/>
    </g>

    <g id="icon-users">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" fill="none" stroke="#7C3AED" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="9" cy="7" r="4" fill="none" stroke="#7C3AED" stroke-width="2.5"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" fill="none" stroke="#9333EA" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75" fill="none" stroke="#9333EA" stroke-width="2.5" stroke-linecap="round"/>
    </g>

    <g id="icon-clock">
      <circle cx="16" cy="16" r="12" fill="none" stroke="#2563EB" stroke-width="2.5"/>
      <path d="M16 10v6l4 2" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round"/>
    </g>

    <g id="icon-gear">
      <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" fill="none" stroke="#2563EB" stroke-width="2"/>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" fill="none" stroke="#2563EB" stroke-width="2"/>
    </g>

    <g id="icon-shield">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M9 12l2 2 4-4" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    </g>

    <g id="icon-barchart">
      <path d="M18 20V10M12 20V4M6 20v-6" stroke="#2563EB" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </g>

    <g id="icon-trend">
      <path d="M23 6l-9.5 9.5-5-5L1 18" fill="none" stroke="#2563EB" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M17 6h6v6" fill="none" stroke="#2563EB" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </g>

    <g id="icon-calendar">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" fill="none" stroke="#E11D48" stroke-width="2.5"/>
      <line x1="16" y1="2" x2="16" y2="6" stroke="#E11D48" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="8" y1="2" x2="8" y2="6" stroke="#E11D48" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="3" y1="10" x2="21" y2="10" stroke="#E11D48" stroke-width="2.5"/>
    </g>
  </defs>

  <!-- Background -->
  <rect width="1440" height="3600" fill="#FFFFFF"/>

  <!-- ================= TOP HEADER ================= -->
  <!-- Brand Header Row -->
  <g transform="translate(70, 70)">
    <!-- Logo Symbol -->
    <rect x="0" y="0" width="48" height="48" rx="12" fill="#2563EB"/>
    <path d="M14 24l8 8 12-16" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    
    <!-- Brand Title -->
    <text x="64" y="34" font-size="34" class="title-navy">Clickstream Lakehouse</text>
    
    <!-- Case Study Pill Badge (Top Right) -->
    <g transform="translate(1080, 0)">
      <rect x="0" y="0" width="190" height="48" rx="24" fill="none" stroke="#0F172A" stroke-width="2"/>
      <!-- Camera Icon -->
      <path d="M18 20h3l2-3h6l2 3h3a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H18a2 2 0 0 1-2-2V22a2 2 0 0 1 2-2z" fill="none" stroke="#0F172A" stroke-width="2"/>
      <circle cx="26" cy="27" r="4" fill="none" stroke="#0F172A" stroke-width="2"/>
      <text x="48" y="32" font-size="18" font-weight="700" fill="#0F172A" letter-spacing="1">CASE STUDY</text>
    </g>
  </g>

  <!-- Main Standee Title -->
  <g transform="translate(720, 240)" text-anchor="middle">
    <text x="0" y="0" font-size="64" font-weight="900" fill="#0F172A" letter-spacing="-0.5">AZURE &amp; DATABRICKS DATA</text>
    <text x="0" y="75" font-size="64" font-weight="900" fill="#0F172A" letter-spacing="-0.5">ENGINEERING CASE STUDY</text>
    
    <!-- Subtitle 1 -->
    <text x="0" y="140" font-size="32" font-weight="700" fill="#2563EB">Modernizing a Fintech Clickstream &amp; ML Data Platform</text>
    
    <!-- Subtitle 2 -->
    <text x="0" y="185" font-size="24" font-weight="500" fill="#475569">Building a scalable, automated, and analytics-ready lakehouse to power real-time fintech insights.</text>
  </g>

  <!-- ================= SECTION 1: THE CHALLENGE ================= -->
  <!-- Section Divider -->
  <g transform="translate(70, 520)">
    <line x1="0" y1="0" x2="480" y2="0" class="header-line"/>
    <use href="#icon-snowflake" x="500" y="-12"/>
    <text x="535" y="8" font-size="28" font-weight="800" fill="#0F172A" letter-spacing="1.5">THE CHALLENGE</text>
    <line x1="820" y1="0" x2="1300" y2="0" class="header-line"/>
  </g>

  <!-- 2x2 Grid of Challenge Cards -->
  <g transform="translate(70, 570)">
    <!-- Card 1: Siloed Data -->
    <g transform="translate(0, 0)">
      <rect width="635" height="200" rx="16" class="card-subtle"/>
      <circle cx="65" cy="100" r="34" fill="#EFF6FF"/>
      <use href="#icon-database" x="49" y="84"/>
      <text x="120" y="70" font-size="28" class="text-navy">Siloed Clickstream Data</text>
      <text x="120" y="105" font-size="20" class="text-slate">Fragmented raw logs and unvalidated tracking</text>
      <text x="120" y="135" font-size="20" class="text-slate">events across multiple fintech applications.</text>
    </g>

    <!-- Card 2: Slow Analytics -->
    <g transform="translate(665, 0)">
      <rect width="635" height="200" rx="16" class="card-subtle"/>
      <circle cx="65" cy="100" r="34" fill="#EFF6FF"/>
      <use href="#icon-gauge" x="49" y="84"/>
      <text x="120" y="70" font-size="28" class="text-navy">Slow Analytics &amp; Latency</text>
      <text x="120" y="105" font-size="20" class="text-slate">Heavy queries on unindexed logs, causing high</text>
      <text x="120" y="135" font-size="20" class="text-slate">latency and delayed financial reporting.</text>
    </g>

    <!-- Card 3: Scale & Personalization -->
    <g transform="translate(0, 220)">
      <rect width="635" height="200" rx="16" class="card-subtle"/>
      <circle cx="65" cy="100" r="34" fill="#F3E8FF"/>
      <use href="#icon-users" x="49" y="84"/>
      <text x="120" y="70" font-size="28" class="text-navy">Scale &amp; ML Features</text>
      <text x="120" y="105" font-size="20" class="text-slate">Millions of raw user events requiring automated</text>
      <text x="120" y="135" font-size="20" class="text-slate">feature engineering for churn prediction models.</text>
    </g>

    <!-- Card 4: Real-Time Accuracy -->
    <g transform="translate(665, 220)">
      <rect width="635" height="200" rx="16" class="card-subtle"/>
      <circle cx="65" cy="100" r="34" fill="#EFF6FF"/>
      <use href="#icon-clock" x="49" y="84"/>
      <text x="120" y="70" font-size="28" class="text-navy">Real-Time Data Quality</text>
      <text x="120" y="105" font-size="20" class="text-slate">Lack of automated testing and schema enforcement</text>
      <text x="120" y="135" font-size="20" class="text-slate">leading to data drift and quality issues.</text>
    </g>
  </g>

  <!-- ================= SECTION 2: THE SOLUTION ================= -->
  <!-- Section Divider -->
  <g transform="translate(70, 1040)">
    <line x1="0" y1="0" x2="490" y2="0" class="header-line"/>
    <use href="#icon-snowflake" x="510" y="-12"/>
    <text x="545" y="8" font-size="28" font-weight="800" fill="#0F172A" letter-spacing="1.5">THE SOLUTION</text>
    <line x1="810" y1="0" x2="1300" y2="0" class="header-line"/>
  </g>

  <!-- Subtitle -->
  <text x="720" y="1095" font-size="24" font-weight="500" fill="#334155" text-anchor="middle">A modern cloud data platform that automates ingestion, transformation, activation and analytics.</text>

  <!-- 4 Horizontal Badges in 1 Row -->
  <g transform="translate(70, 1130)">
    <!-- Badge 1 -->
    <g transform="translate(0, 0)">
      <rect width="310" height="70" rx="14" class="card-subtle"/>
      <use href="#icon-gear" x="25" y="20"/>
      <text x="70" y="43" font-size="20" font-weight="700" fill="#0F172A">Automated Pipelines</text>
    </g>
    <!-- Badge 2 -->
    <g transform="translate(330, 0)">
      <rect width="310" height="70" rx="14" class="card-subtle"/>
      <use href="#icon-shield" x="25" y="20"/>
      <text x="70" y="43" font-size="20" font-weight="700" fill="#0F172A">Reliable dbt Data</text>
    </g>
    <!-- Badge 3 -->
    <g transform="translate(660, 0)">
      <rect width="310" height="70" rx="14" class="card-subtle"/>
      <use href="#icon-snowflake" x="25" y="22"/>
      <text x="65" y="43" font-size="20" font-weight="700" fill="#0F172A">Centralized Lakehouse</text>
    </g>
    <!-- Badge 4 -->
    <g transform="translate(990, 0)">
      <rect width="310" height="70" rx="14" class="card-subtle"/>
      <use href="#icon-barchart" x="25" y="20"/>
      <text x="70" y="43" font-size="20" font-weight="700" fill="#0F172A">Faster Insights &amp; ML</text>
    </g>
  </g>

  <!-- ================= SECTION 3: HOW THE DATA FLOWS ================= -->
  <!-- Section Divider -->
  <g transform="translate(70, 1260)">
    <line x1="0" y1="0" x2="450" y2="0" class="header-line"/>
    <use href="#icon-snowflake" x="470" y="-12"/>
    <text x="505" y="8" font-size="28" font-weight="800" fill="#0F172A" letter-spacing="1.5">HOW THE DATA FLOWS</text>
    <line x1="850" y1="0" x2="1300" y2="0" class="header-line"/>
  </g>

  <!-- Architecture Container Box -->
  <g transform="translate(70, 1310)">
    <rect width="1300" height="910" rx="20" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="2"/>

    <!-- Left Source Pills Stack -->
    <g transform="translate(40, 50)">
      <rect width="240" height="60" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="120" y="38" font-size="18" font-weight="600" fill="#0F172A" text-anchor="middle">Clickstream Events</text>

      <rect y="80" width="240" height="60" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="120" y="118" font-size="18" font-weight="600" fill="#0F172A" text-anchor="middle">Python Producer (Faker)</text>

      <rect y="160" width="240" height="60" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="120" y="198" font-size="18" font-weight="600" fill="#0F172A" text-anchor="middle">User Interaction Logs</text>

      <rect y="240" width="240" height="60" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="120" y="278" font-size="18" font-weight="600" fill="#0F172A" text-anchor="middle">App / Stream Data</text>

      <rect y="320" width="240" height="60" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="120" y="358" font-size="18" font-weight="600" fill="#0F172A" text-anchor="middle">Transaction Logs</text>

      <rect y="400" width="240" height="60" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="120" y="438" font-size="18" font-weight="600" fill="#0F172A" text-anchor="middle">3rd Party Integrations</text>
    </g>

    <!-- Connectors from Left Stack to Ingestion -->
    <path d="M 280 260 L 320 260 L 320 180 L 340 180" fill="none" stroke="#94A3B8" stroke-width="2"/>
    <polygon points="340,180 332,174 332,186" fill="#94A3B8"/>

    <!-- Ingestion Engine Box -->
    <g transform="translate(340, 100)">
      <rect width="170" height="160" rx="12" fill="url(#azureGrad)"/>
      <text x="85" y="70" font-size="20" font-weight="800" fill="#FFFFFF" text-anchor="middle">Azure</text>
      <text x="85" y="98" font-size="18" font-weight="700" fill="#FFFFFF" text-anchor="middle">Function &amp;</text>
      <text x="85" y="122" font-size="16" font-weight="500" fill="#E0F2FE" text-anchor="middle">Event Hubs</text>
    </g>

    <!-- Connector to ADLS Gen2 -->
    <path d="M 510 180 L 540 180" fill="none" stroke="#94A3B8" stroke-width="2"/>
    <polygon points="540,180 532,174 532,186" fill="#94A3B8"/>

    <!-- ADLS Gen2 Storage -->
    <g transform="translate(540, 100)">
      <rect width="160" height="160" rx="12" fill="#0EA5E9"/>
      <use href="#icon-database" x="64" y="30"/>
      <text x="80" y="110" font-size="20" font-weight="800" fill="#FFFFFF" text-anchor="middle">ADLS Gen2</text>
      <text x="80" y="135" font-size="15" font-weight="600" fill="#E0F2FE" text-anchor="middle">Data Lake</text>
    </g>

    <!-- Secondary Ingestion Box (Fivetran / Stream Sync) below ADLS Gen2 -->
    <g transform="translate(540, 300)">
      <rect width="160" height="120" rx="12" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="80" y="50" font-size="18" font-weight="800" fill="#2563EB" text-anchor="middle">Fivetran</text>
      <text x="80" y="75" font-size="14" font-weight="600" fill="#64748B" text-anchor="middle">CDC &amp; Sync</text>
    </g>

    <!-- Connector to Databricks -->
    <path d="M 700 180 L 730 180" fill="none" stroke="#94A3B8" stroke-width="2"/>
    <polygon points="730,180 722,174 722,186" fill="#94A3B8"/>

    <path d="M 700 360 L 730 360 L 730 300" fill="none" stroke="#94A3B8" stroke-width="2"/>

    <!-- Large Databricks & Medallion Architecture Box -->
    <g transform="translate(730, 50)">
      <rect width="530" height="520" rx="16" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/>
      
      <!-- Box Header -->
      <text x="265" y="45" font-size="22" font-weight="800" fill="#0F172A" text-anchor="middle">Databricks Lakehouse &amp; dbt</text>
      <text x="265" y="75" font-size="16" font-weight="700" fill="#F97316" text-anchor="middle">dbt Medallion Architecture</text>

      <!-- Medallion Tables Flow -->
      <g transform="translate(30, 100)">
        <!-- Staging Table -->
        <rect width="140" height="160" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1.5"/>
        <rect width="140" height="36" rx="8" fill="#94A3B8"/>
        <text x="70" y="24" font-size="16" font-weight="700" fill="#FFFFFF" text-anchor="middle">Staging</text>
        <line x1="20" y1="70" x2="120" y2="70" stroke="#CBD5E1" stroke-width="1"/>
        <line x1="20" y1="100" x2="120" y2="100" stroke="#CBD5E1" stroke-width="1"/>
        <line x1="20" y1="130" x2="120" y2="130" stroke="#CBD5E1" stroke-width="1"/>

        <!-- Arrow -->
        <path d="M 140 80 L 165 80" fill="none" stroke="#94A3B8" stroke-width="2"/>
        <polygon points="165,80 157,74 157,86" fill="#94A3B8"/>

        <!-- Silver Table -->
        <g transform="translate(165, 0)">
          <rect width="140" height="160" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1.5"/>
          <rect width="140" height="36" rx="8" fill="#64748B"/>
          <text x="70" y="24" font-size="16" font-weight="700" fill="#FFFFFF" text-anchor="middle">Silver</text>
          <line x1="20" y1="70" x2="120" y2="70" stroke="#CBD5E1" stroke-width="1"/>
          <line x1="20" y1="100" x2="120" y2="100" stroke="#CBD5E1" stroke-width="1"/>
          <line x1="20" y1="130" x2="120" y2="130" stroke="#CBD5E1" stroke-width="1"/>
        </g>

        <!-- Arrow -->
        <path d="M 305 80 L 330 80" fill="none" stroke="#94A3B8" stroke-width="2"/>
        <polygon points="330,80 322,74 322,86" fill="#94A3B8"/>

        <!-- Gold Table -->
        <g transform="translate(330, 0)">
          <rect width="140" height="160" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1.5"/>
          <rect width="140" height="36" rx="8" fill="#EAB308"/>
          <text x="70" y="24" font-size="16" font-weight="700" fill="#FFFFFF" text-anchor="middle">Gold</text>
          <line x1="20" y1="70" x2="120" y2="70" stroke="#CBD5E1" stroke-width="1"/>
          <line x1="20" y1="100" x2="120" y2="100" stroke="#CBD5E1" stroke-width="1"/>
          <line x1="20" y1="130" x2="120" y2="130" stroke="#CBD5E1" stroke-width="1"/>
        </g>
      </g>

      <!-- MLflow & Churn Model Box -->
      <g transform="translate(30, 290)">
        <rect width="470" height="200" rx="12" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1.5"/>
        <text x="235" y="36" font-size="18" font-weight="800" fill="#0F172A" text-anchor="middle">MLflow &amp; LightGBM Churn Engine</text>

        <!-- MLflow inner blocks -->
        <g transform="translate(20, 55)">
          <rect width="125" height="120" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
          <text x="62" y="30" font-size="14" font-weight="700" fill="#2563EB" text-anchor="middle">Experiment</text>
          <text x="62" y="50" font-size="14" font-weight="700" fill="#2563EB" text-anchor="middle">Tracking</text>
          <text x="62" y="85" font-size="12" font-weight="500" fill="#64748B" text-anchor="middle">Metrics &amp; Params</text>

          <rect x="145" width="135" height="120" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
          <text x="212" y="30" font-size="14" font-weight="700" fill="#2563EB" text-anchor="middle">Feature Store</text>
          <text x="212" y="50" font-size="14" font-weight="700" fill="#2563EB" text-anchor="middle">&amp; Model Registry</text>
          <text x="212" y="85" font-size="12" font-weight="500" fill="#64748B" text-anchor="middle">Version Control</text>

          <rect x="290" width="140" height="120" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
          <text x="360" y="30" font-size="14" font-weight="700" fill="#2563EB" text-anchor="middle">Inference App</text>
          <text x="360" y="50" font-size="14" font-weight="700" fill="#2563EB" text-anchor="middle">(Streamlit)</text>
          <text x="360" y="85" font-size="12" font-weight="500" fill="#64748B" text-anchor="middle">Real-Time Scoring</text>
        </g>
      </g>
    </g>

    <!-- Downstream Stack Logos Box (Right Area below Databricks) -->
    <g transform="translate(730, 600)">
      <rect width="530" height="160" rx="12" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5"/>
      <text x="265" y="32" font-size="18" font-weight="800" fill="#0F172A" text-anchor="middle">Activated Downstream Platforms</text>
      
      <g transform="translate(25, 55)">
        <!-- Salesforce -->
        <rect width="140" height="42" rx="8" fill="#EFF6FF"/>
        <text x="70" y="26" font-size="15" font-weight="700" fill="#0284C7" text-anchor="middle">Salesforce</text>

        <!-- Power BI -->
        <rect x="170" width="140" height="42" rx="8" fill="#FEF3C7"/>
        <text x="240" y="26" font-size="15" font-weight="700" fill="#D97706" text-anchor="middle">Power BI</text>

        <!-- Streamlit -->
        <rect x="340" width="140" height="42" rx="8" fill="#FFE4E6"/>
        <text x="410" y="26" font-size="15" font-weight="700" fill="#E11D48" text-anchor="middle">Streamlit App</text>

        <!-- dbt -->
        <rect y="55" width="140" height="42" rx="8" fill="#FFEDD5"/>
        <text x="70" y="81" font-size="15" font-weight="700" fill="#EA580C" text-anchor="middle">dbt Core</text>

        <!-- MLflow -->
        <rect x="170" y="55" width="140" height="42" rx="8" fill="#E0F2FE"/>
        <text x="240" y="81" font-size="15" font-weight="700" fill="#0284C7" text-anchor="middle">MLflow</text>

        <!-- Azure -->
        <rect x="340" y="55" width="140" height="42" rx="8" fill="#F0FDFA"/>
        <text x="410" y="81" font-size="15" font-weight="700" fill="#0D9488" text-anchor="middle">Azure ADLS</text>
      </g>
    </g>

    <!-- Lower Left Operational Integration Box to balance layout -->
    <g transform="translate(40, 510)">
      <rect width="660" height="250" rx="12" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="330" y="35" font-size="18" font-weight="800" fill="#0F172A" text-anchor="middle">Operational &amp; Analytical Tooling Stack</text>
      
      <g transform="translate(30, 60)">
        <rect width="180" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
        <text x="90" y="35" font-size="16" font-weight="700" fill="#2563EB" text-anchor="middle">Faker Data Gen</text>

        <rect x="210" width="180" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
        <text x="300" y="35" font-size="16" font-weight="700" fill="#2563EB" text-anchor="middle">LightGBM Model</text>

        <rect x="420" width="180" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
        <text x="510" y="35" font-size="16" font-weight="700" fill="#2563EB" text-anchor="middle">Fivetran Sync</text>

        <rect y="80" width="180" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
        <text x="90" y="115" font-size="16" font-weight="700" fill="#2563EB" text-anchor="middle">25 dbt Data Tests</text>

        <rect x="210" y="80" width="180" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
        <text x="300" y="115" font-size="16" font-weight="700" fill="#2563EB" text-anchor="middle">delta-rs Ingestion</text>

        <rect x="420" y="80" width="180" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
        <text x="510" y="115" font-size="16" font-weight="700" fill="#2563EB" text-anchor="middle">Rest API &amp; Webhooks</text>
      </g>
    </g>

    <!-- Bottom Stack Title inside Container -->
    <text x="650" y="875" font-size="24" font-weight="800" fill="#0F172A" text-anchor="middle">Clickstream Lakehouse's Data Stack</text>
  </g>

  <!-- ================= SECTION 4: BUSINESS DESTINATIONS ================= -->
  <!-- Section Divider -->
  <g transform="translate(70, 2260)">
    <line x1="0" y1="0" x2="430" y2="0" class="header-line"/>
    <use href="#icon-snowflake" x="450" y="-12"/>
    <text x="485" y="8" font-size="28" font-weight="800" fill="#0F172A" letter-spacing="1.5">BUSINESS DESTINATIONS</text>
    <line x1="870" y1="0" x2="1300" y2="0" class="header-line"/>
  </g>

  <!-- Destinations Grid Row -->
  <g transform="translate(70, 2310)">
    <rect width="1300" height="150" rx="16" class="card-subtle"/>

    <!-- Tool 1: Salesforce -->
    <g transform="translate(60, 35)">
      <circle cx="45" cy="35" r="28" fill="#38BDF8" opacity="0.15"/>
      <path d="M 33 35 C 33 28 40 25 45 28 C 48 24 55 26 57 30 C 62 30 63 36 60 40 C 60 43 53 45 45 45 C 37 45 33 41 33 35 Z" fill="#0284C7"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">Salesforce</text>
    </g>

    <!-- Tool 2: Power BI -->
    <g transform="translate(240, 35)">
      <circle cx="45" cy="35" r="28" fill="#F59E0B" opacity="0.15"/>
      <rect x="30" y="32" width="8" height="18" fill="#D97706"/>
      <rect x="41" y="24" width="8" height="26" fill="#D97706"/>
      <rect x="52" y="18" width="8" height="32" fill="#D97706"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">Power BI</text>
    </g>

    <!-- Tool 3: Streamlit -->
    <g transform="translate(420, 35)">
      <circle cx="45" cy="35" r="28" fill="#EF4444" opacity="0.15"/>
      <polygon points="45,20 58,45 32,45" fill="#E11D48"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">Streamlit</text>
    </g>

    <!-- Tool 4: MLflow -->
    <g transform="translate(600, 35)">
      <circle cx="45" cy="35" r="28" fill="#0284C7" opacity="0.15"/>
      <circle cx="35" cy="35" r="5" fill="#0284C7"/>
      <circle cx="55" cy="25" r="5" fill="#0284C7"/>
      <circle cx="55" cy="45" r="5" fill="#0284C7"/>
      <line x1="35" y1="35" x2="55" y2="25" stroke="#0284C7" stroke-width="2"/>
      <line x1="35" y1="35" x2="55" y2="45" stroke="#0284C7" stroke-width="2"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">MLflow</text>
    </g>

    <!-- Tool 5: Databricks -->
    <g transform="translate(780, 35)">
      <circle cx="45" cy="35" r="28" fill="#F97316" opacity="0.15"/>
      <polygon points="45,20 62,30 45,40 28,30" fill="#EA580C"/>
      <polygon points="45,32 62,42 45,52 28,42" fill="#EA580C"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">Databricks</text>
    </g>

    <!-- Tool 6: dbt Core -->
    <g transform="translate(960, 35)">
      <circle cx="45" cy="35" r="28" fill="#EA580C" opacity="0.15"/>
      <polygon points="45,18 60,35 45,52 30,35" fill="#EA580C"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">dbt Core</text>
    </g>

    <!-- Tool 7: Azure ADLS -->
    <g transform="translate(1140, 35)">
      <circle cx="45" cy="35" r="28" fill="#0D9488" opacity="0.15"/>
      <path d="M 30 45 L 45 20 L 60 45 Z" fill="#0D9488"/>
      <text x="45" y="90" font-size="18" font-weight="700" fill="#0F172A" text-anchor="middle">Azure ADLS</text>
    </g>
  </g>

  <!-- ================= SECTION 5: BUSINESS IMPACT ================= -->
  <!-- Section Divider -->
  <g transform="translate(70, 2500)">
    <line x1="0" y1="0" x2="470" y2="0" class="header-line"/>
    <use href="#icon-snowflake" x="490" y="-12"/>
    <text x="525" y="8" font-size="28" font-weight="800" fill="#0F172A" letter-spacing="1.5">BUSINESS IMPACT</text>
    <line x1="830" y1="0" x2="1300" y2="0" class="header-line"/>
  </g>

  <!-- 2x3 Grid of Business Impact Metrics -->
  <g transform="translate(70, 2550)">
    <!-- Metric 1: Processed Events -->
    <g transform="translate(0, 0)">
      <text x="0" y="65" font-size="64" font-weight="900" fill="#2563EB">2.75M+</text>
      <use href="#icon-barchart" x="260" y="25"/>
      <text x="0" y="115" font-size="22" font-weight="700" fill="#0F172A">Processed Raw Events</text>
      <text x="0" y="145" font-size="18" font-weight="500" fill="#64748B">Real-time clickstream log ingestion</text>
    </g>

    <!-- Metric 2: Data Quality -->
    <g transform="translate(450, 0)">
      <text x="0" y="65" font-size="64" font-weight="900" fill="#059669">100%</text>
      <use href="#icon-shield" x="200" y="25"/>
      <text x="0" y="115" font-size="22" font-weight="700" fill="#0F172A">Data Quality SLA</text>
      <text x="0" y="145" font-size="18" font-weight="500" fill="#64748B">25/25 dbt schema &amp; integrity tests</text>
    </g>

    <!-- Metric 3: PR-AUC Score -->
    <g transform="translate(900, 0)">
      <text x="0" y="65" font-size="64" font-weight="900" fill="#7C3AED">0.392</text>
      <use href="#icon-trend" x="220" y="25"/>
      <text x="0" y="115" font-size="22" font-weight="700" fill="#0F172A">PR-AUC Churn Score</text>
      <text x="0" y="145" font-size="18" font-weight="500" fill="#64748B">LightGBM v7 model precision</text>
    </g>

    <!-- Metric 4: Customer Records -->
    <g transform="translate(0, 200)">
      <text x="0" y="65" font-size="64" font-weight="900" fill="#2563EB">3,862</text>
      <use href="#icon-users" x="220" y="25"/>
      <text x="0" y="115" font-size="22" font-weight="700" fill="#0F172A">Salesforce Records Synced</text>
      <text x="0" y="145" font-size="18" font-weight="500" fill="#64748B">Automated CRM activation pipeline</text>
    </g>

    <!-- Metric 5: Pipeline Runtime SLA -->
    <g transform="translate(450, 200)">
      <text x="0" y="65" font-size="64" font-weight="900" fill="#2563EB">38 Min</text>
      <use href="#icon-clock" x="240" y="25"/>
      <text x="0" y="115" font-size="22" font-weight="700" fill="#0F172A">Pipeline Runtime SLA</text>
      <text x="0" y="145" font-size="18" font-weight="500" fill="#64748B">End-to-end batch processing time</text>
    </g>

    <!-- Metric 6: Real-time Ingestion -->
    <g transform="translate(900, 200)">
      <text x="0" y="65" font-size="64" font-weight="900" fill="#E11D48">24/7</text>
      <use href="#icon-calendar" x="180" y="25"/>
      <text x="0" y="115" font-size="22" font-weight="700" fill="#0F172A">Automated Real-Time Sync</text>
      <text x="0" y="145" font-size="18" font-weight="500" fill="#64748B">Continuous streaming &amp; monitoring</text>
    </g>
  </g>

  <!-- ================= FOOTER BANNER ================= -->
  <g transform="translate(0, 3440)">
    <!-- Dark Navy Bar -->
    <path d="M 0 24 Q 0 0 24 0 L 1416 0 Q 1440 0 1440 24 L 1440 160 L 0 160 Z" fill="#0F172A"/>

    <!-- Left: Profile Icon & Developer Name -->
    <g transform="translate(70, 45)">
      <circle cx="35" cy="35" r="32" fill="#FFFFFF"/>
      <circle cx="35" cy="26" r="12" fill="#0F172A"/>
      <path d="M 15 54 C 15 42 24 38 35 38 C 46 38 55 42 55 54 Z" fill="#0F172A"/>
      
      <text x="85" y="28" font-size="20" font-weight="500" fill="#94A3B8">Developed by</text>
      <text x="85" y="58" font-size="30" font-weight="800" fill="#FFFFFF">Muhammad Hamza</text>
    </g>

    <!-- Right: GitHub Repo -->
    <g transform="translate(1370, 80)" text-anchor="end">
      <text x="0" y="0" font-size="24" font-weight="600" fill="#38BDF8">github.com/Muhammad-Hamza69/Databricks-Azure-Fintech-Case-Study</text>
    </g>
  </g>
</svg>'''
    
    output_path = r"c:\Users\hp\Desktop\New folder (9)\standee\standee_vector.svg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG generated successfully: {output_path}")

if __name__ == "__main__":
    build_svg()
