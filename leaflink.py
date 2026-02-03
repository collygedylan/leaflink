import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide")
st.title("🤖 Bot Diagnostic Tool")

# 1. READ THE SECRET EMAIL
try:
    # This reads the email directly from your secrets file
    bot_email = st.secrets["connections"]["gsheets"]["service_account_info"]["client_email"]
    
    st.success("✅ Secrets Loaded Successfully!")
    st.markdown("### 1. COPY THIS EMAIL ADDRESS:")
    st.code(bot_email, language="text")
    st.info("👆 Copy the address above. Go to your Google Sheet > Share > Paste this email as Editor.")

except Exception as e:
    st.error(f"❌ Error reading secrets: {e}")
    st.stop()

# 2. TEST THE CONNECTION
st.markdown("### 2. CONNECTION TEST")
if st.button("I have added the email. Test Connection Now!", type="primary"):
    try:
        # The clean URL (No /edit, no gid junk)
        url = "https://docs.google.com/spreadsheets/d/1ffMWw09rxPSZOsn83PUX0uynqdX9xANUlaMk2TIvbbs"
        
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet='Inventory_Drive_Around')
        
        st.balloons()
        st.success("🎉 SUCCESS! The bot can read the file!")
        st.write(f"Found {len(df)} rows of data.")
        st.dataframe(df.head())
        
    except Exception as e:
        st.error("⛔ STILL FAILING.")
        st.error(f"Error Details: {e}")
        st.markdown("**Check these things:**")
        st.markdown("1. Did you paste the **exact** email from above?")
        st.markdown("2. Is the tab in your sheet named **exactly** `Inventory_Drive_Around`?")
