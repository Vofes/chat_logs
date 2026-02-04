import streamlit as st
import pandas as pd
import dropbox
import io
import requests

st.set_page_config(page_title="Discord Log Merger", layout="wide")
st.title("merged_chats_processor.exe")

# --- Authentication Logic ---
def get_dropbox_client():
    try:
        # Generate temporary access token using refresh token
        auth_url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": st.secrets["DROPBOX_REFRESH_TOKEN"],
            "client_id": st.secrets["DROPBOX_APPKEY"],
            "client_secret": st.secrets["DROPBOX_SECRET"],
        }
        res = requests.post(auth_url, data=data).json()
        return dropbox.Dropbox(res["access_token"])
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

dbx = get_dropbox_client()

# --- Session State ---
if 'file_list' not in st.session_state:
    st.session_state.file_list = []

# --- Sidebar: Dropbox Input ---
with st.sidebar:
    st.header("add_dropbox_files")
    with st.form("dbx_form", clear_on_submit=True):
        dbx_path = st.text_input("Dropbox Path", value="/BRUH/OTHER_CHATS/test.csv")
        channel_name = st.text_input("Channel Name")
        add_btn = st.form_submit_button("Add to Queue")
        
        if add_btn and dbx_path and channel_name:
            st.session_state.file_list.append({"path": dbx_path, "channel": channel_name})

    if st.session_state.file_list:
        st.write("### current_queue")
        for i, f in enumerate(st.session_state.file_list):
            st.text(f"{i+1}. {f['channel']} - {f['path']}")
        if st.button("Clear All"):
            st.session_state.file_list = []

# --- Processing Logic ---
if st.session_state.file_list and dbx:
    all_dfs = []
    
    with st.spinner("fetching_from_dropbox..."):
        for item in st.session_state.file_list:
            try:
                # Download file from Dropbox into memory
                _, res = dbx.files_download(item['path'])
                df = pd.read_csv(io.BytesIO(res.content), header=None)
                
                # Take DCE standard columns: ID, User, Timestamp, Msg
                temp_df = df.iloc[:, [0, 1, 2, 3]].copy()
                temp_df.columns = ['ID', 'User', 'Timestamp', 'Message']
                temp_df['Channel'] = item['channel']
                all_dfs.append(temp_df)
            except Exception as e:
                st.error(f"Failed to load {item['path']}: {e}")

    if all_dfs:
        merged_df = pd.concat(all_dfs, ignore_index=True)
        merged_df['Timestamp'] = pd.to_datetime(merged_df['Timestamp'], errors='coerce')
        merged_df = merged_df.sort_values(by='Timestamp').dropna(subset=['Timestamp'])

        # --- User Filter ---
        st.header("filters")
        all_users = sorted(merged_df['User'].unique().astype(str))
        selected_users = st.multiselect("Filter by User(s)", all_users)
        
        final_df = merged_df.copy()
        if selected_users:
            final_df = final_df[final_df['User'].isin(selected_users)]

        # --- Output ---
        st.header("output_view")
        st.dataframe(final_df.head(1000), use_container_width=True)
        
        # Browser Download
        csv_data = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Merged File", data=csv_data, file_name="merged_logs.csv")
else:
    st.info("Add files from your Dropbox to start merging.")
