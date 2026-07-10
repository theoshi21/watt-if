"""
Generate DFD diagrams for WATT-IF as PNG images using matplotlib.
Run: python Documentation/generate_dfd.py
Output: Documentation/DFD_Level0.png, DFD_Level1.png, DFD_Level2_Ingestion.png,
        DFD_Level2_Forecasting.png, DFD_Level2_RAGChat.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Color palette ---
CLR_ENTITY = "#4A90D9"     # Blue - external entities
CLR_PROCESS = "#7BC67E"    # Green - processes
CLR_STORE = "#F5A623"      # Orange - data stores
CLR_ARROW = "#333333"      # Dark gray - arrows
CLR_BG = "#FFFFFF"         # White background
CLR_TEXT = "#1A1A1A"       # Near-black text


def draw_entity(ax, x, y, text, w=1.8, h=0.6):
    """Draw an external entity (rectangle)."""
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.05",
                          facecolor=CLR_ENTITY, edgecolor="#2C6FAC",
                          linewidth=1.5, alpha=0.9)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=8, fontweight='bold', color='white', wrap=True)


def draw_process(ax, x, y, text, w=2.0, h=0.7):
    """Draw a process (rounded rectangle)."""
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.1",
                          facecolor=CLR_PROCESS, edgecolor="#4A9E4D",
                          linewidth=1.5, alpha=0.9)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=7.5, fontweight='bold', color=CLR_TEXT, wrap=True)


def draw_store(ax, x, y, text, w=2.0, h=0.5):
    """Draw a data store (open-ended rectangle)."""
    ax.plot([x - w/2, x + w/2], [y + h/2, y + h/2], color="#D4780A", lw=1.5)
    ax.plot([x - w/2, x + w/2], [y - h/2, y - h/2], color="#D4780A", lw=1.5)
    ax.plot([x - w/2, x - w/2], [y - h/2, y + h/2], color="#D4780A", lw=1.5)
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="square,pad=0",
                          facecolor="#FFF3E0", edgecolor="none", alpha=0.7)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=7, fontweight='bold', color="#8B5E00")


def draw_arrow(ax, x1, y1, x2, y2, label="", color=CLR_ARROW, curved=False):
    """Draw a labeled arrow between two points."""
    style = "arc3,rad=0.2" if curved else "arc3,rad=0"
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle='->', mutation_scale=12,
                            connectionstyle=style,
                            color=color, lw=1.2)
    ax.add_patch(arrow)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha='center', va='bottom',
                fontsize=6, color="#555555", style='italic')


def setup_ax(fig, ax, title, xlim=(-6, 6), ylim=(-5, 5)):
    """Configure axis for DFD drawing."""
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=15)


# ==========================================================================
# LEVEL 0: Context Diagram
# ==========================================================================
def generate_level0():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    setup_ax(fig, ax, "WATT-IF — Context Diagram (Level 0 DFD)",
             xlim=(-7, 7), ylim=(-5, 5))

    # Central process
    draw_process(ax, 0, 0, "WATT-IF\nSystem", w=2.5, h=1.2)

    # External entities
    draw_entity(ax, -5.5, 0, "User", w=1.6, h=0.7)
    draw_entity(ax, 5.5, 2.5, "Meralco S3", w=1.8, h=0.7)
    draw_entity(ax, 5.5, 0.8, "Open-Meteo\nAPI", w=1.8, h=0.7)
    draw_entity(ax, 5.5, -0.8, "NOAA ONI", w=1.8, h=0.7)
    draw_entity(ax, 5.5, -2.5, "Ollama LLM", w=1.8, h=0.7)

    # Arrows: User <-> System
    draw_arrow(ax, -4.7, 0.15, -1.25, 0.15, "Credentials, CSV,\nEntries, Questions")
    draw_arrow(ax, -1.25, -0.15, -4.7, -0.15, "JWT, Forecasts,\nAnswers, Reports")

    # Arrows: System <-> External APIs
    draw_arrow(ax, 1.25, 0.6, 4.6, 2.4, "HTTP Request")
    draw_arrow(ax, 4.6, 2.6, 1.25, 0.7, "Rate PDF", curved=True)

    draw_arrow(ax, 1.25, 0.3, 4.6, 0.8, "Weather Query")
    draw_arrow(ax, 4.6, 0.7, 1.25, 0.2, "Weather Data", curved=True)

    draw_arrow(ax, 1.25, -0.2, 4.6, -0.8, "ENSO Query")
    draw_arrow(ax, 4.6, -0.9, 1.25, -0.3, "ENSO Phase", curved=True)

    draw_arrow(ax, 1.25, -0.6, 4.6, -2.4, "Prompt + Context")
    draw_arrow(ax, 4.6, -2.6, 1.25, -0.7, "Answer Tokens", curved=True)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=CLR_ENTITY, edgecolor="#2C6FAC", label='External Entity'),
        mpatches.Patch(facecolor=CLR_PROCESS, edgecolor="#4A9E4D", label='Process'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "DFD_Level0.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Generated: {path}")


# ==========================================================================
# LEVEL 1: System Decomposition
# ==========================================================================
def generate_level1():
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    setup_ax(fig, ax, "WATT-IF — Level 1 DFD",
             xlim=(-8, 8), ylim=(-7, 7))

    # External entities
    draw_entity(ax, -7, 5, "User", w=1.4, h=0.6)
    draw_entity(ax, 7, 5, "Meralco S3", w=1.6, h=0.6)
    draw_entity(ax, 7, 3, "Open-Meteo", w=1.6, h=0.6)
    draw_entity(ax, 7, 1, "NOAA ONI", w=1.6, h=0.6)
    draw_entity(ax, 7, -1, "Ollama LLM", w=1.6, h=0.6)

    # Processes
    draw_process(ax, -4, 5, "1.0\nAuthentication", w=2.2, h=0.8)
    draw_process(ax, -4, 2.5, "2.0\nData Ingestion", w=2.2, h=0.8)
    draw_process(ax, 0, 0.5, "3.0\nFeature\nEnrichment", w=2.0, h=0.9)
    draw_process(ax, -4, -1.5, "4.0\nModel Training", w=2.2, h=0.8)
    draw_process(ax, 0, -3.5, "5.0\nForecasting", w=2.0, h=0.8)
    draw_process(ax, 4, -3.5, "6.0\nRAG Chat", w=2.0, h=0.8)
    draw_process(ax, 4, 5, "7.0\nRate Scraping", w=2.0, h=0.8)
    draw_process(ax, 0, -6, "8.0\nHealth\nMonitoring", w=2.0, h=0.8)

    # Data stores
    draw_store(ax, -4, 0.5, "D1 User DB (SQLite)", w=2.4, h=0.5)
    draw_store(ax, 0, 2.5, "D2 Billing Records", w=2.2, h=0.5)
    draw_store(ax, 4, 1.5, "D6 Rate Cache", w=2.0, h=0.5)
    draw_store(ax, -4, -4, "D4 Model Artefacts", w=2.4, h=0.5)
    draw_store(ax, 4, -1, "D5 Vector Store", w=2.2, h=0.5)
    draw_store(ax, -7, -3, "D3 Chat History", w=2.0, h=0.5)

    # Key arrows (simplified for readability)
    # User -> Auth
    draw_arrow(ax, -6.3, 5, -5.1, 5, "Credentials")
    # Auth -> D1
    draw_arrow(ax, -4, 4.6, -4, 0.75, "User Data")
    # User -> Data Ingestion
    draw_arrow(ax, -7, 4.7, -5.1, 2.7, "CSV/Entry")
    # Data Ingestion -> D2
    draw_arrow(ax, -2.9, 2.5, -1.1, 2.5, "Records")
    # D2 -> Feature Enrichment
    draw_arrow(ax, 0, 2.25, 0, 0.95, "Raw Records")
    # External APIs -> Feature Enrichment
    draw_arrow(ax, 6.2, 3, 1.0, 0.8, "Weather")
    draw_arrow(ax, 6.2, 1, 1.0, 0.6, "ENSO")
    # Rate Scraping -> Rate Cache
    draw_arrow(ax, 4, 4.6, 4, 1.75, "Parsed Rates")
    # Meralco -> Rate Scraping
    draw_arrow(ax, 6.2, 5, 5.0, 5, "PDF")
    # Rate Cache -> Feature Enrichment
    draw_arrow(ax, 3.0, 1.5, 1.0, 0.7, "Rate")
    # Feature Enrichment -> Training
    draw_arrow(ax, -1.0, 0.2, -2.9, -1.3, "Enriched Data")
    # Training -> Model Artefacts
    draw_arrow(ax, -4, -1.9, -4, -3.75, "Model .joblib")
    # Model Artefacts -> Forecasting
    draw_arrow(ax, -2.8, -4, -1.0, -3.7, "Load Model")
    # Forecasting -> Vector Store
    draw_arrow(ax, 1.0, -3.3, 2.9, -1.2, "Forecast Docs")
    # Vector Store -> RAG Chat
    draw_arrow(ax, 5.1, -1, 5.0, -3.1, "Context Docs")
    # RAG Chat -> Ollama
    draw_arrow(ax, 5.0, -3.2, 6.2, -1, "Prompt")
    draw_arrow(ax, 6.2, -1.2, 5.0, -3.4, "Tokens", curved=True)
    # User <- Forecasting
    draw_arrow(ax, -1.0, -3.7, -7, 4.5, "Forecast Results")
    # RAG Chat -> Chat History
    draw_arrow(ax, 3.0, -3.7, -6.0, -3, "Messages")

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=CLR_ENTITY, edgecolor="#2C6FAC", label='External Entity'),
        mpatches.Patch(facecolor=CLR_PROCESS, edgecolor="#4A9E4D", label='Process'),
        mpatches.Patch(facecolor="#FFF3E0", edgecolor="#D4780A", label='Data Store'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "DFD_Level1.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Generated: {path}")


# ==========================================================================
# LEVEL 2: Data Ingestion
# ==========================================================================
def generate_level2_ingestion():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    setup_ax(fig, ax, "WATT-IF — Level 2 DFD: Process 2.0 (Data Ingestion)",
             xlim=(-7, 7), ylim=(-5, 5))

    # External entity
    draw_entity(ax, -6, 3, "User", w=1.4, h=0.6)

    # Processes
    draw_process(ax, -2, 3, "2.1\nValidate &\nParse CSV", w=2.0, h=0.9)
    draw_process(ax, 2, 3, "2.2\nClean &\nImpute", w=2.0, h=0.9)
    draw_process(ax, 5, 3, "2.3\nDeduplicate\n& Store", w=2.0, h=0.9)
    draw_process(ax, -2, 0, "2.4\nValidate\nManual Entry", w=2.0, h=0.9)
    draw_process(ax, 2, -2, "2.5\nCheck Auto\nRetrain", w=2.0, h=0.9)

    # Data stores
    draw_store(ax, 5, 0, "D2 Billing Records", w=2.4, h=0.5)
    draw_store(ax, -2, -3.5, "D1 User Settings", w=2.2, h=0.5)

    # Arrows
    draw_arrow(ax, -5.3, 3, -3.0, 3, "CSV File")
    draw_arrow(ax, -1.0, 3, 1.0, 3, "Parsed Rows")
    draw_arrow(ax, 3.0, 3, 4.0, 3, "Cleaned Rows")
    draw_arrow(ax, 5, 2.55, 5, 0.25, "Store Records")
    draw_arrow(ax, -6, 2.7, -3.0, 0.2, "Manual Entry")
    draw_arrow(ax, -1.0, -0.1, 3.9, -0.1, "Entry Row")
    draw_arrow(ax, 5, -0.25, 3.0, -1.8, "Record Count")
    draw_arrow(ax, -2, -3.25, -2, -0.45, "Settings")
    draw_arrow(ax, 0.9, -2, -0.9, -3.3, "Read Threshold")
    draw_arrow(ax, 5.5, 2.5, -5.5, 2.5, "Cleaning Report", curved=True)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=CLR_ENTITY, edgecolor="#2C6FAC", label='External Entity'),
        mpatches.Patch(facecolor=CLR_PROCESS, edgecolor="#4A9E4D", label='Process'),
        mpatches.Patch(facecolor="#FFF3E0", edgecolor="#D4780A", label='Data Store'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "DFD_Level2_Ingestion.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Generated: {path}")


# ==========================================================================
# LEVEL 2: Forecasting
# ==========================================================================
def generate_level2_forecasting():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    setup_ax(fig, ax, "WATT-IF — Level 2 DFD: Process 5.0 (Forecasting)",
             xlim=(-7, 7), ylim=(-5, 5))

    # External entity
    draw_entity(ax, -6, 4, "User", w=1.4, h=0.6)

    # Processes
    draw_process(ax, -2, 4, "5.1\nLoad User\nModel", w=2.0, h=0.9)
    draw_process(ax, -2, 1.5, "5.2\nEstimate\nExog Vars", w=2.0, h=0.9)
    draw_process(ax, 2, 1.5, "5.3\nGenerate\nForecast", w=2.0, h=0.9)
    draw_process(ax, 2, -1, "5.4\nDerive\nPrice", w=2.0, h=0.9)
    draw_process(ax, 2, -3.5, "5.5\nCheck\nThresholds", w=2.0, h=0.9)

    # Data stores
    draw_store(ax, -6, 1.5, "D4 Model Artefacts", w=2.2, h=0.5)
    draw_store(ax, -6, -1, "D2 Billing Records", w=2.2, h=0.5)
    draw_store(ax, 6, 1.5, "D5 Vector Store", w=2.0, h=0.5)
    draw_store(ax, 6, -3.5, "D1 User Settings", w=2.0, h=0.5)

    # Arrows
    draw_arrow(ax, -5.3, 4, -3.0, 4, "Horizon")
    draw_arrow(ax, -4.9, 1.5, -3.0, 1.5, "Load .joblib")
    draw_arrow(ax, -2, 3.55, -2, 1.95, "Loaded Model")
    draw_arrow(ax, -4.9, -1, -3.0, 1.2, "Historical Data")
    draw_arrow(ax, -1.0, 1.5, 1.0, 1.5, "Exog Array")
    draw_arrow(ax, 2, 1.05, 2, -0.55, "kWh + 95% CI")
    draw_arrow(ax, 3.0, 1.5, 5.0, 1.5, "Forecast Docs")
    draw_arrow(ax, 2, -1.45, 2, -3.05, "ForecastMonth[]")
    draw_arrow(ax, 5.0, -3.5, 3.0, -3.5, "Thresholds")
    draw_arrow(ax, 1.0, -3.8, -5.3, 3.7, "Forecast +\nWarnings")

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=CLR_ENTITY, edgecolor="#2C6FAC", label='External Entity'),
        mpatches.Patch(facecolor=CLR_PROCESS, edgecolor="#4A9E4D", label='Process'),
        mpatches.Patch(facecolor="#FFF3E0", edgecolor="#D4780A", label='Data Store'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "DFD_Level2_Forecasting.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Generated: {path}")


# ==========================================================================
# LEVEL 2: RAG Chat
# ==========================================================================
def generate_level2_rag():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    setup_ax(fig, ax, "WATT-IF — Level 2 DFD: Process 6.0 (RAG Chat)",
             xlim=(-7, 7), ylim=(-5, 5))

    # External entities
    draw_entity(ax, -6, 4, "User", w=1.4, h=0.6)
    draw_entity(ax, 6, 0, "Ollama LLM", w=1.8, h=0.7)

    # Processes
    draw_process(ax, -2, 4, "6.1\nScope\nCheck", w=2.0, h=0.9)
    draw_process(ax, -2, 1.5, "6.2\nRetrieve\nContext", w=2.0, h=0.9)
    draw_process(ax, 2, 1.5, "6.3\nBuild\nPrompt", w=2.0, h=0.9)
    draw_process(ax, 2, -2, "6.4\nStream LLM\nResponse", w=2.0, h=0.9)

    # Data stores
    draw_store(ax, -6, -1, "D5 Vector Store", w=2.0, h=0.5)
    draw_store(ax, -6, -3, "EDA Store", w=2.0, h=0.5)
    draw_store(ax, 6, -4, "D3 Chat History", w=2.0, h=0.5)

    # Arrows
    draw_arrow(ax, -5.3, 4, -3.0, 4, "Question")
    draw_arrow(ax, -2, 3.55, -2, 1.95, "In-scope Q")
    draw_arrow(ax, -3.0, 1.3, -5.0, -0.8, "Query")
    draw_arrow(ax, -5.0, -1.2, -3.0, 1.2, "Top-12 Docs")
    draw_arrow(ax, -3.0, 1.1, -5.0, -2.8, "EDA Query")
    draw_arrow(ax, -5.0, -3.2, -3.0, 1.0, "EDA Docs", curved=True)
    draw_arrow(ax, -1.0, 1.5, 1.0, 1.5, "Context + Q")
    draw_arrow(ax, 2, 1.05, 2, -1.55, "Messages")
    draw_arrow(ax, 3.0, -1.8, 5.1, -0.2, "Prompt Payload")
    draw_arrow(ax, 5.1, 0.2, 3.0, -1.6, "Token Stream", curved=True)
    draw_arrow(ax, 1.0, -2.3, -5.3, 3.7, "SSE Events")
    draw_arrow(ax, 3.0, -2.3, 5.0, -3.8, "Persist Messages")
    # Out of scope response
    draw_arrow(ax, -1.0, 4.2, -5.3, 4.2, "Out-of-scope\nResponse", curved=True)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=CLR_ENTITY, edgecolor="#2C6FAC", label='External Entity'),
        mpatches.Patch(facecolor=CLR_PROCESS, edgecolor="#4A9E4D", label='Process'),
        mpatches.Patch(facecolor="#FFF3E0", edgecolor="#D4780A", label='Data Store'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "DFD_Level2_RAGChat.png")
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Generated: {path}")


# ==========================================================================
# Main
# ==========================================================================
if __name__ == "__main__":
    print("Generating WATT-IF DFD diagrams...")
    generate_level0()
    generate_level1()
    generate_level2_ingestion()
    generate_level2_forecasting()
    generate_level2_rag()
    print("\nAll DFD diagrams generated successfully!")
