import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Work Hours Calculator", layout="centered")

st.title("User Work Hours Calculator")
st.write("Upload a user's XLSX file containing check-in / check-out records.")

uploaded_file = st.file_uploader("Upload XLSX file", type=["xlsx"])

def calculate_work_hours(df):
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Required columns check
    required_cols = {"timestamp", "user", "check-in / check-out"}
    if not required_cols.issubset(df.columns):
        raise ValueError("Missing required columns in the uploaded file.")

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Sort chronologically
    df = df.sort_values("timestamp").reset_index(drop=True)

    total_seconds = 0
    last_check_in = None

    for _, row in df.iterrows():
        action = row["check-in / check-out"].strip().lower()
        ts = row["timestamp"]

        if action == "check-in":
            last_check_in = ts

        elif action == "check-out" and last_check_in is not None:
            duration = (ts - last_check_in).total_seconds()
            if duration > 0:
                total_seconds += duration
            last_check_in = None

    total_hours = round(total_seconds / 3600, 2)
    user_name = df["user"].iloc[0]

    return user_name, total_hours

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        user, hours = calculate_work_hours(df)

        result_df = pd.DataFrame({
            "User": [user],
            "Total Hours Worked": [hours]
        })

        st.success("Calculation completed successfully")
        st.dataframe(result_df)

        # Export to XLSX
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Summary")

        st.download_button(
            label="Download XLSX Result",
            data=output.getvalue(),
            file_name=f"{user}_work_hours.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
