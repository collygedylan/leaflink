import streamlit as st
import pandas as pd
import base64
import os
import streamlit.components.v1 as components
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTINGS ---
st.set_page_config(page_title="GNC | LeafLink", layout="wide", initial_sidebar_state="expanded")

# --- 2. AUTO-CLOSE SIDEBAR LOGIC ---
if 'close_sidebar' not in st.session_state:
    st.session_state.close_sidebar = False

if st.session_state.close_sidebar:
    components.html(
        """
        <script>
            var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                var button = sidebar.querySelector('button');
                if (button) { button.click(); }
            }
        </script>
        """,
        height=0, width=0
    )
    st.session_state.close_sidebar = False

# --- 3. HELPER FUNCTIONS ---
def get_base64_leaf():
    return None 

leaf_b64 = get_base64_leaf()

# --- 4. DATA LOADER ---
@st.cache_data(ttl=10)
def load_gnc_data():
    try:
        # 👇👇👇 YOUR NEW LINK IS HERE 👇👇👇
        sheet_url = "https://docs.google.com/spreadsheets/d/1FNuWtLD6okE7tOxD3dRcUXVWL9bwwSye1nhGSVDiiTs"

        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # READ DATA
        # ⚠️ IMPORTANT: Ensure your new sheet has a tab named exactly 'Inventory_Drive_Around'
        df = conn.read(spreadsheet=sheet_url, worksheet='Inventory_Drive_Around')
        
        # Clean Columns
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Ensure required columns exist
        new_cols = ['LOC_SALESNOTE', 'CALIPER', 'SPEC', 'LOC_COMMENTS', 'MATCH_PCT', 'PIC_NOTE', 'PRIME_QTY', 'PHOTO', 'STATUS', 'ITEMCODE']
        for col in new_cols:
            if col not in df.columns:
                df[col] = ""
        
        df = df.fillna("").astype(str)

        # READ NOTES
        sales_notes_map = {}
        try:
            # ⚠️ IMPORTANT: Ensure your new sheet has a tab named 'S1_SalesNotes'
            notes_df = conn.read(spreadsheet=sheet_url, worksheet='S1_SalesNotes')
            notes_df.columns = [str(c).strip().upper() for c in notes_df.columns]
            
            if 'ITEMCODE' in notes_df.columns:
                note_col = next((c for c in notes_df.columns if 'NOTE' in c), None)
                if not note_col:
                    cols = [c for c in notes_df.columns if c != 'ITEMCODE']
                    if cols: note_col = cols[0]
                
                if note_col:
                    sales_notes_map = notes_df.groupby('ITEMCODE')[note_col].apply(lambda x: list(x.dropna().astype(str))).to_dict()
        except: 
            pass 

        return df, sales_notes_map

    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None, {}

