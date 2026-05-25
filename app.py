"""
app.py — Top 1000 meest gebruikte woorden in Nederlandse vacatures
Uruchomienie: streamlit run app.py
"""

import re
from collections import Counter

import pandas as pd
import streamlit as st


# ── Stop words ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_stopwords():
    return {
        "de", "en", "van", "een", "het", "in", "is", "dat", "op", "te",
        "voor", "met", "zijn", "er", "maar", "om", "aan", "ook", "als",
        "bij", "dan", "of", "uit", "door", "naar", "die", "dit", "niet",
        "ze", "we", "je", "hij", "zij", "ik", "u", "uw", "hun",
        "hen", "onze", "ons", "mijn", "jouw", "haar", "heeft",
        "hebben", "wordt", "worden", "was", "waren", "kan", "kunnen",
        "zal", "zullen", "moet", "moeten", "mogen", "wil", "willen",
        "meer", "zo", "nog", "al", "wel", "geen", "wat", "wie", "hoe",
        "waar", "wanneer", "waarom", "omdat", "want", "dus", "toch",
        "via", "per", "tot", "over", "onder", "tussen", "binnen", "buiten",
        "the", "and", "or", "for", "with", "you", "your", "will", "have",
        "this", "that", "are", "from", "our", "its", "been", "has",
        "were", "they", "their", "which", "who", "all", "can", "not",
        "jij", "mee", "toe", "ben", "erg", "elk", "elke",
        "ander", "andere", "beiden", "veel", "weinig", "reeds", "deze",
        "hem", "men", "iets", "niets", "alles", "ieder", "iedere", "wij", "jou", "bent"
    }


# ── Word frequency ───────────────────────────────────────────────────────────
@st.cache_data
def compute_word_freq(df: pd.DataFrame) -> pd.DataFrame:
    try:
        result = pd.read_csv("words_nl_translated-5.csv")
        stops = load_stopwords()
        result = result[~result["Woord"].isin(stops)].head(1000)
        result = result.reset_index(drop=True)
        result.index = result.index + 1
        return result
    except FileNotFoundError:
        pass
    all_text = " ".join(df["Job Description"].dropna()).lower()
    tokens = re.findall(r"\b[a-zàáâãäåæçèéêëìíîïðñòóôõöùúûüý]{3,}\b", all_text)
    stops = load_stopwords()
    tokens = [t for t in tokens if t not in stops]
    freq = Counter(tokens).most_common(10000)
    result = pd.DataFrame(freq, columns=["Woord", "Frequentie"])
    result.index = result.index + 1
    return result


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🇳🇱 Top 1000 Nederlandse Woorden",
    page_icon="🇳🇱",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🇳🇱 Top 1000 woorden in Nederlandse vacatures")

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("jobs_nl.csv")
    df["date_posted"] = pd.to_datetime(df["date_posted"]).dt.strftime("%Y-%m-%d")
    df.columns = [col.replace("_", " ").title() for col in df.columns]
    return df


try:
    df_jobs = load_data()
except FileNotFoundError:
    st.error("Bestand 'jobs_nl.csv' niet gevonden. Zet het in dezelfde map als app.py.")
    st.stop()

st.markdown(
    f"Analyse van **{len(df_jobs):,}** vacatureteksten van de Nederlandse arbeidsmarkt. "
    "Bekijk de meest gebruikte woorden!"
)

freq_df = compute_word_freq(df_jobs)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filters")
    top_n    = st.slider("Aantal woorden", 10, 1000, 100, step=10)
    min_freq = st.number_input("Min. frequentie", min_value=1, value=3)
    weergave = st.radio("Weergave", ["📊 Tabel", "📈 Grafiek"])
    st.divider()
    zoek = st.text_input("🔍 Zoek woord", placeholder="bijv. ervaring")
    st.divider()
    show_translation = st.toggle("🇬🇧 Toon Engelse vertaling", value=True)
    st.divider()
    st.caption(f"Bron: JSearch API\n{len(df_jobs)} vacatures · NL filter")

# ── Filter ───────────────────────────────────────────────────────────────────
filtered = freq_df.head(top_n)
filtered = filtered[filtered["Frequentie"] >= int(min_freq)]

if zoek:
    filtered = freq_df[freq_df["Woord"].str.contains(zoek.lower(), na=False)]
    st.info(f"Zoekresultaten voor **'{zoek}'**: {len(filtered)} woorden gevonden")

# ── Kolommen op basis van toggle ─────────────────────────────────────────────
if show_translation and "Translation" in freq_df.columns:
    cols = ["Woord", "Translation", "Frequentie"]
else:
    cols = ["Woord", "Frequentie"]

# ── Metrics ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #666; }
[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #1a1a2e; }
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏢 Vacatures", f"{len(df_jobs):,}")
c2.metric("📚 Unieke woorden", f"{len(freq_df):,}")
c3.metric("🏆 Meest voorkomend", freq_df.iloc[0]["Woord"])
c4.metric("🔢 Frequentie #1", f"{freq_df.iloc[0]['Frequentie']:,}×")

st.divider()

# ── View ─────────────────────────────────────────────────────────────────────
if weergave == "📊 Tabel":
    st.subheader(f"Top {len(filtered)} woorden")
    st.dataframe(
        filtered[cols],
        use_container_width=True,
        height=600,
        column_config={
            "Woord": st.column_config.TextColumn("Woord 🇳🇱", width="medium"),
            "Translation": st.column_config.TextColumn("English 🇬🇧", width="medium"),
            "Frequentie": st.column_config.ProgressColumn(
                "Frequentie",
                min_value=0,
                max_value=int(freq_df["Frequentie"].max()),
                format="%d",
            ),
        },
    )
    with st.expander("📋 Brondata — bekijk alle vacatures"):
        st.dataframe(
            df_jobs[["Job Title", "Employer Name", "Job City", "Date Posted", "Job Description"]],
            use_container_width=True,
            height=400,
        )

else:
    top_chart = st.slider("Top N voor grafiek", 10, 50, 25)
    chart_data = filtered.head(top_chart).set_index("Woord")["Frequentie"]
    st.subheader(f"Top {top_chart} meest gebruikte woorden")
    st.bar_chart(chart_data, height=450)
    with st.expander("📋 Brondata — bekijk alle vacatures"):
        st.dataframe(
            df_jobs[["Job Title", "Employer Name", "Job City", "Date Posted", "Job Description"]],
            use_container_width=True,
            height=400,
        )

st.divider()
st.caption("Powered by JSearch API.")