import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import json


st.set_page_config(page_title="NBA Player Stats Explorer", layout="wide")  # 👈 FIRST Streamlit call



genai.configure(api_key="AIzaSyCJZsrkF9CjwhDHtqdcIOKr902ozpnAzA8")


model = genai.GenerativeModel("gemini-2.0-flash")


@st.cache_data
def load_data():
    return pd.read_csv("all_seasons.csv")

df = load_data()

st.title("🏀 NBA Player Stats Explorer")


question = st.text_input("Pose une question :")


data = df.head(50).to_string(index=False)

if st.button("Demander au coach"):
    prompt = f"""Tu es un coach de basket qui a toutes les informations des match nba entre 1996 et 2022 :

{json.dumps(data)}

Réponds de manière concise, claire et pédagogique à la question suivante :

{question}
"""
    with st.spinner("Le coach réfléchit..."):
        response = model.generate_content(prompt)
        st.markdown(f"{response.text}")



# Sidebar
st.sidebar.header("🔍 Search Player")
search_query = st.sidebar.text_input("Enter player name:")

st.sidebar.markdown("---")
st.sidebar.header("📂 Filters")
teams = sorted(df['team_abbreviation'].dropna().unique())
seasons = sorted(df['season'].dropna().unique(), reverse=True)

selected_team = st.sidebar.selectbox("Filter by team:", ["All"] + teams)
selected_season = st.sidebar.selectbox("Filter by season:", ["All"] + seasons)

# Filtering
if search_query:
    filtered = df[df['player_name'].str.contains(search_query, case=False, na=False)]

    if selected_team != "All":
        filtered = filtered[filtered['team_abbreviation'] == selected_team]

    if selected_season != "All":
        filtered = filtered[filtered['season'] == selected_season]

    unique_players = filtered['player_name'].unique()

    st.sidebar.markdown("### 👤 Matching Players")
    if len(unique_players) > 0:
        selected_player = st.sidebar.radio("Click a player:", unique_players)

        # Player view
        player_df = df[df['player_name'] == selected_player]
        st.header(f"📊 {selected_player} – Stats Dashboard")

        # === Player Profile ===
        latest = player_df.sort_values(by="season", ascending=False).iloc[0]
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            ### 🧾 Player Profile
            - **Team:** {latest['team_abbreviation']}
            - **Position:** {latest.get('player_position', 'N/A')}
            - **College:** {latest.get('college', 'N/A')}
            - **Draft Year:** {latest.get('draft_year', 'N/A')}
            - **Height:** {latest.get('height', 'N/A')}
            - **Weight:** {latest.get('weight', 'N/A')} lbs
            """)
        with col2:
            st.download_button(
                label="⬇️ Download Player Data (CSV)",
                data=player_df.to_csv(index=False),
                file_name=f"{selected_player.replace(' ', '_')}_stats.csv",
                mime="text/csv"
            )

        # === Career Stats Table ===
        st.markdown("### 📋 Full Stats by Season")
        st.dataframe(player_df.sort_values(by="season", ascending=False).reset_index(drop=True))

        # === Career Averages ===
        st.markdown("### 🧮 Career Averages")
        career_avg = player_df.select_dtypes(include='number').mean(numeric_only=True).round(2)
        st.dataframe(career_avg.to_frame("Average").T)

        # === Best Scoring Season ===
        if "pts" in player_df.columns:
            best_season = player_df.loc[player_df['pts'].idxmax()]
            st.success(f"🔥 Best scoring season: **{best_season['season']}** with **{best_season['pts']} PPG**")

        # === Line Chart ===
        st.markdown("### 📈 Performance Over Seasons")
        potential_cols = ["pts", "ast", "reb", "gp", "stl", "blk", "min"]
        existing_cols = [col for col in potential_cols if col in player_df.columns]

        if existing_cols:
            melted = player_df[["season"] + existing_cols].melt("season", var_name="Stat", value_name="Value")
            chart = alt.Chart(melted).mark_line(point=True).encode(
                x='season:N',
                y='Value:Q',
                color='Stat:N',
                tooltip=['season:N', 'Stat:N', 'Value:Q']
            ).properties(
                width=800,
                height=400
            ).interactive()
            st.altair_chart(chart)
        else:
            st.info("No numeric stats available for chart.")

        # === Bar Chart Comparison ===
        st.markdown("### 📊 Bar Chart: PTS vs REB vs AST")
        stat_cols = ["pts", "reb", "ast"]
        stat_cols = [col for col in stat_cols if col in player_df.columns]
        if stat_cols:
            bar_df = player_df[["season"] + stat_cols].set_index("season")
            st.bar_chart(bar_df)
    else:
        st.warning("No players matched your search and filters.")
else:
    st.info("Use the search bar to find a player.")
