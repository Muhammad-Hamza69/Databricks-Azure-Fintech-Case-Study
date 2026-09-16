# Reverse ETL: Gold -> Fivetran -> Salesforce

**Status: built and verified.** 3,862/3,862 records synced successfully (0 rejected, 0 invalid),
completed in 4 minutes, running on a daily schedule (09:00 UTC).

**Source of truth for the sync**: `clickstream.gold.export_visitor_engagement_salesforce` (a dbt
view - 3,862 rows, one per visitor). It exists specifically so the Salesforce sync has a stable
contract instead of pointing at `gold_visitor_summary` directly - if that table's internal shape
changes later, this view is the one place to adjust so the sync doesn't silently break. Columns:
`visitor_id`, `account_name`, `total_views`, `total_addtocarts`, `total_transactions`,
`distinct_items_viewed`, `first_seen`, `last_seen`, `is_converted`.

This document is the exact click-by-click record of how it was configured, including the two
points where the original plan hit a real-world wall and had to change.

---

## Part A - Salesforce: target fields on Account

**A1. Get into full Setup.** Gear icon (top right) -> if the "Quick Settings" flyout panel
appears (a limited shortcuts panel, no Object Manager on it) -> click **Open Advanced Setup** to
land on the real Setup page.

**A2. Navigate to Account's fields.** On the Setup page, click the **Object Manager** tab (next
to "Home", at the top) -> click **Account** in the object list -> click **Fields & Relationships**
in the left sub-menu.

**A3. Gotcha - the original plan was a dedicated custom object.** The first attempt was
**Object Manager -> Create -> Custom Object**, filling in Label `Visitor Engagement`, Plural
Label `Visitor Engagements`, Object Name `Visitor_Engagement`, Record Name data type **Auto
Number** with format `VE-{0000}` and Starting Number `1`, Deployment Status `Deployed`. Saving
this failed with **"Custom Object Limits Exceeded."** This Salesforce org is on the **Starter**
edition trial, whose custom-object quota is very low and was already fully used by the
platform's own `Knowledge_kav` object (auto-created when the Knowledge feature is enabled - not
something this project created). Custom **fields** on an *existing* standard object don't count
against that limit, so the plan pivoted to adding fields directly onto the standard **Account**
object instead: one visitor = one Account record (e.g. "Visitor 629333"). No object-creation step
needed after that - Account already exists.

**A4. Add the 8 custom fields.** For each field: click **New** (top right of the Fields &
Relationships list) -> **Step 1: Choose the field type** (select the radio button) -> **Next**
-> **Step 2: Enter the details** (Field Label, Length/Decimal Places if numeric, leave
Required/Unique/External ID unchecked unless noted) -> **Next** -> **Step 3: field-level
security** (leave the default - System Administrator profile shows Visible checked) -> **Next**
-> **Step 4: page layout** (leave "Account Layout" checked) -> click **Save & New** to jump
straight into the next field (plain **Save** on the last one):

| # | Field Label | Type | Length/Decimals | Checkboxes |
|---|---|---|---|---|
| 1 | Visitor Id | Number | 18 / 0 | **External ID** + **Unique** (this becomes the upsert match key) |
| 2 | Total Views | Number | 18 / 0 | none |
| 3 | Total AddToCarts | Number | 18 / 0 | none |
| 4 | Total Transactions | Number | 18 / 0 | none |
| 5 | Distinct Items Viewed | Number | 18 / 0 | none |
| 6 | First Seen | Date/Time | - | none |
| 7 | Last Seen | Date/Time | - | none |
| 8 | Is Converted | Checkbox | - | Default Value left unchecked |

API names auto-fill from the Field Label with underscores and a `__c` suffix (e.g. "Visitor Id"
-> `Visitor_Id__c`). Verified all 8 landed correctly by checking the Fields & Relationships list
afterward.

---

## Part B - Fivetran: connect Databricks and Salesforce

**B1. Enable Activations.** Fivetran's reverse-ETL feature is called **Activations** - a
separate product from its normal Connectors/Destinations (which only move data *into* a
warehouse), and it needs enabling once per account. Left sidebar -> **Activations** -> on the
"Enable Reverse ETL with Activations!" screen, click **Enable Activations**.

**B2. Create the Activation Source (Databricks).**
`Activations -> Activation Sources -> + Activation Source`.

- Gotcha: the destination/source picker's default choice was **"Databricks via Managed Data
  Lake Service"**, which demands cloud storage bucket config (Storage Provider, Bucket, Fivetran
  Role ARN, S3 Prefix Path, Bucket Region) that isn't needed here at all. The fix is a link in
  that page's info banner: **"Switch to Databricks Unity Managed tables"** - click it (an
  optional feedback survey modal may appear first; skip or answer it, then click **"Continue to
  Databricks Unity Managed"**). That produces the plain **Databricks** form used below.
- **Sync Engine**: select **Basic** (not the pre-selected "Advanced"). Advanced requires write
  access to a `CENSUS` schema in Databricks for Fivetran's own internal bookkeeping - unnecessary
  setup for this data volume. Basic only needs read access and tracks sync state on Fivetran's
  own infrastructure.
- **Authentication type**: the dropdown defaults to "OAUTH 2.0 (Recommended)" (Client ID/Secret).
  Open that dropdown and pick **PERSONAL ACCESS TOKEN** instead - simpler, and consistent with
  how dbt and Power BI connect to the same warehouse.
- Fill in:

