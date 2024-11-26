
import pandas as pd
from sodapy import Socrata
import streamlit as st

# Function to fetch data for multiple DOT numbers
@st.cache_data
def fetch_data(dot_numbers):
    # Create the Socrata client
    client = Socrata("data.transportation.gov", None)
    
    # Prepare a list to store all results
    all_results = []

    # Fetch data for each DOT number
    for dot_number in dot_numbers:
        results = client.get(
            "az4n-8mr2",
            select="dot_number, phy_state, power_units",
            where=f"dot_number='{dot_number}'",
            limit=1
        )
        all_results.extend(results)
    
    # Convert the results to a pandas DataFrame
    return pd.DataFrame.from_records(all_results)

# Streamlit UI
st.title("DOT Number Power Units Discrepancy Checker")

# Input: DOT numbers and power units
user_input = st.text_area(
    "Enter DOT numbers and their respective power units (comma-separated, one per line):\n"
    "Example:\n123456, 10\n654321, 20\n987654, 15"
)

if st.button("Check Discrepancies"):
    if user_input:
        # Parse user input into a DataFrame
        input_data = []
        for line in user_input.strip().split("\n"):
            parts = line.split(",")
            if len(parts) == 2:
                input_data.append({
                    "dot_number": parts[0].strip(),
                    "original_power_units": int(parts[1].strip())
                })

        input_df = pd.DataFrame(input_data)

        # Fetch data from the API for the given DOT numbers
        try:
            queried_df = fetch_data(input_df["dot_number"].tolist())

            if not queried_df.empty:
                # Merge input data with queried data
                merged_df = input_df.merge(
                    queried_df, 
                    on="dot_number", 
                    how="left", 
                    suffixes=("_input", "_queried")
                )

                # Calculate discrepancies
                merged_df["difference"] = (
                    merged_df["original_power_units"] - merged_df["power_units"].astype(float)
                )

                # Filter out rows with 0 difference
                discrepancies_df = merged_df[merged_df["difference"] != 0]

                # Display results
                if not discrepancies_df.empty:
                    st.write("Discrepancy Results:")
                    st.write(
                        discrepancies_df[["dot_number", "original_power_units", "power_units", "difference"]]
                    )
                else:
                    st.success("No discrepancies found!")
            else:
                st.error("No data found for the entered DOT numbers.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please enter DOT numbers and their respective power units.")
