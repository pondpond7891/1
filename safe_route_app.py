import streamlit as st
import math
import time
import pandas as pd

# ==========================================
# 1. ตั้งค่าหน้าเว็บ (Page Config)
# ==========================================
st.set_page_config(
    page_title="SAFE-ROUTE | ระบบค้นหาเส้นทางประหยัดและแจ้งเตือนความเร็ว",
    page_icon="🚗",
    layout="centered"
)

# ==========================================
# 2. ฟังก์ชันคำนวณหลัก (Core Logic)
# ==========================================
def haversine_distance(lat1, lon1, lat2, lon2):
    """คำนวณระยะทางระหว่างพิกัด GPS 2 จุด (กิโลเมตร)"""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_trip_cost(distance_km, fuel_efficiency, fuel_price, toll_fee):
    """คำนวณปริมาณน้ำมันและต้นทุนรวม"""
    fuel_used = distance_km / fuel_efficiency if fuel_efficiency > 0 else 0
    fuel_cost = fuel_used * fuel_price
    total_cost = fuel_cost + toll_fee
    return {
        "distance_km": round(distance_km, 2),
        "fuel_used": round(fuel_used, 2),
        "fuel_cost": round(fuel_cost, 2),
        "toll_fee": round(toll_fee, 2),
        "total_cost": round(total_cost, 2)
    }

