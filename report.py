import sys
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
from datetime import datetime
import io

# ─── Configuration ────────────────────────────────────────────────────────────
TICKERS = sys.argv[1:] if len(sys.argv) > 1 else ["AAPL", "TSLA", "MSFT"]
PERIOD  = "1y"

print(f"Generating report for: {', '.join(TICKERS)}")

# ─── Fetch data ───────────────────────────────────────────────────────────────
data = {}
for ticker in TICKERS:
    print(f"  Downloading {ticker}...")
    df = yf.Ticker(ticker).history(period=PERIOD)
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    data[ticker] = df

# ─── Generate one chart per ticker ────────────────────────────────────────────
def make_chart(ticker, df):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor("#0f0f0f")
    ax.set_facecolor("#1a1a1a")

    ax.plot(df.index, df["Close"], color="#00d4ff", linewidth=1.2, label="Price")
    ax.plot(df.index, df["MA20"],  color="#ffaa00", linewidth=0.9, linestyle="--", label="MA20")
    ax.plot(df.index, df["MA50"],  color="#ff4444", linewidth=0.9, linestyle="--", label="MA50")

    ax.set_title(f"{ticker} - Price history ({PERIOD})", color="white", fontsize=11)
    ax.tick_params(colors="white", labelsize=7)
    ax.set_ylabel("Price ($)", color="white", fontsize=8)
    ax.legend(facecolor="#1a1a1a", labelcolor="white", fontsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    buf.seek(0)
    return buf

charts = {ticker: make_chart(ticker, df) for ticker, df in data.items()}
print("Charts generated ✅")

# ─── Compute stats ────────────────────────────────────────────────────────────
def get_stats(ticker, df):
    p0, p1 = df["Close"].iloc[0], df["Close"].iloc[-1]
    perf = ((p1 - p0) / p0) * 100
    vol  = df["Close"].pct_change().std() * 100
    return {
        "ticker":      ticker,
        "current":     f"${p1:.2f}",
        "performance": f"{perf:+.2f}%",
        "volatility":  f"{vol:.2f}%/day",
        "52w_high":    f"${df['High'].max():.2f}",
        "52w_low":     f"${df['Low'].min():.2f}",
        "avg_volume":  f"{df['Volume'].mean()/1e6:.1f}M",
        "perf_value":  perf,
    }

stats = [get_stats(t, df) for t, df in data.items()]

# ─── Build PDF ────────────────────────────────────────────────────────────────
def make_chart(ticker, df):
    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8f9fa")

    ax.plot(df.index, df["Close"], color="#2563eb", linewidth=1.5, label="Price")
    ax.plot(df.index, df["MA20"],  color="#f59e0b", linewidth=1,   linestyle="--", label="MA20")
    ax.plot(df.index, df["MA50"],  color="#ef4444", linewidth=1,   linestyle="--", label="MA50")

    ax.set_title(f"{ticker} - Price history ({PERIOD})", fontsize=11, fontweight="bold", color="#111827")
    ax.tick_params(colors="#6b7280", labelsize=7)
    ax.set_ylabel("Price ($)", color="#6b7280", fontsize=8)
    ax.legend(fontsize=7, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_edgecolor("#e5e7eb")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf

charts = {ticker: make_chart(ticker, df) for ticker, df in data.items()}

filename = f"report_{'_'.join(TICKERS)}_{datetime.today().strftime('%Y%m%d')}.pdf"
doc = SimpleDocTemplate(filename, pagesize=A4,
                        leftMargin=1.8*cm, rightMargin=1.8*cm,
                        topMargin=2*cm, bottomMargin=2*cm)

styles = getSampleStyleSheet()

title_style = ParagraphStyle("title", fontSize=22, fontName="Helvetica-Bold",
                              textColor=colors.HexColor("#111827"), spaceAfter=4)
sub_style   = ParagraphStyle("sub", fontSize=9, fontName="Helvetica",
                              textColor=colors.HexColor("#6b7280"), spaceAfter=16)
ticker_style = ParagraphStyle("ticker", fontSize=13, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#111827"), spaceBefore=16, spaceAfter=6)

elements = []

elements.append(Paragraph("Stock Analysis Report", title_style))
elements.append(Spacer(1, 0.5*cm))
elements.append(Paragraph(f"Generated on {datetime.today().strftime('%B %d, %Y')}  ·  Period: {PERIOD}  ·  {', '.join(TICKERS)}", sub_style))

# Summary table
table_data = [["Ticker", "Price", "Performance", "Volatility", "52w High", "52w Low", "Avg Vol"]]
for s in stats:
    table_data.append([
        s["ticker"], s["current"], s["performance"],
        s["volatility"], s["52w_high"], s["52w_low"], s["avg_volume"]
    ])

perf_colors = [colors.HexColor("#16a34a") if s["perf_value"] > 0 else colors.HexColor("#dc2626") for s in stats]

t = Table(table_data, colWidths=[2*cm, 2.5*cm, 2.8*cm, 2.8*cm, 2.3*cm, 2.3*cm, 1.8*cm])
t.setStyle(TableStyle([
    ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a5f")),
    ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
    ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
    ("FONTSIZE",     (0, 0), (-1, -1), 8.5),
    ("ROWBACKGROUNDS",(0, 1),(-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#111827")),
    ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
    ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
    ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
    ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING",   (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ("FONTNAME",     (0, 1), (0, -1),  "Helvetica-Bold"),
] + [("TEXTCOLOR", (2, i+1), (2, i+1), perf_colors[i]) for i in range(len(stats))]))

elements.append(t)

for s, (ticker, chart_buf) in zip(stats, charts.items()):
    elements.append(KeepTogether([
        Paragraph(ticker, ticker_style),
        Image(chart_buf, width=17*cm, height=6*cm),
    ]))

doc.build(elements)
print(f"✅ Report saved → {filename}")