import streamlit as st
import pandas as pd
import random
from plyer import notification 
import joblib

svm_model = joblib.load('svm_model.pkl')
xgb_model = joblib.load('xgb_model.pkl')

# Simulate Identity and Device Info
def simulate_identity_and_device_check():
    return {
        'user_role': random.choice(['admin', 'edge_ops', 'core_ops', 'guest']),
        'authenticated': random.choice([True, False]),
        'compliant': random.choice([True, False])
    }

# Micro-Segmentation Logic
zones = {
    "core_network": {"access_roles": ["admin", "core_ops"]},
    "edge_network": {"access_roles": ["admin", "edge_ops"]},
    "ai_module": {"access_roles": ["ai_monitor"]}
}

def check_segment_access(user_role, zone):
    return user_role in zones[zone]["access_roles"]

# Mobile Notification Function
from pushbullet import Pushbullet
pb = Pushbullet("add-pushbullet-key-from-the profile")

def send_mobile_notification(title, message):
    pb.push_note(title, message)

# Desktop Notification Function
def send_notification(title, message):
    notification.notify(title=title, message=message, timeout=5)
    send_mobile_notification(title, message)

# ZTA Access Control Logic
def zero_trust_access_control(features, model, zone, identity_info):
    threat_prob = model.predict_proba([features])[0][1]

    if threat_prob >= 0.0:
        send_notification("⚠️ Threat Detected", "Access denied due to high threat.")
        return "❌ Access Denied: High Threat Detected"

    if not identity_info['authenticated']:
        return "❌ Access Denied: User Not Authenticated"
    
    if not identity_info['compliant']:
        return "❌ Access Denied: Non-Compliant Device"
    
    if not check_segment_access(identity_info['user_role'], zone):
        return f"❌ Access Denied: Role '{identity_info['user_role']}' not allowed in {zone}"
    
    return "✅ Access Granted"


# Streamlit UI
st.title("🔐 5G Threat Detection with ZTA")

uploaded_file = st.file_uploader("Upload BiLSTM Feature CSV", type=["csv"])
selected_model = st.selectbox("Choose a Model", ['SVM', 'XGBoost'])
zone = st.selectbox("Select Network Zone", list(zones.keys()))

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write("Uploaded Features", data.head())

    model = svm_model if selected_model == 'SVM' else xgb_model

    st.success(f"{selected_model} model is ready!")

    if st.button("Simulate Access Requests"):
        for i in range(min(5, len(data))):
            features = data.iloc[i].values
            identity = simulate_identity_and_device_check()
            decision = zero_trust_access_control(features, model, zone, identity)

            st.markdown(f"""
            **Request #{i+1}**
            - User Role: `{identity['user_role']}`
            - Authenticated: `{identity['authenticated']}`
            - Compliant: `{identity['compliant']}`
            - Zone: `{zone}`
            - **Access Decision**: {decision}
            """)
