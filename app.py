import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Discord Log Merger", layout="wide")

st.title("merged_chats_processor.exe")

# --- Session State for File List ---
if 'file_list' not in st.session_state:
    st.session_state.file_list = []

# --- Sidebar: Input Files ---
with st.sidebar:
    st.header("add_files_to_merge")
    with st.form("file_form", clear_on_submit=True):
        file_path = st.text_input("Relative File Path (e.g., Documents/chat.csv)")
        channel_name = st.text_input("Channel Name Label")
        add_btn = st.form_submit_button("Add to Queue")
        
        if add_btn and file_path and channel_name:
            st.session_state.file_list.append({"path": file_path, "channel": channel_name})

    if st.session_state.file_list:
        st.write("### current_queue")
        for i, f in enumerate(st.session_state.file_list):
            st.text(f"{i+1}. {f['channel']} ({f['path']})")
        if st.button("Clear All"):
            st.session_state.file_list = []

# --- Main Logic ---
if st.session_state.file_list:
    all_dfs = []
    
    with st.spinner("processing_massive_data..."):
        for item in st.session_state.file_list:
            full_path = os.path.expanduser(f"~/{item['path']}") # Starts from home dir
            if os.path.exists(full_path):
                # We assume the 5-column structure from before
                df = pd.read_csv(full_path, header=None, names=['ID', 'User', 'Timestamp', 'Message', 'Empty'])
                df['Channel'] = item['channel'] # Add the row label
                all_dfs.append(df)
            else:
                st.error(f"File not found: {full_path}")

    if all_dfs:
        # Merge and Sort by Timestamp
        merged_df = pd.concat(all_dfs, ignore_index=True)
        merged_df['Timestamp'] = pd.to_datetime(merged_df['Timestamp'])
        merged_df = merged_df.sort_values(by='Timestamp')

        # --- User Filter ---
        st.header("filters")
        all_users = merged_df['User'].unique().tolist()
        selected_users = st.multiselect("Select Users to Filter By (Leave empty for all)", all_users)
        
        display_df = merged_df.copy()
        if selected_users:
            display_df = display_df[display_df['User'].isin(selected_users)]

        # --- Viewing Section ---
        st.header("data_preview")
        st.dataframe(display_df.head(1000), use_container_width=True) # View first 1k rows to save RAM

        # --- Save/Download Section ---
        st.header("export_options")
        col1, col2 = st.columns(2)
        
        with col1:
            out_filename = st.text_input("Save As (filename.csv)", value="merged_export.csv")
            save_path = st.text_input("Save Location (Relative to home)", value="Downloads")
            
            if st.button("Save to Disk"):
                final_save_path = os.path.expanduser(f"~/{save_path}/{out_filename}")
                display_df.to_csv(final_save_path, index=False)
                st.success(f"Saved to {final_save_path}")

        with col2:
            # Browser download button
            csv_bytes = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download via Browser",
                data=csv_bytes,
                file_name=out_filename,
                mime='text/csv',
            )
else:
    st.info("Awaiting file paths in the sidebar to begin merging.")
