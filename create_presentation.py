"""
Generates a professional PowerPoint presentation for the Clickstream Lakehouse project.
Matches executive tech presentation standards (full-bleed dark navy hero title page,
dark navy headers, accent blue bars, clean grid cards, zero empty whitespace).
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# ── Colour palette ──────────────────────────────────────────────────────────
DARK_NAVY     = RGBColor(0x1F, 0x4E, 0x79)
ACCENT_BLUE   = RGBColor(0x2E, 0x75, 0xB6)
LIGHT_BLUE    = RGBColor(0xD6, 0xE4, 0xF0)
SUBTITLE_GREY = RGBColor(0x6B, 0x6B, 0x6B)
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
BLACK         = RGBColor(0x00, 0x00, 0x00)
DARK_GREY     = RGBColor(0x33, 0x33, 0x33)
MEDIUM_GREY   = RGBColor(0x55, 0x55, 0x55)
GREEN_BG      = RGBColor(0xE8, 0xF5, 0xE9)
RED_BG        = RGBColor(0xFD, 0xED, 0xED)
WINNER_TEXT   = RGBColor(0x1B, 0x5E, 0x20)
BOX_BORDER    = RGBColor(0xDE, 0xDE, 0xDE)
CARD_BG_DARK  = RGBColor(0x16, 0x39, 0x59)

SLIDE_WIDTH  = 12191365  # 13.333 inches
SLIDE_HEIGHT = 6858000   # 7.5 inches

prs = Presentation()
prs.slide_width  = SLIDE_WIDTH
prs.slide_height = SLIDE_HEIGHT


# ── Helper functions ─────────────────────────────────────────────────────────

def add_blank_slide():
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_top_bar(slide):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, Pt(8))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ACCENT_BLUE
    shape.line.fill.background()


def add_footer(slide, page_num=""):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, SLIDE_HEIGHT - Pt(28), SLIDE_WIDTH, Pt(28)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = DARK_NAVY
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.6), SLIDE_HEIGHT - Pt(24), Inches(8), Pt(22))
    run = tb.text_frame.paragraphs[0].add_run()
    run.text = "Clickstream Lakehouse  |  Azure + Databricks + dbt + MLflow"
    run.font.size = Pt(9.5)
    run.font.color.rgb = WHITE

    if page_num:
        tb2 = slide.shapes.add_textbox(SLIDE_WIDTH - Inches(1.2), SLIDE_HEIGHT - Pt(24), Inches(0.6), Pt(22))
        p = tb2.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        run2 = p.add_run()
        run2.text = page_num
        run2.font.size = Pt(9.5)
        run2.font.color.rgb = WHITE


def add_separator_line(slide, top, left=Inches(0.6), width=Inches(12.13)):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Pt(1.5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ACCENT_BLUE
    shape.line.fill.background()


def add_metric_box(slide, value_text, label_text, left, top, width=Inches(2.88), height=Inches(1.85)):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = DARK_NAVY
    box.line.fill.background()

    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    p1 = tf.paragraphs[0]
    p1.alignment = PP_ALIGN.CENTER
    run_val = p1.add_run()
    run_val.text = value_text
    run_val.font.size = Pt(28)
    run_val.font.bold = True
    run_val.font.color.rgb = WHITE

    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(4)
    run_lbl = p2.add_run()
    run_lbl.text = label_text
    run_lbl.font.size = Pt(10.5)
    run_lbl.font.color.rgb = LIGHT_BLUE


def add_bullet_box(slide, title, subtitle, bullets, left, top, width=Inches(5.9), height=Inches(2.85), font_size=10.5, space_after=6):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = BOX_BORDER
    box.line.width = Pt(1)

    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Pt(6), height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_BLUE
    bar.line.fill.background()

    tb_title = slide.shapes.add_textbox(left + Pt(16), top + Pt(10), width - Pt(24), Pt(24))
    run = tb_title.text_frame.paragraphs[0].add_run()
    run.text = title
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = DARK_NAVY

    if subtitle:
        tb_sub = slide.shapes.add_textbox(left + Pt(16), top + Pt(34), width - Pt(24), Pt(18))
        run2 = tb_sub.text_frame.paragraphs[0].add_run()
        run2.text = subtitle
        run2.font.size = Pt(10)
        run2.font.color.rgb = ACCENT_BLUE
        body_top = top + Pt(54)
        body_height = height - Pt(62)
    else:
        body_top = top + Pt(36)
        body_height = height - Pt(44)

    tb_body = slide.shapes.add_textbox(left + Pt(16), body_top, width - Pt(28), body_height)
    tf_body = tb_body.text_frame
    tf_body.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf_body.paragraphs[0] if i == 0 else tf_body.add_paragraph()
        run_b = p.add_run()
        run_b.text = f"\u2022  {bullet}"
        run_b.font.size = Pt(font_size)
        run_b.font.color.rgb = DARK_GREY
        p.space_after = Pt(space_after)


def add_tech_card(slide, name, description, left, top, width=Inches(3.9), height=Inches(1.35)):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = BOX_BORDER
    box.line.width = Pt(1)

    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Pt(5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_BLUE
    bar.line.fill.background()

    tb_name = slide.shapes.add_textbox(left + Pt(12), top + Pt(10), width - Pt(20), Pt(22))
    run = tb_name.text_frame.paragraphs[0].add_run()
    run.text = name
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = DARK_NAVY

    tb_desc = slide.shapes.add_textbox(left + Pt(12), top + Pt(34), width - Pt(20), height - Pt(40))
    tf_desc = tb_desc.text_frame
    tf_desc.word_wrap = True
    run2 = tf_desc.paragraphs[0].add_run()
    run2.text = description
    run2.font.size = Pt(9.5)
    run2.font.color.rgb = MEDIUM_GREY


def make_table(slide, data, left, top, width, height, col_widths=None, font_size=9.5):
    rows = len(data)
    cols = len(data[0])
    table = slide.shapes.add_table(rows, cols, left, top, width, height).table

    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w

    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = val
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(font_size if r > 0 else font_size + 1)
                para.font.color.rgb = DARK_GREY if r > 0 else WHITE
                para.space_before = Pt(3)
                para.space_after = Pt(3)
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = DARK_NAVY
                for para in cell.text_frame.paragraphs:
                    para.font.bold = True
    return table


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 ─ EXECUTIVE FULL-BLEED DARK NAVY TITLE PAGE
# ════════════════════════════════════════════════════════════════════════════
slide_title = add_blank_slide()

# Full-bleed dark navy background covering entire slide (0,0 to SLIDE_WIDTH, SLIDE_HEIGHT)
bg = slide_title.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT)
bg.fill.solid()
bg.fill.fore_color.rgb = DARK_NAVY
bg.line.fill.background()

# Top Accent Bar
bar = slide_title.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, Pt(8))
bar.fill.solid()
bar.fill.fore_color.rgb = ACCENT_BLUE
bar.line.fill.background()

# Overline Badge
tb_over = slide_title.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Pt(22))
run_o = tb_over.text_frame.paragraphs[0].add_run()
run_o.text = "CLOUD DATA ENGINEERING & ADVANCED ML PLATFORM"
run_o.font.size = Pt(12)
run_o.font.bold = True
run_o.font.color.rgb = ACCENT_BLUE

# Main Hero Title
tb_title = slide_title.shapes.add_textbox(Inches(0.8), Inches(1.15), Inches(11.7), Inches(0.95))
tf_t = tb_title.text_frame
tf_t.word_wrap = True
run_t = tf_t.paragraphs[0].add_run()
run_t.text = "Clickstream Lakehouse"
run_t.font.size = Pt(48)
run_t.font.bold = True
run_t.font.color.rgb = WHITE

# Subtitle
tb_sub = slide_title.shapes.add_textbox(Inches(0.8), Inches(2.15), Inches(11.7), Inches(0.65))
tf_s = tb_sub.text_frame
tf_s.word_wrap = True
run_s = tf_s.paragraphs[0].add_run()
run_s.text = "End-to-End Real-Time Data Platform & Purchase Propensity Machine Learning on Azure Databricks"
run_s.font.size = Pt(17)
run_s.font.color.rgb = LIGHT_BLUE

# Separator Line
sep = slide_title.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.95), Inches(11.73), Pt(2))
sep.fill.solid()
sep.fill.fore_color.rgb = ACCENT_BLUE
sep.line.fill.background()

# Tech Stack Pills (5 dark glass pills)
pills_data = [
    ("⚡ Azure Event Hubs",      Inches(0.8),  Inches(3.2), Inches(2.15)),
    ("🧱 Databricks Auto Loader", Inches(3.1),  Inches(3.2), Inches(2.45)),
    ("⚙️ dbt Transformation",    Inches(5.7),  Inches(3.2), Inches(2.25)),
    ("🎯 LightGBM + MLflow",     Inches(8.1),  Inches(3.2), Inches(2.15)),
    ("☁️ Salesforce Reverse ETL",Inches(10.4), Inches(3.2), Inches(2.13)),
]
for pill_text, p_left, p_top, p_w in pills_data:
    p_box = slide_title.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, p_left, p_top, p_w, Inches(0.42))
    p_box.fill.solid()
    p_box.fill.fore_color.rgb = CARD_BG_DARK
    p_box.line.color.rgb = ACCENT_BLUE
    p_box.line.width = Pt(1)
    tf_p = p_box.text_frame
    tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_para = tf_p.paragraphs[0]
    p_para.alignment = PP_ALIGN.CENTER
    r_p = p_para.add_run()
    r_p.text = pill_text
    r_p.font.size = Pt(10)
    r_p.font.bold = True
    r_p.font.color.rgb = WHITE

# 4 Executive Key Highlight Metric Cards at bottom
metric_y = Inches(4.7)
metrics_data = [
    ("2.75M",   "Clickstream Events Ingested",   Inches(0.8)),
    ("0.97",    "ROC-AUC Prediction Score",     Inches(3.8)),
    ("< 40 min", "Bronze to Gold Pipeline Time", Inches(6.8)),
    ("3,862",   "Daily Salesforce CRM Syncs",    Inches(9.8)),
]
for val, lbl, m_left in metrics_data:
    m_box = slide_title.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, m_left, metric_y, Inches(2.73), Inches(1.85))
    m_box.fill.solid()
    m_box.fill.fore_color.rgb = CARD_BG_DARK
    m_box.line.color.rgb = ACCENT_BLUE
    m_box.line.width = Pt(1.5)

    tf_m = m_box.text_frame
    tf_m.vertical_anchor = MSO_ANCHOR.MIDDLE
    p1 = tf_m.paragraphs[0]
    p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run()
    r1.text = val
    r1.font.size = Pt(30)
    r1.font.bold = True
    r1.font.color.rgb = WHITE

    p2 = tf_m.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(4)
    r2 = p2.add_run()
    r2.text = lbl
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = LIGHT_BLUE

# Footer text on Title Slide
tb_foot = slide_title.shapes.add_textbox(Inches(0.8), Inches(6.85), Inches(11.7), Pt(20))
p_f = tb_foot.text_frame.paragraphs[0]
r_f = p_f.add_run()
r_f.text = "Azure Databricks  •  Unity Catalog  •  dbt  •  MLflow  •  Streamlit  •  Salesforce"
r_f.font.size = Pt(10)
r_f.font.color.rgb = LIGHT_BLUE


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 ─ Title + Problem & Solution + Impact
# ════════════════════════════════════════════════════════════════════════════
slide1 = add_blank_slide()
add_top_bar(slide1)

tb = slide1.shapes.add_textbox(Inches(0.6), Inches(0.12), Inches(10), Pt(14))
run = tb.text_frame.paragraphs[0].add_run()
run.text = "CLOUD DATA ENGINEERING & ML PROJECT"
run.font.size = Pt(10.5)
run.font.bold = True
run.font.color.rgb = ACCENT_BLUE

tb2 = slide1.shapes.add_textbox(Inches(0.6), Inches(0.28), Inches(12), Inches(0.7))
tf2 = tb2.text_frame
tf2.word_wrap = True
p_title = tf2.paragraphs[0]
run_t = p_title.add_run()
run_t.text = "Clickstream Lakehouse Overview"
run_t.font.size = Pt(26)
run_t.font.bold = True
run_t.font.color.rgb = DARK_NAVY
p_title.space_after = Pt(2)

p_sub = tf2.add_paragraph()
run_s = p_sub.add_run()
run_s.text = "End-to-End Data Platform with Purchase Propensity ML on Azure Databricks"
run_s.font.size = Pt(12)
run_s.font.color.rgb = SUBTITLE_GREY

add_separator_line(slide1, Inches(1.05))

add_bullet_box(
    slide1, "Problem Statement", "Current Bottlenecks & Legacy Limitations",
    [
        "Raw clickstream data (2.75M events) stored in flat CSVs with no pipeline or automation.",
        "No real-time ingestion: analyzing user behavior required manual bulk data loads.",
        "No purchase prediction capability: marketing teams made decisions without data-driven signals.",
        "Data quality unverified: duplicate events, null keys, and invalid types went undetected.",
        "No connection between analytics and CRM: Salesforce had zero visibility into visitor engagement."
    ],
    Inches(0.6), Inches(1.15), width=Inches(5.9), height=Inches(3.25), font_size=10.5, space_after=6
)

add_bullet_box(
    slide1, "Solution", "Modern Medallion Architecture & ML Pipeline",
    [
        "Medallion Lakehouse (Bronze/Silver/Gold) on Azure Databricks with Unity Catalog governance.",
        "Event Hubs + Azure Function for real-time streaming ingestion with Auto Loader checkpoint.",
        "dbt data transformation: 12 models, 25 automated tests for quality gating.",
        "ML purchase propensity model: 10 algorithms compared, isotonic-calibrated LightGBM deployed.",
        "Reverse ETL via Fivetran: 3,862 visitor engagement records synced to Salesforce daily.",
        "Streamlit scoring app: real-time model serving on 20,000 candidate interactions."
    ],
    Inches(6.8), Inches(1.15), width=Inches(5.9), height=Inches(3.25), font_size=10.5, space_after=5
)

tb_impact = slide1.shapes.add_textbox(Inches(0.6), Inches(4.52), Inches(5), Pt(24))
run_imp = tb_impact.text_frame.paragraphs[0].add_run()
run_imp.text = "IMPACT OF THE SOLUTION"
run_imp.font.size = Pt(15)
run_imp.font.bold = True
run_imp.font.color.rgb = ACCENT_BLUE

metric_top = Inches(4.9)
add_metric_box(slide1, "0.395",  "PR-AUC (Calibrated Model)",  Inches(0.6),  metric_top, width=Inches(2.88), height=Inches(1.9))
add_metric_box(slide1, "0.97",   "ROC-AUC Score",              Inches(3.68), metric_top, width=Inches(2.88), height=Inches(1.9))
add_metric_box(slide1, "84%",    "Max Calibrated Probability",  Inches(6.76), metric_top, width=Inches(2.88), height=Inches(1.9))
add_metric_box(slide1, "3,862",  "Salesforce Records Synced",   Inches(9.84), metric_top, width=Inches(2.88), height=Inches(1.9))

add_footer(slide1, page_num="1")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 ─ Input Parameters, Model & Algorithms, Accuracy Metrics
# ════════════════════════════════════════════════════════════════════════════
slide2 = add_blank_slide()
add_top_bar(slide2)

tb = slide2.shapes.add_textbox(Inches(0.6), Inches(0.15), Inches(10), Pt(34))
run = tb.text_frame.paragraphs[0].add_run()
run.text = "ML Model Deep Dive"
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = DARK_NAVY

add_separator_line(slide2, Inches(0.76))

add_bullet_box(
    slide2, "Input Parameters", "Features fed to the purchase propensity model",
    [
        "view_count: Number of times the visitor viewed this item",
        "addtocart_count: Number of cart-add events for this item",
        "days_since_last_interaction: Recency (days since last activity)",
        "item_is_available: Boolean flag from item properties",
        "item_category_id deliberately EXCLUDED: nominal ID with no ordering",
        "transaction_count excluded as feature to prevent label leakage",
    ],
    Inches(0.6), Inches(0.88), width=Inches(5.9), height=Inches(2.45), font_size=10, space_after=4
)

add_bullet_box(
    slide2, "Training Dataset", "clickstream.ml_training.ml_training_purchase_propensity",
    [
        "2,144,652 total rows (one per visitor-item interaction pair)",
        "20,743 positive labels (actual purchases = ~0.97% positive rate)",
        "Train/Test split: 75% / 25% with stratified sampling",
        "Source: RetailRocket clickstream dataset (2.75M events)",
        "Label: label_purchased (1 if transaction_count > 0, else 0)",
    ],
    Inches(6.8), Inches(0.88), width=Inches(5.9), height=Inches(2.45), font_size=10, space_after=6
)

algo_top = Inches(3.45)
tb_algo = slide2.shapes.add_textbox(Inches(0.6), algo_top, Inches(10), Pt(22))
run_algo = tb_algo.text_frame.paragraphs[0].add_run()
run_algo.text = "10-Candidate Algorithm Comparison (sorted by PR-AUC)"
run_algo.font.size = Pt(15)
run_algo.font.bold = True
run_algo.font.color.rgb = DARK_NAVY

table_data = [
    ["Candidate", "Type", "PR-AUC", "ROC-AUC", "Status"],
    ["lightgbm_depth6 (WINNER)", "Gradient Boosting (LightGBM)", "0.3916", "0.9726", "Calibrated & Registered"],
    ["xgboost_depth6", "Gradient Boosting (XGBoost)", "0.3893", "0.9720", "Passed"],
    ["random_forest_depth6", "Ensemble (Random Forest)", "0.3890", "0.9741", "Passed"],
    ["random_forest_depth3", "Ensemble (Random Forest)", "0.3657", "0.9724", "Passed"],
    ["logistic_regression (C=0.1)", "Linear Model", "0.3421", "0.9699", "Passed"],
    ["logistic_regression (C=0.01)", "Linear Model", "0.3416", "0.9717", "Passed"],
    ["logistic_regression (C=0.001)", "Linear Model", "0.3414", "0.9717", "Passed"],
    ["logistic_regression (C=1.0)", "Linear Model", "0.3421", "0.9699", "Passed"],
    ["extra_trees_depth6", "Ensemble (Extra Trees)", "0.3240", "0.9702", "Passed"],
    ["naive_bayes", "Probabilistic (Gaussian NB)", "0.2825", "0.9685", "Passed"],
]

table = make_table(
    slide2, table_data,
    Inches(0.6), algo_top + Pt(24), Inches(12.13), Inches(3.08),
    col_widths=[Inches(3.2), Inches(3.2), Inches(1.5), Inches(1.5), Inches(2.73)],
    font_size=9.5
)

for c in range(5):
    cell = table.cell(1, c)
    cell.fill.solid()
    cell.fill.fore_color.rgb = GREEN_BG
    for para in cell.text_frame.paragraphs:
        para.font.bold = True
        para.font.color.rgb = WINNER_TEXT

add_footer(slide2, page_num="2")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 ─ Accuracy Metrics & Calibration + Tech Stack
# ════════════════════════════════════════════════════════════════════════════
slide3 = add_blank_slide()
add_top_bar(slide3)

tb = slide3.shapes.add_textbox(Inches(0.6), Inches(0.15), Inches(10), Pt(34))
run = tb.text_frame.paragraphs[0].add_run()
run.text = "Model Accuracy & Calibration"
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = DARK_NAVY

add_separator_line(slide3, Inches(0.76))

add_bullet_box(
    slide3, "Isotonic Calibration (v7)", "CalibratedClassifierCV wraps LightGBM winner",
    [
        "BEFORE: rows scored 90-100% only converted ~31% in reality",
        "AFTER: predicted vs. actual match closely across every band",
        "Predicted 0-10%  ->  Actual 0.09% observed conversion",
        "Predicted 30-40% ->  Actual 35.5% observed conversion",
        "Predicted 40-50% ->  Actual 42.4% observed conversion",
        "Predicted 60-70% ->  Actual 65.6% observed conversion",
        "Max output across 20K candidates: 84% (no false 99%)",
        "PR-AUC after calibration: 0.395 (ranking quality preserved)",
    ],
    Inches(0.6), Inches(0.88), width=Inches(5.9), height=Inches(2.68), font_size=10, space_after=4
)

add_bullet_box(
    slide3, "Model Selection Criteria", "Beyond PR-AUC: two mandatory checks",
    [
        "Non-degenerate probability spread: test-set std > 0.02",
        "Stress test: hand-built 'disengaged' vs 'engaged' examples",
        "Low engagement (0 views, 60 days stale) must score < 50%",
        "Gap between high and low engagement must be >= 30 points",
        "All 10 candidates pass both checks at full data scale",
        "At demo scale (20 positives), EVERY candidate failed",
        "class_weight='balanced' used across all models",
    ],
    Inches(6.8), Inches(0.88), width=Inches(5.9), height=Inches(2.68), font_size=10, space_after=6
)

tech_top = Inches(3.68)
tb_tech = slide3.shapes.add_textbox(Inches(0.6), tech_top, Inches(5), Pt(22))
run_tech = tb_tech.text_frame.paragraphs[0].add_run()
run_tech.text = "Tech Stack"
run_tech.font.size = Pt(16)
run_tech.font.bold = True
run_tech.font.color.rgb = DARK_NAVY

card_y1 = tech_top + Pt(24)
add_tech_card(slide3, "Azure Databricks", "Unity Catalog-governed Lakehouse: Auto Loader, Delta Lake, MLflow experiment tracking & model registry", Inches(0.6), card_y1, width=Inches(3.9), height=Inches(1.35))
add_tech_card(slide3, "Azure Event Hubs", "Streaming ingestion: 3 hubs (events, item-properties, category-tree) with Avro Capture to ADLS Gen2", Inches(4.71), card_y1, width=Inches(3.9), height=Inches(1.35))
add_tech_card(slide3, "dbt (dbt-databricks)", "12 SQL models across Silver/Gold/ML schemas, 25 automated tests for data quality gating", Inches(8.82), card_y1, width=Inches(3.9), height=Inches(1.35))

card_y2 = card_y1 + Inches(1.42)
add_tech_card(slide3, "scikit-learn + MLflow", "10-candidate comparison, isotonic calibration, auto-registration to Unity Catalog model registry", Inches(0.6), card_y2, width=Inches(3.9), height=Inches(1.35))
add_tech_card(slide3, "LightGBM / XGBoost", "Gradient-boosted tree algorithms: LightGBM won (PR-AUC 0.392), XGBoost runner-up (0.389)", Inches(4.71), card_y2, width=Inches(3.9), height=Inches(1.35))
add_tech_card(slide3, "Streamlit + Fivetran", "Real-time scoring app (20K candidates) + daily reverse ETL sync to Salesforce (3,862 records)", Inches(8.82), card_y2, width=Inches(3.9), height=Inches(1.35))

add_footer(slide3, page_num="3")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 ─ Business Impact Before & After
# ════════════════════════════════════════════════════════════════════════════
slide4 = add_blank_slide()
add_top_bar(slide4)

tb = slide4.shapes.add_textbox(Inches(0.6), Inches(0.15), Inches(10), Pt(34))
run = tb.text_frame.paragraphs[0].add_run()
run.text = "Business Impact: Before & After"
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = DARK_NAVY

add_separator_line(slide4, Inches(0.76))

ba_data = [
    ["Dimension", "BEFORE (Manual / No Pipeline)", "AFTER (Clickstream Lakehouse)"],
    ["Data Ingestion", "Manual CSV bulk loads, no schedule, hours of effort", "Automated streaming via Event Hubs + Auto Loader (every 30 min)"],
    ["Data Quality", "No validation: duplicates, null keys, invalid types", "25 automated dbt tests: not-null, uniqueness, accepted-values"],
    ["Data Freshness", "Stale: analysis only after manual refresh", "Near real-time: Bronze to Gold in < 40 min end-to-end"],
    ["Purchase Prediction", "None: no ML, marketing relies on gut feeling", "Calibrated LightGBM: PR-AUC 0.395, scores 20K candidates/sec"],
    ["CRM Integration", "Zero: Salesforce blind to clickstream behavior", "3,862 visitor records synced daily with engagement data"],
    ["Analytics / BI", "Ad-hoc queries on raw CSVs, no KPI dashboards", "Power BI Gold layer: funnel trends, conversion rates, item perf"],
    ["Model Reliability", "N/A", "Isotonic-calibrated: predicted scores match actual rates within 3%"],
    ["Infrastructure", "Manual setup, no IaC, unreproducible", "Full Terraform + deploy.sh: one-command full rebuild"],
]

ba_table = make_table(
    slide4, ba_data,
    Inches(0.6), Inches(0.88), Inches(12.13), Inches(3.65),
    col_widths=[Inches(2.0), Inches(5.06), Inches(5.07)],
    font_size=9.5
)

for r in range(1, len(ba_data)):
    ba_table.cell(r, 1).fill.solid()
    ba_table.cell(r, 1).fill.fore_color.rgb = RED_BG
    ba_table.cell(r, 2).fill.solid()
    ba_table.cell(r, 2).fill.fore_color.rgb = GREEN_BG

bm_top = Inches(4.65)
tb_bm = slide4.shapes.add_textbox(Inches(0.6), bm_top, Inches(5), Pt(22))
run_bm = tb_bm.text_frame.paragraphs[0].add_run()
run_bm.text = "KEY BUSINESS OUTCOMES"
run_bm.font.size = Pt(15)
run_bm.font.bold = True
run_bm.font.color.rgb = ACCENT_BLUE

bm_y = Inches(4.98)
add_metric_box(slide4, "~95%",      "Less Manual Data Effort",    Inches(0.6),   bm_y, width=Inches(2.28), height=Inches(1.85))
add_metric_box(slide4, "< 40 min",  "End-to-End Pipeline Time",   Inches(3.06),  bm_y, width=Inches(2.28), height=Inches(1.85))
add_metric_box(slide4, "25/25",     "Automated Quality Tests",    Inches(5.52),  bm_y, width=Inches(2.28), height=Inches(1.85))
add_metric_box(slide4, "100%",      "Records Synced Successfully",Inches(7.98),  bm_y, width=Inches(2.28), height=Inches(1.85))
add_metric_box(slide4, "38.4 min",  "Full Pipeline Runtime",      Inches(10.44), bm_y, width=Inches(2.28), height=Inches(1.85))

add_footer(slide4, page_num="4")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 ─ How to Improve the Model More
# ════════════════════════════════════════════════════════════════════════════
slide5 = add_blank_slide()
add_top_bar(slide5)

tb = slide5.shapes.add_textbox(Inches(0.6), Inches(0.15), Inches(10), Pt(34))
run = tb.text_frame.paragraphs[0].add_run()
run.text = "How Can We Improve the Model More"
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = DARK_NAVY

add_separator_line(slide5, Inches(0.76))

add_bullet_box(
    slide5, "Feature Engineering", "Richer features for better signal extraction",
    [
        "Session-level features: session duration, page-sequence patterns, bounce rates",
        "Temporal features: time-of-day, day-of-week purchase patterns, seasonality",
        "Category embedding: learn dense representations instead of excluding category_id",
        "Visitor-level aggregates: lifetime value, cross-category interest breadth",
        "Interaction velocity: rate of engagement change over recent time windows",
    ],
    Inches(0.6), Inches(0.88), width=Inches(5.9), height=Inches(2.88), font_size=10.5, space_after=6
)

add_bullet_box(
    slide5, "Data Enhancements", "More data, better data, richer signals",
    [
        "Real product metadata: names, prices, images for content-based features",
        "External data: marketing campaigns, promotions, seasonal events as signals",
        "Continuous ingestion: move from batch-replay to real-time event streaming",
        "A/B testing framework: controlled experiments on model-driven recommendations",
        "User demographic data: age, location, device type for segmentation",
    ],
    Inches(6.8), Inches(0.88), width=Inches(5.9), height=Inches(2.88), font_size=10.5, space_after=6
)

add_bullet_box(
    slide5, "Advanced Modeling", "More sophisticated algorithms & techniques",
    [
        "Deep learning: TabNet or Wide & Deep neural networks for tabular data",
        "Sequence models: LSTM / Transformer on clickstream event sequences",
        "Hyperparameter tuning: Optuna/Hyperopt systematic search",
        "Ensemble stacking: combine LightGBM + XGBoost + RF for marginal gains",
        "Online learning: incremental updates without full retraining",
        "Uplift modeling: predict incremental lift of interventions",
    ],
    Inches(0.6), Inches(3.9), width=Inches(5.9), height=Inches(2.92), font_size=10.5, space_after=5
)

add_bullet_box(
    slide5, "Operational Improvements", "Production hardening & monitoring",
    [
        "Model monitoring: data drift detection (PSI) + automated retraining triggers",
        "A/B model serving: shadow deploy new versions alongside production",
        "Databricks Model Serving: server-side REST endpoint instead of client-side",
        "Feature Store: centralized, versioned features for train/serve parity",
        "Automated scheduling: retrain on data volume thresholds, not ad-hoc",
        "Explainability: SHAP/LIME dashboards for stakeholder trust",
    ],
    Inches(6.8), Inches(3.9), width=Inches(5.9), height=Inches(2.92), font_size=10.5, space_after=5
)

add_footer(slide5, page_num="5")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 ─ Architecture Diagram
# ════════════════════════════════════════════════════════════════════════════
slide6 = add_blank_slide()
add_top_bar(slide6)

tb = slide6.shapes.add_textbox(Inches(0.6), Inches(0.15), Inches(10), Pt(34))
run = tb.text_frame.paragraphs[0].add_run()
run.text = "System Architecture"
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = DARK_NAVY

add_separator_line(slide6, Inches(0.76))

script_dir = os.path.dirname(os.path.abspath(__file__))
arch_path = os.path.join(script_dir, "Architecture_New.png")
if os.path.exists(arch_path):
    img_width = Inches(12.13)
    img_height = Inches(5.95)
    slide6.shapes.add_picture(arch_path, Inches(0.6), Inches(0.88), width=img_width, height=img_height)

add_footer(slide6, page_num="6")


# ════════════════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════════════════
output_path = os.path.join(script_dir, "Clickstream_Lakehouse_Presentation.pptx")
try:
    prs.save(output_path)
    print(f"Presentation saved to: {output_path}")
except PermissionError:
    alt_path = os.path.join(script_dir, "Clickstream_Lakehouse_Presentation_v4.pptx")
    prs.save(alt_path)
    output_path = alt_path
    print(f"File locked by PowerPoint. Saved copy to: {alt_path}")

print(f"Total slides: {len(prs.slides)}")
print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")
