import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Work Hours Calculator", layout="centered")

st.title("User Work Hours Calculator")

# --- NEW: Expected hours input ---
expected_monthly_hours = st.number_input(
    "Expected working hours for this month",
    min_value=0.0,
    step=1.0
)

uploaded_file = st.file_uploader("Upload XLSX file", type=["xlsx"])


def calculate_daily_work_hours(df):
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    required_cols = {"timestamp", "user", "check-in / check-out"}
    if not required_cols.issubset(df.columns):
        raise ValueError("Missing required columns in the uploaded file.")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    df = df.sort_values("timestamp").reset_index(drop=True)

    daily_seconds = {}
    last_check_in = None
    last_date = None

    for _, row in df.iterrows():
        action = row["check-in / check-out"].strip().lower()
        ts = row["timestamp"]
        current_date = row["date"]

        if action == "check-in":
            last_check_in = ts
            last_date = current_date

        elif action == "check-out" and last_check_in is not None:
            if current_date == last_date:
                duration = (ts - last_check_in).total_seconds()
                if duration > 0:
                    daily_seconds[current_date] = daily_seconds.get(current_date, 0) + duration
            last_check_in = None
            last_date = None

    daily_hours_df = (
        pd.DataFrame(
            [
                {"Date": d, "Hours Worked": round(sec / 3600, 2)}
                for d, sec in daily_seconds.items()
            ]
        )
        .sort_values("Date")
        .reset_index(drop=True)
    )

    total_hours = round(daily_hours_df["Hours Worked"].sum(), 2)
    user_name = df["user"].iloc[0]

    return user_name, total_hours, daily_hours_df


if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        user, total_hours, daily_df = calculate_daily_work_hours(df)

        overtime = round(total_hours - expected_monthly_hours, 2)

        st.success("Calculation completed successfully")

        # --- Summary ---
        st.subheader("Summary")
        st.write(f"**User:** {user}")
        st.write(f"**Total Hours Worked:** {total_hours}")
        st.write(f"**Expected Monthly Hours:** {expected_monthly_hours}")

        if overtime > 0:
            st.write(f"🟢 **Overtime:** {overtime} hours")
        elif overtime < 0:
            st.write(f"🔴 **Undertime:** {abs(overtime)} hours")
        else:
            st.write("⚖️ **Exactly met expected hours**")

        # --- Daily breakdown ---
        st.subheader("Daily Work Hours")
        st.dataframe(daily_df)

        # --- Export XLSX ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            daily_df.to_excel(writer, index=False, sheet_name="Daily Hours")

        st.download_button(
            label="Download XLSX Result",
            data=output.getvalue(),
            file_name=f"{user}_daily_work_hours.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