| Field | Value |
|---|---|
| Server Hostname | `adb-7405616477706025.5.azuredatabricks.net` |
| Port | `443` |
| HTTP Path | `/sql/1.0/warehouses/3ae0ca482ea10df2` |
| Access Token | a Databricks PAT generated via `databricks tokens create --comment "fivetran" --lifetime-seconds 7776000` - never committed to the repo |
| Catalog Allow List | `clickstream` |
| Schema Allow List | `gold` |

- Note: an earlier field on this form, "Databricks Deployment Cloud," needed manually setting to
  Azure on one variant of the form - it later disappeared entirely on the corrected (Unity
  Managed) form, presumably auto-detected from the `azuredatabricks.net` hostname.
- Processing region settings (Data Processing Location, Fivetran Processing Cloud Provider, AWS
  Region) are about where Fivetran's own compute runs, unrelated to Databricks being on Azure -
  left at defaults (`US` / `AWS` / `us-east-1`). Storage backend: **Fivetran-managed storage**
  (Fivetran handles intermediate storage itself, no bucket setup needed).
- Click **Confirm** -> **Test Connectivity** runs automatically (network connectivity, warehouse
  credentials, load tables - all 3 passed) -> **Finish**.

**B3. Create the Activation Destination (Salesforce).**
`Activation Destinations -> + Activation Destination -> Salesforce`.

- Name: leave as `Salesforce`.
- **Select a Domain**: `Production` (this org is a fresh Starter trial signup, not a Sandbox).
- Click **Connect** - this opens the Salesforce login/consent screen in a popup (an OAuth grant,
  which has to be completed by a human in a browser - there's no way to automate this step).
  Sign in and approve.
- Result: destination shows **Healthy** status, connected as the Salesforce username against the
  org's instance URL.

**B4. Create the Activation Sync.** `Activation Syncs -> + Activation Sync` (or "New Activation
Sync").

- **Select an Activation Source**: choose **"Any Warehouse Table"** (not "Existing Dataset &
  Segments") -> Connection = the Databricks source from B2 -> Database `clickstream` -> Schema
  `gold` -> Table `export_visitor_engagement_salesforce`.
- **Select an Activation Destination**: Connection = the Salesforce destination from B3 ->
  Object `Account`.
- **Select a Sync Behavior**: **Update or Create** (Fivetran's term for upsert - updates
  existing Salesforce records on a key match, creates new ones otherwise; deliberately not
  "Mirror," which would also delete Salesforce records that disappear from the source).
- Advanced Configuration: leave "Enable bulk lookup" toggled **True** (fewer API calls).
- **Select a Sync Key**: choose column `visitor_id` on the left, field `Visitor Id`
  (`Visitor_Id__c`) on the right - this is the match key: when both are equal, Fivetran updates
  that Account instead of creating a duplicate.
- **Set Up Salesforce Field Mappings**: `account_name -> Account Name` (Required) was
  auto-populated. Clicking **Generate Mappings** correctly auto-matched all 7 remaining columns
  to their Salesforce fields by name similarity - no manual field-by-field mapping needed:

| Source column | Salesforce field |
|---|---|
| `visitor_id` | `Visitor_Id__c` *(sync key)* |
| `account_name` | `Name` *(Account's required standard field)* |
| `total_views` | `Total_Views__c` |
| `total_addtocarts` | `Total_AddToCarts__c` |
| `total_transactions` | `Total_Transactions__c` |
| `distinct_items_viewed` | `Distinct_Items_Viewed__c` |
| `first_seen` | `First_Seen__c` |
| `last_seen` | `Last_Seen__c` |
| `is_converted` | `Is_Converted__c` |

- **Run a Test Sync** (optional, strongly recommended): click **Run Test** - this sends one
  random record from the source straight to a real Salesforce Account, end to end, without
  committing to the full sync yet. It finished in 4 steps (Prepare/Read/Send/Finish, all green)
  and the record it sent (`Visitor 629333`, 2 distinct items viewed, correct timestamps) matched
  the source row exactly - caught nothing wrong before running the full sync.
- Click **Next** -> review the **Summary** panel (Source, Destination, Behavior, Key, all 9
  mappings) -> optionally label the sync (`Gold Visitor Engagement -> Salesforce Account`) ->
  **Setup a Trigger**: switched from the default **Manual** to **Scheduled**, **Daily at 09:00
  UTC** - this data only changes when `dbt run` re-executes, so there's no value syncing more
  often without actively iterating.
- Click **Create**.

**B5. Run the real initial sync.** The sync starts in status "Waiting for first run" after
creation - it does **not** auto-run immediately just because it was created. Click **Run Now**
(top right of the sync's Overview page) to trigger it rather than waiting for the next scheduled
time.

---

## Verified

Initial sync run: **3,862 changed / 3,862 successful, 0 invalid, 0 rejected, 4 minutes total**
(Prepare Sync 2 min 19 sec, Read From Source 41 sec, Send To Destination 46 sec, Finish Sync
1 sec).

Manual spot-check: Salesforce -> **Accounts** tab -> searched `Visitor 629333` -> opened the
record -> every custom field matched the source row in
`clickstream.gold.export_visitor_engagement_salesforce` exactly (Total Views: 3, Total
AddToCarts: 0, Total Transactions: 0, Distinct Items Viewed: 2, First Seen: 1/6/2015 11:36 AM,
Last Seen: 2/6/2015 10:32 AM, Is Converted: unchecked).

**Heads up**: this created 3,862 Account records in the org, mixed in with any real Accounts
created later. If that becomes a problem, consider a naming convention filter or a dedicated
Salesforce Record Type for these.
