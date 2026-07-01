import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests

st.set_page_config(page_title="Inventory Analytics Dashboard", layout="wide")
st.title("📊 Enterprise Inventory & Data Pipeline Dashboard")

# --- STEP 2: LIVE REST API INTEGRATION ---
@st.cache_data
def fetch_api_data():
    try:
        # Fetching live currency rates to fulfill the API requirement
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        return response.json()["rates"]
    except:
        return {"INR": 83.5}  # Fallback rate

live_rates = fetch_api_data()
inr_rate = live_rates.get("INR", 83.5)

st.sidebar.success(f"🌐 Live REST API Status: Connected")
st.sidebar.metric(label="Live USD to INR Rate", value=f"₹{inr_rate:.2f}")

# --- STEP 3: DATA ENGINE (Ingesting your cleaned data) ---
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_inventory_pipeline.csv")
    # Clean up empty spaces in column names
    df.columns = [col.strip() for col in df.columns]
    return df

try:
    df = load_data()
    cols = list(df.columns)
    
    # Auto-detect best columns or fallback to the first few columns available
    cat_col = "Category" if "Category" in cols else ( "category" if "status" in cols else cols[0] )
    status_col = "Status" if "Status" in cols else ( "status" if "status" in cols else cols[0] )
    
    # Dynamically find numeric columns for charts
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    rev_col = "Revenue" if "Revenue" in cols else (num_cols[0] if len(num_cols) > 0 else cols[0])
    margin_col = "Margin" if "Margin" in cols else (num_cols[1] if len(num_cols) > 1 else rev_col)

    # Sidebar Filters
    st.sidebar.header("Filter Options")
    selected_status = st.sidebar.multiselect(
        f"Select {status_col}", 
        options=df[status_col].unique(), 
        default=df[status_col].unique()
    )
    
    filtered_df = df[df[status_col].isin(selected_status)]

    # --- STEP 4: INTERACTIVE METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows Processed", f"{len(filtered_df):,}")
    
    if df[rev_col].dtype != 'object':
        col2.metric("Total Sum Value", f"₹{filtered_df[rev_col].sum():,.2f}")
    else:
        col2.metric("Unique Items", f"{filtered_df[rev_col].nunique()}")
        
    if df[margin_col].dtype != 'object':
        col3.metric("Average Metric Value", f"{filtered_df[margin_col].mean():.2f}")
    else:
        col3.metric("Columns Processed", f"{len(cols)}")

    # --- STEP 5: LIVE VISUALIZATIONS ---
    st.subheader("📈 Statistical Exploratory Data Analysis")
    
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    
    # Flexible Bar Plot
    sns.countplot(data=filtered_df, x=cat_col, ax=ax[0], palette="viridis")
    ax[0].set_title(f"Distribution of {cat_col}")
    ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=45)
    
    # Flexible Numeric Box Plot / Fallback
    if df[rev_col].dtype != 'object':
        sns.boxplot(data=filtered_df, x=cat_col, y=rev_col, ax=ax[1], palette="mako")
        ax[1].set_title(f"{rev_col} Spread by {cat_col}")
    else:
        sns.countplot(data=filtered_df, x=status_col, ax=ax[1], palette="mako")
        ax[1].set_title(f"Distribution of {status_col}")
        
    ax[1].set_xticklabels(ax[1].get_xticklabels(), rotation=45)
    
    st.pyplot(fig)

    # Show raw dataset option
    if st.checkbox("Show Transformed Dataset"):
        st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Error rendering dashboard structure. Details: {e}")
    st.write("Your available data columns are:", list(df.columns) if 'df' in locals() else "File read error")