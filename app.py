import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Discord Log Merger", layout="wide")

# --- CUSTOM PATH LOGIC ---
# If you leave this as "", it looks from the root or absolute path
# If you want it relative to your current folder, use "."
BASE_PATH = os.path.expanduser("~") 

st.title("merged_chats_processor.exe")

if 'file_list' not in st.session_state:
    st.session_state.file_list = []

with st.sidebar:
    st.header("add_files_to_merge")
    with st.form("file_form", clear_on_submit=True):
        st.write(f"Current Home: `{BASE_PATH}`")
        file_path = st.text_input("Path after Home (e.g. Downloads/chat.csv)")
        channel_name = st.text_input("Channel Name")
        add_btn = st.form_submit_button("Add to Queue")
        
        if add_btn and file_path and channel_name:
            # Clean path to avoid double slashes
            clean_path = file_path.strip("/")
            full_target = os.path.join(BASE_PATH, clean_path)
            
            if os.path.exists(full_target):
                st.session_state.file_list.append({"path": full_target, "channel": channel_name})
                st.success(f"Added: {channel_name}")
            else:
                st.error(f"File not found at: {full_target}")

    if st.session_state.file_list:
        st.write("### current_queue")
        for i, f in enumerate(st.session_state.file_list):
            st.text(f"{i+1}. {f['channel']}")
        if st.button("Clear All"):
            st.session_state.file_list = []

# --- MERGE LOGIC ---
if st.session_state.file_list:
    all_dfs = []
    for item in st.session_state.file_list:
        # Discord CSVs often don't have headers in raw exports
        # Adjust names based on your DCE export format
        df = pd.read_csv(item['path'], header=None)
        
        # DCE Standard CSV: 0:AuthorID, 1:Author, 2:Date, 3:Content, 4:Attachments
        # We take the first 4 and add our Channel column
        temp_df = df.iloc[:, [0, 1, 2, 3]].copy()
        temp_df.columns = ['ID', 'User', 'Timestamp', 'Message']
        temp_df['Channel'] = item['channel']
        all_dfs.append(temp_df)

    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df['Timestamp'] = pd.to_datetime(merged_df['Timestamp'], errors='coerce')
    merged_df = merged_df.sort_values(by='Timestamp').dropna(subset=['Timestamp'])

    # --- USER FILTER ---
    st.header("filters")
    all_users = sorted(merged_df['User'].unique().astype(str))
    selected_users = st.multiselect("Filter by User(s)", all_users)
    
    filtered_df = merged_df.copy()
    if selected_users:
        filtered_df = filtered_df[filtered_df['User'].isin(selected_users)]

    # --- VIEW & EXPORT ---
    st.header("output")
    st.dataframe(filtered_df.head(500), use_container_width=True)
    
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Merged CSV", data=csv_data, file_name="merged_chats.csv")