# --- 5. CSS STYLING ---
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: #0A0A0A !important; border-right: 2px solid #333 !important; }}
    div[data-testid="stTextInput"] > div > div > input,
    div[data-testid="stSelectbox"] > div > div > div {{
        background-color: #1E1E1E !important; color: #E0E0E0 !important; border: 1px solid #444 !important; 
        border-radius: 8px !important; height: 50px !important;
    }}
    div.stButton > button {{
        background-color: #2D2D2D !important; color: #FFFFFF !important; border: 1px solid #444 !important;
        border-radius: 8px !important; height: 50px !important; font-weight: 600 !important; width: 100% !important;
    }}
    div.stButton > button:hover {{ border-color: #006847 !important; color: #006847 !important; }}
    div.stButton > button[kind="primary"] {{ background-color: #006847 !important; color: #FFFFFF !important; border: none !important; }}
    h1, h2, h3 {{ color: #006847 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = 'DRIVEAROUND'
if 'step' not in st.session_state: st.session_state.step = 'variety'
if 'task_step' not in st.session_state: st.session_state.task_step = 'block'
if 'active_seasons' not in st.session_state: st.session_state.active_seasons = set()
if 'user_name' not in st.session_state: st.session_state.user_name = "DYLAN"
if 'sales_stage' not in st.session_state: st.session_state.sales_stage = 'select_member'
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'pending'

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>GNC</h2>", unsafe_allow_html=True)
    nav_pages = ["OVERVIEW", "DRIVEAROUND", "MYTASKS", "SALESTEAM", "INVENTORYTEAM", "SOC", "SALESINVTRACKING", "WEATHER", "CONTACT"]
    for p in nav_pages:
        if st.button(p, key=f"nav_{p}"):
            st.session_state.page = p
            st.session_state.step = 'variety'
            st.session_state.task_step = 'block'
            st.session_state.sales_stage = 'select_member'
            st.session_state.close_sidebar = True
            st.rerun()

# --- 8. MAIN WORKSPACE ---
df, sales_notes_map = load_gnc_data()

with st.container():
    if df is None:
        st.info("Waiting for connection... (If this persists, check Secrets)")
    else:
        # --- SALES TEAM ---
        if st.session_state.page == "SALESTEAM":
            if st.session_state.sales_stage == 'select_member':
                st.markdown("## SALES TEAM")
                cols = st.columns(2)
                team = ["Dylan", "Zoe", "Morgan", "Kayla"]
                for i, member in enumerate(team):
                    with cols[i % 2]:
                        if st.button(member, key=f"team_{member}"):
                            st.session_state.user_name = member.upper()
                            st.session_state.sales_stage = 'select_status'; st.rerun()

            elif st.session_state.sales_stage == 'select_status':
                st.markdown(f"## {st.session_state.user_name}")
                if st.button("PENDING TASKS"):
                    st.session_state.page = "MYTASKS"; st.session_state.view_mode = "pending"; st.session_state.task_step = 'block'; st.rerun()
                if st.button("COMPLETED TASKS"):
                    st.session_state.page = "MYTASKS"; st.session_state.view_mode = "complete"; st.session_state.task_step = 'block'; st.rerun()
                st.markdown("---")
                if st.button("⬅️ BACK"): st.session_state.sales_stage = 'select_member'; st.rerun()

        # --- MYTASKS (DATA ENTRY) ---
        elif st.session_state.page == "MYTASKS":
            mode_label = " (COMPLETED)" if st.session_state.view_mode == "complete" else " (PENDING)"
            st.markdown(f"## TASK: {st.session_state.user_name}{mode_label}")
            
            dylan_heavy = ["#7", "#10", "#15", "#25", "#45", "7DP"]
            if st.session_state.user_name == "DYLAN":
                my_data = df[(df['CONTSIZE'].isin(dylan_heavy)) | (df['SALES_ASSIGNEDTO'].str.upper() == "DYLAN")]
            else:
                my_data = df[df['SALES_ASSIGNEDTO'].str.upper() == st.session_state.user_name]

            if st.session_state.view_mode == "complete":
                my_data = my_data[my_data['STATUS'] == 'COMPLETE']
            else:
                my_data = my_data[my_data['STATUS'] != 'COMPLETE']

            if my_data.empty:
                st.info(f"No {st.session_state.view_mode} tasks found.")
            else:
                if st.session_state.task_step == 'block':
                    st.markdown("### SELECT BLOCK")
                    blocks = my_data.groupby('BLOCKALPHA').size().reset_index(name='counts')
                    for _, row in blocks.iterrows():
                        label = f"{row['BLOCKALPHA']} ({row['counts']})"
                        if st.button(label, key=f"blk_{row['BLOCKALPHA']}"):
                            st.session_state.sel_block = row['BLOCKALPHA']; st.session_state.task_step = 'location'; st.rerun()

                elif st.session_state.task_step == 'location':
                    if st.button("⬅️ BACK"): st.session_state.task_step = 'block'; st.rerun()
                    st.markdown(f"### BLOCK: {st.session_state.sel_block}")
                    loc_data = my_data[my_data['BLOCKALPHA'] == st.session_state.sel_block]
                    locs = loc_data.groupby('LOCATIONCODE').size().reset_index(name='counts')
                    for _, row in locs.iterrows():
                        label = f"{row['LOCATIONCODE']} ({row['counts']})"
                        if st.button(label, key=f"loc_{row['LOCATIONCODE']}"):
                            st.session_state.sel_loc = row['LOCATIONCODE']; st.session_state.task_step = 'details'; st.rerun()

                # --- DETAIL STACK (Where Saving Happens) ---
                elif st.session_state.task_step == 'details':
                    if st.button("⬅️ BACK"): st.session_state.task_step = 'location'; st.rerun()
                    st.markdown(f"### {st.session_state.sel_block} - {st.session_state.sel_loc}")
                    
                    final = my_data[(my_data['BLOCKALPHA'] == st.session_state.sel_block) & 
                                    (my_data['LOCATIONCODE'] == st.session_state.sel_loc)]
                    
                    for idx, row in final.iterrows():
                        uid = f"{row['BLOCKALPHA']}_{row['LOCATIONCODE']}_{idx}"
                        item_code = str(row.get('ITEMCODE', '')).strip()
                        
                        with st.expander(f"{row.get('COMMONNAME')} | {row.get('CONTSIZE')}", expanded=False):
                            
                            st.markdown("##### 📸 PHOTO (Disabled in Cloud Mode)")
                            
                            st.markdown("---")

                            c1, c2 = st.columns(2)
                            with c1:
                                caliper = st.text_input("CALIPER", value=str(row.get('CALIPER','')), key=f"cal_{uid}")
                            with c2:
                                spec = st.text_input("SPEC", value=str(row.get('SPEC','')), key=f"spec_{uid}")
                            
                            c3, c4 = st.columns(2)
                            with c3:
                                match_options = [str(i) for i in range(0, 105, 5)]
                                current_match = str(row.get('MATCH_PCT', '')).strip()
                                if current_match and current_match not in match_options:
                                    match_options = [current_match] + match_options
                                match_index = match_options.index(current_match) if current_match in match_options else 0
                                match_pct = st.selectbox("MATCH %", options=match_options, index=match_index, key=f"match_{uid}")
                            with c4:
                                prime_qty = st.text_input("PRIME QTY", value=str(row.get('PRIME_QTY','')), key=f"prime_{uid}")
                            
                            current_note = str(row.get('LOC_SALESNOTE', '')).strip()
                            note_options = sales_notes_map.get(item_code, [])
                            options = [""] + note_options
                            if current_note and current_note not in options:
                                options.append(current_note)
                            
                            loc_note = st.selectbox("LOC SALES NOTE", options=options, index=options.index(current_note) if current_note in options else 0, key=f"lnote_{uid}")
                            
                            comments = st.text_input("LOC COMMENTS", value=str(row.get('LOC_COMMENTS','')), key=f"cmts_{uid}")
                            pic_note = st.text_input("PIC NOTE", value=str(row.get('PIC_NOTE','')), key=f"pnote_{uid}")
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # --- MODIFIED: WRITE BACK TO GOOGLE SHEETS ---
                            if st.button("MARK COMPLETE", key=f"done_{uid}", type="primary"):
                                try:
                                    # 1. Update the in-memory dataframe
                                    df.at[idx, 'STATUS'] = 'COMPLETE'
                                    df.at[idx, 'CALIPER'] = caliper
                                    df.at[idx, 'SPEC'] = spec
                                    df.at[idx, 'MATCH_PCT'] = match_pct
                                    df.at[idx, 'PRIME_QTY'] = prime_qty
                                    df.at[idx, 'LOC_SALESNOTE'] = loc_note
                                    df.at[idx, 'LOC_COMMENTS'] = comments
                                    df.at[idx, 'PIC_NOTE'] = pic_note

                                    # 2. Write to Google Sheets
                                    conn = st.connection("gsheets", type=GSheetsConnection)
                                    conn.update(worksheet='Inventory_Drive_Around', data=df)
                                    
                                    st.success("✅ SAVED TO GOOGLE SHEETS!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to save: {e}")

        # --- DRIVE AROUND ---
        elif st.session_state.page == "DRIVEAROUND":
            st.markdown("## DRIVE AROUND")
            st.markdown("### 🗓️ FILTERS")
            for row_labels in [["ALL", "F1", "S1", "U1", "U2"], ["U3", "X", "Y", "Z", "CLEAR"]]:
                cols = st.columns(5)
                for i, s in enumerate(row_labels):
                    with cols[i]:
                        if st.button(s, key=f"btn_{s}", use_container_width=True):
                            if s == "ALL" or s == "CLEAR": st.session_state.active_seasons = set()
                            else:
                                if s in st.session_state.active_seasons: st.session_state.active_seasons.remove(s)
                                else: st.session_state.active_seasons.add(s)
                            st.rerun()

            f_df = df.copy()
            if st.session_state.active_seasons:
                f_df = f_df[f_df['SEASON'].isin(st.session_state.active_seasons)]

            if st.session_state.step == 'variety':
                st.markdown("<hr>", unsafe_allow_html=True)
                search = st.text_input("SEARCH VARIETY:", placeholder="Type name...")
                names = sorted([n for n in f_df['COMMONNAME'].unique() if n.strip()])
                filtered = [n for n in names if search.lower() in n.lower()]
                
                for n in filtered:
                    if st.button(n, key=f"var_{n}"):
                        st.session_state.sel_variety = n; st.session_state.step = 'size'; st.rerun()
            
            elif st.session_state.step == 'size':
                if st.button("⬅️ BACK"): st.session_state.step = 'variety'; st.rerun()
                st.markdown(f"### {st.session_state.sel_variety}")
                v_data = f_df[f_df['COMMONNAME'] == st.session_state.sel_variety]
                sizes = sorted(v_data['CONTSIZE'].unique())
                for s in sizes:
                    if st.button(f"SIZE: {s}", key=f"sz_{s}"):
                        st.session_state.sel_size = s; st.session_state.step = 'data'; st.rerun()

            elif st.session_state.step == 'data':
                if st.button("⬅️ BACK"): st.session_state.step = 'size'; st.rerun()
                final = f_df[(f_df['COMMONNAME'] == st.session_state.sel_variety) & (f_df['CONTSIZE'] == st.session_state.sel_size)]
                for _, row in final.iterrows():
                    header = f"{row.get('COMMONNAME')} / {row.get('CONTSIZE')} / {row.get('LOCATIONCODE')}"
                    with st.expander(header):
                        for c, v in row.items(): st.write(f"**{c}:** {v}")

        elif st.session_state.page == "WEATHER":
            components.html('<div style="background-color: white; padding: 10px; border: 2px solid #006847; border-radius: 12px; font-family: sans-serif; text-align: center;"><h1 style="color: #006847; margin: 0; font-size: 1.1rem;">46°F</h1><p style="color: #006847; font-weight: bold; font-size: 0.8rem;">Park Hill, OK</p></div>', height=70)