def play_alert_sound():
    """ฝังโค้ดเล่นเสียงเตือนบนเบราว์เซอร์เมื่อความเร็วเกินกำหนด"""
    audio_html = """
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# ==========================================
# 3. ข้อมูลเส้นทางตัวอย่าง (Simulated Routes)
# ==========================================
ROUTES_DATA = {
    "เส้นทาง A: ทางหลัก (ระยะทางสั้นที่สุด / ประหยัดสุด)": {
        "distance_km": 42.5,
        "time_min": 48,
        "toll_fee": 0,
        "speed_limit": 90,
        "coords": pd.DataFrame({
            "lat": [13.7563, 13.7800, 13.8100, 13.8450],
            "lon": [100.5018, 100.5200, 100.5400, 100.5650]
        })
    },
    "เส้นทาง B: ทางด่วนพิเศษ (เร็วกว่า แต่มีค่าผ่านทาง)": {
        "distance_km": 46.0,
        "time_min": 32,
        "toll_fee": 65,
        "speed_limit": 110,
        "coords": pd.DataFrame({
            "lat": [13.7563, 13.7700, 13.8150, 13.8450],
            "lon": [100.5018, 100.5450, 100.5600, 100.5650]
        })
    }
}

# ==========================================
# 4. ส่วนแสดงผล UI (Streamlit Interface)
# ==========================================
st.title("🚗 SAFE-ROUTE")
st.caption("ระบบค้นหาเส้นทางที่ใกล้ที่สุด ลดต้นทุน และเฝ้าระวังความปลอดภัยในการขับขี่")

# แถบตั้งค่าด้านข้าง (Sidebar)
with st.sidebar:
    st.header("⚙️ ตั้งค่ายานพาหนะและต้นทุน")
    vehicle_type = st.selectbox("ประเภทรถ", ["รถยนต์ส่วนบุคคล (15 กม./ลิตร)", "รถกระบะ/ขนส่ง (11 กม./ลิตร)", "กำหนดเอง"])
    
    if "15" in vehicle_type:
        default_eff = 15.0
    elif "11" in vehicle_type:
        default_eff = 11.0
    else:
        default_eff = 14.0

    fuel_efficiency = st.number_input("อัตราสิ้นเปลือง (กม./ลิตร)", min_value=1.0, value=default_eff, step=0.5)
    fuel_price = st.number_input("ราคาน้ำมัน (บาท/ลิตร)", min_value=1.0, value=36.50, step=0.5)
    custom_speed_limit = st.number_input("กำหนดเพดานความเร็วแจ้งเตือน (กม./ชม.)", min_value=30, max_value=180, value=90, step=5)

# แบ่งแท็บการทำงาน 3 โมดูลหลัก
tab1, tab2, tab3 = st.tabs(["🗺️ 1. วางแผนเส้นทาง & ต้นทุน", "🚨 2. โหมดขับขี่ & แจ้งเตือนความเร็ว", "📊 3. สรุปผลการเดินทาง"])

# --- TAB 1: ค้นหาเส้นทางและเปรียบเทียบต้นทุน ---
with tab1:
    st.subheader("เลือกเส้นทางที่เหมาะสมและประหยัดที่สุด")
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        origin = st.text_input("จุดเริ่มต้น (Origin)", value="มหาวิทยาลัยราชภัฏสวนสุนันทา")
    with col_in2:
        destination = st.text_input("จุดหมายปลายทาง (Destination)", value="ศูนย์กระจายสินค้า นครปฐม")

    selected_route_name = st.radio("เลือกเส้นทางแนะนำ:", list(ROUTES_DATA.keys()))
    route_info = ROUTES_DATA[selected_route_name]

    cost_summary = calculate_trip_cost(
        distance_km=route_info["distance_km"],
        fuel_efficiency=fuel_efficiency,
        fuel_price=fuel_price,
        toll_fee=route_info["toll_fee"]
    )

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ระยะทาง", f"{cost_summary['distance_km']} กม.")
    m2.metric("เวลาเดินทาง", f"{route_info['time_min']} นาที")
    m3.metric("ค่าน้ำมัน", f"{cost_summary['fuel_cost']} ฿")
    m4.metric("ต้นทุนรวมสุทธิ", f"{cost_summary['total_cost']} ฿", delta="คุ้มค่าที่สุด" if cost_summary['toll_fee'] == 0 else f"+ค่าทางด่วน {cost_summary['toll_fee']} ฿", delta_color="normal" if cost_summary['toll_fee'] == 0 else "inverse")

    st.map(route_info["coords"], zoom=11)

# --- TAB 2: โหมดขับขี่และระบบแจ้งเตือนความเร็ว ---
with tab2:
    st.subheader("ระบบเฝ้าระวังความเร็วแบบเรียลไทม์ (Real-time Speed Monitor)")
    st.info(f"ขีดจำกัดความเร็วที่ตั้งไว้: **{custom_speed_limit} กม./ชม.** (ลองเลื่อนแถบความเร็วด้านล่างเพื่อทดสอบระบบแจ้งเตือน)")

    # จำลองความเร็วรถ (หรือเชื่อมข้อมูล GPS จริง)
    current_speed = st.slider("จำลองความเร็วรถปัจจุบัน (กม./ชม.)", min_value=0, max_value=160, value=75)

    # เงื่อนไขตรวจสอบความปลอดภัย
    if current_speed > custom_speed_limit:
        st.error(f"🚨 อันตราย! ความเร็วเกินกำหนด ({current_speed} กม./ชม.) กรุณาลดความเร็วทันที!")
        st.markdown(
            f"""
            <div style="background-color:#ef4444; color:white; padding:30px; border-radius:15px; text-align:center; border: 4px solid #991b1b;">
                <h1 style="font-size:64px; margin:0;">{current_speed}</h1>
                <p style="font-size:20px; margin:0;">กม./ชม. (เกินขีดจำกัด {custom_speed_limit} กม./ชม.)</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        play_alert_sound()
        if "overspeed_count" not in st.session_state:
            st.session_state.overspeed_count = 0
        st.session_state.overspeed_count += 1
    else:
        st.success(f"✅ ความเร็วอยู่ในเกณฑ์ปลอดภัย ({current_speed} / {custom_speed_limit} กม./ชม.)")
        st.markdown(
            f"""
            <div style="background-color:#10b981; color:white; padding:30px; border-radius:15px; text-align:center;">
                <h1 style="font-size:64px; margin:0;">{current_speed}</h1>
                <p style="font-size:20px; margin:0;">กม./ชม. (สถานะปกติ)</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- TAB 3: สรุปผลและคะแนนความปลอดภัย ---
with tab3:
    st.subheader("สรุปผลการเดินทางและความปลอดภัย (Trip Summary)")
    overspeed_times = st.session_state.get("overspeed_count", 0)
    safety_score = max(0, 100 - (overspeed_times * 5))

    s1, s2, s3 = st.columns(3)
    s1.metric("ระยะทางรวม", f"{cost_summary['distance_km']} กม.")
    s2.metric("ต้นทุนเดินทางจริง", f"{cost_summary['total_cost']} บาท")
    s3.metric("คะแนนความปลอดภัย", f"{safety_score} / 100")

    if overspeed_times > 0:
        st.warning(f"บันทึกการแจ้งเตือน: พบการขับรถเร็วเกินกำหนดจำนวน {overspeed_times} ครั้งระหว่างการทดสอบ")
    else:
        st.success("ยอดเยี่ยม! ไม่พบประวัติการขับรถเร็วเกินกำหนดตลอดเส้นทาง")

    if st.button("รีเซ็ตสถิติการขับขี่"):
        st.session_state.overspeed_count = 0
        st.rerun()
