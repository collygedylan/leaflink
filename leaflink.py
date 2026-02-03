import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from concurrent.futures import ThreadPoolExecutor

# --- 1. SETTINGS & PAGE CONFIG ---
st.set_page_config(page_title="GNC | LeafLink", layout="wide", initial_sidebar_state="expanded")

# --- 2. ULTRA-MODERN DARK CSS ---
st.markdown(f"""
    <style>
    /* APP BACKGROUND */
    .stApp {{ background-color: #050505; }} /* Pitch black for high contrast */
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #333 !important; }}
    
    /* INPUT FIELDS - SLEEK & DARK */
    div[data-testid="stTextInput"] > div > div > input,
    div[data-testid="stSelectbox"] > div > div > div {{
        background-color: #1a1a1a !important; 
        color: #FFFFFF !important; 
        border: 1px solid #333 !important; 
        border-radius: 12px !important; 
        height: 55px !important;
        font-size: 16px !important;
    }}
    div[data-testid="stTextInput"] > div > div > input:focus {{
        border-color: #00D08E !important; /* Neon Green Focus */
    }}
    
    /* BUTTONS - HIGH END */
    div.stButton > button {{
        background-color: #1a1a1a !important; 
        color: #E0E0E0 !important; 
        border: 1px solid #333 !important;
        border-radius: 12px !important; 
        height: 55px !important; 
        font-weight: 700 !important; 
        width: 100% !important;
        transition: all 0.2s ease-in-out;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    div.stButton > button:hover {{ 
        border-color: #00D08E !important; 
        color: #00D08E !important; 
        box-shadow: 0 0 10px rgba(0, 208, 142, 0.2);
    }}
    div.stButton > button[kind="primary"] {{ 
        background: linear-gradient(135deg, #006847 0%, #004d35 100%) !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        box-shadow: 0 4px 15px rgba(0, 104, 71, 0.5);
    }}
    
    /* TEXT & HEADERS */
    h1, h2, h3 {{ color: #FFFFFF !important; font-weight: 800 !important; letter-spacing: -0.5px; }}
    p, label {{ color: #CCCCCC !important; font-weight: 500 !important; }}
    
    /* DASHBOARD CARD (The "HUD") */
    .hud-card {{
        background-color: #121212;
        border: 1px solid #333;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .hud-item {{
        text-align: center;
        padding: 0 15px;
    }}
    .hud-label {{
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }}
    .hud-value {{
        font-size: 1.4rem;
        font-weight: 900;
        color: #00D08E; /* NEON GREEN POP */
    }}
    .hud-title {{
        font-size: 1.8rem;
        font-weight: 900;
        color: #FFF;
        margin-bottom: 5px;
    }}
    .hud-subtitle {{
        font-size: 1rem;
        color: #AAA;
    }}
    
    /* LIST ITEM CARD */
    .list-card {{
        background-color: #121212;
        border-left: 4px solid #333;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        transition: border-color 0.2s;
        cursor: pointer;
    }}
    .list-card:hover {{
        border-left-color: #00D08E;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTO-CLOSE SIDEBAR LOGIC ---
if 'close_sidebar' not in st.session_state: st.session_state.close_sidebar = False
if st.session_state.close_sidebar:
    components.html("""<script>var s=window.parent.document.querySelector('[data-testid="stSidebar"]');if(s){var b=s.querySelector('button');if(b){b.click();}}</script>""", height=0, width=0)
    st.session_state.close_sidebar = False

# --- 4. HIGH-PERFORMANCE DATA LOADER ---
@st.cache_data(ttl=600)
def load_gnc_data():
    try:
        sheet_id = "1FNuWtLD6okE7tOxD3dRcUXVWL9bwwSye1nhGSVDiiTs"
        inv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Inventory_Drive_Around"
        notes_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=S1_SalesNotes"

        def fetch_csv(url):
            try: return pd.read_csv(url)
            except: return pd.DataFrame()

        with ThreadPoolExecutor() as executor:
            future_inv = executor.submit(fetch_csv, inv_url)
            future_notes = executor.submit(fetch_csv, notes_url)
            df = future_inv.result()
            notes_df = future_notes.result()

        if not df.empty:
            df.columns = df.columns.str.strip().str.upper()
            required_cols = ['LOC_SALESNOTE', 'CALIPER', 'SPEC', 'LOC_COMMENTS', 'MATCH_PCT', 'PIC_NOTE', 'PRIME_QTY', 'PHOTO', 'STATUS', 'ITEMCODE', 'SALES_ASSIGNEDTO', 'SEASON', 'COMMONNAME', 'CONTSIZE', 'BLOCKALPHA', 'LOCATIONCODE', 'LOTCODE', 'PRIORITY', 'CURRENT_SALESNOTE', 'PTRAVAILABLE', 'S_LTS']
            missing = [c for c in required_cols if c not in df.columns]
            if missing: df[pd.Index(missing)] = ""
            df = df.fillna("").astype(str)

        sales_notes_map = {}
        if not notes_df.empty:
            notes_df.columns = notes_df.columns.str.strip().str.upper()
            if 'ITEMCODE' in notes_df.columns:
                note_cols = [c for c in notes_df.columns if 'NOTE' in c]
                note_col = note_cols[0] if note_cols else (notes_df.columns[1] if len(notes_df.columns)>1 else None)
                if note_col: sales_notes_map = notes_df.groupby('ITEMCODE')[note_col].apply(lambda x: list(x.dropna().astype(str))).to_dict()

        return df, sales_notes_map
    except Exception as e:
        return pd.DataFrame(), {}

# --- 5. STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = 'DRIVEAROUND'
if 'step' not in st.session_state: st.session_state.step = 'variety'
if 'task_step' not in st.session_state: st.session_state.task_step = 'block'
if 'sel_item_idx' not in st.session_state: st.session_state.sel_item_idx = None
if 'active_seasons' not in st.session_state: st.session_state.active_seasons = set()
if 'user_name' not in st.session_state: st.session_state.user_name = "DYLAN"
if 'sales_stage' not in st.session_state: st.session_state.sales_stage = 'select_member'
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'pending'

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>GNC</h2>", unsafe_allow_html=True)
    if st.button("🔄 REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    nav_pages = ["OVERVIEW", "DRIVEAROUND", "MYTASKS", "SALESTEAM", "INVENTORYTEAM", "SOC", "SALESINVTRACKING", "WEATHER", "CONTACT"]
    for p in nav_pages:
        if st.button(p, key=f"nav_{p}"):
            st.session_state.page = p
            st.session_state.step = 'variety'
            st.session_state.task_step = 'block'
            st.session_state.sales_stage = 'select_member'
            st.session_state.close_sidebar = True
            st.rerun()

# --- 7. MAIN WORKSPACE ---
df, sales_notes_map = load_gnc_data()

with st.container():
    if df.empty:
        st.info("Waiting for data... (If stuck, hit Refresh)")
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
            dylan_heavy = ["#7", "#10", "#15", "#25", "#45", "7DP"]
            if st.session_state.user_name == "DYLAN":
                my_data = df[(df['CONTSIZE'].isin(dylan_heavy)) | (df['SALES_ASSIGNEDTO'].str.upper() == "DYLAN")]
            else:
                my_data = df[df['SALES_ASSIGNEDTO'].str.upper() == st.session_state.user_name]

            if st.session_state.view_mode == "complete":
                my_data = my_data[my_data['STATUS'] == 'COMPLETE']
            else:
                my_data = my_data[my_data['STATUS'] != 'COMPLETE']

            # STEP 1: SELECT BLOCK
            if st.session_state.task_step == 'block':
                st.markdown(f"## {st.session_state.user_name} TASKS")
                if my_data.empty: st.info("No tasks found.")
                else:
                    blocks = my_data.groupby('BLOCKALPHA').size().reset_index(name='counts')
                    for _, row in blocks.iterrows():
                        if st.button(f"{row['BLOCKALPHA']} ({row['counts']} Trees)", key=f"blk_{row['BLOCKALPHA']}"):
                            st.session_state.sel_block = row['BLOCKALPHA']; st.session_state.task_step = 'location'; st.rerun()

            # STEP 2: SELECT LOCATION
            elif st.session_state.task_step == 'location':
                if st.button("⬅️ BACK"): st.session_state.task_step = 'block'; st.rerun()
                st.markdown(f"## BLOCK {st.session_state.sel_block}")
                loc_data = my_data[my_data['BLOCKALPHA'] == st.session_state.sel_block]
                locs = loc_data.groupby('LOCATIONCODE').size().reset_index(name='counts')
                for _, row in locs.iterrows():
                    if st.button(f"{row['LOCATIONCODE']} ({row['counts']})", key=f"loc_{row['LOCATIONCODE']}"):
                        st.session_state.sel_loc = row['LOCATIONCODE']; st.session_state.task_step = 'list_items'; st.rerun()

            # STEP 3: LIST ITEMS (THE MENU)
            elif st.session_state.task_step == 'list_items':
                if st.button("⬅️ BACK"): st.session_state.task_step = 'location'; st.rerun()
                st.markdown(f"## {st.session_state.sel_block} - {st.session_state.sel_loc}")
                
                final = my_data[(my_data['BLOCKALPHA'] == st.session_state.sel_block) & 
                                (my_data['LOCATIONCODE'] == st.session_state.sel_loc)]
                
                # Render list as nice cards
                for idx, row in final.iterrows():
                    # Visual Card using HTML, clickable Button below it covers the action
                    card_html = f"""
                    <div style="background-color:#121212; border-left:4px solid #006847; padding:12px; margin-bottom:5px; border-radius:6px;">
                        <div style="color:#FFF; font-weight:bold; font-size:1.1rem;">{row.get('COMMONNAME')}</div>
                        <div style="color:#888; font-size:0.9rem;">{row.get('CONTSIZE')} | {row.get('LOTCODE')}</div>
                        <div style="color:#00D08E; font-size:0.8rem; margin-top:4px;">
                            PRIORITY: {row.get('PRIORITY')} &nbsp;|&nbsp; PTR: {row.get('PTRAVAILABLE')}
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button("OPEN ITEM ➤", key=f"open_{idx}"):
                        st.session_state.sel_item_idx = idx
                        st.session_state.task_step = 'edit_item'
                        st.rerun()
                    st.markdown("<div style='margin-bottom:15px'></div>", unsafe_allow_html=True)

            # STEP 4: EDIT ITEM (THE FULL SCREEN COMMAND CENTER)
            elif st.session_state.task_step == 'edit_item':
                idx = st.session_state.sel_item_idx
                if idx not in df.index:
                    st.error("Item lost. Go back."); st.stop()
                
                row = df.loc[idx]
                item_code = str(row.get('ITEMCODE', '')).strip()

                # --- 1. THE HUD HEADER (INFO AT A GLANCE) ---
                hud_html = f"""
                <div class="hud-card">
                    <div style="width:100%; margin-bottom:15px;">
                        <div class="hud-title">{row.get('COMMONNAME')}</div>
                        <div class="hud-subtitle">{row.get('CONTSIZE')}  •  {row.get('LOTCODE')}</div>
                    </div>
                    <div class="hud-item">
                        <div class="hud-label">PRIORITY</div>
                        <div class="hud-value">{row.get('PRIORITY')}</div>
                    </div>
                    <div class="hud-item">
                        <div class="hud-label">PTR</div>
                        <div class="hud-value">{row.get('PTRAVAILABLE')}</div>
                    </div>
                    <div class="hud-item">
                        <div class="hud-label">LTS</div>
                        <div class="hud-value" style="color:#FFF;">{row.get('S_LTS')}</div>
                    </div>
                </div>
                """
                st.markdown(hud_html, unsafe_allow_html=True)
                
                st.markdown(f"<div style='background:#121212; padding:10px; border-radius:8px; border:1px solid #333; margin-bottom:20px; color:#CCC'><b>📝 NOTE:</b> {row.get('CURRENT_SALESNOTE')}</div>", unsafe_allow_html=True)

                # --- 2. THE INPUT GRID (MODERN) ---
                st.markdown("### 🛠️ DATA ENTRY")
                
                c1, c2 = st.columns(2)
                with c1:
                    caliper = st.text_input("CALIPER", value=str(row.get('CALIPER','')), key=f"cal_{idx}")
                    # Match Logic
                    match_options = [str(i) for i in range(0, 105, 5)]
                    curr_match = str(row.get('MATCH_PCT', '')).strip()
                    if curr_match and curr_match not in match_options: match_options = [curr_match] + match_options
                    midx = match_options.index(curr_match) if curr_match in match_options else 0
                    match_pct = st.selectbox("MATCH %", options=match_options, index=midx, key=f"match_{idx}")
                    
                    # Note Logic
                    curr_note = str(row.get('LOC_SALESNOTE', '')).strip()
                    note_opts = sales_notes_map.get(item_code, [])
                    opts = [""] + note_opts
                    if curr_note and curr_note not in opts: opts.append(curr_note)
                    loc_note = st.selectbox("SALES NOTE", options=opts, index=opts.index(curr_note) if curr_note in opts else 0, key=f"lnote_{idx}")

                with c2:
                    spec = st.text_input("SPEC", value=str(row.get('SPEC','')), key=f"spec_{idx}")
                    prime_qty = st.text_input("PRIME QTY", value=str(row.get('PRIME_QTY','')), key=f"prime_{idx}")
                    comments = st.text_input("COMMENTS", value=str(row.get('LOC_COMMENTS','')), key=f"cmts_{idx}")

                pic_note = st.text_input("PIC NOTE", value=str(row.get('PIC_NOTE','')), key=f"pnote_{idx}")

                st.markdown("---")
                
                # --- 3. ACTIONS ---
                b1, b2 = st.columns([1, 2])
                with b1:
                    if st.button("⬅️ CANCEL"): 
                        st.session_state.task_step = 'list_items'; st.rerun()
                with b2:
                    if st.button("✅ SAVE & COMPLETE", type="primary"):
                        st.warning("⚠️ Saving disabled for 24h (Google API Quota Limit).")

                # Toggle Full Info
                with st.expander("🔍 VIEW ALL FILE DATA"):
                    for k,v in row.items():
                        if str(v).strip(): st.write(f"**{k}:** {v}")

        # --- DRIVE AROUND (UNCHANGED) ---
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
